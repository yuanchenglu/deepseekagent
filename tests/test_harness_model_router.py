"""
测试 ModelRouter (Flash/Pro 智能路由器)
"""
import pytest
from deepagent_harness.model_router import ModelRouter, ModelTier, RouteDecision


class TestModelRouterInit:
    """路由器初始化测试"""

    def test_default_config(self):
        """测试默认配置"""
        router = ModelRouter()
        assert router.flash_model == "deepseek-v4-flash"
        assert router.pro_model == "deepseek-v4-pro"
        assert router.flash_first is True
        assert router.enabled is True

    def test_custom_config(self):
        """测试自定义配置"""
        router = ModelRouter(config={
            "flash_model": "custom-flash",
            "pro_model": "custom-pro",
            "flash_first": False,
            "enabled": True,
        })
        assert router.flash_model == "custom-flash"
        assert router.pro_model == "custom-pro"
        assert router.flash_first is False

    def test_disabled_router(self):
        """测试禁用路由器"""
        router = ModelRouter(config={"enabled": False})
        decision = router.route(context={}, instruction="test")
        assert decision.tier == ModelTier.FLASH_THINK


class TestRoutingDecisions:
    """路由决策测试"""

    def setup_method(self):
        self.router = ModelRouter()

    def test_default_routes_to_flash_think(self):
        """测试默认情况路由到Flash Think"""
        decision = self.router.route(
            context={"tool_calls_so_far": 1},
            instruction="帮我写一个Python函数来处理用户登录认证逻辑"
        )
        assert decision.tier == ModelTier.FLASH_THINK
        assert decision.is_upgrade is False
        assert "Flash" in decision.reason

    def test_simple_task_routes_to_flash_non_think(self):
        """测试简单任务路由到Flash Non-Think"""
        decision = self.router.route(
            context={"tool_calls_so_far": 0, "active_files": 0},
            instruction="翻译这句话成英文"
        )
        assert decision.tier == ModelTier.FLASH_NON_THINK
        assert decision.reasoning_effort is None

    def test_irreversible_routes_to_pro_max(self):
        """测试不可逆操作路由到Pro Max"""
        decision = self.router.route(
            context={"risk_level": "irreversible"},
            instruction="删除生产数据库"
        )
        assert decision.tier == ModelTier.PRO_MAX
        assert decision.reasoning_effort == "max"
        assert decision.is_upgrade is True

    def test_high_risk_routes_to_pro(self):
        """测试高风险任务路由到Pro Think"""
        decision = self.router.route(
            context={"risk_level": "high"},
            instruction="部署到生产环境"
        )
        assert decision.tier == ModelTier.PRO_THINK
        assert decision.is_upgrade is True

    def test_many_failures_routes_to_pro(self):
        """测试多次失败后升级到Pro"""
        decision = self.router.route(
            context={"failures_so_far": 2},
            instruction="修复这个bug"
        )
        assert decision.tier == ModelTier.PRO_THINK
        assert "失败" in decision.reason or "failures" in decision.reason.lower()

    def test_large_context_routes_to_pro(self):
        """测试大上下文路由到Pro"""
        decision = self.router.route(
            context={"context_tokens": 150000},
            instruction="分析这个大文件"
        )
        assert decision.tier == ModelTier.PRO_THINK

    def test_many_files_routes_to_pro(self):
        """测试多文件操作路由到Pro"""
        decision = self.router.route(
            context={"active_files": 6},
            instruction="重构整个项目"
        )
        assert decision.tier == ModelTier.PRO_THINK

    def test_many_tools_routes_to_pro(self):
        """测试工具调用频繁路由到Pro"""
        decision = self.router.route(
            context={"tool_calls_so_far": 10},
            instruction="继续工作"
        )
        assert decision.tier == ModelTier.PRO_THINK


class TestForceUpgrade:
    """强制升级测试"""

    def setup_method(self):
        self.router = ModelRouter()

    def test_force_upgrade(self):
        """测试强制升级到Pro Think"""
        decision = self.router.force_upgrade("测试升级")
        assert decision.tier == ModelTier.PRO_THINK
        assert decision.is_upgrade is True

    def test_force_pro_max(self):
        """测试强制升级到Pro Max"""
        decision = self.router.force_pro_max("最终审查")
        assert decision.tier == ModelTier.PRO_MAX
        assert decision.reasoning_effort == "max"


class TestRouteHistory:
    """路由历史和统计测试"""

    def setup_method(self):
        self.router = ModelRouter()

    def test_route_logging(self):
        """测试路由决策被记录"""
        self.router.route(
            context={"tool_calls_so_far": 1},
            instruction="这是一个需要思考的常规任务描述"
        )
        self.router.route(context={"risk_level": "high"}, instruction="test2")
        history = self.router.get_route_history()
        assert len(history) == 2
        assert history[0]["tier"] == ModelTier.FLASH_THINK.value
        assert history[1]["tier"] == ModelTier.PRO_THINK.value

    def test_decision_fields(self):
        """测试RouteDecision包含必要字段"""
        decision = self.router.route(context={}, instruction="test")
        assert hasattr(decision, 'tier')
        assert hasattr(decision, 'model_name')
        assert hasattr(decision, 'reasoning_effort')
        assert hasattr(decision, 'reason')
        assert hasattr(decision, 'timestamp')
