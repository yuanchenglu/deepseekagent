"""
Reasoning Content 管理器
=========================

【文件职责】
管理 DeepSeek V4 模型返回的 reasoning_content（思维链内容）的生命周期。
核心原则：reasoning 是"得到答案的过程"而非"未来答案的上下文"。

【为什么需要这个模块】
DeepSeek V4 等推理模型在响应中返回 reasoning_content，记录模型的思考过程。
默认行为是把这些 reasoning 全量拼回下一轮 API 请求（历史消息全量回传）。
问题：
  1. 非 tool-call 轮次的 reasoning 对后续回答无帮助（模型已经得出了答案）
  2. 50 轮 session 中 reasoning 可累积 ~25K tokens，100% 浪费
  3. DeepSeek API 将 reasoning_content 计入 input token 计费

但有个例外：tool-calling 轮次必须保留 reasoning（DeepSeek API 协议要求，
否则多步工具调用会报 400 错误）。

【Provider 差异】
- DeepSeek：非 tool 轮可安全剥离；tool 轮必须保留
- Anthropic：必须保留 thinking blocks（有签名验证，剥离会报错）
- OpenAI o1/o3：reasoning 在 API 层处理，客户端不需要回传

【与其他模块的协作】
- 在 run_agent.py 构建 api_messages 时被调用（API 请求前最后一层过滤）
- 本地 messages 列表保留完整 reasoning（用于 display/archive/轨迹存储）
- 过滤只作用于 API 请求的副本，不修改内部数据结构

参考文献：I-14 Reasoning Content 剥离；C-005 设计约束
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = ["ReasoningManager"]


class ReasoningManager:
    """
    Reasoning Content 管理器

    【类职责】
    在发送 API 请求前过滤 messages 中的 reasoning 内容，根据 provider 策略
    和当前是否在 tool loop 中决定保留还是剥离。同时记录统计信息
    （剥离的字符数、估算节省的 token 数）。

    【属性】
        provider:                          provider 名称（小写）
        policy:                            该 provider 的策略字典
        reasoning_archive:                 归档的 reasoning 列表（本地保留，不影响API）
        total_reasoning_chars_stripped:    累计剥离的字符数
        total_reasoning_chars_sent:        累计发送给 API 的字符数
    """

    # Provider 策略配置表
    # strip_non_tool_reasoning: 非 tool 轮次是否剥离 reasoning
    # keep_tool_reasoning:      tool 轮次是否保留 reasoning
    # reasoning_field:          API 协议中 reasoning 字段名
    # max_reasoning_chars:      保留 reasoning 时的最大字符数（超过截断），None 不截断
    PROVIDER_POLICIES: Dict[str, Dict[str, Any]] = {
        "deepseek": {
            "strip_non_tool_reasoning": True,   # DeepSeek 非tool轮可安全剥离
            "keep_tool_reasoning": True,        # tool 轮必须保留
            "reasoning_field": "reasoning_content",
            "max_reasoning_chars": 8000,        # 超过8000字符截断首尾保留
        },
        "anthropic": {
            "strip_non_tool_reasoning": False,  # Anthropic thinking blocks 有签名，不能剥离
            "keep_tool_reasoning": True,
            "reasoning_field": "thinking",
            "max_reasoning_chars": None,        # 不截断
        },
        "openai": {
            "strip_non_tool_reasoning": True,   # OpenAI 不需要客户端回传
            "keep_tool_reasoning": False,
            "reasoning_field": "reasoning",
            "max_reasoning_chars": 8000,
        },
    }

    def __init__(self, provider: str = "deepseek"):
        """
        初始化 ReasoningManager。

        入参:
            provider: 模型提供商名称（"deepseek"/"anthropic"/"openai" 等），
                      未知 provider 默认使用 deepseek 策略
        """
        self.provider = provider.lower()
        # 未知 provider 使用 deepseek 策略（最安全的默认：非tool轮剥离）
        self.policy = self.PROVIDER_POLICIES.get(
            self.provider, self.PROVIDER_POLICIES["deepseek"]
        )
        self.reasoning_archive: List[Dict[str, Any]] = []
        self.total_reasoning_chars_stripped = 0
        self.total_reasoning_chars_sent = 0

    def filter_messages_for_api(
        self,
        messages: List[Dict[str, Any]],
        is_tool_loop: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        过滤消息列表中的 reasoning 内容（在发送 API 请求前调用）。

        【重要】此方法操作 messages 的副本，不修改原始消息列表。
        原始消息中的 reasoning 保留用于 display/archive/轨迹存储。

        入参:
            messages:      要发送给 API 的消息列表（会被复制，不修改原列表）
            is_tool_loop:  当前是否在 tool-calling 循环中
                           （最近消息包含 tool_calls 或 role=tool 时为 True）

        返回:
            过滤后的消息列表副本，供 API 请求使用

        处理逻辑：
        1. 复制每条消息（不修改原始数据）
        2. 对 assistant 消息：
           - 始终归档 reasoning 到 reasoning_archive（本地保留）
           - 根据策略决定是否移除 reasoning_content 字段
           - 如果保留但超长，截断首尾
        3. 统计剥离/发送的字符数
        """
        filtered = []
        reasoning_field = self.policy["reasoning_field"]

        for msg in messages:
            msg_copy = msg.copy()  # 不修改原始消息
            is_assistant = msg.get("role") == "assistant"
            has_reasoning = bool(msg.get("reasoning"))

            # 始终归档 assistant 消息的 reasoning（本地保留）
            if is_assistant and has_reasoning:
                self.reasoning_archive.append({
                    "turn": len(self.reasoning_archive),
                    "content": msg["reasoning"],
                    "has_tool_calls": bool(msg.get("tool_calls")),
                    "provider": self.provider,
                })

            # 判断是否应该剥离此条消息的 reasoning
            should_strip = self._should_strip_reasoning(
                msg, is_tool_loop, is_assistant, has_reasoning
            )

            if should_strip:
                # 统计剥离量
                reasoning_text = msg.get("reasoning", "") or msg.get(reasoning_field, "")
                self.total_reasoning_chars_stripped += len(str(reasoning_text))
                # 从 API 副本中移除 reasoning 相关字段
                msg_copy.pop(reasoning_field, None)
                msg_copy.pop("reasoning", None)
            elif has_reasoning:
                # 保留 reasoning，但可能截断过长内容
                reasoning_text = msg.get("reasoning", "")
                max_chars = self.policy.get("max_reasoning_chars")
                if max_chars and len(reasoning_text) > max_chars:
                    # 截断策略：保留开头和结尾（通常开头是分析，结尾是结论）
                    half = max_chars // 2
                    truncated = (
                        reasoning_text[:half]
                        + f"\n...[reasoning truncated: {len(reasoning_text)} chars total]...\n"
                        + reasoning_text[-half:]
                    )
                    msg_copy["reasoning"] = truncated
                    if reasoning_field in msg_copy:
                        msg_copy[reasoning_field] = truncated
                    self.total_reasoning_chars_sent += len(truncated)
                else:
                    self.total_reasoning_chars_sent += len(reasoning_text)

                # 确保 reasoning_content 字段名正确（API 协议要求）
                if "reasoning" in msg_copy and reasoning_field != "reasoning":
                    msg_copy[reasoning_field] = msg_copy["reasoning"]

            filtered.append(msg_copy)

        return filtered

    def _should_strip_reasoning(
        self, msg: Dict[str, Any], is_tool_loop: bool,
        is_assistant: bool, has_reasoning: bool,
    ) -> bool:
        """
        判断是否应该剥离此条消息的 reasoning。

        剥离条件（全部满足才剥离）：
        1. 是 assistant 消息且有 reasoning
        2. Provider 策略允许剥离非 tool reasoning
        3. 消息本身没有 tool_calls
        4. 不在 tool loop 中（或策略不要求保留 tool reasoning）
        """
        if not has_reasoning or not is_assistant:
            return False

        if not self.policy.get("strip_non_tool_reasoning", False):
            return False

        # 如果消息本身包含 tool_calls，必须保留（协议要求）
        if msg.get("tool_calls"):
            return False

        # 在 tool loop 中，策略要求保留
        if is_tool_loop and self.policy.get("keep_tool_reasoning", False):
            return False

        return True

    def get_summary(self) -> Dict[str, Any]:
        """
        获取 reasoning 管理统计信息（用于 diagnostics/evidence）。

        返回字段:
            provider:                    使用的 provider 策略
            total_reasoning_archived:    归档的 reasoning 条数
            total_chars_stripped:        累计从 API 请求中剥离的字符数
            total_chars_sent:            累计发送给 API 的字符数
            estimated_tokens_saved:      估算节省的 token 数（按 chars/4 粗略估算）
            strip_policy:                当前是否启用剥离
        """
        return {
            "provider": self.provider,
            "total_reasoning_archived": len(self.reasoning_archive),
            "total_chars_stripped": self.total_reasoning_chars_stripped,
            "total_chars_sent": self.total_reasoning_chars_sent,
            "estimated_tokens_saved": self.total_reasoning_chars_stripped // 4,
            "strip_policy": self.policy.get("strip_non_tool_reasoning", False),
        }

    def get_archived_reasoning(self, turn: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取归档的 reasoning 内容。

        入参:
            turn: 指定轮次（None 返回全部）
        """
        if turn is not None:
            return [r for r in self.reasoning_archive if r["turn"] == turn]
        return self.reasoning_archive

    def reset_stats(self):
        """重置统计计数器（不清除归档）。"""
        self.total_reasoning_chars_stripped = 0
        self.total_reasoning_chars_sent = 0
