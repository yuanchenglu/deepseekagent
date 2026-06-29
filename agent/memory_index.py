# === DeepAgent: StarRoad Cognition ===
"""Memory 嵌套索引管理器（StarRoad Cognition）。
核心规则：MAP.md 只存导航指引（1-2KB），深度内容存在于子文档按需加载。"""

from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

COGNITIVE_FENCE_START = "-----COGNITIVE_INDEX_START-----"
COGNITIVE_FENCE_END = "-----COGNITIVE_INDEX_END-----"
MAP_FILENAME = "MAP.md"


class MemoryIndex:
    """记忆嵌套索引管理器。

    用法：
        index = MemoryIndex()
        summary = index.index_summary()  # → 注入 system prompt 的导航段
        entries = index.navigate("deepseek")  # → 找到相关条目
        content = index.read_nested("skills/deepseek-physics/SKILL.md")  # → 读子文档
    """

    def __init__(self, index_path: str | Path | None = None):
        if index_path is None:
            index_path = get_hermes_home() / "memories" / MAP_FILENAME
        self._index_path = Path(index_path)
        self._memories_dir = self._index_path.parent
        self._map_content: str | None = None  # 缓存 MAP.md 内容

    # -- 公开接口 --

    def index_summary(self) -> str:
        """返回注入 system prompt 的导航段。

        格式：
            -----COGNITIVE_INDEX_START-----
            (MAP.md 的导航内容，1-2KB)
            -----COGNITIVE_INDEX_END-----

        如果 MAP.md 不存在或为空，返回空字符串。
        """
        content = self._load_map()
        if not content:
            return ""

        # 限制大小：最多 2000 字符
        if len(content) > 2000:
            content = content[:1950] + "\n...(truncated)"

        return f"{COGNITIVE_FENCE_START}\n{content}\n{COGNITIVE_FENCE_END}"

    def navigate(self, topic: str) -> list[dict]:
        """搜索 MAP.md 找到与 topic 相关的索引条目。

        Args:
            topic: 搜索关键词

        Returns:
            [{"topic": str, "path": str, "description": str}, ...]
        """
        content = self._load_map()
        if not content:
            return []

        results = []
        topic_lower = topic.lower()
        # 解析 MAP.md 中的条目：- topic: path — description
        pattern = re.compile(r"^-\s+(.+?):\s+(.+?)(?:\s+—\s+(.+))?$", re.MULTILINE)
        for match in pattern.finditer(content):
            entry_topic = match.group(1).strip()
            entry_path = match.group(2).strip()
            entry_desc = match.group(3).strip() if match.group(3) else ""

            if topic_lower in entry_topic.lower() or topic_lower in entry_desc.lower():
                results.append({
                    "topic": entry_topic,
                    "path": entry_path,
                    "description": entry_desc,
                })

        return results

    def read_nested(self, path: str) -> str:
        """从索引导航读取子文档内容。

        Args:
            path: 相对路径（如 "skills/deepseek-physics/SKILL.md"）
                  或绝对路径

        Returns:
            子文档的文本内容。如果文件不存在，返回空字符串。
        """
        target = Path(path)
        if not target.is_absolute():
            target = self._memories_dir / target

        if not target.exists() or not target.is_file():
            logger.debug("MemoryIndex: nested path '%s' not found", target)
            return ""

        try:
            return target.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("MemoryIndex: failed to read '%s': %s", target, e)
            return ""

    def update_entry(self, topic: str, path: str, description: str) -> None:
        """更新或新增索引条目。

        如果 topic 已存在，更新其 path 和 description。
        如果不存在，追加新条目。
        """
        content = self._load_map()
        if not content:
            # MAP.md 不存在，创建基本结构
            content = "# 记忆索引（导航层）\n\n## 关键知识领域\n\n"
            content += f"- {topic}: {path} — {description}\n"
        else:
            # 检查是否已存在
            pattern = re.compile(
                rf"^-\s+{re.escape(topic)}:\s+.*$", re.MULTILINE
            )
            if pattern.search(content):
                # 更新已有条目
                new_line = f"- {topic}: {path} — {description}"
                content = pattern.sub(new_line, content)
            else:
                # 追加新条目
                content += f"- {topic}: {path} — {description}\n"

        self._write_map(content)

    def build_initial_index(self) -> None:
        """首次初始化：扫描 memories/ 下子目录，构建 MAP.md。

        根据子目录名称分类到不同章节：
          - skills/ → 关键知识领域
          - paper-notes/ → 研究笔记
          - references/ → 参考资料
          - 其他子目录 → 其他

        如果 MAP.md 已存在且非空，跳过初始化。
        """
        if self._index_path.exists():
            content = self._read_file_content(self._index_path)
            if content and content.strip():
                logger.info("MemoryIndex: MAP.md already exists, skipping initialization")
                return

        # 分类映射：子目录名 → 章节名
        section_map = {
            "skills": "关键知识领域",
            "paper-notes": "研究笔记",
            "references": "参考资料",
        }
        sections: dict[str, list[str]] = {
            "关键知识领域": [],
            "研究笔记": [],
            "参考资料": [],
            "其他": [],
        }

        if self._memories_dir.exists():
            for child in sorted(self._memories_dir.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    # 确定该子目录归属的章节
                    section_name = section_map.get(child.name, "其他")

                    # 扫描子目录中的 .md 文件（排除 MAP.md 自身）
                    md_files = sorted(child.glob("*.md"))
                    for md_file in md_files:
                        if md_file.name == MAP_FILENAME:
                            continue
                        rel_path = md_file.relative_to(self._memories_dir)
                        sections[section_name].append(
                            f"- {child.name}: {rel_path}\n"
                        )

        # 构建 MAP.md 内容
        lines = ["# 记忆索引（导航层）", ""]
        for section_name in ["关键知识领域", "研究笔记", "参考资料", "其他"]:
            entries = sections.get(section_name, [])
            if entries:
                lines.append(f"## {section_name}")
                lines.append("")
                lines.extend(entries)
                lines.append("")

        content = "\n".join(lines).strip()
        if content:
            self._write_map(content)
            logger.info("MemoryIndex: initial MAP.md created")

    # -- 内部方法 --

    def _load_map(self) -> str:
        """读取 MAP.md 内容（带缓存）。"""
        if self._map_content is not None:
            return self._map_content
        content = self._read_file_content(self._index_path)
        self._map_content = content or ""
        return self._map_content

    def _write_map(self, content: str) -> None:
        """写回 MAP.md 并更新缓存。"""
        self._memories_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._index_path.write_text(content, encoding="utf-8")
            self._map_content = content
        except Exception as e:
            logger.error("MemoryIndex: failed to write MAP.md: %s", e)

    @staticmethod
    def _read_file_content(path: Path) -> str:
        """安全读取文件内容，失败返回空字符串。"""
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug("MemoryIndex: failed to read %s: %s", path, e)
            return ""
