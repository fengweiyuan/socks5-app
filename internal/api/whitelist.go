package api

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

func (s *Server) handleGetIPWhitelist(c *gin.Context) {
	var whitelist []database.IPWhitelist
	if err := database.DB.Order("created_at DESC").Find(&whitelist).Error; err != nil {
		logger.Log.Errorf("获取IP白名单失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取IP白名单失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"whitelist": whitelist})
}

func (s *Server) handleAddIPWhitelist(c *gin.Context) {
	var whitelist database.IPWhitelist
	if err := c.ShouldBindJSON(&whitelist); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 检查IP是否已存在
	var existing database.IPWhitelist
	if err := database.DB.Where("ip = ?", whitelist.IP).First(&existing).Error; err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "IP地址已存在"})
		return
	}

	if err := database.DB.Create(&whitelist).Error; err != nil {
		logger.Log.Errorf("添加IP白名单失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "添加IP白名单失败"})
		return
	}

	logger.Log.Infof("添加IP白名单成功: %s", whitelist.IP)
	c.JSON(http.StatusCreated, gin.H{"whitelist": whitelist})
}

func (s *Server) handleRemoveIPWhitelist(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的ID"})
		return
	}

	var whitelist database.IPWhitelist
	if err := database.DB.First(&whitelist, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "白名单记录不存在"})
		return
	}

	if err := database.DB.Delete(&whitelist).Error; err != nil {
		logger.Log.Errorf("删除IP白名单失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除IP白名单失败"})
		return
	}

	logger.Log.Infof("删除IP白名单成功: %s", whitelist.IP)
	c.JSON(http.StatusOK, gin.H{"message": "IP白名单删除成功"})
}
