package api

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/auth"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

type CreateUserRequest struct {
	Username        string `json:"username" binding:"required"`
	Password        string `json:"password" binding:"required"`
	Email           string `json:"email"`
	Role            string `json:"role"`
	BandwidthLimit  int64  `json:"bandwidth_limit"`
}

type UpdateUserRequest struct {
	Email           string `json:"email"`
	Role            string `json:"role"`
	Status          string `json:"status"`
	BandwidthLimit  int64  `json:"bandwidth_limit"`
}

func (s *Server) handleGetUsers(c *gin.Context) {
	var users []database.User
	if err := database.DB.Find(&users).Error; err != nil {
		logger.Log.Errorf("获取用户列表失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取用户列表失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"users": users})
}

func (s *Server) handleCreateUser(c *gin.Context) {
	var req CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 检查用户名是否已存在
	var existingUser database.User
	if err := database.DB.Where("username = ?", req.Username).First(&existingUser).Error; err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "用户名已存在"})
		return
	}

	// 加密密码
	hashedPassword, err := auth.HashPassword(req.Password)
	if err != nil {
		logger.Log.Errorf("密码加密失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "密码加密失败"})
		return
	}

	// 创建用户
	user := &database.User{
		Username:       req.Username,
		Password:       hashedPassword,
		Email:          req.Email,
		Role:           req.Role,
		BandwidthLimit: req.BandwidthLimit,
		Status:         "active",
	}

	if err := database.DB.Create(user).Error; err != nil {
		logger.Log.Errorf("创建用户失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建用户失败"})
		return
	}

	logger.Log.Infof("创建用户成功: %s", user.Username)
	c.JSON(http.StatusCreated, gin.H{"user": user})
}

func (s *Server) handleGetUser(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	var user database.User
	if err := database.DB.First(&user, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"user": user})
}

func (s *Server) handleUpdateUser(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	var req UpdateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	var user database.User
	if err := database.DB.First(&user, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 更新用户信息
	updates := make(map[string]interface{})
	if req.Email != "" {
		updates["email"] = req.Email
	}
	if req.Role != "" {
		updates["role"] = req.Role
	}
	if req.Status != "" {
		updates["status"] = req.Status
	}
	if req.BandwidthLimit > 0 {
		updates["bandwidth_limit"] = req.BandwidthLimit
	}

	if err := database.DB.Model(&user).Updates(updates).Error; err != nil {
		logger.Log.Errorf("更新用户失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新用户失败"})
		return
	}

	logger.Log.Infof("更新用户成功: %s", user.Username)
	c.JSON(http.StatusOK, gin.H{"user": user})
}

func (s *Server) handleDeleteUser(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	var user database.User
	if err := database.DB.First(&user, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 检查是否为管理员用户
	if user.Role == "admin" {
		c.JSON(http.StatusForbidden, gin.H{"error": "不能删除管理员用户"})
		return
	}

	if err := database.DB.Delete(&user).Error; err != nil {
		logger.Log.Errorf("删除用户失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除用户失败"})
		return
	}

	logger.Log.Infof("删除用户成功: %s", user.Username)
	c.JSON(http.StatusOK, gin.H{"message": "用户删除成功"})
}
