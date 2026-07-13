"""
双向 Agent 元指令工具
=====================

【文件职责】
实现论文 I-02 的双向 Agent 四个元指令，作为 tool_call 类型注册到工具系统。
这些工具让模型能够与 Harness 层协同决策，而不是单向输出。

【四个元指令说明】
1. need_more_context: 模型需要更多上下文信息时调用，Harness 会在下一turn注入相关信息
2. request_specialized_model: 模型判断当前任务需要更强模型时调用，请求升级到 Pro/Pro Max
3. trigger_self_review: 模型完成关键步骤后触发自查，Harness 注入反省清单
4. propose_skill: 模型发现可固化的工作流时提议创建 Skill

【为什么需要双向原语】
传统 Agent 是单向的：用户→模型→工具→模型→用户。模型无法主动向 Harness 层
"请求"什么，只能被动接受输入。双向原语让模型能与 Harness 形成闭环反馈。

参考文献：I-02 双向 Agent：LLM ⇄ Harness 协同决策
"""

import json
from typing import Optional

from tools.registry import registry

__all__ = [
    "need_more_context",
    "request_specialized_model",
    "trigger_self_review",
    "propose_skill",
]


def need_more_context(
    what: str,
    why: str = "",
    task_id: Optional[str] = None,
) -> str:
    """
    请求更多上下文信息。

    当你需要额外的信息、文件内容、历史记录才能继续任务时，调用此工具。
    Harness 会在下一轮对话中为你注入相关上下文。

    入参:
        what: 你需要什么具体信息（具体描述，如"项目中所有数据库相关配置"）
        why: 为什么需要这些信息（可选，帮助Harness理解上下文相关性）
        task_id: 任务ID（内部使用，不需要填写）

    返回:
        JSON格式的确认消息，告知请求已被记录，下一轮会注入上下文
    """
    return json.dumps({
        "status": "ok",
        "directive": "need_more_context",
        "message": f"Context request received: {what}. Additional context will be provided in the next turn.",
        "requested": what,
    }, ensure_ascii=False)


def request_specialized_model(
    model_type: str = "pro",
    reason: str = "",
    task_id: Optional[str] = None,
) -> str:
    """
    请求切换到更强的模型。

    当你判断当前任务复杂度高、风险大或多次尝试失败时，调用此工具请求升级模型。

    入参:
        model_type: 请求的模型类型，可选值：
                   - "pro": DeepSeek V4 Pro（通用复杂任务）
                   - "pro_max": Pro Max（不可逆操作、最终审查、架构决策）
        reason: 为什么需要升级模型（说明具体原因，如"多次修复bug失败"）
        task_id: 任务ID（内部使用，不需要填写）

    返回:
        JSON格式的确认消息，告知升级请求已记录
    """
    valid_types = ("pro", "pro_max")
    if model_type not in valid_types:
        model_type = "pro"
    return json.dumps({
        "status": "ok",
        "directive": "request_specialized_model",
        "message": f"Model upgrade requested: {model_type} ({reason})",
        "requested_model": model_type,
    }, ensure_ascii=False)


def trigger_self_review(
    focus_areas: Optional[list] = None,
    confidence: str = "medium",
    task_id: Optional[str] = None,
) -> str:
    """
    触发自我审查。

    在完成关键步骤、提交代码、给出最终答案前，调用此工具触发自查流程。
    Harness 会注入 StarRoad L3 反省清单，帮助你检查遗漏。

    入参:
        focus_areas: 需要重点检查的方面列表（如["安全性", "边界条件", "测试覆盖"]）
        confidence: 当前信心水平，可选值："low"/"medium"/"high"
        task_id: 任务ID（内部使用，不需要填写）

    返回:
        JSON格式的确认消息，告知自查已触发
    """
    if focus_areas is None:
        focus_areas = []
    valid_confidence = ("low", "medium", "high")
    if confidence not in valid_confidence:
        confidence = "medium"
    return json.dumps({
        "status": "ok",
        "directive": "trigger_self_review",
        "message": f"Self-review triggered (confidence={confidence}, focus={focus_areas})",
        "focus_areas": focus_areas,
        "confidence": confidence,
    }, ensure_ascii=False)


def propose_skill(
    skill_name: str,
    trigger: str,
    steps: list,
    task_id: Optional[str] = None,
) -> str:
    """
    提议固化一个新Skill。

    当你发现某个工作流程可以被复用时（如某类bug的固定修复步骤、某类文件的标准生成流程），
    调用此工具提议创建一个新Skill，后续遇到类似场景会自动加载。

    入参:
        skill_name: Skill名称（简短描述，如"python-bug-fix"）
        trigger: 触发条件（什么情况下应该使用这个Skill）
        steps: 执行步骤列表（按顺序排列的具体操作步骤）
        task_id: 任务ID（内部使用，不需要填写）

    返回:
        JSON格式的确认消息，告知Skill提议已记录
    """
    if not skill_name or not steps:
        return json.dumps({
            "status": "error",
            "message": "skill_name and steps are required",
        }, ensure_ascii=False)
    return json.dumps({
        "status": "ok",
        "directive": "propose_skill",
        "message": f"Skill '{skill_name}' proposed for固化",
        "skill_name": skill_name,
        "trigger": trigger,
        "steps_count": len(steps),
    }, ensure_ascii=False)


# ── 注册工具到 Registry ──────────────────────────────────────

# 通用元指令参数（所有元指令都不需要task_id，由系统传入）
_META_PARAM_TASK_ID = {
    "name": "task_id",
    "description": "任务ID（系统内部使用，模型不需要填写）",
    "type": "string",
}

# 注册 need_more_context
registry.register(
    name="need_more_context",
    toolset="meta",
    schema={
        "name": "need_more_context",
        "description": (
            "当你需要额外的上下文信息、文件内容、历史记录或其他缺失信息才能继续任务时，"
            "调用此工具。Harness会在下一轮为你注入相关信息。不要猜测缺失信息，调用这个工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "what": {
                    "type": "string",
                    "description": "具体描述你需要什么信息，越具体越好",
                },
                "why": {
                    "type": "string",
                    "description": "为什么需要这些信息（可选）",
                },
            },
            "required": ["what"],
        },
    },
    handler=need_more_context,
    check_fn=lambda: True,  # 元指令始终可用
)

# 注册 request_specialized_model
registry.register(
    name="request_specialized_model",
    toolset="meta",
    schema={
        "name": "request_specialized_model",
        "description": (
            "当你判断当前任务复杂度太高、风险太大、多次尝试失败或需要处理不可逆操作时，"
            "调用此工具请求升级到更强的模型。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "model_type": {
                    "type": "string",
                    "enum": ["pro", "pro_max"],
                    "description": "请求的模型类型：pro=通用复杂任务；pro_max=架构决策、不可逆操作、最终审查",
                },
                "reason": {
                    "type": "string",
                    "description": "详细说明为什么需要升级模型",
                },
            },
            "required": ["reason"],
        },
    },
    handler=request_specialized_model,
    check_fn=lambda: True,
)

# 注册 trigger_self_review
registry.register(
    name="trigger_self_review",
    toolset="meta",
    schema={
        "name": "trigger_self_review",
        "description": (
            "在完成关键步骤、提交代码、给出最终答案前，调用此工具触发自我审查。"
            "系统会注入检查清单帮助你发现遗漏的问题。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要重点检查的方面列表（如安全性、边界条件）",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "你对当前结果的信心水平",
                },
            },
            "required": [],
        },
    },
    handler=trigger_self_review,
    check_fn=lambda: True,
)

# 注册 propose_skill
registry.register(
    name="propose_skill",
    toolset="meta",
    schema={
        "name": "propose_skill",
        "description": (
            "当你发现某个工作流程可以被复用时（如固定的bug修复模式、标准文件生成流程），"
            "调用此工具提议创建新Skill。后续遇到类似场景会自动加载这个Skill。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Skill的简短名称（使用小写字母和连字符，如python-bug-fix）",
                },
                "trigger": {
                    "type": "string",
                    "description": "什么情况下应该使用这个Skill",
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按顺序排列的具体执行步骤列表",
                },
            },
            "required": ["skill_name", "trigger", "steps"],
        },
    },
    handler=propose_skill,
    check_fn=lambda: True,
)
