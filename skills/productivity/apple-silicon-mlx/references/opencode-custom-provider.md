# Connecting MLX Local Model to OpenCode as Custom Provider

## Correct Config Format (OpenCode v1.0.152)

Add this to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "local-mlx/Qwen3.5-35B-A3B-4bit",
  "provider": {
    "local-mlx": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local MLX Display Name",
      "options": {
        "baseURL": "http://127.0.0.1:8085/v1",
        "apiKey": "sk-not-needed"
      },
      "models": {
        "Qwen3.5-35B-A3B-4bit": {
          "name": "Qwen3.5 MoE (Local)",
          "limit": {
            "context": 8192,
            "output": 4096
          }
        }
      }
    }
  }
}
```

## Credential

Add a dummy credential to `~/.local/share/opencode/auth.json`:

```json
{
  "local-mlx": {
    "type": "api",
    "key": "sk-not-needed"
  }
}
```

## Key details

- **Provider key** (`local-mlx`) must match between config and auth
- **Model ID** in `"model": "local-mlx/Qwen3.5-35B-A3B-4bit"` is `provider-key/model-key`
- **`npm`** must be `@ai-sdk/openai-compatible` for any OpenAI-compatible endpoint
- **`baseURL`** must end with `/v1` (no trailing slash needed, OpenCode strips trailing slashes)
- **`apiKey`** can be a dummy string for local models that don't require auth

## Troubleshooting

- If OpenCode shows "Config file ... is invalid Unrecognized keys: ...", the format is wrong
  - The `options.baseURL` structure is required (not flat `baseUrl`)
  - The `npm` field is required for custom providers
- The `/connect` TUI command can also add credentials interactively but requires selecting "Other" provider type
