"""Tests for AgentRouter — 语义路由总控。"""

import pytest
from agent.router import AgentRouter, RouteDecision
from agent.expert_matcher import Expert, ExpertMatcher


@pytest.fixture
def mock_agents_dir(tmp_path):
    """创建几个模拟的 Agency 专家文件。"""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (agents_dir / "backend-architect.md").write_text(
        "---\nname: Backend Architect\ndivision: Engineering\n"
        "description: Backend architecture and API design\n"
        "---\n\nYou are a backend architect."
    )
    (agents_dir / "database-optimizer.md").write_text(
        "---\nname: Database Optimizer\ndivision: Engineering\n"
        "description: Database optimization and SQL\n"
        "---\n\nYou are a database expert."
    )
    (agents_dir / "security-architect.md").write_text(
        "---\nname: Security Architect\ndivision: Security\n"
        "description: Security architecture reviews\n"
        "---\n\nYou are a security expert."
    )
    return agents_dir


@pytest.fixture
def router(mock_agents_dir):
    """创建 Router 实例，使用 mock 专家目录。"""
    matcher = ExpertMatcher(str(mock_agents_dir))
    matcher.refresh_cache()
    return AgentRouter(expert_matcher=matcher)


class TestClassifyIntent:
    """意图分类测试。"""

    def test_classifies_implement(self, router):
        """中文"实现"关键词触发 implement。"""
        decision = router.route("帮我实现一个登录功能")
        assert decision.route_name == "implement"

    def test_classifies_research(self, router):
        """中文"调研"关键词触发 research。"""
        decision = router.route("帮我调研一下最新的前端框架")
        assert decision.route_name == "research"

    def test_classifies_discuss(self, router):
        """中文"讨论"关键词触发 discuss。"""
        decision = router.route("我想讨论一下微服务架构的利弊")
        assert decision.route_name == "discuss"

    def test_classifies_simple_greeting(self, router):
        """简短问候分类为 simple，路径为 direct。"""
        decision = router.route("你好")
        assert decision.route_name == "simple"
        assert decision.path == "direct"

    def test_classifies_short_message(self, router):
        """极短消息分类为 simple。"""
        decision = router.route("好的")
        assert decision.route_name == "simple"


class TestRouteDecision:
    """路由决策测试。"""

    def test_implement_returns_experts(self, router):
        """implement 意图返回关联的专家列表。"""
        decision = router.route("帮我设计后端 API")
        if decision.path != "direct":
            assert len(decision.experts) > 0
            assert decision.mode in ("A", "B", "D")

    def test_simple_no_experts(self, router):
        """simple 意图不匹配专家。"""
        decision = router.route("谢谢")
        assert len(decision.experts) == 0
        assert decision.mode == ""

    def test_confidence_in_range(self, router):
        """置信度在 0-1 范围内。"""
        decision = router.route("实现一个复杂系统")
        assert 0 <= decision.confidence <= 1.0


class TestPromptSection:
    """认知引导段测试。"""

    def test_format_prompt_section(self, router):
        """引导段包含认知循环的关键要素。"""
        section = router.format_prompt_section()
        # 应包含三层认知核心理念
        assert "内吸" in section
        assert "外求" in section
        assert "三省吾身" in section
        assert "荣辱观" in section
        assert "思维方式" in section
        assert len(section) > 100
