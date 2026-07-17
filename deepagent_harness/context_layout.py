"""
Context Layout 管理器
======================

【文件职责】
根据 DeepSeek V4 的 Hybrid Attention 物理特性（sliding_window=128），
管理消息在上下文中的布局。核心原则：
- 当前任务的关键信息（当前目标、当前步骤、硬约束提醒）必须在最近 128 token 内
- 历史信息通过压缩路径（indexed compressed KV）检索，不需要在近端
- 禁止 history dump（把所有历史拼接到上下文）

【物理依据】
DeepSeek V4 使用 Hybrid Attention = CSA（Compressed Sparse Attention）+ HCA：
- sliding_window=128：近端 128 token 做全注意力
- Indexer（Pro topk=1024, Flash topk=512）：从压缩 KV 中选择 top-k 位置
- 因此：近端 128 token 是"强注意力区"，关键信息必须放这里
- 历史信息必须有清晰的 anchor（便于 Indexer 检索），不能无结构堆放

【布局五区】
论文 C-002 定义的五区布局：
1. stable_prefix:    冻结的 system prompt（全注意力通过 prefix cache）
2. task_anchor:      任务目标/约束摘要（位置稳定，便于 Indexer 检索）
3. active_working:   当前轮次消息（sliding window 内）
4. compressed_history: 旧消息（通过压缩路径，Indexer 检索）
5. turn_tail:        L2 方法论、mid-session 变更（注入当前用户消息头部）

参考文献：1-4 长上下文机制（Hybrid Attention and Long Context）
"""

import re
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["ContextLayoutManager"]


class ContextLayoutManager:
    """
    Context Layout 管理器

    【类职责】
    - 确保关键信息（当前目标/步骤/约束）在 sliding window 近端
    - 生成任务锚点摘要（task anchor），定期注入到消息尾部
    - 检测历史消息中的冗余内容（重复的工具结果、过时信息）
    - 提供布局诊断信息（各区 token 估算）

    【属性】
        sliding_window: V4 sliding window 大小（token 数，默认 128）
        anchor_tokens:   task anchor 的估算 token 预算（默认 ~100）
        _current_goal:   当前任务目标（从首条用户消息提取）
        _current_constraints: 当前硬约束摘要（简短文本）
        _step_marker:    当前步骤编号/描述
    """

    def __init__(self, sliding_window: int = 128, anchor_tokens: int = 100):
        """
        初始化 Context Layout 管理器。

        入参:
            sliding_window: V4 的 sliding_window 参数（Pro/Flash 均为 128）
            anchor_tokens:  task anchor 区域的 token 预算（字符数约 ×4）
        """
        self.sliding_window = sliding_window
        self.anchor_tokens = anchor_tokens
        self._current_goal: str = ""
        self._current_constraints: str = ""
        self._step_marker: str = ""
        self._active_files: List[str] = []

    def set_task_context(
        self,
        goal: str,
        constraints: Optional[List[str]] = None,
        active_files: Optional[List[str]] = None,
    ):
        """
        设置当前任务上下文（在 pre-turn 阶段调用）。

        入参:
            goal:        当前任务目标（简短描述，< 100 字符）
            constraints: 硬约束列表（用于生成摘要）
            active_files: 当前活跃的文件列表
        """
        self._current_goal = goal[:200] if goal else ""
        if constraints:
            # 只取前 3 条约束生成简短摘要，避免 anchor 过长
            short_constraints = []
            for c in constraints[:3]:
                text = c if isinstance(c, str) else c.text if hasattr(c, 'text') else str(c)
                short_constraints.append(text[:60])
            self._current_constraints = "; ".join(short_constraints)
        else:
            self._current_constraints = ""
        self._active_files = (active_files or [])[:5]

    def set_step(self, step: str):
        """
        标记当前步骤（在每轮工具调用后更新）。

        入参:
            step: 当前步骤描述（如 "3/5 实现核心逻辑"）
        """
        self._step_marker = step[:80] if step else ""

    def get_task_anchor(self) -> str:
        """
        生成 Task Anchor 文本（注入到消息尾部，sliding window 内）。

        Task Anchor 是当前任务状态的极短摘要（< 100 tokens），
        放在最近的 user/tool 消息附近，确保在 sliding window 128 token
        范围内始终可见，相当于给模型的"便签"。

        返回:
            格式化的 Task Anchor 文本（无 anchor 信息时返回空字符串）
        """
        parts = []

        if self._current_goal:
            parts.append(f"[当前目标] {self._current_goal}")

        if self._step_marker:
            parts.append(f"[当前步骤] {self._step_marker}")

        if self._current_constraints:
            parts.append(f"[硬约束提醒] {self._current_constraints}")

        if self._active_files:
            files_str = ", ".join(self._active_files[:5])
            parts.append(f"[活跃文件] {files_str}")

        if not parts:
            return ""

        return "\n".join(parts)

    def inject_anchor_to_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        将 Task Anchor 注入到最后一条用户消息的末尾。

        为什么注入到最后一条用户消息而非独立消息？
        因为独立消息会增加一轮对话，且 sliding_window=128 只关注最近位置。
        把 anchor 追加到最后一条 user message 的 content 尾部，
        确保它在近端窗口内。

        入参:
            messages: 消息列表（不修改原始列表，返回副本）

        返回:
            添加了 anchor 的消息列表副本
        """
        anchor = self.get_task_anchor()
        if not anchor:
            return messages

        # 深拷贝（不修改原始列表）
        import copy
        result = copy.deepcopy(messages)

        # 找到最后一条用户消息
        for i in range(len(result) - 1, -1, -1):
            msg = result[i]
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    # 避免重复注入：检查内容末尾是否已有anchor标记
                    # 只检查最近500字符即可，anchor总是加在末尾
                    check_region = content[-500:] if len(content) > 500 else content
                    if "[当前目标]" not in check_region:
                        msg["content"] = content + "\n\n---\n" + anchor
                break

        return result

    def estimate_zone_tokens(self, messages: List[Dict[str, Any]], system_prompt_len: int = 0) -> Dict[str, int]:
        """
        估算五区 token 分布（粗略估算，用于 diagnostics）。

        入参:
            messages:          当前消息列表
            system_prompt_len: system prompt 字符长度

        返回:
            各区 token 估算字典
        """
        # 粗略估算：1 token ≈ 4 字符（中文约 2 字符/token，但保守用 4）
        def est(chars):
            """将字符数粗略估算为token数（1 token ≈ 4字符）。"""
            return max(1, chars // 4)

        # stable_prefix: system prompt 长度
        stable = est(system_prompt_len)

        # 计算最近消息长度（active working 区）
        recent_chars = 0
        for msg in reversed(messages[-6:]):  # 最近 6 条消息
            content = msg.get("content", "")
            if isinstance(content, str):
                recent_chars += len(content)
        active = est(recent_chars)

        # 历史消息总长度
        history_chars = 0
        for msg in messages[:-6]:
            content = msg.get("content", "")
            if isinstance(content, str):
                history_chars += len(content)
        compressed = est(history_chars)

        # task anchor + turn tail 估算
        anchor = est(len(self.get_task_anchor()))
        turn_tail = 0  # PrefixManager 的 turn tail 长度在外部统计

        return {
            "stable_prefix": stable,
            "task_anchor": anchor,
            "active_working": active,
            "compressed_history": compressed,
            "turn_tail": turn_tail,
            "total_estimate": stable + anchor + active + compressed,
            "sliding_window": self.sliding_window,
        }

    def should_warn_proximity(self, recent_assistant_content: str) -> Optional[str]:
        """
        检测关键信息是否可能被挤出 sliding window。

        如果最近的 assistant 消息很长（> 200 字符 ≈ 50 tokens），
        加上 tool 结果可能填满 128 token 窗口，
        此时应该在下一轮注入更明显的 anchor 提醒。

        入参:
            recent_assistant_content: 最近 assistant 消息的内容

        返回:
            警告文本（需要额外注入时）或 None
        """
        if not recent_assistant_content:
            return None
        approx_tokens = len(recent_assistant_content) // 4
        if approx_tokens > self.sliding_window * 0.7:
            return (
                f"[提醒] 上一回合回复较长（约{approx_tokens} tokens），"
                f"请记住当前目标：{self._current_goal[:80]}"
            )
        return None
