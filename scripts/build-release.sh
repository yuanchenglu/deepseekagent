#!/bin/bash
# ============================================================================
# DeepAgent Release Tarball Builder
# ============================================================================
# 从当前源码目录构建 Release tarball，用于上传到 Cloudflare R2 和 GitHub Releases。
#
# 用法:
#   ./scripts/build-release.sh                          # 从 VERSION 文件读取版本
#   ./scripts/build-release.sh --version 0.9.0          # 指定版本号
#   ./scripts/build-release.sh --version 0.9.0-beta.1   # pre-release 版本
#
# 产物:
#   dist/releases/deepagent-{VERSION}.tar.gz
#   dist/releases/deepagent-{VERSION}.sha256
#
# Step 1:  解析版本参数（默认从 VERSION 文件读取）
# Step 2:  校验版本号格式
# Step 3:  检查预构建 WebUI 是否存在
# Step 4:  检查内置 OpenCode 二进制是否存在
# Step 5:  构建 Skills bundled manifest
# Step 6:  创建 dist/releases/ 输出目录
# Step 7:  用 tar 打包，排除 dev/构建产物
# Step 8:  包含指定路径清单
# Step 9:  生成 SHA256 校验和
# Step 10: 打印成功信息
# ============================================================================

set -euo pipefail

# ---- 颜色定义（复用 install-release.sh 风格） ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ---- 项目根目录（脚本位于 scripts/build-release.sh） ----
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ---- 默认配置 ----
VERSION_FILE="${PROJECT_ROOT}/VERSION"          # 版本号文件（含 v 前缀）
DIST_DIR="${PROJECT_ROOT}/dist/releases"         # 产物输出目录
TARBALL_NAME=""                                  # 由版本号决定
VERSION=""                                       # 用户指定或从文件读取

# ============================================================================
# 辅助函数
# ============================================================================

log_info()    { echo -e "${CYAN}→${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

# ============================================================================
# Step 1: 解析版本参数（默认从 VERSION 文件读取）
# ============================================================================

parse_version() {
    if [ -n "$VERSION" ]; then
        # 用户通过 --version 显式指定
        log_info "使用命令行指定的版本号: ${VERSION}"
    elif [ -f "$VERSION_FILE" ]; then
        # 从 VERSION 文件读取（内容示例: "v0.9.0-alpha.1"）
        VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
        log_info "从 VERSION 文件读取版本号: ${VERSION}"
    else
        log_error "未指定版本号且 VERSION 文件不存在"
        log_info "请通过 --version X.Y.Z 指定版本号"
        exit 1
    fi

    # 统一格式：去掉可能的前缀 v，后续统一加
    VERSION="${VERSION#v}"

    # 设置 tarball 名称
    TARBALL_NAME="deepagent-${VERSION}"
}

# ============================================================================
# Step 2: 校验版本号格式
# ============================================================================

validate_version() {
    log_info "校验版本号格式: v${VERSION}"

    # 版本号必须匹配 semver 格式: X.Y.Z 或 X.Y.Z-pre.id
    # 允许: 0.9.0, 0.9.0-alpha.1, 0.9.0-beta.2, 0.9.0-rc.3
    if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'; then
        log_error "版本号格式无效: v${VERSION}"
        log_info "版本号必须是 semver 格式: X.Y.Z 或 X.Y.Z-pre.id"
        log_info "合法示例: 0.9.0  0.9.0-alpha.1  0.9.0-beta.2  0.9.0-rc.3"
        exit 1
    fi

    log_success "版本号格式通过: v${VERSION}"
}

# ============================================================================
# Step 3: 检查预构建 WebUI
# ============================================================================

check_webui() {
    local webui_index="${PROJECT_ROOT}/webui/dist/client/index.html"

    log_info "检查预构建 WebUI..."

    if [ -f "$webui_index" ]; then
        log_success "WebUI 预构建产物存在: ${webui_index}"
    else
        log_error "WebUI 未预构建！缺少文件: ${webui_index}"
        echo ""
        log_info "请先构建 WebUI:"
        log_info "  cd webui && npm install && npm run build"
        echo ""
        log_info "或使用 pre-release 跳过此检查:"
        log_info "  SKIP_WEBUI_CHECK=1 ./scripts/build-release.sh"
        if [ -z "${SKIP_WEBUI_CHECK:-}" ]; then
            exit 1
        fi
        log_warn "SKIP_WEBUI_CHECK 已设置，跳过 WebUI 检查（仅用于预发布测试）"
    fi
}

# ============================================================================
# Step 4: 检查内置 OpenCode 二进制
# ============================================================================

check_opencode() {
    log_info "检查内置 OpenCode 二进制..."

    local found=false

    # 扫描 embedded/opencode/ 下所有平台目录中的 opencode 可执行文件
    while IFS= read -r -d '' binary; do
        # 取相对路径（用于显示）
        local rel_path="${binary#${PROJECT_ROOT}/}"
        if [ -x "$binary" ]; then
            log_success "  OpenCode: ${rel_path}"
            found=true
        else
            log_warn "  OpenCode 不可执行: ${rel_path}"
        fi
    done < <(find "${PROJECT_ROOT}/embedded/opencode" -type f -name "opencode" -print0 2>/dev/null || true)

    # 也检查 embedded/opencode/ 下有无 opencode 命名但无 x 权限的文件
    # （可能在非本机架构上，比如 macOS 上扫描 linux-amd64 二进制）
    while IFS= read -r -d '' binary; do
        local rel_path="${binary#${PROJECT_ROOT}/}"
        if [ ! -x "$binary" ]; then
            log_info "  OpenCode（不可执行，需 chmod）: ${rel_path}"
        fi
    done < <(find "${PROJECT_ROOT}/embedded/opencode" -type f -name "opencode" -print0 2>/dev/null || true)

    if [ "$found" = false ]; then
        if [ -d "${PROJECT_ROOT}/embedded/opencode" ]; then
            # embedded/opencode/ 目录存在但无 opencode 文件
            log_error "embedded/opencode/ 目录中未找到 opencode 可执行文件"
        else
            log_error "embedded/opencode/ 目录不存在"
        fi
        echo ""
        log_info "请先运行 setup-embedded-opencode.sh 下载 OpenCode 二进制:"
        log_info "  ./scripts/setup-embedded-opencode.sh"
        echo ""
        log_info "或使用 pre-release 跳过此检查:"
        log_info "  SKIP_OPENCODE_CHECK=1 ./scripts/build-release.sh"
        if [ -z "${SKIP_OPENCODE_CHECK:-}" ]; then
            exit 1
        fi
        log_warn "SKIP_OPENCODE_CHECK 已设置，跳过 OpenCode 检查（仅用于预发布测试）"
    fi
}

# ============================================================================
# Step 5: 构建 Skills bundled manifest
# ============================================================================

build_skills_manifest() {
    local skills_dir="${PROJECT_ROOT}/skills"
    local manifest_py="${PROJECT_ROOT}/tools/skills_sync.py"
    local manifest_build_py="${PROJECT_ROOT}/scripts/build_skills_index.py"

    log_info "构建 Skills bundled manifest..."

    if [ ! -d "$skills_dir" ]; then
        log_warn "skills/ 目录不存在，跳过 manifest 构建"
        return 0
    fi

    # 策略 A: 使用 tools/skills_sync.py 的 build-manifest 模式
    # skills_sync.py 会根据 manifest 文件追踪每个 skill 的 hash
    if [ -f "$manifest_py" ]; then
        # skills_sync.py 在 repo 根目录下运行，需要 hermes_constants 可导入
        # 先尝试通过 PYTHONPATH 导入
        if PYTHONPATH="${PROJECT_ROOT}" python3 -c "from hermes_constants import get_hermes_home; print('OK')" 2>/dev/null; then
            # 无需额外参数，skills_sync.py 会自动扫描 skills/ 并写入 manifest
            # 但这里我们更多是验证 skills 目录的完整性
            log_info "  skills_sync.py 可用，已验证依赖完整性"
        else
            log_warn "  skills_sync.py 依赖不完整（需在项目 venv 中运行），跳过"
        fi
    fi

    # 策略 B: 使用 scripts/build_skills_index.py 构建索引（如果存在）
    if [ -f "$manifest_build_py" ]; then
        log_info "  使用 build_skills_index.py 构建技能索引..."
        if PYTHONPATH="${PROJECT_ROOT}" python3 "$manifest_build_py" 2>/dev/null; then
            log_success "  技能索引构建完成"
        else
            log_warn "  build_skills_index.py 运行失败（非致命，继续）"
        fi
    fi

    # 验证 skills 目录至少包含一些 skill 目录
    local skill_count=0
    for d in "$skills_dir"/*/; do
        if [ -d "$d" ]; then
            skill_count=$((skill_count + 1))
        fi
    done

    if [ "$skill_count" -gt 0 ]; then
        log_success "  Skills 目录包含 ${skill_count} 个技能，准备打包"
    else
        log_warn "  skills/ 目录为空，tarball 中将不包含技能"
    fi
}

# ============================================================================
# Step 6: 创建 dist/releases/ 目录
# ============================================================================

create_dist_dir() {
    log_info "创建输出目录: ${DIST_DIR}"

    mkdir -p "$DIST_DIR"

    if [ -d "$DIST_DIR" ]; then
        log_success "输出目录已就绪: ${DIST_DIR}"
    else
        log_error "无法创建输出目录: ${DIST_DIR}"
        exit 1
    fi
}

# ============================================================================
# Step 7-8: 打包多个 Release tarball
# ============================================================================
#
# 不再打包单个臃肿的 tar.gz，而是按安装顺序拆分为多个包：
#
#   1. deepagent-core-{VERSION}.tar.gz
#      源码 + CLI + tools + gateway + skills（约 5 MB）
#      不含 webui/dist/ 和 embedded/
#
#   2. deepagent-embedded-{VERSION}.tar.gz
#      所有平台的 OpenCode 二进制（约 254 MB raw）
#      安装脚本按架构只下载对应文件
#
#   3. deepagent-webui-server-{VERSION}.tar.gz
#      Web 服务端 + 前端（约 60 MB，不含 Electron）
#      `deepagent webui install` 时下载
#
#   4. Electron DMG（由 electron-builder 产出，独立分发）
#      webui/dist/electron-output/Deep.*.{arch}.dmg
# ============================================================================

# 共用排除规则
TAR_EXCLUDES=(
    '--exclude=__pycache__'
    '--exclude=.git'
    '--exclude=.venv'
    '--exclude=venv'
    '--exclude=node_modules'
    '--exclude=dist/releases'
    '--exclude=*.pyc'
    '--exclude=*.pyo'
    '--exclude=.DS_Store'
    '--exclude=.coverage'
    '--exclude=htmlcov'
    '--exclude=.pytest_cache'
    '--exclude=*.egg-info'
)

build_core_tarball() {
    local tarball_name="${TARBALL_NAME}"
    local tarball_path="${DIST_DIR}/${tarball_name}.tar.gz"

    log_info "构建 Core tarball..."
    log_info "  路径: ${tarball_path}"

    cd "$PROJECT_ROOT"

    tar czf "$tarball_path" \
        "${TAR_EXCLUDES[@]}" \
        --exclude='embedded' \
        --exclude='webui' \
        \
        pyproject.toml \
        uv.lock \
        requirements.txt \
        constraints-termux.txt \
        cli.py \
        model_tools.py \
        run_agent.py \
        hermes_state.py \
        hermes_constants.py \
        hermes_logging.py \
        hermes_time.py \
        utils.py \
        toolsets.py \
        agent/ \
        hermes_cli/ \
        tools/ \
        gateway/ \
        cron/ \
        acp_adapter/ \
        plugins/ \
        skills/ \
        VERSION

    if [ -f "$tarball_path" ]; then
        local tarball_size
        tarball_size=$(du -h "$tarball_path" | cut -f1)
        log_success "Core tarball 已创建: ${tarball_path} (${tarball_size})"
    else
        log_error "Core tarball 创建失败！"
        exit 1
    fi
}

build_embedded_tarball() {
    local tarball_name="${TARBALL_NAME/deepagent-/deepagent-embedded-}"
    local tarball_path="${DIST_DIR}/${tarball_name}.tar.gz"

    log_info "构建 Embedded tarball..."
    log_info "  路径: ${tarball_path}"

    cd "$PROJECT_ROOT"

    tar czf "$tarball_path" \
        "${TAR_EXCLUDES[@]}" \
        embedded/

    if [ -f "$tarball_path" ]; then
        local tarball_size
        tarball_size=$(du -h "$tarball_path" | cut -f1)
        log_success "Embedded tarball 已创建: ${tarball_path} (${tarball_size})"
    else
        log_error "Embedded tarball 创建失败！"
        exit 1
    fi
}

build_webui_server_tarball() {
    local tarball_name="${TARBALL_NAME/deepagent-/deepagent-webui-server-}"
    local tarball_path="${DIST_DIR}/${tarball_name}.tar.gz"

    log_info "构建 WebUI Server tarball（不含 Electron）..."
    log_info "  路径: ${tarball_path}"

    cd "$PROJECT_ROOT"

    tar czf "$tarball_path" \
        "${TAR_EXCLUDES[@]}" \
        webui/dist/client/ \
        webui/dist/server/ \
        webui/dist/data/ \
        webui/bin/ \
        webui/package.json

    if [ -f "$tarball_path" ]; then
        local tarball_size
        tarball_size=$(du -h "$tarball_path" | cut -f1)
        log_success "WebUI Server tarball 已创建: ${tarball_path} (${tarball_size})"
    else
        log_error "WebUI Server tarball 创建失败！"
        exit 1
    fi
}

# 汇总所有 tarball 路径
collect_tarballs() {
    TARBALL_CORE="${DIST_DIR}/${TARBALL_NAME}.tar.gz"
    TARBALL_EMBEDDED="${DIST_DIR}/deepagent-embedded-${VERSION}.tar.gz"
    TARBALL_WEBUI_SERVER="${DIST_DIR}/deepagent-webui-server-${VERSION}.tar.gz"
}

# ============================================================================
# Step 9: 生成 SHA256 校验和（每个 tarball 独立）
# ============================================================================

detect_sha_cmd() {
    if command -v sha256sum &>/dev/null; then
        SHACMD="sha256sum"
        SHACMD_CHECK="-c"
    elif command -v shasum &>/dev/null; then
        SHACMD="shasum -a 256"
        SHACMD_CHECK="-c"
    elif command -v openssl &>/dev/null; then
        SHACMD="openssl dgst -sha256"
        SHACMD_CHECK=""
    else
        log_error "无可用 SHA256 计算工具"
        exit 1
    fi
}

generate_one_checksum() {
    local file="$1"
    local sha_file="${file}.sha256"
    local basename_file
    basename_file=$(basename "$file")

    cd "$DIST_DIR"
    if [ "$SHACMD" = "sha256sum" ]; then
        sha256sum "$basename_file" > "$sha_file"
    elif [ "$SHACMD" = "shasum -a 256" ]; then
        shasum -a 256 "$basename_file" > "$sha_file"
    else
        local hash
        hash=$(openssl dgst -sha256 "$file" 2>/dev/null | awk '{print $NF}')
        echo "${hash}  ${basename_file}" > "$sha_file"
    fi

    if [ -f "$sha_file" ]; then
        local filesize
        filesize=$(du -h "$file" | cut -f1)
        local filehash
        filehash=$(awk '{print $1}' "$sha_file")
        log_success "  ${basename_file} (${filesize}) → ${filehash}"
    else
        log_error "校验和生成失败: ${sha_file}"
        exit 1
    fi
}

generate_checksums() {
    log_info "生成 SHA256 校验和..."
    detect_sha_cmd
    generate_one_checksum "$TARBALL_CORE"
    generate_one_checksum "$TARBALL_EMBEDDED"
    generate_one_checksum "$TARBALL_WEBUI_SERVER"
    # Electron DMG 校验和（如果存在）
    for dmg in "${DIST_DIR}"/DeepAgent-*.dmg; do
        [ -f "$dmg" ] && generate_one_checksum "$dmg"
    done
}

# ============================================================================
# Step 10: 打印成功信息
# ============================================================================

print_success() {
    local core_size
    local core_sha
    core_size=$(du -h "$TARBALL_CORE" 2>/dev/null | cut -f1)
    core_sha=$(awk '{print $1}' "${TARBALL_CORE}.sha256" 2>/dev/null)

    local emb_size
    local emb_sha
    emb_size=$(du -h "$TARBALL_EMBEDDED" 2>/dev/null | cut -f1)
    emb_sha=$(awk '{print $1}' "${TARBALL_EMBEDDED}.sha256" 2>/dev/null)

    local ws_size
    local ws_sha
    ws_size=$(du -h "$TARBALL_WEBUI_SERVER" 2>/dev/null | cut -f1)
    ws_sha=$(awk '{print $1}' "${TARBALL_WEBUI_SERVER}.sha256" 2>/dev/null)

    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│     ✓ DeepAgent Release 构建完成！                       │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
    echo ""

    echo -e "${CYAN}${BOLD}📦 Release 产物概览 (v${VERSION})${NC}"
    echo ""
    printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "core"          "${core_size}" "${core_sha}"
    printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "embedded"      "${emb_size}" "${emb_sha}"
    printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "webui-server"  "${ws_size}" "${ws_sha}"
    echo ""

    echo -e "${CYAN}${BOLD}🚀 后续操作${NC}"
    echo ""
    echo -e "   1. 上传到 Cloudflare R2:"
    echo -e "      ${GREEN}aws s3 cp ${TARBALL_CORE} s3://deepagent-releases/deepagent-core-${VERSION}.tar.gz${NC}"
    echo -e "      ${GREEN}aws s3 cp ${TARBALL_EMBEDDED} s3://deepagent-releases/deepagent-embedded-${VERSION}.tar.gz${NC}"
    echo -e "      ${GREEN}aws s3 cp ${TARBALL_WEBUI_SERVER} s3://deepagent-releases/deepagent-webui-server-${VERSION}.tar.gz${NC}"
    echo ""
    echo -e "   2. 上传 Electron DMG 到 R2:"
    for dmg in "${DIST_DIR}"/DeepAgent-*.dmg; do
        [ -f "$dmg" ] && echo -e "      ${GREEN}aws s3 cp $dmg s3://deepagent-releases/$(basename "$dmg")${NC}"
    done
    echo ""
    echo -e "   3. (可选) 上传到 GitHub Releases:"
    echo -e "      ${GREEN}gh release create v${VERSION} ${TARBALL_CORE} ${TARBALL_EMBEDDED} ${TARBALL_WEBUI_SERVER} --title \"v${VERSION}\"${NC}"
    echo ""

    echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}输出目录:${NC} ${DIST_DIR}/"
    echo ""
}

# ============================================================================
# 参数解析
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                if [ -z "${2:-}" ]; then
                    log_error "--version 需要参数"
                    exit 1
                fi
                VERSION="$2"
                shift 2
                ;;
            -h|--help)
                echo "DeepAgent Release Tarball Builder"
                echo ""
                echo "用法:"
                echo "  ./scripts/build-release.sh                          # 从 VERSION 文件读取"
                echo "  ./scripts/build-release.sh --version 0.9.0          # 指定版本"
                echo "  ./scripts/build-release.sh --version 0.9.0-beta.1   # pre-release"
                echo ""
                echo "环境变量:"
                echo "  SKIP_WEBUI_CHECK=1     跳过 WebUI 预构建检查（预发布测试用）"
                echo "  SKIP_OPENCODE_CHECK=1   跳过 OpenCode 二进制检查（预发布测试用）"
                echo ""
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                log_info "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    # 必须在项目根目录运行
    if [ ! -f "${PROJECT_ROOT}/pyproject.toml" ]; then
        log_error "请在 DeepAgent 项目根目录运行此脚本"
        log_info "当前目录: $(pwd)"
        log_info "期望项目根: ${PROJECT_ROOT}"
        exit 1
    fi

    # 确保在项目根目录执行
    cd "$PROJECT_ROOT"

    # 先解析命令参数（--version, --help 等）
    parse_args "$@"

    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│     ☤ DeepAgent Release Tarball Builder                  │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│  基于 Hermes 深度改造的数字分身（CEO）产品                │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"

    # ---- Step 1-2: 版本解析与校验 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 1/10] 版本号解析${NC}"
    parse_version

    echo ""
    echo -e "${BLUE}${BOLD}[Step 2/10] 版本号校验${NC}"
    validate_version

    # ---- Step 3: 检查预构建 WebUI ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 3/10] 检查预构建 WebUI${NC}"
    check_webui

    # ---- Step 4: 检查内置 OpenCode 二进制 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 4/10] 检查内置 OpenCode 二进制${NC}"
    check_opencode

    # ---- Step 5: 构建 Skills bundled manifest ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 5/10] 构建 Skills manifest${NC}"
    build_skills_manifest

    # ---- Step 6: 创建输出目录 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 6/10] 创建输出目录${NC}"
    create_dist_dir

    # ---- Step 7-8: 打包 tarball ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 7/10] 打包 Core tarball${NC}"
    build_core_tarball

    echo ""
    echo -e "${BLUE}${BOLD}[Step 8/10] 打包 Embedded tarball${NC}"
    build_embedded_tarball

    echo ""
    echo -e "${BLUE}${BOLD}[Step 9/10] 打包 WebUI Server tarball${NC}"
    build_webui_server_tarball

    # ---- 收集路径 ----
    collect_tarballs

    # ---- Step 10: 生成 SHA256 校验和 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 10/10] 生成 SHA256 校验和${NC}"
    generate_checksums

    # ---- 打印成功信息 ----
    print_success
}

# 执行主流程
main "$@"
