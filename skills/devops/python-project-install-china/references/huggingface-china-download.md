# HuggingFace Model Download in China

When `hf download` fails with `SSL: UNEXPECTED_EOF_WHILE_READING` (GFW SNI blocking), use `git clone` via HF mirror instead.

## The Winning Pattern

```bash
# Clone metadata + configs only (skip giant model weights)
GIT_LFS_SKIP_SMUDGE=1 git clone https://hf-mirror.com/ORG/REPO

# For full download including weights (WARNING: check sizes first!)
cd REPO && git lfs pull
```

## Why This Works When `hf download` Doesn't

- `hf download` uses Python `httpx` → TLS handshake hits SNI block
- `git clone` uses libcurl/git's TLS stack → sometimes routes differently through GFW
- `hf-mirror.com` serves git protocol, redirects to `huggingface.co` transparently

## Pre-Download Size Check

Before attempting to download LFS objects (model weights), always estimate disk needs:

```bash
cd REPO
git lfs ls-files -s | python3 -c "
import sys, re
total = 0
for line in sys.stdin:
    m = re.search(r'\((.*?)\)$', line.strip())
    if m:
        sz = m.group(1).split()
        if len(sz) >= 2:
            val, unit = float(sz[0]), sz[1]
            total += val * {'GB': 1e9, 'MB': 1e6, 'KB': 1e3, 'B': 1}.get(unit, 1)
print(f'Total LFS: {total/1e9:.1f} GB')
"
```

## DeepSeek V4 Model Sizes (reference)

| Model | LFS Size | Notes |
|-------|----------|-------|
| DeepSeek-V4-Pro | ~872 GB | 64 shards, most ~14 GB each |
| DeepSeek-V4-Flash | ~161 GB | Smaller MoE, fits most external drives |
| DeepSeek-V4-Pro-Base | ~1,620 GB | Base model, no instruct tuning |
| DeepSeek-V4-Flash-Base | ~295 GB | Flash base variant |

## Clarifying User Intent

When a user asks to "下载/克隆 HuggingFace 仓库" from China:
1. **Ask if they need model weights or just source code/configs.** Most users analyzing architecture only need the small files.
2. The small files (configs, inference code, tokenizer) are typically < 50 MB total
3. Model weights (`.safetensors` LFS objects) can be hundreds of GB

## CLI Status

- `huggingface-cli` — **DEPRECATED**. Use `hf` instead.
- `hf` — modern CLI, install via `curl -LsSf https://hf.co/cli/install.sh | bash -s`
- `git-lfs` — required for `git clone` approach: `sudo apt-get install git-lfs && git lfs install`

## Finding External Drives

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,LABEL,MODEL
df -h | grep -v "loop\|tmpfs\|overlay"
```
