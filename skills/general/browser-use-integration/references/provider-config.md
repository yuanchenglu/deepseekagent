# Provider Config Reference

Extracted from `~/.hermes/config.yaml` on 2026-06-09.

## opencodego

```yaml
base_url: https://opencode.ai/zen/go/v1
key_env: OPENCODEGO_API_KEY
api_mode: chat_completions
default_model: deepseek-v4-flash
models:
  - deepseek-v4-pro       # context: 1M, output: 32K
  - deepseek-v4-flash     # context: 1M, output: 64K
  - glm-5.1               # context: 200K, output: 16K
  - glm-5                 # context: 200K, output: 128K
  - kimi-k2.6             # context: 256K, output: 32K
  - kimi-k2.5             # context: 256K, output: 32K
  - mimo-v2.5-pro         # context: 256K, output: 32K
  - mimo-v2.5             # context: 256K, output: 32K
  - minimax-m2.7
  - minimax-m2.5
  - qwen3.6-plus
  - qwen3.5-plus
  - qwen3.7-max
```

## 7colorai-liantong

```yaml
base_url: https://aigw-gzgy2.cucloud.cn:8443/v1
key_env: COLORAI_LIANTONG_API_KEY
api_mode: chat_completions
default_model: glm-5.1
models:
  - DeepSeek-V4-Pro
  - glm-5.1
  - glm-5
  - kimi-k2.5
```

## Notes

- All providers use OpenAI-compatible `/v1/chat/completions` API
- Model names are case-sensitive and must match exactly
- For browser-use: always set `dont_force_structured_output=True` unless using OpenAI/Anthropic/Google official APIs
