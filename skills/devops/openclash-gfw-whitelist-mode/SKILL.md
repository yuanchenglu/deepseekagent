---
name: openclash-gfw-whitelist-mode
description: Configure OpenClash to "GFW whitelist mode" — only GFW-listed domains go through the proxy, everything else goes DIRECT. Fixes issues where API domains (opencode.ai, token.clawadmin.org, etc.) are incorrectly routed through an unstable proxy, causing connection resets and EOF errors.
tags:
  - openclash
  - gfw
  - proxy
  - whitelist
  - openwrt
  - clash
version: 1.0.0
triggers:
  - "openclash 白名单"
  - "GFW 白名单模式"
  - "openclash 直连"
  - "代理导致 connection reset"
  - "代理导致 EOF"
  - "openclash 策略配置"
---

# OpenClash GFW 白名单模式配置

## 问题现象

OpenClash 默认的 Fake-IP + Rule 模式下，所有国际域名都被路由到代理服务器。当代理不稳定时，API 调用出现：

- `connection reset by peer`
- `EOF`
- NewAPI/上游返回 500

**根因：** 运行配置的最后一条规则是 `MATCH,🐛境外网站`，所有未匹配规则的域名都走了代理。

## 目标策略

```
只有 GFW 名单里的域名 → 走代理
其他所有域名         → 走直连
```

## 操作步骤

### 前提

- OpenWRT 路由器已安装 OpenClash
- 知道路由器 SSH 密码或 LuCI 登录密码
- 路由器 IP 默认为 `192.168.2.1`

### 风险检查（每次操作前必做）

修改 OpenClash 策略会影响路由器的流量转发。操作前确认：

1. **当前策略模式**：`uci get openclash.config.proxy_mode` — 应返回 `rule`
2. **强制代理开关**：`uci get openclash.config.enable_rule_proxy` — `0` 表示规则模式
3. **运行配置最后一条**：`tail -1 /etc/openclash/config/Clash_*.yaml` — 确认当前 MATCH 指向
4. **备份运行配置**：`cp /etc/openclash/config/Clash_*.yaml /tmp/clash_config.backup`
5. **确认 SSH 访问不中断**：OpenWRT 的 SSH 基于 br-lan，修改防火墙规则时保留一条反向 SSH 通道

### SSH 连接到路由器

#### 方式 A：直接连接（路由器 LAN 口可达）

```bash
ssh root@192.168.2.1
# 密码: 你的路由器密码
```

#### 方式 B：通过跳板机（路由器不可直达）

当路由器不在同一子网，需要通过中间主机跳转时：

```bash
# 跳板机用密钥免密，目标路由器用密码
sshpass -p '路由器的root密码' ssh -J user@jump-host root@router-ip

# 示例：通过 AIPC(100.89.88.88) 跳转到路由器(192.168.10.1)
sshpass -p 'root' ssh -J bluth@100.89.88.88 root@192.168.10.1
```

> 注意：跳板机的 SSH 需事先配好密钥免密登录（见 ssh-keygen + ssh-copy-id）。
> `ssh -J` 复用跳板机的 SSH 连接，不需要在跳板机上装任何额外软件。

### 方式一：SSH 命令行操作（推荐）

#### 1. 连接路由器

使用上方「SSH 连接到路由器」的方法登入。

#### 2. 检查当前策略

```bash
# 确认当前 proxy_mode 和 enable_rule_proxy
uci get openclash.config.proxy_mode         # 应为 'rule'
uci get openclash.config.enable_rule_proxy   # 0=不强制走规则

# 查看运行配置的最后几条规则
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)
tail -5 "$RUNNING"
```

#### 3. 添加自定义直连规则（永久生效）

```bash
cat >> /etc/openclash/custom/openclash_custom_rules.list << 'EOF'

# API直连（非GFW域名不走代理）
- DOMAIN-SUFFIX,opencode.ai,DIRECT
- DOMAIN-SUFFIX,token.clawadmin.org,DIRECT
- DOMAIN-SUFFIX,api.anthropic.com,DIRECT
- DOMAIN-SUFFIX,api.openai.com,DIRECT
- DOMAIN-SUFFIX,github.com,DIRECT
EOF

# 启用自定义规则
uci set openclash.config.enable_custom_clash_rules=1
uci commit openclash
```

#### 4. 添加 Fake-IP 过滤白名单（DNS 返回真实 IP）

```bash
cat >> /etc/openclash/custom/openclash_custom_fake_filter.list << 'EOF'

# API 直连域名（不走 Fake-IP）
+.opencode.ai
+.token.clawadmin.org
+.api.anthropic.com
+.api.openai.com
+.github.com
EOF
```

#### 5. 修改 MATCH 兜底规则（核心步骤）

##### 5a. 即时生效：修改运行配置

```bash
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)

# 用 sed 直接把 MATCH 从 🐟境外网站 改为 🎯不用代理
sed -i 's/MATCH,🐟境外网站/MATCH,🎯不用代理/' "$RUNNING"

# 验证
tail -3 "$RUNNING"
# 应显示: - MATCH,🎯不用代理
```

##### 5b. 永久生效：通过 Overwrite 脚本（推荐）

OpenClash 每次重启后会重新生成运行配置，覆盖上述修改。要持久化，利用 `/etc/openclash/custom/openclash_custom_overwrite.sh`：

```bash
# 在 exit 0 前插入 sed 替换
sed -i '/^exit 0/i\
# GFW Whitelist Mode: unmatched traffic goes DIRECT instead of Proxy\
sed -i "s/- MATCH,🐟境外网站/- MATCH,🎯不用代理/" "$CONFIG_FILE"' \
  /etc/openclash/custom/openclash_custom_overwrite.sh

cat /etc/openclash/custom/openclash_custom_overwrite.sh
# 确认 exit 0 前有 sed 行
```

原理：Overwrite 脚本在 `openclash` 每次生成运行配置后自动执行，`$CONFIG_FILE` 是 OpenClash 传入的参数（即当前运行配置路径）。

> 注：如果 overwrite 脚本已包含其他逻辑（如插入 LinkedIn 规则），`sed -i` 会在 `exit 0` 前追加，不影响已有内容。

#### 6. 重启 OpenClash

```bash
/etc/init.d/openclash restart
sleep 5
ps | grep clash | grep -v grep
cat /tmp/openclash.log | tail -5
# 应该看到: OpenClash Start Successful!
```

### 方式二：LuCI Web 页面操作

1. 浏览器打开 `http://192.168.2.1/cgi-bin/luci/`
2. 登录（用户名 `root`，密码你的路由器密码）
3. 进入 **服务 → OpenClash → 规则管理 → 自定义规则**
4. 添加以下规则：

```
DOMAIN-SUFFIX,opencode.ai,DIRECT
DOMAIN-SUFFIX,token.clawadmin.org,DIRECT
DOMAIN-SUFFIX,api.anthropic.com,DIRECT
DOMAIN-SUFFIX,api.openai.com,DIRECT
DOMAIN-SUFFIX,github.com,DIRECT
```

5. 进入 **服务 → OpenClash → 全局设置 → 策略设置**
6. 将 "默认策略" 从 "🐛境外网站" 改为 "🎯不用代理"
7. 点击保存并应用

### 验证

```bash
# 检查 DNS 是否返回真实 IP
dig +short opencode.ai          # 应返回 172.65.90.x
dig +short token.clawadmin.org  # 应返回 172.67.221.x

# 检查运行配置的最后一条规则
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)
tail -1 "$RUNNING"
# 应显示 MATCH → 不用代理组

# 检查实时日志，确认流量路由决策
tail -10 /tmp/openclash.log
# 应能看到类似:
#   match Match using 🎯不用代理[DIRECT]   ← 未匹配域名直连 ✅
#   match GeoSite(category-*) using 谷歌-AI  ← GFW名单走代理 ✅

# 测试多种域名，确认策略正确
nslookup google.com              # 走代理 → 返回真实境外IP
nslookup github.com              # 直连 → 返回真实IP
nslookup baidu.com               # 国内 → 走DIRECT

# 测试 API 调用
curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://token.clawadmin.org/
# 应返回 200
```

## 原理说明

OpenClash 的规则处理顺序（从上到下）：

```
自定义规则       ← 步骤3添加的DOMAIN-SUFFIX,DIRECT
↓
GEOSITE 规则     ← 自动生成（GFW 名单走代理）
↓
GEOIP 规则       ← CN IP 直连
↓
MATCH 兜底规则   ← 默认 🐛境外网站（代理），改为 🎯不用代理（直连）
```

修改前：
- `opencode.ai` → 无匹配规则 → MATCH → 🐛境外网站 → **走代理** → 代理不稳定 → TCP Reset

修改后：
- `opencode.ai` → 匹配 DOMAIN-SUFFIX → **DIRECT（直连）** → 稳定

## 注意事项

1. **运行时配置 vs 自定义规则**：运行时配置 (`Clash_*.yaml`) 会在 OpenClash 重启时被覆盖。自定义规则文件 (`openclash_custom_rules.list`) 通过 `enable_custom_clash_rules=1` 持久生效。

2. **Fake-IP 过滤白名单**：加入白名单的域名 DNS 返回真实 IP，完全绕过 Clash 的 Fake-IP 劫持。不加不影响功能，但 DNS 会返回 198.18.x.x 虚拟 IP。

3. **MATCH 兜底规则**：通过 Overwrite 脚本（步骤 5b）可永久修改 MATCH 指向，重启不丢。LuCI 页面（步骤 6）也是同样的效果，选其一即可。

4. **MATCH 策略组名称确认**：运行配置中的策略组名可能因 OpenClash 主题语言不同而异（中文/Emoji）。先运行 `grep -E 'name:.*不用|name:.*DIRECT|name:.*Proxy' /etc/openclash/config/Clash_*.yaml` 确认实际名称，再用该名称作为 sed 目标。常见名称：`🎯不用代理`、`DIRECT`、`♻️ 自动直连`。

5. **重启检查**：修改 overwrite 脚本后务必重启验证：`/etc/init.d/openclash restart && sleep 8 && tail -3 /etc/openclash/config/Clash_*.yaml`。

6. **OpenClash 版本**：基于 OpenClash 0.45.51-beta / Clash Meta 验证。不同版本的操作路径可能有差异。

7. **`PROXY` 关键字在自定义规则中的使用**：自定义规则可以使用 Clash 内置关键字 `PROXY`（默认代理组）和 `DIRECT`（直连）。OpenClash 在合并自定义规则到运行配置时保留这些关键字。例如：
   ```yaml
   - DOMAIN-SUFFIX,github.com,PROXY      # 走默认代理
   - DOMAIN-SUFFIX,baidu.com,DIRECT       # 直连
   ```
   与使用实际策略组名称（如 `🌍国外媒体`）效果相同，但 `PROXY` 更通用，跨路由器迁移时无需调整。

## 平台特性：ImmortalWrt

本 Skill 的操作步骤在标准 OpenWrt 上验证通过。以下补充 ImmortalWrt 上的差异和应对。

### 包管理器

ImmortalWrt 使用 `apk` 而非 `opkg`：

```bash
# 安装 WireGuard 等包时：
apk add wireguard-tools
```

### 配置生成机制（关键差异）

ImmortalWrt 的 OpenClash 在重启时 **不会重新生成** `Clash_*.yaml`，而是复用已有的运行配置。这意味着：
- 修改 `openclash_custom_rules.list` 后，仅重启 **不会生效**
- 必须触发配置重生成才会合并新的自定义规则

**触发配置重生成的方法：**

```bash
# 方法 A：通过 init.d 脚本（会触发完整重生成）
/etc/init.d/openclash restart

# 方法 B：手动运行 yml_rules_change.sh（不重启 Clash 时用）
CONFIG=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)
/bin/sh /usr/share/openclash/yml_rules_change.sh "$CONFIG"

# 方法 C：直接用 Ruby 修改运行配置（最可靠）
ruby -ryaml -e '
  config = YAML.load_file(ARGV[0])
  # 移除旧规则
  config["rules"].reject! { |r| r.include?("github.com") }
  # 插入新规则（在 MATCH 前）
  match_idx = config["rules"].rindex { |r| r.include?("MATCH") }
  config["rules"].insert(match_idx, "DOMAIN-SUFFIX,github.com,PROXY")
  File.open(ARGV[0], "w") { |f| YAML.dump(config, f) }
  puts "OK"
' "$CONFIG"

# 修改后用 kill -HUP 重载 Clash
kill -HUP $(pgrep -f '/etc/openclash/clash') 2>/dev/null
```

> **Ruby 是推荐的修改运行配置方式**：OpenClash 自带 Ruby（依赖），且 YAML 解析比 sed/awk 可靠，不会受 Unicode 转义序列影响。

### Watchdog 禁用问题

ImmortalWrt 上的 OpenClash watchdog 会在检测到服务未注册 ubus 时，自动将 `enable` 设为 0 并停止 Clash：

```bash
# /usr/share/openclash/openclash_watchdog.sh（约 184 行附近）
if ! ubus call service list '{"name":"openclash"}' 2>/dev/null | \
   jsonfilter -e '@.openclash.instances.*.running' | grep -q 'true'; then
   uci -q set openclash.config.enable=0   # ← 禁用
   uci -q commit openclash
   /etc/init.d/openclash stop >/dev/null 2>&1
   exit 0
fi
```

Watchdog 被 procd 以 `openclash-watchdog` 实例管理，随 init.d 启动而启动。以下场景会触发 watchdog 禁用：

| 场景 | 原因 |
|------|------|
| 手动 `killall clash` | init.d 停止后 watchdog 发现服务消失 |
| 手动删除 `Clash_*.yaml` | Clash 启动失败 → ubus 无记录 |
| 从 CLI 直接运行 clash 二进制 | 绕过 init.d，procd 不认 |
| 多次 CLI restart 失败 | watchdog 循环触发 |

**解决方法**：

```bash
# 彻底停止所有进程
killall -9 clash 2>/dev/null
killall -9 openclash_watchdog.sh 2>/dev/null
sleep 2

# 确保启用
uci set openclash.config.enable=1
uci commit openclash

# 通过 init.d 正常启动
/etc/init.d/openclash start

# 等待 10-12 秒让 watchdog 完成检查
sleep 12

# 验证
ps | grep '[c]lash' | head -3
uci get openclash.config.enable   # 应为 1
```

如果 watchdog 持续禁用，说明 Clash 核心无法正常启动。检查日志：
```bash
cat /tmp/openclash.log | grep -i error
# 常见原因：配置损坏、核心二进制不匹配、磁盘空间不足
```

### 临时绕过（调试用）

```bash
# 注释掉 watchdog 中的禁用逻辑（调试完成后恢复）
cp /usr/share/openclash/openclash_watchdog.sh /tmp/watchdog.bak
sed -i 's/uci -q set openclash.config.enable=0/# uci -q set openclash.config.enable=0/' \
  /usr/share/openclash/openclash_watchdog.sh

# 完成后恢复
cp /tmp/watchdog.bak /usr/share/openclash/openclash_watchdog.sh
```

## 相关文件

| 文件 | 用途 | 持久性 |
|------|------|--------|
| `/etc/openclash/config/Clash_*.yaml` | 运行配置 | ❌ 重启覆盖 |
| `/etc/openclash/custom/openclash_custom_rules.list` | 自定义规则 | ✅ 永久 |
| `/etc/openclash/custom/openclash_custom_fake_filter.list` | Fake-IP 白名单 | ✅ 永久 |
| `/etc/openclash/custom/openclash_custom_rules_2.list` | 自定义规则2（可选） | ✅ 永久 |
| `/etc/openclash/custom/openclash_custom_overwrite.sh` | 启动后处理脚本 | ✅ 永久（每次重启执行） |

## 相关参考

| 文件 | 用途 |
|------|------|
| `references/overwrite-script-match-modification.md` | Overwrite 脚本完整示例与注入方法 |
| `references/remote-router-via-ssh-jump.md` | 通过 SSH 跳板机连接不可直达的路由器 |
| `references/ruby-yaml-config-editing.md` | Ruby YAML 操作模式：插入/替换/删除规则 |
