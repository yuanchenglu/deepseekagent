# Feishu Group Message Admission — Debugging Workflow

When a Hermes Feishu bot responds in DMs but silently ignores group messages,
the root cause is always in the **admission layer** (`_admit()` in `feishu.py`).
This reference covers the systematic debugging workflow.

---

## The Admission Pipeline (line 3946-3983 in feishu.py)

```python
def _admit(self, sender, message):
    is_group = getattr(message, "chat_type", "p2p") != "p2p"

    # (1) Self-echo check — skip
    # (2) Bot sender check — skip

    # (3) DM shortcut: DMs ALWAYS admitted
    if not is_group:
        return None

    # (4) Group policy check
    if not self._allow_group_message(sender_id, chat_id, is_bot):
        return "group_policy_rejected"

    # (5) Open/proactive OR require_mention=False → admitted
    if not require_mention or self._get_effective_policy(chat_id) in ("open", "proactive"):
        return None

    # (6) Only here: require_mention=True AND NOT open → need @mention
    if not self._mentions_self(message):
        return "group_policy_rejected"
    return None
```

**Key insight**: Line (5) means `FEISHU_GROUP_POLICY=open` ALWAYS admits messages
regardless of `require_mention` setting. The `require_mention` configs in
`config.yaml` (like `slack.require_mention`, `discord.require_mention`) do NOT
affect Feishu — Feishu uses `FEISHU_REQUIRE_MENTION` env var (defaults to `true`).

---

## Debugging Step 1: Check env vars in the running process

The most common failure mode: systemd services don't load `.env` files.

```bash
PID=$(pgrep -f "hermes_cli.main --profile yunying" | head -1)
cat /proc/$PID/environ | tr '\0' '\n' | grep FEISHU_GROUP_POLICY
# Expected: FEISHU_GROUP_POLICY=open
# If empty → env var NOT loaded → group policy defaults to "allowlist"
```

**Fix**: Add `Environment="FEISHU_GROUP_POLICY=open"` to the systemd service file,
then `systemctl --user daemon-reload && systemctl --user restart <service>`.

---

## Debugging Step 2: Check Feishu App API permissions

Even with correct Hermes config, Feishu won't push group message events to the
WebSocket if the app lacks the `im:chat` scope.

```python
# Verify via Feishu API
import requests
resp = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={"app_id": APP_ID, "app_secret": APP_SECRET})
token = resp.json()['tenant_access_token']

# Test group access
r = requests.get(f'https://open.feishu.cn/open-apis/im/v1/chats/{CHAT_ID}',
    headers={"Authorization": f"Bearer {token}"})
# code=0 → im:chat scope OK
# code=99991672 → missing im:chat/im:chat:readonly scope
```

**Required scopes for group message reception**:
- `im:message` — basic message
- `im:message.p2p_msg` — DM reception (this is why DMs work)
- `im:message.group_at_msg` — @mention in groups
- `im:chat` (or `im:chat:readonly`) — **required for ANY group message reception**

**Note**: Permissions in the Feishu developer console must be **published**
(create a new app version and submit for review) before they take effect.

---

## Debugging Step 3: Check WebSocket event subscription

After a fresh gateway restart (new WebSocket connection), verify the connection:

```bash
journalctl --user -u hermes-gateway-<name> --no-pager --since "1 min ago" \
  | grep -i "feishu.*connect\|lark.*connect"
# Expected: [Lark] connected to wss://msg-frontier.feishu.cn/ws/v2...
```

If group messages still don't arrive after all three checks pass, the Feishu
app's event subscription for `im.message.receive_v1` may not include group
events — check the app's event subscription page in the Feishu developer console.

---

## Quick diagnostic checklist

| Check | Command/Test | Expected |
|-------|-------------|----------|
| DM works? | Send DM to bot | ✅ Bot replies |
| Group message? | Send in group | ❌ No response |
| Env var in process | `/proc/<pid>/environ` | `FEISHU_GROUP_POLICY=open` |
| Chat API access | `GET /im/v1/chats/{id}` | code=0 |
| WebSocket connected | journalctl | `connected to wss://...` |

If rows 1-2 match (DM ✅, group ❌) and rows 3-5 all pass, the issue is likely
a Feishu-side event subscription problem — the `im:chat` scope was added but
not published, or the app version needs to be re-submitted.

---

## Common pitfalls

1. **`require_mention: false` in config.yaml doesn't affect Feishu**. Those entries
   are for Slack/Discord/Matrix/Mattermost only. Feishu uses `FEISHU_REQUIRE_MENTION`
   env var (defaults to `true`), but `FEISHU_GROUP_POLICY=open` overrides it anyway.

2. **`hermes gateway install` creates a systemd service without `.env` vars**.
   Each env var the adapter needs must be added as `Environment=KEY=VALUE` in
   the service file.

3. **Permission changes in the Feishu developer console require re-publishing**.
   Adding a scope in the console is not enough — create a new version and submit.

4. **The admission log is at DEBUG level**. `_admit()` rejection reasons (like
   `group_policy_rejected`) only appear in debug logs. Default log level is INFO.
   To see rejections: check if the bot is creating sessions at all (`hermes -p <name> sessions list`).
