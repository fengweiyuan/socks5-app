package collector

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"socks5-app/internal/websocket"
)

// 流量数据收集器
type TrafficCollector struct {
	// WebSocket管理器
	wsManager *websocket.Manager

	// 数据缓存
	trafficCache map[string]*websocket.TrafficData

	// 统计信息
	stats *TrafficStats

	// 配置
	config *CollectorConfig

	// 互斥锁
	mu sync.RWMutex

	// 上下文和取消函数
	ctx    context.Context
	cancel context.CancelFunc

	// 工作协程
	wg sync.WaitGroup
}

// 收集器配置
type CollectorConfig struct {
	// 收集间隔
	CollectionInterval time.Duration

	// 缓存大小
	CacheSize int

	// 启用实时推送
	EnableRealTimePush bool

	// 启用历史记录
	EnableHistoryRecord bool

	// 数据保留时间
	DataRetentionTime time.Duration
}

// 流量统计信息
type TrafficStats struct {
	TotalBytesSent    int64
	TotalBytesRecv    int64
	TotalConnections  int64
	ActiveConnections int64
	PeakSpeed         float64
	AverageSpeed      float64
	LastUpdateTime    time.Time
}

// 创建新的流量收集器
func NewTrafficCollector(wsManager *websocket.Manager, config *CollectorConfig) *TrafficCollector {
	if config == nil {
		config = &CollectorConfig{
			CollectionInterval:  1 * time.Second,
			CacheSize:           1000,
			EnableRealTimePush:  true,
			EnableHistoryRecord: true,
			DataRetentionTime:   24 * time.Hour,
		}
	}

	ctx, cancel := context.WithCancel(context.Background())

	tc := &TrafficCollector{
		wsManager:    wsManager,
		trafficCache: make(map[string]*websocket.TrafficData),
		stats:        &TrafficStats{},
		config:       config,
		ctx:          ctx,
		cancel:       cancel,
	}

	return tc
}

// 启动收集器
func (tc *TrafficCollector) Start() {
	log.Println("启动流量数据收集器...")

	// 启动数据收集协程
	tc.wg.Add(1)
	go tc.collectTrafficData()

	// 启动数据清理协程
	tc.wg.Add(1)
	go tc.cleanupOldData()

	// 启动统计计算协程
	tc.wg.Add(1)
	go tc.calculateStats()

	log.Println("流量数据收集器已启动")
}

// 停止收集器
func (tc *TrafficCollector) Stop() {
	log.Println("停止流量数据收集器...")

	// 发送取消信号
	tc.cancel()

	// 等待所有协程完成
	tc.wg.Wait()

	log.Println("流量数据收集器已停止")
}

// 收集流量数据
func (tc *TrafficCollector) collectTrafficData() {
	defer tc.wg.Done()

	ticker := time.NewTicker(tc.config.CollectionInterval)
	defer ticker.Stop()

	for {
		select {
		case <-tc.ctx.Done():
			return
		case <-ticker.C:
			tc.collectOnce()
		}
	}
}

// 收集一次流量数据
func (tc *TrafficCollector) collectOnce() {
	// 这里应该从实际的代理服务收集流量数据
	// 暂时使用模拟数据

	tc.mu.Lock()
	defer tc.mu.Unlock()

	// 模拟收集数据
	now := time.Now()

	// 为每个活跃连接收集数据
	for _, data := range tc.trafficCache {
		// 更新数据
		data.Timestamp = now.Unix()

		// 计算速度（这里应该基于实际的数据变化）
		if data.BytesSent > 0 || data.BytesRecv > 0 {
			// 模拟速度计算
			data.Speed = float64(data.BytesSent+data.BytesRecv) / 1024 // KB/s
			data.Bandwidth = data.Speed / 1024 * 100                   // 带宽使用率
		}

		// 实时推送到WebSocket
		if tc.config.EnableRealTimePush {
			tc.wsManager.PushTrafficData(*data)
		}
	}
}

// 清理旧数据
func (tc *TrafficCollector) cleanupOldData() {
	defer tc.wg.Done()

	ticker := time.NewTicker(5 * time.Minute) // 每5分钟清理一次
	defer ticker.Stop()

	for {
		select {
		case <-tc.ctx.Done():
			return
		case <-ticker.C:
			tc.cleanupOnce()
		}
	}
}

// 清理一次旧数据
func (tc *TrafficCollector) cleanupOnce() {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	cutoffTime := time.Now().Add(-tc.config.DataRetentionTime)

	for key, data := range tc.trafficCache {
		if time.Unix(data.Timestamp, 0).Before(cutoffTime) {
			delete(tc.trafficCache, key)
		}
	}
}

// 计算统计信息
func (tc *TrafficCollector) calculateStats() {
	defer tc.wg.Done()

	ticker := time.NewTicker(10 * time.Second) // 每10秒计算一次
	defer ticker.Stop()

	for {
		select {
		case <-tc.ctx.Done():
			return
		case <-ticker.C:
			tc.calculateStatsOnce()
		}
	}
}

// 计算一次统计信息
func (tc *TrafficCollector) calculateStatsOnce() {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	var totalSent, totalRecv int64
	var totalSpeed float64
	var count int

	for _, data := range tc.trafficCache {
		totalSent += data.BytesSent
		totalRecv += data.BytesRecv
		totalSpeed += data.Speed
		count++
	}

	// 更新统计信息
	tc.stats.TotalBytesSent = totalSent
	tc.stats.TotalBytesRecv = totalRecv
	tc.stats.ActiveConnections = int64(count)
	tc.stats.LastUpdateTime = time.Now()

	if count > 0 {
		tc.stats.AverageSpeed = totalSpeed / float64(count)
	}

	// 更新峰值速度
	if tc.stats.AverageSpeed > tc.stats.PeakSpeed {
		tc.stats.PeakSpeed = tc.stats.AverageSpeed
	}
}

// 添加流量数据
func (tc *TrafficCollector) AddTrafficData(userID int, clientIP string, bytesSent, bytesRecv int64) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	key := generateTrafficKey(userID, clientIP)

	data := &websocket.TrafficData{
		UserID:    userID,
		ClientIP:  clientIP,
		BytesSent: bytesSent,
		BytesRecv: bytesRecv,
		Timestamp: time.Now().Unix(),
	}

	// 如果缓存已满，删除最旧的数据
	if len(tc.trafficCache) >= tc.config.CacheSize {
		tc.removeOldestData()
	}

	tc.trafficCache[key] = data

	// 更新总统计
	tc.stats.TotalBytesSent += bytesSent
	tc.stats.TotalBytesRecv += bytesRecv
	tc.stats.TotalConnections++
}

// 更新连接状态
func (tc *TrafficCollector) UpdateConnectionStatus(userID int, clientIP string, connectionCount int) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	key := generateTrafficKey(userID, clientIP)

	if data, exists := tc.trafficCache[key]; exists {
		data.ConnectionCount = connectionCount
	}
}

// 移除最旧的数据
func (tc *TrafficCollector) removeOldestData() {
	var oldestKey string
	var oldestTime int64

	for key, data := range tc.trafficCache {
		if oldestKey == "" || data.Timestamp < oldestTime {
			oldestKey = key
			oldestTime = data.Timestamp
		}
	}

	if oldestKey != "" {
		delete(tc.trafficCache, oldestKey)
	}
}

// 生成流量数据键
func generateTrafficKey(userID int, clientIP string) string {
	return fmt.Sprintf("%d_%s", userID, clientIP)
}

// 获取统计信息
func (tc *TrafficCollector) GetStats() *TrafficStats {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	// 返回统计信息的副本
	stats := *tc.stats
	return &stats
}

// 获取用户流量数据
func (tc *TrafficCollector) GetUserTrafficData(userID int) []*websocket.TrafficData {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	var result []*websocket.TrafficData

	for _, data := range tc.trafficCache {
		if data.UserID == userID {
			// 返回数据的副本
			dataCopy := *data
			result = append(result, &dataCopy)
		}
	}

	return result
}

// 获取所有流量数据
func (tc *TrafficCollector) GetAllTrafficData() []*websocket.TrafficData {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	var result []*websocket.TrafficData

	for _, data := range tc.trafficCache {
		// 返回数据的副本
		dataCopy := *data
		result = append(result, &dataCopy)
	}

	return result
}

// 重置统计信息
func (tc *TrafficCollector) ResetStats() {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	tc.stats = &TrafficStats{}
}

// 获取缓存大小
func (tc *TrafficCollector) GetCacheSize() int {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	return len(tc.trafficCache)
}

// 获取配置信息
func (tc *TrafficCollector) GetConfig() *CollectorConfig {
	return tc.config
}

// 更新配置
func (tc *TrafficCollector) UpdateConfig(config *CollectorConfig) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	tc.config = config
}

// 健康检查
func (tc *TrafficCollector) HealthCheck() map[string]interface{} {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	return map[string]interface{}{
		"status":             "healthy",
		"cache_size":         len(tc.trafficCache),
		"active_connections": tc.stats.ActiveConnections,
		"last_update":        tc.stats.LastUpdateTime,
		"config":             tc.config,
	}
}
