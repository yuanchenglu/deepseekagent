"""
测试 ContextLayoutManager (上下文布局管理器)
"""
import pytest
from deepagent_harness.context_layout import ContextLayoutManager


class TestContextLayout:
    """上下文布局测试"""

    def setup_method(self):
        self.clm = ContextLayoutManager(sliding_window=128)

    def test_init_defaults(self):
        """测试初始化默认值"""
        assert self.clm.sliding_window == 128
        assert self.clm.get_task_anchor() == ""

    def test_set_task_context(self):
        """测试设置任务上下文"""
        self.clm.set_task_context(
            goal="实现登录功能",
            constraints=["必须用中文", "不要删除数据库"],
            active_files=["auth.py", "models.py"]
        )
        anchor = self.clm.get_task_anchor()
        assert "[当前目标]" in anchor
        assert "登录功能" in anchor
        assert "[活跃文件]" in anchor

    def test_set_step(self):
        """测试设置当前步骤"""
        self.clm.set_task_context(goal="测试目标")
        self.clm.set_step("3/5 实现核心逻辑")
        anchor = self.clm.get_task_anchor()
        assert "[当前步骤]" in anchor
        assert "3/5" in anchor

    def test_inject_anchor_to_messages(self):
        """测试注入anchor到消息"""
        self.clm.set_task_context(goal="测试目标")
        messages = [
            {"role": "user", "content": "帮我写代码"}
        ]
        result = self.clm.inject_anchor_to_messages(messages)
        assert "[当前目标]" in result[-1]["content"]
        assert "帮我写代码" in result[-1]["content"]

    def test_no_duplicate_injection(self):
        """测试不重复注入anchor"""
        self.clm.set_task_context(goal="测试目标")
        messages = [{"role": "user", "content": "帮我写代码"}]
        # 第一次注入
        messages = self.clm.inject_anchor_to_messages(messages)
        first_content = messages[-1]["content"]
        anchor_count_1 = first_content.count("[当前目标]")
        # 第二次注入（不应重复）
        messages2 = self.clm.inject_anchor_to_messages(messages)
        anchor_count_2 = messages2[-1]["content"].count("[当前目标]")
        assert anchor_count_1 == 1
        assert anchor_count_2 == 1

    def test_estimate_zone_tokens(self):
        """测试token分布估算"""
        messages = [
            {"role": "system", "content": "x" * 400},
            {"role": "user", "content": "Hello" * 50},
        ]
        zones = self.clm.estimate_zone_tokens(messages, system_prompt_len=400)
        assert "stable_prefix" in zones
        assert "active_working" in zones
        assert "compressed_history" in zones
        assert zones["total_estimate"] > 0

    def test_no_anchor_when_empty_context(self):
        """测试空上下文不生成anchor"""
        anchor = self.clm.get_task_anchor()
        assert anchor == ""
        messages = [{"role": "user", "content": "Hi"}]
        result = self.clm.inject_anchor_to_messages(messages)
        assert result == messages  # 无变化
