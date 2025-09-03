package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// JSONResponse 发送JSON响应
func JSONResponse(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		http.Error(w, "JSON编码失败", http.StatusInternalServerError)
	}
}

// ErrorResponse 发送错误响应
func ErrorResponse(w http.ResponseWriter, statusCode int, message string) {
	JSONResponse(w, statusCode, map[string]interface{}{
		"success":   false,
		"error":     message,
		"timestamp": time.Now().Unix(),
	})
}

// SuccessResponse 发送成功响应
func SuccessResponse(w http.ResponseWriter, data interface{}) {
	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success":   true,
		"data":      data,
		"timestamp": time.Now().Unix(),
	})
}

// PaginatedResponse 发送分页响应
func PaginatedResponse(w http.ResponseWriter, data interface{}, page, pageSize, total int) {
	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"data":    data,
		"pagination": map[string]interface{}{
			"page":      page,
			"page_size": pageSize,
			"total":     total,
			"pages":     (total + pageSize - 1) / pageSize,
		},
		"timestamp": time.Now().Unix(),
	})
}

// HealthResponse 发送健康检查响应
func HealthResponse(w http.ResponseWriter, service string, status string) {
	JSONResponse(w, http.StatusOK, map[string]interface{}{
		"service":   service,
		"status":    status,
		"timestamp": time.Now().Unix(),
	})
}

// GetCurrentTimestamp 获取当前时间戳
func GetCurrentTimestamp() int64 {
	return time.Now().Unix()
}

// GetCurrentTime 获取当前时间
func GetCurrentTime() time.Time {
	return time.Now()
}

// FormatTime 格式化时间
func FormatTime(t time.Time) string {
	return t.Format("2006-01-02 15:04:05")
}

// ParseTime 解析时间字符串
func ParseTime(timeStr string) (time.Time, error) {
	return time.Parse("2006-01-02 15:04:05", timeStr)
}

// GetClientIP 获取客户端IP地址
func GetClientIP(r *http.Request) string {
	// 尝试从各种header中获取真实IP
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Client-IP"); ip != "" {
		return ip
	}

	// 从RemoteAddr获取
	return r.RemoteAddr
}

// GetUserAgent 获取用户代理
func GetUserAgent(r *http.Request) string {
	return r.Header.Get("User-Agent")
}

// GetRequestID 获取请求ID（从header或生成新的）
func GetRequestID(r *http.Request) string {
	if requestID := r.Header.Get("X-Request-ID"); requestID != "" {
		return requestID
	}

	// 生成新的请求ID
	return GenerateRequestID()
}

// GenerateRequestID 生成请求ID
func GenerateRequestID() string {
	return "req_" + time.Now().Format("20060102150405") + "_" + randomString(8)
}

// randomString 生成随机字符串
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// ValidateJSON 验证JSON数据
func ValidateJSON(data []byte, v interface{}) error {
	return json.Unmarshal(data, v)
}

// ParseJSONBody 解析JSON请求体
func ParseJSONBody(r *http.Request, v interface{}) error {
	return json.NewDecoder(r.Body).Decode(v)
}

// WriteJSON 写入JSON数据
func WriteJSON(w http.ResponseWriter, data interface{}) error {
	return json.NewEncoder(w).Encode(data)
}

// SetCORSHeaders 设置CORS头
func SetCORSHeaders(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
	w.Header().Set("Access-Control-Max-Age", "86400")
}

// HandleCORS 处理CORS预检请求
func HandleCORS(w http.ResponseWriter, r *http.Request) {
	if r.Method == "OPTIONS" {
		SetCORSHeaders(w)
		w.WriteHeader(http.StatusOK)
		return
	}
}

// SetCacheHeaders 设置缓存头
func SetCacheHeaders(w http.ResponseWriter, maxAge int) {
	w.Header().Set("Cache-Control", fmt.Sprintf("public, max-age=%d", maxAge))
	w.Header().Set("Expires", time.Now().Add(time.Duration(maxAge)*time.Second).Format(time.RFC1123))
}

// SetNoCacheHeaders 设置不缓存头
func SetNoCacheHeaders(w http.ResponseWriter) {
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")
}
