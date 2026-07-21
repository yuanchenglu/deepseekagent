---
name: rustdesk-server-deploy
title: RustDesk 自建服务器部署指南
description: 通过 Docker 部署 RustDesk 自建中继服务器（hbbs + hbbr）和网页版客户端，实现低延迟、高画质的远程桌面控制。包含 Cloudflare Tunnel 集成。
tags: [rustdesk, remote-desktop, docker, self-hosted, cloudflare-tunnel]
---

# RustDesk 自建服务器部署指南

## 触发条件

当用户需要：
- "部署 RustDesk 中继服务器"
- "自建 RustDesk 服务器"
- "部署 RustDesk Web 客户端"
- "远程桌面控制自建方案"
- "取代 TeamViewer/AnyDesk 的自托管方案"

## 架构说明

RustDesk 是三端架构：

| 角色 | 组件 | 功能 | 部署位置 |
|------|------|------|---------|
| **被控端** | RustDesk 桌面端 | 被远程控制的电脑需要安装 | 每台被控电脑 |
| **控制端** | RustDesk 桌面/手机/Web 客户端 | 发起远程连接 | 控制者设备 |
| **中继服务器** | hbbs (ID) + hbbr (Relay) | 分配 ID、中转打洞失败的流量 | **一台服务器部署** |

**关键理解**：
- 中继服务器（hbbs+hbbr）只需要部署 **一次**
- 被控电脑需要安装 RustDesk 被控端
- 控制端只需客户端即可

## 部署步骤

### Step 1：部署 hbbs + hbbr（中继服务器）

```bash
# 创建目录
mkdir -p ~/rustdesk-server/data
cd ~/rustdesk-server

# hbbs - ID 注册服务器
sudo docker run --name rustdesk-hbbs \
  -p 21115:21115 -p 21116:21116 -p 21116:21116/udp \
  -p 21118:21118 \
  -v $(pwd)/data:/root \
  --restart unless-stopped \
  -d rustdesk/rustdesk-server hbbs

# hbbr - 中继传输服务器
sudo docker run --name rustdesk-hbbr \
  -p 21117:21117 \
  --restart unless-stopped \
  -d rustdesk/rustdesk-server hbbr
```

**端口说明：**
| 端口 | 协议 | 用途 |
|------|------|------|
| 21115 | TCP | hbbs ID 注册 |
| 21116 | TCP/UDP | 心跳/打洞协调 |
| 21117 | TCP | 中继传输 |
| 21118 | TCP | WebSocket (网页版用) |

### Step 2：获取公钥

```bash
# 查看 hbbs 日志获取公钥
sudo docker logs rustdesk-hbbs | grep "Public Key"

# 或直接读取文件
sudo cat ~/rustdesk-server/data/id_ed25519.pub
```

**记下这个公钥并妥善保管**。所有客户端连接时需要填写此公钥来验证服务器身份。

> ⚠️ **安全提示**：虽然这是"公钥"，但它用于客户端验证你的服务器身份。不要在任何公开可访问的网页（如配置说明页、GitHub、论坛）上展示此公钥。应通过私聊、本地文件或受控渠道分发给授权用户。建议将公钥保存到主机的安全位置：
> ```bash
> mkdir -p ~/.rustdesk
> sudo cat ~/rustdesk-server/data/id_ed25519.pub > ~/.rustdesk/id_ed25519.pub
> chmod 600 ~/.rustdesk/id_ed25519.pub
> ```

### Step 3：部署网页版客户端（可选，但功能受限）

⚠️ **重要发现**：社区版网页客户端（`pmietlicki/rustdesk-web-client`）**需要 RustDesk API 后端**（端口 21114）来处理用户登录、设备管理等。仅部署 hbbs/hbbr 中继服务器是不够的。没有 API 后端时会出现：
- 页面能加载但显示登录弹窗
- `/api/` 返回 502，客户端 JSON 解析报错
- 右上角中继服务器设置按钮无响应

**如果不需要用户系统和 Web 登录，强烈建议直接使用桌面/手机原生客户端**，功能更完整（支持文件传输、剪贴板同步等），体验更好。

**更好的替代方案：静态配置信息页**

如果你打算用一个域名（如 `rustdesk.example.com`）方便用户访问，但不想部署功能受限的 Web 客户端，可以部署一个极简的 nginx 静态页面，展示服务器地址和配置说明（但不显示公钥）：

```bash
# 创建配置信息目录
mkdir -p ~/rustdesk-info

# 创建 index.html（仅展示服务器地址和配置步骤，公钥部分写明需私下获取）
cat > ~/rustdesk-info/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>RustDesk 配置信息</title></head>
<body>
  <h1>RustDesk 自建服务器</h1>
  <p>ID 服务器: rustdesk.example.com:21116</p>
  <p>中继服务器: rustdesk.example.com:21117</p>
  <p>公钥请私下获取，或查看服务器上的 ~/.rustdesk/id_ed25519.pub</p>
</body>
</html>
EOF

# 运行 nginx 容器
sudo docker run -d --name rustdesk-info \
  -p 127.0.0.1:21129:80 \
  -v ~/rustdesk-info:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:alpine
```

然后将 `rustdesk.example.com` 指向 `http://localhost:21129`。这种方式轻量、安全、无需维护，是 Web 客户端的最佳替代。

```bash
# 拉取镜像
sudo docker pull pmietlicki/rustdesk-web-client:latest

# 运行（映射到本地 21129 端口）
# 注意：BACKEND_HOST 指向 hbbs 的 WebSocket 端口（本机 21128 映射到容器 21118）
sudo docker run -d --name rustdesk-web-client \
  -p 127.0.0.1:21129:80 \
  -e BACKEND_HOST=192.168.x.x \
  --restart unless-stopped \
  pmietlicki/rustdesk-web-client:latest
```

**hbbs 需要额外暴露 WebSocket 端口给 Web 客户端：**
```bash
# hbbs 部署时添加 21118 端口映射
sudo docker run --name rustdesk-hbbs \
  -p 21115:21115 -p 21116:21116 -p 21116:21116/udp \
  -p 21118:21118 \
  -v $(pwd)/data:/root \
  --restart unless-stopped \
  -d rustdesk/rustdesk-server hbbs
```

### Step 4：配置 Cloudflare Tunnel（可选）

如果惸需要通过域名访问网页版客户端：

```yaml
# ~/.cloudflared/config.yml 添加：
  - hostname: rustdesk.yourdomain.com
    service: http://localhost:21129
```

然后更新 Cloudflare 云端配置并重启 cloudflared。

### Step 5：客户端配置

**被控电脑：**
1. 安装 RustDesk 桌面端
2. 设置 → 网络 → ID/中继服务器
3. 填写：
   - ID 服务器: `你的服务器IP或域名:21116`
   - 中继服务器: `你的服务器IP或域名:21117`
   - Key: `从 hbbs 日志中获取的公钥`

**控制端：**
1. 安装 RustDesk 客户端（桌面/手机/Web）
2. 同样配置自建服务器地址和公钥
3. 输入被控电脚的 ID 和密码

## Cloudflare Tunnel + OpenClash 缓存中继关联问题

如果你使用 OpenClash 作为路由器代理（尤其是 Fake-IP 模式），可能遇到 Cloudflare Tunnel 持续返回 **1033 错误**。

**根本原因**：OpenClash 会劫持 `*.argotunnel.com` 域名的 DNS 解析，返回 Fake-IP 段（如 `198.18.0.x`）。导致 cloudflared 实际上连不到 Cloudflare 的编缘节点。

**解决方案**（OpenClash 路由器）：

```bash
# SSH 进入 OpenWrt 路由器
ssh root@192.168.2.1

# 编辑 fake-filter 列表（让 argotunnel 域名绕过代理）
cat >> /etc/openclash/custom/openclash_custom_fake_filter.list << 'EOF'
+.argotunnel.com
+.cfargotunnel.com
EOF

# 重启 OpenClash
/etc/init.d/openclash restart
```

**验证是否修复**：
```bash
# 正确结果应该是真实的 Cloudflare IP（如 198.41.x.x）
# 如果是 198.18.0.x，说明仍在被劫持
dig +short region1.v2.argotunnel.com
```

这也是当前说话中遇到的问题。

## 外网访问方案

RustDesk 使用原生 TCP/UDP 协议（端口 21115-21117），Cloudflare Tunnel **仅能代理 HTTP/WebSocket 流量**。

| 服务 | 能否用 CF Tunnel | 说明 |
|------|----------------|------|
| Web 客户端页面 | ✅ 可以 | HTTP 页面，可以通过 Tunnel 访问 |
| WebSocket ID 服务 | ✅ 可以 | `ws://domain:21118` 可以通过 Tunnel 代理 |
| 中继传输（TCP/UDP） | ❌ 不能 | 桌面/手机客户端直连中继服务器时不能走 Tunnel |

实际场景：
- **桌面端/手机端远程控制** → 需要中继服务器有可达的公网 IP，或使用 Tailscale 组网
- **Web 浏览器访问** → 可以用 Cloudflare Tunnel 代理页面

| 方案 | 实现难度 | 推荐度 | 说明 |
|------|---------|--------|------|
| 公网 IP + 端口映射 | 低 | ★★★★★ | 最佳，中继直连最快 |
| Tailscale | 低 | ★★★★☆ | 虚拟局域网，无需端口映射，手机/电脑都可加入 |
| frp | 中 | ★★★☆☆ | 需要一台有公网 IP 的云服务器做跳板 |
| Cloudflare Tunnel | 仅限页面 | ☆☆☆☆☆ | 只能代理 Web 客户端页面，不能代理中继传输 |

**最佳实践**：同时部署两套方案：
1. 公网 IP/Tailscale 做中继传输通道（桌面端/手机端用）
2. Cloudflare Tunnel 只用于 Web 客户端页面访问（备用选项）

> **实战经验**：对于日常远程控制，桌面端和手机原生 App 的体验远优于 Web 客户端。Web 客户端仅适合临时、轻量级的访问场景。

## 常见问题

### Q: 客户端显示 "连接中..."
- 检查 hbbs/hbbr 容器是否在运行
- 检查防火墙/路由器是否开放了 21115-21117 端口
- 确认客户端填写的服务器地址和端口正确

### Q: 连接成功但画面卡顿
- 被控端设置 → 显示 → 选择硬件编码器（NVENC/VCE/QSV）
- 调高码率到 10-20Mbps
- 关闭自适应码率

### Q: Web 版本和桌面版的区别
- Web 版功能较少（不支持文件传输、声音等）
- Web 版适合临时访问，桌面版适合常规使用
- Web 版需要浏览器支持 WebAssembly

## 参考

- RustDesk 官方: https://github.com/rustdesk/rustdesk
- RustDesk Server: https://github.com/rustdesk/rustdesk-server
- Web Client Docker: https://hub.docker.com/r/pmietlicki/rustdesk-web-client
