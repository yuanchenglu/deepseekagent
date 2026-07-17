"""
测试 BidirectionalPrimitives (双向Agent原语)
"""
import pytest
from deepagent_harness.bidirectional_primitives import (
    BidirectionalPrimitives, MetaDirectiveType, get_meta_directive_tools,
    is_meta_directive_tool_name
)
from deepagent_harness import PrefixManager, ModelRouter, StarRoadCognition


class TestBidirectionalPrimitives:
    """双向原语测试"""

    def setup_method(self):
        self.pm = PrefixManager()
        self.pm.freeze("System prompt")
        self.mr = ModelRouter()
        self.sr = StarRoadCognition()
        self.bp = BidirectionalPrimitives(
            prefix_manager=self.pm,
            model_router=self.mr,
            starroad=self.sr,
        )

    def test_meta_tools_count(self):
        """测试4个元指令工具都已定义"""
        tools = get_meta_directive_tools()
        assert len(tools) == 4
        names = [t["function"]["name"] for t in tools]
        assert "need_more_context" in names
        assert "request_specialized_model" in names
        assert "trigger_self_review" in names
        assert "propose_skill" in names

    def test_is_meta_directive_tool_name(self):
        """测试工具名识别"""
        assert is_meta_directive_tool_name("need_more_context") is True
        assert is_meta_directive_tool_name("request_specialized_model") is True
        assert is_meta_directive_tool_name("read_file") is False
        assert is_meta_directive_tool_name("terminal") is False

    def test_handle_need_more_context(self):
        """测试need_more_context处理"""
        result = self.bp.handle_tool_call(
            "need_more_context",
            {"reason": "需要了解项目结构", "context_type": "project_structure"}
        )
        assert result is not None
        assert result.success is True
        assert result.directive == MetaDirectiveType.NEED_MORE_CONTEXT
        # 应该注入到prefix_manager
        assert self.pm.has_pending_injections is True

    def test_handle_request_model_upgrade(self):
        """测试request_specialized_model处理"""
        result = self.bp.handle_tool_call(
            "request_specialized_model",
            {"reason": "任务太复杂", "requested_tier": "pro_think"}
        )
        assert result is not None
        assert result.success is True
        assert result.data["new_tier"] == "pro_think"

    def test_handle_request_pro_max(self):
        """测试请求Pro Max"""
        result = self.bp.handle_tool_call(
            "request_specialized_model",
            {"reason": "最终审查", "requested_tier": "pro_max"}
        )
        assert result.success is True
        assert result.data["new_tier"] == "pro_max"
        assert result.data["reasoning_effort"] == "max"

    def test_handle_trigger_self_review(self):
        """测试trigger_self_review处理"""
        result = self.bp.handle_tool_call(
            "trigger_self_review",
            {"reason": "核心功能完成", "current_stage": "核心开发完成"}
        )
        assert result is not None
        assert result.success is True
        assert "审查" in result.message or "检查" in result.message or "清单" in result.message

    def test_handle_propose_skill(self):
        """测试propose_skill处理"""
        result = self.bp.handle_tool_call(
            "propose_skill",
            {
                "skill_name": "test-pattern",
                "description": "测试模式",
                "pattern": "1.先写测试 2.再写代码",
                "trigger_conditions": "写新功能时"
            }
        )
        assert result is not None
        assert result.success is True
        assert "test-pattern" in result.data["skill_name"]

    def test_non_meta_tool_returns_none(self):
        """测试非元指令工具返回None"""
        result = self.bp.handle_tool_call("read_file", {"path": "/test"}, None)
        assert result is None

    def test_stats_tracking(self):
        """测试统计追踪"""
        self.bp.handle_tool_call("need_more_context",
                                {"reason": "test", "context_type": "other"})
        self.bp.handle_tool_call("trigger_self_review",
                                {"reason": "test", "current_stage": "x"})
        stats = self.bp.get_stats()
        assert stats["total_directives"] == 2
        assert stats["success_rate"] == 1.0
        assert "need_more_context" in stats["by_type"]
        assert "trigger_self_review" in stats["by_type"]
