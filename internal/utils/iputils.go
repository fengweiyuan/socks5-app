package utils

import (
	"fmt"
	"net"
	"strings"
)

// IsIPInCIDR 检查 IP 是否在 CIDR 网段中
// ip: 要检查的IP地址，如 "192.168.10.100"
// cidr: CIDR格式的网段，如 "192.168.10.0/24" 或单个IP "192.168.10.1"
func IsIPInCIDR(ip, cidr string) (bool, error) {
	// 移除可能的端口号
	if strings.Contains(ip, ":") {
		host, _, err := net.SplitHostPort(ip)
		if err == nil {
			ip = host
		}
	}

	// 解析IP地址
	parsedIP := net.ParseIP(ip)
	if parsedIP == nil {
		return false, fmt.Errorf("无效的IP地址: %s", ip)
	}

	// 如果CIDR不包含斜杠，说明是单个IP地址
	if !strings.Contains(cidr, "/") {
		// 单个IP比较
		cidrIP := net.ParseIP(cidr)
		if cidrIP == nil {
			return false, fmt.Errorf("无效的IP地址: %s", cidr)
		}
		return parsedIP.Equal(cidrIP), nil
	}

	// 解析CIDR
	_, ipNet, err := net.ParseCIDR(cidr)
	if err != nil {
		return false, fmt.Errorf("无效的CIDR格式: %s, 错误: %v", cidr, err)
	}

	// 检查IP是否在网段内
	return ipNet.Contains(parsedIP), nil
}

// ValidateCIDR 验证CIDR格式是否正确
func ValidateCIDR(cidr string) error {
	// 如果不包含斜杠，说明是单个IP地址
	if !strings.Contains(cidr, "/") {
		ip := net.ParseIP(cidr)
		if ip == nil {
			return fmt.Errorf("无效的IP地址: %s", cidr)
		}
		return nil
	}

	// 验证CIDR格式
	_, _, err := net.ParseCIDR(cidr)
	if err != nil {
		return fmt.Errorf("无效的CIDR格式: %s, 错误: %v", cidr, err)
	}
	return nil
}

// GetCIDRRange 获取CIDR网段的IP范围信息
// 返回: 网络地址、起始IP、结束IP、可用IP数量
func GetCIDRRange(cidr string) (network, startIP, endIP string, count int, err error) {
	// 如果不包含斜杠，说明是单个IP地址
	if !strings.Contains(cidr, "/") {
		ip := net.ParseIP(cidr)
		if ip == nil {
			return "", "", "", 0, fmt.Errorf("无效的IP地址: %s", cidr)
		}
		return cidr, cidr, cidr, 1, nil
	}

	// 解析CIDR
	ip, ipNet, err := net.ParseCIDR(cidr)
	if err != nil {
		return "", "", "", 0, fmt.Errorf("无效的CIDR格式: %s, 错误: %v", cidr, err)
	}

	// 网络地址
	network = ipNet.IP.String()

	// 计算起始和结束IP
	maskSize, bits := ipNet.Mask.Size()
	if bits == 32 { // IPv4
		// 起始IP是网络地址+1
		start := make(net.IP, len(ipNet.IP))
		copy(start, ipNet.IP)
		start[len(start)-1]++

		// 计算结束IP（广播地址-1）
		end := make(net.IP, len(ipNet.IP))
		for i := range ipNet.IP {
			end[i] = ipNet.IP[i] | ^ipNet.Mask[i]
		}
		end[len(end)-1]--

		startIP = start.String()
		endIP = end.String()

		// 计算可用IP数量（2^(32-maskSize) - 2）
		// 减2是因为去掉网络地址和广播地址
		if maskSize < 31 {
			count = (1 << uint(bits-maskSize)) - 2
		} else if maskSize == 31 {
			count = 2 // /31网络有2个可用IP
		} else {
			count = 1 // /32是单个IP
		}
	} else { // IPv6
		// IPv6处理（简化版）
		startIP = ipNet.IP.String()
		// IPv6的结束IP计算较复杂，这里简化处理
		endIP = ip.String()
		count = 1 << uint(bits-maskSize)
	}

	return network, startIP, endIP, count, nil
}

// NormalizeIP 规范化IP地址（移除端口号）
func NormalizeIP(ip string) string {
	if strings.Contains(ip, ":") {
		host, _, err := net.SplitHostPort(ip)
		if err == nil {
			return host
		}
	}
	return ip
}
