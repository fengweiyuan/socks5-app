package heartbeat

import (
	"fmt"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"socks5-app/internal/config"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

// HeartbeatService 心跳服务
type HeartbeatService struct {
	proxyID     string
	proxyHost   string
	proxyPort   string
	interval    time.Duration
	stopCh      chan struct{}
	mu          sync.RWMutex
	totalConns  int64
	activeConns int32
	isRunning   bool
}

// NewHeartbeatService 创建心跳服务实例
func NewHeartbeatService() *HeartbeatService {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}

	proxyConfig := &config.GlobalConfig.Proxy
	proxyID := fmt.Sprintf("%s:%s", hostname, proxyConfig.Port)

	return &HeartbeatService{
		proxyID:   proxyID,
		proxyHost: proxyConfig.Host,
		proxyPort: proxyConfig.Port,
		interval:  time.Duration(proxyConfig.HeartbeatInterval) * time.Second,
		stopCh:    make(chan struct{}),
	}
}

// Start 启动心跳服务
func (h *HeartbeatService) Start() {
	h.mu.Lock()
	if h.isRunning {
		h.mu.Unlock()
		return
	}
	h.isRunning = true
	h.mu.Unlock()

	logger.Log.Infof("启动心跳服务，间隔: %v", h.interval)

	// 立即发送一次心跳
	h.sendHeartbeat()

	// 启动定时心跳
	go h.heartbeatLoop()
}

// Stop 停止心跳服务
func (h *HeartbeatService) Stop() {
	h.mu.Lock()
	if !h.isRunning {
		h.mu.Unlock()
		return
	}
	h.isRunning = false
	h.mu.Unlock()

	close(h.stopCh)

	// 发送下线心跳
	h.sendOfflineHeartbeat()

	logger.Log.Info("心跳服务已停止")
}

// IncrementConnection 增加连接计数
func (h *HeartbeatService) IncrementConnection() {
	atomic.AddInt32(&h.activeConns, 1)
	atomic.AddInt64(&h.totalConns, 1)
}

// DecrementConnection 减少连接计数
func (h *HeartbeatService) DecrementConnection() {
	atomic.AddInt32(&h.activeConns, -1)
}

// heartbeatLoop 心跳循环
func (h *HeartbeatService) heartbeatLoop() {
	ticker := time.NewTicker(h.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			h.sendHeartbeat()
		case <-h.stopCh:
			return
		}
	}
}

// sendHeartbeat 发送心跳
func (h *HeartbeatService) sendHeartbeat() {
	// 如果数据库连接失败，不影响正常服务，只记录日志
	if database.DB == nil {
		logger.Log.Warn("数据库连接不可用，跳过心跳上报")
		return
	}

	activeConns := atomic.LoadInt32(&h.activeConns)
	totalConns := atomic.LoadInt64(&h.totalConns)

	heartbeat := &database.ProxyHeartbeat{
		ProxyID:       h.proxyID,
		ProxyHost:     h.proxyHost,
		ProxyPort:     h.proxyPort,
		Status:        "online",
		ActiveConns:   int(activeConns),
		TotalConns:    totalConns,
		LastHeartbeat: time.Now(),
	}

	// 尝试更新现有记录，如果不存在则创建新记录
	var existingHeartbeat database.ProxyHeartbeat
	result := database.DB.Where("proxy_id = ?", h.proxyID).First(&existingHeartbeat)

	if result.Error != nil {
		// 记录不存在，创建新记录
		if err := database.DB.Create(heartbeat).Error; err != nil {
			logger.Log.Errorf("创建心跳记录失败: %v", err)
			return
		}
		logger.Log.Debugf("创建心跳记录成功 - ProxyID: %s, 活跃连接: %d, 总连接: %d",
			h.proxyID, activeConns, totalConns)
	} else {
		// 记录存在，更新记录
		updates := map[string]interface{}{
			"proxy_host":     h.proxyHost,
			"proxy_port":     h.proxyPort,
			"status":         "online",
			"active_conns":   int(activeConns),
			"total_conns":    totalConns,
			"last_heartbeat": time.Now(),
		}

		if err := database.DB.Model(&existingHeartbeat).Updates(updates).Error; err != nil {
			logger.Log.Errorf("更新心跳记录失败: %v", err)
			return
		}
		logger.Log.Debugf("更新心跳记录成功 - ProxyID: %s, 活跃连接: %d, 总连接: %d",
			h.proxyID, activeConns, totalConns)
	}
}

// sendOfflineHeartbeat 发送下线心跳
func (h *HeartbeatService) sendOfflineHeartbeat() {
	// 如果数据库连接失败，不影响正常服务
	if database.DB == nil {
		logger.Log.Warn("数据库连接不可用，跳过下线心跳上报")
		return
	}

	var existingHeartbeat database.ProxyHeartbeat
	result := database.DB.Where("proxy_id = ?", h.proxyID).First(&existingHeartbeat)

	if result.Error == nil {
		updates := map[string]interface{}{
			"status":         "offline",
			"last_heartbeat": time.Now(),
		}

		if err := database.DB.Model(&existingHeartbeat).Updates(updates).Error; err != nil {
			logger.Log.Errorf("更新下线心跳记录失败: %v", err)
		} else {
			logger.Log.Infof("发送下线心跳成功 - ProxyID: %s", h.proxyID)
		}
	}
}

// GetStats 获取统计信息
func (h *HeartbeatService) GetStats() (int32, int64) {
	return atomic.LoadInt32(&h.activeConns), atomic.LoadInt64(&h.totalConns)
}
