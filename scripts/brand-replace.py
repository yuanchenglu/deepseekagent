#!/usr/bin/env python3
"""
DeepAgent 品牌替换脚本（从 Hermes fork 清理）
用法：
  python scripts/brand-replace.py --dry-run          # 只预览，不修改
  python scripts/brand-replace.py --apply            # 实际执行（谨慎使用）
  python scripts/brand-replace.py --apply --target tools/   # 只处理特定目录
"""

import os
import re
import sys
from pathlib import Path

REPLACEMENTS = [
    # (原字符串, 新字符串, 是否大小写敏感)
    ("hermes", "deepagent", True),
    ("Hermes", "DeepAgent", True),
    # 谨慎处理全大写，避免误伤常量
    # ("HERMES", "DEEPAGENT", True),
]

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", ".pytest_cache", "embedded"}
SKIP_FILES = {"uv.lock", "package-lock.json", ".gitmodules"}

def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.name in SKIP_FILES:
        return True
    return False

def replace_in_file(file_path: Path, dry_run: bool) -> int:
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    original = text
    changes = 0

    for old, new, case_sensitive in REPLACEMENTS:
        if case_sensitive:
            if old in text:
                text = text.replace(old, new)
                changes += text.count(new) - original.count(new)  # rough count
        else:
            pattern = re.compile(re.escape(old), re.IGNORECASE)
            if pattern.search(text):
                text = pattern.sub(new, text)
                changes += 1

    if text != original and not dry_run:
        file_path.write_text(text, encoding="utf-8")
    return changes if text != original else 0

def main():
    dry_run = "--dry-run" in sys.argv or "--apply" not in sys.argv
    target = None
    for arg in sys.argv:
        if arg.startswith("--target="):
            target = arg.split("=", 1)[1]

    root = Path(__file__).parent.parent
    if target:
        search_path = root / target
    else:
        search_path = root

    print(f"{'[DRY-RUN]' if dry_run else '[APPLY]'} Brand replacement starting...")
    print(f"Root: {root}")
    if target:
        print(f"Target: {target}")

    total_files = 0
    total_changes = 0

    for path in search_path.rglob("*"):
        if path.is_file() and not should_skip(path):
            # 只处理文本类文件
            if path.suffix in {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".html", ".js", ".ts", ".sh"}:
                changes = replace_in_file(path, dry_run)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
                    print(f"  {'[would change]' if dry_run else '[changed]'} {path.relative_to(root)} ({changes})")

    print(f"\nSummary: {total_files} files affected, ~{total_changes} replacements.")
    if dry_run:
        print("This was a dry-run. Run with --apply to make changes.")
    else:
        print("Changes applied. Please review git diff and test thoroughly.")

if __name__ == "__main__":
    main()