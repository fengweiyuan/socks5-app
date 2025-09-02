package main

import (
	"log"
	"socks5-app/internal/config"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
	"socks5-app/internal/proxy"
)

func main() {
	// 初始化配置
	if err := config.Init(); err != nil {
		log.Fatalf("配置初始化失败: %v", err)
	}

	// 初始化日志
	if err := logger.Init(); err != nil {
		log.Fatalf("日志初始化失败: %v", err)
	}

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
