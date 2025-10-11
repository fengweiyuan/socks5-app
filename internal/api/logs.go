package api

import (
	"encoding/csv"
	"net/http"
	"strconv"
	"time"

	"socks5-app/internal/database"
	"socks5-app/internal/logger"

	"github.com/gin-gonic/gin"
)

// logOperation 记录操作日志
func (s *Server) logOperation(c *gin.Context, operation string, target string, details string) {
	// 从上下文中获取操作用户信息
	operatorID, _ := c.Get("user_id")
	operatorUsername, _ := c.Get("username")

	if operatorID == nil || operatorUsername == nil {
		logger.Log.Warn("无法获取操作用户信息，跳过日志记录")
		return
	}

	// 创建操作日志
	accessLog := &database.AccessLog{
		UserID:    operatorID.(uint),
		ClientIP:  c.ClientIP(),
		TargetURL: c.Request.URL.Path,
		Method:    c.Request.Method,
		Status:    "success",
		UserAgent: c.GetHeader("User-Agent"),
		Timestamp: time.Now(),
	}

	// 将操作详情添加到UserAgent字段中
	if details != "" {
		userAgent := c.GetHeader("User-Agent")
		if userAgent == "" {
			userAgent = "API-Client"
		}
		accessLog.UserAgent = userAgent + " | " + details
	}

	// 保存日志到数据库
	if database.DB != nil {
		if err := database.DB.Create(accessLog).Error; err != nil {
			logger.Log.Errorf("记录操作日志失败: %v", err)
		} else {
			logger.Log.Infof("操作日志已记录: %s %s %s (操作者: %s)", operation, target, details, operatorUsername)
		}
	}
}

func (s *Server) handleGetLogs(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("pageSize", "20"))
	status := c.Query("status")
	username := c.Query("username")
	startDate := c.Query("startDate")
	endDate := c.Query("endDate")
	logType := c.Query("type")

	offset := (page - 1) * pageSize

	// 检查是否是流量日志请求
	logger.Log.Infof("处理日志请求: type=%s, path=%s", logType, c.Request.URL.Path)
	if logType == "traffic" {
		// 返回流量日志
		query := database.DB.Model(&database.TrafficLog{}).Preload("User")

		// 应用过滤条件
		if username != "" {
			query = query.Joins("JOIN users ON traffic_logs.user_id = users.id").
				Where("users.username LIKE ?", "%"+username+"%")
		}
		if startDate != "" && endDate != "" {
			query = query.Where("timestamp BETWEEN ? AND ?", startDate, endDate)
		}

		var total int64
		query.Count(&total)

		var logs []database.TrafficLog
		if err := query.Offset(offset).Limit(pageSize).
			Order("timestamp DESC").
			Find(&logs).Error; err != nil {
			logger.Log.Errorf("获取流量日志失败: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "获取流量日志失败"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"logs":     logs,
			"total":    total,
			"page":     page,
			"pageSize": pageSize,
		})
		return
	}

	// 返回访问日志
	query := database.DB.Model(&database.AccessLog{}).Preload("User")

	// 应用过滤条件
	if status != "" {
		query = query.Where("status = ?", status)
	}
	if username != "" {
		query = query.Joins("JOIN users ON access_logs.user_id = users.id").
			Where("users.username LIKE ?", "%"+username+"%")
	}
	if startDate != "" && endDate != "" {
		query = query.Where("timestamp BETWEEN ? AND ?", startDate, endDate)
	}

	var total int64
	query.Count(&total)

	var logs []database.AccessLog
	if err := query.Offset(offset).Limit(pageSize).
		Order("timestamp DESC").
		Find(&logs).Error; err != nil {
		logger.Log.Errorf("获取日志失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取日志失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"logs":     logs,
		"total":    total,
		"page":     page,
		"pageSize": pageSize,
	})
}

func (s *Server) handleExportLogs(c *gin.Context) {
	var logs []database.AccessLog
	if err := database.DB.Preload("User").
		Order("timestamp DESC").
		Find(&logs).Error; err != nil {
		logger.Log.Errorf("导出日志失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "导出日志失败"})
		return
	}

	// 设置CSV响应头
	filename := "logs_" + time.Now().Format("2006-01-02") + ".csv"
	c.Header("Content-Type", "text/csv")
	c.Header("Content-Disposition", "attachment; filename="+filename)

	writer := csv.NewWriter(c.Writer)
	defer writer.Flush()

	// 写入CSV头部
	headers := []string{"ID", "用户名", "客户端IP", "目标URL", "方法", "状态", "用户代理", "时间"}
	writer.Write(headers)

	// 写入数据
	for _, log := range logs {
		row := []string{
			strconv.FormatUint(uint64(log.ID), 10),
			log.User.Username,
			log.ClientIP,
			log.TargetURL,
			log.Method,
			log.Status,
			log.UserAgent,
			log.Timestamp.Format("2006-01-02 15:04:05"),
		}
		writer.Write(row)
	}

	// 记录导出日志操作
	s.logOperation(c, "EXPORT_LOGS", filename,
		"exported_records:"+strconv.Itoa(len(logs)))

	logger.Log.Infof("日志导出成功，共导出 %d 条记录", len(logs))
}

func (s *Server) handleClearLogs(c *gin.Context) {
	// 先查询要删除的日志数量
	var count int64
	database.DB.Model(&database.AccessLog{}).Where("timestamp < ?", time.Now().AddDate(0, 0, -30)).Count(&count)

	if err := database.DB.Where("timestamp < ?", time.Now().AddDate(0, 0, -30)).Delete(&database.AccessLog{}).Error; err != nil {
		logger.Log.Errorf("清理日志失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "清理日志失败"})
		return
	}

	// 记录清理日志操作
	s.logOperation(c, "CLEAR_LOGS", "30天前",
		"deleted_records:"+strconv.FormatInt(count, 10))

	logger.Log.Infof("日志清理成功，删除了 %d 条记录", count)
	c.JSON(http.StatusOK, gin.H{"message": "日志清理成功"})
}
