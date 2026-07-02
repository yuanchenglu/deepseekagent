#!/bin/bash
# ============================================================
# DeepAgent 嵌入式研发小组启动入口
#
# 用法:
#   ./start.sh                    — 启动隔离研发环境（占位）
#   ./start.sh run-task <指令>    — 直接执行一个研发任务
#   ./start.sh list               — 列出已完成任务
#
# 隔离原则:
#   - 所有操作限制在 embedded/ 目录下
#   - 不访问 ~/.config/opencode 或 ~/.opencode
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---- 检测架构并选择对应的 OpenCode 二进制 ----
ARCH="$(uname -m)"
case "$ARCH" in
    arm64|aarch64)  OPENCODE_BIN="$SCRIPT_DIR/opencode/macos-arm64/opencode" ;;
    x86_64|amd64)   OPENCODE_BIN="$SCRIPT_DIR/opencode/macos-x64/opencode" ;;
    *)              echo "[DeepAgent] Unsupported architecture: $ARCH"; exit 1 ;;
esac

if [ ! -x "$OPENCODE_BIN" ]; then
    echo "[DeepAgent] OpenCode binary not found at $OPENCODE_BIN"
    echo "[DeepAgent] Run scripts/setup-embedded-opencode.sh to install"
    exit 1
fi

ACTION="${1:-help}"

case "$ACTION" in
    run-task)
        shift
        TASK_DESC="$*"
        echo "[DeepAgent Embedded] Running task: ${TASK_DESC:0:80}..."
        echo "[DeepAgent Embedded] Invoking isolated OpenCode..."
        # 直接调用隔离的 OpenCode 二进制，不经过 run_task.sh
        # OPENCODE_CONFIG_DIR 确保不会使用用户本地的 ~/.config/opencode
        OPENCODE_CONFIG_DIR="$SCRIPT_DIR/config" \
            "$OPENCODE_BIN" \
            run "$TASK_DESC"
        ;;

    list)
        echo "[DeepAgent Embedded] Completed tasks:"
        ls -1 "$SCRIPT_DIR/workspace/task_"*.json 2>/dev/null || echo "(none)"
        ;;

    start|up)
        echo "[DeepAgent Embedded] Starting isolated OpenCode team..."
        echo "(MVP mode — run_task.sh is the active execution backend)"
        echo "Use: $0 run-task 'your instruction'"
        ;;

    help|*)
        echo "DeepAgent Embedded R&D Team (Code Mode)"
        echo ""
        echo "用法:"
        echo "  $0 run-task <指令>    执行研发任务"
        echo "  $0 list              列出已完成任务"
        echo "  $0 start             启动研发环境（占位）"
        echo ""
        echo "示例:"
        echo "  $0 run-task '实现一个用户登录页面'"
        ;;
esac
