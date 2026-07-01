#!/bin/bash
set -e

echo "=== Deep Agent Embedded OpenCode Setup ==="

EMBEDDED_DIR="$(cd "$(dirname "$0")/.." && pwd)/embedded"
ARM64_DIR="$EMBEDDED_DIR/opencode/macos-arm64"
X64_DIR="$EMBEDDED_DIR/opencode/macos-x64"
CONFIG_DIR="$EMBEDDED_DIR/config"
WORKSPACE_DIR="$EMBEDDED_DIR/workspace"

# Check for existing binary
ARM64_BIN="$ARM64_DIR/opencode"
X64_BIN="$X64_DIR/opencode"

ARM64_OK=false
X64_OK=false

if [ -f "$ARM64_BIN" ] && [ -x "$ARM64_BIN" ]; then
    ARM64_VER=$("$ARM64_BIN" --version 2>/dev/null || echo "unknown")
    echo "[OK] arm64 binary found: $ARM64_BIN (version $ARM64_VER)"
    ARM64_OK=true
fi

if [ -f "$X64_BIN" ] && [ -x "$X64_BIN" ]; then
    X64_VER=$("$X64_BIN" --version 2>/dev/null || echo "unknown")
    echo "[OK] x86_64 binary found: $X64_BIN (version $X64_VER)"
    X64_OK=true
fi

if $ARM64_OK && $X64_OK; then
    echo ""
    echo "Both binaries already installed. Skipping download."
    echo "To re-download: rm -rf $EMBEDDED_DIR/opencode && re-run this script"
    echo ""
    # Still ensure config exists
    mkdir -p "$CONFIG_DIR" "$WORKSPACE_DIR"
    if [ ! -f "$CONFIG_DIR/opencode-config.yaml" ]; then
        cat > "$CONFIG_DIR/opencode-config.yaml" << 'EOF'
# DeepAgent Embedded OpenCode Configuration
# This is completely separate from any user OpenCode installation.

model: deepseek-v4-flash
workspace: ../workspace
skills_dir: ../skills
isolation: true
EOF
        echo "Created default config."
    fi
    echo "Setup complete. Run with: embedded/start.sh"
    exit 0
fi

echo ""
echo "Downloading OpenCode macOS binaries..."

mkdir -p "$ARM64_DIR" "$X64_DIR" "$CONFIG_DIR" "$WORKSPACE_DIR"

# Detect architecture
ARCH=$(uname -m)

# Fetch latest release version from GitHub API
echo "Fetching latest release info..."
LATEST=$(curl -sL "https://api.github.com/repos/anomalyco/opencode/releases/latest" | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])" 2>/dev/null || echo "v1.17.13")
echo "Latest version: $LATEST"

download_binary() {
    local target_arch="$1"  # "arm64" or "x64"
    local dest_dir="$2"
    local zip_name="opencode-darwin-${target_arch}.zip"
    local url="https://github.com/anomalyco/opencode/releases/download/${LATEST}/${zip_name}"
    local tmp_zip="/tmp/${zip_name}"

    echo "Downloading ${zip_name}..."
    curl -L "$url" -o "$tmp_zip"
    echo "Extracting..."
    unzip -o "$tmp_zip" -d "$dest_dir/"
    chmod +x "$dest_dir/opencode"
    local ver=$("$dest_dir/opencode" --version 2>/dev/null || echo "unknown")
    echo "Installed: $dest_dir/opencode (version $ver)"
    rm -f "$tmp_zip"
}

# Always download both for completeness
download_binary "arm64" "$ARM64_DIR"
download_binary "x64" "$X64_DIR"

echo ""
echo "Creating isolated config..."
if [ ! -f "$CONFIG_DIR/opencode-config.yaml" ]; then
    cat > "$CONFIG_DIR/opencode-config.yaml" << 'EOF'
# DeepAgent Embedded OpenCode Configuration
# This is completely separate from any user OpenCode installation.

model: deepseek-v4-flash
workspace: ../workspace
skills_dir: ../skills
isolation: true
EOF
fi

echo ""
echo "=== Setup Complete ==="
echo "  arm64  binary: $ARM64_DIR/opencode"
echo "  x86_64 binary: $X64_DIR/opencode"
echo "  config:        $CONFIG_DIR/opencode-config.yaml"
echo ""
echo "Run with: embedded/start.sh"
