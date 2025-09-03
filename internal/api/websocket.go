package api

import (
	"net/http"
	"time"

	"socks5-app/internal/websocket"
)

// WebSocket处理器
type WebSocketHandler struct {
	wsManager *websocket.Manager
}

// 创建新的WebSocket处理器
func NewWebSocketHandler(wsManager *websocket.Manager) *WebSocketHandler {
	return &WebSocketHandler{
		wsManager: wsManager,
	}
}

// 处理WebSocket连接
func (h *WebSocketHandler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	// 验证用户身份（这里应该从JWT token中获取）
	userID := h.extractUserIDFromRequest(r)

	// 设置用户ID到查询参数中
	q := r.URL.Query()
	q.Set("user_id", userID)
	r.URL.RawQuery = q.Encode()

	// 处理WebSocket升级
	h.wsManager.HandleWebSocket(w, r)
}

// 从请求中提取用户ID
func (h *WebSocketHandler) extractUserIDFromRequest(r *http.Request) string {
	// 从JWT token中提取用户ID
	// 这里应该实现JWT验证逻辑
	// 暂时返回默认值

	// 从Authorization header中获取token
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" {
		// 解析JWT token并提取用户ID
		// userID := parseJWTToken(authHeader)
		// return userID
	}

	// 从查询参数中获取用户ID（临时方案）
	if userID := r.URL.Query().Get("user_id"); userID != "" {
		return userID
	}

	return "0" // 默认用户ID
}

// 获取WebSocket连接统计
func (h *WebSocketHandler) GetConnectionStats(w http.ResponseWriter, r *http.Request) {
	stats := h.wsManager.GetConnectionStats()

	// 返回JSON响应
	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    stats,
	})
}

// 推送测试数据
func (h *WebSocketHandler) PushTestData(w http.ResponseWriter, r *http.Request) {
	// 推送测试流量数据
	testTrafficData := websocket.TrafficData{
		UserID:          1,
		ClientIP:        "192.168.1.100",
		BytesSent:       1024,
		BytesRecv:       2048,
		Speed:           3.0,
		Bandwidth:       0.3,
		Timestamp:       time.Now().Unix(),
		ConnectionCount: 1,
	}

	h.wsManager.PushTrafficData(testTrafficData)

	// 推送测试代理健康数据
	testProxyHealthData := websocket.ProxyHealthData{
		ProxyID:       "test-proxy-1",
		Status:        "online",
		ActiveConns:   5,
		TotalConns:    100,
		Uptime:        3600,
		LastHeartbeat: time.Now().Unix(),
		Load:          25.5,
	}

	h.wsManager.PushProxyHealthData(testProxyHealthData)

	// 推送测试系统性能数据
	testSystemData := websocket.SystemPerformanceData{
		CPUUsage:    15.2,
		MemoryUsage: 45.8,
		DiskUsage:   32.1,
		NetworkIn:   1024 * 1024, // 1MB/s
		NetworkOut:  2048 * 1024, // 2MB/s
		Timestamp:   time.Now().Unix(),
	}

	h.wsManager.PushSystemPerformanceData(testSystemData)

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success":   true,
		"message":   "测试数据推送成功",
		"timestamp": time.Now().Unix(),
	})
}

// 获取WebSocket状态
func (h *WebSocketHandler) GetStatus(w http.ResponseWriter, r *http.Request) {
	status := map[string]interface{}{
		"service":     "websocket",
		"status":      "running",
		"timestamp":   time.Now().Unix(),
		"connections": h.wsManager.GetConnectionStats(),
	}

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    status,
	})
}
