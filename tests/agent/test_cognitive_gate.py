# === DeepAgent: StarRoad Cognition ===
# CognitiveGate 三层认知评估器测试

"""Tests for CognitiveGate — 三层认知评估器。"""

import pytest
from agent.cognitive_gate import CognitiveGate, HonorResult, ThinkingResult, EvalResult


class TestHonorCheck:
    """Layer 1 荣辱观检查测试。"""

    def test_passes_when_no_issues(self):
        """正常情况：不隐瞒不确定性、有工具验证、如实报告失败。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我不确定这个模块的具体实现，让我查一下源码。",
            "tool_calls": [{"name": "read_file", "arguments": '{"path": "x.py"}'}],
            "tool_results": [{"content": "some content"}],
        }
        result = gate._check_honor(turn_data)
        assert result.passed is True

    def test_detects_hidden_uncertainty(self):
        """有盲区但没说明不确定。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "这个模块的功能是处理数据。",
            "tool_calls": [],
            "tool_results": [],
            "confidence_indicators": ["unfamiliar-module"],
        }
        result = gate._check_honor(turn_data)
        assert result.hid_uncertainty is True

    def test_detects_unverified_claim(self):
        """有事实性论断但没用工具。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "这个函数的复杂度一定是 O(n^2)。",
            "tool_calls": [],
            "tool_results": [],
        }
        result = gate._check_honor(turn_data)
        assert result.made_unverified_claim is True

    def test_detects_hidden_tool_failure(self):
        """工具失败但没汇报。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "让我看看结果。",
            "tool_calls": [{"name": "web_search", "arguments": '{"query": "test"}'}],
            "tool_results": [{"content": '{"error": "timeout"}'}],
        }
        result = gate._check_honor(turn_data)
        assert result.hid_tool_failure is True


class TestThinkingCheck:
    """Layer 2 思维方式检查测试。"""

    def test_passes_when_step_by_step(self):
        """step-by-step 且声明了假设，应该通过。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "第一步先查文档，第二步再实现。",
            "tool_calls": [{"name": "read_file", "arguments": ""}],
        }
        result = gate._check_thinking(turn_data)
        assert result.passed is True

    def test_detects_missing_hypothesis(self):
        """工具调用前没有声明假设，应该被检测到。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我来改这个代码。",
            "tool_calls": [{"name": "edit", "arguments": '{"path": "x.py"}'}],
        }
        result = gate._check_thinking(turn_data)
        assert len(result.no_hypothesis_first) > 0


class TestFullEvaluation:
    """CognitiveGate.evaluate() 完整流程测试。"""

    def test_full_pass(self):
        """全通过场景：假设先行 + 有工具验证 + 无违规。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我认为可能是缓存引起的，先查日志再分析。",
            "tool_calls": [{"name": "read_file", "arguments": '{"path": "x.py"}'}],
            "tool_results": [{"content": "some content"}],
        }
        result = gate.evaluate(turn_data)
        assert isinstance(result, EvalResult)
        assert result.honor.passed is True
        assert result.thinking.passed is True

    def test_detects_multiple_gaps_and_should_ask_user(self):
        """多 gap 场景：隐瞒不确定性 + 未验证论断 → 应该触发 should_interrupt。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我来改这个应该没问题。",
            "tool_calls": [],
            "tool_results": [],
            "confidence_indicators": ["unfamiliar-module"],
        }
        result = gate.evaluate(turn_data)
        assert len(result.gaps_found) >= 2
        assert result.should_interrupt_user is True

    def test_eval_history_tracking(self):
        """历史追踪：多次评估后 get_recent_evaluations 正确返回。"""
        gate = CognitiveGate()
        for i in range(3):
            gate.evaluate({
                "assistant_response": f"response {i}",
                "tool_calls": [],
                "tool_results": [],
            })
        recent = gate.get_recent_evaluations(2)
        assert len(recent) == 2

    def test_plan_id_carried_to_result(self):
        """plan_id 携带：评估结果中 plan_id 与输入一致。"""
        gate = CognitiveGate()
        result = gate.evaluate({
            "assistant_response": "ok",
            "tool_calls": [],
            "tool_results": [],
            "plan_id": "plan-123",
        })
        assert result.plan_id == "plan-123"
