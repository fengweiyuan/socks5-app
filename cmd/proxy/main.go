package main

import (
	"log"
	"net/http"
	_ "net/http/pprof"
	"socks5-app/internal/config"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
	"socks5-app/internal/proxy"
	"time"
)

func main() {
	// 设置全局时区为东8区（Asia/Shanghai）
	location, err := time.LoadLocation("Asia/Shanghai")
	if err != nil {
		log.Printf("警告: 加载时区失败，使用本地时区: %v", err)
	} else {
		time.Local = location
		log.Printf("已设置全局时区为: Asia/Shanghai (UTC+8)")
	}

	// 初始化配置
	if err := config.Init(); err != nil {
		log.Fatalf("配置初始化失败: %v", err)
	}

	// 初始化日志
	if err := logger.Init(); err != nil {
		log.Fatalf("日志初始化失败: %v", err)
	}

	// 启动性能监控服务（pprof）
	go func() {
		logger.Log.Info("启动pprof性能监控服务: http://localhost:6060/debug/pprof/")
		if err := http.ListenAndServe("localhost:6060", nil); err != nil {
			logger.Log.Errorf("pprof服务启动失败: %v", err)
		}
	}()

	// 尝试初始化数据库（失败时不影响代理服务启动）
	if err := database.Init(); err != nil {
		logger.Log.Warnf("数据库初始化失败，代理服务将在无数据库模式下运行: %v", err)
	}

	// 启动SOCKS5代理服务器
	proxyServer := proxy.NewServer()
	if err := proxyServer.Start(); err != nil {
		log.Fatalf("代理服务器启动失败: %v", err)
	}
}
