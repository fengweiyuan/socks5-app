# HTTP深度检测过滤功能说明

## 功能概述

本功能实现了基于HTTP/HTTPS流量的深度包检测（DPI），能够在SOCKS5代理层面检测并拦截特定域名的访问，**即使浏览器在本地已经完成DNS解析，只发送IP地址给代理**。

## 问题背景

### 原有问题

在SOCKS5代理中，当浏览器在本地完成DNS解析后，发送给代理的请求中只包含IP地址，不包含域名信息。例如：

- 管理员设置拦截规则：`baidu.com`
- 浏览器本地解析得到：`220.181.38.148`
- SOCKS5请求中只有：`220.181.38.148` (IP地址)
- 代理无法识别这是访问 `baidu.com`，拦截失败 ❌

### 解决方案

通过深度包检测技术，从HTTP/HTTPS流量中提取真实域名：

1. **HTTP流量**：提取 `Host` 请求头
2. **HTTPS流量**：提取TLS握手中的 `SNI` (Server Name Indication)

## 工作原理

### 检测流程

```
浏览器 → SOCKS5代理 → 目标服务器
        ↓
    1. SOCKS5层检测 (IP/域名)
        ↓
    2. 应用层检测 (HTTP Host / TLS SNI)
        ↓
    3. URL过滤规则匹配
        ↓
    4. 允许/拦截
```

### 详细步骤

1. **SOCKS5握手阶段**
   - 客户端发送目标地址（可能是IP或域名）
   - 代理进行第一次URL过滤检查
   - 如果通过，建立与目标服务器的连接

2. **数据转发阶段**
   - 监测客户端发送的第一个数据包
   - 检测是否为HTTP请求或TLS握手
   - 提取域名信息

3. **深度过滤**
   - 使用提取的域名再次进行URL过滤检查
   - 如果匹配拦截规则，立即断开连接

## 技术实现

### HTTP Host 头检测

HTTP请求示例：
```http
GET / HTTP/1.1
Host: www.baidu.com          ← 提取这个
User-Agent: Mozilla/5.0
Accept: */*
```

即使SOCKS5目标是IP地址 `220.181.38.148`，HTTP的Host头仍然包含原始域名 `www.baidu.com`。

### TLS SNI 检测

HTTPS（TLS）握手示例：
```
ClientHello
├─ Version: TLS 1.2
├─ Random: [...]
├─ Cipher Suites: [...]
└─ Extensions:
   └─ SNI: www.baidu.com     ← 提取这个
```

TLS握手时，客户端会通过SNI扩展告知服务器要访问的域名（用于支持多域名共享同一IP的场景）。

## 使用方法

### 1. 创建过滤规则

在管理后台创建URL过滤规则：

```json
{
  "pattern": "baidu.com",
  "type": "block",
  "description": "阻止访问百度",
  "enabled": true
}
```

### 2. 规则匹配逻辑

系统会在**两个层面**进行检测：

#### 第一层：SOCKS5层检测
- 检测目标：SOCKS5请求中的地址（IP或域名）
- 如果匹配拦截规则，直接拒绝连接

#### 第二层：应用层检测（新增）
- 检测目标：HTTP Host头 或 TLS SNI
- 如果匹配拦截规则，断开已建立的连接

**只要任何一层匹配到拦截规则，都会阻止访问**

### 3. 日志记录

当检测到域名时，会记录详细日志：

```
INFO: 检测到HTTP Host: www.baidu.com (原始目标: 220.181.38.148, 用户: testuser)
WARN: HTTP深度检测拦截: 用户 testuser 访问 www.baidu.com 被阻止 (原始地址: 220.181.38.148)
```

## 支持的协议

### ✅ 支持的协议

| 协议 | 检测方法 | 说明 |
|------|----------|------|
| HTTP | Host头 | 明文HTTP请求 |
| HTTPS | SNI | TLS 1.0+ |
| HTTP/2 | SNI | 基于TLS的HTTP/2 |
| WebSocket | Host头 | 基于HTTP的WebSocket |
| WebSocket Secure | SNI | 基于HTTPS的WebSocket |

### ❌ 不支持的协议

| 协议 | 原因 |
|------|------|
| 加密DNS (DoH/DoT) | 域名已加密 |
| 自定义加密协议 | 无标准域名字段 |
| 纯TCP/UDP协议 | 无域名信息 |
| TLS 1.3 ECH | SNI已加密 (未来可能) |

## 测试示例

### 场景1：拦截百度访问（浏览器本地DNS解析）

1. **配置规则**
```
Pattern: baidu.com
Type: block
Enabled: true
```

2. **用户访问**
```bash
# 浏览器配置SOCKS5代理
# 访问 http://www.baidu.com
```

3. **预期结果**
- SOCKS5层：目标是IP地址，第一次检查通过
- 应用层：检测到HTTP Host: www.baidu.com，匹配规则
- **连接被断开，拦截成功** ✅

### 场景2：拦截HTTPS网站

1. **配置规则**
```
Pattern: google.com
Type: block
Enabled: true
```

2. **用户访问**
```bash
# 访问 https://www.google.com
```

3. **预期结果**
- TLS握手时检测到SNI: www.google.com
- 匹配规则，**连接被断开，拦截成功** ✅

### 场景3：通配符匹配

规则支持包含匹配：

```
Pattern: .cn
→ 拦截所有 .cn 域名

Pattern: ads
→ 拦截包含 "ads" 的域名（如 ads.example.com）
```

## 日志示例

### 成功拦截日志

```log
[INFO] 2024-10-12 10:30:15 checkURLFilter被调用 - 用户: testuser (Role:user), 目标: 220.181.38.148
[INFO] 2024-10-12 10:30:15 查询到 3 条启用的过滤规则
[INFO] 2024-10-12 10:30:15 URL过滤检查通过: 220.181.38.148 (第一层)
[INFO] 2024-10-12 10:30:15 检测到HTTP Host: www.baidu.com (原始目标: 220.181.38.148, 用户: testuser)
[WARN] 2024-10-12 10:30:15 URL过滤: 阻止访问 | 用户: testuser (ID:2) | 目标地址: www.baidu.com | 匹配规则: [ID:1] Pattern:'baidu.com' | 描述: 阻止百度
[WARN] 2024-10-12 10:30:15 HTTP深度检测拦截: 用户 testuser 访问 www.baidu.com 被阻止 (原始地址: 220.181.38.148)
```

### 正常访问日志

```log
[INFO] 2024-10-12 10:31:20 检测到TLS SNI: www.example.com (原始目标: 93.184.216.34, 用户: testuser)
[INFO] 2024-10-12 10:31:20 URL过滤检查通过: www.example.com
```

## 性能影响

### 计算开销

- **第一个数据包检测**：~100-500μs
- **后续数据包**：无额外开销（直接转发）
- **内存占用**：每个连接约 8KB 缓冲区

### 优化措施

1. **只检测第一个包**：使用 `inspectedFirstPkt` 标记
2. **无锁快速路径**：已检测的连接直接转发
3. **异步日志**：日志写入不阻塞数据转发

## 限制与注意事项

### 1. 加密SNI (ESNI/ECH)

未来TLS 1.3可能广泛使用加密SNI，届时无法提取域名。
- **影响**：无法检测HTTPS流量的真实域名
- **应对**：需要强制客户端使用远程DNS

### 2. HTTP/2和HTTP/3

- HTTP/2基于TLS：可以通过SNI检测 ✅
- HTTP/3基于QUIC(UDP)：当前版本不支持 ❌

### 3. 自定义协议

使用自定义加密协议的应用无法检测：
- 游戏客户端
- P2P应用
- VPN协议

### 4. 第一个包大小

如果第一个数据包被分片，可能检测失败。但这种情况很少见，因为：
- TLS ClientHello通常 <1KB
- HTTP请求头通常 <1KB
- MTU通常是1500字节

## 最佳实践

### 1. 组合使用多种规则

```
# 域名规则
Pattern: baidu.com

# IP规则（兜底）
Pattern: 220.181.38.148
Pattern: 220.181.38.251
```

### 2. 定期更新IP规则

某些网站的IP会变化，建议：
- 定期重新解析域名
- 更新IP过滤规则

### 3. 使用通配符

```
Pattern: .ads.
Pattern: -ad-
Pattern: /ads/
```

### 4. 监控日志

定期检查日志，了解：
- 哪些域名被频繁访问
- 哪些拦截规则被命中
- 是否有误拦截

## 故障排查

### 问题1：规则不生效

**检查项：**
1. 规则是否启用 (`enabled = true`)
2. Pattern是否正确（大小写敏感）
3. 查看日志是否有检测记录

### 问题2：HTTPS拦截失败

**可能原因：**
1. 使用了加密SNI (ESNI)
2. 使用了非标准端口
3. 第一个数据包被分片

**解决方案：**
- 添加IP规则作为兜底
- 使用更通用的模式匹配

### 问题3：性能下降

**检查项：**
1. 过滤规则数量（建议<1000条）
2. 日志级别（生产环境使用INFO）
3. 并发连接数

## 代码结构

```
internal/proxy/
├── socks5.go              # 主代理逻辑
├── http_inspector.go      # HTTP/HTTPS检测器（新增）
└── ...

关键函数：
- ExtractHost()            # 提取HTTP Host头
- ExtractSNI()             # 提取TLS SNI
- checkURLFilter()         # URL过滤检查
- forwardData()            # 数据转发（含检测逻辑）
```

## 后续改进方向

1. **支持正则表达式**：更灵活的规则匹配
2. **域名分类**：按类别管理（广告、社交、色情等）
3. **统计报表**：记录被拦截的域名访问统计
4. **白名单优先**：支持白名单模式
5. **机器学习**：基于行为的智能拦截

## 相关文档

- [URL过滤功能快速开始.md](../URL过滤功能快速开始.md)
- [URL过滤测试报告.md](./URL过滤测试报告.md)
- [架构说明.md](./架构说明.md)

## 技术支持

如有问题，请查看日志：
```bash
tail -f logs/proxy.log | grep "检测到"
tail -f logs/proxy.log | grep "拦截"
```

