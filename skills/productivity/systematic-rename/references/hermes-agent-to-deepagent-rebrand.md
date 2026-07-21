### 5. Module Docstrings Pattern

Python module docstrings in `hermes_cli/` follow a consistent pattern:
`"Description of module for Hermes Agent."` → `"Description of module for DeepSeek Agent."`
These are best handled with a batch `sed` targeting the full phrase.

### 6. Skin Engine Defaults (5 Skins)

The `hermes_cli/skin_engine.py` has 5 built-in skin definitions, each with a
`"agent_name": "Hermes Agent"` default. These control the TUI banner when no
custom skin is active. A single `sed` handles all 5:

```bash
sed -i '' 's/"agent_name": "Hermes Agent"/"agent_name": "DeepSeek Agent"/g' hermes_cli/skin_engine.py
```

### 7. Built-in Default API Key Provider

When forking an agent framework that needs to ship with a pre-configured API key
(so users can use it immediately), add a `custom_providers` entry in config.yaml:

```yaml
model:
  default: deepseek-v4-flash
  provider: custom:my-builtin

custom_providers:
- api_key: <built-in-key>
  base_url: https://your-api-gateway.com/v1
  model: deepseek-v4-flash
  models:
    deepseek-v4-flash:
      context_length: 1000000
      name: deepseek-v4-flash
  name: my-builtin
```

**Best practices for built-in keys:**
- The provider should expose only ONE model (the intended default)
- Users can still add their own API keys via the setup wizard
- The built-in key replaces "you must configure your own API key" as the first-run default
- Make this the default by setting `model.provider: custom:<name>`
- Use a dedicated API gateway (like NewAPI) that can control model access, rate limits, and token budgets per key
