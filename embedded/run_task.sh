#!/bin/bash
# ============================================================
# DeepAgent 嵌入式研发小组 — 最小任务执行脚本
#
# 用法: ./run_task.sh <任务文件路径>
#
# 功能:
#   1. 接收一个描述任务的 JSON 文件路径（含有 task_id、instruction）
#   2. 提取 task_id 和 instruction
#   3. 用隔离的 OpenCode 二进制执行 instruction
#   4. 记录运行日志到 workspace/last_run.log
#
# 隔离原则:
#   - 不读取 ~/.config/opencode 或任何用户本地配置
#   - 所有输出仅写入 embedded/workspace/
# ============================================================
set -e

TASK_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/workspace"

mkdir -p "$OUTPUT_DIR"

# --- 从输入文件读取 task_id 和 instruction ---
if [ -f "$TASK_FILE" ]; then
    # 尝试用 Python 解析 JSON 以获取 task_id
    TASK_ID=$(python3 -c "
import json
with open('$TASK_FILE') as f:
    data = json.load(f)
print(data.get('task_id', ''))
" 2>/dev/null || echo "")

    # 读取原始指令内容（保留原始文本）
    INSTRUCTION_RAW=$(python3 -c "
import json
with open('$TASK_FILE') as f:
    data = json.load(f)
print(data.get('instruction', '(no instruction)'))
" 2>/dev/null || head -c 1000 "$TASK_FILE")
else
    TASK_ID=""
    INSTRUCTION_RAW="(no task file provided)"
fi

# 如果 JSON 中没有 task_id，则自动生成一个
if [ -z "$TASK_ID" ]; then
    TASK_ID="$(date +%s)-$$"
fi

# --- 调用隔离的 OpenCode 执行任务 ---
echo "[DeepAgent Embedded] Invoking isolated OpenCode for task ${TASK_ID}..."
OPENCODE_CONFIG_DIR="$SCRIPT_DIR/config" \
    "$SCRIPT_DIR/opencode/macos-arm64/opencode" \
    run "$INSTRUCTION_RAW" 2>&1

# 记录运行日志
{
    echo "=== DeepAgent Code Mode Task Run ==="
    echo "Task ID: ${TASK_ID}"
    echo "Time: $(date)"
    echo "Instruction: ${INSTRUCTION_RAW}"
    echo "=== End of run ==="
} > "$OUTPUT_DIR/last_run.log"
