# DeepAgent (Fork) Feishu Mention Fix — Session 2026-06-30

## Scenario

DeepAgent (a Hermes fork at `~/Code/DeepAgent`) has a Feishu bot configured at
`~/.deepagent/`. The `.env` file already had:

```
FEISHU_GROUP_POLICY=open
FEISHU_REQUIRE_MENTION=false
```

Despite these settings, the bot still required @mention in group chats. DM
worked fine.

## Multi-Gateway Discovery

Two gateway processes were running simultaneously:

| PID | Source | HERMES_HOME | App ID |
|-----|--------|-------------|--------|
| 31473 | `~/.hermes/hermes-agent/venv/` (Hermes) | `~/.hermes` | `cli_aaa0ebd30f399be7` |
| 30146 | `/Volumes/Doc/Code/DeepAgent/venv/` (DeepAgent) | `~/.deepagent` | `cli_aac9dbfca039dcc8` |

The user had edited `~/.deepagent/.env`, but the DeepAgent adapter code
(same fork) didn't read `FEISHU_REQUIRE_MENTION` at all.

## Root Cause

DeepAgent's `gateway/platforms/feishu.py` (3986 lines) uses
`_should_accept_group_message()` instead of the upstream `_admit()` method.
The function hardcodes the @mention gate — it never checks any env var:

```python
def _should_accept_group_message(self, message, sender_id, chat_id=""):
    if not self._allow_group_message(sender_id, chat_id):
        return False
    # ... @mention checking ...
    return False  # ← hardcoded: no mention = rejected
```

`FEISHU_REQUIRE_MENTION` was defined in `~/.deepagent/.env` but no code
read it. The setting was silently ignored.

## Fix (4 locations)

Patched `/Volumes/Doc/Code/DeepAgent/gateway/platforms/feishu.py`:

1. **Settings dataclass** — added `require_mention: bool = True` field
2. **Settings parsing** — added `os.getenv("FEISHU_REQUIRE_MENTION", "true")` parse
   recognizing `false`, `0`, `no` as falsy
3. **Instance init** — mapped `settings.require_mention` to `self._require_mention`
4. **Gate function** — added `if not self._require_mention: return True` before
   the existing @mention check

## Restart

```bash
kill 30146    # launchd's KeepAlive auto-restarts with new code
```

## Verification

Gateway logs showed successful WebSocket reconnection.
