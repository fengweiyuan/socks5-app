# SOCKS5 代理 IP 透传功能说明

## 功能概述

本 SOCKS5 代理服务器现在支持将客户端的真实 IP 地址透传给目标服务器，而不是隐藏客户端的 IP 地址。

## 配置说明

### 启用 IP 透传

在 `configs/config.yaml` 文件中，设置以下配置：

```yaml
proxy:
  port: "1082"
  host: "0.0.0.0"
  timeout: 30
  max_connections: 1000
  heartbeat_interval: 5
  enable_ip_forwarding: true  # 启用IP透传功能
```

- `enable_ip_forwarding: true` - 启用 IP 透传功能
- `enable_ip_forwarding: false` - 禁用 IP 透传功能（默认）

## 实现原理

### 方法1：系统调用方式（预留接口）

代码中预留了使用系统调用设置原始目标地址的接口，但由于不同操作系统的实现差异较大，目前暂未完全实现。

### 方法2：数据流插入方式（当前实现）

当前实现通过在 TCP 连接建立后，向目标服务器发送包含客户端 IP 信息的自定义协议头：

```
X-Real-IP: <client_ip>
X-Forwarded-For: <client_ip>

```

## 使用注意事项

### 1. 协议兼容性

- **HTTP 协议**：完全兼容，目标服务器可以通过 `X-Real-IP` 和 `X-Forwarded-For` 请求头获取客户端真实 IP
- **其他协议**：可能受到影响，因为会在数据流开头插入额外的信息

### 2. 目标服务器配置

如果目标服务器是 HTTP 服务器，需要配置为信任代理服务器：

#### Nginx 配置示例：
```nginx
server {
    listen 80;
    
    # 信任代理服务器
    set_real_ip_from 127.0.0.1;  # 代理服务器IP
    real_ip_header X-Real-IP;
    
    location / {
        # 现在可以通过 $remote_addr 获取真实客户端IP
        access_log /var/log/nginx/access.log;
    }
}
```

#### Apache 配置示例：
```apache
<VirtualHost *:80>
    # 启用远程IP模块
    RemoteIPHeader X-Real-IP
    RemoteIPTrustedProxy 127.0.0.1  # 代理服务器IP
    
    # 日志格式包含真实IP
    LogFormat "%a %l %u %t \"%r\" %>s %O" combined_with_real_ip
    CustomLog /var/log/apache2/access.log combined_with_real_ip
</VirtualHost>
```

## 测试方法

### 1. 启动测试服务器

```bash
cd /Users/fwy/code/pub/socks5-app/scripts
python3 test_ip_forwarding.py server 8888
```

### 2. 测试代理连接

在另一个终端中：

```bash
python3 test_ip_forwarding.py client 127.0.0.1 1082
```

### 3. 检查结果

测试服务器会显示：
- 客户端地址（应该是代理服务器的地址）
- X-Real-IP（应该是真实客户端的地址）
- X-Forwarded-For（应该是真实客户端的地址）

## 日志记录

启用 IP 透传后，代理服务器会在日志中记录相关信息：

```
[INFO] 已插入客户端IP信息到数据流: 192.168.1.100
```

## 安全考虑

1. **IP 伪造风险**：目标服务器应该验证代理服务器的可信度
2. **协议干扰**：某些协议可能无法正确处理插入的 IP 信息
3. **性能影响**：每个连接都会发送额外的 IP 信息，可能略微影响性能

## 故障排除

### 1. IP 透传不生效

- 检查配置文件中的 `enable_ip_forwarding` 是否设置为 `true`
- 查看代理服务器日志，确认是否发送了 IP 信息
- 检查目标服务器是否正确配置了 IP 头解析

### 2. 连接异常

- 如果目标服务器无法处理插入的 IP 信息，可以尝试禁用 IP 透传
- 检查目标服务器是否支持自定义协议头

### 3. 性能问题

- 如果发现性能下降，可以尝试禁用 IP 透传功能
- 监控代理服务器的 CPU 和内存使用情况

## 未来改进

1. **系统调用实现**：完善不同操作系统的系统调用实现
2. **协议检测**：根据目标协议智能选择是否插入 IP 信息
3. **加密传输**：对 IP 信息进行加密传输以提高安全性
4. **配置优化**：支持更细粒度的 IP 透传配置选项
