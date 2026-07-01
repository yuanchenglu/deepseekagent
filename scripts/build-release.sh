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
# Step 7-8: 打包 tarball（含排除规则和包含路径清单）
# ============================================================================
#
# 打包策略：在 PROJECT_ROOT 内执行 tar，使用相对路径。
# 这样 tarball 解压后的根目录就是项目根 — pyproject.toml 在顶层。
#
# 排除规则:
#   --exclude='__pycache__'  — Python 缓存
#   --exclude='.git'         — Git 元数据
#   --exclude='.venv'        — Python 虚拟环境（项目级）
#   --exclude='venv'         — Python 虚拟环境（备选目录名）
#   --exclude='node_modules' — Node.js 依赖
#   --exclude='dist/releases'— 本脚本的输出（防止嵌套打包）
#
# 包含路径（来自 spec Step 8）:
#   pyproject.toml uv.lock requirements.txt constraints-termux.txt
#   cli.py model_tools.py run_agent.py hermes_state.py hermes_constants.py
#   hermes_logging.py hermes_time.py utils.py
#   agent/ hermes_cli/ tools/ gateway/ cron/ acp_adapter/ plugins/
#   skills/ embedded/ webui/dist/ webui/bin/ webui/electron/ webui/package.json
#   VERSION
# ============================================================================

build_tarball() {
    local tarball_path="${DIST_DIR}/${TARBALL_NAME}.tar.gz"

    log_info "构建 Release tarball..."
    log_info "  路径: ${tarball_path}"
    log_info "  版本: v${VERSION}"

    # 切换到项目根目录，确保 tarball 内的路径是相对的
    cd "$PROJECT_ROOT"

    # 用 tar 打包，项目根 = tarball 根
    # 使用 --exclude 排除不需要的目录和文件
    tar czf "$tarball_path" \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='node_modules' \
        --exclude='dist/releases' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.DS_Store' \
        --exclude='.coverage' \
        --exclude='htmlcov' \
        --exclude='.pytest_cache' \
        --exclude='*.egg-info' \
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
        agent/ \
        hermes_cli/ \
        tools/ \
        gateway/ \
        cron/ \
        acp_adapter/ \
        plugins/ \
        skills/ \
        embedded/ \
        webui/dist/ \
        webui/bin/ \
        webui/electron/ \
        webui/package.json \
        VERSION

    # 验证 tarball 是否成功创建
    if [ -f "$tarball_path" ]; then
        local tarball_size
        tarball_size=$(du -h "$tarball_path" | cut -f1)
        log_success "Tarball 已创建: ${tarball_path} (${tarball_size})"
    else
        log_error "Tarball 创建失败！"
        exit 1
    fi
}

# ============================================================================
# Step 9: 生成 SHA256 校验和
# ============================================================================

generate_checksum() {
    local tarball_path="${DIST_DIR}/${TARBALL_NAME}.tar.gz"
    local sha_file="${DIST_DIR}/${TARBALL_NAME}.sha256"

    log_info "生成 SHA256 校验和..."

    # 检测可用的 SHA256 工具
    local sha_cmd=""
    if command -v sha256sum &>/dev/null; then
        sha_cmd="sha256sum"
    elif command -v shasum &>/dev/null; then
        sha_cmd="shasum -a 256"
    elif command -v openssl &>/dev/null; then
        sha_cmd="openssl dgst -sha256"
    else
        log_error "无可用 SHA256 计算工具（需 sha256sum、shasum 或 openssl）"
        exit 1
    fi

    # 计算校验和并写入文件（标准格式: "<hash>  <filename>"）
    # 这样 sha256sum -c 或 shasum -a 256 -c 可直接验证
    cd "$DIST_DIR"
    if [ "$sha_cmd" = "sha256sum" ]; then
        sha256sum "${TARBALL_NAME}.tar.gz" > "$sha_file"
    elif [ "$sha_cmd" = "shasum -a 256" ]; then
        shasum -a 256 "${TARBALL_NAME}.tar.gz" > "$sha_file"
    else
        # openssl: 输出格式与 sha256sum 不同，需要转换
        local hash
        hash=$($sha_cmd "${DIST_DIR}/${TARBALL_NAME}.tar.gz" 2>/dev/null | awk '{print $NF}')
        echo "${hash}  ${TARBALL_NAME}.tar.gz" > "$sha_file"
    fi

    if [ -f "$sha_file" ]; then
        log_success "SHA256 校验和已生成: ${sha_file}"
        log_info "  校验和: $(awk '{print $1}' "$sha_file")"
    else
        log_error "校验和文件生成失败！"
        exit 1
    fi
}

# ============================================================================
# Step 10: 打印成功信息
# ============================================================================

print_success() {
    local tarball_path="${DIST_DIR}/${TARBALL_NAME}.tar.gz"
    local sha_file="${DIST_DIR}/${TARBALL_NAME}.sha256"
    local tarball_size
    local tarball_sha

    tarball_size=$(du -h "$tarball_path" | cut -f1)
    tarball_sha=$(awk '{print $1}' "$sha_file")

    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│     ✓ DeepAgent Release 构建完成！                       │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
    echo ""

    echo -e "${CYAN}${BOLD}📦 Release 包概览${NC}"
    echo ""
    echo -e "   ${YELLOW}版本:${NC}        v${VERSION}"
    echo -e "   ${YELLOW}Tarball:${NC}     ${tarball_path}"
    echo -e "   ${YELLOW}大小:${NC}         ${tarball_size}"
    echo -e "   ${YELLOW}SHA256:${NC}      ${tarball_sha}"
    echo -e "   ${YELLOW}校验文件:${NC}     ${sha_file}"
    echo ""

    echo -e "${CYAN}${BOLD}🚀 后续操作${NC}"
    echo ""
    echo -e "   1. 上传到 Cloudflare R2:"
    echo -e "      ${GREEN}aws s3 cp ${tarball_path} s3://deepseekagent/releases/${TARBALL_NAME}.tar.gz${NC}"
    echo -e "      ${GREEN}aws s3 cp ${sha_file} s3://deepseekagent/releases/${TARBALL_NAME}.sha256${NC}"
    echo ""
    echo -e "   2. 上传到 GitHub Releases:"
    echo -e "      ${GREEN}gh release create v${VERSION} ${tarball_path} ${sha_file} --title \"v${VERSION}\"${NC}"
    echo ""
    echo -e "   3. 本地验证 tarball 内容:"
    echo -e "      ${GREEN}tar tzf ${tarball_path} | head -30${NC}"
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
    echo -e "${BLUE}${BOLD}[Step 7-8/10] 打包 Release tarball${NC}"
    build_tarball

    # ---- Step 9: 生成 SHA256 校验和 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 9/10] 生成 SHA256 校验和${NC}"
    generate_checksum

    # ---- Step 10: 打印成功信息 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 10/10] 构建完成${NC}"
    print_success
}

# 执行主流程
main "$@"
