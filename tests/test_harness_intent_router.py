"""
测试 IntentRouter (7+1 意图路由器)
"""
import pytest
from deepagent_harness.intent_router import (
    IntentRouter, IntentType, IntentStrategy
)


class TestIntentClassification:
    """意图分类测试"""

    def setup_method(self):
        self.router = IntentRouter()

    def test_refactor_intent(self):
        """测试重构意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "帮我重构这个模块的代码结构"
        )
        assert intent == IntentType.REFACTOR
        assert strategy.interview_depth == "deep"
        assert strategy.model_tier_hint == "pro_think"

    def test_new_intent(self):
        """测试新建意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "从零开始创建一个用户认证模块"
        )
        assert intent == IntentType.NEW
        assert strategy.execution_mode == "plan_first"

    def test_architecture_intent(self):
        """测试架构决策意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "帮我做技术选型和架构设计方案对比"
        )
        assert intent == IntentType.ARCHITECTURE
        assert strategy.review_standard == "max"
        assert strategy.model_tier_hint == "pro_max"

    def test_research_intent(self):
        """测试研究意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "调研一下Python异步框架的优缺点对比"
        )
        assert intent == IntentType.RESEARCH
        assert strategy.interview_depth == "none"

    def test_simple_intent(self):
        """测试简单意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "帮我解释一下什么是闭包"
        )
        assert intent == IntentType.SIMPLE
        assert strategy.review_standard == "none"
        assert strategy.model_tier_hint == "flash_non_think"

    def test_collaboration_intent(self):
        """测试协作意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "我们并行分工完成这个任务，分配给多个agent"
        )
        assert intent == IntentType.COLLABORATION
        assert "delegation" in strategy.toolsets

    def test_spec_driven_intent(self):
        """测试Spec-Driven意图识别"""
        intent, strategy = self.router.classify_and_get_strategy(
            "按照spec文档实现这个功能，严格根据PRD来"
        )
        assert intent == IntentType.SPEC_DRIVEN
        assert strategy.execution_mode == "spec_driven"

    def test_code_default_medium(self):
        """测试code场景默认是medium"""
        intent = self.router.classify("修改一下配置", scene_type="code")
        assert intent == IntentType.MEDIUM


class TestStrategyBinding:
    """策略绑定测试"""

    def setup_method(self):
        self.router = IntentRouter()

    def test_all_intents_have_strategies(self):
        """测试所有意图类型都有策略"""
        for intent_type in IntentType:
            strategy = self.router.get_strategy(intent_type)
            assert strategy is not None
            assert strategy.interview_depth in ("none", "shallow", "standard", "deep", "from_spec")
            assert strategy.execution_mode in ("direct", "plan_first", "spec_driven")

    def test_simple_strategy_no_planning(self):
        """测试simple策略无面谈无计划无审查"""
        strategy = self.router.get_strategy(IntentType.SIMPLE)
        assert strategy.interview_depth == "none"
        assert strategy.plan_granularity == "none"
        assert strategy.review_standard == "none"
        assert strategy.execution_mode == "direct"

    def test_architecture_strategy_okr_cascade(self):
        """测试architecture策略使用OKR级联计划"""
        strategy = self.router.get_strategy(IntentType.ARCHITECTURE)
        assert strategy.plan_granularity == "okr_cascade"
        assert strategy.review_standard == "max"


class TestRouteContext:
    """路由上下文生成测试"""

    def test_route_context_fields(self):
        """测试路由上下文字段"""
        router = IntentRouter()
        intent, strategy = router.classify_and_get_strategy("简单测试")
        ctx = router.get_route_context(intent, strategy)
        assert "intent" in ctx
        assert "risk_level" in ctx
        assert "recommended_model_tier" in ctx
        assert "expected_tool_calls" in ctx
        assert "toolsets" in ctx
