#!/usr/bin/env bash
# ============================================================
# OpenSpec 本地安装脚本
#
# 注意：基准包里 OpenSpec 源码位于项目根 openspec/，
# 本脚本放在 embedded/openspec/install.sh 路径下是为了和 omo
# 脚本路径对称；脚本内部会自动定位到真正的源码根
# （<project_root>/openspec）。
#
# 功能：
#   1. 在 openspec/ 源码目录执行 npm install
#   2. 执行 npm run build，产出 dist/cli/index.js（bin 启动依赖）
#   3. 在 embedded/.bin/ 下生成 openspec 包装脚本
#   4. 冒烟执行 openspec --version 验证
#
# 用法：
#   bash embedded/openspec/install.sh
# ============================================================

set -euo pipefail

# 中文输出辅助：颜色
if [[ -t 1 ]]; then
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[36m'; C_RESET=$'\033[0m'
else
  C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_RESET=""
fi
log_info()  { printf '%s[openspec]%s %s\n'  "$C_BLUE"   "$C_RESET" "$*"; }
log_ok()    { printf '%s[openspec]%s %s\n'  "$C_GREEN"  "$C_RESET" "$*"; }
log_warn()  { printf '%s[openspec]%s %s\n'  "$C_YELLOW" "$C_RESET" "$*"; }
log_err()   { printf '%s[openspec]%s %s\n'  "$C_RED"    "$C_RESET" "$*" >&2; }

# ---- 路径定位 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 真实源码根：<project_root>/openspec/ （基准包固定位置）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OPENSPEC_SRC="$PROJECT_ROOT/openspec"
PREBUILT_BIN="$PROJECT_ROOT/embedded/.bin"

if [[ ! -f "$OPENSPEC_SRC/package.json" ]]; then
  log_err "未在 $OPENSPEC_SRC 找到 OpenSpec 源码，请确认基准包已解压"
  exit 1
fi

log_info "OpenSpec 源码目录: $OPENSPEC_SRC"
log_info "预装 bin 目录:     $PREBUILT_BIN"
mkdir -p "$PREBUILT_BIN"

# ---- Node 版本要求（OpenSpec engines.node>=20.19） ----
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
if (( NODE_MAJOR < 20 )); then
  log_err "OpenSpec 要求 Node.js >= 20.19，当前为 $(node --version 2>/dev/null || echo '未安装')"
  exit 1
fi

# ---- 依赖安装 ----
# 注意：基准包的 package.json scripts.prepare 是 `pnpm run build`，在没有 pnpm
# 的环境会失败。我们用 npm 安装时必须 --ignore-scripts，再单独跑 npm run build。
cd "$OPENSPEC_SRC"
if [[ -d "$OPENSPEC_SRC/node_modules/commander" ]] && [[ -d "$OPENSPEC_SRC/node_modules/typescript" ]]; then
  log_info "检测到 node_modules 已存在，跳过依赖安装"
else
  log_info "正在安装 OpenSpec 依赖..."
  npm install --no-audit --no-fund --ignore-scripts
  log_ok "依赖安装完成"
fi

# ---- 构建 dist/（bin/openspec.js 直接 import ../dist/cli/index.js） ----
if [[ -f "$OPENSPEC_SRC/dist/cli/index.js" ]]; then
  log_info "检测到 dist/ 已存在，跳过构建（如需重建请删除 openspec/dist 后重跑）"
else
  log_info "正在构建 OpenSpec（npm run build → node build.js）..."
  npm run build
  if [[ ! -f "$OPENSPEC_SRC/dist/cli/index.js" ]]; then
    log_err "构建失败：未找到 $OPENSPEC_SRC/dist/cli/index.js"
    exit 1
  fi
  log_ok "构建完成：dist/cli/index.js 已就绪"
fi

# ---- 生成包装脚本 ----
WRAPPER_TEMPLATE='#!/usr/bin/env bash
# 自动生成的 openspec 命令包装器（install.sh 创建，请勿手改）
set -euo pipefail
NODE_BIN="$(command -v node || true)"
if [[ -z "$NODE_BIN" ]]; then
  echo "[openspec] 未找到 node，请先安装 Node.js >= 20.19" >&2
  exit 127
fi
# OpenSpec 通过 bin/openspec.js 启动；工作目录切换到源码根以保证相对 import 可用
cd "__OPENSPEC_SRC__"
exec "$NODE_BIN" "__OPENSPEC_JS__" "$@"
'
TARGET="$PREBUILT_BIN/openspec"
content="${WRAPPER_TEMPLATE//__OPENSPEC_SRC__/$OPENSPEC_SRC}"
content="${content//__OPENSPEC_JS__/$OPENSPEC_SRC\/bin\/openspec.js}"
printf '%s' "$content" > "$TARGET"
chmod +x "$TARGET"
log_ok "生成命令包装器: $TARGET"

# ---- 冒烟验证 ----
log_info "正在验证 openspec --version ..."
VER_OUT="$( "$PREBUILT_BIN/openspec" --version 2>&1 || true )"
if [[ -z "$VER_OUT" ]]; then
  log_warn "openspec --version 未返回内容，请手动执行 $PREBUILT_BIN/openspec --help 确认"
else
  log_ok "openspec 版本输出: $VER_OUT"
fi

log_ok "OpenSpec 安装完成。请将下列目录加入 PATH："
log_ok "  export PATH=\"$PREBUILT_BIN:\$PATH\""
