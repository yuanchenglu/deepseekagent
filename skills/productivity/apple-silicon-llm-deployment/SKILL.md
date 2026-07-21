---
name: apple-silicon-llm-deployment
description: "Deploy, serve, and switch between local LLMs on Apple Silicon (M-series) Macs using MLX. Framework selection, quantization analysis, hardware constraint math, model comparison, and management."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [apple-silicon, mlx, local-llm, model-deployment, quantization, apple-mac, m-series]
    related_skills: [llama-cpp, serving-llms-vllm]
---

# Apple Silicon Local LLM Deployment (MLX)

Use this skill when the user asks to deploy, serve, or run a local LLM on their Mac with Apple Silicon (M1/M2/M3/M4/M5 series).

## Core Principle: Analysis First, Execution Second

**Before downloading anything or running any command, present the complete plan first:**

1. Identify which specific model they want
2. Analyze hardware constraints (RAM, memory bandwidth, GPU cores)
3. Compare framework options (MLX vs llama.cpp vs LM Studio vs Ollama)
4. Quantization feasibility and tradeoffs
5. Speed estimates with clear upper/lower bounds
6. Let the user approve before acting

The user explicitly requires: **"先给方案，先不要急着动手"** — show the plan and options first, let them decide, then execute.

## Framework Selection for Apple Silicon

| Framework | Recommendation | Reason |
|---|---|---|
| **MLX (mlx-lm + mlx-vlm)** | ⭐ Best for M-series | Apple-native Metal/GPU optimization, best memory efficiency |
| **Rapid-MLX** | ⭐ Best performance | Wraps MLX with speculative decoding, prompt cache, PFlash for long contexts |
| **LM Studio** | Easy GUI | MLX under the hood, good for testing |
| **Ollama** | Simple but slower | Uses llama.cpp, 30-50% slower than MLX on M-series |
| **llama.cpp (GGUF)** | Legacy choice | Good ecosystem, but MLX is 20-87% faster on Apple Silicon |

**MLX is the default recommendation** unless the user already has a preference for GGUF/llama.cpp.

## Hardware Constraint Math

Apple Silicon LLM inference is **memory-bandwidth-bound**, not compute-bound.

### Memory Bandwidth by Chip

| Chip | Bandwidth | Relative to Max |
|---|---|---|
| M1/M2/M3/M4 Air | ~100-120 GB/s | ~25% |
| M4 Pro | ~200 GB/s | ~50% |
| M4 Max | ~400 GB/s | 100% |
| M3/M4 Ultra | ~800 GB/s | 2x |
| M5 Max | ~500+ GB/s | ~1.25x |

### Speed Estimation Formula

```
max_tok/s ≈ memory_bandwidth / (model_weight_size_in_GB)
```

**Reality check for the user when their speed target is unrealistic:**
- 50 tok/s on M4 Air would require ~2.4 GB/s bandwidth for a 4-bit 27B model — but M4 Air has ~120 GB/s
- The math: 120 GB/s ÷ 16.8 GB (27B 4-bit weights) ≈ 7 tok/s theoretical max
- Real-world with MLX optimizations: ~10-15 tok/s
- MoE models (e.g. 35B-A3B with 3B active) achieve much higher speeds: ~20-30 tok/s

### Memory Budget

```
Available RAM = Total RAM - 8-10 GB (macOS overhead)

M4 Air 16GB: ~6-8 GB available → only 7B-9B models at 4-bit
M4 Air 24GB: ~14-16 GB available → 27B at 4-bit (tight) or 9B at 8-bit
M4 Air 32GB: ~22-24 GB available → 27B 4-bit (comfortable), 35B-A3B 4-bit (tight)
M4 Pro 48GB: ~38-40 GB available → 27B 6-bit, 35B-A3B 6-bit
M4 Max 64GB+: ~54+ GB available → 27B 8-bit, 122B MoE 4-bit
```

## Quantization Guide

| Bit Width | Size Multiple | Quality Impact |
|---|---|---|
| BF16 | 2 bytes/param | Reference (no loss) |
| 8-bit | 1 byte/param | Near-lossless |
| 6-bit | 0.75 bytes/param | Excellent, ~1-2% coding quality loss |
| 4-bit | 0.5 bytes/param | Good, ~5% coding quality loss (HumanEval: 56%→51%) |
| 3-bit | 0.375 bytes/param | Noticeable loss, ~8-15% |
| 2-bit | 0.25 bytes/param | Major loss, only for extreme budgets |

**Function calling is nearly invariant to quantization** (BFCL scores same across all bit widths).

**Coding (HumanEval) is most sensitive** — 8-bit preserves coding ability much better than 4-bit.

**Recommendation for coding on M4 Air 32GB:**
- Best quality: Qwen3.6-27B 6-bit (~22.5 GB) if system is lean
- Best speed: Qwen3.6-35B-A3B 4-bit (~20-22 GB, MoE)
- Best balance: Qwen3.6-27B 4-bit (~17 GB)

## Model Selection Criteria: Local vs API

When the user already has a cheap/reliable API (e.g. DeepSeek V4 Flash), honestly assess:

```text
Local model advantages:
  ✓ Privacy (code never leaves machine)
  ✓ Unlimited usage
  ✓ Works offline
  ✓ Zero inference cost

API model advantages:
  ✓ Higher quality (no quantization loss)
  ✓ Much faster (datacenter GPUs)
  ✓ Larger context windows
  ✓ Lower latency

Best strategy: Use API for primary coding, local for vision/privacy
```

**Be honest when a local model can't beat an API.** Present the tradeoffs with data, not vague statements.

## MLX Model Sources

Quantized MLX models are available on HuggingFace:
- `mlx-community/` — official community quantizations
- `lmstudio-community/` — LM Studio conversions (also MLX)
- `unsloth/` — Unsloth MLX conversions

Search pattern: `https://huggingface.co/models?search=mlx-community+<model_name>`

## MLX Setup

```bash
# Create venv
python3 -m venv ~/mlx-env
source ~/mlx-env/bin/activate

# Install from PyPI mirror (China users)
pip install mlx-lm mlx-vlm huggingface_hub pillow --timeout 120 \
  -i https://pypi.tuna.tsinghua.edu.cn/simple

# Download model
HF_ENDPOINT=https://hf-mirror.com hf download \
  mlx-community/Qwen3.6-27B-4bit \
  --local-dir ~/mlx-models/Qwen3.6-27B-4bit

# Serve (OpenAI-compatible API)
mlx_lm.serve --model ~/mlx-models/Qwen3.6-27B-4bit \
  --host 127.0.0.1 --port 8080

# Vision inference
python -m mlx_vlm.generate \
  --model ~/mlx-models/Qwen3.5-35B-A3B-4bit \
  --prompt "Describe this image." \
  --image path/to/image.jpg \
  --max-tokens 1024
```

## Model Switching Pattern

For users running multiple models (fast vision + high-quality coding), create a management script pattern:

```bash
# Stop existing server
lsof -ti:8080 | xargs kill -9

# Start new model
source ~/mlx-env/bin/activate
nohup mlx_lm.serve --model ~/mlx-models/<model-dir> \
  --host 127.0.0.1 --port 8080 > serve.log 2>&1 &
```

## Long Context Memory Impact

KV cache grows with context length:

| Context | 27B Dense KV Cache | 35B-A3B MoE KV Cache |
|---|---|---|
| 4K (base) | ~0.2 GB | ~0.2 GB |
| 32K | ~2 GB | ~1.5 GB |
| 128K | ~8 GB | ~6 GB |
| 256K | ~16 GB | ~12 GB |

For M4 Air 32GB running at 128K+: limit to 4-bit quantization and close other apps.

## References

- **[qwen-on-m4-reference.md](references/qwen-on-m4-reference.md)** — Model variant reference, benchmark data, quantization impact tables, M4 speed estimates, DS V4 Flash comparison, China mirror setup notes.

## Pitfalls

1. **Don't over-promise speed.** M4 Air memory bandwidth (~120 GB/s) is the hard ceiling. Compute speed expectations realistically.
2. **Don't skip the plan phase.** The user explicitly corrected: "先给方案，先不要急着动手" — always present full analysis + options before acting.
3. **Remember the OS overhead.** macOS uses ~8-10 GB. Available RAM = Total - 10 GB (conservative).
4. **Port immutability: NEVER take over an occupied port.** If a port is already in use, choose a different free port for your new service. Existing services may be bound to Cloudflare tunnels — changing a running service's port breaks those tunnels.
4. **Vision models need mlx-vlm.** `mlx_lm.serve` handles text-only; image input requires `mlx_vlm.generate` or a custom vision server.
5. **HF mirror may be slow for large files.** hf-mirror.com can drop to ~300 KB/s on large safetensors. **For China users, modelscope.cn is 10-50× faster** (20-40 MB/s). See `apple-silicon-mlx` skill's "Model download (from China)" section for the modelscope download + HF cache conversion workflow.
6. **Quantization quality varies by task.** Function calling is robust to quantization; pure coding is not. Test your use case.
7. **MoE speed advantage shrinks at long contexts.** KV cache is proportional to total params (not active), so MoE advantage in decode speed diminishes at 128K+.
8. **Block on speculative decoding for Apple Silicon**: If the user asks about DSpark (DeepSeek, June 2026) or any speculative decoding paper claiming 60-85% speedup, check whether it has an MLX/Apple Silicon port. DSpark requires NVIDIA CUDA and has no MLX port — the checkpoints are for Qwen3 (not Qwen3.6) and DeepSeek-V4 models only. DFlash via `dflash-mlx` (bstnxbt fork) is the only production-ready speculative decoding option for Apple Silicon as of June 2026.
9. **`hf download --include` quirk**: The `--include` flag is silently ignored when filenames aren't also explicitly specified. Always download large safetensors files by explicitly naming each shard file (e.g., `model-00001-of-00003.safetensors`), not with glob patterns.
