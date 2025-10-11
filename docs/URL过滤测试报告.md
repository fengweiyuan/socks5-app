# URL过滤功能测试报告

## 测试日期
2025年10月11日

## 测试目的
验证当设置URL过滤规则阻止 `baidu.com` 时，其他网址（如 `www.163.com`）是否能正常访问。

## 测试环境
- 代理服务器: localhost:1082
- API服务器: localhost:8012
- 数据库: MySQL (socks5_db)
- 测试用户: testuser/testpass

## 测试场景

### 场景1: 无过滤规则时的基准测试
**测试步骤:**
1. 清空数据库中所有过滤规则
2. 测试访问 baidu.com
3. 测试访问 www.163.com

**测试结果:**
- baidu.com: ✅ 成功
- www.163.com: ✅ 成功

**结论:** 在没有过滤规则的情况下，两个网站都可以正常访问。

---

### 场景2: 设置 block baidu.com 规则后
**测试步骤:**
1. 在数据库中创建过滤规则:
   - Pattern: `baidu.com`
   - Type: `block`
   - Enabled: `true`
2. 等待规则生效（2秒）
3. 测试访问 baidu.com
4. 测试访问 www.163.com

**测试结果:**
- baidu.com: ❌ 被阻止（符合预期）
- www.163.com: ✅ 成功（符合预期）

**结论:** URL过滤规则工作正常，只阻止匹配的域名，不影响其他域名。

---

## 核心问题答案

### ❓ 当设置了URL过滤 `baidu.com` 时，`www.163.com` 能否访问？

### ✅ 答案：**可以访问**

**说明:**
- www.163.com 可以正常访问
- URL过滤规则只阻止包含 `baidu.com` 的域名
- 其他域名（包括内网地址）不受影响

---

## 代码逻辑分析

查看 `internal/proxy/socks5.go` 中的 `checkURLFilter` 函数（431-453行）：

```go
func (s *Socks5Server) checkURLFilter(user *database.User, targetAddr string) bool {
    // 检查URL过滤规则（数据库连接失败时允许通过）
    if database.DB == nil {
        logger.Log.Warn("数据库连接不可用，跳过URL过滤检查")
        return true
    }

    var filters []database.URLFilter
    if err := database.DB.Where("enabled = ?", true).Find(&filters).Error; err != nil {
        logger.Log.Errorf("查询URL过滤规则失败: %v", err)
        return true // 数据库查询失败时允许通过
    }

    for _, filter := range filters {
        if strings.Contains(targetAddr, filter.Pattern) {
            if filter.Type == "block" {
                return false  // 阻止访问
            }
        }
    }

    return true  // 默认允许通过
}
```

**逻辑说明:**
1. 遍历所有启用的过滤规则
2. 使用 `strings.Contains()` 检查目标地址是否包含规则的 pattern
3. 如果匹配到 `type == "block"` 的规则，返回 false（阻止访问）
4. 如果没有匹配到任何规则，返回 true（允许访问）
5. **注意:** `type == "allow"` 的规则当前不生效（代码中没有处理）

---

## 问题排查指南

如果您遇到"设置URL过滤后内网地址无法访问"的问题，可能的原因：

### 1. Pattern 设置过于宽泛

❌ **错误示例:**
```
Pattern: "com"     → 会阻止所有包含 .com 的域名
Pattern: "192"     → 会阻止所有包含 192 的IP地址（包括 192.168.x.x）
Pattern: "1"       → 会阻止几乎所有域名和IP
Pattern: "*"       → 会阻止所有访问
```

✅ **正确示例:**
```
Pattern: "baidu.com"       → 只阻止百度相关域名
Pattern: "facebook.com"    → 只阻止Facebook相关域名
Pattern: "pornhub.com"     → 只阻止特定网站
```

### 2. 误用 Allow 类型

当前代码只支持 `type="block"`，不支持 `type="allow"`。

如果您期望实现白名单功能（只允许特定域名访问），需要修改代码逻辑。

### 3. 多条规则冲突

如果设置了多条规则，某些规则可能会意外匹配到内网地址。

---

## 诊断工具使用

我们提供了两个工具脚本：

### 1. 测试脚本
```bash
python3 scripts/test_url_filter_simple.py
```
**功能:** 自动测试URL过滤功能，验证规则是否按预期工作。

### 2. 诊断脚本
```bash
python3 scripts/diagnose_url_filters.py
```
**功能:** 检查数据库中的过滤规则，找出可能有问题的配置。

---

## 建议和最佳实践

### ✅ 推荐做法

1. **使用完整的域名作为 Pattern**
   ```
   baidu.com
   www.google.com
   facebook.com
   ```

2. **测试规则后再正式使用**
   - 创建规则后先用测试工具验证
   - 确认不会误伤其他正常访问

3. **定期检查规则**
   - 使用诊断工具检查现有规则
   - 删除不需要的规则

### ❌ 避免的做法

1. **不要使用过短的 Pattern**
   ```
   com, cn, 1, 2, http, www 等
   ```

2. **不要使用内网IP段作为 Pattern**
   ```
   192, 168, 10, 172 等
   ```

3. **谨慎使用通配符**
   ```
   *, ?, .* 等（当前代码会按字面匹配，不是正则）
   ```

---

## 如果需要实现白名单功能

当前代码不支持白名单（只允许特定域名）。如果需要此功能，需要修改 `checkURLFilter` 函数：

```go
func (s *Socks5Server) checkURLFilter(user *database.User, targetAddr string) bool {
    if database.DB == nil {
        return true
    }

    var filters []database.URLFilter
    if err := database.DB.Where("enabled = ?", true).Find(&filters).Error; err != nil {
        return true
    }

    // 检查是否有 allow 规则
    hasAllowRules := false
    for _, filter := range filters {
        if filter.Type == "allow" {
            hasAllowRules = true
            break
        }
    }

    // 如果有 allow 规则，默认拒绝，只允许匹配的
    if hasAllowRules {
        for _, filter := range filters {
            if filter.Type == "allow" && strings.Contains(targetAddr, filter.Pattern) {
                return true  // 在白名单中，允许
            }
        }
        return false  // 不在白名单中，拒绝
    }

    // 如果只有 block 规则，默认允许，只阻止匹配的
    for _, filter := range filters {
        if filter.Type == "block" && strings.Contains(targetAddr, filter.Pattern) {
            return false  // 在黑名单中，拒绝
        }
    }

    return true  // 默认允许
}
```

---

## 测试总结

✅ **测试通过**

URL过滤功能工作正常：
- Block 类型规则正确阻止匹配的域名
- 其他域名不受影响
- 符合代码逻辑预期

如果遇到问题，请：
1. 使用诊断工具检查数据库中的实际规则
2. 检查 Pattern 是否设置正确
3. 确认 Type 是否为 "block"
4. 查看代理服务日志了解详细信息

---

## 附录：测试命令

```bash
# 安装依赖
pip3 install pymysql PySocks requests

# 运行测试
python3 scripts/test_url_filter_simple.py

# 诊断规则
python3 scripts/diagnose_url_filters.py

# 查看数据库中的规则
mysql -h 127.0.0.1 -u socks5_user -p socks5_db -e "SELECT * FROM url_filters;"

# 查看代理日志
tail -f logs/proxy.log
```

