# Coding Plan Model Auto-Discovery

> Verified 2026-07-17 on MacBook Air with Volcengine Coding Plan subscription.

## The Problem

You configure `providers.volcengine-coding-plan.models` to only `ark-code-latest`, but `/model` still shows 126 models.

## Root Cause

Hermes calls `GET /api/coding/v3/models` at provider initialization. The Coding Plan API returns **all models available on the platform** (126 as of 2026-07-17):

```
doubao-lite-128k-240428, doubao-pro-128k-240515, doubao-lite-4k-240328,
doubao-lite-32k-240428, doubao-pro-4k-240515, doubao-lite-4k-character-240515,
doubao-embedding-text-240515, mistral-7b-instruct-v0.2,
...
deepseek-v4-flash-260425, deepseek-v4-pro-260425,
kimi-k2-250711, glm-4-5-air-20250728, qwen3-8b-20250429,
...
doubao-seed-evolving, glm-5-2-260617
```

Hermes **overrides** the configured `models:` list with the API-discovered models. The config's `models:` section becomes a no-op.

## Contrast with Agent Plan

| Provider | `GET /v3/models` | Behavior |
|----------|-----------------|----------|
| Agent Plan (`/api/plan/v3`) | **404 Not Found** | Respects configured `models:` list ✅ |
| Coding Plan (`/api/coding/v3`) | **126 models returned** | Ignores configured `models:` list ❌ |

## Why `ark-code-latest` Doesn't Help

`ark-code-latest` is **not in the Coding Plan API's model list**. It's an Agent Plan-only alias. The Coding Plan API only returns actual model IDs (e.g. `doubao-seed-2-0-code-preview-260215`). So even if you set `models: [- id: ark-code-latest]`, Hermes doesn't find it in the auto-discovered list and still shows all 126.

## The Fix

Remove `volcengine-coding-plan` from the `providers:` section. Keep the API key only in `custom_providers` for subagent delegation:

```yaml
# DON'T do this — it auto-discovers 126 models
# providers:
#   volcengine-coding-plan:
#     api_key: ...
#     models: ...   # ← Hermes ignores this

# DO this instead — keep coding plan in custom_providers only
custom_providers:
- api_key: "${VOLC_CODING_PLAN_KEY}"
  api_mode: chat_completions
  base_url: "https://ark.cn-beijing.volces.com/api/coding/v3"
  model: deepseek-v4-flash
  models:
    deepseek-v4-flash:
      context_length: 1000000
      name: deepseek-v4-flash
  name: arkcodingplan
- api_key: "${VOLC_CODING_PLAN_KEY}"
  api_mode: codex_responses
  base_url: "https://ark.cn-beijing.volces.com/api/coding/v3"
  model: deepseek-v4-flash
  models:
    deepseek-v4-flash:
      context_length: 1000000
      name: deepseek-v4-flash
  name: arkcodingplan-codex
```

The `custom_providers` entries don't auto-discover models — they respect the configured `models:` dict exactly.

## How to Verify

```bash
# Count models from API
curl -s "https://ark.cn-beijing.volces.com/api/coding/v3/models" \
  -H "Authorization: Bearer $CODING_PLAN_KEY" | python3 -c \
  "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"])} models')"

# Check if ark-code-latest is in the list
curl -s "https://ark.cn-beijing.volces.com/api/coding/v3/models" \
  -H "Authorization: Bearer $CODING_PLAN_KEY" | python3 -c \
  "import sys,json; ms=[m['id'] for m in json.load(sys.stdin)['data'] if 'ark-code' in m.get('id','')]; print(f'ark-code 匹配: {ms}')"
```
