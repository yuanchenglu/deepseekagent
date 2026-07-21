# Cross-Project Per-Chat / Group Model Override Pattern

## Premise

When you implement per-chat or per-group model switching in one project's
Feishu bridge (e.g. Hermes `group_model_defaults`), **audit other Feishu
bridges for the same missing feature**. The pattern is: bridges usually
only support a single global model and have no mechanism for per-chat
overrides.

## Confirmed Projects

| Project | Feature | Implementation | PR |
|---------|---------|---------------|-----|
| **Hermes** (Python) | `group_model_defaults` — YAML map of `chat_id → model_name`, read at runtime by `_resolve_session_agent_runtime` | `gateway/config.py` + `gateway/run.py` | NousResearch/hermes-agent#32343 |
| **CodeWhale** (Node.js) | `/model <name>` command — stores per-chat model in thread store JSON file; `ensureThread()` / `runPrompt()` read it before falling back to bridge default | `integrations/feishu-bridge/src/index.mjs` + `lib.mjs` | Hmbown/CodeWhale#2149 |

## Diagnostic Checklist

To check if a Feishu bridge supports per-chat model switching:

1. **Find the model config source** — where is the default model read from?
   - One env var / config key → no per-chat support yet
   - Database or store per chat/group → may already support it

2. **Check the thread/turn creation API calls** — does the bridge pass the
   same model for every thread, or does it allow per-chat overrides?
   ```
   Thread creation body:  { model: config.model, ... }
   Turn submission body:  { model: config.model, ... }
   ```
   If always `config.model` → no per-chat support.

3. **Check command handlers** — is there a `/model` or equivalent command?
   - No `/model` command → feature missing
   - `/model` exists → may already support it

## Architecture Comparison

```
Hermes (Python gateway):
  Global default (model.default in config.yaml)
    ↓ fallback
  Group default (group_model_defaults[chat_id] in config.yaml)
    ↓ fallback
  Per-session (/model in a specific topic)

CodeWhale (Node.js bridge):
  Global default (DEEPSEEK_MODEL env / default_text_model in config.toml)
    ↓ fallback
  Per-chat (/model command stored in thread store JSON)
```

**Key difference**: CodeWhale maps 1 Feishu chat → 1 runtime thread, so
"per-chat" covers both "per-group" and "per-session" in the Hermes sense.

## Implementation Notes for Porting

### Hermes approach (for Python gateways)
- Add a `group_model_defaults: Dict[str, str]` field to the config model
- Read it at startup from YAML config
- In the model resolution function, check `group_model_defaults.get(chat_id)`
  after resolving global default but before checking per-session overrides

### CodeWhale approach (for Node.js bridges)
- Store per-chat model in a JSON thread store (persisted to disk)
- Add `/model <name>` command handler
- Modify thread creation and turn submission to read per-chat model override
- `/model default` or no-arg resets to bridge-level default

### Generic pattern (any language)
```
resolve_effective_model(chat_id, session_override=None):
  1. Start with global default
  2. If chat_id has a per-chat/group override, use that
  3. If session_override is set (/model), use that
  4. Return the result
```
