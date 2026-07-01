#!/bin/bash
# ============================================================================
# DeepAgent WebUI Start/Stop/Status Script
# ============================================================================
# Manages the WebUI server lifecycle.
#
# Usage:
#   ./scripts/start-webui.sh start    — Start WebUI server
#   ./scripts/start-webui.sh stop     — Stop WebUI server
#   ./scripts/start-webui.sh status   — Check server status
#   ./scripts/start-webui.sh restart  — Restart WebUI server
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBUI_DIR="$PROJECT_DIR/webui"
WEBUI_CONFIG_DIR="$HOME/.deepagent-webui"
PID_FILE="$WEBUI_CONFIG_DIR/server.pid"
LOG_FILE="$WEBUI_CONFIG_DIR/server.log"
DEFAULT_PORT=8648

# Force data directory to DeepAgent's own (not ~/.hermes-web-ui)
export HERMES_WEB_UI_HOME="$WEBUI_CONFIG_DIR"
export HERMES_WEBUI_STATE_DIR="$WEBUI_CONFIG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

get_port() {
    if [ -f "$WEBUI_CONFIG_DIR/config.yaml" ]; then
        local port
        port=$(grep '^port:' "$WEBUI_CONFIG_DIR/config.yaml" | awk '{print $2}' | tr -d '[:space:]')
        if [ -n "$port" ]; then
            echo "$port"
            return
        fi
    fi
    echo "$DEFAULT_PORT"
}

is_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

get_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE" 2>/dev/null | tr -d '[:space:]')
        if is_running "$pid"; then
            echo "$pid"
            return
        fi
    fi
    # Try to find by port
    local port
    port=$(get_port)
    local lsof_pid
    lsof_pid=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$lsof_pid" ]; then
        echo "$lsof_pid"
        # Update PID file
        echo "$lsof_pid" > "$PID_FILE" 2>/dev/null || true
    fi
}

cmd_start() {
    echo -e "${CYAN}→${NC} Starting DeepAgent WebUI..."

    local existing_pid
    existing_pid=$(get_pid)
    if [ -n "$existing_pid" ] && is_running "$existing_pid"; then
        echo -e "${YELLOW}⚠${NC} WebUI is already running (PID: $existing_pid)"
        local port
        port=$(get_port)
        echo "  http://localhost:$port"
        exit 0
    fi

    # Verify webui directory
    if [ ! -f "$WEBUI_DIR/bin/hermes-web-ui.mjs" ]; then
        echo -e "${RED}✗${NC} WebUI not built. Run setup-webui.sh first."
        exit 1
    fi

    mkdir -p "$WEBUI_CONFIG_DIR"

    local port
    port=$(get_port)

    # Start with nohup
    cd "$WEBUI_DIR"

    # Use node directly to run the bin script
    nohup node bin/hermes-web-ui.mjs start --port "$port" \
        >> "$LOG_FILE" 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait for server to become ready
    echo -e "  ${CYAN}Waiting for server to start...${NC}"
    local waited=0
    local max_wait=30
    while [ $waited -lt $max_wait ]; do
        if ! is_running "$pid"; then
            echo -e "  ${RED}✗${NC} Process died during startup"
            echo "    Check log: $LOG_FILE"
            tail -20 "$LOG_FILE"
            exit 1
        fi
        if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} WebUI started successfully (PID: $pid)"
            echo ""
            echo "    Access: http://localhost:$port"
            echo "    Login:  admin / 123456"
            echo "    Log:    $LOG_FILE"
            exit 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    echo -e "  ${YELLOW}⚠${NC} Server started but health check timed out after ${max_wait}s"
    echo "    PID: $pid"
    echo "    Log: $LOG_FILE"
    echo "    Access: http://localhost:$port"
}

cmd_stop() {
    local pid
    pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo -e "${YELLOW}⚠${NC} WebUI is not running"
        return
    fi

    echo -e "${CYAN}→${NC} Stopping WebUI (PID: $pid)..."
    kill "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    local waited=0
    while is_running "$pid" && [ $waited -lt 10 ]; do
        sleep 1
        waited=$((waited + 1))
    done

    if is_running "$pid"; then
        echo -e "  ${YELLOW}⚠${NC} Force killing..."
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo -e "  ${GREEN}✓${NC} WebUI stopped"
}

cmd_status() {
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ] && is_running "$pid"; then
        local port
        port=$(get_port)
        echo -e "${GREEN}✓${NC} WebUI is running"
        echo "  PID:    $pid"
        echo "  Port:   $port"
        echo "  URL:    http://localhost:$port"
        echo "  Log:    $LOG_FILE"
    else
        echo -e "${YELLOW}⚠${NC} WebUI is not running"
    fi
}

cmd_restart() {
    cmd_stop
    sleep 1
    cmd_start
}

# Main command dispatch
ACTION="${1:-help}"

case "$ACTION" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    restart)
        cmd_restart
        ;;
    help|*)
        echo "DeepAgent WebUI Manager"
        echo ""
        echo "Usage:"
        echo "  $0 start      Start WebUI server"
        echo "  $0 stop       Stop WebUI server"
        echo "  $0 status     Check server status"
        echo "  $0 restart    Restart server"
        echo "  $0 help       Show this help"
        ;;
esac
