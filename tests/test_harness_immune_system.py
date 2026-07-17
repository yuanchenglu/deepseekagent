"""
测试 ImmuneSystem (Agent 免疫系统)
"""
import pytest
from deepagent_harness.immune_system import ImmuneSystem
from deepagent_harness.hard_constraint import HardConstraint


class TestImmuneSystem:
    """免疫系统测试"""

    def setup_method(self):
        self.immune = ImmuneSystem()

    def test_no_constraints_passes(self):
        """测试无约束时自动通过"""
        result = self.immune.post_execution_review(
            hard_constraints=[],
            task_output="任务完成"
        )
        assert result.passed is True
        assert result.compliance_rate == 1.0
        assert len(result.violations) == 0

    def test_requirement_compliance_pass(self):
        """测试必须类约束遵守时通过"""
        constraints = [
            HardConstraint(
                text="必须使用中文", source="test",
                constraint_type="requirement", keywords=["中文"]
            )
        ]
        result = self.immune.post_execution_review(
            hard_constraints=constraints,
            task_output="这是中文回复，包含中文关键词"
        )
        assert result.passed is True

    def test_stats_tracking(self):
        """测试统计追踪"""
        constraints = [
            HardConstraint(
                text="测试约束", source="test",
                constraint_type="requirement", keywords=["不存在的词xyz"]
            )
        ]
        _ = self.immune.post_execution_review(
            hard_constraints=constraints,
            task_output="some output"
        )
        stats = self.immune.get_stats()
        assert stats["total_checks"] == 1

    def test_reset(self):
        """测试重置功能"""
        self.immune.total_checks = 10
        self.immune.total_violations = 5
        self.immune.reset()
        assert self.immune.total_checks == 0
        assert self.immune.total_violations == 0
