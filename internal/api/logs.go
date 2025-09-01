package api

import (
	"encoding/csv"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

func (s *Server) handleGetLogs(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("pageSize", "20"))
	status := c.Query("status")
	username := c.Query("username")
	startDate := c.Query("startDate")
	endDate := c.Query("endDate")

	offset := (page - 1) * pageSize

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
		"logs": logs,
		"total": total,
		"page": page,
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
}

func (s *Server) handleClearLogs(c *gin.Context) {
	if err := database.DB.Where("timestamp < ?", time.Now().AddDate(0, 0, -30)).Delete(&database.AccessLog{}).Error; err != nil {
		logger.Log.Errorf("清理日志失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "清理日志失败"})
		return
	}

	logger.Log.Info("日志清理成功")
	c.JSON(http.StatusOK, gin.H{"message": "日志清理成功"})
}
