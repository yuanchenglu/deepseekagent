# Session-Verified Configuration (2026-07-17)

Verified in a real session with user `bluth`. These values are confirmed working.

## OpenCode Verified Config

**Agent Plan (Access AI Tool → OpenCode, doc ID 2373741)**
- baseURL (OpenAI): `https://ark.cn-beijing.volces.com/api/plan/v3`
- baseURL (Anthropic): `https://ark.cn-beijing.volces.com/api/plan`
- Provider ID: `volcengine-agent-plan`
- Model ref: `volcengine-agent-plan/code-latest`

**Coding Plan (Access AI Tool → OpenCode, doc ID 2188958)**
- baseURL: `https://ark.cn-beijing.volces.com/api/coding/v3`
- Provider ID: `volcengine-coding-plan`
- Model ref: `volcengine-coding-plan/code-latest`

**Shared settings**
- npm package: `@ai-sdk/openai` (Responses API, recommended)
- Fallback: `@ai-sdk/openai-compatible` (Chat API)
- API key via env var in `~/.config/opencode/.env`
- Env var names: `VOLC_AGENT_PLAN_KEY` and `VOLC_CODING_PLAN_KEY`
- Default model: `ark-code-latest` (NOT a pinned model name)

## Hermes Agent Verified Config (MacBook Air 2026-07-17)

After cleanup — only `ark-code-latest` kept, `volcengine-coding-plan` removed from `providers`:

```yaml
model:
  default: ark-code-latest
  provider: volcengine-agent-plan

providers:
  volcengine-agent-plan:
    api_key: ark-88d4162a-929d-4b4c-aa12-70a6ea542d3e-8bf2e
    base_url: https://ark.cn-beijing.volces.com/api/plan/v3
    model: ark-code-latest
    models:
    - id: ark-code-latest
    name: Volcengine Agent Plan
```

## Dual-Endpoint Verification Test Results

Both endpoints tested successfully with the same API key and `ark-code-latest` model:

### OpenAI-compatible (`/api/plan/v3/chat/completions`)
```json
{
  "choices": [{
    "message": {
      "content": "ok",
      "reasoning_content": "接下来我将直接回复ok。\n",
      "role": "assistant"
    }
  }],
  "model": "doubao-seed-evolving"
}
```
✅ 200 OK — Contains `content` + `reasoning_content`

### Anthropic-compatible (`/api/plan/v1/messages`)
```json
{
  "id": "...",
  "type": "message",
  "role": "assistant",
  "model": "doubao-seed-evolving",
  "content": [
    {"type": "thinking", "thinking": "直接回复ok。"},
    {"type": "text", "text": "ok"}
  ]
}
```
✅ 200 OK — Anthropic-style response with `thinking` + `text` blocks

**Key observation**: `ark-code-latest` resolves to `doubao-seed-evolving` on the backend. The model name in the response is always the actual backend model, not `ark-code-latest`.

## Pitfalls Encountered

1. **baseURL confusion**: Initial config used `/api/coding/v3` for both plans. Correct: Agent Plan = `/api/plan/v3`
2. **Shared API key**: Initially used `{env:VOLC_API_KEY}` for both. Each plan has its own key.
3. **The `/api/v3` trap**: Standard API endpoint incurs pay-per-token charges. Must use plan-specific endpoints for subscription billing.
4. **arkcli not in PATH**: Homebrew Node installs global npm packages to Cellar directory. Symlink to `~/.local/bin/` resolves this.
5. **Dual protocol not documented**: Agent Plan supports both OpenAI and Anthropic protocols. The `/api/plan` (Anthropic) endpoint is easy to miss because most docs only mention `/api/plan/v3`.
6. **`reasoning_effort: xhigh` breaks volcengine (NOT model name issue)**: The commonly cited explanation that "pinned model names cause reasoning_effort incompatibility" is **misleading**. The real root cause is the Hermes custom value `xhigh` — volcengine only accepts standard `low/medium/high`. This happens regardless of model name (`ark-code-latest` or `doubao-seed-evolving`). `ark-code-latest` just happens to be used alongside the fix (downgrading to `high`), but the model name itself has nothing to do with the parameter validation. See `references/reasoning-effort-compatibility.md` for detailed test results.
