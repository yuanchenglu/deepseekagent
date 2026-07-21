---
name: volcengine-ark-integration
description: Configure and integrate Volcengine Ark (火山方舟) Coding Plan and Agent Plan with AI coding tools (OpenCode, Hermes, Claude Code). Covers base URLs, API key management, provider config, and common pitfalls.
---

# 火山方舟 Ark Integration — OpenCode & AI Tools

Configure Volcengine Ark subscription plans (Agent Plan / Coding Plan) with AI coding tools.

> ⚠️ **IMPORTANT**: Agent Plan and Coding Plan are **two separate providers** with different base URLs and different API keys. Never share config between them.

---

## Quick Reference

| Dimension | Agent Plan (多模态) | Coding Plan (纯编码) |
|-----------|-------------------|-------------------|
| **Base URL (OpenAI)** | `https://ark.cn-beijing.volces.com/api/plan/v3` | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| **Base URL (Anthropic)** | `https://ark.cn-beijing.volces.com/api/plan` | N/A |
| **API Key** | From Agent Plan console | From Coding Plan console |
| **SDK** | `@ai-sdk/openai` (Responses API, 推荐) | `@ai-sdk/openai` (Responses API, 推荐) |
| **备用 SDK** | `@ai-sdk/openai-compatible` (Chat API) | `@ai-sdk/openai-compatible` (Chat API) |
| **Model ref** | `volcengine-agent-plan/code-latest` | `volcengine-coding-plan/code-latest` |

---

## Dual Protocol Support (Agent Plan)

Volcengine Agent Plan supports **two protocol endpoints** under the same API key:

| Protocol | Endpoint | Response Format | Use Case |
|----------|----------|----------------|----------|
| **OpenAI-compatible** (Responses API) | `https://ark.cn-beijing.volces.com/api/plan/v3` | Chat completion w/ `reasoning_content` | Hermes, OpenCode, standard AI tools |
| **Anthropic-compatible** (Messages API) | `https://ark.cn-beijing.volces.com/api/plan/v1/messages` | Anthropic-style w/ `thinking` field | Claude Code, Anthropic-protocol tools |

Both endpoints accept the same `ark-code-latest` model name. The backend resolves it to the actual model (e.g. `doubao-seed-evolving`).

Coding Plan does **not** have an Anthropic-compatible endpoint — only Agent Plan offers dual protocol.

---

## Installing Ark CLI (可选)

```bash
npm install -g @volcengine/ark-cli@latest
# 如果 npm 全局 bin 不在 PATH 中:
ln -sf $(npm root -g)/@volcengine/ark-cli/scripts/run.js ~/.local/bin/arkcli
arkcli --version
```

---

## OpenCode Configuration

### 1. Edit `~/.config/opencode/opencode.json`

Add under the `"provider"` section:

```json
"volcengine-agent-plan": {
  "npm": "@ai-sdk/openai",
  "name": "火山方舟 Agent Plan",
  "options": {
    "baseURL": "https://ark.cn-beijing.volces.com/api/plan/v3",
    "apiKey": "{env:VOLC_AGENT_PLAN_KEY}"
  },
  "models": {
    "code-latest": {
      "name": "Agent Plan Code Latest"
    }
  }
},
"volcengine-coding-plan": {
  "npm": "@ai-sdk/openai",
  "name": "火山方舟 Coding Plan",
  "options": {
    "baseURL": "https://ark.cn-beijing.volces.com/api/coding/v3",
    "apiKey": "{env:VOLC_CODING_PLAN_KEY}"
  },
  "models": {
    "code-latest": {
      "name": "Coding Plan Code Latest"
    }
  }
}
```

### 2. Add API Keys to `~/.config/opencode/.env`

```
# 火山方舟 Agent Plan
VOLC_AGENT_PLAN_KEY=your_agent_plan_key_here

# 火山方舟 Coding Plan
VOLC_CODING_PLAN_KEY=your_coding_plan_key_here
```

### 3. Verify

Run `opencode`, then `/models` — should show both providers with their `code-latest` model.

---

## ark-code-latest Model

- A **dynamic model name** — resolves to whatever model you configure in the Volcengine console
- Switch models in the Ark console (3–5 min生效), **no config file changes needed**
- Always use `code-latest` / `ark-code-latest` instead of pinning a specific model version
- The model naming convention is `{provider-id}/{model-id}`: e.g. `volcengine-agent-plan/code-latest`

---

## Verification Pattern

After configuring an Agent Plan provider, always verify both endpoints independently, and test `reasoning_effort` compatibility:

### OpenAI-compatible endpoint

```bash
curl -s -w "\\nHTTP_CODE:%{http_code}" -X POST \
  "https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"ark-code-latest","messages":[{"role":"user","content":"OK"}],"max_tokens":10}'
```

Expected: `HTTP 200`, response contains `content` + `reasoning_content` fields.

### Anthropic-compatible endpoint

```bash
curl -s -w "\\nHTTP_CODE:%{http_code}" -X POST \
  "https://ark.cn-beijing.volces.com/api/plan/v1/messages" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"ark-code-latest","max_tokens":20,"messages":[{"role":"user","content":"OK"}]}'
```

Expected: `HTTP 200`, response contains `thinking` + `text` blocks in Anthropic format.

### Reasoning Effort Compatibility Test

Test each level to confirm volcengine accepts it:

```bash
for level in low medium high; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"ark-code-latest\",\"messages\":[{\"role\":\"user\",\"content\":\"OK\"}],\"reasoning_effort\":\"$level\",\"max_tokens\":10}")
  echo "reasoning_effort=$level: $code"
done
# Also test the problematic xhigh (expected: 400)
code=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"ark-code-latest","messages":[{"role":"user","content":"OK"}],"reasoning_effort":"xhigh","max_tokens":10}')
echo "reasoning_effort=xhigh: $code (expected 400)"
```

> Both endpoints use the **same API key** and `ark-code-latest` model name. The backend resolves `ark-code-latest` to the actual model (e.g. `doubao-seed-evolving`).

---

## Model Output Limits (`limit.output`)

**Critical**: DeepSeek V4 models have a max output of **384K tokens**, NOT 1M. The 1M is the context window (input). Setting `limit.output` to 4096 wastes 99% of the model's output capability.

For detailed limits across all three providers (coding-plan, agent-plan, opencode-go), the 32K OpenCode cap bug, and the `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` workaround, see `references/opencode-output-limits.md`.

---

## Pitfalls (learned the hard way)

1. **NEVER use a shared env var** for both plans — each plan has its own API Key
2. **NEVER use `/api/v3`** — that's the pay-per-token standard API endpoint, not the subscription endpoint. `/api/plan/v3` and `/api/coding/v3` are subscription-based
3. **SDK package matters**: `@ai-sdk/openai` for Responses API (recommended, better reasoning), `@ai-sdk/openai-compatible` for Chat API (fallback)
4. **Responses API is recommended** by Volcengine for better inference quality
5. **arkcli after npm install**: global npm binary may not be in PATH on Homebrew Node installs. Create a symlink in `~/.local/bin/`
6. **Agent Plan has two endpoints, not one**: The same API key supports both `/api/plan/v3` (OpenAI-compatible) and `/api/plan` (Anthropic-compatible). Configure both when setting up tools that speak different protocols (Claude Code vs standard AI tools)
7. **`reasoning_effort: xhigh` is NOT supported by volcengine**: The volcengine API only accepts standard OpenAI values (`low`, `medium`, `high`). Hermes' custom `xhigh` value causes **HTTP 400 `Invalid reasoning_effort: xhigh`**. This is the most common silent failure when switching from DeepSeek/Kimi providers (which accept xhigh) to volcengine. Workarounds:
   - **Change global `reasoning_effort` to `high`** — simplest fix, volcengine supports it, and the API already defaults to deep thinking (returns `reasoning_content` in every response). See `references/reasoning-effort-compatibility.md`.
   - **Upgrade Hermes to git main (PR #64458+)** — auto-suppresses `reasoning_effort` for volcengine; only sends it to providers that support it (Kimi, Tencent, LM Studio).
   - **Add `reasoning_overrides`** (requires git main PR #64458) for per-model control.

8. **`ark-code-latest` > pinned model names**: Always use `ark-code-latest` as the default model in Hermes config. Pinning a specific model like `doubao-seed-evolving` breaks when the backend model is updated/rotated.

9. **Keep provider model lists lean**: Only keep the models you actually switch between. Every extra model in `providers.<name>.models[]` pollutes Hermes' model catalog and adds noise to tool output. The Volcengine console is where you switch backend models — Hermes doesn't need all of them listed. A clean config has exactly one entry per provider (`ark-code-latest`) unless you explicitly need Hermes to offer multiple options for on-the-fly switching.

10. **Coding Plan auto-discovers 126 models — you can't stop it**: Even if you set `providers.volcengine-coding-plan.models` to only `ark-code-latest`, Hermes queries `GET /api/coding/v3/models` on startup and the API returns **126 real model names** (doubao variants, glm, kimi, minimax, deepseek, etc.). Hermes displays ALL of them in `/model` regardless of the config. By contrast, Agent Plan's `/api/plan/v3/models` endpoint returns 404, so Hermes respects the configured `models:` list. Fix: if the model list bloat is unacceptable, **delete `volcengine-coding-plan` from the `providers:` section entirely** and keep the Coding Plan API key only in `custom_providers` (for subagent delegation via `arkcodingplan` / `arkcodingplan-codex`). See `references/coding-plan-model-discovery.md`.

---

## Hermes Agent Configuration

```yaml
# ~/.hermes/config.yaml
model:
  default: ark-code-latest
  provider: volcengine-agent-plan

providers:
  volcengine-agent-plan:
    base_url: "https://ark.cn-beijing.volces.com/api/plan/v3"
    api_key: "${VOLC_AGENT_PLAN_KEY}"
    model: "ark-code-latest"
    models:
    - id: ark-code-latest          # ⚡ 只留这一个就够了
    name: Volcengine Agent Plan
  # volcengine-coding-plan is NOT listed here intentionally.
  # Its API auto-discovers 126 models that can't be suppressed.
  # Keep its API key only in custom_providers for subagent delegation.
```

> ⚠️ **Keep model lists lean.** Only list `ark-code-latest` in each provider's `models:` section. Adding every model the API supports (doubao variants, glm, kimi, minimax, deepseek pinned versions) bloats Hermes' model catalog and serves no purpose — model switching happens in the Volcengine console, not in Hermes config. Add a new model to the list ONLY when you need Hermes to switch to it on-the-fly via `model.default`.
>
> ⚠️ **Coding Plan auto-discovers 126 models** — even if you set `providers.volcengine-coding-plan.models` to only `ark-code-latest`, the API returns all 126 real model names. If this clutter is unacceptable, remove coding plan from `providers` entirely and keep it only in `custom_providers`. See pitfall #10.
>
> ⚠️ Always use `ark-code-latest` as the default model, not a pinned model name. The backend resolves it to the current active model. Also ensure `reasoning_effort` in Hermes config uses only standard values (`low`/`medium`/`high`) — volcengine does NOT support Hermes' custom `xhigh` value. See pitfall #7 and `references/reasoning-effort-compatibility.md`.
