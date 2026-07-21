# Client-Side Token Validity Check

**Scenario**: You have only the customer's API key (`sk-xxx`) — no admin/database access. You need to check if the token is still valid, how much quota remains, or why API calls fail.

## Diagnostic Workflow

### Step 1: Check key format → `GET /v1/models`

```bash
curl -s 'https://token.clawadmin.org/v1/models' \
  -H 'Authorization: Bearer sk-MuH...xOrM'
```

**Expected on a live key**: Returns `{"data":[...],"object":"list","success":true}` with model list.

**If this fails**:
- HTTP 401 `Invalid token`: New API has rejected the key format — it may be truncated, wrong, or the token was deleted.
- HTTP 403 `error code: 1010`: Cloudflare WAF is blocking — try changing User-Agent or IP.

### Step 2: Test actual API call → `POST /v1/chat/completions`

```bash
curl -s -X POST 'https://token.clawadmin.org/v1/chat/completions' \
  -H 'Authorization: Bearer sk-MuH...xOrM' \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'
```

**Expected on a healthy key**: Returns a valid completion JSON with `usage` field.

**Key error patterns**:

| Response | Meaning | Root Cause |
|----------|---------|------------|
| `401 Invalid token` from New API | Token exhausted or disabled | `remain_quota <= 0 AND unlimited_quota = 0`, or `status = 2` |
| `403 error code: 1010` | Cloudflare WAF | Blocked POST (try Anthropic format or different IP) |
| `402 Payment Required` | Billing issue | Self-use mode off, ModelRatio not configured |
| `429 Too Many Requests` | Rate limited | Too many requests per minute |

## The Key Insight: Models vs Completion

**Models endpoint succeeds but Chat Completions returns "Invalid token"** — this is the definitive sign of an exhausted quota. The models endpoint only checks key format/validity; the completion endpoint checks `remain_quota > 0`.

## Publicly Accessible Endpoints

The `/api/status` endpoint is **public** on most New API instances (no auth needed):

```bash
curl -s 'https://token.clawadmin.org/api/status'
```

Useful fields in the response:

| Field | What it tells you |
|-------|-------------------|
| `self_use_mode_enabled` | If `true`, billing checks are bypassed — all tokens are free |
| `quota_display_type` | `"USD"` or `"CNY"` display currency |
| `quota_per_unit` | Token per unit for currency display |
| `price` | Price per unit |
| `register_enabled` | Whether self-registration is open |
| `password_login_enabled` | Whether password login is available |
| `demo_site_enabled` | Demo mode indicator |
| `version` | New API version (e.g. `"v1.0.0-rc.10"`) |

## Anthropic Format as Fallback

Some New API instances block OpenAI-format POST but accept Anthropic format:

```bash
curl -s -X POST 'https://token.clawadmin.org/v1/messages' \
  -H 'x-api-key: sk-MuH...xOrM' \
  -H 'anthropic-version: 2023-06-01' \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4-flash","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'
```

If Anthropic format returns 403 Cloudflare but OpenAI returns 401 New API, the token is still the problem (New API rejected it). The Anthropic path may fail at the WAF layer even when the token itself is the issue.

## Common Misdiagnosis

### Cloudflare Error 1010 ≠ Token Invalid

Don't confuse Cloudflare WAF blocks with token problems:

```
# Cloudflare WAF (look for CF-RAY header in response)
{"error code: 1010"}  ← WAF rule triggered

# New API token error (New API's own JSON response)
{"error":{"code":"","message":"Invalid token...","type":"new_api_error"}}  ← quota exhausted
```

They can appear together: the same token might trigger both Cloudflare WAF (on Anthropic endpoint) and New API's own rejection (on OpenAI endpoint) — the latter is the real diagnosis.

### "Was Working Before" ≠ Still Working

A token that worked yesterday can exhaust its quota silently. The models endpoint may still appear to accept the key while completions fail. Always test both endpoints.

## Quota Recovery (Requires Admin Access)

If you confirm the token is exhausted and you have admin/database access:

```bash
# Check current state
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, remain_quota, unlimited_quota, status FROM tokens WHERE key='<48-char-key>';"

# Replenish quota (e.g., add 10亿)
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE tokens SET remain_quota = 1000000000 WHERE key='<48-char-key>';"

# Must restart container
sudo docker restart new-api
```

**Note**: The database stores the raw 48-char key WITHOUT `sk-` prefix. Strip `sk-` before querying.
