---
name: openwrt-ssrplus-dns-fix
title: OpenWRT SSR Plus DNS 劫持修复
description: 修复 SSR Plus 代理服务器域名被错误解析为 127.0.0.1 导致无法访问境外网站的问题
tags: [openwrt, ssrplus, dns, proxy, v2ray, troubleshooting]
---

# OpenWRT SSR Plus DNS 劫持修复

## 问题描述

SSR Plus 代理服务器域名被错误解析为 127.0.0.1，导致透明代理无法正常工作，所有境外网站无法访问。

## 症状

- 无法访问 GitHub、Google 等境外网站
- `curl https://github.com` 报错：`SSL_ERROR_SYSCALL`
- `nslookup proxy.domain.com` 返回 `127.0.0.1`
- iptables 规则中服务器 IP 显示为 `127.0.0.1`

## 根本原因

1. SSR Plus 启动时解析代理服务器域名失败
2. 错误地将 127.0.0.1 作为服务器 IP 写入 iptables 规则
3. v2ray 尝试连接本地地址，形成循环

## 修复步骤

### 1. SSH 登录路由器

```bash
sshpass -p "password" ssh -o StrictHostKeyChecking=no root@192.168.2.1
```

### 2. 检查当前 DNS 解析

```bash
nslookup mime.bhcy.email 127.0.0.1  # 错误：返回 127.0.0.1
nslookup mime.bhcy.email 8.8.8.8    # 正确：返回真实 IP
```

### 3. 添加正确的 hosts 条目

```bash
# 获取正确 IP（从外部 DNS）
CORRECT_IP="38.76.141.130"  # 根据实际情况修改

# 添加到 hosts
echo "$CORRECT_IP mime.bhcy.email" >> /etc/hosts
echo "$CORRECT_IP hkzx.bhcy.email" >> /etc/hosts  # 如果有 CNAME
echo "$CORRECT_IP pop3.bhcy.email" >> /etc/hosts  # 如果有其他子域名
```

### 4. 修复 v2ray 监听配置（可选）

如果 v2ray 只监听 IPv6，修改 gen_config.lua：

```bash
sed -i 's/inbound = (local_port ~= "0") and {/inbound = (local_port ~= "0") and {\n\t\tlisten = "0.0.0.0",/' /usr/share/shadowsocksr/gen_config.lua
```

### 5. 重启 SSR Plus

```bash
/etc/init.d/shadowsocksr restart
```

### 6. 验证修复

```bash
# 检查 iptables 规则
iptables -t nat -L SS_SPEC_WAN_AC -n -v | grep -E "RETURN|38.76"

# 检查 DNS 解析
nslookup mime.bhcy.email 127.0.0.1

# 测试代理
curl -I http://www.google.com
curl -I https://github.com
```

## 预防措施

1. **永久修复**：在 `/etc/hosts` 中固定代理服务器 IP
2. **监控**：定期检查 iptables 规则中的服务器 IP 是否正确
3. **备用方案**：配置多个代理服务器，避免单点故障

## 快速诊断命令

```bash
# 一键诊断脚本
ssh root@192.168.2.1 "
echo '=== DNS 解析测试 ==='
nslookup mime.bhcy.email 127.0.0.1
echo ''
echo '=== iptables 规则 ==='
iptables -t nat -L SS_SPEC_WAN_AC -n -v | head -10
echo ''
echo '=== v2ray 进程 ==='
ps | grep v2ray
echo ''
echo '=== 端口监听 ==='
netstat -tlnp | grep 1234
"
```

## 相关文件

- `/etc/hosts` - 静态 DNS 解析
- `/etc/config/shadowsocksr` - SSR Plus 配置
- `/usr/share/shadowsocksr/gen_config.lua` - v2ray 配置生成脚本
- `/var/etc/ssrplus/tcp-only-ssr-retcp.json` - v2ray 运行时配置
- `/tmp/dnsmasq.d/dnsmasq-ssrplus.d/` - dnsmasq 配置目录

## 参考

- SSR Plus 透明代理原理：DNS 劫持 + iptables REDIRECT
- v2ray dokodemo-door 协议用于透明代理
- dnsmasq 将 GFWList 域名解析转发到 dns2tcp (127.0.0.1:5335)
