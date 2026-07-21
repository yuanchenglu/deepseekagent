---
name: wecom-ai-customer-service
description: Deploy AI customer service bot for WeCom (Enterprise WeChat) groups, supporting both internal groups (Webhook) and external groups (wechaty). Includes persona design, Cloudflare Tunnel setup, and Windows deployment.
category: social-media
tags: ["wecom", "enterprise-wechat", "ai-bot", "customer-service", "wechaty", "webhook", "cloudflare-tunnel"]
---

# 企业微信AI客服部署指南

## 概述

为企业微信群部署AI客服机器人，支持：
- 内部群：官方Webhook机器人
- 外部群：wechaty-puppet-xp + Win10傀儡方案
- AI人设：CEO/董事长数字分身，非客服腔

## 前置要求

- 企业微信管理员权限
- 企业ID、AgentId、Secret
- 内部群Webhook Key
- Win10电脑（外部群需要24小时在线）
- Cloudflare账号（可选，用于公网访问）

## 架构

```
内部群: Webhook → 官方API → 群消息
外部群: Win10 + wechaty → Cloudflare Tunnel → Hermes API → AI回复
```

## 配置步骤

### 1. 内部群Webhook配置

```python
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"

import requests

def send_message(content):
    requests.post(WEBHOOK_URL, json={
        "msgtype": "markdown",
        "markdown": {"content": content}
    })
```

### 2. Cloudflare Tunnel配置

```bash
# 安装 cloudflared
curl -L --output /tmp/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64

# 创建隧道
cloudflared tunnel create hermes-tech

# 配置 config.yml
tunnel: YOUR_TUNNEL_ID
ingress:
  - hostname: hermes-tech.yourdomain.com
    service: http://localhost:8766
```

### 3. Hermes API服务

```python
from flask import Flask, request
app = Flask(__name__)

@app.route('/wecom-webhook', methods=['POST'])
def webhook():
    data = request.json
    # AI处理逻辑
    return {"should_reply": True, "reply": "..."}
```

### 4. Win10 wechaty部署

```javascript
const { WechatyBuilder } = require('wechaty')
const { PuppetXp } = require('wechaty-puppet-xp')

const bot = WechatyBuilder.build({
  puppet: new PuppetXp()
})

bot.on('message', async (msg) => {
  // 转发到Hermes API
  const response = await axios.post(API_URL, {
    content: msg.text(),
    user: msg.talker().name()
  })
  
  if (response.data.should_reply) {
    await msg.room().say(response.data.reply)
  }
})
```

## AI人设设计原则

- **身份**：CEO/董事长，非客服
- **语气**：平等对话，无敬语
- **风格**：专业、简洁、偶尔幽默
- **回复延迟**：3-11秒随机，模拟真人打字
- **可拒绝**："这问题没意思"、"我刚在忙"

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| Webhook 400 | Key错误 | 检查Webhook URL |
| Tunnel 502 | 本地服务未启动 | 检查端口监听 |
| wechaty登录失败 | 企业微信版本 | 更新到4.1.x+ |
| 消息不回复 | 群名不匹配 | 检查TARGET_GROUP配置 |

## 参考

- wechaty: https://wechaty.js.org/
- puppet-xp: https://github.com/wechaty/puppet-xp
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
