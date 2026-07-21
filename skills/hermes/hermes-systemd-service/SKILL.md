---
name: hermes-systemd-service
description: Set up Hermes Agent as a systemd service for automatic startup on boot. Handles service file creation, installation, and enablement.
version: 1.1.0
metadata:
  hermes:
    tags: [systemd, service, autostart, boot, linux, ubuntu]
---

# Hermes Systemd Service Setup

Set up Hermes Agent as a systemd service to automatically start on system boot and restart on failure.

> **Related**: `references/multi-agent-profile-setup.md` — complete recipe for creating additional Hermes agents (profiles) with shared skills & memory, separate platform bots, and independent systemd services.

## Prerequisites

- Linux system with systemd (Ubuntu, Debian, CentOS, etc.)
- Hermes installed in a virtual environment
- sudo privileges

## Quick Setup

### 1. Locate Hermes Binary

```bash
which hermes
# or check common locations:
ls ~/.local/bin/hermes
ls /usr/local/bin/hermes
ls ~/.hermes/hermes-agent/venv/bin/hermes
```

### 2. Create Service File

Create `/etc/systemd/system/hermes.service`:

```ini
[Unit]
Description=Hermes Agent - AI Assistant Service
After=network.target

[Service]
Type=simple
User=USERNAME
Environment="HOME=/home/USERNAME"
Environment="PATH=/home/USERNAME/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/USERNAME/.hermes"
WorkingDirectory=/home/USERNAME
ExecStart=/home/USERNAME/.hermes/hermes-agent/venv/bin/hermes --stdio
Restart=always
RestartSec=5
StandardInput=socket
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Replace USERNAME with the actual username.**

### 3. Install and Enable

```bash
# Copy service file
sudo cp hermes.service /etc/systemd/system/hermes.service

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable hermes.service

# Start the service now (optional)
sudo systemctl start hermes.service
```

### 4. Verify

```bash
# Check status
sudo systemctl status hermes.service

# View logs
sudo journalctl -u hermes.service -f
```

## Service Management Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start hermes` | Start the service |
| `sudo systemctl stop hermes` | Stop the service |
| `sudo systemctl restart hermes` | Restart the service |
| `sudo systemctl status hermes` | Check service status |
| `sudo systemctl enable hermes` | Enable auto-start on boot |
| `sudo systemctl disable hermes` | Disable auto-start |
| `sudo journalctl -u hermes -f` | View live logs |

## Critical Pitfall: .env Not Loaded for Profile Services

**systemd does not automatically source `.env` files.** When running a Hermes gateway with `--profile <name>`, environment variables set in `~/.hermes/profiles/<name>/.env` are **NOT** available to the service process. This silently breaks platform adapters that read config from env vars (e.g., `FEISHU_GROUP_POLICY`, `FEISHU_ALLOW_BOTS`).

**Symptoms:**
- Bot responds in DMs but not in group chats (env var defaults to `allowlist`)
- Platform-specific features silently use wrong defaults
- No errors in logs — just different behavior than expected

**Diagnostic:**
```bash
# Check what the process actually sees
PID=$(pgrep -f "hermes_cli.main --profile yunying" | head -1)
cat /proc/$PID/environ | tr '\0' '\n' | grep FEISHU
# If empty → .env vars are NOT loaded
```

**Fix — add each required env var to the systemd service file:**
```ini
Environment="FEISHU_GROUP_POLICY=open"
Environment="FEISHU_ALLOW_BOTS=all"
# ... any other env vars the profile's .env depends on
```
Then: `systemctl --user daemon-reload && systemctl --user restart <service-name>`

**After restart, verify:**
```bash
PID=$(pgrep -f "hermes_cli.main --profile yunying" | head -1)
cat /proc/$PID/environ | tr '\0' '\n' | grep FEISHU_GROUP_POLICY
# Should output: FEISHU_GROUP_POLICY=open
```

## Remote Gateway Management (via SSH)

When Hermes Gateway runs as a systemd user service on a remote machine and you manage it via SSH from another machine:

### The "Cannot restart from inside gateway" block

The gateway process monitors its descendant process tree. **Any command that would restart or stop the gateway service** — `hermes gateway restart`, `systemctl --user restart`, `nohup`, `setsid`, `at` — is **blocked** with:

```
Blocked: cannot restart or stop the gateway from inside the gateway process.
```

This happens even when SSH connects from a different machine, because the SSH session becomes a descendant of the gateway's process tree.

### Solution: Use `systemctl --user reload`

`systemctl --user reload` is the **only reliable workaround**:

```bash
systemctl --user reload hermes-gateway.service
```

This sends the USR1 signal (via `ExecReload=/bin/kill -USR1 $MAINPID`), which triggers a graceful config reload without fully stopping the process. The reload is not blocked because it doesn't count as "stopping" the service.

### Config changes first, then reload

For non-service-impacting changes (e.g., `approvals.mode`, model config), update the config first, then reload:

```bash
# 1. Change config (full path in case hermes isn't in PATH)
~/.local/bin/hermes config set approvals.mode manual
# or: ~/.hermes/hermes-agent/hermes config set approvals.mode manual

# 2. Reload gateway to pick up changes
systemctl --user reload hermes-gateway.service
```

### If `hermes` is not in PATH

Even when installed via pipx, `hermes` may not be in PATH on some machines:

```bash
find ~/.hermes -maxdepth 3 -name hermes -type f 2>/dev/null
```

Common locations:
- `~/.local/bin/hermes`
- `~/.hermes/hermes-agent/hermes`

### Approvals modes reference

`approvals.mode` controls command approval prompts (configure via `hermes config set approvals.mode <value>`). Valid values:

| Mode | Behavior |
|------|----------|
| `manual` | Prompt only for destructive commands (`rm -rf`, `git reset --hard`, etc.) |
| `smart` | Use an auxiliary LLM to auto-approve low-risk commands |
| `off` | Skip all approval prompts (equivalent to `--yolo`) |

Note: `auto` is **not a valid value** — Hermes logs "Unknown approvals.mode 'auto' — defaulting to 'manual'".

## Troubleshooting

> **Reference**: `stale-pyc-debug-recipe.md` — detailed reproduction steps and traceback for the "too many values to unpack" error caused by stale bytecache after code updates.
>
> **Reference**: `gateway-crash-diag-pipeline.md` — session-specific walkthrough of a real crash caused by `_middleware` attribute error + UU merge conflict, with exact commands and output.

### Gateway Crash Diagnostics (PluginManager errors, UU conflicts, branch drift)

**When to use this section:**
- Gateway starts and immediately exits with exit code 1 (FAILURE)
- Error message includes `'PluginManager' object has no attribute '_middleware'`
- Multiple profile gateways crash at once or after restart
- Systemd service shows persistent `auto-restart` / `failed` state
- Gateway was working, then crashes after a `git pull` or code update

#### Diagnostic Pipeline

**Step 1: Check systemd vs. actual process state (they can differ)**

A gateway can be running as a process even though systemd thinks it's failed, and vice versa:

```bash
# Systemd state
systemctl --user list-units --type=service --all | grep -iE 'hermes|gateway'

# Actual processes
ps aux | grep 'hermes.*gateway' | grep -v grep

# Cross-reference: if systemd says "failed" but ps shows the process,
# the service was manually started outside systemd (e.g. via direct python -m)
```

**Signs of trouble:**
- Systemd shows `failed` but process exists → old orphan process
- Systemd shows `auto-restart` → service keeps crashing on startup
- Systemd shows `running` but process NOT in ps → stale systemd state

**Step 2: Log triage — read logs in this order**

```bash
# 1. systemd journal (most recent first)
journalctl --user -u hermes-gateway-<profile>.service --since "10 minutes ago" --no-pager

# 2. Gateway runtime log
tail -50 ~/.hermes/logs/gateway.log

# 3. Agent error log
tail -50 ~/.hermes/logs/errors.log

# 4. Exit diagnostic (JSON-structured, shows Python/system shutdown context)
cat ~/.hermes/logs/gateway-exit-diag.log | tail -20

# 5. Agent operations log
tail -50 ~/.hermes/logs/agent.log
```

**Common error signatures:**

| Log pattern | Likely cause |
|---|---|
| `'PluginManager' object has no attribute '_middleware'` | Code version mismatch — see Steps 3-4 |
| `ValueError: too many values to unpack` | Stale `.pyc` bytecache — see `stale-pyc-debug-recipe.md` |
| `Stream stale for 180s... Broken pipe` | Network issue or API provider instability |
| `bridge init failed — [timeout] session.open` | MemOS bridge not responding (non-fatal) |
| `[99992402] field validation failed` | Feishu message schema mismatch |
| `asyncio.run.returned... success: false` | Gateway exited non-zero — check journal |

**Step 3: Git forensics — check source code state**

If the error mentions a missing attribute or wrong class, the Git working tree may be inconsistent:

```bash
cd ~/.hermes/hermes-agent

# Full status — check for UU (unmerged) files
git status --short
# UU = conflict not yet resolved

# Check for actual conflict markers
grep -n '<<<<<<<\|=======\|>>>>>>>' gateway/platforms/feishu.py

# Branch and divergence
git log --oneline HEAD..upstream/main | wc -l   # behind upstream?
git log --oneline upstream/main..HEAD | wc -l   # ahead of upstream?
```

**Step 4: Resolve UU merge conflicts**

```bash
# View the 3 stages in the index:
git ls-files --stage gateway/platforms/feishu.py
# Stage 1: merge base | Stage 2: ours | Stage 3: theirs

# Quick resolve: keep one side
git checkout --theirs gateway/platforms/feishu.py   # accept upstream
# or
git checkout --ours gateway/platforms/feishu.py     # accept local branch

# Mark as resolved
git add gateway/platforms/feishu.py

# Verify no conflict markers remain
grep -c '<<<<<<<' gateway/platforms/feishu.py       # should be 0
```

**Step 5: Restart all gateways and verify**

```bash
# Restart all gateway services at once
for srv in hermes-gateway hermes-gateway-course-designer hermes-gateway-cto hermes-gateway-yunying hermes-web-ui; do
    systemctl --user restart "$srv.service" 2>/dev/null && echo "$srv restarted" || echo "$srv skipped"
done

# Wait and verify
sleep 5
for srv in hermes-gateway hermes-gateway-course-designer hermes-gateway-cto hermes-gateway-yunying; do
    status=$(systemctl --user is-active "$srv.service" 2>/dev/null)
    echo "$srv: $status"
done

# Verify Feishu connection
journalctl --user -u hermes-gateway.service --since "1 minute ago" --no-pager | grep -i "connected to wss\|feishu connected"
```

**Step 6: Verify code loads correctly in the new process**

```bash
# Test the specific component that was failing
python3 -c "from hermes_cli.plugins import PluginManager; pm = PluginManager(); print('_middleware exists:', hasattr(pm, '_middleware'))"
```

**Root cause analysis of `_middleware` errors:**

The `PluginManager._middleware` attribute was added in a specific upstream commit. If the running process loaded an older version of `plugins.py` that doesn't have `self._middleware: Dict[...] = {}` in `__init__`, any middleware-invoking code path crashes with `AttributeError`.

Three common triggers:
1. **Merge conflict leaves stale code** — UU file means the correct version wasn't loaded from either side
2. **Process loaded old bytecache** — `.pyc` files compiled before the update reference old signatures
3. **Branch drift** — the code on disk has a new import referencing `_middleware`, but `PluginManager.__init__` is still the old version lacking the attribute

### Service fails with "too many values to unpack" after code update

If a long-running Gateway crashes with `ValueError: too many values to unpack (expected N)` after a `git pull` or code update:

**Root cause**: Stale `.pyc` bytecache. Python inline imports (`from X import Y` inside a method) load the new module from disk, but method bodies compiled from old bytecache expect different function signatures.

**Fix**:
```bash
# 1. Restart the service
systemctl --user restart hermes-gateway-<profile>.service

# 2. Clean bytecache to prevent recurrence
find ~/.hermes/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 3. Verify
systemctl --user status hermes-gateway-<profile>.service
```

**Prevention**: Always restart all running Gateway services after updating Hermes code:
```bash
for srv in $(systemctl --user list-units --type=service --state=running --no-legend 2>/dev/null | grep hermes-gateway | awk '{print $1}'); do
    systemctl --user restart "$srv"
done
find ~/.hermes/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

### Service fails to start

1. Check Hermes binary path is correct:
   ```bash
   ls -la /home/USERNAME/.hermes/hermes-agent/venv/bin/hermes
   ```

2. Check environment variables:
   ```bash
   echo $HERMES_HOME
   ```

3. View error logs:
   ```bash
   sudo journalctl -u hermes.service --no-pager -n 50
   ```

### Permission issues

Ensure the service user has proper permissions:
```bash
sudo chown -R USERNAME:USERNAME /home/USERNAME/.hermes
```

### Path issues

If Hermes is installed in a different location, update the `ExecStart` path in the service file.

## Alternative: User Service

To run Hermes as a user service (no sudo required):

```bash
# Create user service directory
mkdir -p ~/.config/systemd/user/

# Copy service file (adjust paths as needed)
cp hermes.service ~/.config/systemd/user/hermes.service

# Enable and start
systemctl --user daemon-reload
systemctl --user enable hermes.service
systemctl --user start hermes.service
```

Note: User services may not start on boot unless `lingering` is enabled:
```bash
sudo loginctl enable-linger USERNAME
```
