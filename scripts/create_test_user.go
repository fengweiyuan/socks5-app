package main

import (
	"fmt"
	"log"
	"socks5-app/internal/auth"
	"socks5-app/internal/config"
	"socks5-app/internal/database"
)

func main() {
	// 初始化配置
	if err := config.Init(); err != nil {
		log.Fatalf("配置初始化失败: %v", err)
	}

	// 初始化数据库
	if err := database.Init(); err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}

	// 生成密码哈希
	password := "123456"
	hashedPassword, err := auth.HashPassword(password)
	if err != nil {
		log.Fatalf("密码加密失败: %v", err)
	}

	fmt.Printf("密码: %s\n", password)
	fmt.Printf("哈希: %s\n", hashedPassword)

	// 创建测试用户
	user := &database.User{
		Username: "testuser3",
		Password: hashedPassword,
		Role:     "user",
		Status:   "active",
	}

	// 检查用户是否已存在
	var existingUser database.User
	if err := database.DB.Where("username = ?", user.Username).First(&existingUser).Error; err == nil {
		// 用户已存在，更新密码
		existingUser.Password = hashedPassword
		if err := database.DB.Save(&existingUser).Error; err != nil {
			log.Fatalf("更新用户失败: %v", err)
		}
		fmt.Printf("用户 %s 的密码已更新\n", user.Username)
	} else {
		// 创建新用户
		if err := database.DB.Create(user).Error; err != nil {
			log.Fatalf("创建用户失败: %v", err)
		}
		fmt.Printf("用户 %s 创建成功\n", user.Username)
	}

	fmt.Println("测试用户信息:")
	fmt.Printf("用户名: %s\n", user.Username)
	fmt.Printf("密码: %s\n", password)
	fmt.Printf("角色: %s\n", user.Role)
}
