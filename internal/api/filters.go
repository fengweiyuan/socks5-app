package api

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

func (s *Server) handleGetURLFilters(c *gin.Context) {
	var filters []database.URLFilter
	if err := database.DB.Order("created_at DESC").Find(&filters).Error; err != nil {
		logger.Log.Errorf("获取URL过滤规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取URL过滤规则失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"filters": filters})
}

func (s *Server) handleCreateURLFilter(c *gin.Context) {
	var filter database.URLFilter
	if err := c.ShouldBindJSON(&filter); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	if err := database.DB.Create(&filter).Error; err != nil {
		logger.Log.Errorf("创建URL过滤规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建URL过滤规则失败"})
		return
	}

	logger.Log.Infof("创建URL过滤规则成功: %s", filter.Pattern)
	c.JSON(http.StatusCreated, gin.H{"filter": filter})
}

func (s *Server) handleUpdateURLFilter(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var filter database.URLFilter
	if err := database.DB.First(&filter, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "过滤规则不存在"})
		return
	}

	var updateData database.URLFilter
	if err := c.ShouldBindJSON(&updateData); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 更新字段
	if updateData.Pattern != "" {
		filter.Pattern = updateData.Pattern
	}
	if updateData.Type != "" {
		filter.Type = updateData.Type
	}
	if updateData.Description != "" {
		filter.Description = updateData.Description
	}
	filter.Enabled = updateData.Enabled

	if err := database.DB.Save(&filter).Error; err != nil {
		logger.Log.Errorf("更新URL过滤规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新URL过滤规则失败"})
		return
	}

	logger.Log.Infof("更新URL过滤规则成功: %s", filter.Pattern)
	c.JSON(http.StatusOK, gin.H{"filter": filter})
}

func (s *Server) handleDeleteURLFilter(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的规则ID"})
		return
	}

	var filter database.URLFilter
	if err := database.DB.First(&filter, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "过滤规则不存在"})
		return
	}

	if err := database.DB.Delete(&filter).Error; err != nil {
		logger.Log.Errorf("删除URL过滤规则失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除URL过滤规则失败"})
		return
	}

	logger.Log.Infof("删除URL过滤规则成功: %s", filter.Pattern)
	c.JSON(http.StatusOK, gin.H{"message": "过滤规则删除成功"})
}
