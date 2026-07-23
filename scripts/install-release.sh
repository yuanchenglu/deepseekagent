#!/bin/bash
# ============================================================================
# DeepAgent Release Installer
# ============================================================================
# Release 级别安装脚本：从预构建的 tarball 安装 DeepAgent，无需源码目录。
#
# 用法:
#   curl -fsSL https://deepseekagent.starseas.org/install.sh | sh
#   curl -fsSL ... | sh -s -- --skip-setup       # 跳过交互式配置
#   curl -fsSL ... | sh -s -- --version v0.9.0   # 指定版本
#   curl -fsSL ... | sh -s -- --dir /opt/deepagent  # 指定安装目录
#
# 特性:
#   - 双源下载：Cloudflare R2 主源 + GitHub Releases 备用源
#   - SHA256 校验和验证（校验和从 GitHub 获取，不同信任域）
#   - uv sync 安装 Python 依赖
#   - 预构建 WebUI（无需 npm build / electron-builder）
#   - 配置保留策略：.env、config.yaml、用户 skills 永不被覆盖
#   - 符号链接 ~/.local/bin/deepagent
#
# 参考:
#   - PRD: docs/specs/05-Release-Installation.md
#   - Hermes upstream install.sh（系统检测、配置保留策略模板）
# ============================================================================

set -e

# ---- 颜色定义 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ---- 默认配置 ----
DEEPAGENT_HOME="${DEEPAGENT_HOME:-$HOME/.deepagent}"
INSTALL_DIR="${INSTALL_DIR:-$DEEPAGENT_HOME}"
DEFAULT_VERSION="latest"
VERSION="${DEEPAGENT_VERSION:-$DEFAULT_VERSION}"
SKIP_SETUP=false
PYTHON_VERSION="3.11"

# ---- Release 下载源 ----
# 主源：Cloudflare R2
R2_BASE_URL="https://deepseekagent.starseas.org/releases"
# 备用源：GitHub Releases（国内友好）
GH_REPO="yuanchenglu/deepseekagent"
GH_BASE_URL="https://github.com/${GH_REPO}/releases/download"

# ---- 检测是否在交互式终端中运行 ----
if [ -t 0 ]; then
    IS_INTERACTIVE=true
else
    IS_INTERACTIVE=false
fi

# ============================================================================
# 参数解析
# ============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-setup)
                SKIP_SETUP=true
                shift
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            --dir)
                INSTALL_DIR="$2"
                DEEPAGENT_HOME="$2"
                shift 2
                ;;
            -h|--help)
                echo "DeepAgent Release Installer"
                echo ""
                echo "Usage: install-release.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-setup      跳过交互式配置向导"
                echo "  --version VERSION  指定安装版本 (默认: latest)"
                echo "  --dir PATH         指定安装目录 (默认: ~/.deepagent)"
                echo "  -h, --help         显示此帮助"
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                echo "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# 辅助函数
# ============================================================================

print_banner() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│          ☤ DeepAgent Release Installer                   │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│  基于 Hermes + OpenCode， 专为 DeepSeek 所有物理特性，深度优化的  │"
    echo "│  数字分身产品                                                │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

log_info()    { echo -e "${CYAN}→${NC} $1"; log_install "INFO" "$1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; log_install "OK" "$1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; log_install "WARN" "$1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; log_install "ERROR" "$1"; }

# ---- 本地安装日志 ----
# 所有安装/更新操作都会记录到 INSTALL_DIR/install_update.log
# 用于后续诊断，不上传任何用户隐私信息
LOG_FILE=""
init_log_file() {
    local log_dir
    if [ -n "${INSTALL_DIR:-}" ]; then
        log_dir="$INSTALL_DIR"
    elif [ -n "${DEEPAGENT_HOME:-}" ]; then
        log_dir="$DEEPAGENT_HOME"
    else
        log_dir="$HOME/.deepagent"
    fi
    mkdir -p "$log_dir"
    LOG_FILE="${log_dir}/install_update.log"
    # 日志文件头（仅首次写入）
    if [ ! -f "$LOG_FILE" ] || [ ! -s "$LOG_FILE" ]; then
        {
            echo "============================================"
            echo " DeepAgent Install/Update Log"
            echo " Started: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
            echo " OS: ${OS:-unknown} (${DISTRO:-unknown})"
            echo " Arch: ${ARCH:-unknown}"
            echo " Version: ${VERSION:-unknown}"
            echo "============================================"
        } > "$LOG_FILE"
    fi
}

log_install() {
    [ -z "$LOG_FILE" ] && return
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    # 日志格式: [时间] [级别] 消息
    # 不包含任何用户个人信息、环境变量值、文件路径（除了已知的 INSTALL_DIR）
    echo "[${timestamp}] [${level}] ${msg}" >> "$LOG_FILE"
}

# 检测是否在 Termux（Android 终端模拟器）中运行
is_termux() {
    [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux/files/usr"* ]]
}

# 获取命令符号链接目录
get_command_link_dir() {
    if is_termux && [ -n "${PREFIX:-}" ]; then
        echo "$PREFIX/bin"
    else
        echo "$HOME/.local/bin"
    fi
}

# 获取命令符号链接目录（用于显示）
get_command_link_display_dir() {
    if is_termux && [ -n "${PREFIX:-}" ]; then
        echo '$PREFIX/bin'
    else
        echo '~/.local/bin'
    fi
}

# ============================================================================
# Step 1: 系统检测
# ============================================================================
# 检测操作系统类型、包管理器、已安装的工具链（uv、Python）
# ============================================================================

detect_os() {
    case "$(uname -s)" in
        Linux*)
            if is_termux; then
                OS="android"
                DISTRO="termux"
            else
                OS="linux"
                if [ -f /etc/os-release ]; then
                    . /etc/os-release
                    DISTRO="$ID"
                    OS_VERSION="$VERSION_ID"
                else
                    DISTRO="unknown"
                    OS_VERSION=""
                fi
            fi
            ;;
        Darwin*)
            OS="macos"
            DISTRO="macos"
            OS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="windows"
            DISTRO="windows"
            log_error "检测到 Windows。DeepAgent Release 安装暂不支持 Windows。"
            log_info "请使用 WSL2（Windows Subsystem for Linux）或虚拟机运行。"
            exit 1
            ;;
        *)
            OS="unknown"
            DISTRO="unknown"
            OS_VERSION=""
            log_warn "未知操作系统，尝试继续..."
            ;;
    esac

    log_success "检测到操作系统: $OS ($DISTRO${OS_VERSION:+ $OS_VERSION})"
}

# 检测 CPU 架构（用于选择正确的二进制包）
detect_arch() {
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64)
            ARCH_SHORT="x64"
            ;;
        aarch64|arm64)
            ARCH_SHORT="arm64"
            ;;
        armv7l)
            ARCH_SHORT="arm"
            ;;
        *)
            ARCH_SHORT="$ARCH"
            log_warn "未知架构: $ARCH，尝试继续..."
            ;;
    esac
    log_success "检测到架构: $ARCH ($ARCH_SHORT)"
}

# 检查基础工具依赖是否齐全
check_prerequisites() {
    local missing=false
    log_info "检查基础工具..."

    for cmd in curl tar; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "缺少必需工具: $cmd"
            missing=true
        fi
    done

    if [ "$missing" = true ]; then
        log_error "请安装上述缺失工具后重新运行。"
        case "$OS" in
            macos)
                log_info "  brew install curl tar"
                ;;
            linux)
                log_info "  sudo apt install curl tar   # Debian/Ubuntu"
                log_info "  sudo dnf install curl tar   # Fedora"
                ;;
        esac
        exit 1
    fi

    # rsync 非必需（有降级方案）
    if ! command -v rsync &>/dev/null; then
        log_warn "rsync 未安装，将使用 cp -r 替代（较慢）"
        HAS_RSYNC=false
    else
        HAS_RSYNC=true
        log_success "rsync 已安装"
    fi

    log_success "基础工具检查通过"
}

# 安装 uv（快速 Python 包管理器）
install_uv() {
    if [ "$DISTRO" = "termux" ]; then
        # Termux 使用 Python 标准库 venv + pip（uv 在 Termux 上兼容性不佳）
        log_info "Termux 环境 — 使用 Python 标准 venv + pip 而非 uv"
        UV_CMD=""
        return 0
    fi

    log_info "检查 uv 包管理器..."

    # 检查常见路径
    if command -v uv &> /dev/null; then
        UV_CMD="uv"
        UV_VERSION=$($UV_CMD --version 2>/dev/null)
        log_success "uv 已安装 ($UV_VERSION)"
        return 0
    fi

    if [ -x "$HOME/.local/bin/uv" ]; then
        UV_CMD="$HOME/.local/bin/uv"
        UV_VERSION=$($UV_CMD --version 2>/dev/null)
        log_success "uv 已安装 (~/.local/bin, $UV_VERSION)"
        return 0
    fi

    if [ -x "$HOME/.cargo/bin/uv" ]; then
        UV_CMD="$HOME/.cargo/bin/uv"
        UV_VERSION=$($UV_CMD --version 2>/dev/null)
        log_success "uv 已安装 (~/.cargo/bin, $UV_VERSION)"
        return 0
    fi

    # 安装 uv
    log_info "正在安装 uv（快速 Python 包管理器）..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then
        if [ -x "$HOME/.local/bin/uv" ]; then
            UV_CMD="$HOME/.local/bin/uv"
        elif [ -x "$HOME/.cargo/bin/uv" ]; then
            UV_CMD="$HOME/.cargo/bin/uv"
        elif command -v uv &> /dev/null; then
            UV_CMD="uv"
        else
            log_error "uv 已安装但不在 PATH 中"
            log_info "请将 ~/.local/bin 加入 PATH 后重新运行"
            exit 1
        fi
        UV_VERSION=$($UV_CMD --version 2>/dev/null)
        log_success "uv 已安装 ($UV_VERSION)"
    else
        log_error "uv 安装失败"
        log_info "手动安装: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
}

# 检查 Python 版本
check_python() {
    if [ "$DISTRO" = "termux" ]; then
        log_info "检查 Termux Python..."
        if command -v python >/dev/null 2>&1; then
            PYTHON_PATH="$(command -v python)"
            if "$PYTHON_PATH" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
                PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
                log_success "Python 已安装: $PYTHON_FOUND_VERSION"
                return 0
            fi
        fi
        log_info "正在通过 pkg 安装 Python..."
        pkg install -y python >/dev/null
        PYTHON_PATH="$(command -v python)"
        PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
        log_success "Python 已安装: $PYTHON_FOUND_VERSION"
        return 0
    fi

    log_info "检查 Python $PYTHON_VERSION..."

    # 让 uv 处理 Python 版本管理
    if [ -n "${UV_CMD:-}" ] && $UV_CMD python find "$PYTHON_VERSION" &> /dev/null; then
        PYTHON_PATH=$($UV_CMD python find "$PYTHON_VERSION")
        PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
        log_success "Python 已安装: $PYTHON_FOUND_VERSION"
        return 0
    fi

    # Python 未找到 — 用 uv 安装（无需 sudo！）
    log_info "Python $PYTHON_VERSION 未找到，通过 uv 安装..."
    if [ -n "${UV_CMD:-}" ] && $UV_CMD python install "$PYTHON_VERSION"; then
        PYTHON_PATH=$($UV_CMD python find "$PYTHON_VERSION")
        PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
        log_success "Python 已安装: $PYTHON_FOUND_VERSION"
    else
        log_error "Python $PYTHON_VERSION 安装失败"
        log_info "请手动安装 Python $PYTHON_VERSION 后重新运行此脚本"
        exit 1
    fi
}

# 检查 Node.js（仅警告，Release 包中 WebUI 已预构建，运行时不需要 Node.js）
# 根据 PRD 要求：不再自动安装，仅警告。Node.js 仅开发/构建 WebUI 时需要。
check_node() {
    local node_required_version="23"
    if command -v node &> /dev/null; then
        local found_ver
        found_ver=$(node --version 2>/dev/null)
        # 提取主版本号进行版本比较
        local major_ver
        major_ver=$(echo "$found_ver" | sed 's/v//' | cut -d. -f1)
        if [ "$major_ver" -ge "$node_required_version" ] 2>/dev/null; then
            log_success "Node.js $found_ver 已安装"
        else
            log_warn "Node.js $found_ver 版本过低，开发 WebUI 需要 v${node_required_version}+"
        fi
    else
        log_warn "Node.js 未安装（Release 版 WebUI 已预构建，运行时不需要）"
        log_info "如需开发/构建 WebUI，请手动安装 Node.js ${node_required_version}+"
    fi
}

# ============================================================================
# Step 2: 顺序下载组件 + 安装
# ============================================================================
# 不再下载单个 900 MB tar.gz，而是按顺序下载多个小包：
#   1. core（~5 MB）→ 解压 → uv sync（终端滚屏）
#   2. embedded（~97 MB）→ 按平台提取
#   3. webui-server（~60 MB，可选）→ `deepagent webui install`
#
# 每一批下载时终端都有进度反馈，用户不会焦虑。
# ============================================================================

# 检测可用的 SHA256 校验工具
detect_sha256_cmd() {
    if command -v sha256sum &>/dev/null; then
        SHA256_CMD="sha256sum"
        SHA256_CHECK_FLAG="-c"
    elif command -v shasum &>/dev/null; then
        SHA256_CMD="shasum"
        SHA256_CHECK_FLAG="-a 256 -c"
    elif command -v openssl &>/dev/null; then
        SHA256_CMD="openssl dgst -sha256"
        SHA256_CHECK_FLAG=""
    else
        SHA256_CMD=""
        SHA256_CHECK_FLAG=""
    fi
}

# 校验文件 SHA256
verify_sha256() {
    local file="$1"
    local sha_file="$2"

    if [ -z "${SHA256_CMD:-}" ]; then
        log_warn "无可用 SHA256 工具，跳过校验"
        return 0
    fi
    if [ ! -f "$sha_file" ]; then
        log_warn "校验和文件不存在，跳过"
        return 0
    fi

    log_info "验证 SHA256 校验和..."
    local check_dir
    check_dir=$(dirname "$file")

    if [ -n "$SHA256_CHECK_FLAG" ]; then
        if (cd "$check_dir" && $SHA256_CMD $SHA256_CHECK_FLAG "$(basename "$sha_file")" 2>/dev/null); then
            log_success "校验和验证通过 ✓"
            return 0
        fi
    else
        local expected_hash
        local actual_hash
        expected_hash=$(awk '{print $1}' "$sha_file" 2>/dev/null)
        actual_hash=$($SHA256_CMD "$file" 2>/dev/null | awk '{print $NF}')
        if [ "$expected_hash" = "$actual_hash" ]; then
            log_success "校验和验证通过 ✓"
            return 0
        fi
    fi

    log_error "校验和验证失败！文件可能已损坏。"
    log_info "文件: $file"
    log_info "预期: $(cat "$sha_file" 2>/dev/null)"
    return 1
}

# 下载单个文件（带进度条），失败时重试一次
# 参数：$1=URL, $2=输出路径, $3=描述（用于日志）
# 小文件用静默下载，大文件用进度条
curl_download() {
    local url="$1"
    local output="$2"
    local desc="$3"
    local max_attempts=2
    local attempt=1

    while [ "$attempt" -le "$max_attempts" ]; do
        log_info "${desc} (attempt ${attempt}/${max_attempts})"
        # 用 --progress-bar 让用户看到下载进度
        if curl -fL --progress-bar --connect-timeout 15 --max-time 900 "$url" -o "$output" 2>&1; then
            return 0
        fi
        if [ "$attempt" -lt "$max_attempts" ]; then
            log_warn "下载失败，3 秒后重试..."
            sleep 3
        fi
        attempt=$((attempt + 1))
    done
    return 1
}

# 获取校验和文件并从 R2 下载校验验证
download_verify_file() {
    local tarball="$1"
    local name="$2"
    local sha_url="${R2_BASE_URL}/${name}.sha256"
    local sha_file
    sha_file="$(dirname "$tarball")/${name}.sha256"

    if curl -fsSL --connect-timeout 10 --max-time 30 "$sha_url" -o "$sha_file" 2>/dev/null; then
        verify_sha256 "$tarball" "$sha_file"
    else
        log_warn "无法获取校验和文件，跳过验证"
        return 0
    fi
}

# ---- 2a: 下载核心代码（~5 MB，瞬间完成） ----
download_core() {
    local name="deepagent-core-${VERSION}"
    local url="${R2_BASE_URL}/${name}.tar.gz"

    log_info "下载核心代码..."
    log_info "  大小: ~6 MB"

    TMP_DIR=$(mktemp -d)
    local tarball="${TMP_DIR}/${name}.tar.gz"

    if curl_download "$url" "$tarball" "(R2)"; then
        download_verify_file "$tarball" "$name" || true
        log_success "核心代码下载完成"
    else
        log_error "核心代码下载失败！"
        log_info "请检查网络连接后重试。"
        log_info "URL: $url"
        rm -rf "$TMP_DIR"
        exit 1
    fi

    # 解压到安装目录
    log_info "解压核心代码..."
    mkdir -p "${INSTALL_DIR}/deepagent"
    tar xzf "$tarball" -C "${INSTALL_DIR}/deepagent"
    log_success "核心代码解压完成"

    CORE_TARBALL="$tarball"
}

# ---- 2b: uv sync 安装 Python 依赖（终端滚屏，用户等得起） ----
do_uv_sync() {
    local pkg_dir="${INSTALL_DIR}/deepagent"

    if [ ! -f "$pkg_dir/pyproject.toml" ]; then
        log_error "未找到 pyproject.toml，无法安装依赖"
        log_info "目录内容: $(ls "$pkg_dir" 2>/dev/null | head -10)"
        exit 1
    fi

    if [ -n "${UV_CMD:-}" ] && [ "$DISTRO" != "termux" ]; then
        log_info "安装 Python 依赖（uv sync）..."
        log_info "  终端将持续输出进度，请耐心等待"
        if (cd "$pkg_dir" && $UV_CMD sync 2>&1); then
            log_success "Python 依赖安装完成"
        else
            log_warn "uv sync 失败，尝试 pip 降级..."
            if [ ! -d "${INSTALL_DIR}/.venv" ]; then
                $UV_CMD venv "${INSTALL_DIR}/.venv" --python "$PYTHON_VERSION"
            fi
            $UV_CMD pip install --python "${INSTALL_DIR}/.venv/bin/python" -e "$pkg_dir" 2>/dev/null || {
                log_warn "pip 安装不完整，继续..."
                "${INSTALL_DIR}/.venv/bin/python" -m pip install --no-deps -e "$pkg_dir" 2>/dev/null || true
            }
        fi
    else
        log_info "使用 pip 安装 Python 依赖..."
        if [ ! -d "${INSTALL_DIR}/.venv" ]; then
            "$PYTHON_PATH" -m venv "${INSTALL_DIR}/.venv"
        fi
        "${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
        "${INSTALL_DIR}/.venv/bin/python" -m pip install -e "$pkg_dir" 2>/dev/null || {
            log_warn "pip 安装不完整，继续..."
            "${INSTALL_DIR}/.venv/bin/python" -m pip install --no-deps -e "$pkg_dir" 2>/dev/null || true
        }
        log_success "Python 依赖安装完成"
    fi
}

# ---- 2c: 下载 Embedded OpenCode（~97 MB，进度条可见） ----
download_embedded() {
    local name="deepagent-embedded-${VERSION}"
    local url="${R2_BASE_URL}/${name}.tar.gz"
    local tarball="${TMP_DIR}/${name}.tar.gz"

    log_info "下载嵌入式 OpenCode（${ARCH}）..."
    log_info "  大小: ~97 MB（含全部平台，安装脚本只提取当前架构）"

    if curl_download "$url" "$tarball" "(R2)"; then
        download_verify_file "$tarball" "$name" || true
        log_success "Embedded 包下载完成"
    else
        log_warn "Embedded 包下载失败（非致命，CLI 可用）"
        log_info "OpenCode 研发小组功能将不可用"
        return 0
    fi

    # 只提取当前平台的 OpenCode 二进制
    log_info "提取嵌入式组件..."
    local embed_dst="${INSTALL_DIR}/deepagent/embedded"
    mkdir -p "$embed_dst"

    # 检测二进制路径（macOS 用 macos-{arch}, Linux 用 linux-{arch}）
    local os_dir=""
    case "$OS" in
        macos) os_dir="macos" ;;
        linux) os_dir="linux" ;;
        *)     os_dir="linux" ;;
    esac

    local opencode_path="embedded/opencode/${os_dir}-${ARCH_SHORT}/opencode"

    if tar tzf "$tarball" "$opencode_path" >/dev/null 2>&1; then
        tar xzf "$tarball" -C "$embed_dst" "$opencode_path" 2>/dev/null || true
        chmod +x "${embed_dst}/${opencode_path}" 2>/dev/null || true
        log_success "OpenCode 已提取: ${opencode_path}"
    else
        log_warn "未找到 ${opencode_path}，跳过"
    fi

    EMBEDDED_TARBALL="$tarball"
}

# ============================================================================
# 复制辅助函数：优先使用 rsync（快速、增量），不可用时降级到 cp -r
# ============================================================================
copy_with_fallback() {
    local src="$1"
    local dst="$2"
    shift 2
    local rsync_args=("$@")

    if [ "${HAS_RSYNC:-false}" = true ]; then
        if [ ${#rsync_args[@]} -gt 0 ]; then
            rsync -a --delete "${rsync_args[@]}" "$src" "$dst"
        else
            rsync -a "$src" "$dst"
        fi
    else
        # rsync 不可用时的 cp 降级方案
        if [ -d "$src" ]; then
            mkdir -p "$dst"
            cp -r "$src"/* "$dst/" 2>/dev/null || cp -r "$src" "$dst"
        else
            cp -r "$src" "$dst"
        fi
    fi
}

# ============================================================================
# Step 3: 安装收尾
# ============================================================================
# core 已解压、uv sync 已完成、embedded 已提取。
# 这里只处理：skills 同步、版本写入、验证。
# WebUI 不在此安装，用户可通过 `deepagent webui install` 后装。
# ============================================================================

install_release() {
    local src_root="${INSTALL_DIR}/deepagent"

    # 判断是全新安装还是更新安装
    if [ -f "$INSTALL_DIR/VERSION" ]; then
        local old_version
        old_version=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
        IS_UPDATE=true
        log_info "检测到已有安装（版本: $old_version），执行更新..."
    else
        IS_UPDATE=false
        log_info "全新安装..."
    fi

    # ---- 备份旧版本（仅更新时） ----
    if [ "$IS_UPDATE" = true ]; then
        local backup_dir="${INSTALL_DIR}/.backup/$(date -u +%Y%m%d-%H%M%S)"
        log_info "备份旧版本到 ${backup_dir}..."
        mkdir -p "$backup_dir"
        for item in "deepagent" "webui" "VERSION" "skills/.bundled_manifest"; do
            if [ -e "${INSTALL_DIR}/${item}" ]; then
                local target_dir="$backup_dir/$(dirname "$item")"
                mkdir -p "$target_dir"
                cp -r "${INSTALL_DIR}/${item}" "$target_dir/" 2>/dev/null || true
            fi
        done
        [ -f "${INSTALL_DIR}/sessions.db" ] && cp "${INSTALL_DIR}/sessions.db" "$backup_dir/" 2>/dev/null || true
        log_success "备份完成"
    fi

    # ---- 创建辅助目录 ----
    mkdir -p "${INSTALL_DIR}"/{skills,logs}

    # ---- 复制系统 skills（从 core 目录到 skills/） ----
    if [ -d "$src_root/skills" ]; then
        log_info "复制系统 skills..."
        mkdir -p "${INSTALL_DIR}/skills"
        cp -r "$src_root/skills/"* "${INSTALL_DIR}/skills/" 2>/dev/null || true
        log_success "系统 skills 已复制"
    fi

    # ---- 写版本文件 ----
    if [ -f "$src_root/VERSION" ]; then
        cp "$src_root/VERSION" "${INSTALL_DIR}/VERSION" 2>/dev/null || true
    else
        echo "$VERSION" > "${INSTALL_DIR}/VERSION"
    fi
    log_success "版本: ${VERSION}"

    # ---- 安装后验证 ----
    local py_file_count
    py_file_count=$(find "$src_root" -type f -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$py_file_count" -lt 10 ]; then
        log_error "安装失败：Python 文件过少（仅 $py_file_count 个）"
        log_info "目录内容: $(ls "$src_root" 2>/dev/null | head -20)"
        rm -rf "$TMP_DIR"
        exit 1
    fi
    log_success "安装验证通过（$py_file_count 个 Python 文件）"
}

# ---- 创建 deepagent 符号链接（单独函数，便于测试/维护） ----
create_symlink() {
    log_info "创建 deepagent 命令符号链接..."

    local command_link_dir
    command_link_dir="$(get_command_link_dir)"
    mkdir -p "$command_link_dir"

    # 依次搜索可能安装 deepagent CLI 的位置
    local deepagent_bin=""
    local search_paths=(
        "${INSTALL_DIR}/deepagent/.venv/bin/deepagent"
        "${INSTALL_DIR}/.venv/bin/deepagent"
        "${INSTALL_DIR}/deepagent/deepagent"
    )

    for path in "${search_paths[@]}"; do
        if [ -x "$path" ]; then
            deepagent_bin="$path"
            break
        fi
    done

    if [ -n "$deepagent_bin" ]; then
        ln -sf "$deepagent_bin" "$command_link_dir/deepagent"
        log_success "符号链接创建: $(get_command_link_display_dir)/deepagent → $deepagent_bin"
    else
        # 找不到 deepagent 可执行文件，创建包装脚本
        # 确定 Python 路径：优先使用 deepagent 目录内的 .venv
        local python_path="${INSTALL_DIR}/deepagent/.venv/bin/python"
        if [ ! -x "$python_path" ]; then
            python_path="${INSTALL_DIR}/.venv/bin/python"
        fi
        if [ ! -x "$python_path" ]; then
            python_path="$PYTHON_PATH"
        fi

        log_info "未找到 deepagent 二进制，创建包装脚本..."
        cat > "$command_link_dir/deepagent" << WRAPPER_EOF
#!/bin/bash
# DeepAgent CLI launcher（由 install-release.sh 生成）
exec "${python_path}" -m hermes_cli.main "\$@"
WRAPPER_EOF
        chmod +x "$command_link_dir/deepagent"
        log_success "包装脚本已创建: $(get_command_link_display_dir)/deepagent"
    fi

    log_success "命令符号链接设置完成"
}

# ============================================================================
# Step 4: Skill 同步
# ============================================================================
# 复用 Hermes skills_sync.py 机制：基于 MD5 目录哈希的 manifest。
# 用户改过的 skill → 不覆盖。详见 skills_sync.py 源码。
# ============================================================================

sync_skills() {
    log_info "同步系统 skills 到用户目录..."

    # Release 包中 skills 的源目录（核心代码已解压到 INSTALL_DIR/deepagent/）
    local bundled_skills_dir="${INSTALL_DIR}/deepagent/skills"
    # 用户 skills 目标目录
    local user_skills_dir="${INSTALL_DIR}/skills"
    # manifest 文件：记录每个 skill 的原始哈希，用于检测用户修改
    local manifest_file="${user_skills_dir}/.bundled_manifest"

    # 创建用户 skills 目录
    mkdir -p "$user_skills_dir"

    # 策略 A：优先使用 Hermes 的 skills_sync.py（基于 manifest hash 的智能同步）
    local skills_sync_script="${INSTALL_DIR}/deepagent/tools/skills_sync.py"
    if [ -f "$skills_sync_script" ] && [ -x "$(command -v python3 2>/dev/null || echo "${INSTALL_DIR}/deepagent/.venv/bin/python")" ]; then
        local py_cmd
        if [ -x "${INSTALL_DIR}/deepagent/.venv/bin/python" ]; then
            py_cmd="${INSTALL_DIR}/deepagent/.venv/bin/python"
        elif [ -x "${INSTALL_DIR}/.venv/bin/python" ]; then
            py_cmd="${INSTALL_DIR}/.venv/bin/python"
        else
            py_cmd="python3"
        fi

        if $py_cmd "$skills_sync_script" 2>/dev/null; then
            log_success "Skills 同步完成（Python skills_sync）"
            return 0
        fi
        log_warn "Python skills_sync 失败，降级到 bash 同步..."
    fi

    # 策略 B：纯 bash 实现的 manifest 同步
    if [ ! -d "$bundled_skills_dir" ]; then
        log_warn "未找到 bundled skills 源目录，跳过 skills 同步"
        return 0
    fi

    log_info "使用 bash 方式同步 skills（manifest 驱动）..."

    # 读取旧的 manifest（记录已同步 skill 的哈希值）
    local old_manifest=""
    if [ -f "$manifest_file" ]; then
        old_manifest=$(cat "$manifest_file")
    fi

    # 扫描 bundled skills，构建新 manifest
    local new_manifest=""
    local has_md5=false
    command -v md5sum &>/dev/null && has_md5=true
    command -v md5 &>/dev/null && has_md5=true

    for skill_dir in "$bundled_skills_dir"/*/; do
        [ -d "$skill_dir" ] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")

        # 计算 bundled skill 的 MD5 哈希（所有文件递归）
        local skill_hash
        if command -v md5sum &>/dev/null; then
            skill_hash=$(find "$skill_dir" -type f -exec md5sum {} + | sort -k2 | md5sum | cut -d' ' -f1 2>/dev/null || echo "unknown")
        elif command -v md5 &>/dev/null; then
            skill_hash=$(find "$skill_dir" -type f -exec md5 -r {} + | sort -k2 | md5 -r | cut -d' ' -f1 2>/dev/null || echo "unknown")
        else
            skill_hash="unknown"
        fi

        new_manifest="${new_manifest}${skill_name}:${skill_hash}"$'\n'

        # 判断是否需要同步该 skill
        local user_skill_dir="${user_skills_dir}/${skill_name}"
        local old_hash
        old_hash=$(echo "$old_manifest" | grep "^${skill_name}:" | cut -d: -f2-)

        if [ ! -d "$user_skill_dir" ]; then
            # 全新 skill，直接复制
            log_info "  新增 skill: ${skill_name}"
            cp -r "$skill_dir" "$user_skills_dir/" 2>/dev/null || true
        elif [ -z "$old_hash" ] || [ "$skill_hash" != "$old_hash" ]; then
            # 旧 manifest 无此记录或 bundled 已更新 → 检查用户是否改过
            local user_hash
            if command -v md5sum &>/dev/null; then
                user_hash=$(find "$user_skill_dir" -type f -exec md5sum {} + | sort -k2 | md5sum | cut -d' ' -f1 2>/dev/null || echo "")
            elif command -v md5 &>/dev/null; then
                user_hash=$(find "$user_skill_dir" -type f -exec md5 -r {} + | sort -k2 | md5 -r | cut -d' ' -f1 2>/dev/null || echo "")
            fi

            if [ -n "$old_hash" ] && [ -n "$user_hash" ] && [ "$user_hash" != "$old_hash" ]; then
                # 用户改过 → 不覆盖
                log_info "  保留（用户已修改）: ${skill_name}"
            else
                # 用户未改 → 安全更新
                log_info "  更新 skill: ${skill_name}"
                rm -rf "$user_skill_dir"
                cp -r "$skill_dir" "$user_skills_dir/" 2>/dev/null || true
            fi
        else
            # 哈希一致 → 最新，跳过
            :
        fi
    done

    # 写入新 manifest
    echo "$new_manifest" > "$manifest_file"
    log_success "Skills manifest 已更新: $manifest_file"
}

# ============================================================================
# Step 5: 配置保留
# ============================================================================
# .env、config.yaml 和 sessions.db 的保留策略：
#   全新安装 → 从模板创建
#   更新安装 → ✅ 保留已有文件
# ============================================================================

setup_config() {
    log_info "配置保留策略..."

    # 创建配置目录
    mkdir -p "$INSTALL_DIR"

    # ---- .env 配置 ----
    local env_file="${INSTALL_DIR}/.env"
    local env_template="${INSTALL_DIR}/deepagent/.env.example"

    if [ ! -f "$env_file" ]; then
        if [ -f "$env_template" ]; then
            cp "$env_template" "$env_file"
            log_success ".env 已从模板创建"
        else
            # 创建最小 .env 模板
            cat > "$env_file" << 'ENV_EOF'
# DeepAgent 环境配置
# 复制此文件并填入你的 API Key
# 完整模板请参考源码仓库的 .env.example

# LLM 提供商 API Key（至少需要一个）
# OPENROUTER_API_KEY=
# DEEPSEEK_API_KEY=

# WebUI 服务配置
WEBUI_HOST=127.0.0.1
WEBUI_PORT=8648
ENV_EOF
            log_success ".env 已创建（最小模板）"
        fi
    else
        log_info ".env 已存在，保留中..."
    fi

    # ---- config.yaml 配置 ----
    local config_file="${INSTALL_DIR}/config.yaml"
    local config_template="${INSTALL_DIR}/deepagent/cli-config.yaml.example"

    if [ ! -f "$config_file" ]; then
        if [ -f "$config_template" ]; then
            cp "$config_template" "$config_file"
            log_success "config.yaml 已从模板创建"
        else
            # 创建最小 config.yaml
            cat > "$config_file" << 'CONFIG_EOF'
# DeepAgent 配置
# 运行时配置，更多选项请参考完整示例

model:
  default: "deepseek/deepseek-v4-pro"

display:
  skin: default
CONFIG_EOF
            log_success "config.yaml 已创建（最小配置）"
        fi
    else
        log_info "config.yaml 已存在，保留中..."
    fi

    log_success "配置保留策略执行完毕"
}

# ============================================================================
# Step 6: PATH 配置
# ============================================================================
# 确保 ~/.local/bin 在 PATH 中，以便 deepagent 命令立即可用。
# 添加 PATH 配置到 shell 配置文件（.zshrc / .bashrc / .profile / config.fish）。
# ============================================================================

setup_path() {
    log_info "配置 PATH..."

    local command_link_dir
    local command_link_display_dir
    command_link_dir="$(get_command_link_dir)"
    command_link_display_dir="$(get_command_link_display_dir)"

    # 检测用户登录 shell（无论 PATH 中是否已有，都确保 shell config 有持久配置）
    local shell_configs=()
    local is_fish=false
    local login_shell
    login_shell="$(basename "${SHELL:-/bin/bash}")"

    case "$login_shell" in
        zsh)
            [ -f "$HOME/.zshrc" ] && shell_configs+=("$HOME/.zshrc")
            [ -f "$HOME/.zprofile" ] && shell_configs+=("$HOME/.zprofile")
            # 如果都不存在，创建 ~/.zshrc（常见于新 macOS）
            if [ ${#shell_configs[@]} -eq 0 ]; then
                touch "$HOME/.zshrc" 2>/dev/null || true
                [ -f "$HOME/.zshrc" ] && shell_configs+=("$HOME/.zshrc")
            fi
            ;;
        bash)
            [ -f "$HOME/.bashrc" ] && shell_configs+=("$HOME/.bashrc")
            [ -f "$HOME/.bash_profile" ] && shell_configs+=("$HOME/.bash_profile")
            ;;
        fish)
            is_fish=true
            local fish_config="$HOME/.config/fish/config.fish"
            mkdir -p "$(dirname "$fish_config")" 2>/dev/null || true
            touch "$fish_config" 2>/dev/null || true
            ;;
        *)
            [ -f "$HOME/.bashrc" ] && shell_configs+=("$HOME/.bashrc")
            [ -f "$HOME/.zshrc" ] && shell_configs+=("$HOME/.zshrc")
            ;;
    esac

    # 也确保 ~/.profile 包含 PATH（登录 shell 在跳过 ~/.bashrc 时使用）
    if [ "$is_fish" = false ] && [ -f "$HOME/.profile" ]; then
        shell_configs+=("$HOME/.profile")
    fi

    local path_line="export PATH=\"$command_link_dir:\$PATH\""

    for config_file in "${shell_configs[@]}"; do
        if ! grep -v '^[[:space:]]*#' "$config_file" 2>/dev/null | grep -qE 'PATH=.*\.local/bin'; then
            echo "" >> "$config_file"
            echo "# DeepAgent — 确保命令目录在 PATH 中" >> "$config_file"
            echo "$path_line" >> "$config_file"
            log_success "已将 $command_link_display_dir 添加到 PATH 中 ($config_file)"
        fi
    done

    # fish shell 使用 fish_add_path 而非 export PATH=
    if [ "$is_fish" = true ]; then
        local fish_config="$HOME/.config/fish/config.fish"
        if ! grep -q 'fish_add_path.*\.local/bin' "$fish_config" 2>/dev/null; then
            echo "" >> "$fish_config"
            echo "# DeepAgent — 确保命令目录在 PATH 中" >> "$fish_config"
            echo "fish_add_path \"$command_link_dir\"" >> "$fish_config"
            log_success "已将 $command_link_display_dir 添加到 PATH 中 ($fish_config)"
        fi
    fi

    # 为当前会话导出 PATH
    export PATH="$command_link_dir:$PATH"

    log_success "PATH 配置完成"
}

# ============================================================================
# Step 7: Desktop DMG 自动弹出（仅 macOS）
# ============================================================================
# 下载 DeepAgent DMG 到 ~/Downloads/，挂载并打开 Finder。
# 用户可关闭 Finder 跳过 Desktop 安装，不影响 CLI 使用。
# ============================================================================

maybe_download_dmg() {
    # 桌面版下载是安装流程的一部分，不是可选步骤
    # 安装过程自动尝试下载，失败不阻塞流程
    DMG_INSTALLED=false

    # 仅在 macOS 上提供 DMG
    [ "$OS" != "macos" ] && return 0

    echo ""
    log_info "🖥️  下载 DeepAgent 桌面版..."

    # 按优先级尝试架构：当前架构优先，然后回退
    local dmg_arches=()
    if [ "$ARCH_SHORT" = "arm64" ]; then
        dmg_arches=("arm64" "x64")
    else
        dmg_arches=("x64" "arm64")
    fi

    local dmg_downloaded=false
    local dmg_path=""

    for arch_try in "${dmg_arches[@]}"; do
        local dmg_name="DeepAgent-${VERSION}-${arch_try}.dmg"
        local dmg_url="${R2_BASE_URL}/${dmg_name}"
        dmg_path="${HOME}/Downloads/${dmg_name}"

            log_info "Trying: ${dmg_name}"
            if curl -fsSL --connect-timeout 10 --max-time 600 "$dmg_url" -o "$dmg_path" 2>/dev/null; then
            log_success "DMG downloaded: ${dmg_path}"
            dmg_downloaded=true
            break
        fi
        log_info "  ${dmg_name} not available"
    done

    if [ "$dmg_downloaded" = true ]; then
        DMG_INSTALLED=true
        log_info "Mounting DMG..."
        if hdiutil attach "$dmg_path" -mountpoint "/Volumes/DeepAgent" 2>/dev/null; then
            log_success "DMG mounted. To install: drag DeepAgent.app to Applications"
            open "/Volumes/DeepAgent" 2>/dev/null || true
            echo ""
            log_info "If you close the window, install later from: ${dmg_path}"
        else
            log_warn "DMG mount failed. Install manually: open ${dmg_path}"
        fi
    else
        log_warn "Desktop DMG not available for download yet"
        log_info "CLI version is unaffected — run 'deepagent' to start"
    fi
}

# ============================================================================
# Step 8: 自动启动
# ============================================================================
# 安装完成后自动启动 DeepAgent WebUI（或桌面版），打开浏览器。
# 用户无需手动输入命令。
# ============================================================================

auto_start() {
    local webui_port=8648
    local webui_url="http://localhost:${webui_port}"

    echo ""
    log_info "Starting DeepAgent..."

    # 判断优先启动桌面版还是 WebUI
    if [ "$DMG_INSTALLED" = true ] && [ -d "/Applications/DeepAgent.app" ]; then
        log_info "Opening DeepAgent desktop app..."
        open "/Applications/DeepAgent.app" 2>/dev/null || true
    else
        # 启动 WebUI 服务（需要 Node.js）
        local node_cmd=""
        if command -v node &>/dev/null; then
            node_cmd="node"
        elif [ -x "${INSTALL_DIR}/webui/bin/node" ]; then
            node_cmd="${INSTALL_DIR}/webui/bin/node"
        fi

        if [ -n "$node_cmd" ] && [ -f "${INSTALL_DIR}/webui/bin/hermes-web-ui.mjs" ]; then
            log_info "Starting WebUI server..."
            mkdir -p "${INSTALL_DIR}/logs"
            nohup "$node_cmd" "${INSTALL_DIR}/webui/bin/hermes-web-ui.mjs" \
                start --port "$webui_port" \
                >> "${INSTALL_DIR}/logs/webui.log" 2>&1 &
            local webui_pid=$!
            echo "$webui_pid" > "${INSTALL_DIR}/webui/server.pid" 2>/dev/null || true

            # Wait up to 15s for server readiness
            local waited=0
            while [ $waited -lt 15 ]; do
                if curl -s "http://127.0.0.1:${webui_port}/health" > /dev/null 2>&1; then
                    break
                fi
                sleep 1
                waited=$((waited + 1))
            done
            log_success "WebUI started (PID: $webui_pid)"
        fi

        # 打开浏览器
        if command -v open &>/dev/null; then
            open "${webui_url}" 2>/dev/null || true
        elif command -v xdg-open &>/dev/null; then
            xdg-open "${webui_url}" 2>/dev/null || true
        fi
    fi

    echo ""
    log_info "WebUI address: ${webui_url}"
    log_info "Default login: admin / 123456"
    log_info "CLI command:   deepagent"
    log_info "You can also access the WebUI from any browser at the address above."
}

# ============================================================================
# Step 9: 开机自启设置
# ============================================================================
# 询问用户是否设置开机自启。这是安装过程中唯一必需的用户交互。
# macOS: LaunchAgents（plist）
# Linux: systemd --user service（无需 sudo）
# ============================================================================

setup_autostart() {
    local autostart_choice
    echo ""
    printf "Set DeepAgent to auto-start on boot? [Y/n] "
    read -r autostart_choice < /dev/tty 2>/dev/null || autostart_choice="y"

    if [[ $autostart_choice =~ ^[Yy]$ ]] || [[ -z $autostart_choice ]]; then
        local link_dir
        link_dir="$(get_command_link_dir)"

        case "$OS" in
            macos)
                local plist_dir="$HOME/Library/LaunchAgents"
                local plist_file="${plist_dir}/com.deepagent.plist"
                mkdir -p "$plist_dir"
                cat > "$plist_file" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.deepagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>${link_dir}/deepagent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
</dict>
</plist>
PLIST_EOF
                launchctl load "$plist_file" 2>/dev/null || true
                log_success "Auto-start configured (LaunchAgent)"
                ;;
            linux)
                local systemd_dir="$HOME/.config/systemd/user"
                local service_file="${systemd_dir}/deepagent.service"
                mkdir -p "$systemd_dir"
                cat > "$service_file" << SERVICE_EOF
[Unit]
Description=DeepAgent - AI Digital Twin
After=network.target

[Service]
Type=simple
ExecStart=${link_dir}/deepagent
WorkingDirectory=${INSTALL_DIR}
Restart=on-failure

[Install]
WantedBy=default.target
SERVICE_EOF
                systemctl --user daemon-reload 2>/dev/null || true
                systemctl --user enable deepagent.service 2>/dev/null || true
                log_success "Auto-start configured (systemd --user)"
                ;;
            *)
                log_warn "Auto-start not supported on $OS yet"
                log_info "Run 'deepagent' manually to start"
                ;;
        esac
    else
        log_info "Auto-start skipped. Run 'deepagent' to start."
    fi
}

# ============================================================================
# Step 10: 完成提示
# ============================================================================

print_success() {
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│        ✓ DeepAgent 安装完成！                            │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
    echo ""

    # 文件位置概览
    echo -e "${CYAN}${BOLD}📁 安装位置:${NC}"
    echo ""
    echo -e "   ${YELLOW}安装目录:${NC}    $INSTALL_DIR"
    echo -e "   ${YELLOW}配置文件:${NC}    $INSTALL_DIR/config.yaml"
    echo -e "   ${YELLOW}环境变量:${NC}    $INSTALL_DIR/.env"
    echo -e "   ${YELLOW}命令行:${NC}      $(get_command_link_display_dir)/deepagent"
    echo -e "   ${YELLOW}版本:${NC}         $VERSION"
    echo ""

    # 后续步骤
    echo -e "${CYAN}${BOLD}🚀 快速开始:${NC}"
    echo ""
    echo -e "   直接输入 ${GREEN}deepagent${NC} 启动 CLI 模式"
    echo -e "   运行 ${GREEN}deepagent setup${NC} 完成交互式向导"
    echo -e "   运行 ${GREEN}deepagent webui install${NC} 安装 Web 管理界面"
    echo ""

    if [ "$OS" = "macos" ]; then
        echo -e "   🖥️  ${YELLOW}桌面版:${NC} 已下载到 ~/Downloads/，拖到 Applications 即可"
        echo ""
    fi

    echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}安装目录:${NC} $INSTALL_DIR"
    echo -e "${BOLD}如遇问题:${NC} https://github.com/${GH_REPO}/issues"
    echo ""
}

# ============================================================================
# 清理临时文件
# ============================================================================

cleanup() {
    if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
        log_info "临时文件已清理"
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    parse_args "$@"
    print_banner

    # ---- Step 1: 系统检测 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 1/6] 系统环境检测${NC}"
    detect_os
    detect_arch
    init_log_file
    log_install "START" "Installation started (version: ${VERSION:-latest})"
    check_prerequisites
    install_uv
    check_python
    check_node

    # ---- Step 2a: 下载核心代码 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 2/6] 下载核心代码${NC}"
    detect_sha256_cmd
    download_core

    # ---- Step 2b: 安装 Python 依赖 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 3/6] 安装 Python 依赖${NC}"
    do_uv_sync

    # ---- Step 2c: 下载嵌入式组件 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 4/6] 下载嵌入式组件${NC}"
    download_embedded

    # ---- Step 3: 安装收尾 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 5/6] 安装收尾${NC}"
    install_release
    create_symlink
    sync_skills

    # ---- Step 4: 配置 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 6/6] 配置${NC}"
    setup_config
    setup_path
    maybe_download_dmg

    echo ""
    echo -e "${BLUE}${BOLD}── 安装完成 ──${NC}"
    print_success

    # 结束日志
    log_install "DONE" "Installation completed successfully (version: ${VERSION:-latest})"

    # 清理临时文件
    cleanup
}

# 仅在直接执行时运行 main，被 source 时不执行（便于测试）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
