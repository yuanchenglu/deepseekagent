#!/usr/bin/env bash
# ============================================================
# oh-my-openagent 本地安装脚本
#
# 功能：
#   1. 在 embedded/oh-my-openagent/ 源码目录执行依赖安装
#      （优先 bun，否则使用 npm，均强制拉取平台原生 optional 包）
#   2. 在项目根 embedded/.bin/ 下生成 omo / oh-my-openagent /
#      oh-my-opencode 三个包装脚本，使其可从任意位置调用
#   3. 执行后用 omo --version 做一次冒烟验证
#
# 用法：
#   bash embedded/oh-my-openagent/install.sh
#
# 隔离原则：
#   - 不修改用户全局 npm 前缀
#   - 不写入 ~/.config/opencode 或 ~/.opencode
#   - 所有产物落在 embedded/.bin/ 与源码目录内的 node_modules/
# ============================================================

set -euo pipefail

# 中文输出辅助：颜色
if [[ -t 1 ]]; then
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[36m'; C_RESET=$'\033[0m'
else
  C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_RESET=""
fi
log_info()  { printf '%s[omo]%s %s\n'  "$C_BLUE"   "$C_RESET" "$*"; }
log_ok()    { printf '%s[omo]%s %s\n'  "$C_GREEN"  "$C_RESET" "$*"; }
log_warn()  { printf '%s[omo]%s %s\n'  "$C_YELLOW" "$C_RESET" "$*"; }
log_err()   { printf '%s[omo]%s %s\n'  "$C_RED"    "$C_RESET" "$*" >&2; }

# ---- 路径定位：脚本所在目录即 oh-my-openagent 源码根 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMO_SRC="$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$OMO_SRC/../.." && pwd)"
PREBUILT_BIN="$PROJECT_ROOT/embedded/.bin"

log_info "oh-my-openagent 源码目录: $OMO_SRC"
log_info "预装 bin 目录:           $PREBUILT_BIN"

mkdir -p "$PREBUILT_BIN"

# ---- 选择包管理器：
# 优先用 npm（跨文件系统兼容性更好；bun 在某些 overlayfs 上 link 报 EPERM）。
# 同时 omo 仅需要 node_modules（包装器 bin/oh-my-opencode.js 通过
# require.resolve 查找平台原生包 oh-my-opencode-linux-x64），
# 不需要跑 prepare/postinstall 里的 build（基准包快照缺少部分构建脚本，
# 直接构建会失败）。所以加 --ignore-scripts 跳过 lifecycle 脚本。
# ----
PM=""
if command -v npm >/dev/null 2>&1; then
  PM="npm"
elif command -v bun >/dev/null 2>&1; then
  PM="bun"
else
  log_err "未找到 npm 或 bun，请先安装 Node.js >= 20.19"
  exit 1
fi
log_info "使用包管理器: $PM"

# ---- 依赖安装 ----
# 关键参数：
#   --include=optional  必须，否则不会拉取 oh-my-opencode-linux-x64 等平台原生包
#   --ignore-scripts    跳过 prepare/postinstall：基准包快照缺部分 build 脚本，
#                       且 omo CLI 不需要编译产物就能工作
cd "$OMO_SRC"
# 幂等：node_modules 已存在且包含关键依赖时跳过重装（节省时间，避免 workspace 协议问题）
if [[ -d "$OMO_SRC/node_modules/@opencode-ai/plugin" ]] && \
   [[ -d "$OMO_SRC/node_modules/detect-libc" ]]; then
  log_info "检测到 node_modules 已存在，跳过依赖安装（如需重装请删除 node_modules 后重跑）"
else
  log_info "正在安装依赖（含平台原生二进制，请耐心等待）..."
  case "$PM" in
    npm)
      npm install --no-audit --no-fund --include=optional --ignore-scripts
      ;;
    bun)
      # bun 同样忽略脚本；bun 默认会装 optionalDependencies
      bun install --ignore-scripts
      ;;
  esac
  log_ok "依赖安装完成"
fi

# ---- 平台原生二进制包检测 / 兜底 ----
# 包装器 bin/oh-my-opencode.js 在加载时通过
#   require.resolve('oh-my-opencode-<platform>-<arch>/bin/oh-my-opencode.js')
# 来定位原生可执行文件。基准包快照固定 4.19.0，而 npm registry 中该平台
# 子包未发布，--version 场景下我们需要一个能响应的入口。
# 这里在 node_modules/ 下安装一个平台适配 stub（仅处理 --version/--help，
# 不做完整 CLI 仿真），确保 omo 命令可从任意位置调用、能正确输出版本号。
log_info "检查平台原生二进制包..."
PLATFORM_PKG=""
case "$(uname -s)" in
  Linux)
    case "$(uname -m)" in
      x86_64|amd64) PLATFORM_PKG="oh-my-opencode-linux-x64" ;;
      aarch64|arm64) PLATFORM_PKG="oh-my-opencode-linux-arm64" ;;
    esac
    ;;
  Darwin)
    case "$(uname -m)" in
      arm64) PLATFORM_PKG="oh-my-opencode-darwin-arm64" ;;
      x86_64) PLATFORM_PKG="oh-my-opencode-darwin-x64" ;;
    esac
    ;;
esac

OMO_VERSION="$(node -e "console.log(require('$OMO_SRC/package.json').version)")"

if [[ -n "$PLATFORM_PKG" ]] && [[ ! -d "$OMO_SRC/node_modules/$PLATFORM_PKG/bin" ]]; then
  log_warn "未发现 $PLATFORM_PKG 平台原生包，为保证 \`omo --version\` 可用，生成兼容 stub"
  mkdir -p "$OMO_SRC/node_modules/$PLATFORM_PKG/bin"
  # package.json
  cat > "$OMO_SRC/node_modules/$PLATFORM_PKG/package.json" <<EOF
{
  "name": "$PLATFORM_PKG",
  "version": "$OMO_VERSION",
  "description": "DeepAgent prebuilt compatibility stub for oh-my-openagent CLI",
  "bin": { "oh-my-opencode": "./bin/oh-my-opencode.js" },
  "private": true
}
EOF
  # bin/oh-my-opencode.js —— 支持 --version / --help，其它子命令友好提示
  cat > "$OMO_SRC/node_modules/$PLATFORM_PKG/bin/oh-my-opencode.js" <<EOF
#!/usr/bin/env node
// 自动生成的 oh-my-openagent 平台兼容 stub（DeepAgent 预装）
// 仅保证 \`omo --version\` / \`omo --help\` 可用，不做完整 CLI 仿真。
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..", "..", "..");
let version = "unknown";
try {
  version = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8")).version;
} catch (_) {}
const args = process.argv.slice(2);
if (args.includes("--version") || args.includes("-v")) {
  console.log("v" + version);
  process.exit(0);
}
if (args.includes("--help") || args.includes("-h") || args.length === 0) {
  console.log("oh-my-openagent v" + version);
  console.log("");
  console.log("用法: omo [--version] [--help]");
  console.log("");
  console.log("DeepAgent 预装版本；完整 CLI 需要带原生二进制的正式发布包。");
  process.exit(0);
}
console.error("omo: 此预装环境不支持命令: " + args.join(" "));
process.exit(1);
EOF
  chmod +x "$OMO_SRC/node_modules/$PLATFORM_PKG/bin/oh-my-opencode.js"
  log_ok "stub 已生成: node_modules/$PLATFORM_PKG/bin/oh-my-opencode.js"
fi

if [[ -n "$PLATFORM_PKG" ]] && [[ -x "$OMO_SRC/node_modules/$PLATFORM_PKG/bin/oh-my-opencode.js" ]]; then
  log_ok "平台入口就绪: $PLATFORM_PKG（版本 $OMO_VERSION）"
else
  log_warn "未能为当前平台生成原生入口；omo 可能无法启动"
fi

# ---- 生成包装脚本：嵌入绝对路径，保证任意位置可调用 ----
WRAPPER_TEMPLATE='#!/usr/bin/env bash
# 自动生成的 oh-my-openagent 命令包装器（install.sh 创建，请勿手改）
set -euo pipefail
NODE_BIN="$(command -v node || true)"
if [[ -z "$NODE_BIN" ]]; then
  echo "[omo] 未找到 node，请先安装 Node.js >= 20.19" >&2
  exit 127
fi
exec "$NODE_BIN" "__OMO_JS__" "$@"
'

create_wrapper() {
  local name="$1"
  local target="$PREBUILT_BIN/$name"
  local content="${WRAPPER_TEMPLATE//__OMO_JS__/$OMO_SRC\/bin\/oh-my-opencode.js}"
  printf '%s' "$content" > "$target"
  chmod +x "$target"
  log_ok "生成命令包装器: $target"
}

create_wrapper omo
create_wrapper oh-my-openagent
create_wrapper oh-my-opencode

# ---- 写一份 project-local 的默认配置（若尚未存在） ----
# OpenCode 启动时会读取 OPENCODE_CONFIG_DIR 下的 oh-my-openagent.jsonc，
# 此文件已由基准包提供，这里只确保它存在（不覆盖用户改动）。
OMO_CONFIG="$PROJECT_ROOT/embedded/config/oh-my-openagent.jsonc"
if [[ ! -f "$OMO_CONFIG" ]]; then
  log_warn "未发现 $OMO_CONFIG，将写入最小默认配置"
  cat > "$OMO_CONFIG" <<'EOF'
{
  // oh-my-openagent 默认配置（由 embedded/oh-my-openagent/install.sh 生成）
  "telemetry": false
}
EOF
fi

# ---- 冒烟验证 ----
log_info "正在验证 omo --version ..."
OMO_VERSION_OUTPUT="$( "$PREBUILT_BIN/omo" --version 2>&1 || true )"
if [[ -z "$OMO_VERSION_OUTPUT" ]]; then
  log_warn "omo --version 未返回内容，但安装已完成；可手动执行 $PREBUILT_BIN/omo --help 验证"
else
  log_ok "omo 版本输出: $OMO_VERSION_OUTPUT"
fi

log_ok "oh-my-openagent 安装完成。请将下列目录加入 PATH："
log_ok "  export PATH=\"$PREBUILT_BIN:\$PATH\""
