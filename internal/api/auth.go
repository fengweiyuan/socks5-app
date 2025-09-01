package api

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/auth"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
)

type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type LoginResponse struct {
	Token    string         `json:"token"`
	User     *database.User `json:"user"`
	ExpiresIn int           `json:"expires_in"`
}

func (s *Server) handleLogin(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请求参数错误"})
		return
	}

	// 验证用户凭据
	user, err := auth.AuthenticateUser(req.Username, req.Password)
	if err != nil {
		logger.Log.Warnf("登录失败: %s - %v", req.Username, err)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "用户名或密码错误"})
		return
	}

	// 生成JWT令牌
	token, err := auth.GenerateToken(user)
	if err != nil {
		logger.Log.Errorf("生成令牌失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "生成令牌失败"})
		return
	}

	// 记录登录日志
	accessLog := &database.AccessLog{
		UserID:    user.ID,
		ClientIP:  c.ClientIP(),
		TargetURL: "/api/v1/auth/login",
		Method:    "POST",
		Status:    "success",
		UserAgent: c.GetHeader("User-Agent"),
		Timestamp: user.CreatedAt,
	}
	database.DB.Create(accessLog)

	logger.Log.Infof("用户登录成功: %s", user.Username)

	c.JSON(http.StatusOK, LoginResponse{
		Token:     token,
		User:      user,
		ExpiresIn: 3600, // 1小时
	})
}

func (s *Server) handleLogout(c *gin.Context) {
	userID, _ := c.Get("user_id")
	username, _ := c.Get("username")

	// 记录登出日志
	accessLog := &database.AccessLog{
		UserID:    userID.(uint),
		ClientIP:  c.ClientIP(),
		TargetURL: "/api/v1/auth/logout",
		Method:    "POST",
		Status:    "success",
		UserAgent: c.GetHeader("User-Agent"),
		Timestamp: userID.(uint),
	}
	database.DB.Create(accessLog)

	logger.Log.Infof("用户登出: %s", username)

	c.JSON(http.StatusOK, gin.H{"message": "登出成功"})
}
