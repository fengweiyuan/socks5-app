package api

import (
	"net/http"
	"runtime"
	"time"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
)

type SystemStatus struct {
	Uptime       string  `json:"uptime"`
	MemoryUsage  float64 `json:"memory_usage"`
	CPUUsage     float64 `json:"cpu_usage"`
	ActiveUsers  int     `json:"active_users"`
	TotalUsers   int64   `json:"total_users"`
	TotalTraffic int64   `json:"total_traffic"`
}

type SystemStats struct {
	TotalBytesSent    int64 `json:"total_bytes_sent"`
	TotalBytesRecv    int64 `json:"total_bytes_recv"`
	ActiveConnections int   `json:"active_connections"`
	TotalSessions     int64 `json:"total_sessions"`
	TotalLogs         int64 `json:"total_logs"`
}

var startTime = time.Now()

func (s *Server) handleGetSystemStatus(c *gin.Context) {
	// 获取系统内存使用情况
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	memoryUsage := float64(m.Alloc) / float64(m.Sys) * 100

	// 获取活跃用户数
	var activeUsers int64
	database.DB.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Count(&activeUsers)

	// 获取总用户数
	var totalUsers int64
	database.DB.Model(&database.User{}).Count(&totalUsers)

	// 获取总流量
	var result struct {
		TotalSent int64
		TotalRecv int64
	}
	database.DB.Model(&database.TrafficLog{}).
		Select("SUM(bytes_sent) as total_sent, SUM(bytes_recv) as total_recv").
		Scan(&result)

	status := SystemStatus{
		Uptime:       time.Since(startTime).String(),
		MemoryUsage:  memoryUsage,
		CPUUsage:     0, // 这里可以添加CPU使用率监控
		ActiveUsers:  int(activeUsers),
		TotalUsers:   totalUsers,
		TotalTraffic: result.TotalSent + result.TotalRecv,
	}

	c.JSON(http.StatusOK, gin.H{"status": status})
}

func (s *Server) handleGetSystemStats(c *gin.Context) {
	var stats SystemStats

	// 获取流量统计
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
	var activeConnections int64
	database.DB.Model(&database.ProxySession{}).
		Where("status = ?", "active").
		Count(&activeConnections)
	stats.ActiveConnections = int(activeConnections)

	// 获取总会话数
	database.DB.Model(&database.ProxySession{}).Count(&stats.TotalSessions)

	// 获取总日志数
	database.DB.Model(&database.AccessLog{}).Count(&stats.TotalLogs)

	c.JSON(http.StatusOK, gin.H{"stats": stats})
}
