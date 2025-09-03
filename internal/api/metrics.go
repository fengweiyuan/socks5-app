package api

import (
	"net/http"
	"time"

	"socks5-app/internal/metrics"
)

// 监控指标处理器
type MetricsHandler struct {
	metricsManager *metrics.MetricsManager
}

// 创建新的监控指标处理器
func NewMetricsHandler(metricsManager *metrics.MetricsManager) *MetricsHandler {
	return &MetricsHandler{
		metricsManager: metricsManager,
	}
}

// 处理Prometheus指标请求
func (h *MetricsHandler) HandleMetrics(w http.ResponseWriter, r *http.Request) {
	// 设置响应头
	w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")

	// 获取Prometheus指标处理器
	handler := h.metricsManager.GetHandler()
	handler.ServeHTTP(w, r)
}

// 处理健康检查请求
func (h *MetricsHandler) HandleHealthCheck(w http.ResponseWriter, r *http.Request) {
	h.metricsManager.HealthCheckHandler(w, r)
}

// 获取监控指标统计信息
func (h *MetricsHandler) GetMetricsStats(w http.ResponseWriter, r *http.Request) {
	stats := h.metricsManager.GetMetricsStats()

	// 返回JSON响应
	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    stats,
	})
}

// 重置监控指标
func (h *MetricsHandler) ResetMetrics(w http.ResponseWriter, r *http.Request) {
	h.metricsManager.ResetMetrics()

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success":   true,
		"message":   "监控指标已重置",
		"timestamp": time.Now().Unix(),
	})
}

// 获取监控配置信息
func (h *MetricsHandler) GetMetricsConfig(w http.ResponseWriter, r *http.Request) {
	config := map[string]interface{}{
		"metrics_endpoint": h.metricsManager.GetMetricsEndpoint(),
		"health_endpoint":  h.metricsManager.GetHealthEndpoint(),
		"service_name":     "socks5-proxy-metrics",
		"version":          "1.0.0",
	}

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    config,
	})
}

// 记录测试指标数据
func (h *MetricsHandler) RecordTestMetrics(w http.ResponseWriter, r *http.Request) {
	// 记录测试代理连接
	h.metricsManager.RecordProxyConnection("test-proxy-1", "1", "192.168.1.100", "active")
	h.metricsManager.RecordProxyConnection("test-proxy-1", "2", "192.168.1.101", "active")

	// 记录测试流量数据
	h.metricsManager.RecordTraffic("1", "192.168.1.100", "8.8.8.8", "tcp", 1024, 2048)
	h.metricsManager.RecordTraffic("2", "192.168.1.101", "1.1.1.1", "tcp", 2048, 4096)

	// 记录测试传输速度
	h.metricsManager.RecordTrafficSpeed("1", "192.168.1.100", "upload", 1024.0)
	h.metricsManager.RecordTrafficSpeed("1", "192.168.1.100", "download", 2048.0)

	// 记录测试代理响应时间
	h.metricsManager.RecordProxyResponseTime("test-proxy-1", "connection", 100*time.Millisecond)
	h.metricsManager.RecordProxyResponseTime("test-proxy-1", "data_transfer", 50*time.Millisecond)

	// 记录测试用户连接数
	h.metricsManager.RecordUserConnections("1", "testuser1", 2)
	h.metricsManager.RecordUserConnections("2", "testuser2", 1)

	// 记录测试用户流量
	h.metricsManager.RecordUserTraffic("1", "testuser1", "upload", 1024)
	h.metricsManager.RecordUserTraffic("1", "testuser1", "download", 2048)

	// 记录测试系统指标
	h.metricsManager.RecordSystemCPU("total", 25.5)
	h.metricsManager.RecordSystemMemory("total", 1024*1024*1024)   // 1GB
	h.metricsManager.RecordSystemNetwork("eth0", "in", 1024*1024)  // 1MB
	h.metricsManager.RecordSystemNetwork("eth0", "out", 2048*1024) // 2MB

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success":   true,
		"message":   "测试指标数据记录成功",
		"timestamp": time.Now().Unix(),
	})
}

// 获取可用的监控指标列表
func (h *MetricsHandler) GetAvailableMetrics(w http.ResponseWriter, r *http.Request) {
	availableMetrics := map[string]interface{}{
		"proxy_metrics": map[string]interface{}{
			"socks5_proxy_connections_active":    "当前活跃的代理连接数",
			"socks5_proxy_connections_total":     "代理连接总数",
			"socks5_proxy_response_time_seconds": "代理响应时间",
			"socks5_proxy_errors_total":          "代理错误总数",
		},
		"traffic_metrics": map[string]interface{}{
			"socks5_traffic_bytes_sent":             "发送的字节数",
			"socks5_traffic_bytes_received":         "接收的字节数",
			"socks5_traffic_speed_bytes_per_second": "当前传输速度",
		},
		"user_metrics": map[string]interface{}{
			"socks5_user_connections_active": "用户当前活跃连接数",
			"socks5_user_traffic_total":      "用户总流量",
		},
		"system_metrics": map[string]interface{}{
			"socks5_system_cpu_usage_percent":  "系统CPU使用率",
			"socks5_system_memory_usage_bytes": "系统内存使用量",
			"socks5_system_network_bytes":      "系统网络流量",
		},
	}

	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    availableMetrics,
	})
}
