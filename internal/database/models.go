package database

import (
	"time"

	"gorm.io/gorm"
)

// User 用户模型
type User struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	Username  string         `gorm:"uniqueIndex;not null;size:50" json:"username"`
	Password  string         `gorm:"not null;size:255" json:"-"`
	Email     string         `gorm:"size:100" json:"email"`
	Role      string         `gorm:"default:'user'" json:"role"`
	Status    string         `gorm:"default:'active'" json:"status"`
	BandwidthLimit int64     `gorm:"default:0" json:"bandwidth_limit"` // 0表示无限制
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}

// ProxySession 代理会话模型
type ProxySession struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	UserID    uint           `json:"user_id"`
	User      User           `json:"user"`
	ClientIP  string         `json:"client_ip"`
	StartTime time.Time      `json:"start_time"`
	EndTime   *time.Time     `json:"end_time"`
	BytesSent int64          `json:"bytes_sent"`
	BytesRecv int64          `json:"bytes_recv"`
	Status    string         `gorm:"default:'active'" json:"status"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

// TrafficLog 流量日志模型
type TrafficLog struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	UserID    uint           `json:"user_id"`
	User      User           `json:"user"`
	ClientIP  string         `json:"client_ip"`
	TargetIP  string         `json:"target_ip"`
	TargetPort int           `json:"target_port"`
	BytesSent int64          `json:"bytes_sent"`
	BytesRecv int64          `json:"bytes_recv"`
	Protocol  string         `json:"protocol"`
	Timestamp time.Time      `json:"timestamp"`
	CreatedAt time.Time      `json:"created_at"`
}

// AccessLog 访问日志模型
type AccessLog struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	UserID    uint           `json:"user_id"`
	User      User           `json:"user"`
	ClientIP  string         `json:"client_ip"`
	TargetURL string         `json:"target_url"`
	Method    string         `json:"method"`
	Status    string         `json:"status"`
	UserAgent string         `json:"user_agent"`
	Timestamp time.Time      `json:"timestamp"`
	CreatedAt time.Time      `json:"created_at"`
}

// URLFilter URL过滤规则模型
type URLFilter struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	Pattern   string         `gorm:"not null" json:"pattern"`
	Type      string         `gorm:"default:'block'" json:"type"` // block, allow
	Description string       `json:"description"`
	Enabled   bool           `gorm:"default:true" json:"enabled"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

// IPWhitelist IP白名单模型
type IPWhitelist struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	IP        string         `gorm:"not null" json:"ip"`
	Description string       `json:"description"`
	Enabled   bool           `gorm:"default:true" json:"enabled"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

// BandwidthLimit 带宽限制模型
type BandwidthLimit struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	UserID    uint           `json:"user_id"`
	User      User           `json:"user"`
	Limit     int64          `gorm:"not null" json:"limit"` // 字节/秒
	Period    string         `gorm:"default:'daily'" json:"period"` // daily, monthly
	Enabled   bool           `gorm:"default:true" json:"enabled"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

