"""Tests for MemoryIndex — 记忆嵌套索引管理器。"""

import pytest
from pathlib import Path
from agent.memory_index import MemoryIndex, COGNITIVE_FENCE_START, COGNITIVE_FENCE_END


@pytest.fixture
def tmp_index(tmp_path):
    """创建临时目录的 MemoryIndex 实例。"""
    mem_dir = tmp_path / "memories"
    mem_dir.mkdir(parents=True)
    index_path = mem_dir / "MAP.md"
    return MemoryIndex(str(index_path))


class TestIndexSummary:
    def test_returns_empty_when_no_map(self, tmp_index):
        """MAP.md 不存在时返回空字符串。"""
        summary = tmp_index.index_summary()
        assert summary == ""

    def test_wraps_content_with_fences(self, tmp_index):
        """返回内容被 COGNITIVE_FENCE 围栏包裹。"""
        tmp_index.update_entry("test-topic", "test/path.md", "test desc")
        summary = tmp_index.index_summary()
        assert summary.startswith(COGNITIVE_FENCE_START)
        assert summary.endswith(COGNITIVE_FENCE_END)

    def test_truncates_to_2000_chars(self, tmp_index):
        """超长内容被截断到 2000 字符。"""
        for i in range(200):
            tmp_index.update_entry(f"topic-{i}", f"path/{i}.md", "d" * 50)
        summary = tmp_index.index_summary()
        # 拿到围栏内部的内容
        inner = summary[len(COGNITIVE_FENCE_START):-len(COGNITIVE_FENCE_END)].strip()
        assert len(inner) <= 2100


class TestNavigate:
    def test_finds_matching_topic(self, tmp_index):
        tmp_index.update_entry("deepseek-physics", "skills/dp/SKILL.md", "DeepSeek V3 physics")
        results = tmp_index.navigate("deepseek")
        assert len(results) >= 1
        assert results[0]["topic"] == "deepseek-physics"

    def test_returns_empty_for_no_match(self, tmp_index):
        tmp_index.update_entry("react", "notes/react.md", "React notes")
        results = tmp_index.navigate("vue")
        assert len(results) == 0

    def test_case_insensitive_search(self, tmp_index):
        tmp_index.update_entry("DeepSeek-Physics", "skills/dp/SKILL.md", "")
        results = tmp_index.navigate("deepseek")
        assert len(results) >= 1


class TestReadNested:
    def test_reads_existing_file(self, tmp_index, tmp_path):
        """读取存在的子文档。"""
        sub_file = tmp_path / "memories" / "test.md"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("hello world")
        content = tmp_index.read_nested(str(sub_file))
        assert content == "hello world"

    def test_returns_empty_for_missing_file(self, tmp_index):
        content = tmp_index.read_nested("/nonexistent/path.md")
        assert content == ""

    def test_resolves_relative_path(self, tmp_index, tmp_path):
        """相对路径基于 memories_dir 解析。"""
        sub_file = tmp_path / "memories" / "sub" / "doc.md"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("relative content")
        content = tmp_index.read_nested("sub/doc.md")
        assert content == "relative content"


class TestUpdateEntry:
    def test_creates_map_when_not_exists(self, tmp_index):
        """MAP.md 不存在时，update_entry 创建它。"""
        tmp_index.update_entry("my-topic", "my/path.md", "desc")
        assert tmp_index._index_path.exists()

    def test_updates_existing_entry(self, tmp_index):
        tmp_index.update_entry("topic", "old/path.md", "old desc")
        tmp_index.update_entry("topic", "new/path.md", "new desc")
        content = tmp_index._load_map()
        assert "new/path.md" in content
        assert "old/path.md" not in content


class TestBuildInitialIndex:
    def test_creates_map_with_sections(self, tmp_index, tmp_path):
        mem_dir = tmp_path / "memories"
        (mem_dir / "skills").mkdir(parents=True)
        (mem_dir / "skills" / "test.md").write_text("test")
        tmp_index.build_initial_index()
        assert tmp_index._index_path.exists()
        content = tmp_index._load_map()
        assert "关键知识领域" in content
        assert "test.md" in content

    def test_skips_if_map_exists(self, tmp_index):
        tmp_index.update_entry("existing", "path.md", "desc")
        initial_mtime = tmp_index._index_path.stat().st_mtime
        tmp_index.build_initial_index()
        assert tmp_index._index_path.stat().st_mtime == initial_mtime
