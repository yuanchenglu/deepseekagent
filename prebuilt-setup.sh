#!/usr/bin/env bash
# ============================================================
# Deep Agent 预装脚本 —— 一键安装 opencode / oh-my-openagent / openspec
#
# 功能：
#   1. 依赖检查（node >= 18、npm 必需、bun 可选）
#   2. 安装 oh-my-openagent（多 Agent 编排插件）
#   3. 安装 OpenSpec（规格驱动开发 CLI）
#   4. 在项目根 bin/ 下生成三个命令的包装脚本
#   5. 执行 --version 验证三个工具都可用
#
# 用法：
#   bash prebuilt-setup.sh
#
# 完成后，用户可以：
#   export PATH="$(pwd)/bin:$PATH"
# 然后从任意位置运行 opencode / omo / openspec
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$PROJECT_ROOT/bin"

# ---- 彩色输出工具（中文友好）----
color_red()    { printf "\033[31m%s\033[0m\n" "$*"; }
color_green()  { printf "\033[32m%s\033[0m\n" "$*"; }
color_yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
color_cyan()   { printf "\033[36m%s\033[0m\n" "$*"; }
color_bold()   { printf "\033[1m%s\033[0m\n" "$*"; }

echo ""
color_bold   "============================================================"
color_bold   "  Deep Agent 预装工具链"
color_bold   "  一键安装 opencode + oh-my-openagent + openspec"
color_bold   "============================================================"
echo ""
echo "项目根目录: $PROJECT_ROOT"
echo ""

# ============================================================
# 阶段 1/5：依赖检查
# ============================================================
color_cyan "[1/5] 检查系统依赖..."

# --- Node.js ---
if ! command -v node >/dev/null 2>&1; then
    color_red "❌ 未检测到 Node.js，请先安装 Node.js >= 20.19.0"
    color_yellow "   下载：https://nodejs.org/"
    exit 2
fi
NODE_VERSION="$(node -v | sed 's/v//')"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
echo "  ✓ Node.js 版本: $NODE_VERSION"
if [ "$NODE_MAJOR" -lt 18 ]; then
    color_red "❌ Node.js 版本过低（$NODE_VERSION），需要 >= 18（OpenSpec 要求 >= 20.19.0）"
    exit 2
fi
if [ "$NODE_MAJOR" -lt 20 ]; then
    color_yellow "⚠️  Node.js $NODE_VERSION 可运行 omo，但 OpenSpec 建议 >= 20.19.0"
fi

# --- npm ---
if ! command -v npm >/dev/null 2>&1; then
    color_red "❌ 未检测到 npm（应随 Node.js 一起安装）"
    exit 3
fi
echo "  ✓ npm 版本: $(npm -v)"

# --- bun（可选）---
if command -v bun >/dev/null 2>&1; then
    echo "  ✓ bun 版本: $(bun --version)（可选，优先使用）"
else
    echo "  - bun 未安装（可选，不影响；将使用 npm）"
fi

echo ""

# ============================================================
# 阶段 2/5：安装 oh-my-openagent
# ============================================================
color_cyan "[2/5] 安装 oh-my-openagent (omo) 多 Agent 编排框架..."
OMO_INSTALL="$PROJECT_ROOT/embedded/oh-my-openagent/install.sh"
if [ ! -x "$OMO_INSTALL" ]; then
    color_red "❌ 找不到 $OMO_INSTALL"
    exit 10
fi
bash "$OMO_INSTALL"
echo ""

# ============================================================
# 阶段 3/5：安装 OpenSpec
# ============================================================
color_cyan "[3/5] 安装 OpenSpec (openspec) 规格驱动开发 CLI..."
OPENSPEC_INSTALL="$PROJECT_ROOT/embedded/openspec/install.sh"
if [ ! -x "$OPENSPEC_INSTALL" ]; then
    color_red "❌ 找不到 $OPENSPEC_INSTALL"
    exit 11
fi
bash "$OPENSPEC_INSTALL"
echo ""

# ============================================================
# 阶段 4/5：生成 bin/ 包装脚本
# ============================================================
color_cyan "[4/5] 创建命令包装脚本到 $BIN_DIR ..."
mkdir -p "$BIN_DIR"

# --- omo 包装 ---
# omo 实际运行时位于 embedded/omo-runtime/node_modules/（install.sh 从 npm 拉取预构建包）
cat > "$BIN_DIR/omo" <<EOF
#!/usr/bin/env bash
# Deep Agent 预装的 omo (oh-my-openagent) 命令
# 优先使用 omo-runtime 中 npm 安装的预构建版本
OMO_RUNTIME="\${OMO_RUNTIME:-$PROJECT_ROOT/embedded/omo-runtime/node_modules/oh-my-opencode}"
if [ -f "\$OMO_RUNTIME/bin/oh-my-opencode.js" ]; then
    exec node "\$OMO_RUNTIME/bin/oh-my-opencode.js" "\$@"
fi
# fallback：源码快照中的 wrapper
exec node "$PROJECT_ROOT/embedded/oh-my-openagent/bin/oh-my-opencode.js" "\$@"
EOF
chmod +x "$BIN_DIR/omo"
echo "  ✓ 已生成 $BIN_DIR/omo"

# --- oh-my-openagent / oh-my-opencode 别名 ---
cp "$BIN_DIR/omo" "$BIN_DIR/oh-my-openagent"
cp "$BIN_DIR/omo" "$BIN_DIR/oh-my-opencode"
echo "  ✓ 已生成别名: oh-my-openagent, oh-my-opencode"

# --- openspec 包装 ---
cat > "$BIN_DIR/openspec" <<EOF
#!/usr/bin/env bash
# Deep Agent 预装的 openspec 命令
exec node "$PROJECT_ROOT/openspec/bin/openspec.js" "\$@"
EOF
chmod +x "$BIN_DIR/openspec"
echo "  ✓ 已生成 $BIN_DIR/openspec"

# --- opencode 包装：优先 PATH 中已有的 opencode，否则提示 ---
cat > "$BIN_DIR/opencode" <<'EOF'
#!/usr/bin/env bash
# Deep Agent 预装的 opencode 命令包装
# 优先使用系统 PATH 中的 opencode；Embedded 二进制（如存在）作为 fallback
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1) 若系统已安装 opencode（不是本包装脚本），直接调用
SYS_OPENC="$(command -v opencode 2>/dev/null || true)"
if [ -n "$SYS_OPENC" ] && [ "$(realpath "$SYS_OPENC" 2>/dev/null || echo "$SYS_OPENC")" != "$(realpath "$0" 2>/dev/null || echo "$0")" ]; then
    exec "$SYS_OPENC" "$@"
fi

# 2) 尝试 embedded 内置的平台二进制（Linux x64）
for candidate in \
    "$PROJECT_ROOT/embedded/opencode/opencode" \
    "$PROJECT_ROOT/embedded/opencode/linux-x64/opencode" \
    "$PROJECT_ROOT/embedded/opencode/macos-arm64/opencode" \
    "$PROJECT_ROOT/embedded/opencode/macos-x64/opencode"; do
    if [ -x "$candidate" ]; then
        exec "$candidate" "$@"
    fi
done

# 3) Fallback：提示用户
echo "[opencode] 未找到 OpenCode 二进制。" >&2
echo "[opencode] 请先安装 OpenCode (https://opencode.ai) 或把二进制放到 embedded/opencode/<platform>/opencode" >&2
exit 127
EOF
chmod +x "$BIN_DIR/opencode"
echo "  ✓ 已生成 $BIN_DIR/opencode"

echo ""

# ============================================================
# 阶段 5/5：版本验证（关闭 set -e 以便独立验证每个命令）
# ============================================================
set +e
color_cyan "[5/5] 验证三个工具版本号..."
FAIL=0

echo ""
echo "---- omo ----"
OMO_OUT="$("$BIN_DIR/omo" --version 2>&1)"
OMO_RC=$?
echo "$OMO_OUT" | head -5
if [ $OMO_RC -eq 0 ] && echo "$OMO_OUT" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+'; then
    color_green "✓ omo 命令可用"
else
    color_red "✗ omo 命令执行失败 (exit=$OMO_RC)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "---- openspec ----"
OS_OUT="$("$BIN_DIR/openspec" --version 2>&1)"
OS_RC=$?
echo "$OS_OUT" | head -5
if [ $OS_RC -eq 0 ] && echo "$OS_OUT" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+'; then
    color_green "✓ openspec 命令可用"
else
    color_red "✗ openspec 命令执行失败 (exit=$OS_RC)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "---- opencode ----"
OC_OUT="$("$BIN_DIR/opencode" --version 2>&1)"
OC_RC=$?
echo "$OC_OUT" | head -5
if [ $OC_RC -eq 0 ]; then
    color_green "✓ opencode 命令可用"
else
    color_yellow "⚠ opencode 返回 exit=$OC_RC（通常因为 OpenCode 原生二进制未放入 embedded/opencode/）—— omo/openspec 已可用"
fi
set -e

echo ""
color_bold "============================================================"
if [ "$FAIL" -eq 0 ]; then
    color_green "🎉 Deep Agent 预装工具链安装成功！"
else
    color_red "⚠️  部分工具安装失败（$FAIL 个），请查看上方日志"
fi
color_bold "============================================================"
echo ""
color_yellow "提示：把 bin/ 目录加入 PATH 即可在任意位置调用三个命令："
echo ""
echo "    export PATH=\"$BIN_DIR:\$PATH\""
echo ""
echo "也可以写进 ~/.bashrc 或 ~/.zshrc 以永久生效。"
echo ""

exit "$FAIL"
