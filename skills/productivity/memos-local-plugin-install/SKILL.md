---
name: memos-local-plugin-install
description: Install MemOS Local Plugin (Reflect2Evolve memory system) for Hermes Agent from GitHub source when npm package is not yet published. Handles tarball creation, dependency installation with --ignore-scripts, and Hermes adapter configuration.
triggers:
  - Install MemOS Local Plugin
  - Setup memos-local-plugin for Hermes
  - Install MemOS memory plugin from GitHub
  - memos-local-plugin npm install fails
  - onnxruntime-node timeout during install
---

# MemOS Local Plugin Installation

## Overview

Install MemOS Local Plugin (Reflect2Evolve V7 memory system) for Hermes Agent. This skill handles installation from GitHub source when the npm package `@memtensor/memos-local-plugin` is not yet published or unavailable.

## What is MemOS Local Plugin

A local-first, file-backed memory system that gives an AI agent four cooperating layers of memory:
- **L1 trace** — step-level grounded records (action + observation + reflection + value)
- **L2 policy** — sub-task strategies induced across many traces
- **L3 world model** — compressed environmental cognition derived from L2 + L1
- **Skill** — callable, crystallized capabilities the agent can invoke directly

## Prerequisites

- Node.js >= 20.0.0
- Hermes Agent installed (`~/.hermes/` exists)
- Git (to clone the repository)

## Installation Steps

### Step 1: Clone Repository and Create Tarball

```bash
cd /tmp
rm -rf MemOS
git clone --depth 1 https://github.com/MemTensor/MemOS.git
cd MemOS/apps/memos-local-plugin
npm pack
```

This creates `memtensor-memos-local-plugin-2.0.0-beta.1.tgz` in the current directory.

### Step 2: Deploy to Hermes Plugin Directory

```bash
# Set paths
PLUGIN_DIR="$HOME/.hermes/memos-plugin"
TARBALL="/tmp/MemOS/apps/memos-local-plugin/memtensor-memos-local-plugin-2.0.0-beta.1.tgz"

# Clean old installation
rm -rf "$PLUGIN_DIR"
mkdir -p "$PLUGIN_DIR"

# Extract tarball
tar xzf "$TARBALL" -C "$PLUGIN_DIR" --strip-components=1
```

### Step 3: Install Dependencies (CRITICAL WORKAROUND)

**Problem**: `onnxruntime-node` has a postinstall script that downloads large CUDA files (~500MB+), causing timeouts.

**Solution**: Use `--ignore-scripts` flag:

```bash
cd "$PLUGIN_DIR"
MEMOS_SKIP_SETUP=1 npm install --omit=dev --no-fund --no-audit --loglevel=error --ignore-scripts
```

**Why this works**: The plugin doesn't actually need onnxruntime for Hermes adapter functionality. The `--ignore-scripts` flag skips the problematic postinstall script.

### Step 4: Rebuild Native Dependencies

```bash
cd "$PLUGIN_DIR"
npm rebuild better-sqlite3 --loglevel=error

# Verify it loads
node -e "require('better-sqlite3')" && echo "✓ better-sqlite3 OK"
```

### Step 5: Create Runtime Directories

```bash
mkdir -p "$PLUGIN_DIR/data"
mkdir -p "$PLUGIN_DIR/skills"
mkdir -p "$PLUGIN_DIR/logs"
mkdir -p "$PLUGIN_DIR/daemon"
chmod 700 "$PLUGIN_DIR"
```

### Step 6: Configure Plugin

Copy template config and set permissions:

```bash
cp "$PLUGIN_DIR/templates/config.hermes.yaml" "$PLUGIN_DIR/config.yaml"
chmod 600 "$PLUGIN_DIR/config.yaml"
```

Edit `~/.hermes/memos-plugin/config.yaml` to add your API keys:

```yaml
version: 1

viewer:
  port: 18799

embedding:
  provider: openai_compatible
  baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  apiKey: "YOUR_BAILIAN_API_KEY"
  model: "text-embedding-v3"

llm:
  provider: openai_compatible
  baseUrl: "https://coding.dashscope.aliyuncs.com/v1"
  apiKey: "YOUR_CODINGPLAN_API_KEY"
  model: "glm-5"

hub:
  enabled: false
  address: ""
  teamToken: ""
  userToken: ""

telemetry:
  enabled: true

logging:
  level: info
```

**Note on API Configuration**: The plugin supports using different API providers for LLM and embedding:
- **LLM**: Can use CodingPlan (e.g., `glm-5` via `coding.dashscope.aliyuncs.com`)
- **Embedding**: Requires Bailian API (e.g., `text-embedding-v3` via `dashscope.aliyuncs.com`)
- Both use `openai_compatible` provider type with their respective base URLs

### Step 7: Setup Hermes Adapter

```bash
PLUGIN_DIR="$HOME/.hermes/memos-plugin"
ADAPTER_DIR="$PLUGIN_DIR/adapters/hermes"
MEM_PLUGIN_DIR="$HOME/.hermes/hermes-agent/plugins/memory"
PYTHON_BIN="$HOME/.hermes/hermes-agent/venv/bin/python3"

# Record bridge path
echo "$PLUGIN_DIR/bridge.cts" > "$ADAPTER_DIR/bridge_path.txt"

# Create symlink for memtensor provider
ln -sf "$ADAPTER_DIR/memos_provider" "$MEM_PLUGIN_DIR/memtensor"

# Copy plugin.yaml
cp "$ADAPTER_DIR/plugin.yaml" "$ADAPTER_DIR/memos_provider/plugin.yaml"

# Verify provider loads
$PYTHON_BIN -c "from plugins.memory import load_memory_provider; p = load_memory_provider('memtensor'); print(f'✓ Provider loaded: {p.name}')"
```

### Step 8: Update Hermes Config

Add to `~/.hermes/config.yaml`:

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: memtensor
```

## Verification

Check installation:

```bash
# Check plugin directory
ls -la ~/.hermes/memos-plugin/

# Check config
cat ~/.hermes/memos-plugin/config.yaml

# Check symlink
ls -la ~/.hermes/hermes-agent/plugins/memory/memtensor

# Check provider loads
source ~/.hermes/hermes-agent/venv/bin/activate
python -c "from plugins.memory import load_memory_provider; p = load_memory_provider('memtensor'); print(f'✓ {p.name} ready')"

# Check Hermes config
grep -A5 "memory:" ~/.hermes/config.yaml
```

## Troubleshooting

### Issue: npm install times out on onnxruntime-node

**Symptoms**: Installation hangs at "Downloading onnxruntime-linux-x64-gpu-1.21.0.tgz"

**Solution**: Use `--ignore-scripts` flag:
```bash
npm install --omit=dev --ignore-scripts
```

### Issue: better-sqlite3 fails to load

**Symptoms**: `Error: Cannot find module 'better-sqlite3'`

**Solution**: Rebuild native module:
```bash
cd ~/.hermes/memos-plugin
npm rebuild better-sqlite3
```

### Issue: Provider not found

**Symptoms**: `load_memory_provider('memtensor')` returns None

**Solution**: Check symlink exists:
```bash
ls -la ~/.hermes/hermes-agent/plugins/memory/memtensor
# Should point to: ~/.hermes/memos-plugin/adapters/hermes/memos_provider
```

### Issue: Permission denied on config.yaml

**Solution**: Set correct permissions:
```bash
chmod 600 ~/.hermes/memos-plugin/config.yaml
```

## Key Learnings

1. **npm --ignore-scripts is critical**: The onnxruntime-node package has a postinstall script that downloads large CUDA binaries, causing timeouts. Using `--ignore-scripts` skips this without breaking functionality.

2. **Dual API configuration**: LLM and embedding can use different API providers. For example, use CodingPlan (coding.dashscope.aliyuncs.com) for LLM and Bailian API (dashscope.aliyuncs.com) for embedding. Both use `openai_compatible` provider type.

3. **System Python vs venv**: The Hermes adapter uses the venv Python (`~/.hermes/hermes-agent/venv/bin/python3`), not system Python.

4. **Symlink for provider discovery**: Hermes discovers memory providers via symlinks in `plugins/memory/`. The symlink must point to the adapter's memos_provider directory.

5. **Config separation**: Plugin config lives in `~/.hermes/memos-plugin/config.yaml` (YAML format), while Hermes config is in `~/.hermes/config.yaml`.

6. **Runtime directories**: The plugin expects `data/`, `skills/`, `logs/`, and `daemon/` directories to exist under the plugin home.

## Post-Installation

After installation, the memory system activates automatically when you start Hermes:

```bash
hermes chat
```

The Memory Viewer will be available at http://127.0.0.1:18799/ once the plugin initializes.

## Files and Directories

| Path | Purpose |
|------|---------|
| `~/.hermes/memos-plugin/` | Plugin code and runtime |
| `~/.hermes/memos-plugin/config.yaml` | Plugin configuration (API keys) |
| `~/.hermes/memos-plugin/data/` | SQLite database (L1/L2/L3/Skills) |
| `~/.hermes/memos-plugin/skills/` | Crystallized skill packages |
| `~/.hermes/memos-plugin/logs/` | Rotating logs |
| `~/.hermes/hermes-agent/plugins/memory/memtensor` | Symlink to adapter |

## References

- GitHub: https://github.com/MemTensor/MemOS/tree/main/apps/memos-local-plugin
- Documentation: `~/.hermes/memos-plugin/docs/`
- Architecture: `~/.hermes/memos-plugin/ARCHITECTURE.md`
