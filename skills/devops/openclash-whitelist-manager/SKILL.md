---
name: openclash-whitelist-manager
title: OpenClash 白名单域名管理
description: 将指定域名加入 OpenClash 的 Fake-IP 过滤器白名单，使其绕过代理、直连访问。适用于 Cloudflare Tunnel 边缘节点、微信 API、国内服务等需要固定出口 IP 的场景。
tags: [openclash, openwrt, dns, fake-ip, whitelist, proxy, bypass]
---

# OpenClash 白名单域名管理

## 触发条件

当用户有以下需求时，使用此 Skill：
- "把 xxx.com 加入 OpenClash 白名单"
- "让 xxx.com 绕过代理/直连"
- "OpenClash 不要代理 xxx.com"
- "修复 xxx 被 OpenClash 劫持的问题"
- "添加域名到 fake-filter"
- "xxx.com 返回 198.18.0.x 假 IP"
- "连接被重置 / connection reset / EOF"（AI API 间歇性失败，可能是 OpenClash 代理不稳定）
- "xxx 走代理了但它应该直连"

## 环境信息

| 项 | 值 | 说明 |
|---|---|---|
| 路由器 IP | `192.168.2.1` | OpenWrt + OpenClash |
| SSH 用户 | `root` | |
| 密码来源 | 从用户处确认 | 用户明确告知后方可使用 |
| 白名单文件 | `/etc/openclash/custom/openclash_custom_fake_filter.list` | Fake-IP 过滤器 |
| 重启命令 | `/etc/init.d/openclash restart` | |
| 验证命令 | `dig +short <domain>` | 应返回真实公网 IP |

## 操作步骤

### Step 1：获取路由器密码

如果当前会话不知道密码，询问用户：
> 需要路由器 root 密码才能操作 OpenClash 白名单，请提供。

### Step 2：标准化域名格式

将用户提供的域名转换为 Fake-IP 过滤器格式：
- 自动添加 `+.` 前缀（匹配域名及其所有子域名）
- 如果用户已提供 `*.` 或 `+.`，保持不变
- 去除 `http://`、`https://`、`www.` 等前缀

**示例转换**：
```
argotunnel.com      → +.argotunnel.com
*.weixin.qq.com     → +.weixin.qq.com
mp.weixin.qq.com    → +.mp.weixin.qq.com
https://example.com → +.example.com
```

### Step 3：SSH 登录并添加白名单

```bash
# 构建 SSH 前缀（所有命令都要加）
SSH_PREFIX="sshpass -p \"\$ROUTER_PASSWORD\" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@192.168.2.1"

# 检查是否已存在（避免重复）
\$SSH_PREFIX "grep -F '\$DOMAIN' /etc/openclash/custom/openclash_custom_fake_filter.list"

# 如果不存在，追加到文件末尾（带注释说明）
\$SSH_PREFIX "echo '' >> /etc/openclash/custom/openclash_custom_fake_filter.list && echo '# \$COMMENT' >> /etc/openclash/custom/openclash_custom_fake_filter.list && echo '\$DOMAIN' >> /etc/openclash/custom/openclash_custom_fake_filter.list"
```

### Step 4：重启 OpenClash

```bash
\$SSH_PREFIX "/etc/init.d/openclash restart"
```

等待 8-10 秒让服务完全启动。

### Step 5：验证 DNS 解析

```bash
# 在本地执行 dig，验证返回的不是 198.18.0.x
dig +short \$DOMAIN | grep -v "198.18.0"
```

如果仍有 `198.18.0.x`，说明：
1. OpenClash 未完全重启，再等待 5 秒后重试
2. 域名格式不匹配（如多级子域名 `region2.v2.argotunnel.com` 需要 `+.argotunnel.com` 而非 `*.argotunnel.com`）
3. 路由器使用了 nftables 而非 iptables，需要同时检查 nft 规则

**重要：如果本机运行了 cloudflared，必须重启 cloudflared 清除 DNS 缓存：**
```bash
# cloudflared 内部缓存了假 IP，即使 OpenClash 修复后也需要重启才能重新解析
sudo systemctl restart cloudflared-hermes
# 或：
sudo systemctl restart cloudflared
# 然后等待 5-8 秒，检查日志确认连接 IP 已变为 198.41.xxx.xxx
sudo journalctl -u cloudflared --since "5 seconds ago" --no-pager | grep "Registered tunnel"
```

**验证所有子域名（尤其是多级子域名）：**
```bash
for sub in region1.v2 region2.v2 region3.v2 api _cftunnel; do
  echo -n "${sub}.argotunnel.com: "
  dig +short ${sub}.argotunnel.com | head -1
done
# 所有返回都应是 198.41.xxx.xxx，不能有 198.18.0.x
```

## 批量添加

如果用户一次提供多个域名，一次性追加：

```bash
\$SSH_PREFIX "cat >> /etc/openclash/custom/openclash_custom_fake_filter.list << 'EOF'

# Batch add by user request
+.domain1.com
+.domain2.com
+.domain3.com
EOF"
```

## 已知的常用白名单

以下域名已被加入白名单，不要重复添加：

```
# Cloudflare Tunnel
+.argotunnel.com
+.cfargotunnel.com

# WeChat API
+.mp.weixin.qq.com
+.weixin.qq.com

# AI API 直连（不走代理，避免代理不稳定导致连接重置）
+.opencode.ai               # OpenCode Go API（NewAPI 上游）
+.token.clawadmin.org       # NewAPI 中转站自身域名
+.clawadmin.org             # clawadmin 体系
+.api.anthropic.com         # Anthropic API
+.api.openai.com            # OpenAI API
+.github.com                # 代码托管（直连避免 git push 间歇性失败）
```

## 常见问题

### Q1: 添加后 dig 仍返回 198.18.0.x
- 检查是否用了 `*.` 而非 `+.`（OpenClash 支持 `+.` 匹配多级子域名）
- 检查域名是否有额外层级（如 `region2.v2.argotunnel.com` 需要 `+.argotunnel.com`）
- 确认 OpenClash 已重启完成（`ps | grep clash` 看进程是否存在）

### Q2: 其他电脑也受影响
这是正常的——所有设备都走同一路由器 DNS，路由器修复后全部生效。

### Q3: 需要同时加 Clash 规则吗？
如果只是要让域名绕过 Fake-IP 劫持，fake-filter 就够了。
如果需要让域名走代理/直连策略，才需要加 custom_rules。

### Q4: AI API 间歇性 "connection reset by peer" / "EOF" 错误
如果 NewAPI 或其他 AI API 中转报间歇性 `upstream error: do request failed` 且底层错误是 `connection reset by peer` 或 `EOF`，原因通常是 **OpenClash 将 AI API 域名的流量路由到了代理服务器，而代理服务器不稳定**。

**诊断步骤：**
```bash
# 1. 检查是否被 Fake-IP 劫持
dig +short <domain>
# 如果返回 198.18.x.x → 被劫持

# 2. 获取真实 IP（绕过 OpenClash DNS 劫持）
curl -s "https://dns.google/resolve?name=<domain>&type=A" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('Answer',[{}])[0].get('data','no answer'))"

# 3. 验证直连是否正常
curl -s --resolve "<domain>:443:<真实IP>" -o /dev/null -w "HTTP %{http_code}, %{time_total}s" https://<domain>/

# 4. 检查出口 IP（确认是否通过代理）
curl -s https://api.ipify.org
# 如果返回的不是你家宽的公网 IP，说明所有流量都在走代理

# 5. 检查 NewAPI（或对应服务）的 Docker 日志
sudo docker logs new-api --tail 30 2>&1 | grep -i "upstream error"
```

**修复：** 将该域名加入 Fake-IP 白名单（本 Skill 的操作步骤）。

## 完整诊断流程：检查是否走了代理

当怀疑某个域名被错误地路由到代理时，按以下步骤诊断：

```bash
# 1. 检查 DNS 是否被 Fake-IP 劫持
dig +short <domain>
# 如果返回 198.18.x.x → 被 OpenClash Fake-IP 劫持

# 2. 获取真实 IP（通过 DoH 绕过本地 DNS 劫持）
curl -s "https://dns.google/resolve?name=<domain>&type=A" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('Answer',[{}])[0].get('data','no answer'))"

# 3. 检查出口 IP（确认真实在走代理）
curl -s https://api.ipify.org
# 如果返回的不是家宽公网 IP → 所有流量走代理

# 4. 检查当前 Clash MATCH 兜底规则（核心诊断）
ssh root@192.168.2.1
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml 2>/dev/null | head -1)
grep '^  - \"MATCH' "$RUNNING"
# 如果返回 MATCH,🐛境外网站 → 未匹配规则的全走代理 ❌
# 如果返回 MATCH,🎯不用代理 → 未匹配规则的全直连 ✅

# 5. 检查 OpenClash UCI 配置
grep "enable_rule_proxy\|router_self_proxy" /etc/config/openclash
```

## GFW 白名单模式（核心策略）

用户的正确策略：「只有 GFW 清单里的域名走代理，其他全部走直连」。这需要两步：

### 第一步：确保兜底 MATCH 规则为 DIRECT

OpenClash 自动生成的配置中，最后一条规则通常是 `MATCH,🐛境外网站`（未匹配的流量全走代理）。修复方法：

**方法 A：修改运行中配置（即时生效，但会被 OpenClash 重新生成时覆盖）**
```bash
ssh root@192.168.2.1
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml 2>/dev/null | head -1)

# 找到 MATCH 行
MATCH_LINE=$(grep -n 'MATCH' "$RUNNING" | tail -1 | cut -d: -f1)

# 就在 MATCH 之前插入 DIRECT 规则
sed -i "${MATCH_LINE}i\  - \"DOMAIN-SUFFIX,opencode.ai,\\U0001F3AF不用代理\"" "$RUNNING"
sed -i "${MATCH_LINE}i\  - \"DOMAIN-SUFFIX,token.clawadmin.org,\\U0001F3AF不用代理\"" "$RUNNING"
# ... 更多域名

# 把 MATCH 规则改为指向 🎯不用代理（即 DIRECT）
sed -i 's/MATCH,\\U0001F41F境外网站/MATCH,\\U0001F3AF不用代理/' "$RUNNING"

# 重载配置
kill -HUP $(pgrep -f 'clash -d') 2>/dev/null || /etc/init.d/openclash restart
```

**方法 B：通过自定义规则文件（持久化，OpenClash 重启后保留）**
编辑 `/etc/openclash/custom/openclash_custom_rules.list`：
```
rules:
DOMAIN-SUFFIX,opencode.ai,\U0001F3AF不用代理
DOMAIN-SUFFIX,token.clawadmin.org,\U0001F3AF不用代理
```
注意：自定义规则文件的格式在 OpenClash 不同版本中可能不兼容。推荐优先使用方法 A 修改运行中配置。

### 第二步：添加特定域名的直连规则

见本节下方「操作步骤」中的域名白名单添加方法。通常需要添加以下类别的域名：
- **AI API 上游**：`opencode.ai`、`api.anthropic.com`、`api.openai.com`
- **自建中转服务**：`token.clawadmin.org`、`clawadmin.org`
- **代码托管**：`github.com`

### 验证策略是否生效

```bash
# 1. 检查出口 IP 变为家宽 IP
curl -s https://api.ipify.org

# 2. 检查 MATCH 规则
ssh root@192.168.2.1
grep 'MATCH' /etc/openclash/config/Clash_*.yaml | grep -v '^#' | tail -1
# 应返回 MATCH,\U0001F3AF不用代理

# 3. 直连测试（绕过一切代理）
curl -s --resolve "opencode.ai:443:<真实IP>" -o /dev/null -w "HTTP %{http_code}" https://opencode.ai/zen/go/v1/chat/completions
```

## Clash YAML 配置操作注意事项（重要！）

### 1. YAML 转义序列

Clash 配置文件中，代理组名称使用 **YAML Unicode 转义序列** `\UXXXXXXXX`（8位十六进制），而不是实际 Emoji 字符。常见映射：

| 代理组 | YAML 转义 | 实际字符 |
|--------|-----------|---------|
| 境外网站 | `\U0001F41F境外网站` | 🐟境外网站 |
| 不用代理 | `\U0001F3AF不用代理` | 🎯不用代理 |
| 国内网址 | `\U0001F9F1国内网址` | 🧱国内网址 |
| 游戏世界 | `\U0001F3AE游戏世界` | 🎮游戏世界 |
| 国外媒体 | `\U0001F30D国外媒体` | 🌍国外媒体 |

**关键陷阱**：
- 在 YAML 双引号字符串中，`\` 是转义字符。`\不` 不是有效的 YAML 转义序列 → 解析错误
- 必须使用 `\UXXXXXXXX` 格式，不能写入实际 Emoji 字符（Clash 也能解析实际字符，但混合使用时容易出问题）
- 在 shell 的 `sed` 命令中，`\\U` 才能得到字面量 `\U`

### 2. Block Sequence 缩进一致性

在 `rules:` 段中，所有规则条目必须使用**相同的缩进层级**。混合缩进会导致 YAML 解析失败：

```yaml
# ✅ 正确：所有规则同一缩进层级
rules:
- "DOMAIN-SUFFIX,example.com,\U0001F3AF不用代理"
- "MATCH,\U0001F3AF不用代理"

# ❌ 错误：混合缩进层级
rules:
- "GEOIP,CN,国内,no-resolve"
  - "DOMAIN-SUFFIX,example.com,不用代理"  # ← 多缩进 2 格
```

### 3. 配置损坏恢复

如果直接修改运行中 Clash YAML 导致配置损坏（OpenClash 无法启动）：

```bash
# 1. 找到当前唯一的配置
ls /etc/openclash/config/Clash_*.yaml

# 2. 如果只有一个文件且已损坏，删除后重启 OpenClash 会自动生成新的
rm /etc/openclash/config/Clash_*.yaml
/etc/init.d/openclash restart

# 3. 如果 OpenClash 无法自动生成（无订阅源），需要从备份恢复
# 查看备份目录
ls /usr/share/openclash/backup/

# 4. 如果以上都不行，用 Python 在本机重建 YAML（路由器上无 python3）
ssh root@192.168.2.1 "cat /etc/openclash/config/Clash_*.yaml" > /tmp/Clash_running.yaml
# 修改后传回
cat /tmp/Clash_fixed.yaml | ssh root@192.168.2.1 "cat > /etc/openclash/config/Clash_1778507584.yaml"
# 验证
ssh root@192.168.2.1 "/etc/openclash/clash -t -f /etc/openclash/config/Clash_*.yaml"
# 重启
ssh root@192.168.2.1 "/etc/init.d/openclash restart"
```

### 4. 是否需要同时加 Fake-IP 过滤器？

| 方法 | 做什么 | 优点 | 缺点 |
|------|--------|------|------|
| **Fake-IP 白名单** | DNS 返回真实 IP，不走 Clash 管道 | 彻底绕过 Clash | OpenClash 合并机制可能失败 |
| **规则修改** | DNS 仍返回 Fake-IP，但 Clash 路由到 DIRECT | Clash 仍可控制流量 | 依赖 Clash 运行正常 |

**推荐组合**：Fake-IP 白名单 + DIRECT 规则一起加，双重保障。

## 关键陷阱

### 陷阱 1：OpenClash 可能已被禁用

修改 Clash YAML 或自定义规则文件之前，先检查 OpenClash 是否处于启用状态：

```bash
ssh root@192.168.2.1 "uci get openclash.config.enable"
# 返回 0 → OpenClash 已禁用，所有配置修改都不生效
# 返回 1 → 已启用
```

如果为 0，需要启用并启动：

```bash
ssh root@192.168.2.1 "uci set openclash.config.enable=1 && uci commit openclash && /etc/init.d/openclash start"
```

如果 OpenClash 无法启动，查日志：`cat /tmp/openclash.log`。常见原因：
- 无可用配置（Config Not Found）→ 需要上传或等待订阅更新
- YAML 语法错误（Unable To Parse Config File）→ 修正或重建

### 陷阱 2：自定义规则没生效 — 忘记开开关

自定义规则文件 `openclash_custom_rules.list` 的修改需要 `enable_custom_clash_rules=1` 才会被 OpenClash 合并：

```bash
ssh root@192.168.2.1 "uci get openclash.config.enable_custom_clash_rules"
# 返回 0 → 自定义规则被忽略
# 返回 1 → 生效中

# 如果为 0，启用：
uci set openclash.config.enable_custom_clash_rules=1
uci commit openclash
```

修改后只有 OpenClash 下次**重新生成配置**时才会合并（重启即可）。运行中的 Clash 不会自动读入。

### 陷阱 3：Fake-IP 过滤需要完整重启才能生效

添加域名到 `openclash_custom_fake_filter.list` 后，`kill -HUP`（重载）不够，必须完整重启：

```bash
ssh root@192.168.2.1 "/etc/init.d/openclash restart"
sleep 8
```

验证方式：`dig +short <domain>` 应返回真实 IP（非 198.18.x.x）。

### 陷阱 4：YAML 规则缩进必须一致

OpenClash 生成的 `Clash_*.yaml` 使用**无缩进**格式：
```yaml
rules:
- "GEOIP,CN,国内网址,no-resolve"
- "MATCH,境外网站"
```

手动插入的规则如果使用**带缩进**格式：
```yaml
  - "DOMAIN-SUFFIX,example.com,不用代理"  # ← 缩进 2 格，不同层级
```

会导致 YAML 解析失败（`expected <block end>, but found '<block sequence start>'`）。

**修复多层缩进问题**：用 Python 重建规则段，统一所有行以 `- ` 开头，不缩进。详见 `references/clash-yaml-manipulation.md` 中的「安全重建方法」。

## 完整诊断流程（从怀疑到定位）

当怀疑某个域名被错误路由时，按此流程诊断：

```bash
# 0. 检查 OpenClash 是否启用（最容易被忽略！）
ssh root@192.168.2.1 "uci get openclash.config.enable"
# 0 = 已禁用 → 先启用再排查

# 0a. 检查 enable_custom_clash_rules
ssh root@192.168.2.1 "uci get openclash.config.enable_custom_clash_rules"
# 0 = 自定义规则不生效

# 0b. 检查 enable_rule_proxy
ssh root@192.168.2.1 "uci get openclash.config.enable_rule_proxy"

# 0c. 检查实际 MATCH 兜底规则（唯一可靠的判断）
ssh root@192.168.2.1 "grep 'MATCH' /etc/openclash/config/Clash_*.yaml | tail -1"
# MATCH,\\U0001F41F境外网站 → 默认走代理 ❌
# MATCH,\\U0001F3AF不用代理 → 默认直连 ✅

# 1. 检查是否被 Fake-IP 劫持
dig +short <domain>
# 如果返回 198.18.x.x → 被劫持

# 2. 获取真实 IP（通过 DoH 绕过）
curl -s "https://dns.google/resolve?name=<domain>&type=A" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('Answer',[{}])[0].get('data','no answer'))"

# 3. 检查出口 IP（确认真实在走代理）
curl -s https://api.ipify.org
# 如果不是家宽 IP → 全流量走代理

# 4. 直连测试（不经过 Fake-IP）
curl -s --resolve "<domain>:443:<真实IP>" -o /dev/null -w "HTTP %{http_code}, %{time_total}s" https://<domain>/

# 5. 检查 NewAPI/Docker 日志中的具体错误
sudo docker logs new-api --tail 30 2>&1 | grep -i "upstream error"
```

## 快速诊断

```bash
# 检查当前 fake-filter 内容
\$SSH_PREFIX "tail -20 /etc/openclash/custom/openclash_custom_fake_filter.list"

# 检查 OpenClash 是否启用
\$SSH_PREFIX "uci get openclash.config.enable"

# 检查自定义规则是否启用
\$SSH_PREFIX "uci get openclash.config.enable_custom_clash_rules"

# 检查 OpenClash 运行状态
\$SSH_PREFIX "/etc/init.d/openclash status"

# 检查 clash 进程
\$SSH_PREFIX "ps | grep -E 'clash|mihomo' | grep -v grep"

# 检查当前 DNS 解析（路由器上执行）
\$SSH_PREFIX "nslookup \$DOMAIN 127.0.0.1"

# 检查 MATCH 兜底规则
\$SSH_PREFIX "grep 'MATCH' /etc/openclash/config/Clash_*.yaml | tail -1"

# 检查 OpenClash 后端配置
grep "enable_rule_proxy\|enable_custom_clash_rules\|enable" /etc/config/openclash | head -5
```
