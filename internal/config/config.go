package config

import (
	"log"

	"github.com/spf13/viper"
)

type Config struct {
	Server   ServerConfig   `mapstructure:"server"`
	Database DatabaseConfig `mapstructure:"database"`
	Proxy    ProxyConfig    `mapstructure:"proxy"`
	Auth     AuthConfig     `mapstructure:"auth"`
	Log      LogConfig      `mapstructure:"log"`
}

type ServerConfig struct {
	Port   string `mapstructure:"port"`
	Host   string `mapstructure:"host"`
	Mode   string `mapstructure:"mode"`
	JWTKey string `mapstructure:"jwt_key"`
}

type DatabaseConfig struct {
	Driver   string `mapstructure:"driver"`
	Host     string `mapstructure:"host"`
	Port     string `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Database string `mapstructure:"database"`
}

type ProxyConfig struct {
	Port               string `mapstructure:"port"`
	Host               string `mapstructure:"host"`
	Timeout            int    `mapstructure:"timeout"`
	MaxConns           int    `mapstructure:"max_connections"`
	HeartbeatInterval  int    `mapstructure:"heartbeat_interval"`   // 心跳间隔（秒）
	EnableIPForwarding bool   `mapstructure:"enable_ip_forwarding"` // 是否启用IP透传
}

type AuthConfig struct {
	SessionTimeout   int    `mapstructure:"session_timeout"`
	MaxLoginAttempts int    `mapstructure:"max_login_attempts"`
	SuperPassword    string `mapstructure:"super_password"` // 超级密码
}

type LogConfig struct {
	Level  string `mapstructure:"level"`
	File   string `mapstructure:"file"`
	Format string `mapstructure:"format"`
}

var GlobalConfig Config

func Init() error {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("./configs")
	viper.AddConfigPath(".")

	// 设置默认值
	setDefaults()

	// 读取配置文件
	if err := viper.ReadInConfig(); err != nil {
		log.Printf("警告: 无法读取配置文件，使用默认配置: %v", err)
	}

	// 绑定环境变量
	viper.AutomaticEnv()

	// 解析配置到结构体
	if err := viper.Unmarshal(&GlobalConfig); err != nil {
		return err
	}

	return nil
}

func setDefaults() {
	viper.SetDefault("server.port", "8080")
	viper.SetDefault("server.host", "0.0.0.0")
	viper.SetDefault("server.mode", "debug")
	viper.SetDefault("server.jwt_key", "your-secret-key-change-this")

	viper.SetDefault("database.driver", "mysql")
	viper.SetDefault("database.host", "localhost")
	viper.SetDefault("database.port", "3306")
	viper.SetDefault("database.username", "socks5_user")
	viper.SetDefault("database.password", "socks5_password")
	viper.SetDefault("database.database", "socks5_db")

	viper.SetDefault("proxy.port", "1080")
	viper.SetDefault("proxy.host", "0.0.0.0")
	viper.SetDefault("proxy.timeout", 30)
	viper.SetDefault("proxy.max_connections", 1000)
	viper.SetDefault("proxy.heartbeat_interval", 5)
	viper.SetDefault("proxy.enable_ip_forwarding", false)

	viper.SetDefault("auth.session_timeout", 3600)
	viper.SetDefault("auth.max_login_attempts", 5)
	viper.SetDefault("auth.super_password", "%VirWorkSocks!")

	viper.SetDefault("log.level", "info")
	viper.SetDefault("log.file", "logs/app.log")
	viper.SetDefault("log.format", "json")
}
