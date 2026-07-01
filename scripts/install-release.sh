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
GH_REPO="yuanchenglu/DeepAgent"
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
    echo "│  基于 Hermes 深度改造的数字分身（CEO）产品                │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

log_info()    { echo -e "${CYAN}→${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

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
                else
                    DISTRO="unknown"
                fi
            fi
            ;;
        Darwin*)
            OS="macos"
            DISTRO="macos"
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
            log_warn "未知操作系统，尝试继续..."
            ;;
    esac

    log_success "检测到操作系统: $OS ($DISTRO)"
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

# 检查 Node.js（仅警告，WebUI 已预构建不需要）
check_node() {
    if command -v node &> /dev/null; then
        local found_ver
        found_ver=$(node --version 2>/dev/null)
        log_success "Node.js $found_ver 已安装"
    else
        log_warn "Node.js 未安装（仅开发时需要，Release 版 WebUI 已预构建）"
        log_info "如果需要开发/构建 WebUI，请手动安装 Node.js 23+"
    fi
}

# ============================================================================
# Step 2: 下载 Release 包
# ============================================================================
# 从主源（R2）下载，失败则切备用源（GitHub Releases）。
# 校验和从 GitHub 获取（不同信任域），下载的 tarball 来自 R2。
# ============================================================================

# 获取最新版本号（当 VERSION=latest 时调用）
fetch_latest_version() {
    log_info "正在获取最新版本号..."
    # 从 GitHub API 获取最新 release 的 tag 名
    local api_url="https://api.github.com/repos/${GH_REPO}/releases/latest"
    local latest
    latest=$(curl -fsSL "$api_url" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])" 2>/dev/null || echo "")
    if [ -n "$latest" ]; then
        # tag 名通常为 v0.9.0 格式，去掉前缀 v
        VERSION="${latest#v}"
        log_success "最新版本: v${VERSION}"
    else
        log_warn "无法获取最新版本，使用默认版本 'latest'"
        VERSION="latest"
    fi
}

# 下载 Release tarball
download_release() {
    local version_display="${VERSION}"
    local tarball_name="deepagent-${VERSION}.tar.gz"
    local r2_url="${R2_BASE_URL}/${tarball_name}"
    local gh_url="${GH_BASE_URL}/v${VERSION}/${tarball_name}"

    # 创建临时目录
    TMP_DIR=$(mktemp -d)
    TARBALL_PATH="${TMP_DIR}/${tarball_name}"

    log_info "下载版本: v${version_display}"

    # 尝试从主源（R2）下载
    log_info "正在从主源下载: ${r2_url}"
    if curl -fsSL --connect-timeout 10 --max-time 120 "$r2_url" -o "$TARBALL_PATH"; then
        log_success "从主源下载成功"

        # 从 GitHub 获取 SHA256 校验和（不同信任域）
        local sha_url="${GH_BASE_URL}/v${VERSION}/deepagent-${VERSION}.sha256"
        local sha_file="${TMP_DIR}/deepagent-${VERSION}.sha256"

        if curl -fsSL --connect-timeout 10 --max-time 30 "$sha_url" -o "$sha_file" 2>/dev/null; then
            log_info "验证 SHA256 校验和..."
            if (cd "$TMP_DIR" && sha256sum -c "$(basename "$sha_file")" 2>/dev/null) || \
               (cd "$TMP_DIR" && shasum -a 256 -c "$(basename "$sha_file")" 2>/dev/null); then
                log_success "校验和验证通过 ✓"
            else
                log_error "校验和验证失败！下载的文件可能已损坏或被篡改。"
                log_info "文件: $TARBALL_PATH"
                log_info "预期校验和: $(cat "$sha_file")"
                log_info "实际 SHA256: $(sha256sum "$TARBALL_PATH" 2>/dev/null || shasum -a 256 "$TARBALL_PATH" 2>/dev/null)"
                rm -rf "$TMP_DIR"
                exit 1
            fi
        else
            log_warn "无法获取校验和文件，跳过验证"
            log_info "校验和 URL 不可用: $sha_url"
        fi
    else
        # 主源下载失败，尝试备用源（GitHub Releases）
        log_warn "主源下载失败，尝试备用源..."
        log_info "正在从 GitHub Releases 下载: ${gh_url}"

        if curl -fsSL --connect-timeout 10 --max-time 120 "$gh_url" -o "$TARBALL_PATH"; then
            log_success "从备用源（GitHub Releases）下载成功"
        else
            log_error "下载失败！主源和备用源均不可用。"
            log_info "请检查网络连接后重试。"
            log_info "主源: $r2_url"
            log_info "备用: $gh_url"
            rm -rf "$TMP_DIR"
            exit 1
        fi
    fi
}

# ============================================================================
# Step 3: 安装
# ============================================================================
# 判断全新安装 vs 更新安装，复制文件、uv sync 安装 Python 依赖。
# 注意：不执行 electron-builder（耗时且无 GUI 环境会失败）。
# 注意：不执行 npm build（WebUI 已预构建包含在包中）。
# ============================================================================

install_release() {
    local extract_dir="${TMP_DIR}/deepagent-${VERSION}"

    log_info "解压 Release 包..."
    tar xzf "$TARBALL_PATH" -C "$TMP_DIR"

    if [ ! -d "$extract_dir" ]; then
        # 尝试查找解压后的唯一目录
        extract_dir=$(ls -d "$TMP_DIR"/*/ 2>/dev/null | head -1)
        if [ -z "$extract_dir" ] || [ ! -d "$extract_dir" ]; then
            log_error "解压失败：无法找到解压后的目录"
            rm -rf "$TMP_DIR"
            exit 1
        fi
    fi

    log_success "Release 包解压成功"

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

        # 备份核心目录和文件（不备份 .env、config.yaml、用户 skills）
        for item in "deepagent" "webui" "VERSION" "sessions.db" "skills/.bundled_manifest"; do
            if [ -e "${INSTALL_DIR}/${item}" ]; then
                local target_dir="$backup_dir/$(dirname "$item")"
                mkdir -p "$target_dir"
                cp -r "${INSTALL_DIR}/${item}" "$target_dir/" 2>/dev/null || true
            fi
        done
        log_success "备份完成"
    fi

    # ---- 复制文件 ----
    log_info "安装文件到 ${INSTALL_DIR}..."

    # 创建安装目录
    mkdir -p "$INSTALL_DIR"/{deepagent,webui,skills,logs}

    # 复制 deepagent Python 包（排除 venv，更新时保留用户 venv）
    log_info "复制 deepagent 核心模块..."
    if [ -d "$extract_dir/deepagent" ]; then
        # 使用 rsync 高效同步，排除 __pycache__ 和 .pyc
        rsync -a --delete \
            --exclude="__pycache__" \
            --exclude="*.pyc" \
            --exclude=".pyo" \
            --exclude="venv/" \
            --exclude="*.egg-info/" \
            "$extract_dir/deepagent/" "${INSTALL_DIR}/deepagent/"
        log_success "deepagent 核心模块已复制"
    fi

    # 复制预构建 WebUI
    if [ -d "$extract_dir/webui" ]; then
        log_info "复制 WebUI（预构建）..."
        # 保留 dist/ 和 src/ 目录结构
        rsync -a --delete \
            --exclude="node_modules" \
            "$extract_dir/webui/" "${INSTALL_DIR}/webui/"
        log_success "WebUI 已复制"
    fi

    # 复制系统 skills（manifest 同步在 Step 4 处理）
    if [ -d "$extract_dir/skills" ]; then
        log_info "复制系统 skills..."
        mkdir -p "${INSTALL_DIR}/skills"
        rsync -a "$extract_dir/skills/" "${INSTALL_DIR}/skills/" 2>/dev/null || true
        log_success "系统 skills 已复制"
    fi

    # 写版本文件
    echo "$VERSION" > "${INSTALL_DIR}/VERSION"
    log_success "版本文件已更新: $VERSION"

    # ---- uv sync 安装 Python 依赖 ----
    if [ -f "${INSTALL_DIR}/deepagent/pyproject.toml" ] || [ -f "${INSTALL_DIR}/deepagent/setup.py" ] || [ -f "${INSTALL_DIR}/deepagent/setup.cfg" ]; then
        local pkg_dir="${INSTALL_DIR}/deepagent"

        if [ -n "${UV_CMD:-}" ] && [ "$DISTRO" != "termux" ]; then
            log_info "使用 uv sync 安装 Python 依赖..."
            # 确保有 venv
            if [ ! -d "${INSTALL_DIR}/.venv" ]; then
                $UV_CMD venv "${INSTALL_DIR}/.venv" --python "$PYTHON_VERSION"
            fi

            # 在 venv 上下文中安装 deepagent 包
            if $UV_CMD pip install --python "${INSTALL_DIR}/.venv/bin/python" -e "$pkg_dir" 2>/dev/null; then
                log_success "Python 依赖安装完成 (uv sync)"
            else
                log_warn "uv sync 部分失败，尝试降级安装方式..."
                # 降级：仅安装核心依赖
                "${INSTALL_DIR}/.venv/bin/python" -m pip install --no-deps -e "$pkg_dir" 2>/dev/null || true
            fi
        else
            # 无 uv 时使用标准 pip
            if [ "$DISTRO" = "termux" ] || [ -z "${UV_CMD:-}" ]; then
                log_info "使用 pip 安装 Python 依赖..."
                if [ ! -d "${INSTALL_DIR}/.venv" ]; then
                    "$PYTHON_PATH" -m venv "${INSTALL_DIR}/.venv"
                fi
                "${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
                "${INSTALL_DIR}/.venv/bin/python" -m pip install -e "$pkg_dir" 2>/dev/null || {
                    log_warn "pip 安装不完整，尝试最小安装..."
                    "${INSTALL_DIR}/.venv/bin/python" -m pip install --no-deps -e "$pkg_dir" 2>/dev/null || true
                }
                log_success "Python 依赖安装完成 (pip)"
            fi
        fi
    else
        log_warn "未找到 pyproject.toml 或 setup.py，跳过 Python 依赖安装"
        log_info "请稍后手动运行: cd ${INSTALL_DIR}/deepagent && pip install -e ."
    fi

    # ---- 创建符号链接 ----
    local command_link_dir
    command_link_dir="$(get_command_link_dir)"
    mkdir -p "$command_link_dir"

    # 确定 deepagent 可执行文件路径
    local deepagent_bin=""
    if [ -x "${INSTALL_DIR}/.venv/bin/deepagent" ]; then
        deepagent_bin="${INSTALL_DIR}/.venv/bin/deepagent"
    elif [ -x "${INSTALL_DIR}/deepagent/deepagent" ]; then
        deepagent_bin="${INSTALL_DIR}/deepagent/deepagent"
    elif [ -f "${INSTALL_DIR}/deepagent/deepagent" ]; then
        deepagent_bin="${INSTALL_DIR}/deepagent/deepagent"
    fi

    if [ -n "$deepagent_bin" ]; then
        ln -sf "$deepagent_bin" "$command_link_dir/deepagent"
        log_success "符号链接创建: $(get_command_link_display_dir)/deepagent"
    else
        # 如果找不到 deepagent 可执行文件，创建一个指向 venv 模块的包装脚本
        log_info "创建 deepagent 包装脚本..."
        cat > "$command_link_dir/deepagent" << WRAPPER_EOF
#!/bin/bash
# DeepAgent CLI launcher (由 install-release.sh 生成)
exec "${INSTALL_DIR}/.venv/bin/python" -m hermes_cli.main "\$@"
WRAPPER_EOF
        chmod +x "$command_link_dir/deepagent"
        log_success "包装脚本已创建: $(get_command_link_display_dir)/deepagent"
    fi

    log_success "文件安装完成"
}

# ============================================================================
# Step 4: Skill 同步
# ============================================================================
# 复用 Hermes skills_sync.py 机制：基于 MD5 目录哈希的 manifest。
# 用户改过的 skill → 不覆盖。详见 skills_sync.py 源码。
# ============================================================================

sync_skills() {
    log_info "同步系统 skills 到用户目录..."

    local skills_sync_script="${INSTALL_DIR}/tools/skills_sync.py"
    local bundled_skills_dir="${INSTALL_DIR}/skills"

    # 创建用户 skills 目录
    mkdir -p "${INSTALL_DIR}/skills"

    # 构建 .bundled_manifest（描述系统 bundled skills 的哈希清单）
    if [ -d "$bundled_skills_dir" ]; then
        log_info "生成 skills manifest..."

        # 扫描 bundled skills 目录，为每个 skill 计算 MD5 哈希
        local manifest_file="${INSTALL_DIR}/skills/.bundled_manifest"
        : > "$manifest_file"  # 清空 manifest 文件

        for skill_dir in "$bundled_skills_dir"/*/; do
            [ -d "$skill_dir" ] || continue
            local skill_name
            skill_name=$(basename "$skill_dir")

            # 计算整个 skill 目录的 MD5 哈希（递归）
            local skill_hash
            if command -v md5sum &> /dev/null; then
                skill_hash=$(find "$skill_dir" -type f -exec md5sum {} + | sort -k2 | md5sum | cut -d' ' -f1)
            elif command -v md5 &> /dev/null; then
                skill_hash=$(find "$skill_dir" -type f -exec md5 -r {} + | sort -k2 | md5 -r | cut -d' ' -f1)
            else
                skill_hash="unknown"
            fi

            echo "${skill_name}:${skill_hash}" >> "$manifest_file"
        done

        log_success "Skills manifest 已生成（${#manifest_file}）"
    else
        log_warn "未找到 bundled skills 目录，跳过 skills 同步"
    fi

    # 尝试使用 skills_sync.py（如果存在）
    if [ -f "$skills_sync_script" ] && [ -x "${INSTALL_DIR}/.venv/bin/python" ]; then
        if "${INSTALL_DIR}/.venv/bin/python" "$skills_sync_script" 2>/dev/null; then
            log_success "Skills 同步完成（Python sync）"
            return 0
        fi
    fi

    # 降级：简单目录复制（仅复制不存在的 skill 到用户目录）
    if [ -d "$bundled_skills_dir" ]; then
        for skill_dir in "$bundled_skills_dir"/*/; do
            [ -d "$skill_dir" ] || continue
            local skill_name
            skill_name=$(basename "$skill_dir")
            local user_skill_dir="${INSTALL_DIR}/skills/${skill_name}"

            # 仅在用户目录中不存在该 skill 时才复制
            if [ ! -d "$user_skill_dir" ]; then
                cp -r "$skill_dir" "$user_skill_dir" 2>/dev/null || true
            fi
        done
        log_success "Skills 同步完成（目录复制）"
    fi
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

    # 检查 ~/.local/bin 是否已在 PATH 中
    if echo "$PATH" | tr ':' '\n' | grep -q "^$command_link_dir$"; then
        log_info "$command_link_display_dir 已在 PATH 中"
        export PATH="$command_link_dir:$PATH"
        return 0
    fi

    # 检测用户登录 shell
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
    # 仅在 macOS 上提供 DMG 提示
    [ "$OS" != "macos" ] && return 0
    # 非交互式模式跳过
    [ "$IS_INTERACTIVE" = false ] && return 0

    echo ""
    log_info "🖥️  DeepAgent 桌面版（可选）..."
    log_info "DeepAgent 提供 macOS 桌面应用（基于 Electron），可作为独立窗口使用。"
    echo ""
    printf "是否下载桌面版 DMG？[y/N] "
    read -r dmg_answer < /dev/tty 2>/dev/null || dmg_answer="n"

    if [[ $dmg_answer =~ ^[Yy]$ ]]; then
        local dmg_name="DeepAgent-${VERSION}-arm64.dmg"
        local dmg_url="${R2_BASE_URL}/${dmg_name}"
        local dmg_path="${HOME}/Downloads/${dmg_name}"

        log_info "正在下载桌面版 DMG..."
        log_info "URL: ${dmg_url}"

        if curl -fsSL --connect-timeout 10 --max-time 180 "$dmg_url" -o "$dmg_path"; then
            log_success "DMG 已下载到: ${dmg_path}"

            # 挂载 DMG 并打开 Finder
            log_info "挂载 DMG..."
            if hdiutil attach "$dmg_path" -mountpoint "/Volumes/DeepAgent" 2>/dev/null; then
                log_success "DMG 已挂载"
                # 打开 Finder 窗口提示用户拖拽安装
                open "/Volumes/DeepAgent" 2>/dev/null || true
                echo ""
                log_info "📋 请将 DeepAgent.app 拖到 Applications 文件夹完成桌面版安装"
                log_info "（关掉 Finder 窗口即可跳过，不影响终端使用）"
            else
                log_warn "DMG 挂载失败，文件已保存到 ${dmg_path}"
                log_info "请手动打开 DMG 安装桌面版"
            fi
        else
            log_warn "DMG 下载失败，跳过桌面版安装"
            log_info "稍后可手动下载: ${dmg_url}"
        fi
    else
        log_info "已跳过桌面版安装。如需安装，请访问: https://deepseekagent.starseas.org/download"
    fi
}

# ============================================================================
# Step 8: 完成提示
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
    echo -e "   运行 ${GREEN}deepagent update --check${NC} 查看更新"
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
    echo -e "${BLUE}${BOLD}[Step 1/8] 系统环境检测${NC}"
    detect_os
    install_uv
    check_python
    check_node

    # ---- Step 2: 下载 Release 包 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 2/8] 下载 Release 包${NC}"
    if [ "$VERSION" = "latest" ] || [ "$VERSION" = "DEFAULT_VERSION" ]; then
        fetch_latest_version
    fi
    download_release

    # ---- Step 3: 安装 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 3/8] 安装 DeepAgent${NC}"
    install_release

    # ---- Step 4: Skill 同步 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 4/8] 技能同步${NC}"
    sync_skills

    # ---- Step 5: 配置保留 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 5/8] 配置保留${NC}"
    setup_config

    # ---- Step 6: PATH 配置 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 6/8] PATH 配置${NC}"
    setup_path

    # ---- Step 7: Desktop DMG（macOS 可选） ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 7/8] 桌面版安装（可选）${NC}"
    maybe_download_dmg

    # ---- Step 8: 完成提示 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 8/8] 安装完成${NC}"
    print_success

    # 清理临时文件
    cleanup
}

main "$@"
