# Reasoning Effort Compatibility — Volcengine Agent Plan

> Tested 2026-07-17 against `https://ark.cn-beijing.volces.com/api/plan/v3` with `ark-code-latest` model.

## Compatibility Matrix

| `reasoning_effort` | Volcengine (Agent Plan) | DeepSeek (opencode-go) | Kimi (kimi-coding) |
|---|---|---|---|
| `none` (omitted) | ✅ 200 — default deep thinking | ✅ 200 | ✅ 200 |
| `low` | ✅ 200 | ✅ 200 | ✅ 200 |
| `medium` | ✅ 200 | ✅ 200 | ✅ 200 |
| `high` | ✅ 200 | ✅ 200 | ✅ 200 |
| **`xhigh`** (Hermes custom) | **❌ 400** `Invalid reasoning_effort: xhigh` | ✅ 200 | ✅ 200 |

## Root Cause

Volcengine Agent Plan implements the standard OpenAI `reasoning_effort` parameter with the standard values `low | medium | high`. Hermes Agent adds a custom `xhigh` (extra high) value that is **not** part of the OpenAI spec. While DeepSeek and Kimi providers accept `xhigh`, volcengine rejects it with HTTP 400.

## Runtime Failure Pattern

1. Hermes config has `agent.reasoning_effort: xhigh` (global)
2. Hermes sends `"reasoning_effort": "xhigh"` in the API request body
3. Volcengine returns `HTTP 400: Invalid reasoning_effort: xhigh`
4. Hermes retries 3 times → all fail → `"The model provider failed after retries"`

## The Deeper Insight: Volcengine Defaults to Deep Thinking

**Important**: Even without any `reasoning_effort` parameter, the volcengine Agent Plan API **always returns `reasoning_content`** in the response. Deep thinking is the default behavior, not optional. This means:

- Setting `reasoning_effort: high` (or `low`/`medium`) gives the same deep thinking as `xhigh` would
- The only difference across levels is **token budget** for thinking, not whether thinking happens at all
- Dropping from `xhigh` → `high` loses no reasoning capability; the model still outputs `reasoning_content`

## Test Script

```python
import urllib.request, json

url = "https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions"
headers = {
    "Authorization": "Bearer $API_KEY",
    "Content-Type": "application/json"
}

for level in [None, "low", "medium", "high", "xhigh"]:
    body = {"model": "ark-code-latest", "messages": [{"role": "user", "content": "OK"}], "max_tokens": 10}
    if level:
        body["reasoning_effort"] = level

    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode())
            reasoning = "reasoning_content" in r["choices"][0]["message"]
            print(f"{level or 'none'}: 200 reasoning={reasoning}")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode())
        print(f"{level}: {e.code} {err.get('error', {}).get('message', '')}")
```

## Fixes

| Approach | Change | Effect | Complexity |
|---|---|---|---|
| **Global downgrade** (simplest) | `reasoning_effort: xhigh` → `high` | All providers work. Volcengine still does deep thinking. | 1 line |
| **Upgrade to git main** (PR #64458) | `pipx install git+https://github.com/NousResearch/hermes-agent.git` | Hermes auto-suppresses `reasoning_effort` for volcengine; sends only to supporting providers | Full upgrade |
| **Per-model override** (PR #64458+) | Add `reasoning_overrides` in config | xhigh for DeepSeek/Kimi, blank for volcengine | git main required |

## Notes

- The `xhigh` rejection is **parameter-level**, not model-level — any model routed through `/api/plan/v3` has the same constraint, regardless of model name (`ark-code-latest` vs `doubao-seed-evolving`)
- The Anthropic-compatible endpoint (`/api/plan/v1/messages`) does NOT have a `reasoning_effort` parameter — it controls reasoning through the `thinking` block type
- v0.18.2 Hermes sends `reasoning_effort` to **all** providers. Git main (PR #64458) selectively skips it for providers that don't support reasoning parameters
