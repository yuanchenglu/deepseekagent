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

cat >"${FAKE_BIN}/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  clone)
    destination="${!#}"
    mkdir -p "$destination"
    ;;
  show-ref)
    printf '%040d refs/heads/develop\n' 0
    ;;
  fsck)
    ;;
  *)
    echo "unexpected fake git command: $*" >&2
    exit 80
    ;;
esac
EOF
chmod +x "${FAKE_BIN}/git"

cat >"${FAKE_BIN}/gitleaks" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
report_path=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --report-path)
      report_path="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [[ -z "$report_path" ]]; then
  exit 81
fi
if [[ "${FAKE_GITLEAKS_MODE:-clean}" == "findings" ]]; then
  cat >"$report_path" <<'JSON'
[{"RuleID":"generic-api-key","File":"config.env","Secret":"REDACTED"}]
JSON
  exit 1
fi
printf '[]\n' >"$report_path"
exit 0
EOF
chmod +x "${FAKE_BIN}/gitleaks"

CLEAN_OUTPUT="${TEMP_DIR}/audit-clean"
PATH="${FAKE_BIN}:${PATH}" FAKE_GITLEAKS_MODE=clean \
  bash "$AUDIT_SCRIPT" https://example.invalid/deepseekagent.git "$CLEAN_OUTPUT" >/dev/null

grep -Fxq '0' "${CLEAN_OUTPUT}/gitleaks-findings-count.txt"
grep -Fq -- '- Gitleaks findings：0' "${CLEAN_OUTPUT}/all-refs-secret-audit.md"

FINDINGS_OUTPUT="${TEMP_DIR}/audit-findings"
set +e
PATH="${FAKE_BIN}:${PATH}" FAKE_GITLEAKS_MODE=findings \
  bash "$AUDIT_SCRIPT" https://example.invalid/deepseekagent.git "$FINDINGS_OUTPUT" >/dev/null 2>&1
FINDINGS_STATUS=$?
set -e
if [[ "$FINDINGS_STATUS" -ne 3 ]]; then
  echo "Expected findings exit code 3, got $FINDINGS_STATUS" >&2
  exit 1
fi
grep -Fxq '1' "${FINDINGS_OUTPUT}/gitleaks-findings-count.txt"
grep -Fq '| `generic-api-key` | 1 |' "${FINDINGS_OUTPUT}/all-refs-secret-audit.md"

if grep -R -Fq 'must-not-leak' "$TEMP_DIR"; then
  echo "A test secret leaked into generated outputs" >&2
  exit 1
fi

echo "owner-gate kit tests passed"
