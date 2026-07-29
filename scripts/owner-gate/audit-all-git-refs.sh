#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/owner-gate/audit-all-git-refs.sh \
    https://github.com/yuanchenglu/deepseekagent.git \
    /absolute/path/to/audit-output

Requirements:
  - git
  - gitleaks
  - python3

This script is read-only with respect to the remote repository. It creates a mirror clone,
scans every reachable Git ref with gitleaks, and writes a redacted JSON report plus a
Markdown summary. It never rewrites history and never force-pushes.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "$#" -ne 2 ]]; then
  usage >&2
  exit 2
fi

REPOSITORY_URL="$1"
OUTPUT_DIR="$2"

for command_name in git gitleaks python3 mktemp date; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 2
  fi
done

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
WORK_DIR="$(mktemp -d)"
MIRROR_DIR="${WORK_DIR}/repository.git"
REPORT_JSON="${OUTPUT_DIR}/gitleaks-all-refs-redacted.json"
REFS_TXT="${OUTPUT_DIR}/git-refs.txt"
FSCK_TXT="${OUTPUT_DIR}/git-fsck.txt"
SUMMARY_MD="${OUTPUT_DIR}/all-refs-secret-audit.md"
STARTED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT INT TERM

echo "Creating isolated mirror clone..."
git clone --mirror "$REPOSITORY_URL" "$MIRROR_DIR" >/dev/null

(
  cd "$MIRROR_DIR"
  git show-ref | sort >"$REFS_TXT"
  git fsck --full --no-reflogs --unreachable >"$FSCK_TXT" 2>&1 || true

  set +e
  gitleaks git \
    --redact \
    --no-banner \
    --report-format json \
    --report-path "$REPORT_JSON" \
    .
  GITLEAKS_STATUS=$?
  set -e

  python3 - "$REPORT_JSON" "$REFS_TXT" "$FSCK_TXT" "$SUMMARY_MD" \
    "$REPOSITORY_URL" "$STARTED_AT" "$GITLEAKS_STATUS" <<'PY'
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

report_path = Path(sys.argv[1])
refs_path = Path(sys.argv[2])
fsck_path = Path(sys.argv[3])
summary_path = Path(sys.argv[4])
repository_url = sys.argv[5]
started_at = sys.argv[6]
status = int(sys.argv[7])

try:
    findings = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else []
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid gitleaks JSON report: {exc}")

if not isinstance(findings, list):
    raise SystemExit("Expected gitleaks report to be a JSON list")

rules = Counter(str(item.get("RuleID") or "unknown") for item in findings)
files = Counter(str(item.get("File") or "unknown") for item in findings)
refs = [line for line in refs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
fsck_lines = [line for line in fsck_path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
finished_at = datetime.now(timezone.utc).isoformat()

lines = [
    "# Git 全 refs 秘密扫描报告",
    "",
    f"> 仓库：`{repository_url}`  ",
    f"> 开始时间（UTC）：`{started_at}`  ",
    f"> 完成时间（UTC）：`{finished_at}`  ",
    "> 扫描方式：隔离 mirror clone + `gitleaks git --redact`  ",
    "> 远程写操作：**无**",
    "",
    "## 摘要",
    "",
    f"- Git refs：{len(refs)}",
    f"- Gitleaks findings：{len(findings)}",
    f"- Gitleaks exit status：`{status}`",
    f"- `git fsck` 输出行数：{len(fsck_lines)}",
    "",
]

if rules:
    lines.extend(["## Findings 按规则", "", "| Rule | 数量 |", "|---|---:|"])
    for rule, count in sorted(rules.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{rule}` | {count} |")
    lines.append("")

if files:
    lines.extend(["## Findings 按文件（前 30）", "", "| 文件 | 数量 |", "|---|---:|"])
    for file_name, count in files.most_common(30):
        lines.append(f"| `{file_name}` | {count} |")
    lines.append("")

lines.extend(
    [
        "## 判定",
        "",
        "- Findings 为 0：扫描证据可用于关闭全 refs 重扫子 Gate，但仍需确认扫描覆盖和工具版本。",
        "- Findings 大于 0：不得发布；先确认对应凭据已失效，再在备份 mirror 中进行历史清理。",
        "- 本脚本不执行 `git filter-repo`、force push、Tag 删除或 Release/channel 变更。",
        "- 完整逐项内容位于同目录的 `gitleaks-all-refs-redacted.json`，所有匹配值应已脱敏。",
        "",
    ]
)
summary_path.write_text("\n".join(lines), encoding="utf-8")
PY

  if [[ "$GITLEAKS_STATUS" -eq 0 ]]; then
    echo "All-refs scan passed with no findings."
  elif [[ "$GITLEAKS_STATUS" -eq 1 ]]; then
    echo "All-refs scan found potential secrets. Review the redacted report." >&2
  else
    echo "Gitleaks execution failed with status $GITLEAKS_STATUS." >&2
    exit "$GITLEAKS_STATUS"
  fi
)

echo "Audit outputs written to: $OUTPUT_DIR"
if [[ -s "$REPORT_JSON" ]]; then
  exit 3
fi
