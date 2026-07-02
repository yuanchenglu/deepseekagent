#!/bin/bash
# ============================================================================
# Cloudflare R2 + Pages Function Setup
# ============================================================================
# Phase 6.1-6.2 of release-installation-plan
#
# This script:
#   1. Sources Cloudflare credentials from ~/.deepagent/.env
#   2. Attempts to create the R2 bucket via Cloudflare API
#   3. Prints manual instructions if the API token lacks permissions
#   4. Verifies Pages Function files exist
#
# Prerequisites:
#   - CF_ACCOUNT_ID and CF_API_TOKEN in ~/.deepagent/.env
#   - curl, jq for API calls
#
# Configuration:
#   CF_ACCOUNT_ID=d0a9c688290c80b51d6d4605ba32160a
#   R2 Bucket: deepagent-releases
#   Pages Project: deepagent-landing (or deepagent-docs)
#   Domain: deepseekagent.starseas.org
# ============================================================================

set -euo pipefail

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

log_info()    { echo -e "${CYAN}→${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }
log_step()    { echo ""; echo -e "${BLUE}${BOLD}[Step $1]${NC} $2"; }

# ---- Paths ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${HOME}/.deepagent/.env"
FUNCTIONS_DIR="${PROJECT_ROOT}/website/functions"
WRANGLER_TOML="${PROJECT_ROOT}/website/wrangler.toml"

# ---- Configuration (edit these as needed) ----
CF_ACCOUNT_ID="d0a9c688290c80b51d6d4605ba32160a"
R2_BUCKET_NAME="deepagent-releases"
R2_BUCKET_LOCATION="WEUR"  # Western Europe — closest to most users
PAGES_PROJECT="deepagent-landing"
DOMAIN="deepseekagent.starseas.org"

# ============================================================================
print_banner() {
    echo ""
    echo -e "${BLUE}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│       ☤ Cloudflare R2 + Pages Setup                      │"
    echo "│       Phase 6.1-6.2 — Release Infrastructure             │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│   R2 Bucket:  ${R2_BUCKET_NAME}                          │"
    echo "│   Pages:      ${PAGES_PROJECT}.${DOMAIN}                 │"
    echo "│   Install:    https://${DOMAIN}/install.sh               │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

# ============================================================================
# Step 1: Source credentials
# ============================================================================
load_credentials() {
    log_step "1/5" "加载 Cloudflare 凭证"

    # First check environment variables, then fall back to .env file
    if [ -n "${CF_API_TOKEN:-}" ]; then
        log_success "CF_API_TOKEN 已从环境变量加载"
    elif [ -f "$ENV_FILE" ]; then
        log_info "从 ${ENV_FILE} 加载凭证..."
        # shellcheck disable=SC1090
        source "$ENV_FILE"
        if [ -n "${CF_API_TOKEN:-}" ]; then
            log_success "CF_API_TOKEN 已从 ${ENV_FILE} 加载"
        else
            log_warn "${ENV_FILE} 中未设置 CF_API_TOKEN"
        fi
    else
        log_warn "${ENV_FILE} 不存在，请先创建或设置环境变量"
    fi

    if [ -z "${CF_API_TOKEN:-}" ]; then
        log_error "CF_API_TOKEN 未设置！"
        echo ""
        echo "请先在 ~/.deepagent/.env 中添加："
        echo "  CF_ACCOUNT_ID=${CF_ACCOUNT_ID}"
        echo "  CF_API_TOKEN=your_api_token_here"
        echo ""
        echo "Token 需要以下权限："
        echo "  - R2: Read + Write"
        echo "  - Pages: Read + Write"
        echo "  或直接用 API Token 模板 'Edit Cloudflare Workers'"
        echo ""
        return 1
    fi

    # Also try to load CF_ACCOUNT_ID from env (may differ from default)
    if [ -n "${CF_ACCOUNT_ID_ENV:-}" ]; then
        CF_ACCOUNT_ID="$CF_ACCOUNT_ID_ENV"
        log_info "使用环境变量中的 CF_ACCOUNT_ID: ${CF_ACCOUNT_ID}"
    else
        log_info "使用默认 CF_ACCOUNT_ID: ${CF_ACCOUNT_ID}"
    fi

    return 0
}

# ============================================================================
# Step 2: Verify token scope (test API access)
# ============================================================================
verify_token() {
    log_step "2/5" "验证 API Token 权限"

    if [ -z "${CF_API_TOKEN:-}" ]; then
        log_warn "跳过 — 无 API Token"
        return 1
    fi

    # Simple test: try listing R2 buckets (requires R2:Read)
    log_info "测试 API 连通性（列出 R2 buckets）..."
    local response
    response=$(curl -fsSL \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets" 2>/dev/null || echo "")

    if [ -z "$response" ]; then
        log_warn "API 调用失败 — Token 可能缺少 R2 权限"
        log_info "尝试查询账户详情确认 Token 有效..."
        local user_resp
        user_resp=$(curl -fsSL \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            "https://api.cloudflare.com/client/v4/user/tokens/verify" 2>/dev/null || echo "")

        if echo "$user_resp" | grep -q '"success":true'; then
            log_warn "Token 有效，但缺少 R2 权限"
        else
            log_error "Token 无效或已过期"
        fi
        return 1
    fi

    # Check if the response indicates success
    if echo "$response" | grep -q '"success":true'; then
        log_success "API Token 有效且具有 R2 读取权限"
        return 0
    else
        log_warn "API 返回异常: $(echo "$response" | head -c 200)"
        return 1
    fi
}

# ============================================================================
# Step 3: Create R2 bucket
# ============================================================================
create_r2_bucket() {
    log_step "3/5" "创建 R2 Bucket"

    if [ -z "${CF_API_TOKEN:-}" ]; then
        log_warn "跳过 — 无 API Token"
        return 1
    fi

    # First check if it already exists
    log_info "检查 bucket '${R2_BUCKET_NAME}' 是否已存在..."
    local check_resp
    check_resp=$(curl -fsSL \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets?name=${R2_BUCKET_NAME}" 2>/dev/null || echo "")

    if echo "$check_resp" | grep -q '"success":true'; then
        local bucket_count
        bucket_count=$(echo "$check_resp" | grep -o '"name":"'"${R2_BUCKET_NAME}"'"' | wc -l)
        if [ "$bucket_count" -ge 1 ]; then
            log_success "Bucket '${R2_BUCKET_NAME}' 已存在，跳过创建"
            return 0
        fi
    fi

    # Create the bucket
    log_info "正在创建 R2 bucket '${R2_BUCKET_NAME}'（位置: ${R2_BUCKET_LOCATION}）..."
    local create_resp
    create_resp=$(curl -fsSL -X POST \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${R2_BUCKET_NAME}\",\"location\":\"${R2_BUCKET_LOCATION}\"}" \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets" 2>/dev/null || echo "")

    if echo "$create_resp" | grep -q '"success":true'; then
        log_success "R2 bucket '${R2_BUCKET_NAME}' 创建成功！"
        return 0
    else
        local err_msg
        err_msg=$(echo "$create_resp" | grep -o '"message":"[^"]*"' | head -1 || echo "未知错误")
        log_error "创建 bucket 失败: ${err_msg}"
        log_warn "Token 可能缺少 R2:Write 权限"
        return 1
    fi
}

# ============================================================================
# Step 4: Verify Pages Function files
# ============================================================================
verify_pages_functions() {
    log_step "4/5" "验证 Pages Function 文件"

    local all_ok=true

    # Check install.sh.js
    if [ -f "${FUNCTIONS_DIR}/install.sh.js" ]; then
        log_success "install.sh.js 已存在"
    else
        log_error "install.sh.js 缺失！请运行: cp website/functions/install.sh.js.example website/functions/install.sh.js"
        all_ok=false
    fi

    # Check _routes.json
    if [ -f "${FUNCTIONS_DIR}/_routes.json" ]; then
        log_success "_routes.json 已存在"
        log_info "  路由: /install.sh → install.sh.js"
    else
        log_warn "_routes.json 缺失，Pages Function 将使用默认路由规则"
        all_ok=false
    fi

    # Verify wrangler.toml has the right name
    if [ -f "$WRANGLER_TOML" ]; then
        local current_name
        current_name=$(grep '^name' "$WRANGLER_TOML" | sed 's/name = "\(.*\)"/\1/' || echo "")
        if [ "$current_name" != "$PAGES_PROJECT" ] && [ "$current_name" != "deepagent-docs" ]; then
            log_warn "wrangler.toml 中 Pages 项目名为 '${current_name}'，预期 '${PAGES_PROJECT}' 或 'deepagent-docs'"
            log_info "如需修改: sed -i '' 's/name = \"${current_name}\"/name = \"${PAGES_PROJECT}\"/' ${WRANGLER_TOML}"
        else
            log_success "wrangler.toml 项目名: ${current_name}"
        fi
    else
        log_warn "wrangler.toml 不存在，Pages 部署可能需要手动配置"
    fi

    if [ "$all_ok" = true ]; then
        log_success "所有 Pages Function 文件就绪"
    fi
}

# ============================================================================
# Step 5: Print manual instructions
# ============================================================================
print_manual_instructions() {
    log_step "5/5" "后续手动配置步骤"

    echo ""
    echo -e "${YELLOW}${BOLD}如果在自动步骤中遇到权限错误，请按以下步骤手动完成配置：${NC}"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 1. 创建 R2 Bucket${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   a. 登录 Cloudflare Dashboard: https://dash.cloudflare.com/"
    echo "   b. 选择账户 → R2 → 创建 bucket"
    echo "   c. Bucket 名称: ${R2_BUCKET_NAME}"
    echo "   d. 位置: 自动（或选 Western Europe）"
    echo "   e. 创建后 → 设置 → 公开访问 → 允许"
    echo "   f. 记下 Public URL（类似: https://pub-xxxx.r2.dev）"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 2. 配置 API Token${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   a. https://dash.cloudflare.com/profile/api-tokens"
    echo "   b. 创建令牌 → 'Edit Cloudflare Workers' 模板"
    echo "      或自定义模板，权限:"
    echo "       - Account → R2: Read + Write"
    echo "       - Account → Pages: Read + Write"
    echo "       - Zone → Zone: Read"
    echo "   c. 将 Token 添加到 ~/.deepagent/.env:"
    echo "      CF_API_TOKEN=your_new_token"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 3. 创建 Pages 项目（如果尚未创建）${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   a. Cloudflare Dashboard → Workers & Pages → 创建"
    echo "   b. 选择 'Pages' → '连接到 Git'"
    echo "   c. 选择 GitHub 仓库: yuanchenglu/deepseekagent"
    echo "   d. 项目名称: ${PAGES_PROJECT}"
    echo "   e. 生产分支: main"
    echo "   f. 构建命令: npm run build（在 website/ 目录）"
    echo "   g. 构建输出目录: build"
    echo "   h. 环境变量(高级):"
    echo "       - R2_PUBLIC_URL: https://${R2_BUCKET_NAME}.${CF_ACCOUNT_ID}.r2.dev"
    echo "   i. 部署后 → 自定义域 → 添加 ${DOMAIN}"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 4. Pages Function 自动部署${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   以下文件已创建在仓库中，部署 Pages 后自动生效:"
    echo "     - website/functions/install.sh.js  → 处理 /install.sh"
    echo "     - website/functions/_routes.json    → 路由规则"
    echo ""
    echo "   验证 Pages Function 是否生效:"
    echo "     curl -sI https://${DOMAIN}/install.sh | grep Location"
    echo "   预期输出: Location: https://${R2_BUCKET_NAME}.${CF_ACCOUNT_ID}.r2.dev/deepagent-latest.tar.gz"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 5. 上传 Release 包${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   构建后上传到 R2（参考 scripts/build-release.sh）:"
    echo "     # 通过 wrangler CLI:"
    echo "     npx wrangler r2 object put ${R2_BUCKET_NAME}/deepagent-latest.tar.gz --file=dist/deepagent-latest.tar.gz"
    echo ""
    echo "     # 或通过 AWS S3 兼容 API:"
    echo "     # 在 R2 → Bucket → 设置 → S3 API 中获取凭证"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo -e "${BOLD}▶ 6. DNS 验证${NC}"
    echo "───────────────────────────────────────────────────────────"
    echo "   Zone ID: 7ba2a1f358993350f15fadfdabdb2fdf"
    echo "   确保 ${DOMAIN} 的 DNS 记录指向 Cloudflare:"
    echo "     - CNAME @  → ${PAGES_PROJECT}.pages.dev"
    echo "     - CNAME releases.${DOMAIN} → ${R2_BUCKET_NAME}.${CF_ACCOUNT_ID}.r2.dev"
    echo "     （或直接在 R2 bucket 设置中添加自定义域）"
    echo ""
}

# ============================================================================
# Main
# ============================================================================
main() {
    print_banner

    local has_creds=false
    local has_r2_perms=false

    # Step 1
    if load_credentials; then
        has_creds=true
    fi

    # Step 2
    if verify_token; then
        has_r2_perms=true
    fi

    # Step 3
    if [ "$has_r2_perms" = true ]; then
        create_r2_bucket || true
    else
        log_step "3/5" "创建 R2 Bucket"
        log_warn "跳过自动创建（需有效 API Token）"
    fi

    # Step 4 — always runs, no credentials needed
    verify_pages_functions

    # Step 5 — always runs, manual fallback
    print_manual_instructions

    # Summary
    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
    if [ "$has_creds" = true ] && [ "$has_r2_perms" = true ]; then
        echo -e "${GREEN}自动配置完成！${NC}"
    else
        echo -e "${YELLOW}部分步骤需手动完成（见上方说明）${NC}"
    fi
    echo -e "${BOLD}Pages Function 文件:${NC} ${FUNCTIONS_DIR}/"
    echo -e "${BOLD}部署 Pages 后测试:${NC}"
    echo "  curl -sI https://${DOMAIN}/install.sh | grep Location"
    echo ""
}

main "$@"
