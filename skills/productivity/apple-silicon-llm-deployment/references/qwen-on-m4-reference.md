# Apple Silicon LLM Reference Data

> **Compiled from the Qwen-on-M4 deployment session (June 2026).**
> Source: Artificial Analysis, Qwen official blog, willitrunai.com, community benchmarks.

## Model Variant Quick Reference

### Qwen 3.x 27B Family

| Model | Architecture | Vision | Coding Focus | Release | Context |
|---|---|---|---|---|---|
| **Qwen3.5-27B** | Dense 27B | ✅ Unified VL | Strong | Feb 2026 | 262K (native), 1M (ext.) |
| **Qwen3.6-27B** | Dense 27B | ✅ Unified VL | ⭐ Strongest coding | Apr 2026 | 262K (native) |
| **Qwen3.7-Max** | Proprietary | Unknown | Unknown | May 2026 | ❌ NOT open source |

### Qwen 3.x MoE Family

| Model | Total Params | Active Params | Vision | Coding | Speed on M4 Air |
|---|---|---|---|---|---|
| **Qwen3.5-35B-A3B** | 35B | 3B | ✅ Unified VL | Good | ~20-30 tok/s (4-bit) |
| **Qwen3.6-35B-A3B** | 35B | 3B | ❌ No vision | Coding-focused | ~20-30 tok/s (4-bit) |

**Warning about 3.6 MoE**: Community reports quality regression vs Qwen3.5-35B-A3B. 18% of failures attributed to system prompt non-compliance. The dense 3.6-27B beats the MoE 3.6-35B-A3B by 4-20 points on coding benchmarks.

## MLX Quantized Model Availability

| Model | 4-bit | 6-bit | 8-bit | Notes |
|---|---|---|---|---|
| Qwen3.5-35B-A3B | ✅ hr | ❌ | ❌ | 20.4 GB at 4-bit |
| Qwen3.6-27B | ✅ hf | ✅ hf | ✅ hf | All three available in mlx-community |
| Qwen3.5-27B | ✅ hf | ✅ hf | ✅ hf | Also available |

## Coding Benchmark Data

### Qwen3.6-27B vs Competition

| Benchmark | Qwen3.6-27B | Qwen3.5-397B-A17B | Qwen3.6-35B-A3B | DS V4 Flash |
|---|---|---|---|---|
| **SWE-bench Verified** | **77.2** | 76.2 | 73.4 | ~75+ |
| **SWE-bench Pro** | **53.5** | 50.9 | 49.5 | — |
| **Terminal-Bench 2.0** | **59.3** | 52.5 | 51.5 | — |
| **SkillsBench Avg5** | **48.2** | 30.0 | 28.7 | — |
| **GPQA Diamond** | 87.8 | 88.4 | 86.0 | **87%** (DS V4) |
| **LiveCodeBench v6** | **83.9** | 83.6 | 80.4 | **~90%** (DS V4) |

### Quantization Quality Impact (Qwen3.6-27B, via llama.cpp GGUF)

| Variant | HumanEval | HellaSwag | BFCL | Peak RAM | Speed |
|---|---|---|---|---|---|
| BF16 (full) | 56.10% | 86.00% | 63.25% | 50.45 GB | 15.5 tok/s |
| Q8_0 | 52.44% | 85.00% | 63.00% | 26.96 GB | 18.0 tok/s |
| Q4_K_M | 50.61% | 84.00% | 63.00% | 25.77 GB | 22.5 tok/s |

**Key finding**: Function calling (BFCL) is nearly invariant to quantization. Coding (HumanEval) drops ~5.5 points from BF16 to 4-bit. For tool-calling use cases, 4-bit is essentially equivalent to full precision.

## M4 MacBook Air 32GB Speed Estimates

### Qwen3.5-27B 4-bit (dense)
- **M4 Air, plain MLX**: ~10-15 tok/s
- **M4 Air, +DFlash**: ~20-25 tok/s (short ctx), ~15-18 tok/s (8K), ~10-12 tok/s (128K)
- **M4 Pro 24GB**: 15-22 tok/s
- **M4 Max 36GB**: 30-42 tok/s

### Qwen3.5-35B-A3B 4-bit (MoE, faster than dense on M4 Air)
- **M4 Air**: ~20-30 tok/s
- **M4 Pro 24GB**: 18-25 tok/s
- **M4 Max 36GB**: 40-55 tok/s

### Qwen3.5-9B 4-bit
- **M4 Air 16GB**: 25-35 tok/s
- **M4 Pro 24GB**: 32-42 tok/s

## DFlash Speculative Decoding on M4 Air

DFlash (dflash-mlx v0.1.10+) is the only production-ready speculative decoding option for Apple Silicon (as of June 2026). It uses a ~1B draft model to generate 16 tokens in parallel, then the target verifies all 16 in one pass — 2-3× lossless speedup.

### Hardware scaling from M5 Max benchmarks

M5 Max bandwidth ~540 GB/s. M4 Air bandwidth ~120 GB/s. Scale factor ≈ 0.22×.

| Context | M5 Max DFlash | Est. M4 Air DFlash | Notes |
|---------|-------------|-------------------|-------|
| 1K tok | 98.1 tok/s | **~22 tok/s** | ✅ 20+ target met |
| 8K tok | 79.1 tok/s | **~17 tok/s** | ✅ Over 15 |
| 16K tok | 60.8 tok/s | **~13 tok/s** | ⚠️ OK but not great |
| 128K tok | ~40 tok/s (est) | **~9-10 tok/s** | ⚠️ Drops under 10 |

### Memory footprint (Qwen3.6-27B-4bit + DFlash, 128K ctx, Q4 KV)

| Component | Size |
|-----------|------|
| Target model (4-bit) | ~16.8 GB |
| Draft model | ~1.5 GB |
| KV cache (128K Q4) | ~4.5 GB |
| Runtime overhead | ~1 GB |
| **Total model memory** | **~23-24 GB** |
| macOS overhead | ~8 GB (lean) |
| **Total system** | **~31-32 GB** |

**Only fits 32GB Macs.** 24GB Macs cannot run Qwen3.6-27B + DFlash (would need 16GB model + no KV cache headroom).

### How DFlash differs from DSpark

- **DFlash**: Block-diffusion speculative decoding, works on Apple Silicon via dflash-mlx. 2-3× speedup. Lossless.
- **DSpark** (DeepSeek, June 27 2026): Semi-autoregressive draft + confidence-scheduled verification. 60-85% on production NVIDIA clusters. **No Apple Silicon support.** No Qwen3.6 checkpoints released. The checkpoints are for Qwen3-4B/8B/14B only, not Qwen3.6-27B.

### DFlash vs MoE on M4 Air

| Strategy | Speed (1K ctx) | Coding quality | Memory |
|----------|---------------|----------------|--------|
| Dense 27B + DFlash | ~22 tok/s | ⭐ Strongest (77% SWE-bench) | ~24 GB |
| MoE 35B-A3B (no DFlash) | ~20-30 tok/s | ~73% SWE-bench (4pts loss) | ~20 GB |
| Dense 9B + DFlash | ~60 tok/s | Much weaker | ~7 GB |

For coding quality without DFlash → MoE wins on speed. For max quality with acceptable speed → Dense 27B + DFlash.

## Tips for approaching your speed limits

When the user asks for "50 tok/s" on a dense 27B on M4 Air:

1. Be honest: memory bandwidth is the hard ceiling (120 GB/s / 17 GB = ~7 tok/s theoretical max autoregressive)
2. DFlash multiplies this by 2-3×, bringing it to 20+ tok/s
3. To go faster: use a MoE model (35B-A3B), smaller model (9B), or use an API (DeepSeek V4 Flash)
4. KV cache grows linearly with context — at 128K+ it adds 4-6 GB, so longer context eats into memory and indirectly reduces speed

## DFlash server for OpenCode

The dflash-mlx OpenAI-compatible server runs on port 8000 by default. Connect OpenCode via:

```bash
# In OpenCode config or env:
OPENAI_API_KEY=unused...
```
Or use curl directly:
```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mlx-community/Qwen3.6-27B-4bit",
       "messages": [{"role": "user", "content": "Write quicksort in Python"}],
       "max_tokens": 1024, "stream": true}'
```

### Download pitfalls for China

- `hf download --include "*.safetensors"` is silently **ignored** — use explicit filenames only
- Large safetensors files (>5GB) from hf-mirror.com may slow to ~300 KB/s
- Always download model shards individually with explicit filenames (e.g. `model-00001-of-00003.safetensors`)
- Use background mode for large downloads

## DeepSeek V4 Flash (High Reasoning) — Benchmark Points

From Artificial Analysis comparison:
- **Architecture**: MoE, 284B total / 13B active
- **Context**: 1M tokens
- **SciCode**: 42% (vs Qwen3.5-27B 39%)
- **HLE**: 28% (vs 22%)
- **GPQA Diamond**: 87% (vs 86%)
- **AA-LCR (Long Context)**: 63% (vs Qwen3.5-27B 67%)
- **IFBench**: 73% (vs 76%)
- **Non-hallucination rate**: 10% (vs Qwen 20%)

**Pricing**: Input $0.28/M, Cache $0.03/M, Output $0.14/M tokens (USD).

## MLX Setup Notes for China Users

```bash
# PyPI mirror (Tsinghua)
pip install mlx-lm mlx-vlm huggingface_hub pillow \
  --timeout 120 -i https://pypi.tuna.tsinghua.edu.cn/simple

# HuggingFace mirror
HF_ENDPOINT=https://hf-mirror.com hf download <repo> --local-dir <path>

# If hf download fails on large files, use Python fallback:
python -c "
from huggingface_hub import snapshot_download
snapshot_download('<repo_id>', local_dir='<path>',
                  local_dir_use_symlinks=False, resume_download=True,
                  max_workers=4)
"
```
