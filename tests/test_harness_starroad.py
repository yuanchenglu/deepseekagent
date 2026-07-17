"""
测试 StarRoadCognition (三层认知引擎)
"""
import pytest
from deepagent_harness.starroad_cognition import StarRoadCognition, MEMORY_TIERS


class TestStarRoadCognition:
    """三层认知引擎测试"""

    def setup_method(self):
        self.cognition = StarRoadCognition()

    def test_l1_principles_not_empty(self):
        """测试L1荣辱观原则不为空"""
        l1 = self.cognition.get_l1_prompt_section()
        assert "核心价值观" in l1
        assert "安全优先" in l1
        assert "诚实可信" in l1
        assert len(l1) > 100

    def test_l2_methods_by_intent(self):
        """测试L2方法论按意图类型返回"""
        for intent_type in ["refactor", "new", "architecture", "research",
                            "simple", "medium", "collaboration", "spec_driven"]:
            l2 = self.cognition.get_l2_prompt_section(intent_type)
            assert len(l2) > 0
            assert "方法论" in l2

    def test_l2_unknown_intent_returns_empty(self):
        """测试未知意图返回空字符串"""
        l2 = self.cognition.get_l2_prompt_section("unknown_type_xyz")
        assert l2 == ""

    def test_l3_review_prompt(self):
        """测试L3反省清单生成"""
        l3 = self.cognition.get_l3_review_prompt()
        assert "自省检查清单" in l3
        assert "理解" in l3 or "需求" in l3
        assert len(l3) > 200

    def test_l3_review_with_context(self):
        """测试带上下文的L3反省清单"""
        context = {
            "goal": "完成用户登录功能",
            "completed_steps": ["数据库设计", "API实现"],
            "remaining_steps": ["测试", "文档"],
        }
        l3 = self.cognition.get_l3_review_prompt(context)
        assert "用户登录" in l3
        assert "数据库设计" in l3

    def test_memory_tiers_structure(self):
        """测试记忆分层结构正确"""
        assert "global_constraint" in MEMORY_TIERS
        assert MEMORY_TIERS["global_constraint"]["lambda"] == 1.0
        assert MEMORY_TIERS["global_constraint"]["always_inject"] is True
        assert "user_preference" in MEMORY_TIERS
        assert "episodic_memory" in MEMORY_TIERS
        assert MEMORY_TIERS["episodic_memory"]["archive_only"] is True
