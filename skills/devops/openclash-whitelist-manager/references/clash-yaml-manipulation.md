# Clash YAML 配置操作参考

## 场景：将 MATCH 兜底规则从代理改为直连

### 问题定位

OpenClash 自动生成的 `Clash_*.yaml` 最后两条规则通常是：
```
- "GEOIP,CN,\U0001F9F1国内网址,no-resolve"  # 国内 IP 直连
- "MATCH,\U0001F41F境外网站"                   # 未匹配的 → 走代理 ❌
```

需要改为：
```
- "GEOIP,CN,\U0001F9F1国内网址,no-resolve"  # 不变
- "DOMAIN-SUFFIX,opencode.ai,\U0001F3AF不用代理"  # 新增：直连
- "MATCH,\U0001F3AF不用代理"                        # 改：默认直连 ✅
```

### YAML 转义序列表

| 代理组 | YAML 转义 | 十六进制 | 含义 |
|--------|-----------|---------|------|
| 🐛境外网站 | `\U0001F41F境外网站` | U+1F41F | 原兜底组（走代理） |
| 🎯不用代理 | `\U0001F3AF不用代理` | U+1F3AF | DIRECT 组 |
| 🧱国内网址 | `\U0001F9F1国内网址` | U+1F9F1 | 国内直连组 |

### sed 修改命令（在路由器上执行）

```bash
# 找到当前运行配置
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml 2>/dev/null | head -1)

# 1. 在 MATCH 前插入 DIRECT 域名规则（\U0001F3AF = 🎯 = 不用代理组）
sed -i 's/^- "MATCH,\\U0001F41F境外网站"/  - "DOMAIN-SUFFIX,opencode.ai,\\U0001F3AF不用代理"\
  - "DOMAIN-SUFFIX,token.clawadmin.org,\\U0001F3AF不用代理"\
  - "DOMAIN-SUFFIX,api.anthropic.com,\\U0001F3AF不用代理"\
  - "DOMAIN-SUFFIX,api.openai.com,\\U0001F3AF不用代理"\
  - "DOMAIN-SUFFIX,github.com,\\U0001F3AF不用代理"\
  - "MATCH,\\U0001F3AF不用代理"/' "$RUNNING"

# 2. 重载配置
kill -HUP $(pgrep -f 'clash -d') 2>/dev/null || /etc/init.d/openclash restart

# 3. 验证
tail -8 "$RUNNING"
```

### 安全重建方法（当 YAML 损坏时）

如果直接 sed 导致 Clash 配置损坏，用本机 Python 重建：

```python
# 在本地 Linux 机器上执行（路由器无 python3）
import yaml, re

# 1. 从路由器下载
# ssh root@192.168.2.1 "cat /etc/openclash/config/Clash_*.yaml" > /tmp/clash.yaml

with open('/tmp/clash.yaml', 'r') as f:
    content = f.read()

# 2. 分离 header 和 rules
parts = content.split('rules:\n', 1)
header = parts[0] + 'rules:\n'
rule_text = parts[1]

# 3. 清理和重建
rules = [l.strip() for l in rule_text.split('\n') if l.strip()]
# 移除之前的编辑残留
rules = [r for r in rules if not any(d in r for d in ['opencode.ai','token.clawadmin'])]

# 4. 找到 MATCH 行并修改
match_idx = next(i for i, r in enumerate(rules) if r.startswith('- "MATCH,'))
rules[match_idx] = '- "MATCH,\\U0001F3AF不用代理"'

# 5. 插入新规则
new_rules = [
    '- "DOMAIN-SUFFIX,opencode.ai,\\U0001F3AF不用代理"',
    '- "DOMAIN-SUFFIX,token.clawadmin.org,\\U0001F3AF不用代理"',
    '- "DOMAIN-SUFFIX,api.anthropic.com,\\U0001F3AF不用代理"',
    '- "DOMAIN-SUFFIX,api.openai.com,\\U0001F3AF不用代理"',
]
for r in reversed(new_rules):
    rules.insert(match_idx, r)

# 6. 写出
with open('/tmp/clash_fixed.yaml', 'w') as f:
    f.write(header)
    for r in rules:
        f.write(r + '\n')

# 7. 验证
yaml.safe_load(open('/tmp/clash_fixed.yaml'))  # 不抛异常 = 有效

# 8. 上传回路由器
# cat /tmp/clash_fixed.yaml | ssh root@192.168.2.1 "cat > /etc/openclash/config/Clash_1778507584.yaml"
# ssh root@192.168.2.1 "/etc/openclash/clash -t -f /etc/openclash/config/Clash_1778507584.yaml"
```

### 验证清单

```bash
# DNS 检查（仍返回 Fake-IP 是正常的，关键看流量路由）
dig +short opencode.ai            # → 198.18.x.x (Fake-IP, normal)
dig +short token.clawadmin.org    # → 198.18.x.x (Fake-IP, normal)

# 服务检查
curl -s -o /dev/null -w "HTTP %{http_code}" https://opencode.ai/zen/go/v1/chat/completions
# → 404 (expected — Clash routing correctly)

# NewAPI 模型调用检查
curl -s --max-time 30 -X POST http://localhost:3000/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":3}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'choices' in d else 'FAIL')"

# 出口 IP 检查（重启 Clash 后可能需要等待）
curl -s https://api.ipify.org
```

### 在运行配置中添加 fake-ip-filter

除了修改规则外，还可以在运行中的 Clash YAML 的 `dns:` 段添加 `fake-ip-filter`，让特定域名在 DNS 阶段就返回真实 IP：

```yaml
dns:
  enable: true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter:
  - "+.opencode.ai"
  - "+.token.clawadmin.org"
  - "+.api.anthropic.com"
  - "+.api.openai.com"
  - "+.github.com"
```

这里的 `+.domain.com` 格式是 Clash 的匹配语法，含义是「匹配 domain.com 及其所有子域名」。

**注意：添加 fake-ip-filter 后必须完整重启 OpenClash（`/etc/init.d/openclash restart`），仅 SIGHUP 不会使 DNS 返回真实 IP。**

### 验证方法

```bash
# DNS 应返回真实 IP（不再被 Fake-IP 劫持）
dig +short opencode.ai            # → 172.x.x.x （不是 198.18.x.x）

# 服务检查
curl -s -o /dev/null -w "HTTP %{http_code}" https://opencode.ai/zen/go/v1/chat/completions
# → 404 (expected — Clash routing correctly)

# NewAPI 模型调用检查
curl -s --max-time 30 -X POST http://localhost:3000/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":3}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'choices' in d else 'FAIL')"
```
# 如果用本机 Python 重建
# （完整的 Python 重建脚本见上方「安全重建方法」）

# 上传回路由器
cat /tmp/clash_fixed.yaml | ssh root@192.168.2.1 "cat > /etc/openclash/config/Clash_1778507584.yaml"

# 验证 YAML 语法
ssh root@192.168.2.1 "/etc/openclash/clash -t -f /etc/openclash/config/Clash_1778507584.yaml"

# 启动
ssh root@192.168.2.1 "uci set openclash.config.enable=1 && uci commit openclash && /etc/init.d/openclash start"
```

### 情形 3：OpenClash 完全无法生成配置

```bash
# 启动 OpenClash 日志监控
cat /tmp/openclash.log

# 如果报 Config Not Found，检查 uci 设置
uci show openclash.config.config_path
# 确保 config_path 指向存在且有效的文件

# 如果报 Unable To Parse Config File，说明 YAML 语法错误
# 用方法 2 重建或修正
```

### 已知风险

1. **sed 插入的缩进不一致问题**：路由器的 shell 环境可能与预期不同，插入的行可能有缩进错误。用 `cat` 传文件比 sed 更可靠。
2. **YAML 转义坑**：`\U0001F3AF不用代理` 中的 `\U` 在 YAML 双引号字符串中是合法转义，但 `\不` 不是。必须确保 `\U` 后面紧跟 8 位十六进制数字。
3. **OpenClash 重启可能导致配置回滚**：如果 OpenClash watchdog 检测到订阅更新，它可能覆盖修改。持久化的方法是将规则写入 `openclash_custom_rules.list`。
4. **cloudflared 需要重启**：修改 Clash 规则后，`token.clawadmin.org`（Cloudflare Tunnel）需要重启 cloudflared 才能恢复连接。