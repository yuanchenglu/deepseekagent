#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  # SEC-004: validate the replacement credential before revoking the old one.
  CF_ACCOUNT_ID=... \
  NEW_CF_R2_ACCESS_KEY_ID=... \
  NEW_CF_R2_SECRET_ACCESS_KEY=... \
  EVIDENCE_PATH=docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md \
  bash scripts/owner-gate/verify-r2-credential-rotation.sh --new-only

  # SEC-006: after SEC-005 revokes the old credential, prove denial.
  CF_ACCOUNT_ID=... \
  OLD_CF_R2_ACCESS_KEY_ID=... \
  OLD_CF_R2_SECRET_ACCESS_KEY=... \
  EVIDENCE_PATH=docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md \
  bash scripts/owner-gate/verify-r2-credential-rotation.sh --old-denial-only

  # Convenience mode after the old credential has already been revoked.
  CF_ACCOUNT_ID=... \
  NEW_CF_R2_ACCESS_KEY_ID=... \
  NEW_CF_R2_SECRET_ACCESS_KEY=... \
  OLD_CF_R2_ACCESS_KEY_ID=... \
  OLD_CF_R2_SECRET_ACCESS_KEY=... \
  EVIDENCE_PATH=docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md \
  bash scripts/owner-gate/verify-r2-credential-rotation.sh --full

Modes:
  --new-only         Default. Isolated upload/readback/compare/delete with the new credential.
  --old-denial-only  Read-only request with the revoked old credential; success is a hard failure.
  --full             Run --new-only and then --old-denial-only. Use only after revocation.

Optional environment variables:
  R2_BUCKET       Default: deepagent-releases
  TEST_PREFIX     Default: credential-rotation-test

Safety properties:
  - Never prints credential values.
  - Never passes credential values as command-line arguments.
  - Uses the new credential only for an isolated upload/readback/compare/delete cycle.
  - Uses the old credential only for one read-only list request and requires denial.
  - Does not create a Git tag, GitHub Release, channel manifest, or public post.
EOF
}

MODE="${1:---new-only}"
case "$MODE" in
  --help|-h)
    usage
    exit 0
    ;;
  --new-only|--old-denial-only|--full)
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage >&2
    exit 2
    ;;
esac

required_commands=(aws python3 cmp mktemp date)
for command_name in "${required_commands[@]}"; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 2
  fi
done

require_variable() {
  local variable_name="$1"
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Missing required environment variable: $variable_name" >&2
    exit 2
  fi
}

require_variable CF_ACCOUNT_ID
require_variable EVIDENCE_PATH
if [[ "$MODE" == "--new-only" || "$MODE" == "--full" ]]; then
  require_variable NEW_CF_R2_ACCESS_KEY_ID
  require_variable NEW_CF_R2_SECRET_ACCESS_KEY
fi
if [[ "$MODE" == "--old-denial-only" || "$MODE" == "--full" ]]; then
  require_variable OLD_CF_R2_ACCESS_KEY_ID
  require_variable OLD_CF_R2_SECRET_ACCESS_KEY
fi

R2_BUCKET="${R2_BUCKET:-deepagent-releases}"
TEST_PREFIX="${TEST_PREFIX:-credential-rotation-test}"
ENDPOINT_URL="https://${CF_ACCOUNT_ID}.r2.cloudflarestorage.com"
TEMP_DIR=""
OBJECT_KEY=""
UPLOADED=0

redacted_last4() {
  printf '%s' "$1" | python3 -c 'import sys; value=sys.stdin.read(); print(value[-4:] if len(value) >= 4 else value)'
}

cleanup() {
  set +e
  if [[ "$UPLOADED" -eq 1 && -n "${NEW_CF_R2_ACCESS_KEY_ID:-}" && -n "${NEW_CF_R2_SECRET_ACCESS_KEY:-}" ]]; then
    AWS_ACCESS_KEY_ID="$NEW_CF_R2_ACCESS_KEY_ID" \
    AWS_SECRET_ACCESS_KEY="$NEW_CF_R2_SECRET_ACCESS_KEY" \
    AWS_DEFAULT_REGION=auto \
      aws s3 rm "s3://${R2_BUCKET}/${OBJECT_KEY}" \
        --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null 2>&1
  fi
  if [[ -n "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
  unset NEW_CF_R2_ACCESS_KEY_ID NEW_CF_R2_SECRET_ACCESS_KEY || true
  unset OLD_CF_R2_ACCESS_KEY_ID OLD_CF_R2_SECRET_ACCESS_KEY || true
}
trap cleanup EXIT INT TERM

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

assert_evidence_does_not_contain() {
  local value="$1"
  if [[ -n "$value" ]] && grep -Fq "$value" "$EVIDENCE_PATH"; then
    echo "Safety check failed: evidence contains an unredacted credential value." >&2
    rm -f "$EVIDENCE_PATH"
    exit 4
  fi
}

validate_new_credential() {
  local started_at finished_at new_last4 account_last4 source_file readback_file object_id
  started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  TEMP_DIR="$(mktemp -d)"
  source_file="${TEMP_DIR}/source.bin"
  readback_file="${TEMP_DIR}/readback.bin"
  object_id="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
  OBJECT_KEY="${TEST_PREFIX}/${object_id}/probe.bin"

  python3 - "$source_file" <<'PY'
from pathlib import Path
import secrets
import sys
Path(sys.argv[1]).write_bytes(secrets.token_bytes(4096))
PY

  echo "Validating replacement R2 credential with an isolated object cycle..."
  run_new_aws s3 cp "$source_file" "s3://${R2_BUCKET}/${OBJECT_KEY}" \
    --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
  UPLOADED=1

  run_new_aws s3 cp "s3://${R2_BUCKET}/${OBJECT_KEY}" "$readback_file" \
    --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
  cmp "$source_file" "$readback_file"

  run_new_aws s3 rm "s3://${R2_BUCKET}/${OBJECT_KEY}" \
    --endpoint-url "$ENDPOINT_URL" --region auto >/dev/null
  UPLOADED=0

  finished_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  new_last4="$(redacted_last4 "$NEW_CF_R2_ACCESS_KEY_ID")"
  account_last4="$(redacted_last4 "$CF_ACCOUNT_ID")"
  mkdir -p "$(dirname "$EVIDENCE_PATH")"
  cat >"$EVIDENCE_PATH" <<EOF
# Cloudflare R2 凭据轮换分阶段自动验证证据

> Provider：Cloudflare R2  
> Bucket：\`${R2_BUCKET}\`  
> Account ID 脱敏标识：\`last4:${account_last4}\`  
> Secret 值：**未记录**

## SEC-004：新凭据最小读写闭环

> 执行开始（UTC）：\`${started_at}\`  
> 执行完成（UTC）：\`${finished_at}\`  
> 新 Access Key 脱敏标识：\`last4:${new_last4}\`

| 检查项 | 结果 |
|---|---|
| 新凭据隔离对象上传 | PASS |
| 新凭据读回 | PASS |
| 字节级比较 | PASS |
| 隔离对象删除 | PASS |
| Tag / Release / Channel 变更 | 未执行 |

## SEC-006：旧凭据失效验证

PENDING — 必须先完成 SEC-005 撤销旧凭据，再运行：

\`bash scripts/owner-gate/verify-r2-credential-rotation.sh --old-denial-only\`

## 人工复核仍需完成

- [ ] 新 Token 的平台权限范围仅覆盖所需 Bucket / 对象操作；
- [ ] Repository / Organization / Environment / Dependabot / Codespaces Secrets 已盘点；
- [ ] 其他 Provider 凭据已按同一规则轮换并验证；
- [ ] 本地 shell history、CI 日志和密码管理器共享项不存在旧值；
- [ ] 执行人与复核人已签字；
- [ ] 本文件及相关 PR、Issue、Actions 日志不含任何 Secret 值。
EOF

  assert_evidence_does_not_contain "$NEW_CF_R2_ACCESS_KEY_ID"
  assert_evidence_does_not_contain "$NEW_CF_R2_SECRET_ACCESS_KEY"
  echo "New R2 credential verification passed. Revocation has not been tested yet."
}

validate_old_credential_denial() {
  local started_at finished_at old_status old_last4
  if [[ ! -f "$EVIDENCE_PATH" ]] || ! grep -Fq '| 新凭据隔离对象上传 | PASS |' "$EVIDENCE_PATH"; then
    echo "SEC-006 requires an existing SEC-004 PASS evidence file at EVIDENCE_PATH." >&2
    exit 2
  fi
  if grep -Fq 'OLD-CREDENTIAL-DENIAL-PASSED' "$EVIDENCE_PATH"; then
    echo "SEC-006 evidence is already present; refusing to append a duplicate result." >&2
    exit 2
  fi

  started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "Confirming the revoked credential is denied by a read-only request..."
  set +e
  run_old_aws s3api list-objects-v2 \
    --bucket "$R2_BUCKET" \
    --max-items 1 \
    --endpoint-url "$ENDPOINT_URL" \
    --region auto >/dev/null 2>&1
  old_status=$?
  set -e

  if [[ "$old_status" -eq 0 ]]; then
    echo "Old credential is still accepted. Gate remains NO-GO." >&2
    exit 3
  fi

  finished_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  old_last4="$(redacted_last4 "$OLD_CF_R2_ACCESS_KEY_ID")"
  cat >>"$EVIDENCE_PATH" <<EOF

<!-- OLD-CREDENTIAL-DENIAL-PASSED -->
### SEC-006 最终结果：PASSED

> 执行开始（UTC）：\`${started_at}\`  
> 执行完成（UTC）：\`${finished_at}\`  
> 旧 Access Key 脱敏标识：\`last4:${old_last4}\`

| 检查项 | 结果 |
|---|---|
| 旧凭据安全只读请求 | DENIED（退出码 \`${old_status}\`） |
| 旧凭据写入操作 | 未执行 |
| Tag / Release / Channel 变更 | 未执行 |

该结果只证明此旧 R2 凭据在观测时点被拒绝。Issue #21 仍需完成其他 Provider 和人工复核。
EOF

  assert_evidence_does_not_contain "$OLD_CF_R2_ACCESS_KEY_ID"
  assert_evidence_does_not_contain "$OLD_CF_R2_SECRET_ACCESS_KEY"
  echo "Revoked R2 credential denial verified. Redacted evidence updated: $EVIDENCE_PATH"
}

case "$MODE" in
  --new-only)
    validate_new_credential
    ;;
  --old-denial-only)
    validate_old_credential_denial
    ;;
  --full)
    validate_new_credential
    validate_old_credential_denial
    ;;
esac
