package api

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"socks5-app/internal/config"
	"socks5-app/internal/logger"
	"socks5-app/internal/middleware"
)

type Server struct {
	router *gin.Engine
}

func NewServer() *Server {
	// 设置Gin模式
	gin.SetMode(config.GlobalConfig.Server.Mode)

	router := gin.New()

	// 使用中间件
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORSMiddleware())

	server := &Server{
		router: router,
	}

	// 设置路由
	server.setupRoutes()

	return server
}

func (s *Server) setupRoutes() {
	// API v1 路由组
	v1 := s.router.Group("/api/v1")
	{
		// 认证相关路由
		auth := v1.Group("/auth")
		{
			auth.POST("/login", s.handleLogin)
			auth.POST("/logout", middleware.AuthMiddleware(), s.handleLogout)
		}

		// 需要认证的路由
		authenticated := v1.Group("")
		authenticated.Use(middleware.AuthMiddleware())
		{
			// 用户管理
			users := authenticated.Group("/users")
			{
				users.GET("", s.handleGetUsers)
				users.POST("", middleware.AdminMiddleware(), s.handleCreateUser)
				users.GET("/:id", s.handleGetUser)
				users.PUT("/:id", s.handleUpdateUser)
				users.DELETE("/:id", middleware.AdminMiddleware(), s.handleDeleteUser)
			}

			// 流量管理
			traffic := authenticated.Group("/traffic")
			{
				traffic.GET("", s.handleGetTrafficStats)
				traffic.GET("/realtime", s.handleGetRealtimeTraffic)
				traffic.POST("/limit", middleware.AdminMiddleware(), s.handleSetBandwidthLimit)
			}

			// 日志管理
			logs := authenticated.Group("/logs")
			{
				logs.GET("", s.handleGetLogs)
				logs.GET("/export", s.handleExportLogs)
				logs.DELETE("", middleware.AdminMiddleware(), s.handleClearLogs)
			}

			// 在线用户
			online := authenticated.Group("/online")
			{
				online.GET("", s.handleGetOnlineUsers)
				online.DELETE("/:id", middleware.AdminMiddleware(), s.handleDisconnectUser)
			}

			// URL过滤
			filters := authenticated.Group("/filters")
			{
				filters.GET("", s.handleGetURLFilters)
				filters.POST("", middleware.AdminMiddleware(), s.handleCreateURLFilter)
				filters.PUT("/:id", middleware.AdminMiddleware(), s.handleUpdateURLFilter)
				filters.DELETE("/:id", middleware.AdminMiddleware(), s.handleDeleteURLFilter)
			}

			// IP白名单
			whitelist := authenticated.Group("/whitelist")
			{
				whitelist.GET("", s.handleGetIPWhitelist)
				whitelist.POST("", middleware.AdminMiddleware(), s.handleAddIPWhitelist)
				whitelist.DELETE("/:id", middleware.AdminMiddleware(), s.handleRemoveIPWhitelist)
			}

			// 系统状态
			system := authenticated.Group("/system")
			{
				system.GET("/status", s.handleGetSystemStatus)
				system.GET("/stats", s.handleGetSystemStats)
			}
		}
	}

	// 静态文件服务
	s.router.Static("/static", "./web/build/static")
	s.router.StaticFile("/", "./web/build/index.html")
	s.router.StaticFile("/favicon.ico", "./web/build/favicon.ico")
}

func (s *Server) Run() error {
	addr := fmt.Sprintf("%s:%s", config.GlobalConfig.Server.Host, config.GlobalConfig.Server.Port)
	logger.Log.Infof("API服务器启动成功，监听地址: %s", addr)
	return s.router.Run(addr)
}
