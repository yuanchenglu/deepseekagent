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
#   4. 写入结构化结果到 workspace/task_{task_id}.json
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
    TASK_ID=$(python3 -c "
import json
with open('$TASK_FILE') as f:
    data = json.load(f)
print(data.get('task_id', ''))
" 2>/dev/null || echo "")

    # Write raw instruction to a temp file to avoid quoting issues
    INSTRUCTION_FILE="$OUTPUT_DIR/.instr_${TASK_ID}.txt"
    python3 -c "
import json
with open('$TASK_FILE') as f:
    data = json.load(f)
with open('$INSTRUCTION_FILE', 'w') as f:
    f.write(data.get('instruction', '(no instruction)'))
" 2>/dev/null || echo "(no instruction)" > "$INSTRUCTION_FILE"
    INSTRUCTION_RAW=$(cat "$INSTRUCTION_FILE")
else
    TASK_ID=""
    INSTRUCTION_RAW="(no task file provided)"
fi

# 如果 JSON 中没有 task_id，则自动生成一个
if [ -z "$TASK_ID" ]; then
    TASK_ID="$(date +%s)-$$"
fi

RESULT_FILE="$OUTPUT_DIR/task_${TASK_ID}.json"

# --- 调用隔离的 OpenCode 执行任务 ---
# B3 修复：根据当前 OS + 架构选择正确的 binary 路径，避免硬编码 macos-arm64
OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$OS_NAME" in
    darwin) OS_DIR="macos" ;;
    linux)  OS_DIR="linux" ;;
    mingw*|msys*|cygwin*) OS_DIR="windows" ;;
    *)      OS_DIR="linux" ;;
esac
case "$ARCH" in
    arm64|aarch64) ARCH_DIR="arm64" ;;
    x86_64|amd64)  ARCH_DIR="x64" ;;
    *)             ARCH_DIR="$ARCH" ;;
esac
OPENCODE_BIN="$SCRIPT_DIR/opencode/${OS_DIR}-${ARCH_DIR}/opencode"
[ "$OS_DIR" = "windows" ] && OPENCODE_BIN="${OPENCODE_BIN}.exe"

if [ ! -x "$OPENCODE_BIN" ]; then
    echo "[DeepAgent Embedded] Warning: OpenCode binary not found at $OPENCODE_BIN"
    echo "[DeepAgent Embedded] Falling back to simulated result."
    python3 << PYEOF
import json
data = {
    "task_id": "$TASK_ID",
    "status": "simulated",
    "instruction": open("$INSTRUCTION_FILE").read() if __import__('os').path.exists("$INSTRUCTION_FILE") else "",
    "result": {"summary": "OpenCode binary not available; task recorded but not executed."}
}
with open("$RESULT_FILE", "w") as f:
    json.dump(data, f, ensure_ascii=False)
PYEOF
    rm -f "$INSTRUCTION_FILE"
    exit 0
fi

echo "[DeepAgent Embedded] Invoking isolated OpenCode ($OPENCODE_BIN) for task ${TASK_ID}..."

OPENCODE_CONFIG_DIR="$SCRIPT_DIR/config" \
    "$OPENCODE_BIN" \
    run "$INSTRUCTION_RAW" > "$OUTPUT_DIR/.output_${TASK_ID}.txt" 2>&1
OPENCODE_EXIT=$?

# Write structured result file for collect_result() to read
python3 << PYEOF
import json
instr = open("$INSTRUCTION_FILE").read() if __import__('os').path.exists("$INSTRUCTION_FILE") else ""
try:
    output = open("$OUTPUT_DIR/.output_${TASK_ID}.txt").read()[:500]
except:
    output = ""

data = {
    "task_id": "$TASK_ID",
    "status": "completed" if $OPENCODE_EXIT == 0 else "failed",
    "instruction": instr,
    "exit_code": $OPENCODE_EXIT,
    "result": {"summary": "Task completed with exit code $OPENCODE_EXIT"},
    "output": output,
}
with open("$RESULT_FILE", "w") as f:
    json.dump(data, f, ensure_ascii=False)
PYEOF

# Cleanup temp files
rm -f "$INSTRUCTION_FILE" "$OUTPUT_DIR/.output_${TASK_ID}.txt"

# 记录运行日志
{
    echo "=== DeepAgent Code Mode Task Run ==="
    echo "Task ID: ${TASK_ID}"
    echo "Time: $(date)"
    echo "Instruction: ${INSTRUCTION_RAW}"
    echo "Exit Code: ${OPENCODE_EXIT}"
    echo "=== End of run ==="
} > "$OUTPUT_DIR/last_run.log"
