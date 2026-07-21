# Multi-Agent Profile Setup (Shared Skills & Memory)

Complete recipe for creating a second Hermes agent/profile that shares skills
and memory with the primary profile, binds a different platform bot, and runs
as an independent systemd service.

## Use Case

You have one primary Hermes agent (e.g., CEO role, strong model) and want a
second agent (e.g., operations, cheaper model) that shares all skills and
strategic memory but uses different platform credentials and a different
default model.

## Steps

### 1. Create the profile

```bash
hermes profile create <name> --clone --description "role description"
```

`--clone` copies config.yaml, .env, SOUL.md, and skills from the active profile.
This gives you a working starting point with the same API keys and model config.

### 2. Share skills via symlink

The `--clone` flag copies skills, not symlinks them. Replace with a symlink:

```bash
rm -rf ~/.hermes/profiles/<name>/skills
ln -sf ~/.hermes/skills ~/.hermes/profiles/<name>/skills
```

Now any skill change in either profile is instantly visible to both.

### 3. Verify memory sharing

The default memory config (`memtensor` provider) stores memories at
`~/.hermes/memories/`. Both profiles should point to the same directory:

```bash
grep "directory:" ~/.hermes/config.yaml ~/.hermes/profiles/<name>/config.yaml
# Both should show: directory: ~/.hermes/memories
```

If the cloned profile's config has a different path, align it to
`~/.hermes/memories`.

### 4. Update platform credentials

Edit `~/.hermes/profiles/<name>/.env` — replace the platform credentials
(e.g., `FEISHU_APP_ID`, `FEISHU_APP_SECRET`) with the new bot's values.
The default model can be changed here or in config.yaml:
```bash
hermes config set model.default deepseek-v4-flash --profile <name>
```

### 5. Customize SOUL.md

Write a role-specific personality prompt:
```bash
# Edit ~/.hermes/profiles/<name>/SOUL.md
```

Clear any stale `FEISHU_HOME_CHANNEL` from config.yaml — the new bot will
auto-discover its home channel on first DM.

### 6. Install and start the gateway

```bash
<name> gateway install    # Creates systemd service
<name> gateway start      # Starts immediately
```

### 7. CRITICAL: Add env vars to systemd service

**systemd does not source `.env` files.** Platform adapters read config from
environment variables (e.g., `FEISHU_GROUP_POLICY`), and these will be
missing from the service process. Add them manually:

```bash
# Edit ~/.config/systemd/user/hermes-gateway-<name>.service
# Add under [Service]:
Environment="FEISHU_GROUP_POLICY=open"
```

Then reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway-<name>
```

### 8. Verify

```bash
# Check process env
PID=$(pgrep -f "hermes_cli.main --profile <name>" | head -1)
cat /proc/$PID/environ | tr '\0' '\n' | grep FEISHU_GROUP_POLICY
# Must output: FEISHU_GROUP_POLICY=open

# Check gateway is running
systemctl --user status hermes-gateway-<name>

# Check platform connection
journalctl --user -u hermes-gateway-<name> --no-pager -n 20 | grep -i "connect"
```

## Feishu Group Chat Diagnostic

If the bot responds in DMs but not group chats:

1. **Check process env**: `FEISHU_GROUP_POLICY` must be `open` (not `allowlist`)
   ```bash
   PID=$(pgrep -f "hermes_cli.main --profile <name>" | head -1)
   cat /proc/$PID/environ | tr '\0' '\n' | grep FEISHU
   # Must show: FEISHU_GROUP_POLICY=open
   ```

2. **Check for inbound events**:
   ```bash
   journalctl --user -u hermes-gateway-<name> --no-pager -n 50 | grep -i "inbound\|dropping"
   ```
   - **Events arrive but get rejected** → `FEISHU_GROUP_POLICY` is likely `allowlist` (verify step 1)
   - **No inbound events at all** → Feishu app permission issue (steps 3-4)

3. **Verify Feishu app permissions via API** (use this before guessing):
   ```bash
   # Get tenant access token
   TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
     -H 'Content-Type: application/json' \
     -d '{"app_id":"<FEISHU_APP_ID>","app_secret":"<FEISHU_APP_SECRET>"}' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

   # Try to read group chat info — if it fails with "Access denied",
   # the app is missing im:chat scope
   curl -s "https://open.feishu.cn/open-apis/im/v1/chats/<CHAT_ID>/members" \
     -H "Authorization: Bearer $TOKEN" \
     | python3 -m json.tool
   ```

4. **Required Feishu app scopes for group messaging**:

   | Scope | Purpose | Required? |
   |-------|---------|-----------|
   | `im:message.p2p_msg` | DM messages | ✅ For DMs |
   | `im:message` | Basic message access | ✅ For all messages |
   | `im:message.group_at_msg` | Group messages where @mentioned | ⚠️ For @mention only |
   | `im:chat` | Read/write group chat info | ✅ **Required for ALL group messages** |

   **Without `im:chat` (or `im:chat:readonly`), the Feishu server will NOT push
   group message events to the WebSocket, even if `im:message.group_at_msg` is
   granted.** This is the most commonly missed permission when setting up a new
   Feishu bot app.

   Fix: go to [Feishu Developer Console](https://open.feishu.cn/app) → App →
   Permissions → add `im:chat` → **create and publish a new app version**.
   No Hermes restart needed — WebSocket will pick up new permissions automatically.

5. **Note: `require_mention` in config.yaml does NOT apply to Feishu**

   The `require_mention` settings in `config.yaml` are for slack, discord,
   mattermost, and matrix — not for Feishu. Feishu group message admission is
   controlled by `FEISHU_GROUP_POLICY` (env var) and `FEISHU_REQUIRE_MENTION`
   (env var, defaults to `true`). When `FEISHU_GROUP_POLICY=open`, all group
   messages are admitted regardless of `require_mention` setting.
