package api

import (
	"github.com/gin-gonic/gin"
)

// Gin兼容的WebSocket处理器函数

// HandleWebSocketGin 处理WebSocket连接的Gin版本
func (h *WebSocketHandler) HandleWebSocketGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.HandleWebSocket(w, r)
}

// GetConnectionStatsGin 获取WebSocket连接统计的Gin版本
func (h *WebSocketHandler) GetConnectionStatsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.GetConnectionStats(w, r)
}

// GetStatusGin 获取WebSocket状态的Gin版本
func (h *WebSocketHandler) GetStatusGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.GetStatus(w, r)
}

// PushTestDataGin 推送测试数据的Gin版本
func (h *WebSocketHandler) PushTestDataGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.PushTestData(w, r)
}
