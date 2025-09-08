package proxy

import (
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"sync"
	"time"

	"socks5-app/internal/auth"
	"socks5-app/internal/config"
	"socks5-app/internal/database"
	"socks5-app/internal/heartbeat"
	"socks5-app/internal/logger"
	"socks5-app/internal/traffic"
)

const (
	SOCKS5_VERSION = 0x05
	NO_AUTH        = 0x00
	USER_PASS_AUTH = 0x02
	NO_ACCEPTABLE  = 0xFF

	CONNECT = 0x01
	BIND    = 0x02
	UDP     = 0x03

	SUCCEEDED = 0x00
	FAILED    = 0x01
)

type Socks5Server struct {
	listener          net.Listener
	config            *config.ProxyConfig
	clients           map[string]*Client
	mu                sync.RWMutex
	heartbeatService  *heartbeat.HeartbeatService
	trafficController *traffic.TrafficController
}

type Client struct {
	conn      net.Conn
	user      *database.User
	session   *database.ProxySession
	startTime time.Time
	bytesSent int64
	bytesRecv int64
	mu        sync.Mutex
}

func NewServer() *Socks5Server {
	trafficController := traffic.NewTrafficController()
	trafficController.Start()

	return &Socks5Server{
		config:            &config.GlobalConfig.Proxy,
		clients:           make(map[string]*Client),
		heartbeatService:  heartbeat.NewHeartbeatService(),
		trafficController: trafficController,
	}
}

func (s *Socks5Server) Start() error {
	addr := fmt.Sprintf("%s:%s", s.config.Host, s.config.Port)
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("启动SOCKS5服务器失败: %v", err)
	}

	s.listener = listener
	logger.Log.Infof("SOCKS5服务器启动成功，监听地址: %s", addr)

	// 启动心跳服务
	s.heartbeatService.Start()

	// 确保在服务停止时关闭心跳服务
	defer s.heartbeatService.Stop()

	for {
		conn, err := listener.Accept()
		if err != nil {
			logger.Log.Errorf("接受连接失败: %v", err)
			continue
		}

		go s.handleConnection(conn)
	}
}

func (s *Socks5Server) handleConnection(conn net.Conn) {
	defer conn.Close()

	clientIP := conn.RemoteAddr().String()
	logger.Log.Infof("新连接来自: %s", clientIP)

	// 认证阶段
	user, err := s.authenticate(conn)
	if err != nil {
		logger.Log.Errorf("认证失败: %v", err)
		return
	}

	// 创建客户端会话
	client := &Client{
		conn:      conn,
		user:      user,
		startTime: time.Now(),
	}

	// 创建数据库会话记录（数据库连接失败时不影响正常服务）
	session := &database.ProxySession{
		UserID:    user.ID,
		ClientIP:  clientIP,
		StartTime: client.startTime,
		Status:    "active",
	}
	if database.DB != nil {
		if err := database.DB.Create(session).Error; err != nil {
			logger.Log.Errorf("创建会话记录失败: %v", err)
		}
	}
	client.session = session

	// 添加到客户端列表
	s.mu.Lock()
	s.clients[clientIP] = client
	s.mu.Unlock()

	// 增加连接计数
	s.heartbeatService.IncrementConnection()

	defer func() {
		s.mu.Lock()
		delete(s.clients, clientIP)
		s.mu.Unlock()

		// 减少连接计数
		s.heartbeatService.DecrementConnection()

		// 更新会话结束时间（数据库连接失败时不影响正常服务）
		if database.DB != nil {
			endTime := time.Now()
			client.session.EndTime = &endTime
			client.session.Status = "closed"
			client.session.BytesSent = client.bytesSent
			client.session.BytesRecv = client.bytesRecv
			if err := database.DB.Save(client.session).Error; err != nil {
				logger.Log.Errorf("保存会话记录失败: %v", err)
			}
		}
	}()

	// 处理请求
	for {
		if err := s.handleRequest(client); err != nil {
			if err != io.EOF {
				logger.Log.Errorf("处理请求失败: %v", err)
			}
			break
		}
	}
}

func (s *Socks5Server) authenticate(conn net.Conn) (*database.User, error) {
	// 读取客户端支持的认证方法
	buf := make([]byte, 2)
	if _, err := io.ReadFull(conn, buf); err != nil {
		return nil, err
	}

	if buf[0] != SOCKS5_VERSION {
		return nil, errors.New("不支持的SOCKS版本")
	}

	nmethods := buf[1]
	methods := make([]byte, nmethods)
	if _, err := io.ReadFull(conn, methods); err != nil {
		return nil, err
	}

	// 检查是否支持用户名密码认证
	hasUserPass := false
	for _, method := range methods {
		if method == USER_PASS_AUTH {
			hasUserPass = true
			break
		}
	}

	if !hasUserPass {
		// 回复不支持认证
		conn.Write([]byte{SOCKS5_VERSION, NO_ACCEPTABLE})
		return nil, errors.New("客户端不支持用户名密码认证")
	}

	// 回复使用用户名密码认证
	conn.Write([]byte{SOCKS5_VERSION, USER_PASS_AUTH})

	// 读取用户名密码
	authBuf := make([]byte, 2)
	if _, err := io.ReadFull(conn, authBuf); err != nil {
		return nil, err
	}

	if authBuf[0] != 0x01 {
		return nil, errors.New("无效的认证子协议版本")
	}

	ulen := authBuf[1]
	username := make([]byte, ulen)
	if _, err := io.ReadFull(conn, username); err != nil {
		return nil, err
	}

	plenBuf := make([]byte, 1)
	if _, err := io.ReadFull(conn, plenBuf); err != nil {
		return nil, err
	}

	plen := plenBuf[0]
	password := make([]byte, plen)
	if _, err := io.ReadFull(conn, password); err != nil {
		return nil, err
	}

	// 验证用户名密码
	user, err := auth.AuthenticateUser(string(username), string(password))
	if err != nil {
		// 认证失败
		conn.Write([]byte{0x01, 0x01})
		return nil, err
	}

	// 认证成功
	conn.Write([]byte{0x01, 0x00})
	return user, nil
}

func (s *Socks5Server) handleRequest(client *Client) error {
	// 读取请求头
	header := make([]byte, 4)
	if _, err := io.ReadFull(client.conn, header); err != nil {
		return err
	}

	if header[0] != SOCKS5_VERSION {
		return errors.New("不支持的SOCKS版本")
	}

	cmd := header[1]
	addrType := header[3]

	// 读取目标地址
	var targetAddr string
	switch addrType {
	case 0x01: // IPv4
		addr := make([]byte, 4)
		if _, err := io.ReadFull(client.conn, addr); err != nil {
			return err
		}
		targetAddr = net.IP(addr).String()
	case 0x03: // 域名
		lenBuf := make([]byte, 1)
		if _, err := io.ReadFull(client.conn, lenBuf); err != nil {
			return err
		}
		domainLen := lenBuf[0]
		domain := make([]byte, domainLen)
		if _, err := io.ReadFull(client.conn, domain); err != nil {
			return err
		}
		targetAddr = string(domain)
	case 0x04: // IPv6
		addr := make([]byte, 16)
		if _, err := io.ReadFull(client.conn, addr); err != nil {
			return err
		}
		targetAddr = net.IP(addr).String()
	default:
		return errors.New("不支持的地址类型")
	}

	// 读取端口
	portBuf := make([]byte, 2)
	if _, err := io.ReadFull(client.conn, portBuf); err != nil {
		return err
	}
	port := binary.BigEndian.Uint16(portBuf)

	// 检查URL过滤
	if !s.checkURLFilter(client.user, targetAddr) {
		s.sendReply(client.conn, FAILED, targetAddr, int(port))
		return errors.New("URL被过滤")
	}

	// 处理不同类型的命令
	switch cmd {
	case CONNECT:
		return s.handleConnect(client, targetAddr, int(port))
	case BIND:
		return s.handleBind(client, targetAddr, int(port))
	case UDP:
		return s.handleUDP(client, targetAddr, int(port))
	default:
		return errors.New("不支持的命令")
	}
}

func (s *Socks5Server) handleConnect(client *Client, targetAddr string, port int) error {
	// 连接目标服务器
	target := fmt.Sprintf("%s:%d", targetAddr, port)
	targetConn, err := net.DialTimeout("tcp", target, time.Duration(s.config.Timeout)*time.Second)
	if err != nil {
		s.sendReply(client.conn, FAILED, targetAddr, port)
		return err
	}
	defer targetConn.Close()

	// 如果启用了IP透传，在连接建立后发送客户端IP信息
	if s.config.EnableIPForwarding {
		if err := s.sendClientIPInfo(targetConn, client.conn.RemoteAddr().String()); err != nil {
			logger.Log.Warnf("发送客户端IP信息失败: %v", err)
			// 即使IP透传失败，也不影响正常代理功能
		}
	}

	// 发送成功响应
	s.sendReply(client.conn, SUCCEEDED, targetAddr, port)

	// 开始数据转发
	go s.forwardData(client, targetConn, true) // 客户端 -> 目标
	s.forwardData(client, targetConn, false)   // 目标 -> 客户端

	return nil
}

func (s *Socks5Server) handleBind(client *Client, targetAddr string, port int) error {
	// 实现BIND命令（通常用于FTP等协议）
	// 这里简化处理，返回不支持
	s.sendReply(client.conn, FAILED, targetAddr, port)
	return errors.New("BIND命令暂不支持")
}

func (s *Socks5Server) handleUDP(client *Client, targetAddr string, port int) error {
	// 实现UDP命令
	// 这里简化处理，返回不支持
	s.sendReply(client.conn, FAILED, targetAddr, port)
	return errors.New("UDP命令暂不支持")
}

func (s *Socks5Server) forwardData(client *Client, targetConn net.Conn, toTarget bool) {
	var src, dst net.Conn
	if toTarget {
		src = client.conn
		dst = targetConn
	} else {
		src = targetConn
		dst = client.conn
	}

	buffer := make([]byte, 4096)
	for {
		n, err := src.Read(buffer)
		if err != nil {
			if err != io.EOF {
				logger.Log.Errorf("读取数据失败: %v", err)
			}
			break
		}

		if n > 0 {
			// 应用流量控制
			if s.trafficController != nil {
				ctx := context.Background()
				if err := s.trafficController.ThrottleConnection(ctx, client.user.ID, int64(n)); err != nil {
					logger.Log.Warnf("流量控制失败: %v", err)
				}

				// 记录流量到流量控制器
				s.trafficController.RecordTraffic(client.user.ID, int64(n))
			}

			_, err = dst.Write(buffer[:n])
			if err != nil {
				logger.Log.Errorf("写入数据失败: %v", err)
				break
			}

			// 更新流量统计
			client.mu.Lock()
			if toTarget {
				client.bytesSent += int64(n)
			} else {
				client.bytesRecv += int64(n)
			}
			client.mu.Unlock()

			// 记录流量日志
			s.logTraffic(client, targetConn.RemoteAddr().String(), n, toTarget)
		}
	}
}

func (s *Socks5Server) sendReply(conn net.Conn, reply byte, addr string, port int) {
	// 构建响应
	response := []byte{SOCKS5_VERSION, reply, 0x00, 0x01}

	// 添加IP地址（这里简化处理，使用127.0.0.1）
	ip := net.ParseIP("127.0.0.1").To4()
	response = append(response, ip...)

	// 添加端口
	portBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(portBytes, uint16(port))
	response = append(response, portBytes...)

	conn.Write(response)
}

func (s *Socks5Server) checkURLFilter(user *database.User, targetAddr string) bool {
	// 检查URL过滤规则（数据库连接失败时允许通过）
	if database.DB == nil {
		logger.Log.Warn("数据库连接不可用，跳过URL过滤检查")
		return true
	}

	var filters []database.URLFilter
	if err := database.DB.Where("enabled = ?", true).Find(&filters).Error; err != nil {
		logger.Log.Errorf("查询URL过滤规则失败: %v", err)
		return true // 数据库查询失败时允许通过
	}

	for _, filter := range filters {
		if strings.Contains(targetAddr, filter.Pattern) {
			if filter.Type == "block" {
				return false
			}
		}
	}

	return true
}

func (s *Socks5Server) sendClientIPInfo(targetConn net.Conn, clientIP string) error {
	// 实现IP透传功能
	// 方法1: 使用系统调用设置原始目标地址（需要root权限）
	if err := s.setOriginalDst(targetConn, clientIP); err != nil {
		logger.Log.Warnf("设置原始目标地址失败，使用备用方法: %v", err)
		// 方法2: 在数据流中插入IP信息（可能影响协议）
		return s.insertIPInfo(targetConn, clientIP)
	}

	logger.Log.Infof("已设置客户端IP信息到目标服务器: %s", clientIP)
	return nil
}

func (s *Socks5Server) setOriginalDst(targetConn net.Conn, clientIP string) error {
	// 尝试使用系统调用设置原始目标地址
	// 注意：这个功能需要系统支持且可能需要特殊权限
	// 目前简化实现，直接返回错误以使用备用方法

	// 获取底层文件描述符
	tcpConn, ok := targetConn.(*net.TCPConn)
	if !ok {
		return errors.New("连接不是TCP连接")
	}

	file, err := tcpConn.File()
	if err != nil {
		return fmt.Errorf("获取文件描述符失败: %v", err)
	}
	defer file.Close()

	// 这里可以添加具体的系统调用实现
	// 由于不同系统的实现差异较大，暂时返回错误使用备用方法
	_ = file.Fd() // 避免未使用变量警告

	return errors.New("系统调用方法暂未实现，使用备用方法")
}

func (s *Socks5Server) insertIPInfo(targetConn net.Conn, clientIP string) error {
	// 备用方法：在数据流中插入IP信息
	// 注意：这个实现会修改数据流，可能影响某些协议
	// 建议目标服务器能够处理这种格式的IP信息

	// 使用自定义协议发送客户端IP信息
	// 格式: "X-Real-IP: <client_ip>\r\nX-Forwarded-For: <client_ip>\r\n\r\n"
	ipInfo := fmt.Sprintf("X-Real-IP: %s\r\nX-Forwarded-For: %s\r\n\r\n", clientIP, clientIP)
	_, err := targetConn.Write([]byte(ipInfo))
	if err != nil {
		return fmt.Errorf("写入客户端IP信息失败: %v", err)
	}

	logger.Log.Infof("已插入客户端IP信息到数据流: %s", clientIP)
	return nil
}

func (s *Socks5Server) logTraffic(client *Client, targetAddr string, bytes int, sent bool) {
	// 数据库连接失败时不影响正常服务
	if database.DB == nil {
		return
	}

	// 解析目标地址
	host, portStr, err := net.SplitHostPort(targetAddr)
	if err != nil {
		host = targetAddr
		portStr = "0"
	}
	port, _ := strconv.Atoi(portStr)

	// 创建流量日志
	trafficLog := &database.TrafficLog{
		UserID:     client.user.ID,
		ClientIP:   client.conn.RemoteAddr().String(),
		TargetIP:   host,
		TargetPort: port,
		Protocol:   "tcp",
		Timestamp:  time.Now(),
	}

	if sent {
		trafficLog.BytesSent = int64(bytes)
	} else {
		trafficLog.BytesRecv = int64(bytes)
	}

	if err := database.DB.Create(trafficLog).Error; err != nil {
		logger.Log.Errorf("创建流量日志失败: %v", err)
	}
}

// GetActiveClients 获取活跃客户端列表
func (s *Socks5Server) GetActiveClients() []*Client {
	s.mu.RLock()
	defer s.mu.RUnlock()

	clients := make([]*Client, 0, len(s.clients))
	for _, client := range s.clients {
		clients = append(clients, client)
	}
	return clients
}

// GetTrafficController 获取流量控制器
func (s *Socks5Server) GetTrafficController() *traffic.TrafficController {
	return s.trafficController
}
