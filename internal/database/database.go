package database

import (
	"fmt"
	"socks5-app/internal/config"
	"socks5-app/internal/logger"

	"gorm.io/driver/mysql"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

var DB *gorm.DB

func Init() error {
	var err error

	// 根据配置选择数据库驱动
	switch config.GlobalConfig.Database.Driver {
	case "mysql":
		dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=Local",
			config.GlobalConfig.Database.Username,
			config.GlobalConfig.Database.Password,
			config.GlobalConfig.Database.Host,
			config.GlobalConfig.Database.Port,
			config.GlobalConfig.Database.Database,
		)
		DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{
			Logger: gormlogger.Default.LogMode(gormlogger.Info),
		})
	case "sqlite":
		// 保留SQLite支持作为备选
		DB, err = gorm.Open(sqlite.Open(config.GlobalConfig.Database.Database), &gorm.Config{
			Logger: gormlogger.Default.LogMode(gormlogger.Info),
		})
	default:
		logger.Log.Fatal("不支持的数据库驱动")
	}

	if err != nil {
		return err
	}

	// 自动迁移数据库表（暂时禁用，因为表已存在）
	// if err := autoMigrate(); err != nil {
	// 	return err
	// }

	// 初始化默认数据
	if err := initDefaultData(); err != nil {
		return err
	}

	return nil
}

func autoMigrate() error {
	return DB.AutoMigrate(
		&User{},
		&ProxySession{},
		&TrafficLog{},
		&AccessLog{},
		&URLFilter{},
		&IPWhitelist{},
		&BandwidthLimit{},
	)
}

func initDefaultData() error {
	// 检查是否已有管理员用户
	var count int64
	DB.Model(&User{}).Count(&count)
	if count == 0 {
		// 创建默认管理员用户
		admin := User{
			Username: "admin",
			Password: "$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi", // password
			Role:     "admin",
			Status:   "active",
		}
		return DB.Create(&admin).Error
	}
	return nil
}

