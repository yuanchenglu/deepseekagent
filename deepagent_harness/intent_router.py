"""
7+1 意图路由器
==============

【文件职责】
在认知循环开始前识别用户任务类型（7种基础意图 + 1种 Spec-Driven 元机制），
为每种意图绑定四维执行策略（面谈深度/计划粒度/审查标准/执行模式）。
这是 scene_router 的上层补充：scene_router 做粗分类（CODE/RESEARCH/...），
intent_router 做细粒度分类（Refactor/New/Architecture/...）。

【7+1 意图体系】
基础意图（7种）：
  Refactor:      重构任务——深度面谈、详细计划、深度审查、plan_first
  New:           新建任务——标准面谈、详细计划、标准审查
  Medium:        中等任务——浅层面谈、大纲计划、标准审查
  Architecture:  架构决策——深度面谈、OKR级联、Max审查（Pro Max）
  Research:      研究分析——无面谈、大纲计划、浅层审查
  Simple:        简单任务——无面谈、无计划、无审查（Flash Non-think）
  Collaboration: 协作任务——标准面谈、详细计划、标准审查（delegate_task）
元机制（+1）：
  Spec-Driven:   从用户提供的 Spec 反向推导策略

【为什么用意图路由】
论文 I-10 指出：所有任务进入同一套通用流程会导致策略错配：
  - 重构任务需要深度面谈确认边界，否则容易出 bug
  - 简单任务被过度面谈会让用户烦躁
  - 架构决策需要 Pro Max 多方案对比
意图路由让不同任务自动匹配合适的策略。

【与其他模块的协作】
- 在 pre-turn 阶段被调用（run_agent.py）
- 分类结果传给 ModelRouter（model_tier_hint 影响模型选择）
- 分类结果传给 StarRoadCognition（选择 L2 方法论）
- strategy.toolsets 可用于工具集过滤（当前版本记录但未强制过滤）
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["IntentRouter", "IntentType", "IntentStrategy"]


class IntentType(Enum):
    """意图类型枚举"""
    REFACTOR = "refactor"           # 重构
    NEW = "new"                     # 新建
    MEDIUM = "medium"               # 中等
    ARCHITECTURE = "architecture"   # 架构决策
    RESEARCH = "research"           # 研究
    SIMPLE = "simple"               # 简单
    COLLABORATION = "collaboration" # 协作
    SPEC_DRIVEN = "spec_driven"     # Spec-Driven 元机制


@dataclass
class IntentStrategy:
    """
    意图绑定的执行策略。

    属性:
        interview_depth:  面谈深度——"none"/"shallow"/"standard"/"deep"
        plan_granularity: 计划粒度——"none"/"outline"/"detailed"/"okr_cascade"/"from_spec"
        review_standard:  审查标准——"none"/"shallow"/"standard"/"deep"/"max"/"from_spec"
        execution_mode:  执行模式——"direct"/"plan_first"/"spec_driven"
        model_tier_hint: 建议模型层级——"flash_non_think"/"flash_think"/"pro_think"/"pro_max"/"from_spec"
        toolsets:        推荐启用的工具集列表
    """
    interview_depth: str
    plan_granularity: str
    review_standard: str
    execution_mode: str
    model_tier_hint: str
    toolsets: List[str] = field(default_factory=list)


# 7+1 意图→策略绑定表
# 论文 I-10 中的完整策略矩阵
INTENT_STRATEGIES: Dict[IntentType, IntentStrategy] = {
    IntentType.REFACTOR: IntentStrategy(
        interview_depth="deep", plan_granularity="detailed",
        review_standard="deep", execution_mode="plan_first",
        model_tier_hint="pro_think", toolsets=["file", "terminal", "code_execution"],
    ),
    IntentType.NEW: IntentStrategy(
        interview_depth="standard", plan_granularity="detailed",
        review_standard="standard", execution_mode="plan_first",
        model_tier_hint="flash_think", toolsets=["file", "terminal", "web", "code_execution"],
    ),
    IntentType.MEDIUM: IntentStrategy(
        interview_depth="shallow", plan_granularity="outline",
        review_standard="standard", execution_mode="plan_first",
        model_tier_hint="flash_think", toolsets=["file", "terminal", "web"],
    ),
    IntentType.ARCHITECTURE: IntentStrategy(
        interview_depth="deep", plan_granularity="okr_cascade",
        review_standard="max", execution_mode="plan_first",
        model_tier_hint="pro_max", toolsets=["file", "web", "code_execution"],
    ),
    IntentType.RESEARCH: IntentStrategy(
        interview_depth="none", plan_granularity="outline",
        review_standard="shallow", execution_mode="direct",
        model_tier_hint="flash_think", toolsets=["web", "web_extract", "file"],
    ),
    IntentType.SIMPLE: IntentStrategy(
        interview_depth="none", plan_granularity="none",
        review_standard="none", execution_mode="direct",
        model_tier_hint="flash_non_think", toolsets=["file", "terminal"],
    ),
    IntentType.COLLABORATION: IntentStrategy(
        interview_depth="standard", plan_granularity="detailed",
        review_standard="standard", execution_mode="plan_first",
        model_tier_hint="pro_think", toolsets=["delegation", "file", "terminal", "web"],
    ),
    IntentType.SPEC_DRIVEN: IntentStrategy(
        interview_depth="none", plan_granularity="from_spec",
        review_standard="from_spec", execution_mode="spec_driven",
        model_tier_hint="from_spec", toolsets=["file", "terminal", "web"],
    ),
}

# 意图分类关键词映射（MVP 阶段用规则，后续可升级为小模型）
_INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    IntentType.REFACTOR: ["重构", "refactor", "重写", "改造", "迁移", "migrate",
                          "优化代码", "改进代码", "代码结构"],
    IntentType.NEW: ["创建", "新建", "从零开始", "create", "new project", "搭建",
                     "初始化项目", "init", "bootstrap"],
    IntentType.ARCHITECTURE: ["架构", "architecture", "设计方案", "技术选型", "系统设计",
                              "方案对比", "design doc", "技术决策"],
    IntentType.RESEARCH: ["研究", "research", "分析", "调查", "调研", "对比",
                          "怎么看", "为什么", "原理"],
    IntentType.COLLABORATION: ["分工", "协作", "合作", "一起做", "多个agent", "并行",
                               "分配任务", "团队"],
}

# 简单任务指示词
_SIMPLE_KEYWORDS = [
    "帮我看看", "解释一下", "什么是", "怎么用", "显示", "列出",
    "格式化", "翻译", "总结", "摘要", "计算", "转换",
    "help", "explain", "what is", "how to", "list", "show",
]

# Spec-Driven 指示器
_SPEC_INDICATORS = [
    "根据spec", "按照规范", "按文档", "spec-driven", "按prd",
    "根据需求文档", "按设计文档", "按照spec", "根据spec文档",
    "按spec", "spec文档",
]


class IntentRouter:
    """
    7+1 意图路由器

    【类职责】
    将用户指令分类到 8 种意图类型之一，并返回对应的执行策略。
    与 scene_router 协同：scene_type 决定大类，intent 决定细粒度策略。

    【分类优先级】（高到低）
    1. Spec-Driven 指示器检测
    2. 简单任务检测
    3. 特定意图关键词匹配
    4. 基于 scene_type 的默认映射
    5. 默认 MEDIUM
    """

    def __init__(self):
        self.strategies = INTENT_STRATEGIES

    def classify(self, instruction: str, scene_type: str = "other") -> IntentType:
        """
        分类用户意图。

        入参:
            instruction: 用户指令文本
            scene_type:  scene_router 的分类结果（小写字符串，如 "code"/"research"）

        返回:
            IntentType 枚举值
        """
        instruction_lower = instruction.lower().strip()

        # 1. Spec-Driven 检测（优先级最高）
        for indicator in _SPEC_INDICATORS:
            if indicator in instruction_lower:
                return IntentType.SPEC_DRIVEN

        # 2. 简单任务检测
        is_short = len(instruction.strip()) < 50
        has_question = ("?" in instruction) or ("？" in instruction)
        is_simple_kw = any(kw in instruction_lower for kw in _SIMPLE_KEYWORDS)
        # 排除复杂关键词的覆盖
        is_complex = any(kw in instruction_lower for kw in
                        ["重构", "架构", "创建项目", "refactor", "architecture"])
        if is_simple_kw and not is_complex:
            return IntentType.SIMPLE

        # 3. 特定意图关键词匹配
        for intent_type, keywords in _INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in instruction_lower:
                    return intent_type

        # 4. 基于 scene_type 的默认映射
        scene_to_intent = {
            "code": IntentType.MEDIUM,
            "research": IntentType.RESEARCH,
            "query": IntentType.SIMPLE,
            "planning": IntentType.MEDIUM,
            "operation": IntentType.MEDIUM,
            "other": IntentType.MEDIUM,
        }
        return scene_to_intent.get(scene_type.lower(), IntentType.MEDIUM)

    def get_strategy(self, intent: IntentType) -> IntentStrategy:
        """获取意图对应的执行策略。"""
        return self.strategies.get(intent, self.strategies[IntentType.MEDIUM])

    def classify_and_get_strategy(
        self, instruction: str, scene_type: str = "other"
    ) -> Tuple[IntentType, IntentStrategy]:
        """便捷方法：一次性完成分类和策略获取。"""
        intent = self.classify(instruction, scene_type)
        strategy = self.get_strategy(intent)
        return intent, strategy

    def get_route_context(self, intent: IntentType, strategy: IntentStrategy) -> Dict[str, Any]:
        """
        生成路由上下文字典（传递给 ModelRouter 等下游模块）。

        将四维策略转换为 ModelRouter 可理解的 context 字段。
        """
        # 审查标准到风险等级的映射
        risk_map = {"none": "low", "shallow": "low", "standard": "medium",
                    "deep": "high", "max": "irreversible"}
        risk_level = risk_map.get(strategy.review_standard, "medium")

        # 模型提示到预期工具数的映射
        tools_expected = {"flash_non_think": 1, "flash_think": 5,
                          "pro_think": 10, "pro_max": 15}
        expected_tools = tools_expected.get(strategy.model_tier_hint, 5)

        return {
            "intent": intent.value,
            "interview_depth": strategy.interview_depth,
            "plan_granularity": strategy.plan_granularity,
            "review_standard": strategy.review_standard,
            "execution_mode": strategy.execution_mode,
            "recommended_model_tier": strategy.model_tier_hint,
            "risk_level": risk_level,
            "expected_tool_calls": expected_tools,
            "toolsets": strategy.toolsets,
        }
