"""
Byte-Stable Prefix 管理器
=========================

【文件职责】
实现 DeepSeek V4 的 Byte-Stable Prefix 架构原则：
System Prompt 在 session 的第一个 turn（turn-0）构建完成后被"冻结"，
之后 session 内任何 mid-session 变更（Memory 更新、Skill 新增、后台任务完成等）
都不修改前缀字节，而是通过"用户消息头部注入"（turn tail injection）的方式传递。

【为什么这样设计】
DeepSeek V4 的 Context Caching 机制要求 full prefix unit 完整匹配才能命中 KV Cache。
如果每轮都修改 System Prompt，缓存命中率会大幅下降，导致：
  1. 输入 token 成本上升（cache miss 价格是 cache hit 的 50-120 倍）
  2. 首 token 延迟增加（需要重新计算前缀的 KV）
  3. 前缀中的硬约束被后续变更"稀释"（注意力权重分散）

【与其他模块的协作】
- 在 run_agent.py 的 AIAgent.__init__ 中被实例化为 self._prefix_manager
- freeze() 在首次 _build_system_prompt() 后调用
- inject_mid_session_change() 被以下位置调用：
  · _invalidate_system_prompt()：压缩后 memory 重新加载
  · _handle_meta_directive()：元指令反馈
- consume_turn_tail() 在每轮构建 api_messages 时被调用，内容注入到当前 user message 头部
- fingerprint 被 post-execution harness diagnostics 读取

【生命周期】
  1. AIAgent.__init__() → 创建 PrefixManager 实例
  2. run_conversation() 首次 turn → _build_system_prompt() → freeze()
  3. session 期间 → inject_mid_session_change() 记录变更
  4. 每轮 API 调用前 → consume_turn_tail() 获取并清空待注入内容
  5. session 结束 / reset() → reset() 清空状态

参考文献：I-13 Byte-Stable Prefix 架构
对应设计约束：C-001（Byte-Stable Prefix 是一级架构约束）
"""

import hashlib
from typing import Optional, List

__all__ = ["PrefixManager"]


class PrefixManager:
    """
    Byte-Stable Prefix 管理器

    【类职责】
    维护 System Prompt 的字节级稳定性。提供：
    - 冻结机制（freeze）：首次构建后锁定前缀内容
    - 指纹追踪（fingerprint）：SHA-256 前缀哈希，用于诊断 prefix drift
    - Mid-session 变更队列：后续变更不修改前缀，排队注入下一 turn 的用户消息
    - 消费机制：每轮注入后清空队列，避免重复注入

    【属性说明】
    _frozen_prefix:      冻结的 System Prompt 字符串（freeze 后永不改变）
    _prefix_fingerprint: 前缀的 SHA-256 指纹前 16 字符（诊断用）
    _pending_injections: 待注入到下一 turn 用户消息头部的文本列表
    _frozen:             布尔标记，前缀是否已冻结
    _injection_log:      历史注入类型记录（调试/诊断用，不存储完整内容）
    """

    def __init__(self):
        """初始化 PrefixManager，初始状态为未冻结。"""
        self._frozen_prefix: Optional[str] = None
        self._prefix_fingerprint: Optional[str] = None
        self._pending_injections: List[str] = []
        self._frozen: bool = False
        self._injection_log: List[str] = []

    def freeze(self, system_prompt: str) -> str:
        """
        冻结 System Prompt，计算并记录指纹。

        【调用时机】仅在 session 第一个 turn 的 _build_system_prompt() 完成后调用一次。
        后续 turn 中即使有 Memory 更新、Skill 变化等，也不会重新调用此方法。

        入参:
            system_prompt: 初次构建完成的完整 System Prompt 字符串

        返回:
            冻结后的 SHA-256 指纹（前16字符），用于诊断 prefix drift

        设计决策：为什么不在 freeze 时做任何内容修改？
            因为前缀的内容由 prompt_builder 和 hard_constraint 模块负责组装，
            PrefixManager 只做"锁定"这一件事，职责单一。
        """
        self._frozen_prefix = system_prompt
        # 计算 SHA-256 哈希，取前 16 字符作为指纹
        # 16 字符 = 64 bits，碰撞概率极低，足以用于诊断日志
        self._prefix_fingerprint = hashlib.sha256(
            system_prompt.encode("utf-8")
        ).hexdigest()[:16]
        self._frozen = True
        return self._prefix_fingerprint

    def inject_mid_session_change(self, change_type: str, content: str):
        """
        记录一项 mid-session 变更，等待在下一 turn 注入用户消息头部。

        【调用时机】session 期间发生了以下事件但不应修改 System Prompt：
        - Memory 写入后（用户偏好更新）
        - 新 Skill 安装后
        - Background job（如 memory flush）完成
        - 元指令（need_more_context 等）的反馈内容
        - 上下文压缩后 memory 从磁盘重新加载

        入参:
            change_type: 变更类型标识，如 "memory_update"/"skill_added"/"bg_job_done"
                         这个标识会出现在注入文本的方括号标记中，方便模型识别来源
            content:     变更内容的自然语言描述，直接拼接到注入文本中

        注意：此方法不做内容长度检查。调用方应控制 content 长度（建议 < 500 字符），
        过长的注入会占用 turn tail 的 token 预算。
        """
        # 格式: "[memory_update]\n新的记忆内容"
        # 方括号标记让模型能快速识别这是元信息而非用户输入
        injection = f"[{change_type}]\n{content}"
        self._pending_injections.append(injection)
        self._injection_log.append(change_type)

    def consume_turn_tail(self) -> str:
        """
        消费并返回所有待注入的变更文本，清空队列。

        【调用时机】在每轮构建 api_messages 时，当前 user message 构建完成后、
        发送 API 请求前调用。返回的文本 prepend 到 user message 的 content 头部。

        返回:
            待注入的文本（多个变更用双换行拼接）。
            如果没有待注入内容，返回空字符串。

        设计决策：为什么是"消费"而非"查看"？
            避免重复注入同一条变更。每轮注入一次后队列清空，
            确保每条变更恰好注入一次，不会在下一轮重复出现浪费 token。
        """
        if not self._pending_injections:
            return ""
        # 用双换行分隔不同类型的注入，保持可读性
        injection = "\n\n".join(self._pending_injections)
        self._pending_injections.clear()
        return injection

    @property
    def is_frozen(self) -> bool:
        """前缀是否已冻结（布尔值，用于条件判断）。"""
        return self._frozen

    @property
    def frozen_prefix(self) -> Optional[str]:
        """获取冻结的 System Prompt 文本（未冻结时返回 None）。"""
        return self._frozen_prefix

    @property
    def fingerprint(self) -> str:
        """
        获取前缀的 SHA-256 指纹（前16字符）。
        未冻结时返回 "unfrozen"。
        此指纹用于 diagnostics/evidence 报告中记录 cache 稳定性。
        """
        return self._prefix_fingerprint or "unfrozen"

    @property
    def has_pending_injections(self) -> bool:
        """是否有等待注入下一 turn 的 mid-session 变更。"""
        return len(self._pending_injections) > 0

    def get_stats(self) -> dict:
        """
        获取管理器统计信息（用于 diagnostics/evidence）。

        返回字段:
            frozen:                  是否已冻结
            fingerprint:             前缀指纹
            prefix_length:           冻结前缀的字符长度
            pending_injections:      当前待注入的变更数量
            total_injections_logged: 历史累计注入次数
        """
        return {
            "frozen": self._frozen,
            "fingerprint": self.fingerprint,
            "prefix_length": len(self._frozen_prefix) if self._frozen_prefix else 0,
            "pending_injections": len(self._pending_injections),
            "total_injections_logged": len(self._injection_log),
        }

    def reset(self):
        """
        重置管理器到初始状态（用于新 session 或强制重建前缀）。

        【重要】正常 session 内不应调用此方法！Byte-Stable Prefix 原则要求
        前缀在整个 session 生命周期内保持不变。此方法仅在以下场景使用：
        - 全新 session 开始（AIAgent 重新实例化时自动调用）
        - 用户显式请求 reset /clear 命令
        - 测试场景

        调用后：前缀解除冻结，待注入队列清空，指纹重置为 None。
        """
        self._frozen_prefix = None
        self._prefix_fingerprint = None
        self._pending_injections.clear()
        self._frozen = False
        self._injection_log.clear()
