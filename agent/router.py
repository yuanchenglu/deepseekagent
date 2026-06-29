"""语义路由总控（StarRoad Cognition Route 1-3）。
决定消息走哪条处理路径。前置路由，在 run_conversation() 开始时调用。"""

# === DeepAgent: StarRoad Cognition ===

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from agent.expert_matcher import Expert, ExpertMatcher
from agent.plan_tracker import PlanTracker
from agent.memory_index import MemoryIndex
from agent.cognitive_gate import CognitiveGate

logger = logging.getLogger(__name__)

# 意图分类规则（中英文关键词匹配）
_INTENT_PATTERNS: dict[str, list[str]] = {
    "implement": [
        "实现", "写代码", "创建", "开发", "构建", "加个", "添加", "修改",
        "implement", "create", "build", "add", "write", "code", "fix",
        "重构", "改", "修", "develop",
    ],
    "analyze": [
        "分析", "评审", "review", "检查", "审计", "评估",
        "analyze", "check", "audit", "evaluate",
    ],
    "research": [
        "调研", "搜索", "查一下", "研究", "找", "research", "search",
        "find", "look up", "explore", "调查",
    ],
    "discuss": [
        "讨论", "聊聊", "你觉得", "怎么看", "商量", "discuss",
        "thoughts", "opinion", "what do you think",
    ],
    "simple": [],  # 简单任务无关键词特征，由阈值判断
}

# 简单消息特征：短问候语、单字回复（不包含中文句子）
_SIMPLE_PATTERNS = [
    r"^你好$", r"^hi$", r"^hello$", r"^谢谢$", r"^thanks$",
    r"^yes$", r"^no$", r"^是的$", r"^好的$", r"^ok$",
    r"^bye$", r"^再见$",
]


@dataclass
class RouteDecision:
    """路由决策结果。"""
    path: str = "direct"                # 'direct' | 'cognitive_loop' | 'expert_delegate'
    mode: str = ""                      # 'A' | 'B' | 'C' | 'D'（对应 Agency 四种执行模式）
    route_name: str = "simple"          # 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
    experts: list[Expert] = field(default_factory=list)
    confidence: float = 1.0             # 0.0-1.0，表示分类置信度


class AgentRouter:
    """消息路由总控。决定消息走哪条处理路径。

    职责：
    1. 分类意图（route_name）
    2. 简单任务 → path='direct'
    3. 复杂任务 → 匹配专家 → 决定执行模式 A/B/C/D

    不负责：后置评估（由 CognitiveGate 负责）。
    """

    def __init__(
        self,
        expert_matcher: ExpertMatcher,
        plan_tracker: PlanTracker | None = None,
        memory_index: MemoryIndex | None = None,
        cognitive_gate: CognitiveGate | None = None,
    ):
        """初始化 AgentRouter。

        Args:
            expert_matcher: ExpertMatcher 实例
            plan_tracker: PlanTracker 实例（可选）
            memory_index: MemoryIndex 实例（可选）
            cognitive_gate: CognitiveGate 实例（可选）
        """
        self._expert_matcher = expert_matcher
        self._plan_tracker = plan_tracker
        self._memory_index = memory_index
        self._cognitive_gate = cognitive_gate

    def route(self, message: str, context: dict | None = None) -> RouteDecision:
        """主路由方法。

        Args:
            message: 用户消息
            context: 可选上下文（包含当前 plan 状态、对话历史长度等）

        Returns:
            RouteDecision — 路由决策结果
        """
        # 步骤 1：分类意图
        route_name = self._classify_intent(message)
        confidence = self._estimate_confidence(message, route_name)

        # 步骤 2：简单任务 → 直走原流程
        # 注意：只有关键词分类也为 simple 时，长度/模式检查才生效
        if route_name == "simple" and self._is_simple_message(message):
            return RouteDecision(
                path="direct",
                route_name="simple",
                confidence=confidence,
            )

        # 步骤 3：若分类为 simple 但有关键词命中，重新分类
        if route_name == "simple" and not self._is_simple_message(message):
            route_name = "implement"  # 非简单长消息默认走 implement
            confidence = 0.6

        # 步骤 4：复杂任务 → 匹配专家
        experts = self._expert_matcher.match(message, route_name, top_n=2)

        # 步骤 4：决定执行模式
        mode = self._decide_mode(route_name, experts, context)

        # 步骤 5：决定路径
        path = self._decide_path(route_name, mode, experts)

        return RouteDecision(
            path=path,
            mode=mode,
            route_name=route_name,
            experts=experts,
            confidence=confidence,
        )

    def format_prompt_section(self) -> str:
        """返回注入 system prompt 的认知循环引导段（约 300 字）。"""
        parts = [
            "## Cognitive Loop (StarRoad Cognition)",
            "",
            "### 先内后外流程",
            "面对复杂任务时，请遵循先内后外的认知循环：",
            "",
            "1. **内吸（Internal Recall）** — 先向内求：",
            "   - 搜索记忆索引中的已有知识",
            "   - 搜索历史对话中的相关讨论",
            "   - 加载相关 skill",
            "",
            "2. **形成探索计划** — 将盲区转化为具体探索任务",
            "",
            "3. **外求（External Exploration）** — 再向外求：",
            "   - 用最合适的工具执行探索计划",
            "   - 发现新盲区时追加到计划",
            "",
            "4. **综合评估** — 判断是否可以回复，还是需要继续探索或问用户",
            "",
            "5. **三省吾身** — 每次行动后检查：",
            "   - Layer 1 荣辱观：有没有隐瞒不确定性？有没有未经验证的论断？",
            "   - Layer 2 思维方式：有没有 step by step？有没有假设先行？",
            "   - Layer 3 反省：有哪些可以改进？",
        ]
        return "\n".join(parts)

    # -- 内部方法 --

    def _classify_intent(self, message: str) -> str:
        """用关键词匹配分类意图。"""
        msg_lower = message.lower()

        # 按优先级检查：实现 → 调研 → 分析 → 讨论
        for pattern in _INTENT_PATTERNS["implement"]:
            if pattern in msg_lower:
                return "implement"

        for pattern in _INTENT_PATTERNS["research"]:
            if pattern in msg_lower:
                return "research"

        for pattern in _INTENT_PATTERNS["analyze"]:
            if pattern in msg_lower:
                return "analyze"

        for pattern in _INTENT_PATTERNS["discuss"]:
            if pattern in msg_lower:
                return "discuss"

        # 默认：长消息含代码特征时倾向 implement
        if len(message) > 100 and any(c in message for c in ("{", "}", "(", ")", "def ", "class ")):
            return "implement"

        return "simple"

    def _is_simple_message(self, message: str) -> bool:
        """判断是否为简单消息。"""
        msg_stripped = message.strip()
        if len(msg_stripped) < 15:
            return True
        for pattern in _SIMPLE_PATTERNS:
            if re.match(pattern, msg_stripped, re.IGNORECASE):
                return True
        return False

    def _estimate_confidence(self, message: str, route_name: str) -> float:
        """估算分类置信度。"""
        msg_len = len(message.strip())
        if route_name == "simple":
            return 0.9 if msg_len < 30 else 0.6

        # 消息越长、含代码特征越多，置信度越高
        code_chars = sum(1 for c in message if c in "{}()[]<>")
        if msg_len > 200 and code_chars > 10:
            return 0.95
        if msg_len > 100:
            return 0.85
        return 0.7

    def _decide_mode(self, route_name: str, experts: list[Expert], context: dict | None) -> str:
        """根据意图决定 Agency 执行模式。"""
        if route_name == "implement" and experts:
            return "A"  # 委派编码任务
        elif route_name == "analyze" and experts:
            return "B"  # 本地专家模式
        elif route_name == "discuss":
            return "C"  # 讨论/咨询模式
        elif route_name == "research":
            return "D"  # 认知循环模式
        return "B"

    def _decide_path(self, route_name: str, mode: str, experts: list[Expert]) -> str:
        """根据意图和模式决定路径。"""
        if route_name == "simple":
            return "direct"
        if mode == "A" and experts:
            return "expert_delegate"
        if mode == "D":
            return "cognitive_loop"
        return "direct"  # 模式 B/C 走直接路径（prompt 注入即可）
