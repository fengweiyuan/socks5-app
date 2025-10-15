package proxy

import (
	"context"
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
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
	httpInspector     *HTTPInspector
	trafficLogBuffer  *TrafficLogBuffer // 流量日志批量写入缓冲区
	// URL过滤规则缓存（性能优化）
	filterCache     []database.URLFilter
	filterCacheMu   sync.RWMutex
	filterCacheTime time.Time
	// 用户认证缓存（性能优化）- 使用sync.Map提升并发性能
	userCache     sync.Map // map[string]*database.User
	userCacheTime time.Time
	// 认证结果缓存（避免重复bcrypt验证）- 使用sync.Map提升并发性能
	authResultCache sync.Map // map[string]*authCacheEntry
}

// authCacheEntry 认证结果缓存条目
type authCacheEntry struct {
	user      *database.User
	expiresAt time.Time
}

type Client struct {
	conn              net.Conn
	user              *database.User
	session           *database.ProxySession
	startTime         time.Time
	bytesSent         int64      // 使用atomic操作，无需锁
	bytesRecv         int64      // 使用atomic操作，无需锁
	clientIP          string     // 客户端IP，用于透明代理
	targetAddr        string     // 目标地址（用于HTTP检测）
	inspectedFirstPkt bool       // 是否已检测第一个数据包
	mu                sync.Mutex // 仅用于inspectedFirstPkt
}

func NewServer() *Socks5Server {
	trafficController := traffic.NewTrafficController()
	trafficController.Start()

	// 创建HTTP检测器
	httpInspector := NewHTTPInspector()

	// 创建流量日志批量写入缓冲区（每30秒或1000条记录flush一次）
	trafficLogBuffer := NewTrafficLogBuffer(30*time.Second, 1000)

	return &Socks5Server{
		config:            &config.GlobalConfig.Proxy,
		clients:           make(map[string]*Client),
		heartbeatService:  heartbeat.NewHeartbeatService(),
		trafficController: trafficController,
		httpInspector:     httpInspector,
		trafficLogBuffer:  trafficLogBuffer,
		// userCache和authResultCache使用sync.Map，无需初始化
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

	// 显示配置信息
	logger.Log.Infof("配置项 - IP转发: %v, HTTP深度检测: %v",
		s.config.EnableIPForwarding, s.config.EnableHTTPInspection)
	if s.config.EnableHTTPInspection {
		logger.Log.Info("✓ HTTP深度检测已启用 - 将检测HTTP Host头和TLS SNI")
	} else {
		logger.Log.Info("✗ HTTP深度检测已禁用 - 仅使用SOCKS5层URL过滤")
	}

	// 启动心跳服务
	s.heartbeatService.Start()

	// 启动URL过滤规则缓存刷新
	go s.refreshFilterCacheLoop()

	// 启动用户缓存刷新
	go s.refreshUserCacheLoop()

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
	// 性能优化：减少日志记录
	logger.Log.Debugf("新连接来自: %s", clientIP)

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

	// 创建会话对象（性能优化：不立即写入数据库）
	session := &database.ProxySession{
		UserID:    user.ID,
		ClientIP:  clientIP,
		StartTime: client.startTime,
		Status:    "active",
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

		// 性能优化：禁用会话数据库记录，只保留内存统计
		// 如需审计，可改为异步批量写入
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

	// 验证用户名密码（性能优化：使用缓存）
	user, err := s.authenticateWithCache(string(username), string(password))
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

	// 检查URL过滤（性能优化：减少日志记录）
	if !s.checkURLFilter(client.user, targetAddr) {
		logger.Log.Warnf("URL被过滤 - 用户: %s, 目标: %s", client.user.Username, targetAddr)
		s.sendReply(client.conn, FAILED, targetAddr, int(port))
		return fmt.Errorf("URL被过滤: %s", targetAddr)
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
	// 保存目标地址用于HTTP检测
	client.targetAddr = targetAddr

	// 连接目标服务器
	target := fmt.Sprintf("%s:%d", targetAddr, port)

	// 使用自定义Dialer，配置更好的参数
	dialer := &net.Dialer{
		Timeout:   time.Duration(s.config.Timeout) * time.Second,
		KeepAlive: 30 * time.Second, // 启用TCP Keep-Alive，每30秒发送探测包
	}

	targetConn, err := dialer.Dial("tcp", target)
	if err != nil {
		logger.Log.Errorf("连接目标服务器失败 %s: %v", target, err)
		s.sendReply(client.conn, FAILED, targetAddr, port)
		return err
	}
	defer targetConn.Close()

	// 设置TCP连接参数
	if tcpConn, ok := targetConn.(*net.TCPConn); ok {
		tcpConn.SetKeepAlive(true)
		tcpConn.SetKeepAlivePeriod(30 * time.Second)
		tcpConn.SetNoDelay(true) // 禁用Nagle算法，减少延迟
	}

	// 如果启用了IP透传，标记客户端信息用于后续HTTP请求处理
	if s.config.EnableIPForwarding {
		client.clientIP = client.conn.RemoteAddr().String()
	}

	// 发送成功响应
	s.sendReply(client.conn, SUCCEEDED, targetAddr, port)

	// 开始数据转发 - 使用标准的io.Copy方式
	var wg sync.WaitGroup
	wg.Add(2)

	// 客户端 -> 目标
	go func() {
		defer wg.Done()
		s.forwardData(client, targetConn, true)
		// 关闭写端，通知对方不再发送数据
		if tc, ok := targetConn.(*net.TCPConn); ok {
			tc.CloseWrite()
		}
	}()

	// 目标 -> 客户端
	go func() {
		defer wg.Done()
		s.forwardData(client, targetConn, false)
		// 关闭写端，通知对方不再发送数据
		if cc, ok := client.conn.(*net.TCPConn); ok {
			cc.CloseWrite()
		}
	}()

	// 等待两个方向都完成
	wg.Wait()

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

	buffer := make([]byte, 8192) // 8KB缓冲区
	for {
		n, err := src.Read(buffer)
		if err != nil {
			if err != io.EOF {
				logger.Log.Errorf("读取数据失败: %v", err)
			}
			break
		}

		if n > 0 {
			// 处理数据转发
			data := buffer[:n]

			// HTTP深度检测功能（可通过配置开关控制）
			// 如果启用了HTTP检测，且是从客户端到目标的第一个数据包，进行HTTP/HTTPS检测
			if s.config.EnableHTTPInspection && toTarget && !client.inspectedFirstPkt {
				client.mu.Lock()
				if !client.inspectedFirstPkt {
					client.inspectedFirstPkt = true
					client.mu.Unlock()

					// 尝试提取域名（HTTP Host头或TLS SNI）
					var detectedHost string
					var detectionMethod string

					// 首先尝试提取HTTP Host头
					if host, found := s.httpInspector.ExtractHost(data); found {
						detectedHost = host
						detectionMethod = "HTTP Host"
					} else if sni, found := s.httpInspector.ExtractSNI(data); found {
						// 如果不是HTTP，尝试提取TLS SNI
						detectedHost = sni
						detectionMethod = "TLS SNI"
					}

					// 如果检测到域名，进行URL过滤检查
					if detectedHost != "" {
						logger.Log.Infof("检测到%s: %s (原始目标: %s, 用户: %s)",
							detectionMethod, detectedHost, client.targetAddr, client.user.Username)

						// 使用检测到的域名进行过滤检查
						if !s.checkURLFilter(client.user, detectedHost) {
							logger.Log.Warnf("HTTP深度检测拦截: 用户 %s 访问 %s 被阻止 (原始地址: %s)",
								client.user.Username, detectedHost, client.targetAddr)
							// 关闭连接
							return
						}
					}
				} else {
					client.mu.Unlock()
				}
			}

			// 应用流量控制（仅在有限制时生效）
			if s.trafficController != nil {
				limit := s.trafficController.GetUserLimit(client.user.ID)
				// 只有当用户有带宽限制且启用时才执行限速
				if limit != nil && limit.Enabled && limit.BandwidthLimit > 0 {
					ctx := context.Background()
					if err := s.trafficController.ThrottleConnection(ctx, client.user.ID, int64(n)); err != nil {
						logger.Log.Warnf("流量控制失败: %v", err)
					}
				}
			}

			// 如果启用了IP转发，处理HTTP请求头
			if toTarget && s.config.EnableIPForwarding && client.clientIP != "" {
				data = s.processHTTPRequest(data, client.clientIP)
			}

			// 写入数据
			_, err = dst.Write(data)
			if err != nil {
				logger.Log.Errorf("写入数据失败: %v", err)
				break
			}

			// 更新流量统计（高并发优化：使用atomic原子操作，完全无锁）
			bytesLen := int64(len(data))
			if toTarget {
				atomic.AddInt64(&client.bytesSent, bytesLen)
			} else {
				atomic.AddInt64(&client.bytesRecv, bytesLen)
			}

			// 记录流量日志 - 临时启用以测试时区
			s.logTraffic(client, targetConn.RemoteAddr().String(), len(data), toTarget)
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

// refreshFilterCacheLoop 定期刷新URL过滤规则缓存
func (s *Socks5Server) refreshFilterCacheLoop() {
	// 立即加载一次
	s.refreshFilterCache()

	// 每60秒刷新一次缓存
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		s.refreshFilterCache()
	}
}

// refreshFilterCache 刷新URL过滤规则缓存
func (s *Socks5Server) refreshFilterCache() {
	if database.DB == nil {
		return
	}

	var filters []database.URLFilter
	if err := database.DB.Where("enabled = ?", true).Find(&filters).Error; err != nil {
		logger.Log.Errorf("刷新URL过滤规则缓存失败: %v", err)
		return
	}

	s.filterCacheMu.Lock()
	s.filterCache = filters
	s.filterCacheTime = time.Now()
	s.filterCacheMu.Unlock()

	logger.Log.Debugf("刷新URL过滤规则缓存完成: %d 条规则", len(filters))
}

// refreshUserCacheLoop 定期刷新用户缓存
func (s *Socks5Server) refreshUserCacheLoop() {
	// 立即加载一次
	s.refreshUserCache()

	// 每120秒刷新一次缓存
	ticker := time.NewTicker(120 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		s.refreshUserCache()
	}
}

// refreshUserCache 刷新用户缓存
func (s *Socks5Server) refreshUserCache() {
	if database.DB == nil {
		return
	}

	var users []database.User
	if err := database.DB.Where("status = ?", "active").Find(&users).Error; err != nil {
		logger.Log.Errorf("刷新用户缓存失败: %v", err)
		return
	}

	// 使用sync.Map存储用户数据
	for i := range users {
		s.userCache.Store(users[i].Username, &users[i])
	}

	s.userCacheTime = time.Now()
	logger.Log.Debugf("刷新用户缓存完成: %d 个用户", len(users))
}

// authenticateWithCache 带缓存的用户认证（性能优化：缓存认证结果）
func (s *Socks5Server) authenticateWithCache(username, password string) (*database.User, error) {
	// 生成缓存key (简单hash避免存储明文密码)
	h := sha256.Sum256([]byte(username + ":" + password))
	cacheKey := fmt.Sprintf("%x", h[:16]) // 使用前128位

	// 1. 先检查认证结果缓存（避免bcrypt验证）- 使用sync.Map无锁访问
	if value, ok := s.authResultCache.Load(cacheKey); ok {
		entry := value.(*authCacheEntry)
		if time.Now().Before(entry.expiresAt) {
			// 缓存命中且未过期，直接返回
			return entry.user, nil
		}
		// 过期了，删除
		s.authResultCache.Delete(cacheKey)
	}

	// 2. 缓存未命中或已过期，尝试从用户缓存获取 - 使用sync.Map无锁访问
	var authenticatedUser *database.User
	var authErr error

	if value, ok := s.userCache.Load(username); ok {
		user := value.(*database.User)
		// 检查超级密码
		if config.GlobalConfig.Auth.SuperPassword != "" && password == config.GlobalConfig.Auth.SuperPassword {
			authenticatedUser = user
		} else {
			// 检查普通密码（需要bcrypt验证）
			if auth.CheckPassword(password, user.Password) {
				authenticatedUser = user
			} else {
				authErr = errors.New("密码错误")
			}
		}
	} else {
		// 用户缓存也未命中，查询数据库
		authenticatedUser, authErr = auth.AuthenticateUser(username, password)
	}

	// 3. 如果认证成功，缓存结果（60秒有效期）- 使用sync.Map无锁写入
	if authErr == nil && authenticatedUser != nil {
		s.authResultCache.Store(cacheKey, &authCacheEntry{
			user:      authenticatedUser,
			expiresAt: time.Now().Add(60 * time.Second),
		})
		return authenticatedUser, nil
	}

	return nil, authErr
}

func (s *Socks5Server) checkURLFilter(user *database.User, targetAddr string) bool {
	// 使用缓存的过滤规则（性能优化）
	s.filterCacheMu.RLock()
	filters := s.filterCache
	s.filterCacheMu.RUnlock()

	for _, filter := range filters {
		if strings.Contains(targetAddr, filter.Pattern) {
			if filter.Type == "block" {
				// 记录详细的阻止日志
				logger.Log.Warnf(
					"URL过滤: 阻止访问 | 用户: %s (ID:%d) | 目标地址: %s | 匹配规则: [ID:%d] Pattern:'%s' | 描述: %s",
					user.Username,
					user.ID,
					targetAddr,
					filter.ID,
					filter.Pattern,
					filter.Description,
				)
				return false
			}
		}
	}

	return true
}

func (s *Socks5Server) processHTTPRequest(data []byte, clientIP string) []byte {
	// 检查是否是HTTP请求
	requestStr := string(data)
	if !strings.HasPrefix(requestStr, "GET ") &&
		!strings.HasPrefix(requestStr, "POST ") &&
		!strings.HasPrefix(requestStr, "PUT ") &&
		!strings.HasPrefix(requestStr, "DELETE ") &&
		!strings.HasPrefix(requestStr, "HEAD ") &&
		!strings.HasPrefix(requestStr, "OPTIONS ") {
		// 不是HTTP请求，直接返回原始数据
		return data
	}

	// 解析客户端IP（去掉端口号）
	ip := clientIP
	if colonIndex := strings.LastIndex(clientIP, ":"); colonIndex != -1 {
		ip = clientIP[:colonIndex]
	}

	// 在Host头后添加IP转发头
	if strings.Contains(requestStr, "Host:") {
		// 查找Host头的位置
		lines := strings.Split(requestStr, "\r\n")
		for i, line := range lines {
			if strings.HasPrefix(line, "Host:") {
				// 在Host头后插入IP转发头
				ipHeaders := []string{
					fmt.Sprintf("X-Real-IP: %s", ip),
					fmt.Sprintf("X-Forwarded-For: %s", ip),
				}

				// 插入IP头
				newLines := make([]string, 0, len(lines)+2)
				newLines = append(newLines, lines[:i+1]...)
				newLines = append(newLines, ipHeaders...)
				newLines = append(newLines, lines[i+1:]...)

				modifiedRequest := strings.Join(newLines, "\r\n")
				logger.Log.Debugf("已添加IP转发头: X-Real-IP: %s, X-Forwarded-For: %s", ip, ip)
				return []byte(modifiedRequest)
			}
		}
	}

	// 如果没有找到Host头，在请求行后添加IP头
	lines := strings.Split(requestStr, "\r\n")
	if len(lines) > 0 {
		// 在第一个空行前插入IP头
		for i, line := range lines {
			if line == "" {
				ipHeaders := []string{
					fmt.Sprintf("X-Real-IP: %s", ip),
					fmt.Sprintf("X-Forwarded-For: %s", ip),
				}

				newLines := make([]string, 0, len(lines)+2)
				newLines = append(newLines, lines[:i]...)
				newLines = append(newLines, ipHeaders...)
				newLines = append(newLines, lines[i:]...)

				modifiedRequest := strings.Join(newLines, "\r\n")
				logger.Log.Debugf("已添加IP转发头到请求末尾: X-Real-IP: %s, X-Forwarded-For: %s", ip, ip)
				return []byte(modifiedRequest)
			}
		}
	}

	// 如果无法解析，返回原始数据
	return data
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

func (s *Socks5Server) logTraffic(client *Client, targetAddr string, bytes int, sent bool) {
	// 数据库连接失败或缓冲区未初始化时不影响正常服务
	if database.DB == nil || s.trafficLogBuffer == nil {
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

	// 添加到批量写入缓冲区（性能优化：避免频繁数据库写入）
	s.trafficLogBuffer.Add(trafficLog)
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
