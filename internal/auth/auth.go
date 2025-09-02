package auth

import (
	"errors"
	"time"

	"socks5-app/internal/config"
	"socks5-app/internal/database"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type Claims struct {
	UserID   uint   `json:"user_id"`
	Username string `json:"username"`
	Role     string `json:"role"`
	jwt.RegisteredClaims
}

// HashPassword 密码加密
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPassword 验证密码
func CheckPassword(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// GenerateToken 生成JWT令牌
func GenerateToken(user *database.User) (string, error) {
	expirationTime := time.Now().Add(time.Duration(config.GlobalConfig.Auth.SessionTimeout) * time.Second)
	claims := &Claims{
		UserID:   user.ID,
		Username: user.Username,
		Role:     user.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(config.GlobalConfig.Server.JWTKey))
}

// ValidateToken 验证JWT令牌
func ValidateToken(tokenString string) (*Claims, error) {
	claims := &Claims{}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(config.GlobalConfig.Server.JWTKey), nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, errors.New("无效的令牌")
	}

	return claims, nil
}

// AuthenticateUser 用户认证
func AuthenticateUser(username, password string) (*database.User, error) {
	// 数据库连接不可用时拒绝认证
	if database.DB == nil {
		return nil, errors.New("数据库连接不可用，无法进行用户认证")
	}

	var user database.User
	if err := database.DB.Where("username = ? AND status = ?", username, "active").First(&user).Error; err != nil {
		return nil, errors.New("用户不存在或已被禁用")
	}

	if !CheckPassword(password, user.Password) {
		return nil, errors.New("密码错误")
	}

	return &user, nil
}

// GetUserByID 根据ID获取用户
func GetUserByID(userID uint) (*database.User, error) {
	// 数据库连接不可用时返回错误
	if database.DB == nil {
		return nil, errors.New("数据库连接不可用")
	}

	var user database.User
	if err := database.DB.First(&user, userID).Error; err != nil {
		return nil, err
	}
	return &user, nil
}
