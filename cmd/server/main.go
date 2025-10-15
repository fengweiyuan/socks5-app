package main

import (
	"log"
	"socks5-app/internal/api"
	"socks5-app/internal/config"
	"socks5-app/internal/database"
	"socks5-app/internal/logger"
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

	// 初始化数据库
	if err := database.Init(); err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}

	// 启动API服务器
	server := api.NewServer()
	if err := server.Run(); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}
