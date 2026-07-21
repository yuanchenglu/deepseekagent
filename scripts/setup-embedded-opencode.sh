#!/bin/bash
set -e

echo "=== DeepAgent 嵌入式 OpenCode 安装 ==="

EMBEDDED_DIR="$(cd "$(dirname "$0")/.." && pwd)/embedded"
ARM64_DIR="$EMBEDDED_DIR/opencode/macos-arm64"
X64_DIR="$EMBEDDED_DIR/opencode/macos-x64"
CONFIG_DIR="$EMBEDDED_DIR/config"
WORKSPACE_DIR="$EMBEDDED_DIR/workspace"

# ==========================================================
# 步骤 1：检测已有二进制
# ==========================================================
ARM64_BIN="$ARM64_DIR/opencode"
X64_BIN="$X64_DIR/opencode"

ARM64_OK=false
X64_OK=false

if [ -f "$ARM64_BIN" ] && [ -x "$ARM64_BIN" ]; then
    ARM64_VER=$("$ARM64_BIN" --version 2>/dev/null || echo "unknown")
    echo "[OK] arm64 二进制已存在: $ARM64_BIN (版本 $ARM64_VER)"
    ARM64_OK=true
fi

if [ -f "$X64_BIN" ] && [ -x "$X64_BIN" ]; then
    X64_VER=$("$X64_BIN" --version 2>/dev/null || echo "unknown")
    echo "[OK] x86_64 二进制已存在: $X64_BIN (版本 $X64_VER)"
    X64_OK=true
fi

if ! $ARM64_OK || ! $X64_OK; then
    echo ""
    echo "下载 OpenCode 二进制..."

    mkdir -p "$ARM64_DIR" "$X64_DIR"

    # 获取最新版本号
    echo "获取最新版本信息..."
    LATEST=$(curl -sL "https://api.github.com/repos/anomalyco/opencode/releases/latest" | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])" 2>/dev/null || echo "v1.17.13")
    echo "最新版本: $LATEST"

    download_binary() {
        local target_arch="$1"
        local dest_dir="$2"
        local zip_name="opencode-darwin-${target_arch}.zip"
        local url="https://github.com/anomalyco/opencode/releases/download/${LATEST}/${zip_name}"
        local tmp_zip="/tmp/${zip_name}"

        echo "下载 ${zip_name}..."
        curl -L "$url" -o "$tmp_zip"
        echo "解压..."
        unzip -o "$tmp_zip" -d "$dest_dir/"
        chmod +x "$dest_dir/opencode"
        local ver=$("$dest_dir/opencode" --version 2>/dev/null || echo "unknown")
        echo "已安装: $dest_dir/opencode (版本 $ver)"
        rm -f "$tmp_zip"
    }

    download_binary "arm64" "$ARM64_DIR"
    download_binary "x64" "$X64_DIR"
fi

# ==========================================================
# 步骤 2：确保配置文件就绪
# ==========================================================
echo ""
echo "确保配置就绪..."
mkdir -p "$CONFIG_DIR" "$WORKSPACE_DIR"

# 基础 YAML 配置
if [ ! -f "$CONFIG_DIR/opencode-config.yaml" ]; then
    cat > "$CONFIG_DIR/opencode-config.yaml" << 'EOF'
# DeepAgent 嵌入式研发小组配置
# 与用户本地 OpenCode 完全隔离

model: deepseek-v4-flash
workspace: ../workspace
skills_dir: ../skills
isolation: true
EOF
    echo "  [OK] opencode-config.yaml"
fi

# opencode.json — 注册 oh-my-openagent 插件
if [ ! -f "$CONFIG_DIR/opencode.json" ]; then
    cat > "$CONFIG_DIR/opencode.json" << 'EOF'
{
  "plugin": ["oh-my-openagent"]
}
EOF
    echo "  [OK] opencode.json（注册 oh-my-openagent 插件）"
fi

# oh-my-openagent.jsonc — 插件配置（DeepSeek 模型）
if [ ! -f "$CONFIG_DIR/oh-my-openagent.jsonc" ]; then
    cat > "$CONFIG_DIR/oh-my-openagent.jsonc" << 'OPNEOF'
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  "agents": {
    "sisyphus":          { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max", "temperature": 0.3 },
    "explore":           { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max", "temperature": 0.3 },
    "librarian":         { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max" },
    "multimodal-looker": { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max" },
    "atlas":             { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max", "temperature": 0.3 },
    "sisyphus-junior":   { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max", "temperature": 0.3 },
    "hephaestus":        { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max", "temperature": 0.2 },
    "oracle":            { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max", "temperature": 0.2 },
    "prometheus":        { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max", "temperature": 0.3 },
    "metis":             { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max", "temperature": 0.2 },
    "momus":             { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max", "temperature": 0.2 }
  },

  "categories": {
    "visual-engineering": { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max" },
    "quick":             { "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "max" },
    "deep":              { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max" },
    "ultrabrain":        { "model": "deepseek/deepseek-v4-pro",   "reasoningEffort": "max" }
  },

  "telemetry": false
}
OPNEOF
    echo "  [OK] oh-my-openagent.jsonc（11 Agent × DeepSeek V4 Flash/Pro 配置）"
fi

# ==========================================================
# 步骤 3：安装 oh-my-openagent npm 依赖
# ==========================================================
echo ""
echo "安装 oh-my-openagent 插件依赖..."

# 检查 package.json 是否存在
if [ ! -f "$CONFIG_DIR/package.json" ]; then
    cat > "$CONFIG_DIR/package.json" << 'EOF'
{
  "dependencies": {
    "@opencode-ai/plugin": "1.17.13",
    "oh-my-openagent": "^4.19.0"
  }
}
EOF
fi

# 检测包管理器
NPM_CMD=""
if command -v npm &>/dev/null; then
    NPM_CMD="npm"
elif command -v bun &>/dev/null; then
    NPM_CMD="bun"
fi

if [ -n "$NPM_CMD" ]; then
    echo "使用 $NPM_CMD 安装 oh-my-openagent..."
    cd "$CONFIG_DIR" && $NPM_CMD install --omit=dev --no-audit --no-fund 2>&1 | tail -5
    echo "  [OK] oh-my-openagent 插件已安装"
else
    echo "  [WARN] 未检测到 npm 或 bun，跳过自动安装。"
    echo "  如需使用 oh-my-openagent 插件，请手动执行:"
    echo "    cd $CONFIG_DIR && npm install"
fi

# ==========================================================
# 完成
# ==========================================================
echo ""
echo "=== 安装完成 ==="
echo "  arm64  二进制: $ARM64_DIR/opencode"
echo "  x86_64 二进制: $X64_DIR/opencode"
echo "  配置目录:      $CONFIG_DIR"
echo "  oh-my-openagent: 已预装并配置 DeepSeek V4 Flash/Pro"
echo ""
echo "启动方式: embedded/start.sh"
