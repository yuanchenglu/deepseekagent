# Feishu Group Chat Troubleshooting — Admit Gate Analysis

> Session: 2026-06-25 — User reported DM works but group @mention doesn't respond.

## Symptoms

- Private DM with the bot on Feishu → instant response
- Group chat @mention of the bot → no response, no error in gateway logs
- Gateway logs show only `Inbound dm message received` for the user's DMs
- No `Inbound group message received` entries seen when @mentioning in group
- Gateway status: running, connected in websocket mode
- Feishu app permissions: verified granted in Feishu Developer Console

## Root Cause

The Feishu adapter's message admission gate (`_admit()`) silently drops
group messages before they reach the agent loop. The default policy is
`"allowlist"` with an empty allowlist, so every group message is rejected
before the @mention check is even evaluated.

## Code Analysis

### Entry point: `_handle_message_event_data()`

`adapter.py` line 2410:

```python
async def _handle_message_event_data(self, data: Any) -> None:
    ...
    reason = self._admit(sender, message)    # ← line 2424
    if reason is not None:
        logger.debug("[Feishu] dropping inbound event: %s", reason)
        return
    chat_type = getattr(message, "chat_type", "p2p")
    await self._process_inbound_message(...)   # ← never reached for groups
```

### The admit gate: `_admit()`

`adapter.py` line 4095:

```python
def _admit(self, sender: Any, message: Any) -> Optional[RejectReason]:
    ...
    is_group = getattr(message, "chat_type", "p2p") != "p2p"
    ...
    if not is_group:
        return None                     # DM always admitted

    # GROUP PATH — two sequential checks

    # CHECK 1: Group policy gate
    if not self._allow_group_message(sender_id, chat_id, is_bot=is_bot):
        return "group_policy_rejected"   # ← silent drop for default "allowlist"

    # CHECK 2: @mention requirement (only reached if CHECK 1 passed)
    if require_mention and policy != "open" and not self._mentions_self(message):
        return "group_policy_rejected"
    return None
```

### Policy resolution: `_allow_group_message()`

`adapter.py` line 4148:

```python
def _allow_group_message(self, sender_id, chat_id, *, is_bot=False):
    ...
    # Policy resolution order:
    #   1. Per-chat rule (group_rules config)
    #   2. default_group_policy (extra.get("default_group_policy"))
    #   3. FEISHU_GROUP_POLICY env var
    #   4. Fallback: "allowlist" (hardcoded default)
    policy = self._default_group_policy or self._group_policy
    # self._group_policy = os.getenv("FEISHU_GROUP_POLICY", "allowlist")

    if policy == "open":
        return True          # ← THE FIX: bypasses all checks
    if policy == "disabled":
        return False
    if policy == "admin_only":
        return False         # admins handled earlier at line 4160
    if policy == "allowlist":
        return bool(sender_ids & allowlist)  # ← empty allowlist → False
    ...
    return False
```

### Default values (from adapter.py lines 1528, 1576-1578)

```python
FEISHU_GROUP_POLICY     → defaults to "allowlist"
FEISHU_REQUIRE_MENTION  → defaults to "true"
FEISHU_ALLOWED_USERS    → defaults to "" (empty → empty allowlist)
```

## The Fix

Add `FEISHU_GROUP_POLICY=open` to `~/.hermes/.env`:

```bash
echo 'FEISHU_GROUP_POLICY=open' >> ~/.hermes/.env
```

Then restart the gateway **from a terminal** (not from within a gateway
session — the restart command would kill itself):

```bash
hermes gateway restart
```

### Why "open" is the right choice

| Policy | Behaviour | Use case |
|--------|-----------|----------|
| `allowlist` (default) | Only specified users can talk in groups | Locked-down groups |
| `open` | Anyone can talk in groups (if @mention is satisfied) | Open collaboration |
| `disabled` | No one can talk in groups | Bot should never respond in groups |
| `admin_only` | Only admin list members | Admin-only bot |

With `"open"` + the default `FEISHU_REQUIRE_MENTION=true`:
- DM works (always admitted, regardless of policy)
- Group @mention → bot responds
- Group without @mention → bot silently ignores

## Related Feishu Plugin Env Vars

| Env var | Default | Purpose |
|---------|---------|---------|
| `FEISHU_GROUP_POLICY` | `allowlist` | Group chat admission policy |
| `FEISHU_REQUIRE_MENTION` | `true` | Require @mention in groups |
| `FEISHU_ALLOWED_USERS` | `""` | Comma-separated user IDs for allowlist |
| `FEISHU_ALLOW_ALL_USERS` | unset | Bypass DM user allowlist (dev) |
| `FEISHU_ALLOW_BOTS` | `none` | How to handle messages from other bots |
| `FEISHU_BOT_OPEN_ID` | `""` | Bot's own open_id for @mention matching |
| `FEISHU_BOT_NAME` | `""` | Bot name for @mention fallback matching |

## Constraint

A gateway restart **cannot** be performed from within a gateway session
(the command would be killed by its own SIGTERM). Must be run from a
separate terminal. The error is explicit:

```
Blocked: cannot restart or stop the gateway from inside the gateway process.
Run `hermes gateway restart` from a separate shell outside the running gateway.
```
