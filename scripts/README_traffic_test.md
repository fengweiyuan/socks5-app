# SOCKS5 代理流量测试脚本

本目录包含了用于测试 SOCKS5 代理流量统计功能的 Python 脚本。

## 脚本说明

### 1. `traffic_generator.py` - 完整功能流量生成器
功能最全面的流量测试脚本，支持多种模式和配置选项。

**使用方法：**
```bash
# 查看帮助
python3 scripts/traffic_generator.py --help

# 持续生成混合流量
python3 scripts/traffic_generator.py --mode continuous

# 生成 HTTP 流量，持续 60 秒
python3 scripts/traffic_generator.py --mode http --duration 60

# 生成 HTTPS 流量，持续 120 秒，间隔 2 秒
python3 scripts/traffic_generator.py --mode https --duration 120 --interval 2

# 生成大文件下载流量
python3 scripts/traffic_generator.py --mode large --duration 300

# 使用认证
python3 scripts/traffic_generator.py --username testuser --password testpass
```

**参数说明：**
- `--proxy-host`: 代理服务器地址 (默认: localhost)
- `--proxy-port`: 代理服务器端口 (默认: 1082)
- `--username`: 代理认证用户名
- `--password`: 代理认证密码
- `--mode`: 流量生成模式 (http/https/large/continuous)
- `--duration`: 持续时间(秒)
- `--interval`: 请求间隔(秒)

### 2. `simple_traffic_test.py` - 简单流量测试
交互式简单测试脚本，适合快速验证代理连接。

**使用方法：**
```bash
python3 scripts/simple_traffic_test.py
```

### 3. `authenticated_traffic_test.py` - 带认证流量测试
支持用户名密码认证的流量测试脚本。

**使用方法：**
```bash
python3 scripts/authenticated_traffic_test.py
```

### 4. `no_auth_traffic_test.py` - 无认证流量测试
测试无认证模式的代理连接。

**使用方法：**
```bash
python3 scripts/no_auth_traffic_test.py
```

## 安装依赖

运行以下命令安装所需的 Python 包：

```bash
python3 scripts/install_traffic_deps.py
```

或者手动安装：

```bash
pip install requests PySocks
```

## 测试用户

如果代理需要认证，可以使用以下测试用户：

- 用户名: `testuser`
- 密码: `testpass`

或者使用数据库中的其他用户：
- 用户名: `admin`
- 用户名: `fwy`

## 使用建议

1. **首次测试**：先运行 `simple_traffic_test.py` 验证代理连接
2. **持续测试**：使用 `traffic_generator.py --mode continuous` 进行长期流量生成
3. **观察统计**：在 Web 管理界面 (http://localhost:8012) 的「流量管理」页面观察实时统计
4. **性能测试**：使用 `--mode large` 测试大文件下载性能

## 故障排除

### 认证失败
```
Socket error: All offered SOCKS5 authentication methods were rejected
```
**解决方案：**
1. 检查用户名和密码是否正确
2. 确认用户状态为 `active`
3. 尝试使用 `authenticated_traffic_test.py` 脚本

### 连接超时
```
Max retries exceeded
```
**解决方案：**
1. 检查代理服务是否正常运行
2. 确认代理端口是否正确 (默认 1082)
3. 检查网络连接

### 依赖包问题
```
ModuleNotFoundError: No module named 'requests'
```
**解决方案：**
```bash
python3 scripts/install_traffic_deps.py
```

## 监控流量统计

运行流量测试脚本后，可以在以下位置查看统计信息：

1. **Web 管理界面**: http://localhost:8012
   - 登录后进入「流量管理」页面
   - 查看实时流量监控图表
   - 查看流量日志

2. **数据库查询**:
```sql
-- 查看流量日志
SELECT * FROM traffic_logs ORDER BY timestamp DESC LIMIT 10;

-- 查看代理会话
SELECT * FROM proxy_sessions WHERE status = 'active';

-- 查看用户统计
SELECT username, COUNT(*) as session_count 
FROM proxy_sessions 
JOIN users ON proxy_sessions.user_id = users.id 
GROUP BY username;
```

## 注意事项

1. 流量测试会消耗网络带宽，请根据网络环境调整参数
2. 长时间运行测试时，注意监控系统资源使用情况
3. 测试完成后记得停止脚本，避免不必要的流量消耗
4. 某些测试网站可能有访问限制，如遇到 429 错误可增加请求间隔
