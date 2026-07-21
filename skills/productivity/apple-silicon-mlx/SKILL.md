---
name: apple-silicon-mlx
description: Deploy, quantize, and serve LLMs on Apple Silicon Macs using MLX framework. Model selection, quantization tradeoffs, API server setup, LM Studio integration.
version: 1.2.0
author: Hermes Agent
license: MIT
dependencies: [mlx-lm>=0.31, mlx-vlm>=0.6, huggingface-hub]
platforms: [macos, arm64]
metadata:
  hermes:
    tags: [apple-silicon, mlx, macos, local-llm, inference, metal, m-series, qwen, deepseek]
---

# Apple Silicon MLX Deployment

Deploy and serve LLMs on Apple Silicon Macs using Apple's MLX framework. Covers model selection, quantization, download strategy (including China mirrors), API serving, and GUI management.

## When to use

- The user wants to run a large model (7B-70B) on an Apple Silicon Mac
- The user asks about MLX vs llama.cpp vs LM Studio for local inference
- The user needs quantized model recommendations for their specific Mac tier (M1-M4, Air/Pro/Max, RAM)
- The user needs an OpenAI-compatible API server from a local MLX model
- The user asks about vision model support on Apple Silicon
- Comparing local deployment feasibility vs API-based alternatives

## Hardware memory budget

macOS uses ~8-10 GB, leaving **22-24 GB** available for models on a 32GB machine. Adjust proportionally for other RAM sizes.

| Mac Tier | Mem BW | Typical Available |
|---|---|---|
| M4 MacBook Air (8-10 GPU) | ~100-120 GB/s | RAM - 9GB |
| M4 Pro (20 GPU) | ~200 GB/s | RAM - 9GB |
| M4 Max (40 GPU) | ~400 GB/s | RAM - 9GB |
| M4 Ultra | ~800 GB/s | RAM - 10GB |

## Model selection guidance

### For coding + vision (multimodal)

Prefer **Qwen3.5-35B-A3B (MoE, 4-bit)** on 32GB Macs. It activates only ~3B params per token, giving 3-4x faster inference than a dense 27B, while including vision encoder. ~20-22 GB at 4-bit.

For maximum coding quality (no vision needed), prefer **Qwen3.6-27B dense (4-bit)** at ~17 GB. Its SWE-bench score (77.2%) beats the MoE variant but runs slower (~10-14 tok/s on M4 Air vs ~20-30 for MoE).

### Dense vs MoE tradeoff

- **Dense 27B**: Best quality (~10-14 tok/s on M4 Air), SWE-bench ~77%
- **MoE 35B-A3B**: ~4x faster active params (~20-30 tok/s), quality loss 4-20 pts on coding benchmarks
- **Dense 9B**: Fast (25-35 tok/s), fits 16GB Macs, but significantly weaker

### Quantization tiers (for 27B dense)

| Quant | Size | Speed (M4 Air) | Quality vs FP16 | Fit on 32GB |
|---|---|---|---|---|
| 4-bit | ~17 GB | ~10-14 tok/s | ~5% coding loss | ✅ Comfortable, room for 128K ctx |
| 6-bit | ~21 GB | ~7-10 tok/s | ~2% loss | ⚠️ Tight, fits with DFlash draft (~24GB total) |
| 8-bit | ~29 GB | ❌ doesn't fit 32GB | near-lossless | ❌ |

**6-bit recommendation for coding**: If you want maximum coding quality and are willing to close other apps, 6-bit is the best choice on 32GB. The quality gap between 4-bit and 6-bit on coding benchmarks (HumanEval, SWE-bench) is ~3-5 points. With DFlash speculative decoding, 6-bit still achieves ~10-14 tok/s on short tasks.

### Key benchmark data: DeepSeek V4 Flash (API) vs Qwen local

Use this when the user asks whether to deploy locally or use an API:

| Benchmark | DS V4 Flash (High Reasoning) | Qwen3.5-27B (local 4-bit) | Verdict |
|---|---|---|---|
| SciCode | **42%** | ~39% (~37% at 4-bit) | DS ahead |
| SWE-bench Verified | ~75% | **77.2%** (Qwen3.6-27B) | Qwen3.6 ahead |
| LiveCodeBench v6 | **~90%** | 83.9% (Qwen3.6-27B) | DS ahead |
| Vision | ❌ No | ✅ Yes | Qwen only |
| Context | 1M tokens | 262K tokens | DS ahead |
| Cost | $0.14/M tok (output) | Free | Qwen (local) |
| Speed | Fast (cloud) | 10-44 tok/s (M4 Air) | DS faster |

Bottom line: **For pure coding, DS V4 Flash API beats any local 27B model** and costs pennies. Only deploy locally when:
- You need **vision/multimodal** capability (DS has none)
- You have **sensitive code** that can't go to cloud
- You want **unlimited usage** without API limits
- You need **zero latency** (no network round-trip)

## Framework comparison

| Framework | Speed | Vision | Ease | Best for |
|---|---|---|---|---|
| **dflash-mlx** | Fastest (2-3× MLX) | ❌ (text only) | CLI | Maximum speed, DFlash speculative decoding |
| **MLX (mlx-lm + mlx-vlm)** | Fast baseline | ✅ | CLI | General MLX inference + vision |
| **LM Studio** | ~MLX | ✅ | GUI | Daily use, model switching |
| **Rapid-MLX** | ~MLX + speculative | ✅ | CLI | Optimized long context |
| **Ollama (llama.cpp)** | ~30% slower | ✅ | Very easy | Quick experiments |
| **llama.cpp** | ~15-25% slower | ✅ | CLI | GGUF ecosystem |

**Recommendation**: dflash-mlx for max speed, MLX for vision-capable, LM Studio for GUI management.

## DFlash Speculative Decoding (dflash-mlx)

DFlash is a block-diffusion speculative decoding method that uses a ~1B draft model to generate 16 tokens in parallel, then the target model verifies all 16 in a single forward pass. **Lossless** — every emitted token is verified against the target. 2-3× real-world speedup on Apple Silicon.

### What this is NOT

- **DSpark** (DeepSeek, June 2026) is a more advanced speculative decoding framework that builds on DFlash. It requires NVIDIA CUDA GPUs and has no Apple Silicon port. Only use DSpark on Linux with NVIDIA GPUs.
- **DFlash** (this skill) is the original block-diffusion method, now ported to MLX as `dflash-mlx`. It works on Apple Silicon.

### Setup

```bash
# Install from PyPI (or clone from GitHub)
pip install dflash-mlx -i https://pypi.tuna.tsinghua.edu.cn/simple

# Or clone for bleeding edge (recommended)
git clone https://github.com/bstnxbt/dflash-mlx.git ~/dflash-mlx
cd ~/dflash-mlx && pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# Verify environment
dflash doctor
```

### Model download (from China)

## Primary: Modelscope (fastest, 20-40 MB/s)

[Modelscope](https://www.modelscope.cn) (阿里魔搭) is a Chinese HF mirror with much better bandwidth than hf-mirror.com for large model files. Download at 20-40 MB/s:

```bash
pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple

# Download model
python3 -c "
from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download('<repo_id>', cache_dir='/tmp/msc_cache')
print(f'Downloaded to: {model_dir}')
"
```

**After download, convert to HF cache format** so `mlx_lm` / `dflash` can find the model:

```python
import hashlib, os, shutil
model_name = '<repo-id>'  # e.g. 'z-lab--Qwen3.6-27B-DFlash'
src = '/tmp/msc_cache/<normalized_path>'
hf_base = os.path.expanduser(f'~/.cache/huggingface/hub/models--{model_name}')
blobs_dir = os.path.join(hf_base, 'blobs')
snap_dir = os.path.join(hf_base, 'snapshots', 'main')
os.makedirs(blobs_dir, exist_ok=True)
os.makedirs(snap_dir, exist_ok=True)
for fname in ['model.safetensors', 'config.json', 'tokenizer.json', 'tokenizer_config.json', 'README.md']:
    src_path = os.path.join(src, fname)
    if not os.path.exists(src_path): continue
    sha256 = hashlib.sha256()
    with open(src_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''): sha256.update(chunk)
    blob_hash = sha256.hexdigest()
    blob_path = os.path.join(blobs_dir, blob_hash)
    if not os.path.exists(blob_path): shutil.copy2(src_path, blob_path)
    os.symlink(f'../../blobs/{blob_hash}', os.path.join(snap_dir, fname))
```

**Check if a model is on Modelscope:**
```python
from modelscope.hub.api import HubApi
api = HubApi()
try:
    api.get_model('mlx-community/Qwen3.6-27B-4bit')
    print('Available')
except: print('Not available')
```

Most `mlx-community/*`, `z-lab/*`, and `Qwen/*` models are mirrored there.

## Fallback: hf-mirror.com (slower, 300 KB/s - 2 MB/s)

```bash
# ⚠️ --include flag is IGNORED by hf download when filenames aren't specified
# Download each safetensors shard explicitly:

# Draft model:
HF_ENDPOINT=https://hf-mirror.com hf download z-lab/Qwen3.6-27B-DFlash model.safetensors

# Target model (~17GB, 3 shards):
HF_ENDPOINT=https://hf-mirror.com hf download mlx-community/Qwen3.6-27B-4bit \
  model-00001-of-00003.safetensors \
  model-00002-of-00003.safetensors \
  model-00003-of-00003.safetensors \
  config.json tokenizer.json tokenizer_config.json \
  chat_template.jinja generation_config.json \
  model.safetensors.index.json
```

Use background mode (`notify_on_complete=true`) for large files.

### Run OpenAI-compatible server

**Recommended parameters for coding (6-bit on M4 32GB):**

```bash
dflash serve \
  --model /path/to/Qwen3.6-27B-6bit \
  --draft z-lab/Qwen3.6-27B-DFlash \
  --port 8085 \
  --temp 0.0 \
  --dflash-max-ctx 262144 \
  --quantize-kv-cache \
  --fastpath-max-tokens 256
```

Key parameter explanation:
- `--dflash-max-ctx 262144` — hard cap at 256K (model's native max). **Context is dynamic**: KV cache only grows with actual prompt+generation length. Sending a 1K prompt uses ~1K of cache; a 128K prompt uses ~128K. No need to manually adjust per task — it auto-scales.
- `--quantize-kv-cache` — 8-bit quantized KV cache halves long-context memory growth at minimal quality cost
- `--fastpath-max-tokens 256` — requests with max_tokens ≤ 256 skip speculative decoding and use pure AR. Short completions (single-line code, short answers) start instantly without draft overhead.
- `--temp 0.0` — deterministic for coding

This server is compatible with OpenCode, aider, Continue, Open WebUI, and any OpenAI-compatible client. Use `http://localhost:8085/v1` as the base URL.

### Benchmark data (M5 Max 64GB)

Baseline = stock `mlx_lm.stream_generate` without DFlash.

| Model | Tokens | Baseline | DFlash | Speedup |
|-------|--------|----------|--------|---------|
| Qwen3.6-27B-4bit | 1024 | 33.3 | **98.1** | 2.95× |
| Qwen3.6-27B-4bit | 4096 | 30.6 | **93.6** | 3.06× |
| Qwen3.6-27B-4bit | 8192 | 26.0 | **79.1** | 3.04× |
| Qwen3.6-27B-4bit | 16384 | 21.5 | **60.8** | 2.78× |

### Estimated performance on M4 Air (32GB, 120 GB/s)

M4 Air bandwidth is ~1/4.5 of M5 Max. Scale proportionally:

| Context | Est. Baseline | Est. DFlash | Notes |
|---------|--------------|-------------|-------|
| 1K | ~7 tok/s | **~22 tok/s** | ✅ Comfortable |
| 8K | ~6 tok/s | **~17-18 tok/s** | ✅ Fine |
| 32K | ~5 tok/s | **~14 tok/s** | ⚠️ OK |
| 128K | ~4-5 tok/s | **~10-12 tok/s** | ⚠️ Should work, close apps |

**Key takeaway**: 50 tok/s is NOT possible on M4 Air for a dense 27B model — memory bandwidth is the hard ceiling. 20+ tok/s is achievable with DFlash at short-to-medium context lengths.

### Empirical results: Qwen3.6-27B-4bit + DFlash on M4 Air 32GB (2026-06-30)

Real run (clean system after reboot, only Hermes + Chrome + background services):

- Short prompts (20-31 tokens): **14.3–16.1 tok/s** (79–86% draft acceptance)
- Longer generation (400 tokens): **10.7 tok/s** (64.5% acceptance)
- Prefill logical: 14–22 tok/s depending on prompt length
- Memory: ~16.5–16.9 GB active for target + draft; process RSS ~4–8.7 GB peak

**Key observations from logs**:
- `dflash` server logs the true internal speed: `[dflash] decode X tok/s | Y% accepted | Z tokens | Ts`
- Client-reported speed can appear lower when the model emits large "thinking process" / reasoning_content (common with Qwen). Always cross-check server logs.
- Acceptance rate drops on long outputs; short deterministic prompts give highest speedup.
- After heavy/long-context requests, generation can hang (HTTP 000 after 25-40s). Restart the server cleanly in this case.

**Memory in practice**:
- Fits comfortably at 128K Q4 KV when other apps are closed.
- Do not rely on swap — it destroys speed.

Update your expectations: 12–16 tok/s short/medium context is the realistic sweet spot on M4 Air + DFlash for this model class.

### Connecting to Hermes Agent

After starting the DFlash server, add it as a custom provider in Hermes config:

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: local-qwen
    base_url: http://localhost:8085/v1
    api_key: not-needed     # local server, no auth required
    model: local-qwen       # model ID exposed by DFlash server
    models:
      local-qwen:           # ← must match --model's final path segment
        name: Qwen3.6-27B-6bit
        context_length: 262144   # matches --dflash-max-ctx
```

Then switch to it at runtime:
```bash
hermes model local-qwen/local-qwen
```

Or make it the default:
```yaml
# ~/.hermes/config.yaml
model:
  default: local-qwen
  provider: custom:local-qwen
```

**Critical rule (Hermes is lifeline):** The local model is an additional option, NOT a replacement for the primary API provider. Always keep existing API providers (clawadmin, opencode-go, etc.) as fallbacks. The workflow:
1. `dflash serve --model ...` (in one terminal)
2. `hermes model local-qwen/local-qwen` (switch to local)
3. `hermes model deepseek-v4-flash` (switch back when local is not running)

If the local server is not running when Hermes tries to use it, you'll get connection errors. Just switch back to the API provider — no Hermes config is harmed.

### Memory budget (32GB Mac)

| Item | Size |
|------|------|
| macOS system | ~8-10 GB |
| Qwen3.6-27B 4-bit | ~17 GB |
| DFlash draft model | ~1.5 GB |
| KV cache (128K Q4) | ~4.5 GB |
| **Total** | **~31 GB** |

Tight but fits. For 262K native context, KV cache grows to ~9 GB, which may trigger swap. Capable but expect performance degradation.

### Limitations

- **Text-only**: No vision/multimodal support in the DFlash server
- **M4 NAX kernels unavailable**: dflash-mlx falls back to steel simdgroup-MMA kernels on M4 (not M5). Still fast, just not peak.
- **No streaming metrics GUI**: Use `/metrics` endpoint on the server
- **No tool call enforcement**: `tool_choice` other than `"auto"` or `"none"` is rejected
- **Draft download is required**: You must download both the target model AND the matching DFlash draft model

### Common commands

```bash
# List supported target/draft pairs
dflash models

# One-shot generation
dflash generate --model Qwen/Qwen3.5-9B --prompt "Hello"

# Run benchmark
dflash benchmark --model mlx-community/Qwen3.6-27B-4bit --draft z-lab/Qwen3.6-27B-DFlash

# Environment check
dflash doctor

# Basic diagnostic server
dflash serve --model mlx-community/Qwen3.6-27B-4bit --diagnostics basic

# Live metrics
curl http://127.0.0.1:8000/metrics
```

### Qwen thinking mode

Qwen3.5+ models have **model-inherent** thinking/reasoning — it is baked into the model weights, not solely controlled by the chat template. Even `--use-default-chat-template` on `mlx_lm.server` does NOT fully disable it.

**Field names differ by serving framework:**
- **DFlash**: `reasoning_content`
- **MLX server (`mlx_lm.server`)**: `reasoning`

**Practical impact:**
- Simple requests need ~500 tokens total (thinking preamble + final content)
- Coding tasks need 1000–2000+ tokens; short `max_tokens` produces empty `content`
- First response takes 30–60s on M4 Air 32GB due to thinking overhead
- MoE models (35B-A3B) complete thinking faster than dense 27B due to fewer active params

**Always check both fields in client code:**
```python
msg = choice["message"]
text = msg.get("content") or msg.get("reasoning_content") or msg.get("reasoning") or ""
```

**Verification test**: Set `max_tokens: 500`, `temperature: 0.1`. If the model only outputs `reasoning` (no `content`), increase `max_tokens`. Short prompts like "say hi" can take 200+ tokens of thinking before emitting "hello".

### Supported model pairs

| Target | Draft |
|--------|-------|
| `mlx-community/Qwen3.6-27B-4bit` | `z-lab/Qwen3.6-27B-DFlash` |
| `mlx-community/Qwen3.5-27B-4bit` | `z-lab/Qwen3.5-27B-DFlash` |
| `mlx-community/Qwen3.6-35B-A3B-4bit` | `z-lab/Qwen3.6-35B-A3B-DFlash` |
| `mlx-community/Qwen3.5-35B-A3B-4bit` | `z-lab/Qwen3.5-35B-A3B-DFlash` |
| `Qwen/Qwen3.5-4B` | `z-lab/Qwen3.5-4B-DFlash` |
| `Qwen/Qwen3.5-9B` | `z-lab/Qwen3.5-9B-DFlash` |

### Tips

- **Prep the draft model first**: The server auto-resolves draft model. `dflash models` to verify support.
- **Pre-warm the server**: First request loads the model lazily. Call `/v1/models` first (doesn't load), or make a short dummy request.
- **Draft quantization**: Defaults to w4 for memory efficiency. Pass `--draft-quant none` for bf16 draft if memory permits.
- **Prefix cache** enabled by default: Revisit prompts skip prefill. Set `--no-prefix-cache-l2` to disable SSD spill.
- **Swappiness**: On 32GB Mac running a 23GB model, close Chrome and other memory-heavy apps. macOS swap is auto-managed but model MUST fit in physical RAM — SSD swap is ~3 GB/s vs 120 GB/s RAM bandwidth, making inference unusable if it pages.

## Setup

```bash
# Create environment
python3 -m venv mlx-env
source mlx-env/bin/activate

# Install MLX stack
pip install mlx-lm mlx-vlm huggingface_hub pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

# Or if you prefer Chinese mirror for all pip operations:
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## Model download

### From China — large files timeout (use individual download)

`hf download` from mirrors often times out on individual safetensors files >5GB.
Use `[scripts/download-files.py](scripts/download-files.py)` instead — it downloads
one shard at a time with retries:

```bash
source mlx-env/bin/activate
python scripts/download-files.py \
  mlx-community/Qwen3.6-27B-4bit \
  ~/mlx-models/Qwen3.6-27B-4bit \
  --retries 20 --timeout 600
```

Available MLX-quantized models:
- `mlx-community/Qwen3.5-35B-A3B-4bit` (20 GB, vision, MoE, fastest)
- `mlx-community/Qwen3.6-27B-4bit` (16 GB, dense, best coding)
- `mlx-community/Qwen3.6-27B-6bit` (23 GB, dense, higher quality)
- `mlx-community/Qwen3.5-35B-A3B-8bit` (38 GB, vision, near-lossless)

### Direct (outside China)

```bash
hf download <repo> --local-dir ~/mlx-models/<name>
```

### Verify download

```bash
find ~/mlx-models/<model> -maxdepth 1 -name "*.safetensors" | wc -l
# Should match the expected shard count from model.safetensors.index.json
```

## Running inference

### Quick text generation

```python
from mlx_lm import load, generate

model, tokenizer = load("~/mlx-models/Qwen3.5-35B-A3B-4bit")

prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": "Write quick sort in Python"}],
    tokenize=False, add_generation_prompt=True
)

response = generate(model, tokenizer, prompt=prompt, max_tokens=200)
print(response)
```

### Disable thinking mode (Qwen3.5+)

Qwen3.5+ outputs thinking process by default. Disable it:
```python
prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": "Your prompt here"}],
    tokenize=False, add_generation_prompt=True,
    enable_thinking=False  # Only works with Qwen tokenizer
)
```

### Vision inference

```bash
python -m mlx_vlm.generate \
  --model ~/mlx-models/Qwen3.5-35B-A3B-4bit \
  --prompt "Describe this image" \
  --image ~/Desktop/photo.jpg \
  --max-tokens 1024
```

### API server

Use `[api-server.py](scripts/api-server.py)` for a lightweight OpenAI-compatible server:

```bash
source mlx-env/bin/activate
python scripts/api-server.py \
  --model ~/mlx-models/Qwen3.5-35B-A3B-4bit \
  --port 8085
```

Then connect from any OpenAI-compatible client:
```bash
curl http://localhost:8085/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

**Important**: Port 8080 is commonly used by other services (PHP, npm, etc.). Use 8083-8089 to avoid conflicts.

### DFlash fallback: mlx_lm.server

When DFlash cannot download draft models (network issues, blocked HuggingFace), use the built-in MLX server as a fallback. It is slower (no speculative decoding) but has no external dependencies:

```bash
source ~/mlx-env/bin/activate
mlx_lm.server \
  --model /path/to/model \
  --port 8085 \
  --host 0.0.0.0 \
  --log-level INFO
```

**Why use mlx_lm.server over DFlash:**
- No draft model download needed (avoids HF network failures)
- Equally compatible OpenAI API (same endpoints)
- Works offline once model is on disk
- Also supports `--use-default-chat-template` for simpler templating

**Why use DFlash over mlx_lm.server (when draft downloads work):**
- 2-3× faster generation throughput
- Better memory efficiency with `--quantize-kv-cache`
- Prefix caching for repeated prompts

**Migration path**: Start with `mlx_lm.server` to validate model + connectivity, then switch to DFlash once the draft model is downloaded.

## LM Studio (GUI alternative)

LM Studio provides a GUI for model management, chat, and API serving. It uses MLX under the hood.

**Install**: Download from [lmstudio.ai](https://lmstudio.ai) (⚠️ downloads may be slow from China)
**Model storage**: `~/Library/Application Support/LM Studio/models/`
**Model search**: Discover tab → filter by "MLX"

To import pre-downloaded MLX models:
```bash
cp -r ~/mlx-models/Qwen3.5-35B-A3B-4bit \
  "~/Library/Application Support/LM Studio/models/huggingface/mlx-community/"
```

## User preferences

- Prefers GUI tools (LM Studio) over CLI for day-to-day model management
- Wants data-driven comparisons with concrete benchmark numbers, not vague statements
- On M4 MacBook Air 32GB — available memory is ~22-24 GB
- May need Chinese network mirrors for downloads (hf-mirror.com, tuna pypi mirror)
- Uses Hermes + Chrome + OpenCode as primary apps

## Pitfalls

1. **Port conflicts**: 8080 is commonly occupied. Use 8083+ for API servers.
2. **NEVER take over an occupied port for a new service**: If a port is already in use (e.g. 8081, 3000), choose a different free port for your new service. The user's existing services may be bound to Cloudflare tunnels or other critical infrastructure. Changing a running service's port breaks those tunnels.
2. **`mlx_lm.server` is deprecated**: Use `python -m mlx_lm server` (subcommand, not module).
3. **`huggingface-cli` is deprecated**: Use `hf download` instead.
4. **China network**: Direct HuggingFace downloads time out. Always use `HF_ENDPOINT=https://hf-mirror.com`.
5. **First load is slow**: The model loads on first request in server mode. First response may take 30s+.
6. **Think mode adds overhead**: Qwen3.5+ defaults to thinking output. Disable with `--chat-template-args '{"enable_thinking":false}'`.
7. **Memory fills up**: 32GB Mac runs tight with 20GB model + KV cache. Expect memory pressure at >64K context. **Close Chrome and other memory-heavy apps** when running local models.
8. **Context is NOT pre-allocated**: `max_position_embeddings: 262144` is the *ceiling*, not the baseline. KV cache auto-scales with actual prompt+generation length. A 1K request does not allocate 256K of KV cache — many developers assume worst case and overestimate memory needs.
9. **Local model is additive, not replacive**: When integrating with Hermes, the local model is an additional provider option, not a replacement for existing API providers. Always keep API fallbacks configured. If the local server is not running, just switch back to the API provider — Hermes itself is never down.
10. **6-bit on M4 32GB is viable with DFlash but tight**: 21GB target + ~1.5GB draft = ~22.5GB before KV cache. At 128K context with quantized KV cache, total ~25-26GB. At 256K, expect ~28-29GB and possible swap. Use `--quantize-kv-cache` to halve KV cache growth.
11. **DFlash is NOT optional for acceptable speed on dense 27B**: Without DFlash, Qwen3.6-27B-6bit runs at ~3-5 tok/s on M4 Air. With DFlash, it achieves ~10-14 tok/s — the difference between unusable and usable.
12. **LM Studio download from China**: Direct CDN (`installers.lmstudio.ai`) times out from China. URL: `https://installers.lmstudio.ai/darwin/arm64/{version}/LM-Studio-{version}-arm64.dmg`. Try `brew install --cask lm-studio` or use a VPN. The DMG is ~539 MB.
13. **`mlx_lm.generate()` rejects temp kwargs**: Passing `temp=` or `temperature=` raises `TypeError`. Always omit temperature parameters:
    ```python
    # Correct
    response = generate(model, tokenizer, prompt=p, max_tokens=200)
    # Wrong — will crash
    response = generate(model, tokenizer, prompt=p, max_tokens=200, temp=0.0)
    ```
14. **First server request loads the model**: The model loads lazily on the first `/v1/chat/completions` request, which can take 15-30s. Pre-warm by calling `/v1/models` first (this does not trigger model loading).

## References

- **[dflash-qwen27b-m4air-20260630.md](references/dflash-qwen27b-m4air-20260630.md)** — Full empirical run (2026-06-30): Qwen3.6-27B-4bit + DFlash on M4 Air 32GB. Observed 14.3–16.1 tok/s (79–86% acceptance) short context, 10.7 tok/s longer gen, server log stats, reasoning_content handling, restart-on-hang procedure, modelscope download + HF cache construction.
- **[model-comparison-coding.md](references/model-comparison-coding.md)** — DeepSeek V4 Flash vs Qwen local comparison data, quantization benchmarks, per-Mac-tier speed estimates
- **[mlx-ecosystem.md](references/mlx-ecosystem.md)** — MLX package overview, version compatibility, Rapid-MLX vs mlx-lm vs LM Studio
- **[opencode-custom-provider.md](references/opencode-custom-provider.md)** — Configuring MLX local model as an OpenCode custom OpenAI-compatible provider (JSON config format, credential setup, troubleshooting)
- **[model-manager.py](templates/model-manager.py)** — Standalone FastAPI web UI for starting/stopping/testing local MLX models via a browser. Drop-in for any model directory.

- **[download-files.py](scripts/download-files.py)** — Individual-file downloader with retries; use when `hf download` times out on large safetensors from China mirrors.

## Resources

- **MLX**: https://github.com/ml-explore/mlx
- **mlx-lm**: https://github.com/ml-explore/mlx-lm
- **mlx-vlm**: https://github.com/Blaizzy/mlx-vlm
- **LM Studio**: https://lmstudio.ai
- **HF Mirrors**: https://hf-mirror.com
- **Qwen3.5-27B**: https://huggingface.co/Qwen/Qwen3.5-27B
- **Qwen3.6-27B**: https://huggingface.co/Qwen/Qwen3.6-27B
