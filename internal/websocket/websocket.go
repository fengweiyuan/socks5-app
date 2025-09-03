package websocket

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// 流量数据类型
type TrafficData struct {
	UserID          int     `json:"user_id"`
	ClientIP        string  `json:"client_ip"`
	BytesSent       int64   `json:"bytes_sent"`
	BytesRecv       int64   `json:"bytes_recv"`
	Speed           float64 `json:"speed"`     // 当前速度 (bytes/s)
	Bandwidth       float64 `json:"bandwidth"` // 带宽使用率 (%)
	Timestamp       int64   `json:"timestamp"`
	ConnectionCount int     `json:"connection_count"` // 当前连接数
}

// 代理健康数据类型
type ProxyHealthData struct {
	ProxyID       string  `json:"proxy_id"`
	Status        string  `json:"status"`
	ActiveConns   int     `json:"active_connections"`
	TotalConns    int     `json:"total_connections"`
	Uptime        int64   `json:"uptime_seconds"`
	LastHeartbeat int64   `json:"last_heartbeat"`
	Load          float64 `json:"load_percentage"`
}

// 系统性能数据类型
type SystemPerformanceData struct {
	CPUUsage    float64 `json:"cpu_usage"`
	MemoryUsage float64 `json:"memory_usage"`
	DiskUsage   float64 `json:"disk_usage"`
	NetworkIn   float64 `json:"network_in"`
	NetworkOut  float64 `json:"network_out"`
	Timestamp   int64   `json:"timestamp"`
}

// WebSocket连接客户端
type Client struct {
	ID     string
	Conn   *websocket.Conn
	Send   chan []byte
	UserID int
	Topics map[string]bool // 订阅的主题
	mu     sync.RWMutex
}

// WebSocket管理器
type Manager struct {
	clients    map[string]*Client
	broadcast  chan interface{}
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex

	// 数据收集器
	trafficCollector     chan TrafficData
	proxyHealthCollector chan ProxyHealthData
	systemCollector      chan SystemPerformanceData

	// 配置
	upgrader websocket.Upgrader
}

// 创建新的WebSocket管理器
func NewManager() *Manager {
	return &Manager{
		clients:              make(map[string]*Client),
		broadcast:            make(chan interface{}, 100),
		register:             make(chan *Client, 10),
		unregister:           make(chan *Client, 10),
		trafficCollector:     make(chan TrafficData, 1000),
		proxyHealthCollector: make(chan ProxyHealthData, 100),
		systemCollector:      make(chan SystemPerformanceData, 100),
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // 允许所有来源，生产环境应该限制
			},
		},
	}
}

// 启动WebSocket管理器
func (m *Manager) Start() {
	go m.run()
	go m.collectAndBroadcast()
}

// 主循环
func (m *Manager) run() {
	for {
		select {
		case client := <-m.register:
			m.mu.Lock()
			m.clients[client.ID] = client
			m.mu.Unlock()
			log.Printf("WebSocket客户端已连接: %s", client.ID)

		case client := <-m.unregister:
			m.mu.Lock()
			if _, ok := m.clients[client.ID]; ok {
				delete(m.clients, client.ID)
				close(client.Send)
			}
			m.mu.Unlock()
			log.Printf("WebSocket客户端已断开: %s", client.ID)

		case message := <-m.broadcast:
			m.broadcastMessage(message)
		}
	}
}

// 数据收集和广播循环
func (m *Manager) collectAndBroadcast() {
	ticker := time.NewTicker(1 * time.Second) // 每秒收集一次数据
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// 定期广播系统状态
			m.broadcastSystemStatus()
		}
	}
}

// 广播消息到所有订阅的客户端
func (m *Manager) broadcastMessage(message interface{}) {
	data, err := json.Marshal(message)
	if err != nil {
		log.Printf("消息序列化失败: %v", err)
		return
	}

	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, client := range m.clients {
		select {
		case client.Send <- data:
		default:
			// 如果客户端缓冲区满了，关闭连接
			close(client.Send)
			delete(m.clients, client.ID)
		}
	}
}

// 广播系统状态
func (m *Manager) broadcastSystemStatus() {
	// 这里可以添加系统状态收集逻辑
	// 暂时发送心跳消息
	heartbeat := map[string]interface{}{
		"type":      "heartbeat",
		"timestamp": time.Now().Unix(),
		"status":    "ok",
	}
	m.broadcastMessage(heartbeat)
}

// 处理WebSocket升级
func (m *Manager) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := m.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket升级失败: %v", err)
		return
	}

	// 从查询参数获取用户ID
	userID := 0 // 默认值，实际应该从认证中获取
	if userIDStr := r.URL.Query().Get("user_id"); userIDStr != "" {
		// 这里应该验证用户ID的有效性
		// userID = parseUserID(userIDStr)
	}

	client := &Client{
		ID:     generateClientID(),
		Conn:   conn,
		Send:   make(chan []byte, 256),
		UserID: userID,
		Topics: make(map[string]bool),
	}

	// 注册客户端
	m.register <- client

	// 启动读写协程
	go client.writePump(m)
	go client.readPump(m)
}

// 生成客户端ID
func generateClientID() string {
	return "client_" + time.Now().Format("20060102150405") + "_" + randomString(8)
}

// 生成随机字符串
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// 客户端写入协程
func (c *Client) writePump(m *Manager) {
	defer func() {
		c.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			if !ok {
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.Conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}

			w.Write(message)

			if err := w.Close(); err != nil {
				return
			}
		}
	}
}

// 客户端读取协程
func (c *Client) readPump(m *Manager) {
	defer func() {
		m.unregister <- c
		c.Conn.Close()
	}()

	c.Conn.SetReadLimit(512)
	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket读取错误: %v", err)
			}
			break
		}

		// 处理客户端消息（如订阅主题）
		c.handleMessage(message)
	}
}

// 处理客户端消息
func (c *Client) handleMessage(message []byte) {
	var msg map[string]interface{}
	if err := json.Unmarshal(message, &msg); err != nil {
		return
	}

	if msgType, ok := msg["type"].(string); ok {
		switch msgType {
		case "subscribe":
			if topic, ok := msg["topic"].(string); ok {
				c.mu.Lock()
				c.Topics[topic] = true
				c.mu.Unlock()
			}
		case "unsubscribe":
			if topic, ok := msg["topic"].(string); ok {
				c.mu.Lock()
				delete(c.Topics, topic)
				c.mu.Unlock()
			}
		case "ping":
			// 响应ping消息
			response := map[string]interface{}{
				"type":      "pong",
				"timestamp": time.Now().Unix(),
			}
			if data, err := json.Marshal(response); err == nil {
				c.Send <- data
			}
		}
	}
}

// 推送流量数据
func (m *Manager) PushTrafficData(data TrafficData) {
	select {
	case m.trafficCollector <- data:
	default:
		// 如果缓冲区满了，丢弃数据
		log.Printf("流量数据缓冲区已满，丢弃数据")
	}
}

// 推送代理健康数据
func (m *Manager) PushProxyHealthData(data ProxyHealthData) {
	select {
	case m.proxyHealthCollector <- data:
	default:
		log.Printf("代理健康数据缓冲区已满，丢弃数据")
	}
}

// 推送系统性能数据
func (m *Manager) PushSystemPerformanceData(data SystemPerformanceData) {
	select {
	case m.systemCollector <- data:
	default:
		log.Printf("系统性能数据缓冲区已满，丢弃数据")
	}
}

// 获取连接数统计
func (m *Manager) GetConnectionStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := map[string]interface{}{
		"total_clients": len(m.clients),
		"timestamp":     time.Now().Unix(),
	}

	// 按用户ID统计连接数
	userConnections := make(map[int]int)
	for _, client := range m.clients {
		userConnections[client.UserID]++
	}
	stats["user_connections"] = userConnections

	return stats
}
