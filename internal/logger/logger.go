package logger

import (
	"os"
	"path/filepath"
	"socks5-app/internal/config"

	"github.com/sirupsen/logrus"
)

var Log *logrus.Logger

func Init() error {
	Log = logrus.New()

	// 设置日志级别
	level, err := logrus.ParseLevel(config.GlobalConfig.Log.Level)
	if err != nil {
		level = logrus.InfoLevel
	}
	Log.SetLevel(level)

	// 设置日志格式
	if config.GlobalConfig.Log.Format == "json" {
		Log.SetFormatter(&logrus.JSONFormatter{})
	} else {
		Log.SetFormatter(&logrus.TextFormatter{
			FullTimestamp: true,
		})
	}

	// 设置日志输出
	if config.GlobalConfig.Log.File != "" {
		// 确保日志目录存在
		logDir := filepath.Dir(config.GlobalConfig.Log.File)
		if err := os.MkdirAll(logDir, 0755); err != nil {
			return err
		}

		// 打开日志文件
		file, err := os.OpenFile(config.GlobalConfig.Log.File, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			return err
		}

		// 同时输出到文件和控制台
		Log.SetOutput(file)
		Log.AddHook(&ConsoleHook{})
	}

	return nil
}

// ConsoleHook 用于同时输出到控制台
type ConsoleHook struct{}

func (h *ConsoleHook) Levels() []logrus.Level {
	return logrus.AllLevels
}

func (h *ConsoleHook) Fire(entry *logrus.Entry) error {
	// 输出到控制台
	_, err := os.Stdout.Write([]byte(entry.Message + "\n"))
	return err
}

