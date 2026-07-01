#!/usr/bin/env python3
"""
generate-conflict-report.py — Hermes 上游同步冲突报告辅助脚本

用于读取 git merge 冲突输出，生成结构化的冲突报告。
可独立使用，也可被 sync-hermes-upstream.sh 自动调用。

用法:
  python3 scripts/generate-conflict-report.py <冲突报告文件>
  python3 scripts/generate-conflict-report.py --analyze <冲突文件1> [冲突文件2 ...]

功能:
  - 读取已生成的冲突报告 markdown 文件，追加结构化分析
  - 直接分析冲突文件中的冲突标记（<<<<<<< / ======= / >>>>>>>）
  - 输出优化后的冲突分析 JSON / 表格
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ============================================================================
# 常量定义
# ============================================================================

# 高优先级关键词（核心文件）
HIGH_PRIORITY_KEYWORDS = [
    "core", "main", "harness", "config", "cli", "runtime",
    "agent", "skill", "plugin", "server", "engine",
]

# 低优先级关键词（文档/非代码文件）
LOW_PRIORITY_KEYWORDS = [
    ".md", ".txt", ".rst", "readme", "license", "changelog",
    ".png", ".jpg", ".svg", ".ico",
]


# ============================================================================
# 冲突分析函数
# ============================================================================

def classify_priority(filepath: str) -> str:
    """根据文件路径判断冲突优先级。"""
    fp_lower = filepath.lower()

    # 低优先级：文档、图片、配置文件
    for kw in LOW_PRIORITY_KEYWORDS:
        if fp_lower.endswith(kw) or kw in fp_lower:
            return "低"

    # 高优先级：核心代码文件
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in fp_lower:
            return "高"

    # 默认中优先级
    return "中"


def suggest_action(priority: str, filepath: str) -> str:
    """根据优先级和文件路径给出决策建议。"""
    fp_lower = filepath.lower()
    if priority == "低":
        return "可手工合并文档内容"
    if priority == "高":
        return "需 CEO 决策：保留 DeepAgent 修改 或 接受上游"
    # 中优先级
    if fp_lower.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
        return "逐行手动合并"
    return "需要人工检查后合并"


def count_conflict_markers(filepath: str) -> int:
    """统计文件中的冲突标记对数（<<<<<<< 的出现次数）。"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return len(re.findall(r'^<<<<<<< ', content, re.MULTILINE))
    except (FileNotFoundError, IOError):
        return 0


def analyze_conflict_files(file_list: list[str], repo_root: str | None = None) -> list[dict]:
    """分析冲突文件列表，返回结构化信息。"""
    results = []
    for f in file_list:
        full_path = f
        if repo_root and not os.path.isabs(f):
            full_path = os.path.join(repo_root, f)

        priority = classify_priority(f)
        marker_count = count_conflict_markers(full_path)
        suggestion = suggest_action(priority, f)

        results.append({
            "file": f,
            "priority": priority,
            "conflict_markers": marker_count,
            "suggestion": suggestion,
            "full_path": full_path,
        })
    return results


def extract_conflict_files_from_report(report_path: str) -> list[str]:
    """从冲突报告 markdown 文件中提取冲突文件列表。"""
    files = []
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找表格中的文件引用（`path/to/file` 格式）
        pattern = r'`([^`]+)`'
        in_conflict_section = False
        for line in content.split("\n"):
            if "检测到冲突" in line:
                in_conflict_section = True
            elif "CEO 决策指引" in line:
                in_conflict_section = False

            if in_conflict_section:
                matches = re.findall(pattern, line)
                for m in matches:
                    # 过滤掉非文件路径（如 commit hash、分支名）
                    if ("/" in m or "\\" in m) and not m.startswith("`"):
                        files.append(m)
    except FileNotFoundError:
        print(f"错误: 找不到报告文件 {report_path}", file=sys.stderr)
    return list(set(files))


def generate_structured_report(report_path: str) -> str:
    """为已有的冲突报告追加结构化分析内容。"""
    if not os.path.exists(report_path):
        return f"错误: 文件 {report_path} 不存在"

    # 从报告中提取文件列表
    conflict_files = extract_conflict_files_from_report(report_path)
    if not conflict_files:
        # 尝试从当前目录读取冲突文件
        print("未从报告中解析出文件列表，尝试当前工作目录...")
        conflict_files = [
            f for f in Path.cwd().rglob("*")
            if f.is_file() and not f.name.startswith(".")
        ][:20]  # 限制数量避免误判

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(report_path)))
    analysis = analyze_conflict_files(conflict_files, repo_root)

    # 生成追加内容
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "",
        "---",
        "",
        "## 🔬 结构化冲突分析（自动生成）",
        "",
        f"**分析时间**: {now}",
        f"**冲突文件数**: {len(analysis)}",
        "",
    ]

    if analysis:
        # 按优先级分组
        high = [a for a in analysis if a["priority"] == "高"]
        mid = [a for a in analysis if a["priority"] == "中"]
        low = [a for a in analysis if a["priority"] == "低"]

        lines.append("### 优先级分布")
        lines.append("")
        lines.append(f"- 🔴 **高优先级**: {len(high)} 个文件 — 核心功能文件，需 CEO 审慎决策")
        lines.append(f"- 🟡 **中优先级**: {len(mid)} 个文件 — 常规功能文件，可手动合并")
        lines.append(f"- 🟢 **低优先级**: {len(low)} 个文件 — 文档/配置，可快速合并")
        lines.append("")

        # 详细表格
        lines.append("### 详细分析")
        lines.append("")
        lines.append("| 文件 | 优先级 | 冲突标记数 | 建议操作 |")
        lines.append("|------|--------|-----------|---------|")
        for a in analysis:
            priority_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(a["priority"], "⚪")
            lines.append(
                f"| `{a['file']}` | {priority_icon} {a['priority']} | "
                f"{a['conflict_markers']} | {a['suggestion']} |"
            )
        lines.append("")

        # 决策树建议
        lines.append("### 🎯 决策建议")
        lines.append("")
        if high:
            lines.append("**建议优先处理以下高优先级文件：**")
            lines.append("")
            for a in high:
                lines.append(f"1. **`{a['file']}`** — {a['suggestion']}")
            lines.append("")
            lines.append("> 提示：高优先级文件涉及核心功能。如果上游修改与 DeepAgent 方向一致，")
            lines.append("> 建议手动合并；如果冲突较大，可暂缓同步，等待 CEO 决策。")
            lines.append("")

        # JSON 摘要
        lines.append("### 📊 JSON 摘要（机器可读）")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(analysis, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    # 追加到报告文件
    append_content = "\n".join(lines)
    try:
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(append_content + "\n")
        return f"✅ 结构化分析已追加到 {report_path}"
    except IOError as e:
        return f"❌ 写入失败: {e}"


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    if sys.argv[1] == "--analyze":
        # 直接分析冲突文件
        files = sys.argv[2:]
        if not files:
            print("错误: --analyze 需要指定至少一个文件路径", file=sys.stderr)
            return 1

        analysis = analyze_conflict_files(files)
        print("冲突分析结果：")
        print("=" * 60)
        for item in analysis:
            icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(item["priority"], "⚪")
            print(f"{icon} {item['file']}")
            print(f"   优先级: {item['priority']}")
            print(f"   冲突标记: {item['conflict_markers']}")
            print(f"   建议: {item['suggestion']}")
            print()

        # 输出 JSON
        print("JSON 输出:")
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    else:
        # 分析已有报告文件
        result = generate_structured_report(sys.argv[1])
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
