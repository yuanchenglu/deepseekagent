"""
StarRoad 三层认知引擎
======================

【文件职责】
实现 StarRoad 三层认知架构：
- L1 荣辱观（价值过滤器）：通用原则，session 级别稳定，注入冻结前缀
- L2 思维方式（方法论框架）：按意图类型选择，注入 turn tail
- L3 三省吾身（反省循环）：Checkpoint 审查 prompt，传给独立审查 Agent

【三层设计原理】
L1（荣辱观）：所有任务通用的价值底线（安全、诚实、用户主权等），不随任务变化，
  放在冻结前缀中确保始终可见（KV Cache 命中）。
L2（方法论）：不同类型任务的最佳实践（重构要小步验证，研究要交叉验证等），
  随意图变化，放在 turn tail 注入，不破坏前缀稳定性。
L3（反省清单）：任务完成/checkpoint 时的自省问题清单，由审查 Agent 使用，
  不进入主对话上下文，避免浪费 token。

【与其他模块的协作】
- L1 段在 _build_system_prompt() 后、freeze() 前追加到 system prompt
- L2 段在构建用户消息时注入（通过 PrefixManager 的 turn tail 机制）
- L3 段在免疫系统审查和 trigger_self_review 元指令时使用
- Memory 分层标签（MEMORY_TIERS）用于未来的记忆强度过滤

参考文献：STARROAD_COARSE_PLAN.md
"""

from typing import Any, Dict, List, Optional

__all__ = ["StarRoadCognition", "MEMORY_TIERS"]


class StarRoadCognition:
    """
    StarRoad 三层认知引擎

    【类职责】
    提供三层认知 prompt 段的生成：
    - get_l1_prompt_section(): 价值原则（冻结前缀）
    - get_l2_prompt_section(): 方法论（turn tail）
    - get_l3_review_prompt(): 反省清单（审查 Agent）
    """

    # L1 荣辱观：核心价值原则（冻结前缀级，不随任务变化）
    # 每条原则都是模型必须始终遵守的底线
    L1_PRINCIPLES: Dict[str, str] = {
        "safety_first": "安全优先：不确定的操作先确认，不可逆操作必须获得用户审批",
        "truthfulness": "诚实可信：不知道就说不知道，不编造信息，不猜测结果",
        "user_sovereignty": "用户主权：用户的数据和决策权属于用户，不擅自做决定",
        "completion_verifiable": "可验证完成：每个产出物必须有可检查的完成标准",
        "no_harm": "不造成伤害：不执行可能导致数据丢失、系统损坏或安全风险的操作",
        "respect_constraints": "遵守约束：严格遵守用户明确提出的所有硬性要求",
        "cost_efficiency": "成本意识：优先使用低成本方案（Flash模型），必要时才升级Pro",
    }

    # L2 思维方式：按意图类型的方法论框架（turn tail 级）
    # 每种意图类型有对应的最佳实践清单
    L2_METHODS: Dict[str, List[str]] = {
        "refactor": [
            "先完整理解现有代码结构和依赖关系再开始修改",
            "小步前进，每修改一个模块就验证一次",
            "保持接口向后兼容，不破坏已有调用方",
            "修改后运行相关测试确认没有回归",
        ],
        "new": [
            "先确认需求边界和验收标准",
            "设计整体架构后再分模块实现",
            "每个模块有明确的输入输出定义",
            "先做最小可运行版本，再逐步完善",
        ],
        "architecture": [
            "至少提出两个备选方案进行对比",
            "列出每个方案的优势、劣势、风险和成本",
            "考虑扩展性、维护成本和团队熟悉度",
            "从最简单可用的方案开始，避免过度设计",
        ],
        "research": [
            "从多个来源交叉验证信息，标注置信度",
            "区分事实（有来源）和推论（自己的分析）",
            "对关键数据点记录来源",
            "总结时给出明确结论而非信息堆砌",
        ],
        "simple": [
            "直接回答问题，不做多余的解释或计划",
            "如果需要工具，直接调用不犹豫",
            "输出简洁明了",
        ],
        "medium": [
            "先理解任务目标，再制定执行计划",
            "完成后验证结果是否符合预期",
            "遇到问题及时调整策略",
        ],
        "collaboration": [
            "将大任务分解为可并行的子任务",
            "明确每个子任务的输入输出和依赖",
            "子任务结果需要合并验证",
        ],
        "spec_driven": [
            "严格按照Spec文档的要求执行",
            "如果Spec有歧义，先确认再执行",
            "完成后对照Spec逐条验收",
        ],
    }

    # L3 三省吾身：反省检查清单（checkpoint 审查用）
    L3_REFLECTION_QUESTIONS: List[str] = [
        "我是否真正理解了用户的核心需求？",
        "我是否遵守了用户提出的所有硬性约束？",
        "我的执行过程是否有遗漏或错误？",
        "产出物是否达到了可验证的完成标准？",
        "有没有更高效或更安全的方式来完成这个任务？",
        "我是否做了超出任务范围的事情（scope creep）？",
        "我的工具调用是否必要且高效？",
        "是否有风险点我没有充分告知用户？",
    ]

    def __init__(self):
        """初始化 StarRoad 认知引擎（无状态，所有内容为类常量）。"""
        pass

    def get_l1_prompt_section(self) -> str:
        """
        获取 L1 荣辱观 prompt 段。

        该段内容稳定（不随任务/意图变化），应注入 System Prompt 的冻结前缀区。

        返回:
            格式化的 Markdown 文本，包含所有核心价值原则
        """
        lines = [
            "## 核心价值观（必须始终遵守）",
            "",
            "以下原则是你的行为基础，在任何情况下都必须遵守：",
        ]
        for _key, principle in self.L1_PRINCIPLES.items():
            lines.append(f"- {principle}")
        lines.append("")
        return "\n".join(lines)

    def get_l2_prompt_section(self, intent_type: str) -> str:
        """
        获取 L2 方法论 prompt 段（按意图类型）。

        该段内容随意图变化，应注入用户消息头部（turn tail），
        不修改冻结前缀。

        入参:
            intent_type: 意图类型字符串（如 "refactor", "new" 等）

        返回:
            格式化的 Markdown 文本。无对应方法论时返回空字符串。
        """
        methods = self.L2_METHODS.get(intent_type, [])
        if not methods:
            return ""

        # 意图类型到中文名称的映射（用于 prompt 中的可读标题）
        intent_names = {
            "refactor": "重构任务", "new": "新建任务",
            "architecture": "架构决策", "research": "研究分析",
            "simple": "简单任务", "medium": "中等任务",
            "collaboration": "协作任务", "spec_driven": "规范驱动任务",
        }
        intent_name = intent_names.get(intent_type, intent_type)

        lines = [
            f"## 本任务方法论（{intent_name}）",
            "",
            f"对于{intent_name}，请遵循以下工作方法：",
        ]
        for i, method in enumerate(methods, 1):
            lines.append(f"{i}. {method}")
        lines.append("")
        return "\n".join(lines)

    def get_l3_review_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        获取 L3 反省 prompt（用于 checkpoint review）。

        该 prompt 传给独立审查 Agent（delegate_task spawn），
        不进入主对话上下文。

        入参:
            context: 可选的任务上下文字典，可包含：
                     goal（任务目标）、completed_steps（已完成步骤）、
                     remaining_steps（剩余步骤）

        返回:
            格式化的审查 prompt 文本
        """
        lines = [
            "## 自省检查清单",
            "",
            "请对照以下问题逐一检查当前任务的执行情况：",
            "",
        ]
        for i, question in enumerate(self.L3_REFLECTION_QUESTIONS, 1):
            lines.append(f"{i}. {question}")

        if context:
            lines.append("")
            lines.append("## 当前任务上下文")
            if context.get("goal"):
                lines.append(f"**任务目标**：{context['goal']}")
            if context.get("completed_steps"):
                lines.append(f"**已完成步骤**：{', '.join(context['completed_steps'])}")
            if context.get("remaining_steps"):
                lines.append(f"**剩余步骤**：{', '.join(context['remaining_steps'])}")

        lines.append("")
        lines.append("请逐一回答上述问题，如发现问题请明确指出。")
        return "\n".join(lines)


# Memory 分层标签（论文 I-12 记忆粒度分层）
# λ (lambda) 表示注入强度：1.0=全量注入，0.0=仅归档
# 安全红线和全局约束永远 λ=1.0，不受过滤
MEMORY_TIERS: Dict[str, Dict[str, Any]] = {
    "global_constraint": {
        "lambda": 1.0,
        "always_inject": True,
        "description": "安全红线、全局约束",
    },
    "user_preference": {
        "lambda": 0.8,
        "always_inject": True,
        "description": "用户偏好（语言、风格等）",
    },
    "project_context": {
        "lambda": 0.6,
        "inject_on_relevance": True,
        "description": "项目上下文和技术栈",
    },
    "historical_decision": {
        "lambda": 0.3,
        "retrieve_on_query": True,
        "description": "历史决策记录",
    },
    "episodic_memory": {
        "lambda": 0.1,
        "archive_only": True,
        "description": "情景记忆（历史对话片段）",
    },
}
