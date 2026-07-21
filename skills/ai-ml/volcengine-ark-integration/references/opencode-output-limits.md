# OpenCode `limit.output` Configuration — Max Tokens

Session-verified knowledge about max_tokens limits across OpenCode providers.

## Model Output Limits

DeepSeek V4 Flash/Pro: **max output = 384,000 tokens** (384K). Confirmed by [DeepSeek API Docs](https://api-docs.deepseek.com/quick_start/pricing) (MAX OUTPUT MAXIMUM: 384K).

This is a **model-level constraint**, not provider-specific. All three providers enforce the same limit:

| Provider | Base URL | max_tokens上限 | 实测 |
|----------|----------|---------------|------|
| `opencode-go` | `https://opencode.ai/zen/go/v1` | 393,216 (384K) | 384K ✅ 400K ❌ |
| `coding-plan` | `https://ark.cn-beijing.volces.com/api/coding/v3` | 393,216 (384K) | 384K ✅ 400K ❌ |
| `agent-plan` | `https://ark.cn-beijing.volces.com/api/plan/v3` | 393,216 (384K) | 384K ✅ 400K ❌ |

## Context vs Output: Two Independent Constraints

Do NOT conflate the 1M context window with the 384K output limit:

1. **max_tokens ≤ 384K** — hard validation at request time. Exceeds → HTTP 400.
2. **prompt_tokens + actual_output_tokens ≤ 1M** — runtime cap, NOT checked at request time. Output is truncated at runtime, not rejected.

The relationship is NOT `input = 1M - max_tokens`. Setting `max_tokens=384K` is safe for all prompt lengths.

## The `limit.output` Field in opencode.json

In OpenCode's `~/.config/opencode/opencode.json`, each model can have a `limit` block:

```json
"deepseek-v4-flash": {
  "name": "DeepSeek V4 Flash",
  "reasoning": true,
  "limit": {
    "context": 1048576,
    "output": 384000
  }
}
```

- `limit.context` = context window (1M for DeepSeek V4)
- `limit.output` = max_tokens sent to API (384K for DeepSeek V4)

**Bug: OpenCode caps `limit.output` at 32K internally.** (GitHub issue [#29363](https://github.com/anomalyco/opencode/issues/29363), filed 2026-05-26, still open)

```js
// OpenCode source code
export const OUTPUT_TOKEN_MAX = 32_000;
return Math.min(model.limit.output, 32_000) || 32_000;
```

This means:
- No `limit` set → default 32K used
- `limit.output: 4096` → 4096 used (4096 < 32000, so `Math.min(4096, 32000) = 4096`)
- `limit.output: 384000` → 32K used (`Math.min(384000, 32000) = 32000`)

**Workaround**: Set environment variable to bypass the 32K cap:
```bash
export OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=384000
```

**For persistence across restarts (macOS launchd):**

OpenCode Web 通常由 launchd 服务 `com.opencode.server` 管理，自动重启。`.zshrc` 的 export 对 launchd 无效，必须在 plist 中配置：

1. 编辑 `~/Library/LaunchAgents/com.opencode.server.plist`，在 `EnvironmentVariables` 的 `<dict>` 中添加：
   ```xml
   <key>OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX</key>
   <string>384000</string>
   ```

2. 重启 launchd 服务：
   ```bash
   launchctl bootout gui/$(id -u)/com.opencode.server
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.opencode.server.plist
   ```

3. 验证：
   ```bash
   ps eww $(pgrep -f 'opencode web' | head -1) | tr ' ' '\n' | grep OUTPUT_TOKEN
   # 应显示: OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=384000
   ```

## Provider Naming Convention

The user's actual config uses short provider names, not the verbose `volcengine-*-plan` format:

| Config key | Provider name | Base URL |
|-----------|---------------|----------|
| `coding-plan` | Volcano Engine (Coding Plan) | `/api/coding/v3` |
| `agent-plan` | Volcano Engine (Agent Plan) | `/api/plan/v3` |
| `opencode-go` | OpenCode Go | `/zen/go/v1` |

The `model` field uses `provider/model-id` format: e.g. `coding-plan/ark-code-latest`, `opencode-go/deepseek-v4-flash`.

## What NOT to Do

- Do NOT set `limit.output: 4096` for DeepSeek V4 models — this wastes 99% of the model's output capability. The user explicitly rejected this.
- Do NOT use `model.max_tokens` to compute `input = 1M - max_tokens` — this is incorrect. The two constraints are independent.
- Do NOT assume `opencode-go` without `limit` defaults to a large value — it defaults to 32K, which is small but not harmful.