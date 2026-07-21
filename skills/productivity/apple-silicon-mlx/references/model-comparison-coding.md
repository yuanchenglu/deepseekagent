# Coding Model Comparison: DeepSeek V4 Flash vs Qwen Local

Session date: 2026-06-28
Hardware: M4 MacBook Air 32GB unified memory
Framework: MLX (mlx-lm 0.31.3)

## Head-to-head: API vs Local

| Benchmark | DS V4 Flash (High Reasoning) | Qwen3.5-27B (official) | Qwen3.6-27B (official) |
|---|---|---|---|
| SWE-bench Verified | ~75%* | ~72% (Qwen3.5-27B) | **77.2%** |
| LiveCodeBench v6 | **~90%** | 89% | 83.9% |
| SciCode | **42%** | 39% | — |
| GPQA Diamond | **87%** | 86% | 87.8% |
| HLE (reasoning) | **28%** | 22% | — |
| AA-LCR (long context) | 63% | **67%** | — |
| IFBench (instruction following) | 73% | **76%** | — |

*DS V4 Flash SWE-bench estimate based on MoE 284B architecture with 13B active params.

**Verdict**: DS V4 Flash wins on pure coding + reasoning benchmarks by 2-6 points. Qwen3.6-27B is competitive on SWE-bench but trails on LiveCodeBench and competitive programming.

## Quantization impact on coding (Qwen3.6-27B)

| Quant | HumanEval | HellaSwag | BFCL | Speed | RAM |
|---|---|---|---|---|---|
| BF16 | 56.10% | 86.00% | 63.25% | 15.5 tok/s | 50 GB |
| Q8_0 | 52.44% | 85.00% | 63.00% | 18.0 tok/s | 27 GB |
| Q4_K_M | 50.61% | 84.00% | 63.00% | 22.5 tok/s | 26 GB |

Source: Neo AI evaluation. Q4_K_M preserves ~90% of coding ability vs BF16, with 2.3x speedup and 49% less RAM. BFCL (function calling) is invariant to quantization.

## Per-Mac-tier speed estimates (MLX 4-bit)

### Qwen3.5-35B-A3B (MoE, 3B active, ~20 GB)

| Mac | Est. tok/s | Notes |
|---|---|---|
| M4 Air 32GB | **20-30** | 10-core GPU, ~100 GB/s |
| M4 Pro 24GB | 18-25 | RAM bottleneck |
| M4 Max 36GB | 40-55 | 400 GB/s bandwidth |
| M4 Max 64GB | 55-70 | |
| M3 Ultra | 80-110 | |

### Qwen3.6-27B dense (~17 GB at 4-bit)

| Mac | Est. tok/s | Notes |
|---|---|---|
| M4 Air 32GB | **10-14** | Bandwidth bottleneck |
| M4 Pro 24GB | 15-22 | Tight fit |
| M4 Max 36GB | 30-42 | |
| M3 Ultra | 65-85 | |

## When to deploy locally vs use API

**Use API (DS V4 Flash)** when:
- Pure coding/reasoning tasks
- Budget is ~$5-30/month (DS V4 Flash is extremely cheap)
- Speed matters (cloud = instant)
- No vision needed

**Deploy locally (Qwen MLX)** when:
- Vision tasks (DS has none)
- Sensitive code (privacy)
- No internet / offline environment
- Unlimited usage needed
- Specific model features needed (thinking mode, long context at <32K)
