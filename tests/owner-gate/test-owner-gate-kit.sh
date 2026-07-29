#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIFY_SCRIPT="${ROOT_DIR}/scripts/owner-gate/verify-r2-credential-rotation.sh"
AUDIT_SCRIPT="${ROOT_DIR}/scripts/owner-gate/audit-all-git-refs.sh"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT INT TERM

bash -n "$VERIFY_SCRIPT"
bash -n "$AUDIT_SCRIPT"
bash "$VERIFY_SCRIPT" --help >/dev/null
bash "$AUDIT_SCRIPT" --help >/dev/null

FAKE_BIN="${TEMP_DIR}/bin"
FAKE_STORE="${TEMP_DIR}/store"
EVIDENCE_PATH="${TEMP_DIR}/evidence.md"
mkdir -p "$FAKE_BIN" "$FAKE_STORE"

cat >"${FAKE_BIN}/aws" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${AWS_ACCESS_KEY_ID:-}" == "old-access-key-0002" ]]; then
  exit 42
fi

if [[ "${AWS_ACCESS_KEY_ID:-}" != "new-access-key-0001" ]]; then
  echo "unexpected access key" >&2
  exit 90
fi

if [[ "${1:-}" == "s3" && "${2:-}" == "cp" ]]; then
  source_path="$3"
  destination_path="$4"
  if [[ "$source_path" == s3://* ]]; then
    cp "${FAKE_AWS_STORE}/object.bin" "$destination_path"
  elif [[ "$destination_path" == s3://* ]]; then
    cp "$source_path" "${FAKE_AWS_STORE}/object.bin"
  else
    exit 91
  fi
  exit 0
fi

if [[ "${1:-}" == "s3" && "${2:-}" == "rm" ]]; then
  rm -f "${FAKE_AWS_STORE}/object.bin"
  exit 0
fi

if [[ "${1:-}" == "s3api" && "${2:-}" == "list-objects-v2" ]]; then
  exit 0
fi

exit 92
EOF
chmod +x "${FAKE_BIN}/aws"

PATH="${FAKE_BIN}:${PATH}" \
FAKE_AWS_STORE="$FAKE_STORE" \
CF_ACCOUNT_ID="account-1234" \
NEW_CF_R2_ACCESS_KEY_ID="new-access-key-0001" \
NEW_CF_R2_SECRET_ACCESS_KEY="new-secret-value-must-not-leak" \
OLD_CF_R2_ACCESS_KEY_ID="old-access-key-0002" \
OLD_CF_R2_SECRET_ACCESS_KEY="old-secret-value-must-not-leak" \
EVIDENCE_PATH="$EVIDENCE_PATH" \
  bash "$VERIFY_SCRIPT" >/dev/null

grep -Fq '| 新凭据隔离对象上传 | PASS |' "$EVIDENCE_PATH"
grep -Fq '| 旧凭据安全只读请求 | DENIED（退出码 `42`） |' "$EVIDENCE_PATH"

for forbidden in \
  'new-access-key-0001' \
  'old-access-key-0002' \
  'new-secret-value-must-not-leak' \
  'old-secret-value-must-not-leak'; do
  if grep -Fq "$forbidden" "$EVIDENCE_PATH"; then
    echo "Evidence leaked forbidden value: $forbidden" >&2
    exit 1
  fi
done

if [[ -e "${FAKE_STORE}/object.bin" ]]; then
  echo "Temporary R2 test object was not deleted" >&2
  exit 1
fi

echo "owner-gate kit tests passed"
