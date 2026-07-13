"""
测试 ReasoningManager (Reasoning Content 管理器)
"""
import pytest
from deepagent_harness.reasoning_manager import ReasoningManager


class TestReasoningManagerInit:
    """初始化测试"""

    def test_default_provider(self):
        """测试默认provider是deepseek"""
        rm = ReasoningManager()
        assert rm.provider == "deepseek"

    def test_custom_provider(self):
        """测试自定义provider"""
        rm = ReasoningManager(provider="anthropic")
        assert rm.provider == "anthropic"
        # Anthropic不剥离reasoning
        assert rm.policy["strip_non_tool_reasoning"] is False

    def test_unknown_provider_fallback(self):
        """测试未知provider回退到deepseek策略"""
        rm = ReasoningManager(provider="unknown_provider")
        assert rm.policy["strip_non_tool_reasoning"] is True


class TestMessageFiltering:
    """消息过滤测试"""

    def setup_method(self):
        self.rm = ReasoningManager(provider="deepseek")

    def test_filter_preserves_non_assistant_messages(self):
        """测试非assistant消息不受影响"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        filtered = self.rm.filter_messages_for_api(messages)
        assert len(filtered) == 2
        assert filtered[0]["role"] == "system"
        assert filtered[1]["role"] == "user"

    def test_strip_reasoning_from_non_tool_assistant(self):
        """测试非tool轮次剥离reasoning"""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!", "reasoning": "Let me think...用户说Hi，我应该回复Hello"},
        ]
        filtered = self.rm.filter_messages_for_api(messages, is_tool_loop=False)
        # assistant消息的reasoning应该被剥离
        assert "reasoning" not in filtered[1] or filtered[1].get("reasoning") is None

    def test_keep_reasoning_in_tool_loop(self):
        """测试tool轮次保留reasoning（DeepSeek协议要求）"""
        messages = [
            {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "function": {"name": "test"}}],
             "reasoning": "I need to call a tool"},
        ]
        filtered = self.rm.filter_messages_for_api(messages, is_tool_loop=True)
        # tool call消息应保留reasoning
        assert "reasoning" in filtered[0] or "reasoning_content" in filtered[0]

    def test_keep_reasoning_for_tool_calls(self):
        """测试包含tool_calls的assistant消息保留reasoning"""
        messages = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}],
             "reasoning": "I need a tool"},
        ]
        filtered = self.rm.filter_messages_for_api(messages, is_tool_loop=False)
        # 即使不在tool_loop，消息本身包含tool_calls时也应保留reasoning
        assert "reasoning" in filtered[0]

    def test_filter_does_not_modify_original(self):
        """测试过滤不修改原始消息列表"""
        messages = [
            {"role": "assistant", "content": "Hi", "reasoning": "thinking..."},
        ]
        original_reasoning = messages[0]["reasoning"]
        _ = self.rm.filter_messages_for_api(messages)
        assert messages[0]["reasoning"] == original_reasoning

    def test_reasoning_archived_locally(self):
        """测试reasoning被本地归档"""
        messages = [
            {"role": "assistant", "content": "Hi", "reasoning": "thinking..."},
        ]
        _ = self.rm.filter_messages_for_api(messages)
        archived = self.rm.get_archived_reasoning()
        assert len(archived) >= 1
        assert "thinking..." in archived[0]["content"]


class TestStats:
    """统计信息测试"""

    def test_summary_contains_required_fields(self):
        """测试summary包含必要字段"""
        rm = ReasoningManager()
        summary = rm.get_summary()
        assert "provider" in summary
        assert "total_chars_stripped" in summary
        assert "estimated_tokens_saved" in summary
        assert "total_reasoning_archived" in summary

    def test_reset_stats(self):
        """测试重置统计"""
        rm = ReasoningManager()
        messages = [
            {"role": "assistant", "content": "Hi", "reasoning": "x" * 1000},
        ]
        _ = rm.filter_messages_for_api(messages)
        assert rm.total_reasoning_chars_stripped > 0
        rm.reset_stats()
        assert rm.total_reasoning_chars_stripped == 0
