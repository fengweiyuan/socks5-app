package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

type TrafficStats struct {
	TotalBytesSent    int64 `json:"total_bytes_sent"`
	TotalBytesRecv    int64 `json:"total_bytes_recv"`
	ActiveConnections int   `json:"active_connections"`
	TotalUsers        int64 `json:"total_users"`
	OnlineUsers       int   `json:"online_users"`
}

type RealtimeTraffic struct {
	Timestamp   time.Time `json:"timestamp"`
	BytesSent   int64     `json:"bytes_sent"`
	BytesRecv   int64     `json:"bytes_recv"`
	Connections int       `json:"connections"`
}

type BandwidthLimitRequest struct {
	UserID uint  `json:"user_id" binding:"required"`
	Limit  int64 `json:"limit" binding:"required"`
	Period string `json:"period"`
}

func (s *Server) handleGetTrafficStats(c *gin.Context) {
	var stats TrafficStats

	// 获取总流量统计
	var result struct {
		TotalSent int64
		TotalRecv int64
	}
	database.DB.Model(&database.TrafficLog{}).
		Select("SUM(bytes_sent) as total_sent, SUM(bytes_recv) as total_recv").
		Scan(&result)
	
	stats.TotalBytesSent = result.TotalSent
	stats.TotalBytesRecv = result.TotalRecv

	// 获取活跃连接数
	var activeSessions int64
	database.DB.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Count(&activeSessions)
	stats.ActiveConnections = int(activeSessions)

	// 获取总用户数
	var totalUsers int64
	database.DB.Model(&database.User{}).Count(&totalUsers)
	stats.TotalUsers = totalUsers

	// 获取在线用户数
	var onlineUsers int64
	database.DB.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Distinct("user_id").
		Count(&onlineUsers)
	stats.OnlineUsers = int(onlineUsers)

	c.JSON(http.StatusOK, gin.H{"stats": stats})
}

func (s *Server) handleGetRealtimeTraffic(c *gin.Context) {
	// 获取最近1小时的实时流量数据
	now := time.Now()
	oneHourAgo := now.Add(-1 * time.Hour)

	var logs []database.TrafficLog
	database.DB.Where("timestamp >= ?", oneHourAgo).
		Order("timestamp ASC").
		Find(&logs)

	// 按分钟聚合数据
	trafficMap := make(map[string]*RealtimeTraffic)
	for _, log := range logs {
		key := log.Timestamp.Format("2006-01-02 15:04")
		if traffic, exists := trafficMap[key]; exists {
			traffic.BytesSent += log.BytesSent
			traffic.BytesRecv += log.BytesRecv
		} else {
			trafficMap[key] = &RealtimeTraffic{
				Timestamp: log.Timestamp,
				BytesSent: log.BytesSent,
				BytesRecv: log.BytesRecv,
			}
		}
	}

	// 转换为数组
	var realtimeData []*RealtimeTraffic
	for _, traffic := range trafficMap {
		realtimeData = append(realtimeData, traffic)
	}

	c.JSON(http.StatusOK, gin.H{"realtime_traffic": realtimeData})
}

func (s *Server) handleSetBandwidthLimit(c *gin.Context) {
	var req BandwidthLimitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 检查用户是否存在
	var user database.User
	if err := database.DB.First(&user, req.UserID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 检查是否已存在带宽限制
	var existingLimit database.BandwidthLimit
	if err := database.DB.Where("user_id = ?", req.UserID).First(&existingLimit).Error; err == nil {
		// 更新现有限制
		existingLimit.Limit = req.Limit
		if req.Period != "" {
			existingLimit.Period = req.Period
		}
		if err := database.DB.Save(&existingLimit).Error; err != nil {
			logger.Log.Errorf("更新带宽限制失败: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "更新带宽限制失败"})
			return
		}
	} else {
		// 创建新的带宽限制
		bandwidthLimit := &database.BandwidthLimit{
			UserID: req.UserID,
			Limit:  req.Limit,
			Period: req.Period,
		}
		if err := database.DB.Create(bandwidthLimit).Error; err != nil {
			logger.Log.Errorf("创建带宽限制失败: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "创建带宽限制失败"})
			return
		}
	}

	// 同时更新用户的带宽限制字段
	user.BandwidthLimit = req.Limit
	database.DB.Save(&user)

	logger.Log.Infof("设置用户 %s 的带宽限制: %d bytes/s", user.Username, req.Limit)
	c.JSON(http.StatusOK, gin.H{"message": "带宽限制设置成功"})
}
