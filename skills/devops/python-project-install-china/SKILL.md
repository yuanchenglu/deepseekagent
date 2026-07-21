---
name: python-project-install-china
description: Install Python projects from GitHub in China with network troubleshooting, dependency conflict resolution, and mirror configuration.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, pip, china, mirror, network, dependency-conflict, installation]
    related_skills: [github-repo-management]
---

# Python Project Installation in China

Installing Python projects from GitHub when facing network issues, SSL errors, and dependency conflicts common in China.

## Common Issues & Solutions

### 1. Repository Migration

GitHub repos may move. Check if the original repo redirects or has moved:

```bash
# Try cloning, if it shows "moved" message, use new URL
git clone https://github.com/old-owner/old-repo.git
# If redirected or archived, use the new official repo:
git clone https://github.com/new-owner/new-repo.git
```

### 2. Virtual Environment Setup

```bash
# Create venv with pip included
python3 -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Verify pip exists
ls .venv/bin/pip  # Should exist
```

**Note:** `uv venv` may create venv without pip. Use standard `python3 -m venv` for compatibility.

**If pip is missing after uv venv:**
```bash
# Recreate with standard venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
# Now pip should exist
which pip  # Should show .venv/bin/pip
```

### 3. Network/SSL Issues with PyPI

**Problem:** `SSLError`, `tls handshake eof`, timeouts

**Solution:** Use Tsinghua University mirror (清华镜像源)

```bash
# Install with mirror
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Alternative mirrors:
# Alibaba: https://mirrors.aliyun.com/pypi/simple/
# Tencent: https://mirrors.cloud.tencent.com/pypi/simple/
# Douban: https://pypi.doubanio.com/simple/
```

### 4. Dependency Conflicts

**Common conflict:** Pillow version mismatch

```
ERROR: Cannot install pillow~=11.1.0 because crawl4ai depends on pillow~=10.4
```

**Solution:** Edit requirements.txt to use compatible version:

```bash
# Check which package needs the lower version
pip install --no-deps -r requirements.txt  # See what fails

# Edit conflicting line in requirements.txt
# Change: pillow~=11.1.0
# To:     pillow~=10.4

# Or use sed to patch automatically
sed -i 's/pillow~=11.1.0/pillow~=10.4/' requirements.txt
```

**Common conflicting packages:**
- `pillow`: browsergym, crawl4ai, libvisualwebarena often require ~10.4
- `numpy`: deep learning packages may require specific versions
- `torch`: check CUDA compatibility before installing

### 5. Large Package Timeouts

**Problem:** torch, nvidia-cudnn, pytorch packages timeout

**Solutions:**
- Use `--timeout 300` flag
- Install packages individually
- Use `--no-deps` then install deps separately
- Use conda for heavy ML packages instead

### 6. Playwright Browser Installation

```bash
# Install chromium only (smaller than full install)
playwright install chromium

# If timeout, increase Node network timeout
PLAYWRIGHT_DOWNLOAD_TIMEOUT=120000 playwright install chromium
```

## Complete Installation Workflow

```bash
# 1. Clone repo
# If direct clone fails due to SSL issues, see github-access-troubleshoot-china skill
git clone https://github.com/owner/project.git || \
git clone https://ghproxy.com/https://github.com/owner/project.git
cd project

# 2. Create venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Check requirements for version conflicts
# Look for: pillow, numpy, torch, etc. with strict pins

# 4. Install with mirror
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. If dependency conflict, edit requirements.txt
# Then retry

# 6. Install browsers if needed
playwright install chromium

# 7. Copy config template
cp config/config.example.toml config/config.toml

# 8. Test import
python -c "import app; print('Success!')"
```

## HuggingFace Model Downloads in China
## HuggingFace Model Downloads in China

`hf download` often fails with `SSL: UNEXPECTED_EOF_WHILE_READING` (GFW SNI blocking). Use the `git clone` pattern via HF mirror instead. See `references/huggingface-china-download.md` for detailed recipes including:
- `GIT_LFS_SKIP_SMUDGE=1 git clone https://hf-mirror.com/ORG/REPO` — metadata-only clone
- Estimating LFS sizes before downloading weights: `git lfs ls-files -s`
- Clarifying user intent (source code vs model weights)

### ModelScope Alternative (推荐)

Many Chinese AI projects (e.g. VoxCPM, Qwen, ChatGLM) officially support ModelScope, which is hosted in China and much faster than HuggingFace mirrors. Check the project README for `modelscope.cn` links — if present, prefer this path.

```bash
pip install modelscope
```

```python
from modelscope import snapshot_download
snapshot_download("ORG/MODEL_NAME", local_dir='./pretrained_models/MODEL')

# Then point from_pretrained to the local dir
model = SomeModel.from_pretrained('./pretrained_models/MODEL')
```

**When to choose ModelScope vs HuggingFace mirror:**
- ModelScope: project README mentions ModelScope, download is >1GB, or HuggingFace mirror is slow/blocked
- HuggingFace mirror: project is HF-only, small model, or need specific revision/branch
- ModelScope snapshot_download downloads all files in parallel, handles retries, and is generally 2-5x faster from China

**Pitfall:** ModelScope and HuggingFace model IDs may differ. Always use the exact ID from the project README, not a guess.

## GitHub Release Binary & npm Downloads in China

DNS poisoning blocks release asset CDNs (`release-assets.githubusercontent.com`, `*.blob.core.windows.net` → 127.0.0.1). For npm projects needing binary downloads (Playwright, CamoFox, etc.), see `references/china-dns-poisoning-workarounds.md` for detection, /etc/hosts workaround, cross-machine transfer, and npm mirror tactics.

### Quick npm install in China
```bash
npm install --registry=https://registry.npmmirror.com
```
For packages with postinstall binary downloads (skip download, fetch manually after fixing DNS):
```bash
CAMOFOX_SKIP_DOWNLOAD=1 npm install --registry=https://registry.npmmirror.com
# Then fix DNS and run the fetch command manually
```

## Troubleshooting Network Issues

If `git clone` fails with SSL errors:
- See `github-access-troubleshoot-china` skill for comprehensive solutions
- Common fix: Check router SSR Plus run_mode (should be 'router', not 'gfwlist')

## Quick Fixes Table

| Issue | Quick Fix |
|-------|-----------|
| SSL/TLS error | Use `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| No pip in venv | Use `python3 -m venv` not `uv venv` |
| Pillow conflict | Change to `pillow~=10.4` in requirements.txt |
| Timeout on large packages | Add `--timeout 300` or use `--no-deps` |
| Playwright download fail | Set `PLAYWRIGHT_DOWNLOAD_TIMEOUT=120000` |
| HuggingFace model download fail | Try ModelScope: `snapshot_download("ORG/MODEL", local_dir='./dir')` |

## Environment Variables

```bash
# Increase pip timeout
export PIP_DEFAULT_TIMEOUT=300

# Use mirror permanently
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Playwright download timeout
export PLAYWRIGHT_DOWNLOAD_TIMEOUT=120000
```
