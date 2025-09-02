package api

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
)

// ProxyHealthResponse 代理健康状态响应
type ProxyHealthResponse struct {
	Status      string                `json:"status"`       // overall, online, offline, degraded
	Message     string                `json:"message"`      // 状态描述
	ProxyServers []ProxyServerStatus  `json:"proxy_servers"` // 代理服务器列表
	Summary     ProxyHealthSummary    `json:"summary"`      // 健康状态汇总
}

// ProxyServerStatus 代理服务器状态
type ProxyServerStatus struct {
	ProxyID       string    `json:"proxy_id"`
	ProxyHost     string    `json:"proxy_host"`
	ProxyPort     string    `json:"proxy_port"`
	Status        string    `json:"status"`
	ActiveConns   int       `json:"active_conns"`
	TotalConns    int64     `json:"total_conns"`
	LastHeartbeat time.Time `json:"last_heartbeat"`
	IsHealthy     bool      `json:"is_healthy"`
	HealthMessage string    `json:"health_message"`
}

// ProxyHealthSummary 健康状态汇总
type ProxyHealthSummary struct {
	TotalServers    int   `json:"total_servers"`
	OnlineServers   int   `json:"online_servers"`
	OfflineServers  int   `json:"offline_servers"`
	TotalActiveConns int  `json:"total_active_conns"`
	TotalConns      int64 `json:"total_conns"`
}

// HeartbeatRecordsResponse 心跳记录响应
type HeartbeatRecordsResponse struct {
	Records    []database.ProxyHeartbeat `json:"records"`
	Total      int64                     `json:"total"`
	Page       int                       `json:"page"`
	PageSize   int                       `json:"page_size"`
	TotalPages int                       `json:"total_pages"`
}

// handleGetProxyHealth 获取代理健康状态
func (s *Server) handleGetProxyHealth(c *gin.Context) {
	// 如果数据库连接不可用，返回基本状态
	if database.DB == nil {
		c.JSON(http.StatusOK, gin.H{
			"status":  "degraded",
			"message": "数据库连接不可用，无法获取详细健康状态",
			"proxy_servers": []ProxyServerStatus{},
			"summary": ProxyHealthSummary{
				TotalServers:    0,
				OnlineServers:   0,
				OfflineServers:  0,
				TotalActiveConns: 0,
				TotalConns:      0,
			},
		})
		return
	}

	var heartbeats []database.ProxyHeartbeat
	if err := database.DB.Order("last_heartbeat DESC").Find(&heartbeats).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询心跳记录失败",
		})
		return
	}

	// 计算健康状态
	now := time.Now()
	var proxyServers []ProxyServerStatus
	var summary ProxyHealthSummary
	
	// 用于去重的map，因为可能有多个心跳记录
	proxyMap := make(map[string]*database.ProxyHeartbeat)
	
	// 获取每个代理服务器的最新心跳记录
	for _, heartbeat := range heartbeats {
		if existing, exists := proxyMap[heartbeat.ProxyID]; !exists || heartbeat.LastHeartbeat.After(existing.LastHeartbeat) {
			heartbeat := heartbeat // 创建副本
			proxyMap[heartbeat.ProxyID] = &heartbeat
		}
	}

	summary.TotalServers = len(proxyMap)
	
	for _, heartbeat := range proxyMap {
		// 判断服务器是否健康（30秒内有心跳认为健康）
		isHealthy := now.Sub(heartbeat.LastHeartbeat) <= 30*time.Second
		healthMessage := "正常"
		status := heartbeat.Status
		
		if !isHealthy {
			healthMessage = "心跳超时"
			status = "offline"
		}
		
		if status == "online" {
			summary.OnlineServers++
		} else {
			summary.OfflineServers++
		}
		
		summary.TotalActiveConns += heartbeat.ActiveConns
		summary.TotalConns += heartbeat.TotalConns
		
		proxyServers = append(proxyServers, ProxyServerStatus{
			ProxyID:       heartbeat.ProxyID,
			ProxyHost:     heartbeat.ProxyHost,
			ProxyPort:     heartbeat.ProxyPort,
			Status:        status,
			ActiveConns:   heartbeat.ActiveConns,
			TotalConns:    heartbeat.TotalConns,
			LastHeartbeat: heartbeat.LastHeartbeat,
			IsHealthy:     isHealthy,
			HealthMessage: healthMessage,
		})
	}

	// 计算整体状态
	overallStatus := "online"
	message := "所有代理服务器运行正常"
	
	if summary.OnlineServers == 0 {
		overallStatus = "offline"
		message = "所有代理服务器离线"
	} else if summary.OfflineServers > 0 {
		overallStatus = "degraded"
		message = "部分代理服务器离线"
	}

	c.JSON(http.StatusOK, ProxyHealthResponse{
		Status:       overallStatus,
		Message:      message,
		ProxyServers: proxyServers,
		Summary:      summary,
	})
}

// handleGetHeartbeatRecords 获取心跳记录
func (s *Server) handleGetHeartbeatRecords(c *gin.Context) {
	// 如果数据库连接不可用
	if database.DB == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": "数据库连接不可用",
		})
		return
	}

	// 获取分页参数
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	proxyID := c.Query("proxy_id")

	if page < 1 {
		page = 1
	}
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	offset := (page - 1) * pageSize

	// 构建查询
	query := database.DB.Model(&database.ProxyHeartbeat{})
	if proxyID != "" {
		query = query.Where("proxy_id = ?", proxyID)
	}

	// 获取总数
	var total int64
	if err := query.Count(&total).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询心跳记录总数失败",
		})
		return
	}

	// 获取记录
	var records []database.ProxyHeartbeat
	if err := query.Order("last_heartbeat DESC").
		Offset(offset).
		Limit(pageSize).
		Find(&records).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询心跳记录失败",
		})
		return
	}

	totalPages := int((total + int64(pageSize) - 1) / int64(pageSize))

	c.JSON(http.StatusOK, HeartbeatRecordsResponse{
		Records:    records,
		Total:      total,
		Page:       page,
		PageSize:   pageSize,
		TotalPages: totalPages,
	})
}

// handleGetProxyStatus 获取代理状态概览
func (s *Server) handleGetProxyStatus(c *gin.Context) {
	// 如果数据库连接不可用
	if database.DB == nil {
		c.JSON(http.StatusOK, gin.H{
			"database_connected": false,
			"message": "数据库连接不可用，代理服务正常运行",
			"proxy_running": true,
		})
		return
	}

	// 获取最近的心跳记录
	var recentHeartbeats []database.ProxyHeartbeat
	if err := database.DB.Where("last_heartbeat > ?", time.Now().Add(-5*time.Minute)).
		Order("last_heartbeat DESC").
		Find(&recentHeartbeats).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询最近心跳记录失败",
		})
		return
	}

	// 统计活跃代理服务器
	activeProxies := make(map[string]bool)
	totalActiveConns := 0
	var totalConns int64

	for _, heartbeat := range recentHeartbeats {
		if time.Since(heartbeat.LastHeartbeat) <= 30*time.Second {
			activeProxies[heartbeat.ProxyID] = true
			totalActiveConns += heartbeat.ActiveConns
			if heartbeat.TotalConns > totalConns {
				totalConns = heartbeat.TotalConns
			}
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"database_connected":  true,
		"active_proxy_count":  len(activeProxies),
		"total_active_conns":  totalActiveConns,
		"total_conns":        totalConns,
		"last_update":        time.Now(),
	})
}
