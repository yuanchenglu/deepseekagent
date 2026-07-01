#!/bin/bash
# ============================================================
# DeepAgent 嵌入式研发小组 — 最小任务执行脚本
#
# 用法: ./run_task.sh <任务文件路径>
#
# 功能:
#   1. 接收一个描述任务的 JSON 文件路径（含有 task_id、instruction）
#   2. 在 workspace/ 下创建结构化任务记录（task_{task_id}.json）
#   3. 模拟执行（MVP 阶段，后续替换为真实 OpenCode 调用）
#   4. 输出结构化 JSON 结果到 stdout
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

# --- 创建任务工作文件（JSON 格式） ---
{
    echo "{"
    echo "  \"task_id\": \"${TASK_ID}\","
    echo "  \"status\": \"completed\","
    echo "  \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"instruction\": $(echo "$INSTRUCTION_RAW" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo "\"${INSTRUCTION_RAW}\""),"
    echo "  \"result\": {"
    echo "    \"summary\": \"模拟执行完成 — 内置研发小组已收到任务\","
    echo "    \"changed_files\": 0,"
    echo "    \"output\": \"(MVP 模拟模式，无实际代码变更)\""
    echo "  }"
    echo "}"
} > "$OUTPUT_DIR/task_${TASK_ID}.json"

# --- 更新最近运行日志 ---
{
    echo "=== DeepAgent Code Mode Task Run ==="
    echo "Task ID: ${TASK_ID}"
    echo "Time: $(date)"
    echo "Instruction: ${INSTRUCTION_RAW}"
    echo "=== End of run ==="
} > "$OUTPUT_DIR/last_run.log"

# --- 输出结构化结果到 stdout（供 dispatcher 解析） ---
cat "$OUTPUT_DIR/task_${TASK_ID}.json"
