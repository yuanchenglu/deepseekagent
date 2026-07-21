---
name: cc-connect
description: Install and configure CC-Connect to bridge Claude Code (and other AI agents) to messaging platforms like Feishu/Lark, Telegram, Discord, Slack, etc. Supports custom API providers like Alibaba Cloud DashScope (BaiLian).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [CC-Connect, Claude-Code, Feishu, Lark, Messaging-Bridge, AI-Agent-Integration, DashScope, BaiLian]
    related_skills: [claude-code, lark-cli-setup]
---

# CC-Connect Setup Guide

Complete guide for installing and configuring CC-Connect to bridge Claude Code (and other AI coding agents) to messaging platforms like Feishu/Lark, Telegram, Discord, Slack, etc.

## Overview

CC-Connect creates a bridge between local AI coding agents (Claude Code, Codex, Gemini CLI, etc.) and messaging platforms, allowing you to interact with your AI agent through chat apps.

**Key Features:**
- Multi-platform support (Feishu/Lark, Telegram, Discord, Slack, DingTalk, etc.)
- Multi-agent support (Claude Code, Codex, Gemini CLI, OpenCode, etc.)
- Custom API provider support (Alibaba Cloud DashScope/BaiLian, etc.)
- WebSocket long-connection (no public IP needed for most platforms)

## Prerequisites

- Linux/macOS system
- Claude Code installed and configured (or other supported agent)
- Messaging platform account (Feishu/Lark, Telegram, etc.)

## Installation Steps

### Step 1: Download CC-Connect Binary

Since CC-Connect is written in Go and requires compilation, download the pre-built binary:

```bash
# Get latest release URL from GitHub
curl -L -o /tmp/cc-connect.tar.gz \
  "https://github.com/chenhg5/cc-connect/releases/latest/download/cc-connect-linux-amd64.tar.gz"

# Extract
tar -xzf /tmp/cc-connect.tar.gz -C /tmp

# Move to PATH
sudo mv /tmp/cc-connect-*-linux-amd64 /usr/local/bin/cc-connect
sudo chmod +x /usr/local/bin/cc-connect

# Verify
cc-connect --version
```

**Alternative: Download specific version**
```bash
# List available versions at https://github.com/chenhg5/cc-connect/releases
curl -L -o /tmp/cc-connect.tar.gz \
  "https://github.com/chenhg5/cc-connect/releases/download/v1.3.3-beta.1/cc-connect-v1.3.3-beta.1-linux-amd64.tar.gz"
```

### Step 2: Configure Claude Code for Custom Provider (Optional)

If using a custom API provider like Alibaba Cloud DashScope (BaiLian):

```bash
# Edit Claude Code settings
cat > ~/.claude/settings.json << 'EOF'
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-dashscope-api-key",
    "ANTHROPIC_BASE_URL": "https://coding.dashscope.aliyuncs.com/apps/anthropic",
    "ANTHROPIC_MODEL": "kimi-k2.5",
    "ANTHROPIC_SMALL_FAST_MODEL": "kimi-k2.5",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "API_TIMEOUT_MS": "600000"
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
EOF
```

**Verify Claude Code works:**
```bash
claude auth status --text
```

### Step 3: Create CC-Connect Configuration

```bash
# Create config directory
mkdir -p ~/.cc-connect

# Create configuration file
cat > ~/.cc-connect/config.toml << 'EOF'
# CC-Connect Configuration
# Bridges Claude Code to messaging platforms

# =============================================================================
# Global Settings
# =============================================================================

language = "zh"  # Interface language: en, zh, zh-TW, ja, es
data_dir = "~/.cc-connect"

[log]
level = "info"  # debug, info, warn, error

# =============================================================================
# Global Providers (Optional)
# =============================================================================
# Define API providers once, reference in projects

[[providers]]
name = "dashscope-kimi"
api_key = "${ANTHROPIC_AUTH_TOKEN}"  # Uses env var
base_url = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
model = "kimi-k2.5"
agent_types = ["claudecode"]

# =============================================================================
# Projects
# =============================================================================

[[projects]]
name = "my-project"

# Admin users who can run privileged commands
# admin_from = ["user_id_1", "user_id_2"]

[projects.agent]
type = "claudecode"  # claudecode, codex, gemini, opencode, etc.

[projects.agent.options]
work_dir = "~/projects/my-project"  # Default working directory
mode = "default"  # default, auto, plan, bypassPermissions

# Reference global provider (optional)
provider_refs = ["dashscope-kimi"]

[[projects.platforms]]
type = "feishu"  # feishu, telegram, discord, slack, etc.

[projects.platforms.options]
# Feishu app credentials (get from https://open.feishu.cn/)
app_id = "cli_xxxxxxxxxxxx"
app_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Optional settings
# domain = "https://open.feishu.cn"
# enable_feishu_card = true
# thread_isolation = true
# progress_style = "card"  # legacy, compact, card
# done_emoji = "Done"
# resolve_mentions = true
EOF
```

### Step 4: Create Startup Script

Create a script to automatically set environment variables:

```bash
cat > ~/start-cc-connect.sh << 'EOF'
#!/bin/bash
# CC-Connect startup script

# Read API key from Claude Code settings
ANTHROPIC_AUTH_TOKEN=$(cat ~/.claude/settings.json 2>/dev/null | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('env',{}).get('ANTHROPIC_AUTH_TOKEN',''))" 2>/dev/null)

if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "Error: Could not read ANTHROPIC_AUTH_TOKEN from ~/.claude/settings.json"
    exit 1
fi

export ANTHROPIC_AUTH_TOKEN

echo "Starting CC-Connect..."
cc-connect "$@"
EOF

chmod +x ~/start-cc-connect.sh
```

### Step 5: Configure Messaging Platform (Feishu Example)

#### Option A: Using CC-Connect Setup Command (Recommended)

```bash
# Interactive setup with QR code
cc-connect feishu setup --project my-project
```

This will:
1. Generate a QR code for Feishu app authorization
2. Create/bind the Feishu application
3. Automatically write credentials to config.toml

**Important:** The setup command times out after ~60 seconds. If you need to generate a new QR code:

```bash
# Kill any running cc-connect processes first
pkill -f "cc-connect feishu"

# Re-run setup to get a new QR code
cc-connect feishu setup --project my-project
```

**Generating QR Code Image (for sharing):**

If you need to convert the terminal QR code to an image:

```bash
# Install qrcode library
sudo apt-get install -y python3-qrcode  # Debian/Ubuntu

# Generate QR code image
/usr/bin/python3 << 'PYEOF'
import qrcode

# Replace with your actual URL from cc-connect output
url = "https://open.feishu.cn/page/launcher?user_code=XXXX-XXXX"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save('/tmp/feishu_qrcode.png')
print(f"QR Code saved to: /tmp/feishu_qrcode.png")
PYEOF
```

#### Option B: Manual Configuration

1. **Create Feishu App:**
   - Visit https://open.feishu.cn/
   - Click "创建企业自建应用"
   - Fill in app name and description

2. **Get Credentials:**
   - Go to "凭据与基础信息"
   - Copy `App ID` and `App Secret`

3. **Configure Permissions:**
   - Go to "权限管理"
   - Add these permissions:
     - `contact:user.base:readonly`
     - `im:message.group_at_msg:readonly`
     - `im:message.p2p_msg:readonly`
     - `im:message.group_msg`
     - `im:message:send_as_bot`

4. **Configure Event Subscription:**
   - Go to "事件与回调"
   - Select "使用长连接接收事件"
   - Add event: `im.message.receive_v1`
   - Add callback: `card.action.trigger`

5. **Publish App:**
   - Go to "版本管理与发布"
   - Create and publish a version

6. **Update Config:**
   ```bash
   vim ~/.cc-connect/config.toml
   # Fill in app_id and app_secret
   ```

### Step 6: Start CC-Connect

```bash
# Using startup script
~/start-cc-connect.sh

# Or manually with env var
export ANTHROPIC_AUTH_TOKEN="your-api-key"
cc-connect

# Background mode
nohup ~/start-cc-connect.sh > ~/.cc-connect/cc-connect.log 2>&1 &
```

**Expected output:**
```
INFO config loaded path=/home/user/.cc-connect/config.toml
INFO platform started project=my-project platform=feishu
INFO cc-connect is running projects=1
[Info] connected to wss://msg-frontier.feishu.cn/ws/v2?...
```

## Usage

### In Feishu/Lark

1. **Private Chat:** Search for your bot and send messages directly
2. **Group Chat:** @mention the bot in a group

### Available Commands

| Command | Description |
|---------|-------------|
| `/new [name]` | Start a new session |
| `/list` | List all sessions |
| `/switch <id>` | Switch to a session |
| `/current` | Show current session |
| `/dir [path]` | Show or change working directory |
| `/model` | List/switch models |
| `/mode` | Show/switch permission mode |
| `/provider list` | List API providers |
| `/cron add ...` | Add scheduled tasks |

## Troubleshooting

### Issue: "app_id and app_secret are required"
**Solution:** Fill in your Feishu app credentials in `~/.cc-connect/config.toml`

### Issue: "incompatible types: TOML value has type []any"
**Solution:** The `admin_from` field should be commented out or use proper TOML array syntax:
```toml
# Correct
# admin_from = ["user_id_1"]

# Incorrect (causes error)
admin_from = ["袁成路"]  # Non-ASCII in array can cause issues
```

### Issue: Setup command times out before QR code is scanned
**Cause:** The `cc-connect feishu setup` command waits for authorization and times out after ~60 seconds.

**Solution:** 
1. If timeout occurs, the credentials won't be auto-written to config.toml
2. Re-run the setup command to get a new QR code:
   ```bash
   pkill -f "cc-connect feishu"
   cc-connect feishu setup --project my-project
   ```
3. After scanning, if credentials weren't auto-saved, manually add them:
   ```bash
   vim ~/.cc-connect/config.toml
   # Add: app_id = "cli_xxx" and app_secret = "xxx"
   ```

### Issue: Cannot generate QR code image for sharing
**Solution:** The terminal ASCII QR code can be converted to an image:
```bash
# Install qrcode library (system Python)
sudo apt-get install -y python3-qrcode  # Debian/Ubuntu

# Generate from the URL shown in terminal
/usr/bin/python3 -c "
import qrcode
url = 'https://open.feishu.cn/page/launcher?user_code=YOUR_CODE'
qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
qr.add_data(url)
qr.make(fit=True)
qr.make_image(fill_color='black', back_color='white').save('/tmp/feishu_qrcode.png')
print('Saved to /tmp/feishu_qrcode.png')
"
```

### Issue: Claude Code not responding
**Check:**
```bash
# Verify Claude Code works standalone
claude -p "Hello" --max-turns 3

# Check auth status
claude auth status --text
```

### Issue: Cannot download binary from GitHub
**Solution:** Use browser to find correct release URL:
1. Visit https://github.com/chenhg5/cc-connect/releases
2. Find the Assets section
3. Copy the download URL for your platform
4. Use `curl -L` to download

### Issue: Permission denied when moving binary
**Solution:** Use sudo:
```bash
sudo mv cc-connect /usr/local/bin/
sudo chmod +x /usr/local/bin/cc-connect
```

## Advanced Configuration

### Multiple Projects

```toml
[[projects]]
name = "project-a"
[projects.agent]
type = "claudecode"
[projects.agent.options]
work_dir = "~/projects/project-a"

[[projects]]
name = "project-b"
[projects.agent]
type = "codex"
[projects.agent.options]
work_dir = "~/projects/project-b"
```

### Multiple Platforms

```toml
[[projects]]
name = "my-project"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "cli_xxx"
app_secret = "xxx"

[[projects.platforms]]
type = "telegram"
[projects.platforms.options]
token = "${TELEGRAM_BOT_TOKEN}"
```

### Rate Limiting

```toml
[rate_limit]
max_messages = 20
window_secs = 60

[outgoing_rate_limit]
max_per_second = 5
burst = 3
```

### Streaming Preview

```toml
[stream_preview]
enabled = true
interval_ms = 1500
min_delta_chars = 30
max_chars = 2000
```

## Platform-Specific Notes

### Feishu/Lark
- Uses WebSocket long-connection (no public IP needed)
- Supports interactive cards (enable `enable_feishu_card`)
- Supports @mention resolution (enable `resolve_mentions`)

### Telegram
- Uses long polling (no public IP needed)
- Requires bot token from @BotFather

### Discord
- Uses Gateway (no public IP needed)
- Requires bot token from Discord Developer Portal

### Slack
- Uses Socket Mode (no public IP needed)
- Requires app token and bot token

## Resources

- **CC-Connect GitHub:** https://github.com/chenhg5/cc-connect
- **Documentation:** https://github.com/chenhg5/cc-connect/blob/main/docs/
- **Feishu Open Platform:** https://open.feishu.cn/
- **Claude Code Docs:** https://code.claude.com/docs

## File Locations Summary

| File | Location |
|------|----------|
| CC-Connect binary | `/usr/local/bin/cc-connect` |
| Configuration | `~/.cc-connect/config.toml` |
| Data/Logs | `~/.cc-connect/` |
| Claude Code settings | `~/.claude/settings.json` |
| Startup script | `~/start-cc-connect.sh` |

## Common Pitfalls

1. **TOML syntax errors** - Be careful with arrays and special characters
2. **Missing permissions** - Ensure all required permissions are granted in Feishu
3. **Unpublished app** - Feishu app must be published before use
4. **Environment variables** - API keys must be exported before starting cc-connect
5. **Wrong binary architecture** - Download the correct amd64/arm64 binary for your system
