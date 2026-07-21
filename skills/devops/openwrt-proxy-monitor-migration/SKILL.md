---
name: openwrt-proxy-monitor-migration
title: OpenWrt 代理监控迁移指南
description: 将家庭服务器监控面板的路由器代理检测从一种代理软件（如 SSR Plus）迁移到另一种（如 OpenClash、PassWall等）。包含进程检测、防火墙规则检测、自动修复逻辑的完整迁移流程。
tags: [openwrt, proxy, monitor, openclash, ssrplus, passwall, nftables, iptables, migration]
triggers:
  - "路由器代理检测迁移"
  - "从 SSR Plus 改到 OpenClash"
  - "代理监控不工作了"
  - "修改监控代理检测逻辑"
  - "nftables iptables 检测"
  - "openclash 监控"
---

# OpenWrt 代理监控迁移指南

将家庭服务器/监控面板的路由器代理检测从一种代理软件迁移到另一种。适用场景包括：
- SSR Plus → OpenClash
- SSR Plus → PassWall
- OpenClash → PassWall 2
- 任何旧代理 → 新代理

## 迁移前确认信息

在开始迁移前，必须确认以下信息：

| 项 | 说明 |
|---|---|
| 新代理进程名 | OpenClash 通常是 `clash`、`clash_meta`、`mihomo` |
| 新服务名 | OpenClash: `/etc/init.d/openclash` |
| 防火墙系统 | 旧 OpenWrt 用 iptables，新 OpenWrt （22.03+）用 nftables |
| iptables/nft 链名 | OpenClash: `openclash`、`openclash_mangle` 等 |
| 路由器 SSH 凭据 | 需要 root 密码 |

## 确认新代理的具体信息

SSH 登录路由器，逐一检查：

```bash
# 1. 检查进程名
ps | grep -E 'clash|mihomo|v2ray|xray' | grep -v grep
# OpenClash 常见输出：clash、clash_meta、mihomo
# SSR Plus 常见输出：v2ray、xray

# 2. 检查服务名
ls /etc/init.d/ | grep -E 'openclash|shadowsocksr|passwall'

# 3. 检查防火墙系统
which iptables || echo "无 iptables"
which nft || echo "无 nft"
# 如果 nft 存在而 iptables 不存在，说明是 nftables 系统

# 4. 检查实际防火墙规则
# 旧系统（iptables）：
iptables -t nat -L -n | grep -i clash | head -5
# 新系统（nftables）：
nft list chains | grep -i clash | head -5
```

## 代码迁移步骤

### Step 1: 修改进程检测

**旧代码（SSR Plus 例子）：**
```python
process_output = run_ssh_command(ROUTER_IP, "ps | grep -E 'xray|v2ray' | grep -v grep")
result["v2ray_running"] = process_output is not None and len(process_output.strip()) > 0
```

**新代码（OpenClash）：**
```python
process_output = run_ssh_command(ROUTER_IP, "ps | grep -E 'clash|mihomo' | grep -v grep")
result["clash_running"] = process_output is not None and len(process_output.strip()) > 0
```

### Step 2: 修改防火墙规则检测

**旧代码（仅支持 iptables）：**
```python
iptables_output = run_ssh_command(ROUTER_IP, "iptables -t nat -L SS_SPEC_WAN_FW -n | grep REDIRECT")
result["iptables_ok"] = iptables_output is not None and "REDIRECT" in iptables_output
```

**新代码（兼容 iptables 和 nftables）：**
```python
iptables_output = run_ssh_command(
    ROUTER_IP,
    "iptables -t nat -L clash -n 2>/dev/null | grep REDIRECT || "
    "iptables -t nat -L openclash -n 2>/dev/null | grep REDIRECT || "
    "nft list chain inet fw4 openclash 2>/dev/null | grep redirect"
)
result["iptables_ok"] = iptables_output is not None and (
    "REDIRECT" in iptables_output or "redirect" in iptables_output
)
```

**关键差异：**
| 系统 | 命令 | 匹配关键词 |
|---|---|---|
| iptables | `iptables -t nat -L <chain> -n \| grep REDIRECT` | `REDIRECT` |
| nftables | `nft list chain inet fw4 <chain> \| grep redirect` | `redirect` （小写） |

### Step 3: 修改自动修复逻辑

**旧代码：**
```python
if issue == "v2ray进程未运行":
    run_ssh_command(ROUTER_IP, "/etc/init.d/shadowsocksr restart", timeout=30)
    import time  # ❌ 错误做法！
    time.sleep(10)
    process_output = run_ssh_command(ROUTER_IP, "ps | grep -E 'xray|v2ray' | grep -v grep")
```

**新代码：**
```python
# 必须在函数顶部导入 time，否则在 elif 分支会报 UnboundLocalError
def auto_fix_router_issues(issues: list) -> Dict[str, bool]:
    import time  # ✅ 正确做法：放在函数开头
    fix_results = {}
    
    for issue in issues:
        if issue == "clash进程未运行":
            run_ssh_command(ROUTER_IP, "/etc/init.d/openclash restart", timeout=30)
            time.sleep(10)
            process_output = run_ssh_command(ROUTER_IP, "ps | grep -E 'clash|mihomo' | grep -v grep")
            fix_results["restart_openclash"] = process_output is not None and len(process_output.strip()) > 0
        
        elif issue == "iptables规则缺失":
            run_ssh_command(ROUTER_IP, "/etc/init.d/openclash restart", timeout=30)
            time.sleep(5)
            # 同样兼容 nftables
            iptables_output = run_ssh_command(
                ROUTER_IP,
                "iptables -t nat -L clash -n 2>/dev/null | grep REDIRECT || "
                "iptables -t nat -L openclash -n 2>/dev/null | grep REDIRECT || "
                "nft list chain inet fw4 openclash 2>/dev/null | grep redirect"
            )
            fix_results["restart_openclash_iptables"] = iptables_output is not None and (
                "REDIRECT" in iptables_output or "redirect" in iptables_output
            )
    
    return fix_results
```

### Step 4: 修改服务重启命令

```python
# 旧
"/etc/init.d/shadowsocksr restart"
"/etc/init.d/firewall restart"

# 新
"/etc/init.d/openclash restart"
"/etc/init.d/firewall restart"  # 保留，因为 OpenClash 也会修改防火墙规则
```

### Step 5: 更新返回字段名

确保 API 响应和前端 UI 使用一致的字段名：
```python
# 旧
result = {
    "v2ray_running": False,
    ...
}
result["proxy_ok"] = result["v2ray_running"] and result["iptables_ok"] ...

# 新
result = {
    "clash_running": False,  # 或 "proxy_running"
    ...
}
result["proxy_ok"] = result["clash_running"] and result["iptables_ok"] ...
```

## 常见 Python 异常修复

### UnboundLocalError: cannot access local variable 'time'

**问题原因：**
在 for 循环的某个 `if` 分支里写了 `import time`，但后面的 `elif` 分支也使用了 `time.sleep()`。Python 在函数级别将 `time` 视为本地变量，但只在某些分支里被赋值。

**修复：**把 `import time` 移到函数开头，或使用 `import time; time.sleep()` 的完整引用方式。

### f-string 嵌套引号

**问题原因：**
```python
# ❌ 错误
f"sshpass -p \'{info["password"]}\' ssh ..."
# 在 f-string 中使用双引号包含字典键，会导致语法错误
```

**修复：**
```python
# ✅ 正确
f"sshpass -p '{info['password']}' ssh ..."
# 在 f-string 内部使用单引号
```

## 更新前端显示文本

如果前端显示了具体的错误提示（如 "v2ray进程未运行"），需要同步更新：

```javascript
// 前端显示的提示文本
const errorMessages = {
    "clash进程未运行": "Clash 进程未运行",
    "iptables规则缺失": "网络转发规则缺失"
};
```

## 验证流程

1. 重启 homeserver 服务
2. 访问 `/api/router/lifeline` 或 `/api/status`
3. 确认新字段名在响应中正确显示
4. 确认 `proxy_ok: true` 时路由器状态正常
5. 确认路由器实际上网正常（访问 Google 、百度）

## 参考配置映射

| 代理软件 | 进程名 | 服务路径 | iptables/nft 链名 | 备注 |
|---|---|---|---|---|
| SSR Plus | `xray`, `v2ray` | `/etc/init.d/shadowsocksr` | `SS_SPEC_WAN_FW` | 旧版本，iptables |
| OpenClash | `clash`, `clash_meta`, `mihomo` | `/etc/init.d/openclash` | `openclash`, `openclash_mangle` | 支持 nftables |
| PassWall | `xray`, `v2ray`, `trojan` | `/etc/init.d/passwall` | `PSW` 相关 | 变化较大 |
| PassWall 2 | `xray`, `sing-box` | `/etc/init.d/passwall2` | `PSW2` 相关 | 较新版本 |

## 快速诊断脚本

```bash
#!/bin/sh
# 在路由器上执行，确认代理软件信息

echo "=== 进程 ==="
ps | grep -E 'clash|mihomo|v2ray|xray|trojan|sing-box' | grep -v grep

echo ""
echo "=== 服务 ==="
ls /etc/init.d/ | grep -E 'openclash|shadowsocksr|passwall'

echo ""
echo "=== 防火墙系统 ==="
which iptables 2>/dev/null && echo "iptables: $(iptables --version 2>/dev/null)" || echo "无 iptables"
which nft 2>/dev/null && echo "nft: $(nft --version 2>/dev/null)" || echo "无 nft"

echo ""
echo "=== iptables 规则 ==="
iptables -t nat -L -n 2>/dev/null | grep -E 'REDIRECT|clash|openclash|SS_SPEC' | head -5 || echo "iptables 无结果"

echo ""
echo "=== nftables 规则 ==="
nft list chains 2>/dev/null | grep -i 'clash\|openclash' | head -5 || echo "nft 无结果"

echo ""
echo "=== DNS 解析测试 ==="
nslookup www.google.com 127.0.0.1 2>/dev/null | tail -2
```
