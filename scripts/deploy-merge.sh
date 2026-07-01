#!/bin/bash
# scripts/deploy-merge.sh — 合并 landing page 和 Docusaurus 文档站，统一部署到 Cloudflare Pages
# 用法: ./scripts/deploy-merge.sh [--deploy]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/dist/website"
LANDING_SRC="$PROJECT_ROOT/landingpage"
DOCS_SRC="$PROJECT_ROOT/website"

echo "=== 构建合并部署 ==="

# Step 1: Create clean build dir
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Step 2: Copy landing page
echo "→ 复制 landing page..."
cp -r "$LANDING_SRC"/* "$BUILD_DIR/"

# Step 3: Build Docusaurus (if package.json exists)
if [ -f "$DOCS_SRC/package.json" ]; then
    echo "→ 构建 Docusaurus 文档站..."
    cd "$DOCS_SRC"
    npm ci --ignore-scripts 2>/dev/null || true
    npm run build 2>/dev/null || echo "  ⚠ Docusaurus build failed (skip)"
    cd "$PROJECT_ROOT"

    # Copy docs build output
    if [ -d "$DOCS_SRC/build" ]; then
        echo "→ 合并文档站..."
        mkdir -p "$BUILD_DIR/docs"
        cp -r "$DOCS_SRC/build/"* "$BUILD_DIR/docs/"
    fi

    if [ -d "$DOCS_SRC/.docusaurus" ]; then
        echo "→ 复制 .docusaurus 配置..."
        cp -r "$DOCS_SRC/.docusaurus" "$BUILD_DIR/"
    fi
else
    echo "  ⚠ Docusaurus not found at $DOCS_SRC (skip)"
fi

# Step 4: Create _redirects for install.sh
echo "→ 创建 _redirects..."
cat > "$BUILD_DIR/_redirects" << 'REDIRECTS'
# DeepAgent install.sh download redirect
/install.sh  https://deepseekagent.starseas.org/releases/deepagent-latest.tar.gz  302
/releases/*  https://deepseekagent.starseas.org/releases/:splat  302
REDIRECTS

# Step 5: Create _headers
cat > "$BUILD_DIR/_headers" << 'HEADERS'
# Security headers
/*.html
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY

/assets/*
  Cache-Control: public, max-age=31536000, immutable
HEADERS

# Step 6: Show result
echo ""
echo "✅ 构建完成: $BUILD_DIR"
echo "   大小: $(du -sh "$BUILD_DIR" | cut -f1)"
echo "   文件数: $(find "$BUILD_DIR" -type f | wc -l)"
echo ""

# Optional deploy
if [ "${1:-}" = "--deploy" ]; then
    echo "→ 部署到 Cloudflare Pages..."
    if command -v wrangler &>/dev/null; then
        npx wrangler pages deploy "$BUILD_DIR" --project-name deepagent-landing
    elif command -v npx &>/dev/null; then
        npx wrangler pages deploy "$BUILD_DIR" --project-name deepagent-landing
    else
        echo "  ✗ wrangler CLI not found. Install with: npm install -g wrangler"
        exit 1
    fi
    echo "✅ 部署完成"
fi
