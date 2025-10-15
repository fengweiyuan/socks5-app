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
	Enabled        bool      `json:"enabled"`
	LastUpdate     time.Time `json:"last_update"`

	// 令牌桶相关字段
	tokens     float64   // 当前令牌数
	lastRefill time.Time // 上次填充令牌的时间
	mu         sync.Mutex
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

	// 启动带宽限制重新加载协程
	go tc.reloadLimitsLoop()
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

	updatedCount := 0
	newCount := 0

	for _, user := range users {
		// 确定要使用的带宽限制值
		var limitValue int64
		var enabled bool

		// 检查是否有专门的带宽限制记录
		var bandwidthLimit database.BandwidthLimit
		if err := database.DB.Where("user_id = ? AND enabled = ?", user.ID, true).First(&bandwidthLimit).Error; err == nil {
			// 使用专门的带宽限制记录
			limitValue = bandwidthLimit.Limit
			enabled = bandwidthLimit.Enabled
		} else {
			// 使用用户表中的带宽限制字段
			limitValue = user.BandwidthLimit
			enabled = user.BandwidthLimit > 0
		}

		// 检查是否已存在限制配置
		existingLimit, exists := tc.userLimits[user.ID]

		if exists {
			// 检查限制值是否变化
			if existingLimit.BandwidthLimit != limitValue || existingLimit.Enabled != enabled {
				// 限制值变化了，需要更新并重置令牌桶
				existingLimit.mu.Lock()
				existingLimit.BandwidthLimit = limitValue
				existingLimit.Enabled = enabled
				existingLimit.LastUpdate = time.Now()
				// 重置令牌桶状态
				existingLimit.tokens = float64(limitValue * 2)
				existingLimit.lastRefill = time.Now()
				existingLimit.mu.Unlock()

				logger.Log.Infof("更新用户 %d (%s) 的带宽限制: %d B/s (enabled: %v)",
					user.ID, user.Username, limitValue, enabled)
				updatedCount++
			}
			// 如果没有变化，保持现有配置（包括令牌桶状态）
		} else {
			// 新用户，创建限制配置
			tc.userLimits[user.ID] = &UserLimit{
				UserID:         user.ID,
				BandwidthLimit: limitValue,
				Enabled:        enabled,
				LastUpdate:     time.Now(),
			}
			logger.Log.Infof("新增用户 %d (%s) 的带宽限制: %d B/s (enabled: %v)",
				user.ID, user.Username, limitValue, enabled)
			newCount++
		}
	}

	if updatedCount > 0 || newCount > 0 {
		logger.Log.Infof("带宽限制加载完成: 总用户数 %d, 新增 %d, 更新 %d",
			len(tc.userLimits), newCount, updatedCount)
	}
}

// GetUserLimit 获取用户带宽限制
func (tc *TrafficController) GetUserLimit(userID uint) *UserLimit {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	return tc.userLimits[userID]
}

// SetUserLimit 设置用户带宽限制
func (tc *TrafficController) SetUserLimit(userID uint, limit int64) error {
	if database.DB == nil {
		return fmt.Errorf("数据库连接不可用")
	}

	// 更新数据库
	bandwidthLimit := &database.BandwidthLimit{
		UserID:  userID,
		Limit:   limit,
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

// reloadLimitsLoop 定期重新加载带宽限制配置
func (tc *TrafficController) reloadLimitsLoop() {
	ticker := time.NewTicker(120 * time.Second) // 每120秒重新加载一次（优化：从30秒改为120秒）
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			logger.Log.Debug("重新加载带宽限制配置...")
			tc.loadUserLimits()
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

// ThrottleConnection 限速连接 - 使用令牌桶算法（优化版）
func (tc *TrafficController) ThrottleConnection(ctx context.Context, userID uint, bytes int64) error {
	// 获取用户的带宽限制
	tc.mu.RLock()
	limit, exists := tc.userLimits[userID]
	tc.mu.RUnlock()

	// 如果没有限制或限制未启用，不进行限速
	if !exists || !limit.Enabled || limit.BandwidthLimit <= 0 {
		return nil
	}

	// 优化：减少锁持有时间，将计算移到锁外
	now := time.Now()
	requiredTokens := float64(bytes)

	limit.mu.Lock()

	// 初始化令牌桶
	if limit.lastRefill.IsZero() {
		limit.lastRefill = now
		limit.tokens = float64(limit.BandwidthLimit * 2)
	}

	// 计算自上次填充以来应该新增的令牌数
	elapsed := now.Sub(limit.lastRefill).Seconds()
	if elapsed > 0 {
		newTokens := elapsed * float64(limit.BandwidthLimit)
		limit.tokens += newTokens
		maxTokens := float64(limit.BandwidthLimit * 2)
		if limit.tokens > maxTokens {
			limit.tokens = maxTokens
		}
		limit.lastRefill = now
	}

	// 如果令牌足够，直接扣除并返回
	if limit.tokens >= requiredTokens {
		limit.tokens -= requiredTokens
		limit.mu.Unlock()
		return nil
	}

	// 令牌不足，计算等待时间（在锁内完成快速计算）
	tokensNeeded := requiredTokens - limit.tokens
	waitSeconds := tokensNeeded / float64(limit.BandwidthLimit)
	waitTime := time.Duration(waitSeconds * float64(time.Second))

	// 限制最大等待时间
	maxWaitTime := 5 * time.Second // 优化：从10秒改为5秒，避免长时间阻塞
	if waitTime > maxWaitTime {
		waitTime = maxWaitTime
	}

	// 预支令牌
	limit.tokens = 0
	limit.lastRefill = now
	limit.mu.Unlock() // 优化：在等待之前释放锁

	// 在锁外等待，不阻塞其他goroutine
	select {
	case <-time.After(waitTime):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
