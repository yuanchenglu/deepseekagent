#!/usr/bin/env bash
# ===========================================================================
# package-electron.sh — Build Deep Agent WebUI as a standalone Electron app
# ===========================================================================
#
# This script packages the webui/ directory into a desktop application using
# electron-builder. It produces platform-specific installers in
# webui/dist/electron-output/.
#
# Prerequisites:
#   - Node.js >= 23.0.0
#   - npm
#
# Usage:
#   ./scripts/package-electron.sh              # Build for current platform
#   ./scripts/package-electron.sh --mac        # macOS only
#   ./scripts/package-electron.sh --linux      # Linux only
#   ./scripts/package-electron.sh --all        # All platforms (macOS + Linux)
#
# Output directory: webui/dist/electron-output/
#
# See also:
#   webui/electron/electron-builder.config.js
#   webui/electron/main.js
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBUI_DIR="$PROJECT_DIR/webui"

echo "==> Deep Agent — Electron Packaging Script"
echo "    Project root: $PROJECT_DIR"
echo "    WebUI dir:    $WEBUI_DIR"
echo ""

# ---- Validate environment ----
if ! command -v node &>/dev/null; then
  echo "[ERROR] Node.js is required but not found in PATH."
  exit 1
fi

NODE_MAJOR=$(node -e "console.log(process.versions.node.split('.')[0])")
if [ "$NODE_MAJOR" -lt 23 ]; then
  echo "[WARN] Node.js >= 23 recommended (found v$(node -v)). The build may still work."
fi

# ---- 1. Install electron & electron-builder in webui/ if not already present ----
cd "$WEBUI_DIR"

if ! npx --yes electron-builder --version &>/dev/null; then
  echo "[1/4] Installing electron and electron-builder..."
  npm install --save-dev electron electron-builder 2>&1 | tail -3
else
  echo "[1/4] electron-builder already available."
fi

# ---- 2. Build webui dist (client + server) ----
echo "[2/4] Building webui (npm run build)..."
npm run build 2>&1 | tail -5
echo "      Build complete."

# ---- 3. Run electron-builder ----
echo "[3/4] Running electron-builder..."
BUILD_ARGS=("--config" "electron/electron-builder.config.js")

if [ $# -gt 0 ]; then
  # Pass platform flags through
  case "$1" in
    --mac|--macos)  BUILD_ARGS+=("--mac") ;;
    --linux)        BUILD_ARGS+=("--linux") ;;
    --all)          BUILD_ARGS+=("--mac" "--linux") ;;
    *)              echo "[ERROR] Unknown platform: $1. Use --mac, --linux, or --all."
                    exit 1 ;;
  esac
fi

npx electron-builder "${BUILD_ARGS[@]}" 2>&1

# ---- 4. Report results ----
OUTPUT_DIR="$WEBUI_DIR/dist/electron-output"
echo ""
echo "[4/4] Done!"
echo "      Output artifacts:"
if [ -d "$OUTPUT_DIR" ]; then
  ls -lh "$OUTPUT_DIR"
else
  echo "      (Output directory not found — check logs above)"
fi
echo ""
echo "==> Packaging complete."
