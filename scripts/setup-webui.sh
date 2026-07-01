#!/bin/bash
# ============================================================================
# DeepAgent WebUI Setup Script
# ============================================================================
# Sets up the WebUI as the default workbench for DeepAgent.
# Called by setup-deepagent.sh during normal installation.
#
# Usage:
#   ./scripts/setup-webui.sh
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBUI_DIR="$PROJECT_DIR/webui"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN}═══ DeepAgent WebUI Setup ═══${NC}"
echo ""

# ============================================================================
# 1. Check Node.js / npm
# ============================================================================

echo -e "${CYAN}→${NC} Checking Node.js..."

NODE_CMD=""
if command -v node &> /dev/null; then
    NODE_CMD="node"
elif [ -x "$HOME/.hermes/node/bin/node" ]; then
    NODE_CMD="$HOME/.hermes/node/bin/node"
    export PATH="$HOME/.hermes/node/bin:$PATH"
fi

if [ -z "$NODE_CMD" ]; then
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 23+ first."
    echo "  Recommended: https://nodejs.org or use your package manager."
    exit 1
fi

NODE_VERSION=$($NODE_CMD --version)
echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"

NPM_CMD=""
if command -v npm &> /dev/null; then
    NPM_CMD="npm"
elif [ -x "$(dirname "$NODE_CMD")/npm" ]; then
    NPM_CMD="$(dirname "$NODE_CMD")/npm"
fi

if [ -z "$NPM_CMD" ]; then
    echo -e "${RED}✗${NC} npm not found alongside Node.js."
    exit 1
fi

# Check Node version >= 23
NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 23 ]; then
    echo -e "${YELLOW}⚠${NC} Node.js $NODE_VERSION detected. WebUI requires Node.js 23+."
    echo "  Continuing anyway — build may fail."
fi

# ============================================================================
# 2. Verify webui directory
# ============================================================================

echo -e "${CYAN}→${NC} Checking webui directory..."

if [ ! -d "$WEBUI_DIR" ]; then
    echo -e "${YELLOW}⚠${NC} webui/ directory not found. Cloning from GitHub..."
    git clone --depth 1 https://github.com/EKKOLearnAI/hermes-web-ui.git "$WEBUI_DIR"
fi

if [ ! -f "$WEBUI_DIR/package.json" ]; then
    echo -e "${RED}✗${NC} webui/package.json not found. Clone may have failed."
    exit 1
fi

echo -e "${GREEN}✓${NC} webui/ directory ready"

# ============================================================================
# 3. npm install
# ============================================================================

echo -e "${CYAN}→${NC} Installing dependencies (npm install)..."
cd "$WEBUI_DIR"
$NPM_CMD install --no-audit --no-fund 2>&1 | tail -5
echo -e "${GREEN}✓${NC} Dependencies installed"

# ============================================================================
# 4. npm run build
# ============================================================================

echo -e "${CYAN}→${NC} Building webui (npm run build)..."
$NPM_CMD run build 2>&1 | tail -10
echo -e "${GREEN}✓${NC} WebUI built successfully"

# ============================================================================
# 5. Create configuration directory
# ============================================================================

echo -e "${CYAN}→${NC} Creating WebUI configuration..."

WEBUI_CONFIG_DIR="$HOME/.deepagent-webui"
mkdir -p "$WEBUI_CONFIG_DIR"

# Write default config
cat > "$WEBUI_CONFIG_DIR/config.yaml" << 'CONFEOF'
# DeepAgent WebUI Configuration
# Data directory: ~/.deepagent-webui/
port: 8648
webui_dir: ./webui
agent_bridge:
  enabled: true
  socket_path: /tmp/deepagent-ipc.sock
  auto_connect: true
auth:
  default_username: admin
  default_password: "123456"
CONFEOF

echo -e "${GREEN}✓${NC} Config written to $WEBUI_CONFIG_DIR/config.yaml"

# ============================================================================
# 6. Create DeepAgent config integration
# ============================================================================

DEEPAGENT_CONFIG_DIR="$HOME/.deepagent"
mkdir -p "$DEEPAGENT_CONFIG_DIR"

WEBUI_CONFIG_REF="$DEEPAGENT_CONFIG_DIR/webui-config.yaml"
if [ ! -f "$WEBUI_CONFIG_REF" ]; then
    cat > "$WEBUI_CONFIG_REF" << 'REFEOF'
# DeepAgent WebUI reference config
# This file is created by setup-webui.sh
webui:
  enabled: true
  port: 8648
  data_dir: ~/.deepagent-webui/
  install_dir: ./webui
REFEOF
    echo -e "${GREEN}✓${NC} Reference config created at $WEBUI_CONFIG_REF"
else
    echo -e "${GREEN}✓${NC} Reference config exists"
fi

# ============================================================================
# Done
# ============================================================================

echo ""
echo -e "${GREEN}✓ WebUI setup complete!${NC}"
echo ""
echo "  Start WebUI:    deepagent webui start"
echo "  Check status:   deepagent webui status"
echo "  Stop WebUI:     deepagent webui stop"
echo "  Access URL:     http://localhost:8648"
echo ""
echo "  Default login:  admin / 123456"
echo ""
