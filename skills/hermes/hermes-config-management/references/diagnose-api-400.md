# Diagnosing HTTP 400 from OpenCode Go / Custom API Providers

When Hermes returns `HTTP 400: Error from provider (Console Go): Upstream request failed` with no useful error detail, follow this chain.

## Quick Check: Is it max_tokens?

Run the built-in script:

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
python3 scripts/diagnose-max-tokens.py \
  https://opencode.ai/zen/go/v1 \
  "$OPENCODE_GO_API_KEY" \
  deepseek-v4-flash
```

If the script reports `max_tokens=1048576: ❌ HTTP 400` and smaller values pass, the fix is:

```bash
# For DeepSeek V4 (max output = 384K):
sed -i '' 's/max_tokens: [0-9]*/max_tokens: 384000/' ~/.hermes/config.yaml
```

## Known Limits (opencode.ai/zen/go/v1)

| Model | Context Window | Max Output Limit | Max Accepted max_tokens |
|-------|---------------|-----------------|------------------------|
| deepseek-v4-flash | 1,000,000 | 384,000 | 393,216 |
| deepseek-v4-pro | 1,000,000 | 384,000 | 393,216 |

**Source**: DeepSeek [official API docs](https://api-docs.deepseek.com/quick_start/pricing) — "MAX OUTPUT MAXIMUM: 384K" for both V4 models.

The 393,216 limit is **not** 3× context window. It is the model's **max output cap** (384K) plus a small margin. DeepSeek V4's context window is 1M, not 128K. A value of 1,048,576 (1M) is the Hermes default and will be rejected.

## Two Constraints (Not One)

Two independent constraints govern API requests:

```
Constraint 1: max_tokens ≤ model_max_output (384K for DeepSeek V4)
Constraint 2: prompt_tokens + actual_output_tokens ≤ context_length (1M)
```

- **Constraint 1** is a **hard validation** at request time. Set `max_tokens > 384K` → immediate HTTP 400.
- **Constraint 2** is a **runtime cap**. The API does NOT check `prompt_tokens + max_tokens ≤ 1M` at request time. Instead, it generates output until the context window is full, then stops. So setting `max_tokens=384K` with a 900K prompt will NOT return a 400 — it will just generate at most 100K tokens before hitting the 1M wall.

**The relationship is NOT `input = 1M - max_tokens`.** The actual input limit depends on how much output the model generates, not on the `max_tokens` parameter. Setting `max_tokens=384K` is safe for all prompt lengths — the API simply truncates output when the total exceeds 1M.

## Optimal Configuration

For DeepSeek V4 on opencode.ai, the optimal `max_tokens` is **384,000** (384K):

```yaml
model:
  default: deepseek-v4-flash
  provider: opencode-go
  max_tokens: 384000
```

This gives:
- **Maximum output**: 384K tokens per response (the model's limit)
- **No risk of 400 errors**: 384K ≤ 384K ✅
- **Safe for long prompts**: The API will respect the 1M context window at runtime, truncating output if needed rather than rejecting the request

Do NOT use conservative values like 32K or 128K for DeepSeek V4 — the user explicitly prefers maximum input and output capability.

## Full Diagnostic Chain

### Step 1: Direct curl test (bypass Hermes)

```bash
# Extract key from .env
KEY=$(grep OPENCODE_GO_API_KEY ~/.hermes/.env | cut -d= -f2-)

curl -s -w "\nHTTP_CODE:%{http_code}" \
  https://opencode.ai/zen/go/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"OK"}],"max_tokens":10}'
```

Expected success: HTTP 200 with content in response.
Expected failure: HTTP 401 → bad key; HTTP 400 → upstream rejects parameters.

### Step 2: If curl works, test with Hermes config values

Create a Python script that tests the worst-case config values (the ones Hermes sends):

```python
import httpx, os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.hermes/.env"))

resp = httpx.post(
    "https://opencode.ai/zen/go/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.environ['OPENCODE_GO_API_KEY']}"},
    json={
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "OK"}],
        "max_tokens": 1048576,  # <-- Hermes default, often too large
        "stream": False,
    },
    timeout=10,
)
print(resp.status_code, resp.text[:200])
```

### Step 3: Binary search the parameter

If `max_tokens=1048576` fails, binary-search down to find the limit:

```python
for mt in [1024, 32768, 131072, 262144, 384000, 393216, 524288, 1048576]:
    resp = httpx.post(url, json={**base, "max_tokens": mt}, ...)
    print(f"max_tokens={mt}: {resp.status_code}")
```

### Step 4: Fix and verify

1. Set `max_tokens: 384000` in `~/.hermes/config.yaml` (for DeepSeek V4 models)
2. Optionally: `hermes config migrate` to update config version
3. Run `hermes chat -q 'Hello'` to verify end-to-end

## Config Migration

After fixing the immediate issue, also run config migration to catch other stale settings:

```bash
hermes config migrate
```

This updates the `_config_version` field and adds any new defaults that may have been introduced since the config was created.

## Common Confusion: Empty `providers` Section

When you see `providers: {}` in config.yaml, this is **normal** if you're using a built-in provider (opencode-go, kimi-coding, deepseek, volcengine-coding-plan, etc.). Built-in provider definitions are hardcoded into Hermes and don't appear in the config.

Only custom/named providers (`custom:xxx`) need entries in the `providers` or `custom_providers` section. Do not add a built-in provider name to the `providers` dict — it will be ignored.