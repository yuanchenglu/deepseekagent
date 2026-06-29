# === DeepAgent: StarRoad Cognition ===
# 三层认知评估器（StarRoad Cognition Layer 1-3）
# 在每轮对话的 text response 生成后触发，输出三层评估结果。
# 不 block 主循环——只追加调整建议和记录。

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

from hermes_constants import get_hermes_home  # noqa: F401 — 用于路径解析，保持向后兼容

logger = logging.getLogger(__name__)


@dataclass
class HonorResult:
    """Layer 1 荣辱观检查结果。

    检查三件事：
    - 是否隐瞒了不确定性（该说"不确定"时没说）
    - 是否做了未经工具验证的论断（拍脑袋说结论）
    - 是否隐瞒了工具失败（工具报错了但假装没事）
    """

    hid_uncertainty: bool = False
    """模型对明显有盲区的问题没有表达不确定性。"""

    made_unverified_claim: bool = False
    """模型做出了事实性论断，但没有通过任何工具验证。"""

    hid_tool_failure: bool = False
    """工具调用返回了错误/失败，但模型在 response 中没有如实汇报。"""

    @property
    def passed(self) -> bool:
        """整体是否通过：三项违规全为 False 才算通过。"""
        return not (self.hid_uncertainty or self.made_unverified_claim or self.hid_tool_failure)


@dataclass
class ThinkingResult:
    """Layer 2 思维方式检查结果。

    检查三件事：
    - 是否跳过了必要的执行步骤
    - 是否在工具调用前声明了假设（假设先行）
    - 是否主动识别了知识盲区
    """

    skipped_steps: list[str] = field(default_factory=list)
    """跳过的步骤描述列表，例如 ['多步操作未说明执行顺序']"""

    no_hypothesis_first: list[str] = field(default_factory=list)
    """没有假设先行的操作描述，例如 ['工具调用前未声明假设']"""

    blindspots: list[str] = field(default_factory=list)
    """模型主动识别的盲区列表。"""

    @property
    def passed(self) -> bool:
        """整体是否通过：没有跳过步骤且没有盲区才算通过。"""
        return len(self.skipped_steps) == 0 and len(self.blindspots) == 0


@dataclass
class EvalResult:
    """完整的三层评估结果。

    由 CognitiveGate.evaluate() 返回，包含三层评估的汇总信息：
    - 是否需要中断用户询问
    - 发现的盲区列表
    - 目标调整建议
    """

    plan_id: str = ""
    """关联的 plan_id，用于追踪评估和计划的对应关系。"""

    honor: HonorResult = field(default_factory=HonorResult)
    """Layer 1 荣辱观检查结果。"""

    thinking: ThinkingResult = field(default_factory=ThinkingResult)
    """Layer 2 思维方式检查结果。"""

    should_interrupt_user: bool = False
    """是否达到边界需要中断当前流程并询问用户。"""

    gaps_found: list[str] = field(default_factory=list)
    """新发现的盲区/改进项列表。"""

    goal_adjustment: str | None = None
    """如需调整目标，这里给出建议的新目标描述。None 表示无需调整。"""

    adjustments_note: str = ""
    """人类可读的评估结论摘要。"""


class CognitiveGate:
    """三层认知评估器（StarRoad Cognition 核心模块）。

    每轮对话结束后，对模型的 response 进行三层评估：
    1. Layer 1 (Honor) — 荣辱观：有没有隐瞒不确定性、未验证论断、工具失败
    2. Layer 2 (Thinking) — 思维方式：是否 step-by-step、假设先行、识别盲区
    3. Layer 3 (Reflect) — 三省吾身：回顾 L1+L2 结果，生成改进建议

    用法（在 run_agent.py 中集成）：
        gate = CognitiveGate()
        # 在每轮对话的 text response 后：
        result = gate.evaluate(turn_data)
        if result.should_interrupt_user:
            # 问用户确认
        if result.gaps_found:
            plan_tracker.add_gap(gap)
    """

    def __init__(self, max_history: int = 20):
        """初始化认知评估器。

        Args:
            max_history: 最多保留的评估历史记录数，默认 20。超出时自动丢弃最早的记录。
        """
        if max_history < 1:
            raise ValueError(f"max_history 不能小于 1，收到: {max_history}")
        self._eval_history: list[dict] = []
        self._max_history = max_history

    def evaluate(self, turn_data: dict) -> EvalResult:
        """主入口。接收当前 turn 的数据，输出三层评估结果。

        Args:
            turn_data: 包含当前 turn 的信息，支持的 key：
                - user_message: str — 用户消息（可选）
                - assistant_response: str — 模型的最终文本回复
                - tool_calls: list[dict] — 本次 turn 调用的工具列表
                - tool_results: list[dict] — 对应的工具执行结果
                - plan_id: str — 当前 plan_id（可选）
                - confidence_indicators: list[str] — 模型输出的不确定性指标（可选）

        Returns:
            EvalResult — 三层评估的汇总结果。

        异常处理：
            - 任何内部异常都会被捕获并记录，确保评估器不会导致主循环崩溃。
            - 如果 turn_data 为 None 或缺少关键字段，返回通过的默认结果。
        """
        # 防御性检查：确保 turn_data 合法
        if not isinstance(turn_data, dict):
            logger.warning("CognitiveGate.evaluate() 收到非 dict 参数: %s", type(turn_data).__name__)
            return EvalResult(
                adjustments_note="评估跳过：输入数据格式无效",
            )

        try:
            honor = self._check_honor(turn_data)
        except Exception as e:
            logger.error("CognitiveGate Layer1 (Honor) 检查异常: %s", e, exc_info=True)
            honor = HonorResult()
            return EvalResult(
                plan_id=turn_data.get("plan_id", ""),
                adjustments_note=f"Layer1 评估异常: {e}",
            )

        try:
            thinking = self._check_thinking(turn_data)
        except Exception as e:
            logger.error("CognitiveGate Layer2 (Thinking) 检查异常: %s", e, exc_info=True)
            thinking = ThinkingResult()

        try:
            reflection = self._reflect(honor, thinking, turn_data)
        except Exception as e:
            logger.error("CognitiveGate Layer3 (Reflect) 检查异常: %s", e, exc_info=True)
            reflection = {"gaps": [], "goal_adjustment": None, "note": f"Layer3 评估异常: {e}"}

        result = EvalResult(
            plan_id=turn_data.get("plan_id", ""),
            honor=honor,
            thinking=thinking,
            should_interrupt_user=self._should_ask_user(reflection),
            gaps_found=reflection.get("gaps", []),
            goal_adjustment=reflection.get("goal_adjustment"),
            adjustments_note=reflection.get("note", ""),
        )

        # 记录评估历史
        try:
            self._eval_history.append(asdict(result))
            if len(self._eval_history) > self._max_history:
                self._eval_history.pop(0)
        except Exception as e:
            logger.error("CognitiveGate 历史记录异常: %s", e)

        return result

    def _check_honor(self, turn_data: dict) -> HonorResult:
        """Layer 1 荣辱观检查。

        三个检查点：
        1. 模型是否明确说了"我不确定"、"我需要查一下"之类的话
           → 如果始终没有不确定性表达，但有明显盲区 → hid_uncertainty=True
        2. 模型是否使用工具验证了关键论断
           → 如果做出事实性论断但没有对应的工具调用 → made_unverified_claim=True
        3. 工具调用失败时是否如实报告
           → 遍历 tool_results，如果有 error/failure 但在 response 中未提及 → hid_tool_failure=True

        Args:
            turn_data: 当前 turn 的数据字典。

        Returns:
            HonorResult — 荣辱观检查结果。
        """
        result = HonorResult()
        response = turn_data.get("assistant_response", "") or ""
        tool_calls = turn_data.get("tool_calls", []) or []
        tool_results = turn_data.get("tool_results", []) or []
        confidence_indicators = turn_data.get("confidence_indicators", []) or []

        # 检查 1：是否有不确定性表达
        # 如果 response 中包含"不确定""可能""let me check"等关键词，说明模型如实表达了不确定性
        has_uncertainty_expr = any(
            kw in response.lower()
            for kw in [
                "不确定", "不太确定", "可能", "probably", "might", "i'm not sure",
                "我需要查", "let me check", "先查一下", "让我查",
            ]
        )
        if not has_uncertainty_expr and confidence_indicators:
            # 模型有盲区指标但 response 中没有不确定性表达 → 隐瞒了不确定性
            result.hid_uncertainty = True

        # 检查 2：是否有未经工具验证的论断
        # 简单启发式：如果 response 中包含事实性断言关键词但没有调用任何工具
        has_factual_assertion = any(
            kw in response.lower()
            for kw in ["是", "不是", "应该", "必须", "always", "never", "all", "every"]
        )
        if has_factual_assertion and not tool_calls:
            result.made_unverified_claim = True

        # 检查 3：工具失败是否如实汇报
        for tr in tool_results:
            content = str(tr.get("content", ""))
            if "error" in content.lower() or "fail" in content.lower() or "timeout" in content.lower():
                # 工具确实失败了，检查 response 中是否提到了失败
                if "失败" not in response and "error" not in response.lower() and "没有成功" not in response:
                    result.hid_tool_failure = True
                    break

        return result

    def _check_thinking(self, turn_data: dict) -> ThinkingResult:
        """Layer 2 思维方式检查。

        三个检查点：
        1. 是否 step by step（多个工具调用时是否说明了执行顺序）
        2. 是否有假设先行（工具调用前有假设说明）
        3. 是否有主动识别的盲区

        Args:
            turn_data: 当前 turn 的数据字典。

        Returns:
            ThinkingResult — 思维方式检查结果。
        """
        result = ThinkingResult()
        response = turn_data.get("assistant_response", "") or ""
        tool_calls = turn_data.get("tool_calls", []) or []

        # 检查 1：是否有跳过步骤
        # 如果工具调用超过 3 个但 response 中没有"step""先"等步骤说明词
        if len(tool_calls) > 3 and "step" not in response.lower() and "先" not in response:
            result.skipped_steps.append("多步操作未说明执行顺序")

        # 检查 2：是否在工具调用前声明了假设
        if tool_calls and not any(
            kw in response.lower()
            for kw in ["假设", "我认为", "hypothesis", "i think", "应该是因为", "按理说"]
        ):
            result.no_hypothesis_first.append("工具调用前未声明假设")

        # 检查 3：是否有主动识别的盲区
        for kw in ["不确定", "不清楚", "盲区", "需要查", "盲点", "不懂", "unknown", "need to investigate"]:
            if kw in response.lower():
                result.blindspots.append(f"主动识别盲区: {kw}")

        return result

    def _reflect(self, honor: HonorResult, thinking: ThinkingResult, turn_data: dict) -> dict:
        """Layer 3 三省吾身。

        回头检查 L1（荣辱观）+ L2（思维方式）的结果，综合评估后生成：
        - gaps: 需要改进的盲区列表
        - goal_adjustment: 目标调整建议（如果有）
        - note: 人类可读的评估结论

        Args:
            honor: Layer 1 的检查结果。
            thinking: Layer 2 的检查结果。
            turn_data: 原始 turn 数据，用于更多上下文分析。

        Returns:
            dict — 包含 gaps、goal_adjustment、note 三个 key 的字典。
        """
        # 从 thinking 结果中先收集盲区
        gaps = list(thinking.blindspots)
        goal_adjustment = None
        note_parts = []

        # 汇总 Layer 1 的问题
        if not honor.passed:
            if honor.hid_uncertainty:
                gaps.append("Layer1违规：有不确定性但未明确说明")
                note_parts.append("有不确定性应明确说明")
            if honor.made_unverified_claim:
                gaps.append("Layer1违规：有未经工具验证的论断")
                note_parts.append("事实性论断需用工具验证")
            if honor.hid_tool_failure:
                gaps.append("Layer1违规：工具失败未如实报告")
                note_parts.append("工具失败必须如实报告")

        # 汇总 Layer 2 的问题
        if not thinking.passed:
            note_parts.append("思维方式可优化：使用Step-by-Step+假设先行")

        return {
            "gaps": gaps,
            "goal_adjustment": goal_adjustment,
            "note": "; ".join(note_parts) if note_parts else "评估通过",
        }

    def _should_ask_user(self, reflection: dict) -> bool:
        """判断不确定性是否超过阈值，需要中断当前流程并询问用户。

        当前策略：
        - 如果有 2 个以上盲区（含 Layer 1 和 Layer 2 的违规），则需要中断。
        - 这个阈值基于"两个独立指标同时出问题"的经验值。

        Args:
            reflection: _reflect() 返回的字典，包含 gaps 列表。

        Returns:
            bool — True 表示需要中断并询问用户。
        """
        if not isinstance(reflection, dict):
            logger.warning("_should_ask_user 收到非 dict 参数: %s", type(reflection).__name__)
            return False
        gaps = reflection.get("gaps", [])
        return len(gaps) >= 2

    def get_recent_evaluations(self, n: int = 5) -> list[dict]:
        """返回最近 n 次评估记录。

        Args:
            n: 要返回的记录数量，默认最近 5 次。如果 n 超出历史记录总数，返回全部记录。

        Returns:
            list[dict] — 最近的评估历史记录列表，按时间顺序（最新的在后面）。
        """
        if n < 1:
            return []
        return self._eval_history[-n:]
# === End DeepAgent: StarRoad Cognition ===
