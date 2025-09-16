package metrics

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// 监控指标管理器
type MetricsManager struct {
	// 代理连接指标
	proxyConnections      *prometheus.GaugeVec
	proxyConnectionsTotal *prometheus.CounterVec

	// 流量指标
	trafficBytesSent *prometheus.CounterVec
	trafficBytesRecv *prometheus.CounterVec
	trafficSpeed     *prometheus.GaugeVec

	// 代理性能指标
	proxyResponseTime *prometheus.HistogramVec
	proxyErrorRate    *prometheus.CounterVec

	// 用户指标
	userConnections *prometheus.GaugeVec
	userTraffic     *prometheus.CounterVec

	// 系统指标
	systemCPU     *prometheus.GaugeVec
	systemMemory  *prometheus.GaugeVec
	systemNetwork *prometheus.GaugeVec

	// 注册表
	registry *prometheus.Registry

	// 互斥锁
	mu sync.RWMutex

	// 指标缓存
	metricsCache map[string]interface{}
}

// 创建新的监控指标管理器
func NewMetricsManager() *MetricsManager {
	mm := &MetricsManager{
		registry:     prometheus.NewRegistry(),
		metricsCache: make(map[string]interface{}),
	}

	mm.initMetrics()
	return mm
}

// 初始化监控指标
func (mm *MetricsManager) initMetrics() {
	// 代理连接指标
	mm.proxyConnections = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_proxy_connections_active",
			Help: "当前活跃的代理连接数",
		},
		[]string{"proxy_id", "user_id", "client_ip"},
	)

	mm.proxyConnectionsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "socks5_proxy_connections_total",
			Help: "代理连接总数",
		},
		[]string{"proxy_id", "user_id", "client_ip", "status"},
	)

	// 流量指标
	mm.trafficBytesSent = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "socks5_traffic_bytes_sent",
			Help: "发送的字节数",
		},
		[]string{"user_id", "client_ip", "target_ip", "protocol"},
	)

	mm.trafficBytesRecv = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "socks5_traffic_bytes_received",
			Help: "接收的字节数",
		},
		[]string{"user_id", "client_ip", "target_ip", "protocol"},
	)

	mm.trafficSpeed = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_traffic_speed_bytes_per_second",
			Help: "当前传输速度 (bytes/s)",
		},
		[]string{"user_id", "client_ip", "direction"},
	)

	// 代理性能指标
	mm.proxyResponseTime = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "socks5_proxy_response_time_seconds",
			Help:    "代理响应时间",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"proxy_id", "operation"},
	)

	mm.proxyErrorRate = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "socks5_proxy_errors_total",
			Help: "代理错误总数",
		},
		[]string{"proxy_id", "error_type"},
	)

	// 用户指标
	mm.userConnections = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_user_connections_active",
			Help: "用户当前活跃连接数",
		},
		[]string{"user_id", "username"},
	)

	mm.userTraffic = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "socks5_user_traffic_total",
			Help: "用户总流量",
		},
		[]string{"user_id", "username", "direction"},
	)

	// 系统指标
	mm.systemCPU = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_system_cpu_usage_percent",
			Help: "系统CPU使用率",
		},
		[]string{"cpu_core"},
	)

	mm.systemMemory = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_system_memory_usage_bytes",
			Help: "系统内存使用量",
		},
		[]string{"memory_type"},
	)

	mm.systemNetwork = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "socks5_system_network_bytes",
			Help: "系统网络流量",
		},
		[]string{"interface", "direction"},
	)

	// 注册所有指标
	mm.registry.MustRegister(
		mm.proxyConnections,
		mm.proxyConnectionsTotal,
		mm.trafficBytesSent,
		mm.trafficBytesRecv,
		mm.trafficSpeed,
		mm.proxyResponseTime,
		mm.proxyErrorRate,
		mm.userConnections,
		mm.userTraffic,
		mm.systemCPU,
		mm.systemMemory,
		mm.systemNetwork,
	)
}

// 获取Prometheus HTTP处理器
func (mm *MetricsManager) GetHandler() http.Handler {
	return promhttp.HandlerFor(mm.registry, promhttp.HandlerOpts{})
}

// 记录代理连接
func (mm *MetricsManager) RecordProxyConnection(proxyID, userID, clientIP, status string) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// 增加连接总数
	mm.proxyConnectionsTotal.WithLabelValues(proxyID, userID, clientIP, status).Inc()

	// 更新活跃连接数
	if status == "active" {
		mm.proxyConnections.WithLabelValues(proxyID, userID, clientIP).Inc()
	} else if status == "closed" || status == "disconnected" {
		mm.proxyConnections.WithLabelValues(proxyID, userID, clientIP).Dec()
	}
}

// 记录流量数据
func (mm *MetricsManager) RecordTraffic(userID, clientIP, targetIP, protocol string, bytesSent, bytesRecv int64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// 记录发送和接收的字节数
	mm.trafficBytesSent.WithLabelValues(userID, clientIP, targetIP, protocol).Add(float64(bytesSent))
	mm.trafficBytesRecv.WithLabelValues(userID, clientIP, targetIP, protocol).Add(float64(bytesRecv))
}

// 记录传输速度
func (mm *MetricsManager) RecordTrafficSpeed(userID, clientIP, direction string, speed float64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.trafficSpeed.WithLabelValues(userID, clientIP, direction).Set(speed)
}

// 记录代理响应时间
func (mm *MetricsManager) RecordProxyResponseTime(proxyID, operation string, duration time.Duration) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.proxyResponseTime.WithLabelValues(proxyID, operation).Observe(duration.Seconds())
}

// 记录代理错误
func (mm *MetricsManager) RecordProxyError(proxyID, errorType string) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.proxyErrorRate.WithLabelValues(proxyID, errorType).Inc()
}

// 记录用户连接数
func (mm *MetricsManager) RecordUserConnections(userID, username string, count int) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.userConnections.WithLabelValues(userID, username).Set(float64(count))
}

// 记录用户流量
func (mm *MetricsManager) RecordUserTraffic(userID, username, direction string, bytes int64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.userTraffic.WithLabelValues(userID, username, direction).Add(float64(bytes))
}

// 记录系统CPU使用率
func (mm *MetricsManager) RecordSystemCPU(cpuCore string, usagePercent float64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.systemCPU.WithLabelValues(cpuCore).Set(usagePercent)
}

// 记录系统内存使用量
func (mm *MetricsManager) RecordSystemMemory(memoryType string, usageBytes int64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.systemMemory.WithLabelValues(memoryType).Set(float64(usageBytes))
}

// 记录系统网络流量
func (mm *MetricsManager) RecordSystemNetwork(interfaceName, direction string, bytes int64) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.systemNetwork.WithLabelValues(interfaceName, direction).Set(float64(bytes))
}

// 获取指标统计信息
func (mm *MetricsManager) GetMetricsStats() map[string]interface{} {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	stats := map[string]interface{}{
		"timestamp":     time.Now().Unix(),
		"metrics_count": len(mm.metricsCache),
	}

	// 这里可以添加更多统计信息
	return stats
}

// 重置所有指标
func (mm *MetricsManager) ResetMetrics() {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// 重置所有指标
	mm.proxyConnections.Reset()
	mm.proxyConnectionsTotal.Reset()
	mm.trafficBytesSent.Reset()
	mm.trafficBytesRecv.Reset()
	mm.trafficSpeed.Reset()
	mm.proxyResponseTime.Reset()
	mm.proxyErrorRate.Reset()
	mm.userConnections.Reset()
	mm.userTraffic.Reset()
	mm.systemCPU.Reset()
	mm.systemMemory.Reset()
	mm.systemNetwork.Reset()

	// 清空缓存
	mm.metricsCache = make(map[string]interface{})
}

// 自定义指标收集器
type CustomCollector struct {
	metricsManager *MetricsManager
}

// 实现prometheus.Collector接口
func (cc *CustomCollector) Describe(ch chan<- *prometheus.Desc) {
	// 描述所有指标
}

func (cc *CustomCollector) Collect(ch chan<- prometheus.Metric) {
	// 收集所有指标
}

// 创建自定义收集器
func NewCustomCollector(mm *MetricsManager) *CustomCollector {
	return &CustomCollector{
		metricsManager: mm,
	}
}

// 启动指标收集器
func (mm *MetricsManager) StartCollector() {
	// 启动定期收集系统指标的协程
	go mm.collectSystemMetrics()
}

// 收集系统指标
func (mm *MetricsManager) collectSystemMetrics() {
	ticker := time.NewTicker(30 * time.Second) // 每30秒收集一次
	defer ticker.Stop()

	for range ticker.C {
		mm.collectSystemMetricsOnce()
	}
}

// 收集一次系统指标
func (mm *MetricsManager) collectSystemMetricsOnce() {
	// 这里可以添加实际的系统指标收集逻辑
	// 例如：CPU使用率、内存使用量、网络流量等

	// 示例：记录当前时间戳作为心跳
	mm.RecordSystemCPU("total", 0.0)  // 实际应该收集真实的CPU使用率
	mm.RecordSystemMemory("total", 0) // 实际应该收集真实的内存使用量
}

// 获取指标端点URL
func (mm *MetricsManager) GetMetricsEndpoint() string {
	return "/metrics"
}

// 获取健康检查端点URL
func (mm *MetricsManager) GetHealthEndpoint() string {
	return "/health"
}

// 健康检查处理器
func (mm *MetricsManager) HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	health := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"service":   "socks5-proxy-metrics",
		"version":   "1.0.0",
	}

	// 这里可以添加更多健康检查逻辑
	// 例如：检查数据库连接、检查系统资源等

	fmt.Fprintf(w, `{"status":"%s","timestamp":%d,"service":"%s","version":"%s"}`,
		health["status"], health["timestamp"], health["service"], health["version"])
}
