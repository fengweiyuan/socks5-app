package database

import (
	"fmt"
	"socks5-app/internal/config"
	"socks5-app/internal/logger"
	"time"

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
		// 使用东8区（Asia/Shanghai）时区进行时间处理
		dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=Asia%%2FShanghai",
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
		logger.Log.Error("不支持的数据库驱动")
		return fmt.Errorf("不支持的数据库驱动: %s", config.GlobalConfig.Database.Driver)
	}

	if err != nil {
		logger.Log.Errorf("数据库连接失败: %v", err)
		DB = nil // 确保DB为nil
		return err
	}

	// 配置连接池（性能优化）
	sqlDB, err := DB.DB()
	if err != nil {
		logger.Log.Errorf("获取数据库连接池失败: %v", err)
	} else {
		// 设置最大打开连接数
		sqlDB.SetMaxOpenConns(100)
		// 设置最大空闲连接数
		sqlDB.SetMaxIdleConns(20)
		// 设置连接最大存活时间
		sqlDB.SetConnMaxLifetime(time.Hour)
		// 设置连接最大空闲时间
		sqlDB.SetConnMaxIdleTime(10 * time.Minute)
		logger.Log.Info("数据库连接池配置完成: MaxOpenConns=100, MaxIdleConns=20")
	}

	logger.Log.Info("数据库连接成功")

	// 自动迁移数据库表
	if err := autoMigrate(); err != nil {
		logger.Log.Errorf("数据库表迁移失败: %v", err)
		// 迁移失败不影响服务启动，只记录错误
		logger.Log.Warn("数据库表迁移失败，某些功能可能不可用")
	}

	// 初始化默认数据
	if err := initDefaultData(); err != nil {
		logger.Log.Errorf("初始化默认数据失败: %v", err)
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
		&IPBlacklist{},
		&BandwidthLimit{},
		&ProxyHeartbeat{},
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
