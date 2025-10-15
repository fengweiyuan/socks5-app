package main

import (
	"fmt"
	"time"

	"golang.org/x/crypto/bcrypt"
)

func main() {
	password := "fwy1014"

	// 测试密码加密速度
	fmt.Println("测试bcrypt性能:")
	fmt.Println("============================================================")

	// 生成hash
	start := time.Now()
	hash, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	genTime := time.Since(start)
	fmt.Printf("\n生成hash耗时: %v\n", genTime)
	fmt.Printf("Hash: %s\n", hash)

	// 测试验证速度
	fmt.Println("\n测试验证速度 (10次):")
	times := make([]time.Duration, 10)
	for i := 0; i < 10; i++ {
		start := time.Now()
		err := bcrypt.CompareHashAndPassword(hash, []byte(password))
		elapsed := time.Since(start)
		times[i] = elapsed
		status := "✓"
		if err != nil {
			status = "✗"
		}
		fmt.Printf("  %d: %v %s\n", i+1, elapsed, status)
	}

	// 计算平均值
	var total time.Duration
	for _, t := range times {
		total += t
	}
	avg := total / time.Duration(len(times))
	fmt.Printf("\n平均验证时间: %v\n", avg)
}
