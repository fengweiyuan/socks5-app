package api

import (
	"github.com/gin-gonic/gin"
)

// Gin兼容的监控指标处理器函数

// HandleMetricsGin 处理Prometheus指标请求的Gin版本
func (h *MetricsHandler) HandleMetricsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.HandleMetrics(w, r)
}

// HandleHealthCheckGin 处理健康检查请求的Gin版本
func (h *MetricsHandler) HandleHealthCheckGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.HandleHealthCheck(w, r)
}

// GetMetricsStatsGin 获取监控指标统计信息的Gin版本
func (h *MetricsHandler) GetMetricsStatsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.GetMetricsStats(w, r)
}

// ResetMetricsGin 重置监控指标的Gin版本
func (h *MetricsHandler) ResetMetricsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.ResetMetrics(w, r)
}

// GetMetricsConfigGin 获取监控配置信息的Gin版本
func (h *MetricsHandler) GetMetricsConfigGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.GetMetricsConfig(w, r)
}

// RecordTestMetricsGin 记录测试指标数据的Gin版本
func (h *MetricsHandler) RecordTestMetricsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.RecordTestMetrics(w, r)
}

// GetAvailableMetricsGin 获取可用监控指标列表的Gin版本
func (h *MetricsHandler) GetAvailableMetricsGin(c *gin.Context) {
	// 从Gin上下文获取请求和响应
	w := c.Writer
	r := c.Request

	// 调用原始的HTTP处理器
	h.GetAvailableMetrics(w, r)
}
