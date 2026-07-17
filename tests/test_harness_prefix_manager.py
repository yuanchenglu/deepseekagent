"""
测试 PrefixManager (Byte-Stable Prefix 管理器)
"""
import pytest
from deepagent_harness.prefix_manager import PrefixManager


class TestPrefixManagerBasic:
    """PrefixManager 基础功能测试"""

    def test_init_state(self):
        """测试初始化状态"""
        pm = PrefixManager()
        assert pm.is_frozen is False
        assert pm.frozen_prefix is None
        assert pm.fingerprint == "unfrozen"
        assert pm.has_pending_injections is False

    def test_freeze_returns_fingerprint(self):
        """测试freeze返回SHA-256指纹（前16字符）"""
        pm = PrefixManager()
        system_prompt = "You are a helpful assistant."
        fp = pm.freeze(system_prompt)
        assert isinstance(fp, str)
        assert len(fp) == 16  # 前16字符
        assert pm.is_frozen is True
        assert pm.frozen_prefix == system_prompt

    def test_freeze_fingerprint_consistent(self):
        """测试相同输入产生相同指纹"""
        pm1 = PrefixManager()
        pm2 = PrefixManager()
        prompt = "Test system prompt"
        fp1 = pm1.freeze(prompt)
        fp2 = pm2.freeze(prompt)
        assert fp1 == fp2

    def test_freeze_fingerprint_different(self):
        """测试不同输入产生不同指纹"""
        pm1 = PrefixManager()
        pm2 = PrefixManager()
        fp1 = pm1.freeze("Prompt A")
        fp2 = pm2.freeze("Prompt B")
        assert fp1 != fp2


class TestMidSessionInjection:
    """Mid-session 变更注入测试"""

    def test_inject_and_consume(self):
        """测试注入变更后消费"""
        pm = PrefixManager()
        pm.freeze("System prompt")

        # 注入一条变更
        pm.inject_mid_session_change("memory_update", "用户偏好更新：喜欢中文")
        assert pm.has_pending_injections is True

        # 消费
        result = pm.consume_turn_tail()
        assert "[memory_update]" in result
        assert "用户偏好更新" in result
        assert pm.has_pending_injections is False  # 消费后清空

    def test_multiple_injections(self):
        """测试多条变更注入和拼接"""
        pm = PrefixManager()
        pm.freeze("System prompt")

        pm.inject_mid_session_change("memory_update", "记忆1")
        pm.inject_mid_session_change("skill_added", "新技能")
        pm.inject_mid_session_change("bg_job_done", "后台任务完成")

        result = pm.consume_turn_tail()
        assert "[memory_update]" in result
        assert "[skill_added]" in result
        assert "[bg_job_done]" in result
        # 三条变更应该被双换行分隔
        assert result.count("\n\n") >= 2

    def test_consume_empty_when_no_injections(self):
        """测试无注入时消费返回空字符串"""
        pm = PrefixManager()
        pm.freeze("System prompt")
        assert pm.consume_turn_tail() == ""

    def test_consume_clears_queue(self):
        """测试消费后队列清空，不重复注入"""
        pm = PrefixManager()
        pm.freeze("System prompt")
        pm.inject_mid_session_change("test", "内容")
        _ = pm.consume_turn_tail()
        # 第二次消费应该是空
        assert pm.consume_turn_tail() == ""


class TestStatsAndReset:
    """统计信息和重置测试"""

    def test_get_stats_unfrozen(self):
        """测试未冻结状态的统计"""
        pm = PrefixManager()
        stats = pm.get_stats()
        assert stats["frozen"] is False
        assert stats["fingerprint"] == "unfrozen"
        assert stats["prefix_length"] == 0

    def test_get_stats_frozen(self):
        """测试冻结后的统计"""
        pm = PrefixManager()
        prompt = "A" * 100
        pm.freeze(prompt)
        pm.inject_mid_session_change("test", "test content")

        stats = pm.get_stats()
        assert stats["frozen"] is True
        assert stats["prefix_length"] == 100
        assert stats["pending_injections"] == 1
        assert stats["total_injections_logged"] == 1

    def test_reset(self):
        """测试重置功能"""
        pm = PrefixManager()
        pm.freeze("System prompt")
        pm.inject_mid_session_change("test", "content")
        pm.reset()

        assert pm.is_frozen is False
        assert pm.frozen_prefix is None
        assert pm.has_pending_injections is False
        assert pm.fingerprint == "unfrozen"
