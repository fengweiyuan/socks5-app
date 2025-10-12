# 测试指南

## 快速开始

### 1. 启动服务

```bash
# 终端1：启动proxy服务
cd /Users/fwy/code/pub/socks5-app
./bin/proxy

# 终端2：启动server服务
cd /Users/fwy/code/pub/socks5-app
./bin/server
```

### 2. 安装测试依赖

```bash
pip3 install requests PySocks
```

### 3. 运行全面测试

```bash
# 运行双层检测机制测试
python3 scripts/test_comprehensive_filtering.py
```

### 4. 查看日志

```bash
# 实时查看proxy日志
tail -f logs/proxy.log | grep '检测到\|拦截'

# 查看统计
grep "检测到HTTP Host" logs/proxy.log | wc -l
grep "HTTP深度检测拦截" logs/proxy.log | wc -l
```

## 测试脚本说明

### test_comprehensive_filtering.py

**全面测试脚本** - 验证双层检测机制

**测试场景：**
- 场景A: SOCKS5层拦截测试
- 场景B: HTTP深度检测测试  
- 场景C: HTTPS SNI检测
- 场景D: 双层协调测试
- 场景E: 边界情况测试
- 场景F: 性能基准测试

**预期结果：**
```
总测试数: 15
通过: 15 ✅
失败: 0 ❌
通过率: 100.0%
```

### test_http_deep_inspection.py

**HTTP深度检测专项测试**

**测试场景：**
- HTTP Host头检测
- HTTPS SNI检测
- IP地址访问+深度检测
- 通配符匹配

## 其他测试脚本

```bash
# URL过滤基础测试
python3 scripts/test_url_filter_simple.py

# URL过滤综合测试
python3 scripts/test_url_filter_comprehensive.py

# 流量控制测试
python3 scripts/test_traffic_control.py

# 用户管理测试
python3 scripts/test_user_management_logs.py
```

## 测试配置

确保 `configs/config.yaml` 中启用了HTTP深度检测：

```yaml
proxy:
  enable_http_inspection: true  # 必须为true
```

## 故障排查

### 测试失败？

1. **检查服务是否运行**
```bash
ps aux | grep -E "proxy|server"
```

2. **检查端口是否监听**
```bash
lsof -i :1080  # proxy
lsof -i :8080  # server
```

3. **检查配置**
```bash
cat configs/config.yaml | grep enable_http_inspection
```

4. **查看日志**
```bash
tail -50 logs/proxy.log
tail -50 logs/server.log
```

### 网络问题？

```bash
# 测试代理连接
curl --proxy socks5://admin:admin@localhost:1080 http://httpbin.org/get

# 测试API连接
curl http://localhost:8080/api/health
```

## 测试文档

详细的测试文档：
- [双层检测机制测试报告.md](../docs/双层检测机制测试报告.md)
- [HTTP深度检测功能说明.md](../docs/HTTP深度检测过滤功能说明.md)

## 性能测试

### 基准测试

```bash
# 简单性能测试
time python3 scripts/test_comprehensive_filtering.py

# 并发测试（需要额外工具）
ab -n 1000 -c 10 -X localhost:1080 http://httpbin.org/get
```

### 性能指标

- 连接建立延迟：< 20ms
- 首包检测延迟：< 1ms  
- 吞吐量影响：< 5%

## 持续集成

未来可以集成到CI/CD：

```bash
# 在CI中运行
#!/bin/bash
set -e

# 启动服务
./bin/proxy &
PROXY_PID=$!
./bin/server &
SERVER_PID=$!

sleep 5

# 运行测试
python3 scripts/test_comprehensive_filtering.py

# 清理
kill $PROXY_PID $SERVER_PID
```

## 联系支持

如有问题，请查看：
1. 日志文件：`logs/proxy.log`, `logs/server.log`
2. 配置文件：`configs/config.yaml`
3. 文档目录：`docs/`

