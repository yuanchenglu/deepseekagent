"""
双向 Agent 原语（Bidirectional Agent Primitives）
==================================================

【文件职责】
实现论文 I-02 的双向 Agent 协同决策机制：LLM 与 Harness 之间的四个元指令。
传统 Agent 是单向的：Harness 组装 Prompt → LLM 生成回复 → Harness 执行工具。
双向原语让 LLM 能主动向 Harness 发送"控制信号"，请求 Harness 层的干预：
  1. need_more_context:        请求更多上下文信息（记忆、相关文件、历史决策）
  2. request_specialized_model: 请求切换到专门/更强的模型（升级 Pro/Max）
  3. trigger_self_review:       触发自我审查（调用 StarRoad L3 反省清单）
  4. propose_skill:             提议将当前有效工作模式固化为 Skill

【为什么需要双向原语】
单向 Agent 中 LLM 是被动的：只能接收 Harness 给的信息，无法主动请求帮助。
当信息不足、任务复杂度超出当前模型能力、或发现可复用模式时，
LLM 没有机制告知 Harness。双向原语给了 LLM "举手求助"和"主动贡献"的通道。

【与其他模块的协作】
- 原语作为特殊工具注册到工具系统，Agent 可通过 tool_call 调用
- need_more_context → PrefixManager.inject_mid_session_change() 注入检索到的信息
- request_specialized_model → ModelRouter.force_upgrade()/force_pro_max()
- trigger_self_review → StarRoadCognition.get_l3_review_prompt() 生成审查 prompt
- propose_skill → ImmuneSystem 生成 Skill 条目并持久化
- 原语处理结果通过用户消息注入返回给 Agent

参考文献：I-02 双向 Agent：LLM ⇄ Harness 协同决策
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "MetaDirectiveType", "MetaDirective", "MetaDirectiveResult",
    "BidirectionalPrimitives", "get_meta_directive_tools",
]


class MetaDirectiveType(Enum):
    """
    元指令类型枚举。

    四个元指令构成 LLM→Harness 的反馈通道：
    - NEED_MORE_CONTEXT: 信息不足，请求补充上下文
    - REQUEST_SPECIALIZED_MODEL: 当前模型能力不够，请求升级
    - TRIGGER_SELF_REVIEW: 完成一个阶段，请求自查
    - PROPOSE_SKILL: 发现有效模式，提议固化为 Skill
    """
    NEED_MORE_CONTEXT = "need_more_context"
    REQUEST_SPECIALIZED_MODEL = "request_specialized_model"
    TRIGGER_SELF_REVIEW = "trigger_self_review"
    PROPOSE_SKILL = "propose_skill"


@dataclass
class MetaDirective:
    """
    元指令调用的数据结构（来自 LLM 的 tool_call）。

    属性:
        directive_type: 元指令类型
        reason:         调用原因（人类可读，用于诊断）
        parameters:     指令参数（不同指令有不同参数）
        tool_call_id:   原始 tool_call 的 ID（用于返回结果）
    """
    directive_type: MetaDirectiveType
    reason: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: Optional[str] = None


@dataclass
class MetaDirectiveResult:
    """
    元指令处理结果（返回给 LLM 的工具响应）。

    属性:
        success:       处理是否成功
        directive:     对应的元指令类型
        message:       返回给 LLM 的自然语言消息
        action_taken:  Harness 实际执行的动作（人类可读）
        data:          附加数据（如检索到的上下文、升级后的模型名等）
    """
    success: bool
    directive: MetaDirectiveType
    message: str
    action_taken: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


# 元指令对应的工具 schema（OpenAI function calling 格式）
META_DIRECTIVE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "need_more_context",
            "description": (
                "当你发现当前上下文信息不足以完成任务时调用此工具。"
                "可以请求：相关记忆、文件内容、历史决策、项目结构等。"
                "Harness会检索并注入相关信息到下一回合。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么需要更多上下文，缺少什么信息",
                    },
                    "context_type": {
                        "type": "string",
                        "enum": ["memory", "files", "history", "project_structure", "decisions", "other"],
                        "description": "需要的上下文类型",
                    },
                    "specific_query": {
                        "type": "string",
                        "description": "具体要查询什么（如：用户之前对X的偏好、项目的测试配置）",
                    },
                },
                "required": ["reason", "context_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_specialized_model",
            "description": (
                "当你发现当前模型能力不足以完成任务时调用此工具请求升级。"
                "适用场景：复杂架构决策、多次尝试失败、不可逆操作前的最终审查、"
                "需要深度推理的任务。Harness会将模型升级到Pro/Pro Max。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么需要更强模型，当前遇到什么困难",
                    },
                    "requested_tier": {
                        "type": "string",
                        "enum": ["pro_think", "pro_max"],
                        "description": "请求的模型层级",
                    },
                },
                "required": ["reason", "requested_tier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_self_review",
            "description": (
                "当你完成一个重要阶段或发现可能有问题时调用此工具触发自我审查。"
                "Harness会启动反省流程，对照检查清单检查当前工作。"
                "建议在：完成核心功能后、准备提交代码前、遇到bug不知原因时调用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么要触发自我审查",
                    },
                    "current_stage": {
                        "type": "string",
                        "description": "当前完成到什么阶段（如：核心功能完成、准备测试）",
                    },
                    "concerns": {
                        "type": "string",
                        "description": "你担心可能有问题的地方（可选）",
                    },
                },
                "required": ["reason", "current_stage"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_skill",
            "description": (
                "当你发现一个可复用的工作模式或最佳实践时调用此工具提议固化为Skill。"
                "Skill会被保存，后续类似任务自动加载参考。"
                "适用场景：发现某类任务的有效流程、解决了一个反复出现的问题、"
                "总结出某模块的操作规范。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Skill名称（简短描述性的英文名，如：react-testing-pattern）",
                    },
                    "description": {
                        "type": "string",
                        "description": "这个Skill解决什么问题，适用于什么场景",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "具体的工作模式/步骤/最佳实践内容",
                    },
                    "trigger_conditions": {
                        "type": "string",
                        "description": "什么情况下应该使用这个Skill",
                    },
                },
                "required": ["skill_name", "description", "pattern", "trigger_conditions"],
            },
        },
    },
]

# 工具名→指令类型映射
_TOOL_NAME_TO_TYPE = {
    "need_more_context": MetaDirectiveType.NEED_MORE_CONTEXT,
    "request_specialized_model": MetaDirectiveType.REQUEST_SPECIALIZED_MODEL,
    "trigger_self_review": MetaDirectiveType.TRIGGER_SELF_REVIEW,
    "propose_skill": MetaDirectiveType.PROPOSE_SKILL,
}


class BidirectionalPrimitives:
    """
    双向 Agent 原语处理器

    【类职责】
    接收并处理 LLM 通过 tool_call 发出的元指令，协调 Harness 各模块响应：
    - 解析 tool_call 为 MetaDirective
    - 调用对应模块执行动作
    - 返回 MetaDirectiveResult 给 LLM
    - 记录处理日志用于 diagnostics

    【处理回调】
    各元指令的实际处理可以通过回调函数自定义，
    也可以使用默认实现（与其他 Harness 模块协作）。

    【属性】
        handlers: 指令类型→处理函数的映射
        directive_log: 历史元指令处理记录
    """

    def __init__(
        self,
        prefix_manager=None,
        model_router=None,
        starroad=None,
        immune_system=None,
        context_retrieval_fn: Optional[Callable] = None,
    ):
        """
        初始化双向原语处理器。

        入参:
            prefix_manager:      PrefixManager实例（用于注入检索到的上下文）
            model_router:        ModelRouter实例（用于模型升级）
            starroad:            StarRoadCognition实例（用于生成审查prompt）
            immune_system:       ImmuneSystem实例（用于Skill固化）
            context_retrieval_fn: 自定义上下文检索函数
                                 签名: (query: str, context_type: str) -> str
        """
        self.prefix_manager = prefix_manager
        self.model_router = model_router
        self.starroad = starroad
        self.immune_system = immune_system
        self.context_retrieval_fn = context_retrieval_fn
        self.directive_log: List[Dict[str, Any]] = []

        # 注册默认处理函数
        self.handlers: Dict[MetaDirectiveType, Callable] = {
            MetaDirectiveType.NEED_MORE_CONTEXT: self._handle_need_more_context,
            MetaDirectiveType.REQUEST_SPECIALIZED_MODEL: self._handle_request_model,
            MetaDirectiveType.TRIGGER_SELF_REVIEW: self._handle_self_review,
            MetaDirectiveType.PROPOSE_SKILL: self._handle_propose_skill,
        }

    def is_meta_directive_tool(self, tool_name: str) -> bool:
        """判断工具名是否是元指令工具。"""
        return tool_name in _TOOL_NAME_TO_TYPE

    def parse_tool_call(
        self, tool_name: str, arguments: Dict[str, Any], tool_call_id: Optional[str] = None
    ) -> Optional[MetaDirective]:
        """
        将 tool_call 解析为 MetaDirective 对象。

        入参:
            tool_name:   工具名（如 "need_more_context"）
            arguments:   工具参数字典
            tool_call_id: 原始tool_call ID

        返回:
            MetaDirective对象（工具名识别为元指令时）或 None
        """
        if not self.is_meta_directive_tool(tool_name):
            return None
        directive_type = _TOOL_NAME_TO_TYPE[tool_name]
        return MetaDirective(
            directive_type=directive_type,
            reason=arguments.get("reason", ""),
            parameters={k: v for k, v in arguments.items() if k != "reason"},
            tool_call_id=tool_call_id,
        )

    def handle_directive(self, directive: MetaDirective) -> MetaDirectiveResult:
        """
        处理一条元指令，返回处理结果。

        入参:
            directive: 解析后的元指令对象

        返回:
            MetaDirectiveResult 处理结果
        """
        handler = self.handlers.get(directive.directive_type)
        if not handler:
            result = MetaDirectiveResult(
                success=False,
                directive=directive.directive_type,
                message=f"未知的元指令类型: {directive.directive_type.value}",
            )
        else:
            try:
                result = handler(directive)
            except Exception as e:
                logger.error("Meta directive %s failed: %s", directive.directive_type.value, e)
                result = MetaDirectiveResult(
                    success=False,
                    directive=directive.directive_type,
                    message=f"处理元指令时出错: {str(e)}",
                )

        # 记录日志
        self.directive_log.append({
            "type": directive.directive_type.value,
            "reason": directive.reason,
            "success": result.success,
            "action": result.action_taken,
            "timestamp": __import__("time").time(),
        })

        return result

    def handle_tool_call(
        self, tool_name: str, arguments: Dict[str, Any], tool_call_id: Optional[str] = None
    ) -> Optional[MetaDirectiveResult]:
        """
        便捷方法：直接从tool_call名和参数解析并处理。

        非元指令工具返回None，调用方应按普通工具处理。
        """
        directive = self.parse_tool_call(tool_name, arguments, tool_call_id)
        if not directive:
            return None
        return self.handle_directive(directive)

    # ── 各元指令的默认处理实现 ──────────────────────────────────

    def _handle_need_more_context(self, d: MetaDirective) -> MetaDirectiveResult:
        """
        处理 need_more_context 元指令。

        逻辑：
        1. 如果有自定义检索函数，调用它获取信息
        2. 否则生成提示性消息，告诉Agent Harness已记录其信息需求
        3. 通过PrefixManager将请求注入到下一turn（告知记忆/文件系统可用）
        """
        context_type = d.parameters.get("context_type", "other")
        query = d.parameters.get("specific_query", d.reason)

        context_info = ""
        if self.context_retrieval_fn:
            try:
                context_info = self.context_retrieval_fn(query, context_type)
            except Exception as e:
                logger.debug("Context retrieval failed: %s", e)

        if not context_info:
            # 默认响应：提示Agent可以直接使用工具获取所需信息
            type_hints = {
                "memory": "你可以通过搜索会话历史或读取用户配置获取记忆信息",
                "files": "你可以使用file工具(read_file/search_files)读取相关文件",
                "history": "你可以使用search_files搜索代码中的历史决策和模式",
                "project_structure": "你可以先列出项目目录结构了解整体架构",
                "decisions": "检查文档目录(docs/)下的设计决策记录",
                "other": "请明确描述你需要什么信息，或使用可用工具获取",
            }
            context_info = type_hints.get(context_type, type_hints["other"])

        # 将信息请求注入下一turn
        if self.prefix_manager:
            injection = (
                f"[context_request] 你请求了{context_type}类型的信息：{d.reason}\n"
                f"提示：{context_info}"
            )
            self.prefix_manager.inject_mid_session_change("meta_context_request", injection)

        return MetaDirectiveResult(
            success=True,
            directive=d.directive_type,
            message=(
                f"已收到你的信息需求({context_type})。{context_info}\n"
                f"请使用可用工具获取所需信息，或更具体地描述你需要什么。"
            ),
            action_taken=f"记录上下文请求，注入提示到下一回合",
            data={"context_type": context_type, "query": query},
        )

    def _handle_request_model(self, d: MetaDirective) -> MetaDirectiveResult:
        """
        处理 request_specialized_model 元指令。

        逻辑：
        1. 调用ModelRouter.force_upgrade()或force_pro_max()
        2. 记录升级原因
        3. 返回告知Agent模型已升级
        """
        requested_tier = d.parameters.get("requested_tier", "pro_think")

        if not self.model_router:
            return MetaDirectiveResult(
                success=False,
                directive=d.directive_type,
                message="模型路由器未配置，无法升级模型",
            )

        if requested_tier == "pro_max":
            decision = self.model_router.force_pro_max(f"Agent请求: {d.reason}")
        else:
            decision = self.model_router.force_upgrade(f"Agent请求: {d.reason}")

        return MetaDirectiveResult(
            success=True,
            directive=d.directive_type,
            message=(
                f"已切换到 {decision.model_name} 模型（reasoning_effort={decision.reasoning_effort}）。\n"
                f"原因：{d.reason}\n"
                f"请继续工作，更强的模型能力现在可用。"
            ),
            action_taken=f"升级到{decision.tier.value}({decision.model_name})",
            data={
                "new_tier": decision.tier.value,
                "new_model": decision.model_name,
                "reasoning_effort": decision.reasoning_effort,
            },
        )

    def _handle_self_review(self, d: MetaDirective) -> MetaDirectiveResult:
        """
        处理 trigger_self_review 元指令。

        逻辑：
        1. 调用StarRoadCognition.get_l3_review_prompt()生成反省清单
        2. 返回审查prompt给Agent（让Agent自查）
        """
        current_stage = d.parameters.get("current_stage", "")
        concerns = d.parameters.get("concerns", "")

        review_context = {
            "goal": f"当前阶段: {current_stage}",
            "completed_steps": [f"阶段: {current_stage}"],
            "remaining_steps": ["根据审查结果修复发现的问题"],
        }

        if self.starroad:
            review_prompt = self.starroad.get_l3_review_prompt(review_context)
        else:
            # 基础审查清单
            review_prompt = (
                "## 自我审查清单\n\n"
                "请对照以下问题检查当前工作：\n"
                "1. 是否真正理解了用户需求？\n"
                "2. 是否遵守了所有硬约束？\n"
                "3. 代码实现是否正确？\n"
                "4. 是否有遗漏的边界情况？\n"
                "5. 产出物是否符合验收标准？\n"
            )

        if concerns:
            review_prompt += f"\n## 你特别关注的问题\n{concerns}\n"

        review_prompt += "\n请逐一回答上述问题，如发现问题请记录并修复。"

        return MetaDirectiveResult(
            success=True,
            directive=d.directive_type,
            message=review_prompt,
            action_taken="生成L3反省审查清单",
            data={"review_prompt": review_prompt, "stage": current_stage},
        )

    def _handle_propose_skill(self, d: MetaDirective) -> MetaDirectiveResult:
        """
        处理 propose_skill 元指令。

        逻辑：
        1. 验证Skill参数完整性
        2. 通过PrefixManager通知系统
        3. 如果有ImmuneSystem/Skill管理器，尝试持久化
        """
        skill_name = d.parameters.get("skill_name", "")
        description = d.parameters.get("description", "")
        pattern = d.parameters.get("pattern", "")
        triggers = d.parameters.get("trigger_conditions", "")

        if not all([skill_name, description, pattern, triggers]):
            return MetaDirectiveResult(
                success=False,
                directive=d.directive_type,
                message="Skill提案不完整：需要skill_name、description、pattern、trigger_conditions",
            )

        # 生成Skill内容
        skill_content = (
            f"# {skill_name}\n\n"
            f"## 描述\n{description}\n\n"
            f"## 触发条件\n{triggers}\n\n"
            f"## 工作模式\n{pattern}\n"
        )

        # 通知系统
        if self.prefix_manager:
            self.prefix_manager.inject_mid_session_change(
                "skill_proposed",
                f"[skill_proposal] 提议固化新Skill: {skill_name}\n描述: {description}",
            )

        # 尝试通过ImmuneSystem持久化（复用Skill固化机制）
        skill_saved = False
        if self.immune_system and hasattr(self.immune_system, "skill_manager"):
            try:
                if self.immune_system.skill_manager and hasattr(
                    self.immune_system.skill_manager, "create_skill"
                ):
                    self.immune_system.skill_manager.create_skill(
                        name=f"proposed-{skill_name}",
                        content=skill_content,
                    )
                    skill_saved = True
            except Exception as e:
                logger.debug("Failed to save proposed skill: %s", e)

        return MetaDirectiveResult(
            success=True,
            directive=d.directive_type,
            message=(
                f"Skill提案「{skill_name}」已收到。\n"
                f"描述：{description}\n"
                f"状态：{'已保存到Skill库' if skill_saved else '已记录，待人工确认后固化'}\n"
                f"感谢你的贡献！这个模式将在后续类似任务中参考使用。"
            ),
            action_taken=f"记录Skill提案: {skill_name}",
            data={
                "skill_name": skill_name,
                "saved": skill_saved,
                "content_preview": pattern[:200],
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取双向原语使用统计。"""
        type_counts: Dict[str, int] = {}
        for entry in self.directive_log:
            t = entry["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_directives": len(self.directive_log),
            "by_type": type_counts,
            "success_rate": (
                sum(1 for e in self.directive_log if e["success"]) / len(self.directive_log)
                if self.directive_log else 1.0
            ),
        }


def get_meta_directive_tools() -> List[Dict[str, Any]]:
    """
    获取元指令对应的工具schema列表（用于注册到工具系统）。

    返回:
        OpenAI function calling格式的工具schema列表
    """
    return META_DIRECTIVE_TOOLS.copy()


def is_meta_directive_tool_name(name: str) -> bool:
    """判断工具名是否是元指令工具（便捷函数）。"""
    return name in _TOOL_NAME_TO_TYPE
