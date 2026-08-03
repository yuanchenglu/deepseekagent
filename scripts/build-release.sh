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
# Step 5:  确认发布包不携带未审计 Skills
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
CORE_ONLY=false                                  # 第一阶段仅构建 MIT Core
CHANNEL="alpha"                                  # alpha=CLI, beta=WebUI

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

    local source_version
    source_version="$(tr -d '[:space:]' < "$VERSION_FILE")"
    source_version="${source_version#v}"
    if [ "$source_version" != "$VERSION" ]; then
        log_error "VERSION 文件与发布版本不一致: ${source_version} != ${VERSION}"
        log_info "请先在发布 Commit 中更新 VERSION，不得生成版本不一致的制品"
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

    local binary="${PROJECT_ROOT}/embedded/opencode/macos-arm64/opencode"
    local license="${PROJECT_ROOT}/embedded/opencode/src/LICENSE"
    if [ ! -f "$binary" ] || [ ! -x "$binary" ] || [ ! -f "$license" ]; then
        log_error "缺少可执行的 macOS arm64 OpenCode 或上游许可证"
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
        return 0
    fi
    log_success "  OpenCode: embedded/opencode/macos-arm64/opencode"
    log_success "  License: embedded/opencode/src/LICENSE"
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
#   2. deepagent-deepcode-{VERSION}.tar.gz
#      仅含首发支持的 macOS arm64 OpenCode 二进制及其许可证
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
        README.md \
        LICENSE \
        NOTICE \
        SECURITY.md \
        CONTRIBUTING.md \
        CODE_OF_CONDUCT.md \
        THIRD_PARTY_NOTICES.md \
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
        scripts/audit-python-licenses.py \
        scripts/install-release.sh \
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
    local tarball_name="${TARBALL_NAME/deepagent-/deepagent-deepcode-}"
    local tarball_path="${DIST_DIR}/${tarball_name}.tar.gz"

    cd "$PROJECT_ROOT"

    if [ ! -f "embedded/opencode/macos-arm64/opencode" ] && [ -z "${SKIP_OPENCODE_CHECK:-}" ]; then
        log_error "缺少 OpenCode 二进制，无法构建 DeepCode tarball"
        log_info "请先运行 setup-embedded-opencode.sh 或设置 SKIP_OPENCODE_CHECK=1"
        exit 1
    fi

    if [ ! -f "embedded/opencode/macos-arm64/opencode" ]; then
        log_warn "SKIP_OPENCODE_CHECK: 跳过 DeepCode tarball（无 OpenCode 二进制）"
        return 0
    fi

    log_info "构建 DeepCode macOS arm64 tarball..."
    log_info "  路径: ${tarball_path}"

    tar czf "$tarball_path" \
        "${TAR_EXCLUDES[@]}" \
        embedded/opencode/macos-arm64/opencode \
        embedded/opencode/src/LICENSE

    if [ -f "$tarball_path" ]; then
        local tarball_size
        tarball_size=$(du -h "$tarball_path" | cut -f1)
        log_success "DeepCode tarball 已创建: ${tarball_path} (${tarball_size})"
    else
        log_error "DeepCode tarball 创建失败！"
        exit 1
    fi
}

build_webui_server_tarball() {
    local tarball_name="${TARBALL_NAME/deepagent-/deepagent-webui-server-}"
    local tarball_path="${DIST_DIR}/${tarball_name}.tar.gz"
    local stage_dir node_binary node_root

    log_info "构建 WebUI Server tarball（不含 Electron）..."
    log_info "  路径: ${tarball_path}"

    command -v node >/dev/null 2>&1 || { log_error "WebUI 发布需要 Node.js 23"; exit 1; }
    node -e 'const major=Number(process.versions.node.split(".")[0]);process.exit(major>=23?0:1)' || {
        log_error "WebUI Beta 制品需要 Node.js 23 或更高版本"
        exit 1
    }
    node_binary="$(node -p 'require("node:fs").realpathSync(process.execPath)')"
    file "$node_binary" | grep -q 'Mach-O.*arm64' || {
        log_error "WebUI Beta 仅允许内置 macOS arm64 Node.js"
        exit 1
    }
    if otool -L "$node_binary" | tail -n +2 | grep -Ev '^[[:space:]]*(/usr/lib/|/System/Library/)' | grep -q .; then
        log_error "Node.js 不是可独立分发的官方构建（检测到外部动态库）"
        log_info "请使用 actions/setup-node 或 nodejs.org 的 macOS arm64 官方发行包"
        exit 1
    fi
    node_root="$(cd "$(dirname "$node_binary")/.." && pwd -P)"
    [ -f "$node_root/LICENSE" ] || { log_error "Node.js LICENSE 缺失: $node_root/LICENSE"; exit 1; }

    stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/deepagent-webui-release.XXXXXX")"
    mkdir -p "$stage_dir/webui/dist" "$stage_dir/webui/runtime/node/bin"
    cp -R "$PROJECT_ROOT/webui/dist/client" "$stage_dir/webui/dist/client"
    cp -R "$PROJECT_ROOT/webui/dist/server" "$stage_dir/webui/dist/server"
    [ -d "$PROJECT_ROOT/webui/dist/data" ] && cp -R "$PROJECT_ROOT/webui/dist/data" "$stage_dir/webui/dist/data" || true
    cp -R "$PROJECT_ROOT/webui/bin" "$stage_dir/webui/bin"
    cp -R "$PROJECT_ROOT/webui/third_party_licenses" "$stage_dir/webui/third_party_licenses"
    cp "$PROJECT_ROOT/webui/package.json" "$PROJECT_ROOT/webui/package-lock.json" "$stage_dir/webui/"
    cp "$node_binary" "$stage_dir/webui/runtime/node/bin/node"
    cp "$node_root/LICENSE" "$stage_dir/webui/runtime/node/LICENSE"
    chmod 0755 "$stage_dir/webui/runtime/node/bin/node"

    log_info "从已校验 lockfile 安装树复制 WebUI 生产依赖..."
    node "$PROJECT_ROOT/webui/scripts/copy-production-deps.mjs" \
        --source "$PROJECT_ROOT/webui" \
        --destination "$stage_dir/webui"
    [ -f "$stage_dir/webui/node_modules/socket.io/package.json" ] || {
        log_error "WebUI 生产依赖缺少 socket.io"
        exit 1
    }
    [ -f "$stage_dir/webui/node_modules/node-pty/package.json" ] || {
        log_error "WebUI 生产依赖缺少 node-pty"
        exit 1
    }
    (cd "$stage_dir/webui" && "$stage_dir/webui/runtime/node/bin/node" -e \
        "require('socket.io'); require('node-pty')") || {
        log_error "WebUI 生产依赖无法由内置 Node.js 加载"
        exit 1
    }
    node "$PROJECT_ROOT/webui/scripts/audit-npm-licenses.mjs" \
        --root "$stage_dir/webui" \
        --output "$DIST_DIR/deepagent-webui-npm-licenses-${VERSION}.json"
    cp "$DIST_DIR/deepagent-webui-npm-licenses-${VERSION}.json" \
        "$stage_dir/webui/THIRD_PARTY_NOTICES.json"

    tar czf "$tarball_path" -C "$stage_dir" webui
    rm -rf "$stage_dir"

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
    TARBALL_EMBEDDED="${DIST_DIR}/deepagent-deepcode-${VERSION}.tar.gz"
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
    if [ "$CORE_ONLY" != true ]; then
        [ -f "$TARBALL_EMBEDDED" ] && generate_one_checksum "$TARBALL_EMBEDDED"
        [ -f "$TARBALL_WEBUI_SERVER" ] && generate_one_checksum "$TARBALL_WEBUI_SERVER"
    fi
    # Electron DMG 校验和（如果存在）
    for dmg in "${DIST_DIR}"/DeepAgent-*.dmg; do
        [ -f "$dmg" ] && generate_one_checksum "$dmg"
    done
    return 0
}

# ============================================================================
# Step 10: 打印成功信息
# ============================================================================

print_success() {
    local core_size
    local core_sha
    core_size=$(du -h "$TARBALL_CORE" 2>/dev/null | cut -f1)
    core_sha=$(awk '{print $1}' "${TARBALL_CORE}.sha256" 2>/dev/null)

    if [ "$CORE_ONLY" = true ]; then
        echo ""
        echo -e "${GREEN}${BOLD}✓ DeepAgent CLI Alpha Core 构建完成${NC}"
        printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "core" "${core_size}" "${core_sha}"
        echo "  manifest: ${DIST_DIR}/deepagent-manifest-${VERSION}.json"
        echo "  channel:  ${DIST_DIR}/deepagent-channel-${CHANNEL}.json"
        return 0
    fi

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
    printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "deepcode"      "${emb_size}" "${emb_sha}"
    printf "  ${YELLOW}%-40s${NC} ${GREEN}%8s${NC}  ${CYAN}%s${NC}\n" "webui-server"  "${ws_size}" "${ws_sha}"
    echo ""

    echo -e "${CYAN}${BOLD}🚀 后续操作${NC}"
    echo ""
    echo -e "   1. 上传到 Cloudflare R2:"
    echo -e "      ${GREEN}aws s3 cp ${TARBALL_CORE} s3://deepagent-releases/deepagent-core-${VERSION}.tar.gz${NC}"
    echo -e "      ${GREEN}aws s3 cp ${TARBALL_EMBEDDED} s3://deepagent-releases/deepagent-deepcode-${VERSION}.tar.gz${NC}"
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
            --core-only)
                CORE_ONLY=true
                shift
                ;;
            --channel)
                case "${2:-}" in
                    alpha|beta) CHANNEL="$2" ;;
                    *) log_error "--channel 只支持 alpha 或 beta"; exit 1 ;;
                esac
                shift 2
                ;;
            -h|--help)
                echo "DeepAgent Release Tarball Builder"
                echo ""
                echo "用法:"
                echo "  ./scripts/build-release.sh                          # 从 VERSION 文件读取"
                echo "  ./scripts/build-release.sh --version 0.9.0          # 指定版本"
                echo "  ./scripts/build-release.sh --version 0.9.0-beta.1   # pre-release"
                echo "  ./scripts/build-release.sh --core-only              # CLI Alpha Core only"
                echo "  ./scripts/build-release.sh --channel beta           # WebUI Beta artifacts"
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

    if [ "$CORE_ONLY" != true ]; then
        # ---- Step 3: 检查预构建 WebUI ----
        echo ""
        echo -e "${BLUE}${BOLD}[Step 3/10] 检查预构建 WebUI${NC}"
        check_webui

        # ---- Step 4: 检查内置 OpenCode 二进制 ----
        echo ""
        echo -e "${BLUE}${BOLD}[Step 4/10] 检查内置 OpenCode 二进制${NC}"
        check_opencode
    else
        log_info "Core-only 模式：不检查或打包 BSL WebUI/Desktop 与 OpenCode"
    fi

    # ---- Step 5: Skills 许可边界 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 5/10] 检查 Skills 发布边界${NC}"
    log_info "当前 Alpha/Beta 制品不打包未完成许可审计的 bundled Skills"

    # ---- Step 6: 创建输出目录 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 6/10] 创建输出目录${NC}"
    create_dist_dir

    # ---- Step 7-8: 打包 tarball ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 7/10] 打包 Core tarball${NC}"
    build_core_tarball

    if [ "$CORE_ONLY" != true ]; then
        echo ""
        echo -e "${BLUE}${BOLD}[Step 8/10] 打包 Embedded tarball${NC}"
        build_embedded_tarball

        echo ""
        echo -e "${BLUE}${BOLD}[Step 9/10] 打包 WebUI Server tarball${NC}"
        build_webui_server_tarball
    fi

    # ---- 收集路径 ----
    collect_tarballs

    # ---- Step 10: 生成 SHA256 校验和 ----
    echo ""
    echo -e "${BLUE}${BOLD}[Step 10/10] 生成 SHA256 校验和${NC}"
    generate_checksums

    local manifest_args=(
        --version "$VERSION"
        --channel "$CHANNEL"
        --artifact "$TARBALL_CORE"
        --output-dir "$DIST_DIR"
    )
    if [ "$CORE_ONLY" != true ]; then
        manifest_args+=(--webui-artifact "$TARBALL_WEBUI_SERVER")
        manifest_args+=(--deepcode-artifact "$TARBALL_EMBEDDED")
    fi
    python3 "${PROJECT_ROOT}/scripts/generate-release-manifest.py" "${manifest_args[@]}"

    # ---- 打印成功信息 ----
    print_success
}

# 执行主流程
main "$@"
