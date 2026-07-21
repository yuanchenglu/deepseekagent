# Xiaomi MiMo "text is not set" 400 Error — OpenCode Go Fix

**Date**: 2026-06-18
**Commit (fork)**: `1f7c8ca6c` (fork only, never merged to upstream)
**Commit (main)**: `60f768fab` (re-applied to main on 2026-06-18)
**Branch**: `remotes/fork/fix/xiaomi-mimo-vision-tool-messages`

## Symptom

```
❌ Non-retryable error (HTTP 400): HTTP 400: Error from provider (Xiaomi): Param Incorrect
⚠️ Error code: 400 - {'error': {'code': '400', 'message': 'Error from provider (Xiaomi): Param Incorrect', 'param': 'text is not set', 'type': ''}}
```

Occurs when using `opencode-go` provider with Xiaomi MiMo models (mimo-v2.5, mimo-v2.5-pro) and tools return image content (browser screenshots, vision analysis).

## Root Cause

Xiaomi MiMo API accepts multimodal **user messages** but rejects list-type **tool message content** with `400 "text is not set"`. When tool results contain `image_url` parts (multipart content), they get sent as-is to the MiMo backend, which rejects them.

Two provider profiles need this flag, but only one had it:

| Profile | File | `supports_vision_tool_messages` | Status |
|---------|------|-------------------------------|--------|
| xiaomi (native) | `plugins/model-providers/xiaomi/__init__.py` | `False` ✅ | Correct |
| opencode-go (relay) | `plugins/model-providers/opencode-zen/__init__.py` | `True` ❌ (default) | **Missing** |

The `opencode-go` relay sits between Hermes and the MiMo backend, so even though the native xiaomi profile has the flag, the opencode-go profile's default of `True` bypasses the safeguard in `run_agent.py:_tool_result_content_for_active_model()`.

## Fix

Add to `OpenCodeGoProfile` in `plugins/model-providers/opencode-zen/__init__.py`:

```python
opencode_go = OpenCodeGoProfile(
    name="opencode-go",
    aliases=("opencode_go", "go", "opencode-go-sub"),
    env_vars=("OPENCODE_GO_API_KEY",),
    base_url="https://opencode.ai/zen/go/v1",
    default_aux_model="glm-5",
    supports_vision_tool_messages=False,  # Xiaomi MiMo rejects list-type tool content (400 "text is not set")
)
```

## How the Fix Was Lost (and Recovered)

1. Fix was committed on 2026-06-16 to fork branch `remotes/fork/fix/xiaomi-mimo-vision-tool-messages` (commit `1f7c8ca6c`)
2. The branch was never merged to `origin/main` (NousResearch/upstream)
3. After updating Hermes from upstream (`git fetch upstream --tags && git checkout <tag>`), the fix commit was no longer reachable
4. The `OpenCodeGoProfile` reverted to the default `supports_vision_tool_messages=True`
5. **Recovery**: On 2026-06-18, the fix was re-applied directly to `main` as commit `60f768fab`
6. After commit, Hermes gateway needed restart to pick up the new code (Python caches modules at startup)

## Diagnostic Commands

```bash
# Check if fix commit is on current branch
cd ~/.hermes/hermes-agent
git merge-base --is-ancestor 60f768fab HEAD && echo "ON branch" || echo "NOT on branch"
git merge-base --is-ancestor 1f7c8ca6c HEAD && echo "ON branch" || echo "NOT on branch"

# See which branches have the fix
git branch -a --contains 1f7c8ca6c
git branch -a --contains 60f768fab

# Verify the flag is set at runtime (must run from hermes-agent source dir)
cd ~/.hermes/hermes-agent && python3 -c "
from providers import get_provider_profile
for name in ['go', 'opencode-go', 'xiaomi']:
    p = get_provider_profile(name)
    print(f'{name}: supports_vision_tool_messages={getattr(p, \"supports_vision_tool_messages\", \"NOT SET\")}')
"

# Check whether running gateway has the fix (compare start time vs commit time)
ps aux | grep "hermes_cli.main gateway run" | grep -v grep  # note the start time
git log -1 --format="%ai" 60f768fab  # fix commit time
# If gateway start time > commit time → fix is loaded ✅
# If gateway start time < commit time → fix NOT loaded ⚠️ → restart gateway
```

## Code Path

The flag is checked in `run_agent.py`:

```
_tool_result_content_for_active_model()          # line 4535
  → _provider_supports_vision_tool_messages()    # line 4396
    → get_provider_profile(provider)             # looks up by agent's provider name
    → profile.supports_vision_tool_messages      # True → send images; False → text summary
```

When `False`, multimodal tool results are converted to plain text before sending to the API, avoiding the 400 error.

## Related

- ProviderProfile field docs: `providers/base.py` line 68-73
- Xiaomi native profile: `plugins/model-providers/xiaomi/__init__.py` (has `False` since inception)
- OpenCode Go profile: `plugins/model-providers/opencode-zen/__init__.py` (must be patched)
- Test coverage: `tests/run_agent/test_vision_tool_messages.py`
