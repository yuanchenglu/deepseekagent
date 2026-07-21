#!/usr/bin/env python3
"""
Auto-generate Docsify _sidebar.md from article directory.
Recursive scan, URL-encodes non-ASCII paths, supports per-section sidebars for tabs.
"""
import re
from pathlib import Path
from urllib.parse import quote

ARTICLE_DIR = Path.home() / "Documents" / "article"
SITE_DIR = Path.home() / "Documents" / "docsify-site"
SECTIONS = ["文章", "课程", "开源项目"]

def get_display_name(name: str) -> str:
    name = re.sub(r'^[\d\.\s_]+', '', name.strip())
    return name[:40] if name else name

def encode_path(path: str) -> str:
    return '/'.join(quote(p, safe='') for p in path.split('/'))

def scan_dir(directory: Path, rel_root: Path, depth: int = 0) -> list:
    if depth > 5:
        return []
    lines = []
    indent = "  " * (depth + 1)
    
    # Files first
    for f in sorted(directory.glob("*.md"), key=lambda f: f.name.lower()):
        if f.name.startswith('.') or f.name in ('_sidebar.md', 'README.md'):
            continue
        try:
            rel = str(f.relative_to(rel_root))
        except ValueError:
            rel = f.name
        lines.append(f"{indent}- [{get_display_name(f.stem)}]({encode_path(rel)})")
    
    # Then subdirectories
    for d in sorted(directory.iterdir(), key=lambda d: d.name.lower()):
        if not d.is_dir() or d.name.startswith('.'):
            continue
        if any(d.rglob("*.md")):
            lines.append(f"{indent}- **{get_display_name(d.name)}**")
            lines.extend(scan_dir(d, rel_root, depth + 1))
    
    return lines

def generate(root: Path, title: str = "📚 **文章目录**") -> str:
    lines = ["<!-- auto-generated -->", "", f"- {title}", ""]
    if root.exists():
        lines.extend(scan_dir(root, root))
    return "\n".join(lines)

if __name__ == "__main__":
    # Global sidebar
    global_sb = generate(ARTICLE_DIR)
    (SITE_DIR / "_sidebar.md").write_text(global_sb)
    (ARTICLE_DIR / "_sidebar.md").write_text(global_sb)
    print(f"Global: {len(global_sb.splitlines())} lines")
    
    # Per-section sidebars for tab navigation
    for s in SECTIONS:
        sd = ARTICLE_DIR / s
        if sd.is_dir():
            sb = generate(sd, f"📄 **{s}**")
            (sd / "_sidebar.md").write_text(sb)
            print(f"{s}: {len(sb.splitlines())} lines")
    
    import subprocess
    subprocess.run(["docker", "exec", "study-docsify", "nginx", "-s", "reload"],
                   capture_output=True)
