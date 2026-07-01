#!/bin/bash
set -e

echo "=== Deep Agent Embedded OpenCode Setup ==="

EMBEDDED_DIR="$(cd "$(dirname "$0")/.." && pwd)/embedded"
OPENCODE_DIR="$EMBEDDED_DIR/opencode"

if [ -d "$OPENCODE_DIR" ]; then
    echo "OpenCode already exists at $OPENCODE_DIR"
    echo "To re-clone: rm -rf $OPENCODE_DIR && re-run this script"
    exit 0
fi

echo "Cloning a clean OpenCode into embedded/opencode ..."
# TODO: replace with actual OpenCode repo once decided
git clone --depth 1 https://github.com/your-org/opencode.git "$OPENCODE_DIR" || {
    echo "Clone failed. Creating placeholder structure instead."
    mkdir -p "$OPENCODE_DIR"
}

echo "Creating isolated config..."
mkdir -p "$EMBEDDED_DIR/config"
mkdir -p "$EMBEDDED_DIR/workspace"

cat > "$EMBEDDED_DIR/config/opencode-config.yaml" << 'EOF'
# DeepAgent Embedded OpenCode Configuration
# This is completely separate from any user OpenCode installation.

model: deepseek-v4-flash
workspace: ../workspace
skills_dir: ../skills
isolation: true
EOF

echo "Setup complete. Run with: embedded/start.sh"