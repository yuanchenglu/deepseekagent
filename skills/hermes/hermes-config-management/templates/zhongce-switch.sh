#!/bin/bash
# 方舟众测 - Hermes 模型切换脚本模板
# 用法: ./zhongce-switch.sh [canvas|eclipse|falcon|granite|helix|restore|status]
#
# 自定义前: 搜索 TODO 并替换为你的实际值
#   - TEST_API_KEY: 你的众测唯一识别码
#   - TEST_BASE_URL: API 网关地址
set -e

CONFIG="$HOME/.hermes/config.yaml"
ENV="$HOME/.hermes/.env"
BACKUP_CONFIG="$HOME/.hermes/config.yaml.bak-zhongce"
BACKUP_ENV="$HOME/.hermes/.env.bak-zhongce"

# ===== 自定义配置（替换为你的值）=====
TEST_BASE_URL="https://sd7k0j05hv504o9evirf0.apigateway-cn-beijing.volceapi.com"
TEST_API_KEY="<your-unique-id>"   # TODO: 替换为你的识别码
# =====================================

usage() {
  echo "用法: $(basename $0) [canvas|eclipse|falcon|granite|helix|restore|status]"
  exit 1
}

case "$1" in
  canvas|eclipse|falcon|granite|helix)
    echo "=== 切换到众测模式: anonymous/$1 ==="
    [ ! -f "$BACKUP_CONFIG" ] && cp "$CONFIG" "$BACKUP_CONFIG" && cp "$ENV" "$BACKUP_ENV" && echo "→ 已备份原配置"

    python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['model'] = {
    'default': 'anonymous/$1',
    'provider': 'custom',
    'base_url': '$TEST_BASE_URL',
    'api_key': '$TEST_API_KEY',
    'max_tokens': 128000,
    'timeoutSeconds': 900
}
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"
    # 更新 .env 中的 OPENAI_API_KEY
    if grep -q '^OPENAI_API_KEY=' "$ENV"; then
      sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$TEST_API_KEY|" "$ENV"
    else
      echo "OPENAI_API_KEY=$TEST_API_KEY" >> "$ENV"
    fi

    rm -rf "$HOME/.hermes/sessions/"* "$HOME/.hermes/skills/"* 2>/dev/null
    echo "→ 已清理会话和技能缓存"
    grep -A5 '^model:' "$CONFIG" | head -6
    echo "=== 重启 Hermes 后生效 ==="
    ;;

  restore)
    if [ ! -f "$BACKUP_CONFIG" ]; then
      echo "✗ 没有找到备份"; exit 1
    fi
    echo "=== 恢复正常配置 ==="
    cp "$BACKUP_CONFIG" "$CONFIG"
    cp "$BACKUP_ENV" "$ENV"
    rm -rf "$HOME/.hermes/sessions/"* 2>/dev/null
    echo "→ 已恢复"
    echo "=== 重启 Hermes 后生效 ==="
    ;;

  status)
    echo "当前模型: $(grep '^  default:' "$CONFIG" | head -1 | sed 's/^  default: //')"
    echo "备份存在: $([ -f "$BACKUP_CONFIG" ] && echo '是' || echo '否')"
    ;;

  *) usage ;;
esac
