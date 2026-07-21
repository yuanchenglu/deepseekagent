---
title: Hermes Web UI 管理与故障排查
name: hermes-web-ui-admin
description: Hermes Web UI 的安全升级、认证故障排查、systemd 服务管理和常见问题快速修复流程
version: 1.0
created: 2026-05-14
---

# Hermes Web UI 管理与故障排查

## 适用场景
- Hermes Web UI 升级失败/版本回退
- 登录无反应/认证失败
- systemd 服务运行异常
- 前后端版本不一致

## 核心原则
1. **永远不要直接复制文件升级 Node.js 应用** — 含有原生模块（如 bcrypt、sqlite3）的包需要重新编译，简单复制 dist 和 node_modules 会导致运行时错误。
2. **信任 API 而非文件系统** — package.json 的版本号不代表实际运行的版本，必须通过 `/health` 端点验证。
3. **停得彻底，启得干净** — systemd 服务重启前必须 `daemon-reload` + 确认旧进程已终止。

---

## 常见操作

### 1. 快速健康检查
```bash
# 查看实际运行版本
curl -s http://localhost:8648/health | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('webui_version'), d.get('node_version'))"

# 查看进程工作目录（确认是否跑在正确目录）
readlink -f /proc/$(pgrep -f "dist/server/index.js")/cwd

# 查看端口占用
ss -tlnp | grep 8648
```

### 2. 安全升级流程
```bash
cd ~/Code/hermes-web-ui

# 停止服务
systemctl --user stop hermes-web-ui.service
pkill -9 -f "dist/server/index.js"
sleep 2

# 备份
mv dist dist-backup-$(date +%Y%m%d)
mv node_modules node_modules-backup-$(date +%Y%m%d)

# 从 npm 重新安装（推荐）
npm install -g hermes-web-ui@latest
# 或者如果需要本地开发版，执行 npm install 重新构建
npm install && npm run build  # 如果有 build 脚本

# 更新 systemd
systemctl --user daemon-reload
systemctl --user start hermes-web-ui.service

# 验证
sleep 3
curl -s http://localhost:8648/health | grep webui_version
```

### 3. 认证故障排查

v0.5.17+ 引入了用户名/密码登录，与 token 登录并存。

```bash
# 检查认证状态
curl -s http://localhost:8648/api/auth/status
# 返回: {"hasPasswordLogin":false,"username":null}

# 测试 token 登录（正确方式）
curl -s -H "Authorization: Bearer <TOKEN>" http://localhost:8648/api/hermes/sessions

# 如果返回 200 且包含 sessions，说明 token 有效
```

**前端登录逻辑：**
- 前端会检测 `window.__LOGIN_TOKEN__`
- 如果没有，用户输入 token 后前端会用 Bearer 方式调用 `/api/hermes/sessions` 验证
- 验证通过后跳转到 `/hermes/chat`

### 4. 系统服务管理

```bash
# 创建 systemd 服务
mkdir -p ~/.config/systemd/user/
cat > ~/.config/systemd/user/hermes-web-ui.service << 'EOF'
[Unit]
Description=Hermes Web UI Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/bluth/Code/hermes-web-ui
Environment="NODE_ENV=production"
Environment="PORT=8648"
Environment="AUTH_TOKEN=YOUR_TOKEN"
ExecStart=/usr/bin/node dist/server/index.js
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable hermes-web-ui.service
systemctl --user start hermes-web-ui.service
```

---

## 常见问题

| 现象 | 原因 | 解决 |
|-------|-------|-------|
| 登录无反应 | 前后端版本不匹配 | 清除浏览器缓存，确认 `/health` 返回的版本号 |
| 登录后 401 | token 不正确或认证方式已变 | 检查 `~/.hermes-web-ui/.token`，确认 AUTH_TOKEN 环境变量 |
| 服务启动后立即崩溃 | bcrypt/sqlite3 等原生模块与当前 Node 版本不兼容 | 执行 `npm rebuild` 或重新 npm install |
| systemd 显示 active 但访问不通 | 端口冲突或旧进程未终止 | `pkill -9 -f "dist/server/index.js"` 后重启 |

---

## 快速修复指南

**情况 A：升级后登录失败**
1. `curl http://localhost:8648/health` 确认版本
2. 如果版本不对，停止服务，清理旧进程，重新安装
3. 清除浏览器缓存或使用隐身模式测试

**情况 B：想直接跳过登录**
```
https://hermes-tech.skysea.uk/#/hermes/chat?token=YOUR_TOKEN
```

---

## 相关路径
- 代码目录：`~/Code/hermes-web-ui`
- 配置/数据：`~/.hermes-web-ui/`
- 日志：`~/.hermes-web-ui/logs/server.log`
- 令牌：`~/.hermes-web-ui/.token`

---

## vision_analyze 故障排查

当 `vision_analyze` 工具反复报 `Server disconnected without sending a response` 时，排查路径：

### 1. 检查辅助视觉提供商配置

`config.yaml` 中 `auxiliary.vision` 决定了 vision_analyze 的后备模型：

```yaml
auxiliary:
  vision:
    provider: google        # 必须匹配 providers 中已配置的提供商
    model: gemini-2.5-flash
    api_key: ''             # 空字符串 = 从 key_env 环境变量读取
```

**常见问题**：provider 配了但 API Key 为空（环境变量未设置）。

### 2. 环境变量覆盖

`~/.hermes/profiles/<profile>/config.yaml` 的 `auxiliary.vision` 优先级高于全局 config。检查两个位置：

```bash
# 全局
grep -A 5 "auxiliary:" ~/.hermes/config.yaml
# Profile
grep -A 5 "auxiliary:" ~/.hermes/profiles/course-designer/config.yaml
```

环境变量也可覆盖：
```bash
env | grep AUXILIARY_VISION
# AUXILIARY_VISION_PROVIDER=google
# AUXILIARY_VISION_MODEL=gemini-2.5-flash
```

### 3. 修复方案

**方案 A**：添加缺失的 API Key 到 `~/.hermes/env/api-keys.env`
```bash
echo 'GEMINI_API_KEY=your-key-here' >> ~/.hermes/env/api-keys.env
```

**方案 B**：切换到已有 Key 的提供商
```yaml
auxiliary:
  vision:
    provider: 7colorai-liantong   # 已有 COLORAI_LIANTONG_API_KEY
    model: glm-5.1                # GLM-5.1 支持视觉输入
```

### 4. 代理提供商的图片转发限制

通过第三方代理（如 opencodego）调用模型时，代理可能不支持转发图片内容。即使 `image_input_mode: auto`，图片也不会进入模型上下文。

**诊断**：如果辅助视觉配置正确但 `vision_analyze` 仍然失败，检查当前模型是否通过代理调用。代理不支持图片 = vision_analyze 无效。

**绕过**：确保辅助视觉使用直连提供商（Google/OpenAI/7colorai），而非代理。
