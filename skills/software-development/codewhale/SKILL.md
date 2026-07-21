---
name: codewhale
description: Install, configure, and integrate CodeWhale — a DeepSeek-first terminal coding agent. Covers npm/cargo install, DeepSeek API config, V4Pro/V4Flash model setup, and the Feishu/Lark mobile bridge for phone-controlled coding.
---

# CodeWhale Setup & Feishu Bridge

CodeWhale (`codewhale`) is a DeepSeek-first terminal coding agent (Rust TUI) with 1M-token context, thinking-mode streaming, model auto-routing, and an official Feishu/Lark bridge for phone-controlled coding.

## Triggers

Use this skill when the user wants to:
- Install or configure CodeWhale
- Set up DeepSeek API credentials for CodeWhale
- Connect CodeWhale to a Feishu/Lark bot for mobile control
- Troubleshoot the Feishu bridge connection

## 1. Installation

**Easiest path** — npm wrapper (downloads prebuilt Rust binaries):

```bash
npm install -g codewhale
codewhale --version   # verify
```

Alternative paths: `cargo install codewhale-cli --locked && cargo install codewhale-tui --locked` (requires Rust 1.88+), Homebrew, or direct binary download from GitHub Releases.

## 2. DeepSeek API Configuration

### Save API key (recommended):

```bash
codewhale auth set --provider deepseek --api-key "sk-..."
```

### Full config at `~/.deepseek/config.toml`:

```toml
provider = "deepseek"
api_key = "sk-..."
base_url = "https://api.deepseek.com/beta"
default_text_model = "deepseek-v4-pro"
reasoning_effort = "max"
cost_currency = "cny"   # for Chinese users

[providers.deepseek]
api_key = "sk-..."
base_url = "https://api.deepseek.com/beta"

[tui]
locale = "zh-Hans"
```

### Verify:

```bash
codewhale doctor
```

### Model usage:
- `codewhale --model auto` — **recommended**: Fin router auto-selects V4Pro vs V4Flash + thinking level per turn
- `codewhale --model deepseek-v4-pro` — manual Pro
- `codewhale --model deepseek-v4-flash` — manual Flash

## 3. Feishu Bridge Architecture

```
Phone Feishu → Feishu WebSocket long-connection → bridge (Node.js) → localhost:7878 (codewhale serve --http) → DeepSeek API
```

**Key point**: The bridge uses WebSocket long-connection mode, NOT webhook callbacks. No public URL needed. The runtime API stays bound to 127.0.0.1.

## 4. Feishu Bridge Setup

### 4a. Copy bridge files:

```bash
sudo mkdir -p /opt/codewhale/bridge
sudo cp -r ~/Code/CodeWhale/integrations/feishu-bridge/* /opt/codewhale/bridge/
sudo chown -R $USER:$USER /opt/codewhale/bridge
cd /opt/codewhale/bridge && npm install --omit=dev
```

### 4b. Create env files:

**`/etc/deepseek/feishu-bridge.env`**:
```ini
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=your-app-secret
FEISHU_DOMAIN=feishu

DEEPSEEK_RUNTIME_URL=http://127.0.0.1:7878
DEEPSEEK_RUNTIME_TOKEN=<openssl rand -hex 32>
DEEPSEEK_WORKSPACE=/opt/whalebro
DEEPSEEK_MODEL=auto
DEEPSEEK_MODE=agent
DEEPSEEK_ALLOW_SHELL=true
DEEPSEEK_TRUST_MODE=false
DEEPSEEK_AUTO_APPROVE=false

# First pairing: allow all. Lock down after getting your chat_id.
DEEPSEEK_CHAT_ALLOWLIST=
DEEPSEEK_ALLOW_UNLISTED=true

FEISHU_THREAD_MAP_PATH=/var/lib/codewhale-feishu-bridge/thread-map.json
FEISHU_ALLOW_GROUPS=false
FEISHU_REQUIRE_PREFIX_IN_GROUP=true
FEISHU_GROUP_PREFIX=/ds
FEISHU_MAX_REPLY_CHARS=3500
DEEPSEEK_TURN_TIMEOUT_MS=900000
```

**`/etc/deepseek/runtime.env`**:
```ini
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_RUNTIME_TOKEN=<same token as above>
```

Ensure files are readable by the bridge user: `sudo chown $USER:$USER /etc/deepseek/*.env`

### 4c. Create runtime directories (**crucial — permission pitfalls**):

```bash
sudo mkdir -p /var/lib/codewhale-feishu-bridge /opt/whalebro
sudo chown -R $USER:$USER /var/lib/codewhale-feishu-bridge /opt/whalebro
```

**⚠️ PITFALL**: The bridge writes `thread-map.json.tmp` → atomic rename → `thread-map.json` in this directory. If created with `sudo mkdir` without `chown`, you'll get `EACCES: permission denied, open 'thread-map.json.tmp'` on the first incoming message.

### 4d. Feishu Open Platform Configuration

Go to `https://open.feishu.cn/app` → find your app:

1. **Add bot capability** (应用能力 → 机器人)
2. **Permissions** (权限管理):
   - `im:message`
   - `im:message:send_as_bot`
3. **Event subscription** (事件订阅):
   - Subscribe to `im.message.receive_v1`
   - **Use WebSocket long-connection mode** (长连接), NOT webhook URL
4. **Publish** the app (创建版本 → 发布)

**⚠️ Use a separate Feishu app for CodeWhale** — don't reuse the Hermes Agent bot. They're independent services and sharing an app causes message routing conflicts.

### 4e. Start the runtime:

```bash
codewhale serve --http \
  --host 127.0.0.1 \
  --port 7878 \
  --auth-token "<your-runtime-token>"
```

Verify: `curl -s http://127.0.0.1:7878/health` → `{"status":"ok"}`

### 4f. Start the bridge:

```bash
cd /opt/codewhale/bridge
set -a && source /etc/deepseek/feishu-bridge.env && set +a
node src/index.mjs
```

**⚠️ PITFALL**: The bridge reads env vars directly (`process.env.FEISHU_APP_ID` etc.), it does NOT parse `.env` files. You must source the env file before running. Using `set -a; source <file>; set +a` is the reliable pattern.

**⚠️ PITFALL — background output buffering**: When running as a background/systemd service, Node.js stdout is buffered. Use `stdbuf -oL -eL node src/index.mjs` for line-buffered output, or log with `| tee ~/.codewhale/bridge.log` (NOT `/var/log/` — that requires root).

### 4g. Verify WebSocket connection:

Successful startup shows:
```
[info] client ready
[info] event-dispatch is ready
Starting DeepSeek Feishu bridge
Runtime: http://127.0.0.1:7878
[info] [ws] ws client ready        ← WebSocket connected!
```

## 5. Post-Setup: Lock Down

After first successful DM, the bridge replies with your `chat_id` and `open_id`. Add them to `DEEPSEEK_CHAT_ALLOWLIST` and set `DEEPSEEK_ALLOW_UNLISTED=false`:

```ini
DEEPSEEK_CHAT_ALLOWLIST=oc_xxxxxxxx,your_open_id
DEEPSEEK_ALLOW_UNLISTED=false
```

## 6. Bridge Commands (from Feishu)

| Command | Action |
|---------|--------|
| `/help` | Show commands |
| `/status` | Runtime + workspace status |
| `/threads` | List recent threads |
| `/new` | Create new thread |
| `/resume <id>` | Resume a thread |
| `/interrupt` | Interrupt active turn |
| `/compact` | Compact context |
| `/allow <id>` | Approve tool call |
| `/deny <id>` | Deny tool call |
| Anything else | Sent as a prompt |

## 7. Troubleshooting

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `EACCES thread-map.json.tmp` | `/var/lib/codewhale-feishu-bridge/` owned by root | `sudo chown -R $USER:$USER /var/lib/codewhale-feishu-bridge/` |
| `DEEPSEEK_RUNTIME_TOKEN is required` | Bridge didn't source the env file | Use `set -a; source ...env; set +a` before `node src/index.mjs` |
| No output in background | Node.js stdout buffered | Use `stdbuf -oL -eL` or log to `~/.codewhale/` |
| `permission denied` on log | Writing to `/var/log/` as non-root | Use `~/.codewhale/bridge.log` |
| Bridge exits immediately | Old process still on port | `pkill -f "node src/index.mjs"` then restart |
| `--bind` not recognized | Wrong flag name | Use `--host`, not `--bind` |

## Reference Files

- `references/config.toml` — Full `~/.deepseek/config.toml` template
- `references/feishu-bridge.env` — Bridge env template (`/etc/deepseek/feishu-bridge.env`)
- `references/runtime.env` — Runtime env template (`/etc/deepseek/runtime.env`)
