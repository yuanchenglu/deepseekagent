# MLX Ecosystem Reference

## Framework comparison

| Feature | mlx-lm (+mlx-vlm) | LM Studio | Rapid-MLX | Ollama (MLX backend) |
|---|---|---|---|---|
| **Speed** | Baseline | ~baseline | +20-60% | -30% |
| **Vision** | ✅ mlx-vlm | ✅ Built-in | ✅ [vision] extra | ✅ llama.cpp |
| **Speculative Decoding** | ❌ | ❌ | ✅ DFlash | ❌ |
| **dflash-mlx (bstnxbt fork)** | **✅ 2-3× baseline** | ❌ text only | Uses same MLX backend | ❌ |
| **DSpark (DeepSeek)** | ❌ NVIDIA only | ❌ | ❌ | ❌ |
| **Long Context Optimization** | Basic | Basic | ✅ PFlash | Basic |
| **API Server** | `mlx_lm server` | Built-in | `rapid-mlx serve` | `ollama serve` |
| **GUI** | ❌ CLI only | ✅ Full GUI | ❌ CLI only | ❌ CLI only |
| **Model Download** | Manual | Built-in browser | Built-in aliases | `ollama pull` |
| **Prompt Cache** | Basic | Basic | ✅ KV + DeltaNet | ❌ |
| **Integration** | Manual | Click-to-connect | `rapid-mlx launch` | `OLLAMA_BASE_URL` |

## Version compatibility (June 2026)

- **mlx-lm 0.31.3**: Last version checked in this session
- **mlx-vlm 0.6.3**: Used for Qwen3.5/3.6 vision models
- **mlx 0.31.2**: Core MLX framework
- **LM Studio 0.4.16**: Latest stable as of this session
- **Rapid-MLX v0.6.80**: With PFlash + DFlash support

## Key commands

### mlx-lm server (correct, NOT mlx_lm.serve)
```bash
python -m mlx_lm server --model <path> --host 127.0.0.1 --port 8085
```

### mlx-vlm vision inference
```bash
python -m mlx_vlm.generate --model <path> --image <file> --prompt "Describe"
```

### hf download (not deprecated huggingface-cli)
```bash
HF_ENDPOINT=https://hf-mirror.com hf download <repo> --local-dir <dir>
```

## Known issues

1. **`mlx_lm.serve` is deprecated** — use `python -m mlx_lm server` (subcommand)
2. **`huggingface-cli` is deprecated** — use `hf download`
3. **Port 8080 in use** — many systems (PHP, npm, etc.) already use 8080. Use 8083+
4. **LM Studio large download from China** — 539 MB, CDN times out. Use brew or VPN.
5. **First request slow** — server loads model lazily; first response can take 30s+
6. **Qwen thinking mode** — output includes thinking process by default. Disable with `--chat-template-args '{"enable_thinking":false}'`
7. **`hf download --include` silently ignored** — the `--include` flag is only for glob filtering when filenames are not specified, but it's silently ignored when targeting specific files. Use explicit filenames for safetensors shards.
8. **dflash-mlx NAX fallback** — dflash-mlx uses steel simdgroup-MMA fallback on M4-class GPUs (NAX is M5+ only). Still fast, just not peak.
