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

ACTION="${1:-help}"

case "$ACTION" in
    run-task)
        shift
        TASK_DESC="$*"
        echo "[DeepAgent Embedded] Running task: ${TASK_DESC:0:80}..."
        # 创建临时任务文件并调用 run_task.sh
        TASK_FILE=$(mktemp "${SCRIPT_DIR}/workspace/tmp_task_XXXXXX.txt")
        echo "$TASK_DESC" > "$TASK_FILE"
        exec "$SCRIPT_DIR/run_task.sh" "$TASK_FILE"
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
