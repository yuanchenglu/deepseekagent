#!/usr/bin/env python3
"""
Auto-generate Docsify _sidebar.md from a markdown article directory.
Each folder = a sidebar section, each .md file = a link.
Prioritizes article_optimized.md > article_final.md > article_full.md > first .md.

Usage: python3 generate_sidebar.py
Config: Edit ARTICLE_DIR and OUTPUT_FILE below.
"""
import os
import re
import subprocess
from pathlib import Path

# === CONFIG ===
ARTICLE_DIR = Path.home() / "Documents" / "article"
OUTPUT_FILE = Path.home() / "Documents" / "docsify-site" / "_sidebar.md"

PREFERRED_NAMES = [
    "article_optimized.md",
    "article_final.md",
    "article_full.md",
    "index.md",
    "README.md"
]

def find_best_md(directory: Path) -> str | None:
    """Find the best markdown file in a directory."""
    md_files = list(directory.glob("*.md"))
    if not md_files:
        return None
    for pref in PREFERRED_NAMES:
        for f in md_files:
            if f.name == pref:
                return f.name
    md_files.sort(key=lambda x: x.name.lower())
    return md_files[0].name

def get_display_name(folder_name: str) -> str:
    """Convert folder name to display-friendly name."""
    name = folder_name.strip()
    name = re.sub(r'^[\d\.\s_]+', '', name)
    if len(name) > 40:
        name = name[:38] + '...'
    return name if name else folder_name

def sync_readme():
    """Sync README.md to article root for Docsify homepage."""
    readme_src = Path.home() / "Documents" / "docsify-site" / "docs" / "README.md"
    readme_dst = ARTICLE_DIR / "README.md"
    if readme_src.exists():
        readme_dst.write_text(readme_src.read_text(encoding='utf-8'), encoding='utf-8')

def generate_sidebar() -> str:
    """Generate _sidebar.md content."""
    lines = ["<!-- Auto-generated sidebar — do not edit manually -->", ""]
    lines.append("- 📚 **文章目录**")
    lines.append("")

    if not ARTICLE_DIR.exists():
        lines.append("> ⚠️ 文章目录不存在")
        return "\n".join(lines)

    dirs = sorted(
        [d for d in ARTICLE_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')],
        key=lambda d: d.name.lower()
    )

    for d in dirs:
        best_md = find_best_md(d)
        display = get_display_name(d.name)
        if best_md:
            rel_path = f"{d.name}/{best_md}"
            lines.append(f"  - [{display}]({rel_path})")
        else:
            lines.append(f"  - {display} (空)")

        other_mds = sorted(
            [f for f in d.glob("*.md") if f.name != best_md],
            key=lambda f: f.name.lower()
        )
        for md in other_mds:
            sub_name = md.stem[:30]
            rel_path = f"{d.name}/{md.name}"
            lines.append(f"    - [{sub_name}]({rel_path})")

    loose_mds = sorted(
        [f for f in ARTICLE_DIR.iterdir() 
         if f.is_file() and f.suffix == '.md' and not f.name.startswith('.') and f.name != 'README.md'],
        key=lambda f: f.name.lower()
    )
    if loose_mds:
        lines.append("")
        lines.append("- 📄 **未分类文章**")
        for f in loose_mds:
            name = f.stem[:40]
            lines.append(f"  - [{name}]({f.name})")

    return "\n".join(lines)

if __name__ == "__main__":
    sync_readme()
    sidebar = generate_sidebar()
    OUTPUT_FILE.write_text(sidebar, encoding='utf-8')
    print(f"✅ Sidebar: {OUTPUT_FILE} ({len(sidebar.splitlines())} lines)")
    # Reload nginx
    subprocess.run(
        ["docker", "exec", "study-docsify", "nginx", "-s", "reload"],
        capture_output=True
    )
