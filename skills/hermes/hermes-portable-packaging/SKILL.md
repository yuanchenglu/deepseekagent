---
name: hermes-portable-packaging
description: Package Hermes Agent for portable USB deployment with self-contained runtimes. Cross-platform startup scripts (macOS/M-series, Intel, Windows, Linux x64/ARM64), correct HERMES_HOME layout, and pitfall avoidance.
version: 1.0.0
tags: [hermes, portable, usb, cross-platform, packaging, deployment]
---

# Hermes Portable Packaging

Package Hermes Agent for zero-install USB deployment — copy folder, double-click, ready to use. Covers the correct directory layout, environment variables, runtime bundling, cross-platform startup scripts, and common pitfalls from real-world deployment.

## When to Use

- Building a portable (USB-friendly) Hermes Agent distribution
- Updating an existing portable deployment for a new Hermes version
- Debugging startup failures in a portable Hermes setup
- Adding cross-platform runtime support to an existing Hermes deployment
- Creating a one-click local installer alongside portable mode

## Architecture

### Directory Layout

```
u-hermes/                          ← Copy entire folder to USB
├── Mac-Start.command              ← macOS double-click launcher
├── Linux-Start.sh                 ← Linux launcher
├── Windows-Start.bat              ← Windows launcher
├── setup.sh                       ← Download runtimes + build venv (first run)
├── install-local.sh / .bat        ← One-click local install via official script
├── .env.template                  ← API key config template
├── config.yaml.template           ← Hermes config template
├── app/
│   ├── core/
│   │   └── .venv.tar.gz           ← Pre-built Hermes Agent venv
│   └── runtime/                   ← Platform runtimes (tar.gz, extracted on first run)
│       ├── python-{platform}.tar.gz
│       └── node-{platform}.tar.gz
├── data/
│   └── .hermes/                   ← HERMES_HOME
│       ├── config.yaml
│       ├── .env
│       ├── workspace/
│       ├── skills/
│       ├── logs/
│       ├── sessions/
│       ├── memories/
│       └── cron/
├── tests/
└── README.md
```

### Environment Variables — The ONLY One You Need

```bash
export HERMES_HOME="$PROJECT_DIR/data/.hermes"
```

**Critical pitfall**: Previous portable attempts invented fake env vars that do NOT exist in Hermes source code. Do NOT set, reference, or test for these:

| Fake Var | Reality |
|----------|---------|
| `HERMES_STATE_DIR` | Does not exist in Hermes source |
| `HERMES_CONFIG_PATH` | Does not exist in Hermes source |
| `HERMES_WEBUI_PORTABLE` | Does not exist in Hermes source |

Source: grep across entire hermes-agent codebase — zero results for all three.

The only official env var is `HERMES_HOME`. Hermes finds everything relative to it.

### Service Architecture — Two Services Only

Start exactly two services. No third-party WebUI, no Socket.io servers:

1. **Gateway** (`hermes gateway run`) — messaging platform integration, port 8642-8670
2. **Dashboard** (`hermes dashboard --host 0.0.0.0`) — web management UI, port 9119-9140

Both ports auto-discover available ports on startup (scan range, pick first free).

## Cross-Platform Runtimes

### Platform Matrix

| Platform | Python Runtime | Node.js Runtime |
|----------|---------------|-----------------|
| macOS Apple Silicon (M1-M4) | `python-mac-arm64` | `node-mac-arm64` |
| macOS Intel | `python-mac-x64` | `node-mac-x64` |
| Linux x64 | `python-linux-x64` | `node-linux-x64` |
| Linux ARM64 | `python-linux-arm64` | `node-linux-arm64` |
| Windows x64 | `python-win-x64` | `node-win-x64` |
| Windows ARM64 | `python-win-x64` (x64 emulation) | `node-win-arm64` |

### Runtime Sources

- Python: [astral-sh/python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases) (use China mirror `https://github.com/astral-sh/python-build-standalone/releases/download` if needed)
- Node.js: Official Node.js mirrors (use `https://npmmirror.com/mirrors/node` for China)

### Runtime Storage

Store as `.tar.gz` files in `app/runtime/`. Extract on first run — never ship extracted directories (too many files for USB filesystems, slow copy).

### exFAT/NTFS Pitfalls

USB drives are often formatted as exFAT or NTFS which don't support symlinks. The Linux startup script must handle:
- Missing `python3` → `python3.11` symlink: copy the binary instead
- Missing `python` → `python3` symlink: copy instead
- Hardcoded venv shebangs: rewrite to `#!/usr/bin/env python3`

## Startup Script Pattern

### Shared Flow (all platforms)

1. Detect CPU architecture (`uname -m` / `PROCESSOR_ARCHITECTURE`)
2. Auto-extract runtimes from tar.gz if not already extracted
3. Auto-extract Hermes Agent venv from tar.gz if not present
4. Create data directories under `HERMES_HOME`
5. Copy config.yaml from template on first run
6. Load `.env` file
7. Set `HERMES_HOME` environment variable
8. Find available ports (scan range, pick first free)
9. Start Gateway in background
10. Start Dashboard in background
11. Wait for services to be ready (health-check with curl/netstat)
12. Open browser to Dashboard
13. Trap cleanup on exit (kill both services)

### Platform-Specific Details

**macOS**:
- Remove quarantine attributes (`xattr -rd com.apple.quarantine`) before running binaries
- Use `sed -i ''` (BSD sed syntax)
- Use `open` to launch browser

**Linux**:
- Use `sed -i` (GNU sed syntax)
- Handle exFAT/NTFS symlink failures (see pitfall above)
- Use `xdg-open` to launch browser

**Windows**:
- Handle UNC paths (reject them, must be local drive)
- Use `netstat -an | findstr` for port checking (no `lsof`)
- Use `start /B` for background processes
- Set `PYTHONUTF8=1` and `chcp 65001` for UTF-8
- Redirect `HOME`, `USERPROFILE`, `APPDATA`, `TEMP` to portable data dir

## One-Click Local Install

Alongside portable mode, provide one-click install scripts that use the official Hermes install method:

```bash
# macOS / Linux
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Windows PowerShell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

After installation, users run `hermes desktop` for the GUI or `hermes` for CLI.

## setup.sh — Build Script

The setup script should:
1. Detect current OS/arch
2. Download Python standalone build for current platform (and optionally all platforms with `--all-platforms`)
3. Download Node.js for current platform (and optionally all)
4. Create venv and pip install `hermes-agent[all]`
5. Package venv as `.venv.tar.gz` (after removing `__pycache__`)
6. Create data directories under `HERMES_HOME`
7. Copy config and env templates

On Windows, the packaged venv should be named `.venv-win.tar.gz` (Windows Scripts/ layout differs from Unix bin/ layout).

## Testing

Tests should verify script content and structure, not rely on running hermess services:

- Check scripts exist and are executable
- Check architecture detection branches exist
- Check HERMES_HOME is set (but don't check for literal `data/.hermes` — the variable may be constructed via shell expansion)
- Check port discovery logic exists
- Check cleanup trap exists
- Check browser launch commands exist
- Verify runtime tar.gz files (not extracted directories) exist for all platforms in `--all-platforms` mode
- Config template has required sections (model, gateway, web, terminal, memory)
- No fake env vars in tests or scripts

Tests should NOT:
- Check for literal strings that only appear via variable expansion (`$DATA_DIR/.hermes` won't match literal `data/.hermes`)
- Require extracted runtimes (check tar.gz instead)
- Require running services (unit test the script content)

## Pitfalls

1. **Fake env vars**: `HERMES_STATE_DIR`, `HERMES_CONFIG_PATH`, `HERMES_WEBUI_PORTABLE` do not exist in Hermes. Never use them.
2. **HERMES_HOME must point to `.hermes/` directory**, not its parent. `data/` is wrong, `data/.hermes/` is correct.
3. **Third-party WebUI**: Do not bundle separate Node.js WebUI servers (Socket.io, etc.). Use Hermes's built-in `hermes dashboard` instead.
4. **BSD vs GNU sed**: macOS uses BSD `sed -i ''`, Linux uses GNU `sed -i`. Wrong syntax silently corrupts files.
5. **exFAT symlinks**: Copy binaries instead of symlinking when deploying to exFAT/NTFS USB drives.
6. **Port range inconsistency**: Keep Gateway and Dashboard port ranges identical across all three startup scripts.
7. **String-matching tests**: Don't test for exact literal strings that come from variable expansion. Test for the variable name itself or the semantic concept.

## Verification

After building:
1. Run `python3 -m pytest tests/ -v` — all tests should pass
2. On macOS: `bash Mac-Start.command` and verify Dashboard opens in browser
3. Check `data/.hermes/` has all subdirectories created
4. Check Gateway health at `http://127.0.0.1:8642/health`
