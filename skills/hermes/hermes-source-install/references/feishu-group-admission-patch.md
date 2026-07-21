# Feishu Group Admission Patch

## Problem

After updating Hermes from v0.15.1 to v0.16.0 (git checkout), the CTO profile stopped responding to group chat messages on Feishu. Direct messages (private chat) still worked. This also affects any Hermes install with `FEISHU_GROUP_POLICY=open` that expects the bot to respond without @mention.

## Root Cause

This is an **upstream bug** in Hermes' Feishu adapter (`gateway/platforms/feishu.py`). The `_admit()` method checks `require_mention` against the global `require_mention` flag, but does NOT consider the group's effective policy. When `group_policy="open"` (meaning "any user in the group can interact with the bot"), the `require_mention` gate should not apply — but it does. The default `require_mention=True` combined with `_admit` ignoring the policy means open groups still silently drop non-@mentioned messages.

Additionally, if a Hermes install had **local uncommitted patches** on `main` branch that worked around this bug, `git checkout` of a new tag will stash them. If the stash is not restored, the upstream defaults (buggy behavior) take effect.

**Upstream PR submitted**: https://github.com/NousResearch/hermes-agent/pull/47916

## The Patch

### `gateway/platforms/feishu.py` — Group admission bypass

The default `_admit()` function returns `"group_policy_rejected"` when:
1. Group policy is `"allowlist"` (default) and the user is not in the allowlist, OR
2. `require_mention=True` (default) but the message doesn't `@mention` the bot

The local patch adds a `_get_effective_policy()` helper and a bypass: if the effective group policy is `"open"` or `"proactive"`, skip both the allowlist check AND the @mention requirement:

```python
# Diff context: in _admit() method, replace:
if require_mention and not self._mentions_self(message):
    return "group_policy_rejected"
return None

# With:
# Open/proactive mode: accept all messages from allowed users without @mention
if not require_mention or self._get_effective_policy(chat_id) in ("open", "proactive"):
    return None
if not self._mentions_self(message):
    return "group_policy_rejected"
return None
```

Also adds the helper method:

```python
def _get_effective_policy(self, chat_id: str) -> str:
    """Get the effective policy for a chat."""
    rule = self._group_rules.get(chat_id) if chat_id else None
    if rule:
        return rule.policy
    return self._default_group_policy or self._group_policy
```

And adds `resolve_channel_prompt` import and `channel_prompt` field to `MessageEvent` construction.

### `gateway/run.py` — Group model defaults

Adds per-chat model routing from `group_model_defaults` config:

```python
# In the model resolution block, after resolving the gateway model:
if source and source.chat_id:
    group_defaults = (user_config or {}).get("gateway", {}).get("group_model_defaults", {})
    if isinstance(group_defaults, dict):
        group_model = group_defaults.get(source.chat_id)
        if group_model:
            model = group_model
```

## How to Verify the Patch Is Active

```bash
cd ~/.hermes/hermes-agent

# Check if patches are present
git diff -- gateway/platforms/feishu.py

# Expected: _get_effective_policy method, modified _admit, channel_prompt
git diff -- gateway/run.py

# Expected: group_model_defaults resolution block
```

## How to Reapply if Lost Again

**IMPORTANT**: If the same bug affects multiple machines running Hermes, patch each one independently. After patching, the gateway MUST be restarted — even if it has been running for hours. Old code is cached in the running process.

```bash
cd ~/.hermes/hermes-agent

# Check stash
git stash list

# Restore
git stash pop  # or git stash pop stash@{N}

# If no stash but changes are committed on the old branch:
git log --all --oneline | grep -i "patch\\|feishu\\|group"
git cherry-pick <commit-hash>

# If neither, the patches need to be manually recreated
# Copy the content from this reference file

# After code change: RESTART the gateway (MANDATORY)
systemctl --user restart hermes-gateway.service
systemctl --user restart hermes-gateway-cto.service     # if exists
systemctl --user restart hermes-gateway-*.service       # all profiles
```

## Stale Home Channel Cleanup

Old `FEISHU_HOME_CHANNEL` entries in `config.yaml` may refer to stale chat IDs. If the user wants to re-set them via Feishu's `/sethome`:

```bash
# Find all home channel entries across profiles
grep -rn "HOME_CHANNEL" ~/.hermes/profiles/ ~/.hermes/config.yaml 2>/dev/null

# Remove the stale line (example):
sed -i '/^FEISHU_HOME_CHANNEL:/d' ~/.hermes/config.yaml
```
