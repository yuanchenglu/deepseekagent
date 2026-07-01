#!/bin/bash
# ============================================================================
# sync-hermes-upstream.sh — 每周 Hermes 上游同步脚本（冲突检测 + 报告生成）
# ============================================================================
# 用法：
#   ./scripts/sync-hermes-upstream.sh            # 标准同步
#   ./scripts/sync-hermes-upstream.sh --dry-run   # 只预览，不修改任何文件
#   ./scripts/sync-hermes-upstream.sh --status    # 查看当前版本信息
#   ./scripts/sync-hermes-upstream.sh --help      # 显示帮助
# ============================================================================

set -euo pipefail

# ---------- 颜色与辅助函数 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()      { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}  $*${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ---------- 路径配置 ----------
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

VERSION_FILE="hermes-upstream-version.txt"
UPSTREAM_REMOTE="hermes-upstream"
UPSTREAM_URL="https://github.com/NousResearch/hermes-agent.git"
SYNC_DIR="docs/sync"
CONFLICT_DIR="${SYNC_DIR}"
HELPER_SCRIPT="scripts/generate-conflict-report.py"

# ---------- 确保 docs/sync/ 目录存在 ----------
mkdir -p "$SYNC_DIR"

# ---------- 帮助 ----------
show_help() {
    cat <<'HELP'
用法: ./scripts/sync-hermes-upstream.sh [选项]

选项:
  --dry-run       只预览上游变更，不执行 merge 或写版本文件
  --status        查看当前跟踪版本与上游状态
  --help          显示此帮助信息

说明:
  每周同步脚本，用于将 NousResearch/hermes-agent 的上游变更同步到
  当前 DeepAgent 仓库。同步策略为「检测 + 报告 + 人工决策」：
    1. 拉取上游最新代码
    2. 检测与本地分支的差异和冲突
    3. 生成结构化的冲突报告
    4. 由 CEO 决定如何合并（不自动 merge）
HELP
    exit 0
}

# ---------- 读取版本文件 ----------
read_version_info() {
    if [[ ! -f "$VERSION_FILE" ]]; then
        error "版本文件 $VERSION_FILE 不存在！"
        error "请先创建该文件，内容格式为："
        echo "  HERMES_UPSTREAM_COMMIT=<commit-hash>"
        echo "  HERMES_UPSTREAM_VERSION=<version-tag>"
        echo "  LAST_SYNC_DATE=<date>"
        echo "  LAST_SYNC_STATUS=<status>"
        exit 1
    fi

    # shellcheck source=/dev/null
    source "$VERSION_FILE"

    COMMIT="${HERMES_UPSTREAM_COMMIT:-unknown}"
    VERSION="${HERMES_UPSTREAM_VERSION:-unknown}"
    SYNC_DATE="${LAST_SYNC_DATE:-unknown}"
    SYNC_STATUS="${LAST_SYNC_STATUS:-unknown}"
}

# ---------- 显示版本状态 ----------
show_status() {
    section "📋 DeepAgent — Hermes 上游版本状态"

    read_version_info

    echo -e "  当前跟踪 Commit:   ${CYAN}${COMMIT}${NC}"
    echo -e "  上游版本标签:      ${CYAN}${VERSION}${NC}"
    echo -e "  上次同步日期:      ${YELLOW}${SYNC_DATE}${NC}"
    echo -e "  同步状态:          ${YELLOW}${SYNC_STATUS}${NC}"
    echo ""

    # 检查 git 仓库状态
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "当前目录不是 Git 仓库！"
        exit 1
    fi

    # 本地 HEAD
    LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo -e "  本地 HEAD:          ${CYAN}${LOCAL_HEAD:0:12}${NC}"

    # 检查上游 remote 是否存在
    if git remote get-url "$UPSTREAM_REMOTE" > /dev/null 2>&1; then
        echo -e "  上游 Remote:        ${GREEN}已配置${NC}"
        echo -e "  上游 URL:           ${CYAN}$(git remote get-url "$UPSTREAM_REMOTE")${NC}"

        # 尝试获取上游最新 commit
        if git fetch "$UPSTREAM_REMOTE" --quiet 2>/dev/null; then
            UPSTREAM_HEAD=$(git rev-parse "${UPSTREAM_REMOTE}/main" 2>/dev/null || git rev-parse "${UPSTREAM_REMOTE}/master" 2>/dev/null || echo "unknown")
            if [[ "$UPSTREAM_HEAD" != "unknown" ]]; then
                echo -e "  上游最新 Commit:    ${CYAN}${UPSTREAM_HEAD:0:12}${NC}"

                if [[ "$COMMIT" != "unknown" ]]; then
                    if [[ "${COMMIT:0:12}" == "${UPSTREAM_HEAD:0:12}" ]]; then
                        ok "当前版本与上游一致 ✅"
                    else
                        warn "当前版本落后于上游 ⚠️"
                        echo ""
                        echo -e "  落后 commit 数:     ${YELLOW}$(git rev-list --count "${COMMIT}..${UPSTREAM_HEAD}" 2>/dev/null || echo "N/A")${NC}"
                    fi
                fi
            fi
        else
            warn "无法获取上游信息（网络问题？）"
        fi
    else
        warn "上游 Remote ($UPSTREAM_REMOTE) 未配置"
        echo -e "  可执行以下命令添加："
        echo -e "    git remote add ${UPSTREAM_REMOTE} ${UPSTREAM_URL}"
    fi
    echo ""
}

# ---------- 设置上游 remote ----------
setup_remote() {
    if ! git remote get-url "$UPSTREAM_REMOTE" > /dev/null 2>&1; then
        info "添加上游 remote: $UPSTREAM_REMOTE → $UPSTREAM_URL"
        git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
    else
        local current_url
        current_url=$(git remote get-url "$UPSTREAM_REMOTE")
        if [[ "$current_url" != "$UPSTREAM_URL" ]]; then
            warn "上游 remote URL 不匹配，更新中..."
            git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
        fi
    fi
}

# ---------- 检测冲突并生成报告 ----------
generate_conflict_report() {
    local tracked_commit="$1"
    local upstream_branch="$2"
    local date_suffix
    date_suffix=$(date +%Y%m%d)
    local report_file="${CONFLICT_DIR}/conflict-${date_suffix}.md"
    local changed_files
    local has_conflicts=false

    section "🔍 冲突检测中..."

    # 生成变更摘要
    info "上游变更摘要（${tracked_commit:0:12}..${upstream_branch}）："
    local commit_log
    commit_log=$(git log "${tracked_commit}..${upstream_branch}" --oneline 2>/dev/null || true)

    if [[ -z "$commit_log" ]]; then
        info "没有新的上游变更。"
        return 0
    fi

    echo "$commit_log"

    # 检测变更的文件列表
    changed_files=$(git diff --name-only "${tracked_commit}".."${upstream_branch}" 2>/dev/null || true)

    # 尝试模拟 merge 检测冲突（不实际修改工作区）
    local merge_output
    merge_output=$(git merge --no-commit --no-ff "$upstream_branch" 2>&1 || true)

    # 检查冲突
    local conflict_files
    if echo "$merge_output" | grep -qi "conflict\|CONFLICT"; then
        has_conflicts=true
        conflict_files=$(echo "$merge_output" | grep -i "CONFLICT" | sed 's/.*in //' | sed 's///' | sort -u || true)

        # 如果 grep 没抓到文件，尝试从 merge 输出提取
        if [[ -z "$conflict_files" ]]; then
            conflict_files=$(echo "$merge_output" | grep -i "conflict" | awk '{print $NF}' | sort -u || true)
        fi
    fi

    # 放弃 merge（恢复工作区）
    git merge --abort 2>/dev/null || git reset --merge 2>/dev/null || true

    # ---------- 写入报告文件 ----------
    cat > "$report_file" << REPORT_HEADER
# 上游同步冲突报告 — ${date_suffix}

**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**跟踪 Commit**: \`${tracked_commit}\`
**上游分支**: \`${upstream_branch}\`

---

REPORT_HEADER

    if [[ "$has_conflicts" == true ]]; then
        # 冲突报告
        {
            echo "## ⚠️ 检测到冲突"
            echo ""
            echo "冲突文件列表："
            echo ""
            echo "| 文件 | 冲突行数 | 优先级 | 建议操作 |"
            echo "|------|---------|--------|---------|"

            # 构建冲突文件清单
            for f in $conflict_files; do
                # 判断优先级
                local priority="中"
                local suggestion="需要人工合并"
                if echo "$f" | grep -qiE "\.(md|txt|rst)$"; then
                    priority="低"
                    suggestion="可手工合并文档内容"
                elif echo "$f" | grep -qiE "\.(py|ts|js|tsx|jsx)$" && echo "$f" | grep -qiE "(core|main|harness|config|cli)"; then
                    priority="高"
                    suggestion="需 CEO 决策：保留 DeepAgent 修改或接受上游"
                elif echo "$f" | grep -qiE "\.(py|ts|js)$"; then
                    priority="中"
                    suggestion="逐行手动合并"
                fi

                # 统计冲突行数（如果有冲突标记）
                local conflict_count=0
                if [[ -f "$f" ]]; then
                    conflict_count=$(grep -c "^<<<<<<< " "$f" 2>/dev/null || echo "0")
                fi
                if [[ "$conflict_count" -eq 0 ]]; then
                    conflict_count="合并后查看"
                fi

                echo "| \`$f\` | ${conflict_count} | ${priority} | ${suggestion} |"
            done

            echo ""
            echo "---"
            echo ""
            echo "## 👑 CEO 决策指引"
            echo ""
            echo "请根据以下选项决定每个冲突文件的处理方式："
            echo ""
            echo "| 选项 | 操作 | 适用场景 |"
            echo "|------|------|---------|"
            echo "| **接受上游** | 使用 \`git checkout --theirs <file>\` | 上游修复了 bug / 新增了功能，本地无实质修改 |"
            echo "| **保留本地** | 使用 \`git checkout --ours <file>\` | DeepAgent 特有功能，上游不相关 |"
            echo "| **手动合并** | 手动编辑冲突标记 | 双方都有有价值的修改 |"
            echo "| **跳过此版本** | 放弃本次同步 | 上游变更与 DeepAgent 方向不一致 |"
            echo ""
            echo "### 决策步骤"
            echo ""
            echo "1. 查看上方冲突文件清单和优先级"
            echo "2. 对每个文件做出决策（接受上游 / 保留本地 / 手动合并）"
            echo "3. 执行合并操作"
            echo "4. 更新 \`hermes-upstream-version.txt\` 记录新版本"
            echo ""
        } >> "$report_file"
    else
        # 无冲突报告
        {
            echo "## ✅ 无冲突检测"
            echo ""
            echo "以下上游变更可以安全合并："
            echo ""
            echo '```'
            echo "$commit_log"
            echo '```'
            echo ""
            echo "受影响的文件："
            echo ""
            echo '```'
            echo "$changed_files"
            echo '```'
            echo ""
            echo "### 建议操作"
            echo ""
            echo "1. 确认变更内容不影响 DeepAgent 特有功能"
            echo "2. 执行 \`git merge ${upstream_branch}\` 或 cherry-pick 特定 commit"
            echo "3. 更新 \`hermes-upstream-version.txt\`"
            echo ""
        } >> "$report_file"
    fi

    # 附加变更详细信息
    {
        echo "---"
        echo ""
        echo "## 附录：详细变更列表"
        echo ""
        echo '```'
        echo "$commit_log"
        echo '```'
        echo ""
        echo "## 附录：受影响的文件"
        echo ""
        echo '```'
        echo "$changed_files"
        echo '```'
        echo ""
    } >> "$report_file"

    echo ""
    ok "冲突报告已生成 → ${report_file}"

    # 如果存在 Python 辅助脚本，运行它生成结构化报告
    if [[ -f "$HELPER_SCRIPT" && "$has_conflicts" == true ]]; then
        info "运行冲突报告辅助脚本..."
        python3 "$HELPER_SCRIPT" "$report_file" 2>/dev/null || true
    fi

    # 返回检测结果（便于调用者判断）
    if [[ "$has_conflicts" == true ]]; then
        return 1
    else
        return 0
    fi
}

# ---------- 主流程：实际同步（或 dry-run） ----------
do_sync() {
    local dry_run=${1:-false}

    section "🚀 Hermes 上游同步流程"

    read_version_info

    info "当前跟踪版本: ${VERSION} (${COMMIT})"
    echo ""

    # Step 1: 配置 remote
    setup_remote

    # Step 2: Fetch 上游
    info "正在拉取上游代码..."
    if [[ "$dry_run" == true ]]; then
        info "[DRY-RUN] 将执行: git fetch ${UPSTREAM_REMOTE}"
    fi
    git fetch "$UPSTREAM_REMOTE"
    ok "上游代码拉取完成"

    # Step 3: 确定上游 main/master 分支
    local upstream_branch
    if git rev-parse --verify "${UPSTREAM_REMOTE}/main" > /dev/null 2>&1; then
        upstream_branch="${UPSTREAM_REMOTE}/main"
    elif git rev-parse --verify "${UPSTREAM_REMOTE}/master" > /dev/null 2>&1; then
        upstream_branch="${UPSTREAM_REMOTE}/master"
    else
        error "无法找到上游的主分支（main 或 master）"
        exit 1
    fi

    UPSTREAM_HEAD=$(git rev-parse "$upstream_branch")
    info "上游最新 Commit: ${UPSTREAM_HEAD:0:12}"

    # Step 4: 比较版本
    if [[ "${COMMIT}" == "${UPSTREAM_HEAD}" ]]; then
        section "✅ 当前已是最新版本，无需同步"
        return 0
    fi

    local behind_count
    behind_count=$(git rev-list --count "${COMMIT}..${UPSTREAM_HEAD}" 2>/dev/null || echo "0")
    warn "当前落后上游 ${behind_count} 个 commit"

    # Step 5: 生成变更摘要
    section "📜 上游变更摘要"
    local commit_log
    commit_log=$(git log "${COMMIT}..${upstream_branch}" --oneline 2>/dev/null || true)
    if [[ -n "$commit_log" ]]; then
        echo "$commit_log"
    else
        info "无新变更"
    fi
    echo ""

    if [[ "$dry_run" == true ]]; then
        # Dry-run 模式：只显示变更，不检测冲突
        local changed_files
        changed_files=$(git diff --name-only "${COMMIT}".."${upstream_branch}" 2>/dev/null || true)
        info "[DRY-RUN] 以下文件将受上游变更影响："
        if [[ -n "$changed_files" ]]; then
            echo "$changed_files"
        fi
        section "📋 DRY-RUN 完成 — 未执行任何修改"
        return 0
    fi

    # Step 6: 冲突检测与报告生成
    section "🔎 执行冲突检测..."
    if generate_conflict_report "$COMMIT" "$upstream_branch"; then
        ok "无冲突 — 可安全合并"
        echo ""
        info "建议执行以下命令合并："
        echo "  git merge ${upstream_branch}"
        echo "  然后更新 ${VERSION_FILE}"
    else
        warn "检测到冲突！"
        echo ""
        section "👑 CEO 决策流程"
        echo ""
        echo "请查阅 docs/sync/ 目录下的冲突报告文件。"
        echo "对每个冲突文件，选择以下操作之一："
        echo ""
        echo "  a) 接受上游版本    → git checkout --theirs <file>"
        echo "  b) 保留 DeepAgent  → git checkout --ours <file>"
        echo "  c) 手动合并        → 编辑冲突标记后 git add"
        echo "  d) 跳过本次同步    → 放弃合并"
        echo ""
        echo "决策完成后，执行:"
        echo "  git merge --continue"
        echo "  # 或 git merge --abort（放弃合并）"
        echo ""

        # 列出冲突文件
        local merge_check
        merge_check=$(git merge --no-commit --no-ff "$upstream_branch" 2>&1 || true)
        git merge --abort 2>/dev/null || git reset --merge 2>/dev/null || true

        local conflict_files
        conflict_files=$(echo "$merge_check" | grep -i "CONFLICT" | sed 's/.*in //' | sed 's///' | sort -u || true)
        if [[ -n "$conflict_files" ]]; then
            echo "冲突文件清单："
            for f in $conflict_files; do
                echo "  ▸ $f"
            done
        fi
    fi

    section "✅ 同步检测完成"
}

# ---------- 主入口 ----------
main() {
    local mode="sync"

    # 解析参数
    for arg in "$@"; do
        case "$arg" in
            --help|-h)
                show_help
                ;;
            --status)
                mode="status"
                ;;
            --dry-run)
                mode="dry-run"
                ;;
            *)
                error "未知参数: $arg"
                show_help
                ;;
        esac
    done

    case "$mode" in
        status)
            show_status
            ;;
        dry-run)
            do_sync true
            ;;
        sync)
            do_sync false
            ;;
    esac
}

main "$@"
