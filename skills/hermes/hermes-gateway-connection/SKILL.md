---
name: hermes-gateway-connection
description: >
  Diagnose and fix silent messaging-platform failures on Hermes Gateway.
  When Hermes stops responding on Feishu, Telegram, Discord, or another
  platform — gateway is running but no messages get through. Covers the
  credential-loss failure mode, the "No messaging platforms enabled"
  signal, and the recovery workflow.
version: 1.0.0
---

# Hermes Gateway Connection Troubleshooting

When a previously working messaging platform goes silent — Hermes doesn't
respond on Feishu/Telegram/Discord — the gateway is often running but the
platform adapter silently failed to load.

## Diagnostic Flow

### 1. Check gateway status

```bash
hermes gateway status
```

Verify the process PID is present and `LastExitStatus` (normal = 15/SIGTERM).

### 2. Check startup logs — look for the key signal

```bash
grep -E "platform|enabled|connect" ~/.hermes/logs/gateway.log | tail -30
```

The smoking gun: **`No messaging platforms enabled`** — every platform
adapter failed to load. This means one or more `required_env` variables
are missing from `~/.hermes/.env`.

A healthy gateway log shows:
```
Connecting to feishu...
✓ feishu connected
Gateway running with 1 platform(s)
```

### 3. Verify platform credentials in `.env`

```bash
grep -i "FEISHU\|TELEGRAM\|DISCORD\|SLACK" ~/.hermes/.env
```

Each platform plugin declares its required env vars in
`plugins/platforms/<name>/plugin.yaml`. If those vars are absent,
the plugin's `check_fn` returns false and the platform is skipped.

**Feishu / Lark** (plugins/platforms/feishu/plugin.yaml):
- `FEISHU_APP_ID` — required, App ID like `cli_xxx`
- `FEISHU_APP_SECRET` — required
- `FEISHU_DOMAIN` — `feishu` (China) or `lark` (International)
- `FEISHU_ALLOW_ALL_USERS=true` — bypass allowlist (dev)

### 4. Check why credentials were lost

Common causes:
- Hermes update that rebuilt `.env`
- Manual edit error
- Migration / backup-restore that omitted the file
- `.env` was accidentally truncated (starts with 3 lines, no Feishu vars)

The `.env` file is **NOT** managed by Hermes update — it's user data. If it's
missing entries, they must be manually re-added.

### 5. Restore credentials and restart

```bash
# Add missing env vars to ~/.hermes/.env
echo 'FEISHU_APP_ID=cli_xxx' >> ~/.hermes/.env
echo 'FEISHU_APP_SECRET=***' >> ~/.hermes/.env

# Restart gateway
hermes gateway restart

# Verify
sleep 5 && tail -10 ~/.hermes/logs/gateway.log
```

Expected after fix:
```
Connecting to feishu...
[Feishu] Connected in websocket mode (feishu)
✓ feishu connected
Gateway running with 1 platform(s)
```

### 6. Feishu Group Chat Not Responding (DM works, group @mention doesn't)

**Symptom:** Private DM conversations with the bot work perfectly, but messages
sent in group chats — even with @mention — get no response. The gateway is
running, the bot is in the group, Feishu app permissions are all granted.

**Root cause:** The Feishu adapter enforces a group chat policy that defaults
to `"allowlist"` with an **empty** allowlist. Every group message is silently
dropped by the admit gate before it reaches the agent loop.

The admit gate (`_admit()` in the Feishu adapter) runs two checks for group
messages:
1. `_allow_group_message()` — checks `FEISHU_GROUP_POLICY` (default:
   `"allowlist"`) against the sender and chat. With an empty allowlist,
   everyone is rejected.
2. @mention requirement — only checked if step 1 passes (so step 1's
   rejection short-circuits it entirely).

**Fix — set `FEISHU_GROUP_POLICY=open` in `.env`:**
```bash
echo 'FEISHU_GROUP_POLICY=open' >> ~/.hermes/.env
hermes gateway restart
```

With `"open"` policy, the admit gate allows all group messages through to
the @mention check (step 2). Combined with the default
`FEISHU_REQUIRE_MENTION=true` (bots only respond when @mentioned in groups),
this gives the expected behaviour:
- **Group @mention** → bot responds ✅
- **Group without @mention** → bot silently ignores ✅
- **DM** → always responds (regardless of policy) ✅

**Verification:**
```bash
grep -i "FEISHU_GROUP_POLICY\\|FEISHU_REQUIRE_MENTION" ~/.hermes/.env
# Restart is required — cannot restart gateway from within a gateway session
hermes gateway restart
```

**If it still doesn't work:** Check gateway logs for group vs DM routing.
Inbound messages are logged at INFO level:
```
[Feishu] Inbound dm message received: ...
[Feishu] Inbound group message received: ...
```
If only "dm" messages appear when you @mention the bot in a group, the
Feishu app's event subscription (`im.message.receive_v1`) may be missing
group message events — check the Feishu Developer Console under
Event Subscriptions → im.message.receive_v1.

---

### 7. FEISHU_REQUIRE_MENTION=false Still Not Working (fork/adapter mismatch)

**Symptom:** `.env` has `FEISHU_GROUP_POLICY=open` and
`FEISHU_REQUIRE_MENTION=false` set correctly, gateway is restarted, but
group messages without @mention are still silently ignored.

#### 7a. Quick self-check — are you looking at the right gateway?

Multiple gateway processes can run simultaneously (different profiles, forks,
or test instances). The env var you edited may belong to a different gateway:

```bash
# List ALL running gateway processes
ps aux | grep "hermes_cli.main.*gateway" | grep -v grep
```

Each gateway reads `.env` from its own `HERMES_HOME`. Find each one via its
launchd plist:

```bash
cat ~/Library/LaunchAgents/ai.hermes.gateway*.plist
```

Look for the `<key>HERMES_HOME</key>` value inside
`<key>EnvironmentVariables</key>`. Check that `.env`:

```bash
# For HERMES_HOME=~/.hermes:
cat ~/.hermes/.env | grep FEISHU
# For HERMES_HOME=~/.deepagent:
cat ~/.deepagent/.env | grep FEISHU
```

#### 7b. If env vars are correct — check if the adapter code reads them

The env var may be present in `.env` but never referenced in the source code
(most common with forked versions).

```bash
# Search for FEISHU_REQUIRE_MENTION in the adapter
grep -rn "REQUIRE_MENTION\|_require_mention" gateway/platforms/feishu* 2>/dev/null
# Also find the group-accept gate method (varies by version)
grep -n "_should_accept_group_message\|_admit" gateway/platforms/feishu*
```

If these searches return **empty** (no matches), you have an adapter version
that predates the `FEISHU_REQUIRE_MENTION` feature. The adapter's group-message
gate hardcodes the @mention requirement with a bare `return False` at the end —
no env var check exists.

**DeepAgent / older Hermes fork specifics:**
- Platform adapters as **flat files**: `gateway/platforms/feishu.py` (not `feishu/adapter.py`)
- Method name: `_should_accept_group_message()` (upstream Hermes uses `_admit()`)
- Hardcoded `return False` at line ~3080 (no FEISHU_REQUIRE_MENTION support)

#### 7c. Fix — add FEISHU_REQUIRE_MENTION support (4 locations)

1. **Settings dataclass** — add field:
   ```python
   @dataclass
   class FeishuAdapterSettings:
       ...
       require_mention: bool = True
   ```

2. **Settings parsing** — read env var:
   ```python
   require_mention=os.getenv("FEISHU_REQUIRE_MENTION", "true").strip().lower() not in (
       "false", "0", "no",
   ),
   ```

3. **Instance attribute** — store in `__init__`:
   ```python
   self._require_mention = settings.require_mention
   ```

4. **Group-message gate** — add early return:
   ```python
   def _should_accept_group_message(self, message, sender_id, chat_id="") -> bool:
       if not self._allow_group_message(sender_id, chat_id):
           return False
       if not self._require_mention:     # <-- skip @mention check
           return True
       # ... rest of @mention logic ...
   ```

#### 7d. After patching — restart

```bash
# Kill the old process — launchd's KeepAlive auto-restarts
kill <PID>
```

If auto-restart doesn't fire:
```bash
launchctl bootout gui/$(id -u)/<label> && \
launchctl bootstrap gui/$(id -u)/<plist-path>
```

#### 7e. Verification

```bash
tail -5 ~/{hermes_home}/logs/gateway.log
# Expected: "[Lark] connected to wss://..."
```

Then send a group message **without** @mention — it should now route through.

> **Method name note:** Upstream Hermes adapter uses `_admit()` →
> `_allow_group_message()` + `_mentions_self()`. DeepAgent's fork uses
> `_should_accept_group_message()` → `_allow_group_message()` +
> `_message_mentions_bot()`. Names differ but fix pattern is identical:
> check `FEISHU_REQUIRE_MENTION` before doing any mention matching.

### 8. Feishu Outbound Markdown Table Content Shows Raw Syntax

**Symptom:** Feishu bot replies display raw table syntax (`| col | col |`, `---|---|---`)
instead of rendered table content. Other markdown (bold, headers, code) may also be
lost if the message contains a table.

**Root cause:** `_build_outbound_payload()` in `plugins/platforms/feishu/adapter.py`
detects markdown table syntax via `_MARKDOWN_TABLE_RE` and force-downgrades the
**entire message** to `msg_type=text` — which Feishu renders as raw plaintext.

Original rationale: "Feishu post-type 'md' elements do not render markdown tables;
sending table content as post causes the message to appear blank on the client."

**This rationale is now outdated.** As of mid-2026, Feishu's `post(md)` element
natively supports GFM tables (including alignment, Unicode, mixed bold+table+lists).
Confirmed empirically against live Feishu API and documented in Feishu's own API docs.

**Status in official Hermes repo:**
- Bug exists in `main` branch — identical code path, unpatched
- 5+ open issues (#9549, #52786, #58269, #61643, etc.)
- 5 open unmerged PRs (#57566, #58019, #58391, #61377, #61647)
- No fix shipped upstream yet. This is a well-known open bug.

**Preferred fix (simplest, gives best UX):**
Remove the `_MARKDOWN_TABLE_RE` guard entirely. Add table-pipe detection to
`_MARKDOWN_HINT_RE` so pure-table messages still trigger `post(md)` mode.

**Fallback fix (when native table rendering is untested/unverified):**
Use `_convert_table_content_to_readable()` to strip pipe/separator syntax
into readable text, then route as `post(md)` for remaining markdown.

**Cross-machine deployment via SSH:**
```bash
# Find adapter path on each pipx-installed host:
ls ~/.local/share/pipx/venvs/hermes-agent/lib/python3.*/site-packages/plugins/platforms/feishu/adapter.py

# Apply fix via SSH (Tailscale):
ssh bluth@<tailscale-ip> 'adapter=.../adapter.py; python3 -c "..."'

# Restart gateway (kill + KeepAlive auto-restart):
ssh bluth@<tailscale-ip> 'kill $(pgrep -f "hermes.*gateway")'
```

**Incremental rollout pattern:** When deploying across multiple machines, fix only
one host first, verify with the test prompt, then roll out to the rest. Avoids
breaking all Feishu bots at once if the environment differs (different Feishu
API version, different Hermes adapter fork, etc.).

### 9. Linux systemd Gateway: Wrong Python Binary / Broken typing_extensions

**Symptom:** Gateway fails to start with an import error like
`cannot import name 'Sentinel' from 'typing_extensions'`. The system
Python's `typing_extensions` is too old (lacks `Sentinel`).

**Root cause:** `hermes gateway install` may create a systemd service that
uses `/usr/bin/python3` (system Python) instead of the pipx venv Python.
The pipx venv has the correct `typing_extensions`, but the systemd service
doesn't use it.

```bash
# Check what Python the systemd service uses
grep ExecStart ~/.config/systemd/user/hermes-gateway.service

# Expected: ExecStart=<pipx-venv-python> -m hermes_cli.main gateway run --replace
#            e.g. /home/bluth/.local/share/pipx/venvs/hermes-agent/bin/python

# Fix: sed the ExecStart to use pipx venv Python
sed -i "s|ExecStart=/usr/bin/python3|ExecStart=$HOME/.local/share/pipx/venvs/hermes-agent/bin/python|" \
  ~/.config/systemd/user/hermes-gateway.service

# Some installs also inject a bogus VIRTUAL_ENV pointing to user site-packages
# Remove it — the pipx venv manages its own isolated deps
sed -i '/VIRTUAL_ENV=/d' ~/.config/systemd/user/hermes-gateway.service

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway
```

**Why this happens:** On Linux, `hermes gateway install` writes the systemd
unit using the first `python3` found in `PATH` at install time, not the
pipx venv's Python. If pipx was installed via system pip (which uses
`/usr/bin/python3`), the venv Python is correct but the systemd unit isn't. 
This is a known Hermes installer quirk on Linux. Check the
`ExecStart` line immediately after `hermes gateway install` to catch it
early.

## References

- `references/feishu-gateway-silent-diagnostics.md` — Full session transcript and reproduction steps for the Feishu credential-loss pattern.
- `references/feishu-group-chat-troubleshooting.md` — Detailed code-level analysis of the group chat admit gate.
- `references/feishu-markdown-table-rendering.md` — Markdown table rendering fix (both fallback and preferred approaches, with SSH cross-machine deployment details).
- `references/feishu-table-verification-prompt.md` — Test prompts to verify the fix is working (standard, pure-table, wide-table scenarios).
