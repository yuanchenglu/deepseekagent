# Per-Group Model Defaults for Hermes Gateway

## What Was Implemented

A simple flat `{chat_id: model_name}` map at the **top level** of
`config.yaml`.  This matches the three-tier resolution model:
`global default < group default < session /model override`.

### Config Format (Actual)

```yaml
# Top-level in config.yaml (not nested under platforms.feishu)
group_model_defaults:
  oc_869c1d931f317119d8f51f20797b599c: deepseek-v4-flash  # 课程设计部
  oc_53d22ce34646cebabf06e48ff986ee4c: deepseek-v4-flash  # 自媒体发文部Hermes
```

### Code Changes (Committed)

**`gateway/config.py`**:
- `group_model_defaults: Dict[str, str] = field(default_factory=dict)` on GatewayConfig
- `_normalize_group_model_defaults()` helper for YAML → dict coercion
- YAML pass-through in `load_gateway_config()`

**`gateway/run.py`**:
- In `_resolve_session_agent_runtime`: after `_resolve_gateway_model(user_config)` but
  before `self._session_model_overrides.get(...)`, check `group_model_defaults[chat_id]`

### Design Decision: Flat Dict vs Nested Object

Chose a flat `{chat_id: model_name}` (string-only values) over a nested
`{chat_id: {model, provider, api_key}}` object.  Rationale:

1. **Minimum viable change** — strings are simpler to validate, normalize,
   and log.  Adding provider/API-key overrides can follow in a separate PR.
2. **Model name is sufficient** for the vast majority of use cases (groups
   share the same provider config).
3. **Future extension** — the field type could change to `Dict[str, str |
   Dict[str, str]]` without breaking existing flat-format configs.

### PR

- Upstream: https://github.com/NousResearch/hermes-agent/pull/32343

### Chat ID Acquisition (Important Pitfall)

**Do NOT infer chat_id from `channel_directory.json` or session context.**
These may contain cached or stale IDs.

**Correct method**: ask the user to open Feishu group settings →
More Info → "Session ID" (format: `oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Session Key Structure

```
agent:main:feishu:group:<chat_id>:<thread_id>
```

Each thread gets its own session key. Model overrides are stored per
session key in `_session_model_overrides` (in-memory dict).

## Model Resolution Priority (After Patch)

1. **Session override** — `/model` command (highest priority)
2. **Group default** — `group_model_defaults[chat_id]` (new)
3. **Global config** — `model.default` in config.yaml (fallback)
4. **Provider default** — first catalog model of resolved provider

## Verification

1. Add a `group_model_defaults` entry in config.yaml
2. Restart gateway: `hermes gateway restart`
3. Create a **new thread** in the target group (existing threads have
   their own `/model` overrides if any were set)
4. Send a message — verify model changed
5. Check gateway logs for "Group model default" message

## Caveats

- Only affects **new threads** in the group — existing threads keep their
  current model
- Changing `group_model_defaults` in config.yaml requires gateway restart
- Only model name is configurable per group (not provider/API key)
- The feature is platform-agnostic (`source.chat_id` works for Telegram,
  Discord, etc.) but was tested primarily on Feishu
