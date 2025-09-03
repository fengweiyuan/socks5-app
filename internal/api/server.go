package api

import (
	"fmt"
	"strings"

	"socks5-app/internal/collector"
	"socks5-app/internal/config"
	"socks5-app/internal/logger"
	"socks5-app/internal/metrics"
	"socks5-app/internal/middleware"
	"socks5-app/internal/websocket"

	"github.com/gin-gonic/gin"
)

type Server struct {
	router *gin.Engine

	// WebSocket管理器
	wsManager *websocket.Manager

	// 监控指标管理器
	metricsManager *metrics.MetricsManager

	// 流量收集器
	trafficCollector *collector.TrafficCollector

	// WebSocket处理器
	wsHandler *WebSocketHandler

	// 监控指标处理器
	metricsHandler *MetricsHandler
}

func NewServer() *Server {
	// 设置Gin模式
	gin.SetMode(config.GlobalConfig.Server.Mode)

	router := gin.New()

	// 使用中间件
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORSMiddleware())

	// 创建WebSocket管理器
	wsManager := websocket.NewManager()

	// 创建监控指标管理器
	metricsManager := metrics.NewMetricsManager()

	// 创建流量收集器
	trafficCollector := collector.NewTrafficCollector(wsManager, nil)

	// 创建处理器
	wsHandler := NewWebSocketHandler(wsManager)
	metricsHandler := NewMetricsHandler(metricsManager)

	server := &Server{
		router:           router,
		wsManager:        wsManager,
		metricsManager:   metricsManager,
		trafficCollector: trafficCollector,
		wsHandler:        wsHandler,
		metricsHandler:   metricsHandler,
	}

	// 设置路由
	server.setupRoutes()

	// 启动WebSocket管理器
	wsManager.Start()

	// 启动流量收集器
	trafficCollector.Start()

	// 启动监控指标收集器
	metricsManager.StartCollector()

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

			// 代理健康状态
			proxy := authenticated.Group("/proxy")
			{
				proxy.GET("/health", s.handleGetProxyHealth)
				proxy.GET("/heartbeat", s.handleGetHeartbeatRecords)
				proxy.GET("/status", s.handleGetProxyStatus)
				proxy.POST("/cleanup", middleware.AdminMiddleware(), s.handleCleanupHeartbeats)
			}

			// WebSocket相关路由
			websocket := authenticated.Group("/websocket")
			{
				websocket.GET("/stats", s.wsHandler.GetConnectionStatsGin)
				websocket.GET("/status", s.wsHandler.GetStatusGin)
				websocket.POST("/test-data", s.wsHandler.PushTestDataGin)
			}

			// 监控指标相关路由
			metrics := authenticated.Group("/metrics")
			{
				metrics.GET("/stats", s.metricsHandler.GetMetricsStatsGin)
				metrics.GET("/config", s.metricsHandler.GetMetricsConfigGin)
				metrics.GET("/available", s.metricsHandler.GetAvailableMetricsGin)
				metrics.POST("/reset", middleware.AdminMiddleware(), s.metricsHandler.ResetMetricsGin)
				metrics.POST("/test", s.metricsHandler.RecordTestMetricsGin)
			}
		}
	}

	// WebSocket连接端点（不需要认证）
	s.router.GET("/ws", s.wsHandler.HandleWebSocketGin)

	// Prometheus监控指标端点（不需要认证）
	s.router.GET("/metrics", s.metricsHandler.HandleMetricsGin)

	// 健康检查端点（不需要认证）
	s.router.GET("/health", s.metricsHandler.HandleHealthCheckGin)

	// 静态文件服务
	s.router.Static("/static", "./web/build/static")
	s.router.StaticFile("/favicon.ico", "./web/build/favicon.ico")

	// 处理前端路由 - 所有未匹配的路径都返回index.html
	s.router.NoRoute(func(c *gin.Context) {
		// 如果是API请求，返回404
		if strings.HasPrefix(c.Request.URL.Path, "/api/") {
			c.JSON(404, gin.H{"error": "API endpoint not found"})
			return
		}

		// 其他所有路径都返回index.html，让前端路由处理
		c.File("./web/build/index.html")
	})
}

func (s *Server) Run() error {
	addr := fmt.Sprintf("%s:%s", config.GlobalConfig.Server.Host, config.GlobalConfig.Server.Port)
	logger.Log.Infof("API服务器启动成功，监听地址: %s", addr)
	logger.Log.Infof("WebSocket端点: ws://%s/ws", addr)
	logger.Log.Infof("Prometheus指标端点: http://%s/metrics", addr)
	logger.Log.Infof("健康检查端点: http://%s/health", addr)
	return s.router.Run(addr)
}

// 获取WebSocket管理器
func (s *Server) GetWebSocketManager() *websocket.Manager {
	return s.wsManager
}

// 获取监控指标管理器
func (s *Server) GetMetricsManager() *metrics.MetricsManager {
	return s.metricsManager
}

// 获取流量收集器
func (s *Server) GetTrafficCollector() *collector.TrafficCollector {
	return s.trafficCollector
}
