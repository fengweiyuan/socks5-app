package api

import (
	"net/http"
	"strconv"

	"socks5-app/internal/database"
	"socks5-app/internal/logger"
	"socks5-app/internal/utils"

	"github.com/gin-gonic/gin"
)

// ==================== IP黑名单 API ====================

// handleGetIPBlacklist 获取IP黑名单列表
func (s *Server) handleGetIPBlacklist(c *gin.Context) {
	var blacklist []database.IPBlacklist
	if err := database.DB.Order("created_at DESC").Find(&blacklist).Error; err != nil {
		logger.Log.Errorf("获取IP黑名单失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取IP黑名单失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"blacklist": blacklist})
}

// handleCreateIPBlacklist 创建IP黑名单规则
func (s *Server) handleCreateIPBlacklist(c *gin.Context) {
	var entry database.IPBlacklist
	if err := c.ShouldBindJSON(&entry); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 验证CIDR格式
	if err := utils.ValidateCIDR(entry.CIDR); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的CIDR格式: " + err.Error()})
		return
	}

	if err := database.DB.Create(&entry).Error; err != nil {
		logger.Log.Errorf("创建IP黑名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建IP黑名单规则失败"})
		return
	}

	logger.Log.Infof("创建IP黑名单规则成功: %s", entry.CIDR)
	c.JSON(http.StatusCreated, gin.H{"entry": entry})
}

// handleUpdateIPBlacklist 更新IP黑名单规则
func (s *Server) handleUpdateIPBlacklist(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var entry database.IPBlacklist
	if err := database.DB.First(&entry, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "IP黑名单规则不存在"})
		return
	}

	var updateData database.IPBlacklist
	if err := c.ShouldBindJSON(&updateData); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 更新字段
	if updateData.CIDR != "" {
		// 验证CIDR格式
		if err := utils.ValidateCIDR(updateData.CIDR); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "无效的CIDR格式: " + err.Error()})
			return
		}
		entry.CIDR = updateData.CIDR
	}
	if updateData.Description != "" {
		entry.Description = updateData.Description
	}
	entry.Enabled = updateData.Enabled

	if err := database.DB.Save(&entry).Error; err != nil {
		logger.Log.Errorf("更新IP黑名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新IP黑名单规则失败"})
		return
	}

	logger.Log.Infof("更新IP黑名单规则成功: %s", entry.CIDR)
	c.JSON(http.StatusOK, gin.H{"entry": entry})
}

// handleDeleteIPBlacklist 删除IP黑名单规则
func (s *Server) handleDeleteIPBlacklist(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var entry database.IPBlacklist
	if err := database.DB.First(&entry, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "IP黑名单规则不存在"})
		return
	}

	if err := database.DB.Delete(&entry).Error; err != nil {
		logger.Log.Errorf("删除IP黑名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除IP黑名单规则失败"})
		return
	}

	logger.Log.Infof("删除IP黑名单规则成功: %s", entry.CIDR)
	c.JSON(http.StatusOK, gin.H{"message": "IP黑名单规则删除成功"})
}

// ==================== IP白名单 API ====================

// handleGetIPWhitelist 获取IP白名单列表
func (s *Server) handleGetIPWhitelist(c *gin.Context) {
	var whitelist []database.IPWhitelist
	if err := database.DB.Order("created_at DESC").Find(&whitelist).Error; err != nil {
		logger.Log.Errorf("获取IP白名单失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取IP白名单失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"whitelist": whitelist})
}

// handleCreateIPWhitelist 创建IP白名单规则
func (s *Server) handleCreateIPWhitelist(c *gin.Context) {
	var entry database.IPWhitelist
	if err := c.ShouldBindJSON(&entry); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	if err := database.DB.Create(&entry).Error; err != nil {
		logger.Log.Errorf("创建IP白名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建IP白名单规则失败"})
		return
	}

	logger.Log.Infof("创建IP白名单规则成功: %s", entry.IP)
	c.JSON(http.StatusCreated, gin.H{"entry": entry})
}

// handleUpdateIPWhitelist 更新IP白名单规则
func (s *Server) handleUpdateIPWhitelist(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var entry database.IPWhitelist
	if err := database.DB.First(&entry, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "IP白名单规则不存在"})
		return
	}

	var updateData database.IPWhitelist
	if err := c.ShouldBindJSON(&updateData); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 更新字段
	if updateData.IP != "" {
		entry.IP = updateData.IP
	}
	if updateData.Description != "" {
		entry.Description = updateData.Description
	}
	entry.Enabled = updateData.Enabled

	if err := database.DB.Save(&entry).Error; err != nil {
		logger.Log.Errorf("更新IP白名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新IP白名单规则失败"})
		return
	}

	logger.Log.Infof("更新IP白名单规则成功: %s", entry.IP)
	c.JSON(http.StatusOK, gin.H{"entry": entry})
}

// handleDeleteIPWhitelist 删除IP白名单规则
func (s *Server) handleDeleteIPWhitelist(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var entry database.IPWhitelist
	if err := database.DB.First(&entry, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "IP白名单规则不存在"})
		return
	}

	if err := database.DB.Delete(&entry).Error; err != nil {
		logger.Log.Errorf("删除IP白名单规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除IP白名单规则失败"})
		return
	}

	logger.Log.Infof("删除IP白名单规则成功: %s", entry.IP)
	c.JSON(http.StatusOK, gin.H{"message": "IP白名单规则删除成功"})
}
