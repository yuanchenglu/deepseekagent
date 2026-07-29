#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  CF_ACCOUNT_ID=... \
  NEW_CF_R2_ACCESS_KEY_ID=... \
  NEW_CF_R2_SECRET_ACCESS_KEY=... \
  OLD_CF_R2_ACCESS_KEY_ID=... \
  OLD_CF_R2_SECRET_ACCESS_KEY=... \
  EVIDENCE_PATH=docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md \
  bash scripts/owner-gate/verify-r2-credential-rotation.sh

Optional environment variables:
  R2_BUCKET       Default: deepagent-releases
  TEST_PREFIX     Default: credential-rotation-test

Safety properties:
  - Never prints credential values.
  - Uses the new credential only for an isolated upload/readback/compare/delete cycle.
  - Uses the old credential only for one read-only list request and requires denial.
  - Does not create a Git tag, GitHub Release, channel manifest, or public post.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

required_commands=(aws python3 cmp mktemp date)
for command_name in "${required_commands[@]}"; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 2
  fi
done

required_variables=(
  CF_ACCOUNT_ID
  NEW_CF_R2_ACCESS_KEY_ID
  NEW_CF_R2_SECRET_ACCESS_KEY
  OLD_CF_R2_ACCESS_KEY_ID
  OLD_CF_R2_SECRET_ACCESS_KEY
  EVIDENCE_PATH
)
for variable_name in "${required_variables[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Missing required environment variable: $variable_name" >&2
    exit 2
  fi
done

R2_BUCKET="${R2_BUCKET:-deepagent-releases}"
TEST_PREFIX="${TEST_PREFIX:-credential-rotation-test}"
ENDPOINT_URL="https://${CF_ACCOUNT_ID}.r2.cloudflarestorage.com"
STARTED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
TEMP_DIR="$(mktemp -d)"
SOURCE_FILE="${TEMP_DIR}/source.bin"
READBACK_FILE="${TEMP_DIR}/readback.bin"
OBJECT_ID="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)"
OBJECT_KEY="${TEST_PREFIX}/${OBJECT_ID}/probe.bin"
UPLOADED=0

redacted_last4() {
  python3 - "$1" <<'PY'
import sys
value = sys.argv[1]
print(value[-4:] if len(value) >= 4 else value)
PY
}

cleanup() {
  set +e
  if [[ "$UPLOADED" -eq 1 ]]; then
    AWS_ACCESS_KEY_ID="$NEW_CF_R2_ACCESS_KEY_ID" \
    AWS_SECRET_ACCESS_KEY="$NEW_CF_R2_SECRET_ACCESS_KEY" \
    AWS_DEFAULT_REGION=auto \
      aws s3 rm "s3://${R2_BUCKET}/${OBJECT_KEY}" \
        --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null 2>&1
  fi
  rm -rf "$TEMP_DIR"
  unset NEW_CF_R2_ACCESS_KEY_ID NEW_CF_R2_SECRET_ACCESS_KEY
  unset OLD_CF_R2_ACCESS_KEY_ID OLD_CF_R2_SECRET_ACCESS_KEY
}
trap cleanup EXIT INT TERM

python3 - "$SOURCE_FILE" <<'PY'
from pathlib import Path
import secrets
import sys
Path(sys.argv[1]).write_bytes(secrets.token_bytes(4096))
PY

run_new_aws() {
  AWS_ACCESS_KEY_ID="$NEW_CF_R2_ACCESS_KEY_ID" \
  AWS_SECRET_ACCESS_KEY="$NEW_CF_R2_SECRET_ACCESS_KEY" \
  AWS_DEFAULT_REGION=auto \
    aws "$@"
}

run_old_aws() {
  AWS_ACCESS_KEY_ID="$OLD_CF_R2_ACCESS_KEY_ID" \
  AWS_SECRET_ACCESS_KEY="$OLD_CF_R2_SECRET_ACCESS_KEY" \
  AWS_DEFAULT_REGION=auto \
    aws "$@"
}

echo "Validating replacement R2 credential with an isolated object cycle..."
run_new_aws s3 cp "$SOURCE_FILE" "s3://${R2_BUCKET}/${OBJECT_KEY}" \
  --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
UPLOADED=1

run_new_aws s3 cp "s3://${R2_BUCKET}/${OBJECT_KEY}" "$READBACK_FILE" \
  --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
cmp "$SOURCE_FILE" "$READBACK_FILE"

run_new_aws s3 rm "s3://${R2_BUCKET}/${OBJECT_KEY}" \
  --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
UPLOADED=0

echo "Confirming the revoked credential is denied by a read-only request..."
set +e
run_old_aws s3api list-objects-v2 \
  --bucket "$R2_BUCKET" \
  --max-items 1 \
  --endpoint-url "$ENDPOINT_URL" \
  --region auto >/dev/null 2>&1
OLD_STATUS=$?
set -e

if [[ "$OLD_STATUS" -eq 0 ]]; then
  echo "Old credential is still accepted. Gate remains NO-GO." >&2
  exit 3
fi

FINISHED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
NEW_LAST4="$(redacted_last4 "$NEW_CF_R2_ACCESS_KEY_ID")"
OLD_LAST4="$(redacted_last4 "$OLD_CF_R2_ACCESS_KEY_ID")"
ACCOUNT_LAST4="$(redacted_last4 "$CF_ACCOUNT_ID")"
mkdir -p "$(dirname "$EVIDENCE_PATH")"
cat >"$EVIDENCE_PATH" <<EOF
# Cloudflare R2 凭据轮换自动验证证据

> 执行开始（UTC）：\`${STARTED_AT}\`  
> 执行完成（UTC）：\`${FINISHED_AT}\`  
> Provider：Cloudflare R2  
> Bucket：\`${R2_BUCKET}\`  
> Account ID 脱敏标识：\`last4:${ACCOUNT_LAST4}\`  
> 新 Access Key 脱敏标识：\`last4:${NEW_LAST4}\`  
> 旧 Access Key 脱敏标识：\`last4:${OLD_LAST4}\`  
> Secret 值：**未记录**

## 自动验证结果

| 检查项 | 结果 |
|---|---|
| 新凭据隔离对象上传 | PASS |
| 新凭据读回 | PASS |
| 字节级比较 | PASS |
| 隔离对象删除 | PASS |
| 旧凭据安全只读请求 | DENIED（退出码 \`${OLD_STATUS}\`） |
| Tag / Release / Channel 变更 | 未执行 |

## 人工复核仍需完成

- [ ] 新 Token 的平台权限范围仅覆盖所需 Bucket / 对象操作；
- [ ] Repository / Organization / Environment / Dependabot / Codespaces Secrets 已盘点；
- [ ] 其他 Provider 凭据已按同一规则轮换并验证；
- [ ] 本地 shell history、CI 日志和密码管理器共享项不存在旧值；
- [ ] 执行人与复核人已签字；
- [ ] 本文件及相关 PR、Issue、Actions 日志不含任何 Secret 值。

## Gate 判定

本脚本只关闭 Cloudflare R2 的自动技术验证部分。只有全部人工复核和其他 Provider 均完成后，Issue #21 才能标记为 PASSED。
EOF

if grep -Fq "$NEW_CF_R2_SECRET_ACCESS_KEY" "$EVIDENCE_PATH" || \
   grep -Fq "$OLD_CF_R2_SECRET_ACCESS_KEY" "$EVIDENCE_PATH" || \
   grep -Fq "$NEW_CF_R2_ACCESS_KEY_ID" "$EVIDENCE_PATH" || \
   grep -Fq "$OLD_CF_R2_ACCESS_KEY_ID" "$EVIDENCE_PATH"; then
  echo "Safety check failed: evidence contains an unredacted credential." >&2
  rm -f "$EVIDENCE_PATH"
  exit 4
fi

echo "R2 credential verification passed. Redacted evidence: $EVIDENCE_PATH"
