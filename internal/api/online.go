package api

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

func (s *Server) handleGetOnlineUsers(c *gin.Context) {
	// 获取活跃的代理会话
	var sessions []database.ProxySession
	if err := database.DB.Preload("User").
		Where("status = ?", "active").
		Order("start_time DESC").
		Find(&sessions).Error; err != nil {
		logger.Log.Errorf("获取在线用户失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取在线用户失败"})
		return
	}

	// 转换为前端需要的格式
	var onlineUsers []map[string]interface{}
	for _, session := range sessions {
		onlineUsers = append(onlineUsers, map[string]interface{}{
			"id":         session.ID,
			"username":   session.User.Username,
			"clientIP":   session.ClientIP,
			"startTime":  session.StartTime,
			"bytesSent":  session.BytesSent,
			"bytesRecv":  session.BytesRecv,
			"duration":   session.StartTime.Format("15:04:05"),
		})
	}

	c.JSON(http.StatusOK, gin.H{"online_users": onlineUsers})
}

func (s *Server) handleDisconnectUser(c *gin.Context) {
	// 这里可以实现强制断开用户连接的功能
	// 由于SOCKS5代理的特性，我们需要在代理服务器层面处理断开连接
	
	sessionID := c.Param("id")
	if sessionID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的会话ID"})
		return
	}

	// 更新会话状态为已断开
	if err := database.DB.Model(&database.ProxySession{}).
		Where("id = ?", sessionID).
		Update("status", "disconnected").Error; err != nil {
		logger.Log.Errorf("断开用户连接失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "断开用户连接失败"})
		return
	}

	logger.Log.Infof("用户会话已断开: %s", sessionID)
	c.JSON(http.StatusOK, gin.H{"message": "用户已断开连接"})
}
