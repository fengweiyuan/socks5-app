package traffic

import (
	"context"
	"fmt"
	"sync"
	"time"

	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

// TrafficController 流量控制器
type TrafficController struct {
	// 用户带宽限制缓存
	userLimits map[uint]*UserLimit
	mu         sync.RWMutex

	// 流量统计
	userStats map[uint]*UserStats
	statsMu   sync.RWMutex

	// 控制通道
	stopChan chan struct{}

	// 配置
	updateInterval time.Duration
}

// UserLimit 用户带宽限制
type UserLimit struct {
	UserID         uint      `json:"user_id"`
	BandwidthLimit int64     `json:"bandwidth_limit"` // 字节/秒，0表示无限制
	Period         string    `json:"period"`          // daily, monthly
	Enabled        bool      `json:"enabled"`
	LastUpdate     time.Time `json:"last_update"`
}

// UserStats 用户流量统计
type UserStats struct {
	UserID       uint      `json:"user_id"`
	CurrentSpeed int64     `json:"current_speed"` // 当前速度（字节/秒）
	TotalBytes   int64     `json:"total_bytes"`   // 总流量（字节）
	SessionBytes int64     `json:"session_bytes"` // 当前会话流量
	LastActivity time.Time `json:"last_activity"`
	IsThrottled  bool      `json:"is_throttled"` // 是否被限速
}

// NewTrafficController 创建流量控制器
func NewTrafficController() *TrafficController {
	return &TrafficController{
		userLimits:     make(map[uint]*UserLimit),
		userStats:      make(map[uint]*UserStats),
		stopChan:       make(chan struct{}),
		updateInterval: 5 * time.Second, // 每5秒更新一次
	}
}

// Start 启动流量控制器
func (tc *TrafficController) Start() {
	logger.Log.Info("启动流量控制器")

	// 初始化用户限制
	tc.loadUserLimits()

	// 启动更新协程
	go tc.updateLoop()

	// 启动统计清理协程
	go tc.cleanupLoop()
}

// Stop 停止流量控制器
func (tc *TrafficController) Stop() {
	logger.Log.Info("停止流量控制器")
	close(tc.stopChan)
}

// loadUserLimits 加载用户带宽限制
func (tc *TrafficController) loadUserLimits() {
	if database.DB == nil {
		logger.Log.Warn("数据库连接不可用，跳过加载用户限制")
		return
	}

	var users []database.User
	if err := database.DB.Where("status = ?", "active").Find(&users).Error; err != nil {
		logger.Log.Errorf("加载用户列表失败: %v", err)
		return
	}

	tc.mu.Lock()
	defer tc.mu.Unlock()

	for _, user := range users {
		// 检查是否有专门的带宽限制记录
		var bandwidthLimit database.BandwidthLimit
		if err := database.DB.Where("user_id = ? AND enabled = ?", user.ID, true).First(&bandwidthLimit).Error; err == nil {
			// 使用专门的带宽限制记录
			tc.userLimits[user.ID] = &UserLimit{
				UserID:         user.ID,
				BandwidthLimit: bandwidthLimit.Limit,
				Period:         bandwidthLimit.Period,
				Enabled:        bandwidthLimit.Enabled,
				LastUpdate:     time.Now(),
			}
		} else {
			// 使用用户表中的带宽限制字段
			tc.userLimits[user.ID] = &UserLimit{
				UserID:         user.ID,
				BandwidthLimit: user.BandwidthLimit,
				Period:         "daily", // 默认日限制
				Enabled:        user.BandwidthLimit > 0,
				LastUpdate:     time.Now(),
			}
		}
	}

	logger.Log.Infof("加载了 %d 个用户的带宽限制", len(tc.userLimits))
}

// GetUserLimit 获取用户带宽限制
func (tc *TrafficController) GetUserLimit(userID uint) *UserLimit {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	return tc.userLimits[userID]
}

// SetUserLimit 设置用户带宽限制
func (tc *TrafficController) SetUserLimit(userID uint, limit int64, period string) error {
	if database.DB == nil {
		return fmt.Errorf("数据库连接不可用")
	}

	// 更新数据库
	bandwidthLimit := &database.BandwidthLimit{
		UserID:  userID,
		Limit:   limit,
		Period:  period,
		Enabled: limit > 0,
	}

	// 使用 Upsert 操作
	if err := database.DB.Where("user_id = ?", userID).Assign(bandwidthLimit).FirstOrCreate(bandwidthLimit).Error; err != nil {
		return fmt.Errorf("更新用户带宽限制失败: %v", err)
	}

	// 更新缓存
	tc.mu.Lock()
	tc.userLimits[userID] = &UserLimit{
		UserID:         userID,
		BandwidthLimit: limit,
		Period:         period,
		Enabled:        limit > 0,
		LastUpdate:     time.Now(),
	}
	tc.mu.Unlock()

	logger.Log.Infof("设置用户 %d 的带宽限制为 %d 字节/秒", userID, limit)
	return nil
}

// RecordTraffic 记录用户流量
func (tc *TrafficController) RecordTraffic(userID uint, bytes int64) {
	tc.statsMu.Lock()
	defer tc.statsMu.Unlock()

	stats, exists := tc.userStats[userID]
	if !exists {
		stats = &UserStats{
			UserID:       userID,
			LastActivity: time.Now(),
		}
		tc.userStats[userID] = stats
	}

	stats.TotalBytes += bytes
	stats.SessionBytes += bytes
	stats.LastActivity = time.Now()
}

// CheckBandwidthLimit 检查用户是否超过带宽限制
func (tc *TrafficController) CheckBandwidthLimit(userID uint) (bool, int64) {
	tc.mu.RLock()
	limit, exists := tc.userLimits[userID]
	tc.mu.RUnlock()

	if !exists || !limit.Enabled || limit.BandwidthLimit <= 0 {
		return false, 0 // 无限制
	}

	tc.statsMu.RLock()
	stats, exists := tc.userStats[userID]
	tc.statsMu.RUnlock()

	if !exists {
		return false, 0 // 无统计数据，允许通过
	}

	// 计算当前速度（基于最近的活动）
	now := time.Now()
	timeDiff := now.Sub(stats.LastActivity).Seconds()
	if timeDiff < 1 {
		timeDiff = 1 // 最小时间间隔1秒
	}

	currentSpeed := int64(float64(stats.SessionBytes) / timeDiff)

	// 检查是否超过限制
	if currentSpeed > limit.BandwidthLimit {
		stats.IsThrottled = true
		return true, limit.BandwidthLimit // 需要限速
	}

	stats.IsThrottled = false
	return false, limit.BandwidthLimit
}

// GetUserStats 获取用户流量统计
func (tc *TrafficController) GetUserStats(userID uint) *UserStats {
	tc.statsMu.RLock()
	defer tc.statsMu.RUnlock()

	return tc.userStats[userID]
}

// GetAllUserStats 获取所有用户流量统计
func (tc *TrafficController) GetAllUserStats() map[uint]*UserStats {
	tc.statsMu.RLock()
	defer tc.statsMu.RUnlock()

	result := make(map[uint]*UserStats)
	for userID, stats := range tc.userStats {
		result[userID] = stats
	}
	return result
}

// updateLoop 更新循环
func (tc *TrafficController) updateLoop() {
	ticker := time.NewTicker(tc.updateInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			tc.updateUserStats()
		case <-tc.stopChan:
			return
		}
	}
}

// updateUserStats 更新用户统计
func (tc *TrafficController) updateUserStats() {
	tc.statsMu.Lock()
	defer tc.statsMu.Unlock()

	now := time.Now()
	for userID, stats := range tc.userStats {
		// 计算当前速度
		timeDiff := now.Sub(stats.LastActivity).Seconds()
		if timeDiff > 0 {
			stats.CurrentSpeed = int64(float64(stats.SessionBytes) / timeDiff)
		}

		// 检查带宽限制
		tc.mu.RLock()
		limit, exists := tc.userLimits[userID]
		tc.mu.RUnlock()

		if exists && limit.Enabled && limit.BandwidthLimit > 0 {
			stats.IsThrottled = stats.CurrentSpeed > limit.BandwidthLimit
		}
	}
}

// cleanupLoop 清理循环
func (tc *TrafficController) cleanupLoop() {
	ticker := time.NewTicker(1 * time.Minute) // 每分钟清理一次
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			tc.cleanupOldStats()
		case <-tc.stopChan:
			return
		}
	}
}

// cleanupOldStats 清理旧的统计数据
func (tc *TrafficController) cleanupOldStats() {
	tc.statsMu.Lock()
	defer tc.statsMu.Unlock()

	now := time.Now()
	cutoff := now.Add(-1 * time.Hour) // 清理1小时前的数据

	for _, stats := range tc.userStats {
		if stats.LastActivity.Before(cutoff) {
			// 重置会话统计，保留总统计
			stats.SessionBytes = 0
			stats.CurrentSpeed = 0
			stats.IsThrottled = false
		}
	}
}

// ThrottleConnection 限速连接
func (tc *TrafficController) ThrottleConnection(ctx context.Context, userID uint, bytes int64) error {
	// 检查带宽限制
	shouldThrottle, limit := tc.CheckBandwidthLimit(userID)
	if !shouldThrottle {
		return nil // 不需要限速
	}

	// 计算需要等待的时间
	// 假设我们要将速度限制在 limit 字节/秒
	waitTime := time.Duration(float64(bytes) / float64(limit) * float64(time.Second))

	if waitTime > 100*time.Millisecond {
		// 如果等待时间超过100ms，则进行限速
		select {
		case <-time.After(waitTime):
			return nil
		case <-ctx.Done():
			return ctx.Err()
		}
	}

	return nil
}
