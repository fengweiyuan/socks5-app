package api

import (
	"net/http"
	"strconv"
	"time"

	"socks5-app/internal/database"
	"socks5-app/internal/logger"

	"github.com/gin-gonic/gin"
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
	UserID uint   `json:"user_id" binding:"required"`
	Limit  int64  `json:"limit" binding:"required"`
	Period string `json:"period"`
}

func (s *Server) handleGetTrafficStats(c *gin.Context) {
	var stats TrafficStats

	// 获取总流量统计
	var result struct {
		TotalSent *int64 `json:"total_sent"`
		TotalRecv *int64 `json:"total_recv"`
	}

	// 使用事务确保数据一致性
	tx := database.DB.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	err := tx.Model(&database.TrafficLog{}).
		Select("COALESCE(SUM(bytes_sent), 0) as total_sent, COALESCE(SUM(bytes_recv), 0) as total_recv").
		Scan(&result).Error

	if err != nil {
		logger.Log.Errorf("获取流量统计失败: %v", err)
		// 即使查询失败，也返回默认值
		stats.TotalBytesSent = 0
		stats.TotalBytesRecv = 0
	} else {
		// 处理可能为 NULL 的值
		if result.TotalSent != nil {
			stats.TotalBytesSent = *result.TotalSent
		} else {
			stats.TotalBytesSent = 0
		}

		if result.TotalRecv != nil {
			stats.TotalBytesRecv = *result.TotalRecv
		} else {
			stats.TotalBytesRecv = 0
		}
	}

	// 获取活跃连接数
	var activeSessions int64
	if err := tx.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Count(&activeSessions).Error; err != nil {
		logger.Log.Errorf("获取活跃连接数失败: %v", err)
		stats.ActiveConnections = 0
	} else {
		stats.ActiveConnections = int(activeSessions)
	}

	// 获取总用户数
	var totalUsers int64
	if err := tx.Model(&database.User{}).Count(&totalUsers).Error; err != nil {
		logger.Log.Errorf("获取总用户数失败: %v", err)
		stats.TotalUsers = 0
	} else {
		stats.TotalUsers = totalUsers
	}

	// 获取在线用户数
	var onlineUsers int64
	if err := tx.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Distinct("user_id").
		Count(&onlineUsers).Error; err != nil {
		logger.Log.Errorf("获取在线用户数失败: %v", err)
		stats.OnlineUsers = 0
	} else {
		stats.OnlineUsers = int(onlineUsers)
	}

	tx.Commit()

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

// BandwidthLimitResponse 带宽限制响应
type BandwidthLimitResponse struct {
	ID        uint   `json:"id"`
	UserID    uint   `json:"user_id"`
	Username  string `json:"username"`
	Limit     int64  `json:"limit"`
	Period    string `json:"period"`
	Enabled   bool   `json:"enabled"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

// handleGetBandwidthLimits 获取所有用户的带宽限制
func (s *Server) handleGetBandwidthLimits(c *gin.Context) {
	var limits []database.BandwidthLimit
	if err := database.DB.Preload("User").Find(&limits).Error; err != nil {
		logger.Log.Errorf("获取带宽限制失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取带宽限制失败"})
		return
	}

	var response []BandwidthLimitResponse
	for _, limit := range limits {
		response = append(response, BandwidthLimitResponse{
			ID:        limit.ID,
			UserID:    limit.UserID,
			Username:  limit.User.Username,
			Limit:     limit.Limit,
			Period:    limit.Period,
			Enabled:   limit.Enabled,
			CreatedAt: limit.CreatedAt.Format("2006-01-02 15:04:05"),
			UpdatedAt: limit.UpdatedAt.Format("2006-01-02 15:04:05"),
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  response,
		"total": len(response),
	})
}

// handleUpdateBandwidthLimit 更新用户带宽限制
func (s *Server) handleUpdateBandwidthLimit(c *gin.Context) {
	userIDStr := c.Param("user_id")
	userID, err := strconv.ParseUint(userIDStr, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	var req struct {
		Limit  int64  `json:"limit" binding:"required,min=0"`
		Period string `json:"period" binding:"required,oneof=daily monthly"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 检查用户是否存在
	var user database.User
	if err := database.DB.First(&user, uint(userID)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 更新带宽限制
	var bandwidthLimit database.BandwidthLimit
	if err := database.DB.Where("user_id = ?", uint(userID)).First(&bandwidthLimit).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "带宽限制不存在"})
		return
	}

	bandwidthLimit.Limit = req.Limit
	bandwidthLimit.Period = req.Period
	bandwidthLimit.Enabled = req.Limit > 0

	if err := database.DB.Save(&bandwidthLimit).Error; err != nil {
		logger.Log.Errorf("更新用户带宽限制失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新带宽限制失败"})
		return
	}

	// 同时更新用户的带宽限制字段
	user.BandwidthLimit = req.Limit
	database.DB.Save(&user)

	c.JSON(http.StatusOK, gin.H{
		"message": "带宽限制更新成功",
		"data": BandwidthLimitResponse{
			ID:        bandwidthLimit.ID,
			UserID:    bandwidthLimit.UserID,
			Username:  user.Username,
			Limit:     bandwidthLimit.Limit,
			Period:    bandwidthLimit.Period,
			Enabled:   bandwidthLimit.Enabled,
			CreatedAt: bandwidthLimit.CreatedAt.Format("2006-01-02 15:04:05"),
			UpdatedAt: bandwidthLimit.UpdatedAt.Format("2006-01-02 15:04:05"),
		},
	})
}

// handleDeleteBandwidthLimit 删除用户带宽限制
func (s *Server) handleDeleteBandwidthLimit(c *gin.Context) {
	userIDStr := c.Param("user_id")
	userID, err := strconv.ParseUint(userIDStr, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	// 删除带宽限制
	if err := database.DB.Where("user_id = ?", uint(userID)).Delete(&database.BandwidthLimit{}).Error; err != nil {
		logger.Log.Errorf("删除用户带宽限制失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除带宽限制失败"})
		return
	}

	// 重置用户的带宽限制字段
	var user database.User
	if err := database.DB.First(&user, uint(userID)).Error; err == nil {
		user.BandwidthLimit = 0
		database.DB.Save(&user)
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "带宽限制删除成功",
	})
}
