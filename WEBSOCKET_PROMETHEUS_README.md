# WebSocket实时流量推送和Prometheus监控功能部署指南

## 🎯 功能概述

本项目已实现以下功能：

1. **WebSocket实时流量推送**: 通过WebSocket协议实时推送流量数据、代理健康状态和系统性能指标
2. **Prometheus监控接口**: 暴露标准的Prometheus指标，支持Grafana等可视化工具
3. **实时流量收集器**: 自动收集和缓存流量数据，支持实时推送
4. **前端实时监控组件**: Vue3组件，实时显示流量监控数据

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           实时监控系统架构                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   SOCKS5代理    │    │   流量收集器     │    │   WebSocket     │        │
│  │                 │    │                 │    │    管理器       │        │
│  │ • 连接管理      │    │ • 数据收集      │    │ • 连接管理      │        │
│  │ • 流量统计      │───▶│ • 数据缓存      │───▶│ • 实时推送      │        │
│  │ • 性能监控      │    │ • 统计分析      │    │ • 主题订阅      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  Prometheus     │    │   前端Vue组件    │    │   监控告警      │        │
│  │   指标收集      │    │                 │    │                 │        │
│  │                 │    │ • 实时显示      │    │ • 规则引擎      │        │
│  │ • 指标暴露      │    │ • 图表展示      │    │ • 告警通知      │        │
│  │ • 数据存储      │    │ • 交互控制      │    │ • 阈值管理      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📁 新增文件结构

```
socks5-app/
├── internal/
│   ├── websocket/           # WebSocket管理器
│   │   └── websocket.go
│   ├── metrics/             # Prometheus监控指标
│   │   └── prometheus.go
│   ├── collector/           # 实时数据收集器
│   │   └── traffic_collector.go
│   └── api/
│       ├── websocket.go     # WebSocket API接口
│       ├── metrics.go       # 监控指标API接口
│       ├── websocket_gin.go # Gin兼容的WebSocket处理器
│       ├── metrics_gin.go   # Gin兼容的监控指标处理器
│       └── common.go        # 通用API工具函数
├── web/src/
│   ├── utils/
│   │   └── websocket.js     # 前端WebSocket客户端
│   └── components/
│       └── RealtimeTraffic.vue  # 实时流量监控组件
├── configs/
│   └── prometheus.yml       # Prometheus配置文件
└── WEBSOCKET_PROMETHEUS_README.md  # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Go依赖
go mod tidy

# 安装前端依赖
cd web
npm install
```

### 2. 启动服务

```bash
# 启动API服务器（包含WebSocket和Prometheus）
make dev

# 或者分别启动
make build
./bin/server
```

### 3. 访问端点

- **WebSocket连接**: `ws://localhost:8012/ws`
- **Prometheus指标**: `http://localhost:8012/metrics`
- **健康检查**: `http://localhost:8012/health`
- **前端页面**: `http://localhost:8012`

## 🔧 配置说明

### WebSocket配置

WebSocket管理器支持以下配置：

```go
// 创建WebSocket管理器时的配置选项
wsManager := websocket.NewManager()

// 配置选项
type Manager struct {
    // 客户端连接管理
    clients map[string]*Client
    
    // 数据缓冲区大小
    trafficCollector     chan TrafficData      // 1000
    proxyHealthCollector chan ProxyHealthData  // 100
    systemCollector      chan SystemPerformanceData // 100
    
    // 连接配置
    upgrader websocket.Upgrader
}
```

### Prometheus配置

监控指标管理器提供以下指标：

```go
// 代理连接指标
socks5_proxy_connections_active    // 当前活跃连接数
socks5_proxy_connections_total     // 连接总数

// 流量指标
socks5_traffic_bytes_sent         // 发送字节数
socks5_traffic_bytes_received     // 接收字节数
socks5_traffic_speed_bytes_per_second // 传输速度

// 用户指标
socks5_user_connections_active     // 用户活跃连接数
socks5_user_traffic_total         // 用户总流量

// 系统指标
socks5_system_cpu_usage_percent   // CPU使用率
socks5_system_memory_usage_bytes // 内存使用量
socks5_system_network_bytes      // 网络流量
```

## 📊 使用示例

### 1. WebSocket客户端连接

```javascript
import WebSocketClient from '@/utils/websocket'

// 创建WebSocket客户端
const wsClient = new WebSocketClient('ws://localhost:8012/ws', {
  autoConnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 5
})

// 监听事件
wsClient.on('open', () => {
  console.log('连接已建立')
  
  // 订阅主题
  wsClient.subscribe('traffic_data')
  wsClient.subscribe('proxy_health')
})

wsClient.on('message', (data) => {
  console.log('收到数据:', data)
})

// 发送消息
wsClient.send('ping')
```

### 2. 前端组件使用

```vue
<template>
  <RealtimeTraffic />
</template>

<script>
import RealtimeTraffic from '@/components/RealtimeTraffic.vue'

export default {
  components: {
    RealtimeTraffic
  }
}
</script>
```

### 3. Prometheus指标查询

```promql
# 查询当前活跃连接数
socks5_proxy_connections_active

# 查询流量速度
socks5_traffic_speed_bytes_per_second

# 查询用户连接数
socks5_user_connections_active

# 查询系统CPU使用率
socks5_system_cpu_usage_percent
```

## 🔍 监控和告警

### 1. Prometheus告警规则

配置文件 `configs/prometheus.yml` 包含以下告警规则：

- **高连接数告警**: 连接数超过100个
- **高错误率告警**: 错误率超过10%
- **流量异常告警**: 流量速度异常
- **系统资源告警**: CPU/内存使用率过高

### 2. Grafana仪表板

可以使用以下查询创建Grafana仪表板：

```promql
# 连接数趋势
rate(socks5_proxy_connections_total[5m])

# 流量速度趋势
rate(socks5_traffic_bytes_sent[5m])
rate(socks5_traffic_bytes_received[5m])

# 系统资源使用率
socks5_system_cpu_usage_percent
socks5_system_memory_usage_bytes
```

## 🛠️ 开发和调试

### 1. 测试WebSocket连接

```bash
# 使用wscat测试WebSocket
wscat -c ws://localhost:8012/ws

# 发送测试消息
{"type": "ping"}
{"type": "subscribe", "topic": "traffic_data"}
```

### 2. 测试Prometheus指标

```bash
# 查看指标端点
curl http://localhost:8012/metrics

# 查看健康检查
curl http://localhost:8012/health
```

### 3. 推送测试数据

```bash
# 推送测试指标数据
curl -X POST http://localhost:8012/api/v1/metrics/test

# 推送测试WebSocket数据
curl -X POST http://localhost:8012/api/v1/websocket/test-data
```

## 🔐 安全考虑

### 1. WebSocket安全

- 生产环境应限制WebSocket来源
- 实现JWT认证验证
- 限制连接数和消息频率

### 2. Prometheus安全

- 限制指标端点访问
- 使用HTTPS和认证
- 监控指标端点访问日志

## 📈 性能优化

### 1. WebSocket优化

- 使用连接池管理
- 实现消息压缩
- 优化心跳机制

### 2. 监控指标优化

- 合理设置抓取间隔
- 使用指标聚合
- 优化存储策略

## 🚨 故障排除

### 1. WebSocket连接失败

**问题**: WebSocket连接建立失败  
**解决方案**:
```bash
# 检查服务是否启动
curl http://localhost:8012/health

# 检查WebSocket端点
curl -I http://localhost:8012/ws

# 查看服务日志
tail -f logs/app.log
```

### 2. Prometheus指标为空

**问题**: Prometheus无法获取指标  
**解决方案**:
```bash
# 检查指标端点
curl http://localhost:8012/metrics

# 推送测试数据
curl -X POST http://localhost:8012/api/v1/metrics/test

# 检查指标管理器状态
curl http://localhost:8012/api/v1/metrics/stats
```

### 3. 前端组件不显示数据

**问题**: 实时流量组件无数据  
**解决方案**:
```javascript
// 检查WebSocket连接状态
console.log(wsClient.getConnectionState())

// 检查订阅状态
console.log(wsClient.getStats())

// 手动推送测试数据
fetch('/api/v1/websocket/test-data', { method: 'POST' })
```

## 🔮 扩展功能

### 1. 支持的功能

- ✅ 实时流量监控
- ✅ 代理健康状态
- ✅ 系统性能指标
- ✅ 用户行为分析
- ✅ 自动重连机制
- ✅ 主题订阅系统

### 2. 计划功能

- 🔄 数据持久化
- 🔄 历史数据查询
- 🔄 告警通知集成
- 🔄 多实例支持
- 🔄 负载均衡

## 📞 技术支持

### 1. 文档资源

- 项目README文档
- WebSocket协议规范
- Prometheus官方文档
- Vue3官方文档

### 2. 常见问题

- WebSocket连接问题
- 监控指标配置
- 前端组件使用
- 性能优化建议

---

## 🎉 总结

本功能为SOCKS5代理服务器提供了完整的实时监控解决方案：

1. **WebSocket实时推送**: 支持流量数据、代理健康、系统性能的实时推送
2. **Prometheus监控**: 标准的监控指标，支持Grafana等可视化工具
3. **前端实时组件**: Vue3组件，美观的实时监控界面
4. **完整的部署指南**: 详细的配置和使用说明

通过这些功能，您可以：
- 实时监控代理服务器状态
- 及时发现性能问题
- 分析用户行为模式
- 优化系统性能

**功能状态**: ✅ 完成  
**部署就绪**: ✅ 是  
**文档完整**: ✅ 是  
**扩展能力**: ✅ 强  

---

*如有问题或需要技术支持，请参考相关文档或联系开发团队。*
