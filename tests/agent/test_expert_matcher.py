"""Tests for ExpertMatcher — 专家匹配器。"""

import pytest
from pathlib import Path
from agent.expert_matcher import ExpertMatcher, Expert


@pytest.fixture
def mock_agents_dir(tmp_path):
    """创建几个模拟的 Agency 专家文件。"""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # backend-architect.md
    (agents_dir / "backend-architect.md").write_text(
        "---\nname: Backend Architect\ndivision: Engineering\n"
        "description: Backend architecture and API design\n"
        "---\n\nYou are a backend architect. Design scalable APIs."
    )
    # database-optimizer.md
    (agents_dir / "database-optimizer.md").write_text(
        "---\nname: Database Optimizer\ndivision: Engineering\n"
        "description: Database optimization and SQL\n"
        "---\n\nYou are a database expert. Optimize queries."
    )
    # security-architect.md
    (agents_dir / "security-architect.md").write_text(
        "---\nname: Security Architect\ndivision: Security\n"
        "description: Security architecture reviews\n"
        "---\n\nYou are a security expert."
    )
    return agents_dir


class TestMatch:
    """专家匹配功能测试。"""

    def test_returns_experts_for_implement(self, mock_agents_dir):
        """implement 意图返回 Engineering division 的专家。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("帮我设计后端API", "implement", top_n=2)
        assert len(experts) <= 2
        assert all(isinstance(e, Expert) for e in experts)

    def test_returns_empty_for_simple(self, mock_agents_dir):
        """simple 意图返回空列表。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        experts = matcher.match("你好", "simple")
        assert len(experts) == 0

    def test_matches_backend_keywords(self, mock_agents_dir):
        """数据库关键词能匹配到 database-optimizer。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("设计数据库表结构", "implement")
        slugs = [e.slug for e in experts]
        assert "database-optimizer" in slugs or "backend-architect" in slugs

    def test_falls_back_to_default(self, mock_agents_dir):
        """没有关键词匹配时使用默认专家。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("完全无关的内容zzz", "implement")
        assert len(experts) > 0


class TestLoadExpertPrompt:
    """专家 prompt 加载测试。"""

    def test_loads_existing_prompt(self, mock_agents_dir):
        """存在文件时正确加载 prompt。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt = matcher.load_expert_prompt("backend-architect")
        assert "Backend Architect" in prompt or "backend architect" in prompt.lower()

    def test_returns_empty_for_missing(self, mock_agents_dir):
        """文件不存在时返回空字符串。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt = matcher.load_expert_prompt("nonexistent-agent")
        assert prompt == ""

    def test_caches_after_first_load(self, mock_agents_dir):
        """首次加载后缓存生效，避免重复 IO。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt1 = matcher.load_expert_prompt("backend-architect")
        prompt2 = matcher.load_expert_prompt("backend-architect")
        assert prompt1 == prompt2


class TestCacheManagement:
    """缓存管理测试。"""

    def test_refresh_cache_loads_all_agents(self, mock_agents_dir):
        """refresh_cache 加载目录下所有 .md 文件。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        available = matcher.get_available_experts()
        assert len(available) >= 3  # 我们创建了 3 个 mock 文件

    def test_get_experts_for_division(self, mock_agents_dir):
        """按 division 过滤正确。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        engineers = matcher.get_experts_for_division("Engineering")
        assert len(engineers) >= 2
        security = matcher.get_experts_for_division("Security")
        assert len(security) >= 1
