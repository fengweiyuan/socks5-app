# HTTP深度检测快速开始

## 简介

这是一个增强的URL过滤功能，能够检测HTTP请求头中的Host字段和HTTPS流量中的SNI，**即使浏览器在本地做了DNS解析，只发送IP地址给代理，也能准确识别并拦截目标域名**。

## 快速开始

### 1. 配置检测开关（可选）

编辑 `configs/config.yaml`：
```yaml
proxy:
  enable_http_inspection: true  # 启用HTTP深度检测（默认：true）
```

- `true` - 启用深度检测（推荐，可识别IP访问背后的域名）
- `false` - 禁用深度检测（仅SOCKS5层过滤，性能最优）

详见：[HTTP深度检测配置说明.md](./HTTP深度检测配置说明.md)

### 2. 编译并启动服务

```bash
# 编译
make build

# 启动proxy服务
./bin/proxy

# 启动server服务（另一个终端）
./bin/server
```

查看启动日志确认配置：
```bash
tail -f logs/proxy.log | grep "HTTP深度检测"
```

预期输出：
```
[INFO] ✓ HTTP深度检测已启用 - 将检测HTTP Host头和TLS SNI
```

### 3. 创建过滤规则

访问管理后台：http://localhost:8080

登录：`admin/admin`

在"URL过滤"页面添加规则：
- Pattern: `baidu.com`
- Type: `block`
- Description: `阻止访问百度`
- Enabled: `✓`

### 4. 配置浏览器代理

**Firefox:**
1. 设置 → 网络设置 → 手动代理配置
2. SOCKS主机：`localhost` 端口：`1080`
3. SOCKS v5：✓
4. 用户名：`admin` 密码：`admin`

**Chrome (命令行启动):**
```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="socks5://localhost:1080" \
  --host-resolver-rules="MAP * ~NOTFOUND"

# Windows
chrome.exe --proxy-server="socks5://localhost:1080"

# Linux
google-chrome --proxy-server="socks5://localhost:1080"
```

### 5. 测试拦截

访问 `http://www.baidu.com`，应该会被拦截（连接断开或超时）。

查看日志：
```bash
tail -f logs/proxy.log | grep "检测到\|拦截"
```

预期日志：
```
[INFO] 检测到HTTP Host: www.baidu.com (原始目标: 220.181.38.148, 用户: admin)
[WARN] HTTP深度检测拦截: 用户 admin 访问 www.baidu.com 被阻止
```

## 工作原理

### 双层检测机制

```
┌─────────────┐
│  浏览器请求  │
│ baidu.com   │
└──────┬──────┘
       │ 浏览器本地DNS解析
       ↓
┌─────────────┐
│ SOCKS5请求  │
│220.181.38.148│ ← 只有IP地址！
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│ 第一层：SOCKS5检测   │
│ 检查IP: ✓通过        │  ← IP不在黑名单
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ 建立连接             │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ HTTP请求             │
│ GET / HTTP/1.1       │
│ Host: www.baidu.com  │ ← 域名在这里！
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ 第二层：HTTP检测     │
│ 提取Host头           │
│ 检查域名: ✗拦截     │  ← 匹配黑名单！
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ 断开连接             │
│ ❌ 拦截成功          │
└─────────────────────┘
```

### HTTP流量检测

从HTTP请求中提取Host头：
```http
GET / HTTP/1.1
Host: www.baidu.com  ← 提取这个
```

### HTTPS流量检测

从TLS ClientHello中提取SNI：
```
TLS ClientHello
  Extensions:
    SNI: www.baidu.com  ← 提取这个
```

## 测试脚本

运行自动化测试：

```bash
# 安装依赖
pip3 install requests PySocks

# 运行测试
python3 scripts/test_http_deep_inspection.py
```

测试场景：
1. HTTP Host头检测
2. HTTPS SNI检测
3. IP地址访问 + 深度检测
4. 通配符匹配

## 常见问题

### Q1: 为什么有些网站拦不住？

**A:** 可能的原因：
1. 网站使用了加密SNI (ESNI)
2. 使用了自定义协议
3. 过滤规则Pattern不匹配

**解决方案：**
- 查看日志确认是否检测到域名
- 尝试使用更宽泛的Pattern（如 `.com`）
- 添加IP地址规则作为兜底

### Q2: 拦截后浏览器显示什么？

**A:** 通常显示：
- Chrome: "ERR_CONNECTION_CLOSED" 或 "ERR_EMPTY_RESPONSE"
- Firefox: "连接已重置"
- Safari: "无法连接到服务器"

这是正常的，因为代理直接断开了连接。

### Q3: 会影响性能吗？

**A:** 性能影响极小：
- 只检测每个连接的第一个数据包
- 检测耗时：100-500微秒
- 后续数据包直接转发，无额外开销

### Q4: 支持正则表达式吗？

**A:** 当前版本使用简单的子串匹配（`strings.Contains`）。

示例：
```
Pattern: baidu.com
匹配: www.baidu.com, baidu.com, tieba.baidu.com ✓
不匹配: baidu.cn, baiducloud.com ✗

Pattern: .cn
匹配: baidu.cn, qq.cn, example.cn ✓
不匹配: china.com ✗
```

### Q5: 如何查看统计数据？

**A:** 查看日志文件：

```bash
# 统计拦截次数
grep "HTTP深度检测拦截" logs/proxy.log | wc -l

# 查看被拦截的域名
grep "HTTP深度检测拦截" logs/proxy.log | grep -oP "访问 \K[^ ]+" | sort | uniq -c

# 查看检测到的域名（包括未拦截的）
grep "检测到HTTP Host\|检测到TLS SNI" logs/proxy.log | grep -oP ": \K[^ ]+" | sort | uniq -c
```

## 高级用法

### 1. 组合规则

同时使用域名规则和IP规则：

```json
// 规则1: 域名匹配
{
  "pattern": "baidu.com",
  "type": "block",
  "enabled": true
}

// 规则2: IP匹配（兜底）
{
  "pattern": "220.181.38.148",
  "type": "block",
  "enabled": true
}
```

### 2. 分类管理

使用description字段分类：

```json
{
  "pattern": "ads.",
  "description": "[广告] 广告域名",
  "type": "block"
}

{
  "pattern": ".porn",
  "description": "[成人] 成人内容",
  "type": "block"
}
```

### 3. 临时禁用规则

不删除规则，只是禁用：

```json
{
  "pattern": "example.com",
  "enabled": false  ← 临时禁用
}
```

### 4. 监控模式

创建规则但不拦截，只记录日志（需要修改代码）：

```json
{
  "pattern": "suspicious.com",
  "type": "monitor",  // 自定义类型
  "enabled": true
}
```

## 配置选项

在 `configs/config.yaml` 中：

```yaml
proxy:
  host: "0.0.0.0"
  port: "1080"
  timeout: 300
  enable_ip_forwarding: true  # 启用IP转发（可选）
```

## 日志级别

编辑 `internal/logger/logger.go` 调整日志级别：

```go
// DEBUG: 详细的检测信息
logger.Log.Debugf("提取到Host头 = %s", host)

// INFO: 一般检测信息
logger.Log.Infof("检测到HTTP Host: %s", host)

// WARN: 拦截信息
logger.Log.Warnf("HTTP深度检测拦截: %s", host)
```

生产环境建议使用 INFO 级别。

## 与其他功能的关系

本功能与以下功能配合使用：

1. **URL过滤** - 提供过滤规则
2. **流量控制** - 限制带宽
3. **用户认证** - 不同用户不同规则（未来支持）
4. **日志系统** - 记录拦截行为
5. **WebSocket监控** - 实时查看拦截事件（未来支持）

## 下一步

- [完整功能说明](./HTTP深度检测过滤功能说明.md)
- [URL过滤功能总览](./URL过滤功能总览.md)
- [架构说明](./架构说明.md)

## 反馈与支持

如有问题，请：
1. 查看日志：`logs/proxy.log`
2. 运行测试脚本：`scripts/test_http_deep_inspection.py`
3. 检查规则配置是否正确

