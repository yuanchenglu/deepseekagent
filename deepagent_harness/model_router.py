"""
Flash/Pro 智能路由器
=====================

【文件职责】
实现 DeepSeek V4 的 Flash-first / Pro-on-checkpoint 路由策略：
- 默认使用 Flash 模型（便宜、快速）执行低风险步骤
- 在高风险、多次失败、复杂任务等条件下自动升级到 Pro 模型
- 极端不可逆操作使用 Pro Max 模式
- 每次路由决策记录人类可读的原因（route reason），用于 evidence/diagnostics

【为什么需要智能路由】
DeepSeek V4 提供两个模型：
  deepseek-v4-flash: 284B总参数/13B激活，便宜（$0.14/M input），速度快
  deepseek-v4-pro:   1.6T总参数/49B激活，更强（$0.435/M input），适合复杂任务
SWE Verified 测试显示两者差距仅 1.6 分（Pro 80.6 vs Flash 79.0），
所以大部分任务用 Flash 足够，只在关键节点升级 Pro 可以大幅降低成本。

【升级条件（任一触发即升级 Pro）】
- 上下文 > 128K tokens
- 活跃文件 ≥ 5 个
- 依赖深度 ≥ 3
- 失败重试 ≥ 2 次
- 工具调用 ≥ 8 次
- 风险等级 = high/irreversible
- 需要最终审查 / 证据冲突

【与其他模块的协作】
- 在 AIAgent.__init__ 中实例化，从 config.yaml deepseek_routing 段读取配置
- 每轮 API 调用前 route() 被调用，返回 RouteDecision
- 决策结果记录到 self._model_router.route_log，post-execution 写入 result["harness"]
- request_specialized_model 元指令通过 force_upgrade/force_pro_max 触发升级
- IntentRouter 的 model_tier_hint 为路由提供初始建议

参考文献：DSV4调研 Flash/Pro 能力矩阵；C-004 设计约束
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = ["ModelRouter", "ModelTier", "RouteDecision"]


class ModelTier(Enum):
    """
    模型层级枚举。

    这是 model_size × reasoning_effort 的二维决策：
    - FLASH_NON_THINK: Flash + 关闭 thinking（最快最便宜，简单格式化/摘要）
    - FLASH_THINK:     Flash + thinking enabled（常规任务默认）
    - PRO_THINK:       Pro + thinking（复杂/高风险任务）
    - PRO_MAX:         Pro + reasoning_effort=max（不可逆操作、最终审查）
    """
    FLASH_NON_THINK = "flash_non_think"
    FLASH_THINK = "flash_think"
    PRO_THINK = "pro_think"
    PRO_MAX = "pro_max"


@dataclass
class RouteDecision:
    """
    路由决策结果。

    属性:
        tier:              选择的模型层级（ModelTier 枚举）
        model_name:        实际模型名称（如 "deepseek-v4-flash"）
        reasoning_effort:  reasoning 强度：None / "high" / "max"
        reason:            人类可读的路由原因（用于 diagnostics/evidence）
        is_upgrade:        是否从之前的 tier 升级（用于日志高亮）
        context_tokens:    决策时的上下文 token 数快照
        timestamp:         决策时间戳（Unix 时间）
    """
    tier: ModelTier
    model_name: str
    reasoning_effort: Optional[str]
    reason: str
    is_upgrade: bool
    context_tokens: int = 0
    timestamp: float = field(default_factory=time.time)


class ModelRouter:
    """
    Flash/Pro 智能路由器

    【类职责】
    根据当前任务上下文（token 数、文件数、失败次数、风险等级等）决定使用哪个模型。
    实现 Flash-first, Pro-on-checkpoint 策略。

    【路由优先级】（从高到低）
        1. 不可逆操作 → PRO_MAX（最高优先级，不可降级）
        2. 升级条件触发 → PRO_THINK
        3. 简单任务 → FLASH_NON_THINK
        4. 默认 → FLASH_THINK

    【属性】
        flash_model:      Flash 模型名（从配置读取，默认 "deepseek-v4-flash"）
        pro_model:        Pro 模型名（从配置读取，默认 "deepseek-v4-pro"）
        flash_first:      是否启用 Flash 优先策略（默认 True）
        enabled:          路由器是否启用（禁用时始终返回 FLASH_THINK）
        route_log:        历史路由决策列表（用于 diagnostics）
        _current_tier:    当前路由层级（用于 is_upgrade 判断）
    """

    # 升级条件映射：条件标识 → (人类可读原因, 检查函数)
    # 检查函数接收 context 字典，返回 True 表示需要升级
    UPGRADE_CONDITIONS = {
        "context_large": (
            "上下文较大（>128K tokens），需要更强的长上下文理解能力",
            lambda ctx: ctx.get("context_tokens", 0) > 128_000,
        ),
        "many_files": (
            "涉及多个文件（≥5个），需要跨文件推理能力",
            lambda ctx: ctx.get("active_files", 0) >= 5,
        ),
        "deep_deps": (
            "依赖关系复杂（深度≥3），需要更强的架构理解",
            lambda ctx: ctx.get("dependency_depth", 0) >= 3,
        ),
        "failures": (
            "多次失败（≥2次），切换到更强模型重试",
            lambda ctx: ctx.get("failures_so_far", 0) >= 2,
        ),
        "many_tools": (
            "工具调用频繁（≥8次），任务复杂度较高",
            lambda ctx: ctx.get("tool_calls_so_far", 0) >= 8,
        ),
        "high_risk": (
            "高风险操作，使用 Pro 模型更可靠",
            lambda ctx: ctx.get("risk_level") == "high",
        ),
        "irreversible": (
            "不可逆操作（如删除/部署），使用 Pro Max 模式",
            lambda ctx: ctx.get("risk_level") == "irreversible",
        ),
        "final_review": (
            "最终交付审查，使用 Pro 确保质量",
            lambda ctx: ctx.get("requires_final_review", False),
        ),
        "evidence_conflict": (
            "多个来源证据冲突，需要 Pro 分析判断",
            lambda ctx: ctx.get("evidence_conflict", False),
        ),
    }

    # 简单任务指示词（中英文）：出现这些词且无升级条件时，走 FLASH_NON_THINK
    SIMPLE_TASK_INDICATORS = [
        "格式化", "格式转换", "简单计算", "摘要", "总结一下",
        "翻译", "替换文本", "提取", "列出", "显示",
        "format", "summarize", "extract", "list", "translate",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化路由器。

        入参:
            config: 路由配置字典（来自 config.yaml 的 deepseek_routing 段）
                    支持字段：
                    - enabled: bool, 是否启用路由（默认 True）
                    - flash_model: str, Flash 模型名
                    - pro_model: str, Pro 模型名
                    - flash_first: bool, 是否 Flash 优先
        """
        config = config or {}
        self.flash_model = config.get("flash_model", "deepseek-v4-flash")
        self.pro_model = config.get("pro_model", "deepseek-v4-pro")
        self.flash_first = config.get("flash_first", True)
        self.enabled = config.get("enabled", True)
        self.route_log: List[RouteDecision] = []
        self._current_tier: ModelTier = ModelTier.FLASH_THINK

    def route(
        self,
        context: Dict[str, Any],
        instruction: str = "",
    ) -> RouteDecision:
        """
        根据当前上下文做路由决策。

        入参:
            context:     上下文字典，可包含字段：
                         context_tokens, active_files, dependency_depth,
                         failures_so_far, tool_calls_so_far, risk_level,
                         requires_final_review, evidence_conflict
            instruction: 用户指令文本（用于简单任务判断）

        返回:
            RouteDecision 对象，包含选择的模型、原因、是否升级等

        决策顺序:
            1. 如果路由器禁用 → 返回 FLASH_THINK
            2. 不可逆操作 → PRO_MAX（最高优先级）
            3. 检查升级条件 → PRO_THINK（任一条件触发）
            4. 简单任务判断 → FLASH_NON_THINK
            5. 默认 → FLASH_THINK
        """
        if not self.enabled:
            return self._make_decision(
                ModelTier.FLASH_THINK, "路由器未启用，使用默认 Flash Think", False, context
            )

        # 1. 不可逆操作 → PRO_MAX（最高优先级，不可降级）
        if self.UPGRADE_CONDITIONS["irreversible"][1](context):
            decision = self._make_decision(
                ModelTier.PRO_MAX,
                self.UPGRADE_CONDITIONS["irreversible"][0],
                True, context,
            )
            self._log(decision)
            return decision

        # 2. 检查升级条件（优先级高于简单任务判断）
        upgrade_reasons = []
        for cond_key, (reason, check_fn) in self.UPGRADE_CONDITIONS.items():
            if cond_key == "irreversible":
                continue  # 上面已处理
            if check_fn(context):
                upgrade_reasons.append(reason)

        if upgrade_reasons:
            reason_text = "; ".join(upgrade_reasons)
            decision = self._make_decision(
                ModelTier.PRO_THINK,
                f"升级到 Pro：{reason_text}",
                True, context,
            )
            self._log(decision)
            return decision

        # 3. 简单任务 → FLASH_NON_THINK
        if self._is_simple_task(instruction, context):
            decision = self._make_decision(
                ModelTier.FLASH_NON_THINK,
                "简单任务，使用 Flash 非思考模式（快速低成本）",
                False, context,
            )
            self._log(decision)
            return decision

        # 4. 默认 → FLASH_THINK
        decision = self._make_decision(
            ModelTier.FLASH_THINK,
            "常规任务，使用 Flash 思考模式（Flash-first 策略）",
            False, context,
        )
        self._log(decision)
        return decision

    def _is_simple_task(self, instruction: str, context: Dict[str, Any]) -> bool:
        """
        判断是否为简单任务（可走 FLASH_NON_THINK）。

        简单任务特征（全部满足才判定为简单）：
        - 无高风险标记
        - 活跃文件 < 3
        - 无工具调用历史
        - 指令文本包含简单任务指示词，或文本极短（<20字符）且无问号
        """
        if context.get("risk_level") in ("high", "irreversible"):
            return False
        if context.get("active_files", 0) >= 3:
            return False
        if context.get("tool_calls_so_far", 0) > 0:
            return False

        instruction_lower = instruction.lower()
        for indicator in self.SIMPLE_TASK_INDICATORS:
            if indicator in instruction_lower:
                return True

        # 超短指令（<20字符）且不是疑问句，通常是简单任务
        if len(instruction.strip()) < 20 and "?" not in instruction and "？" not in instruction:
            return True

        return False

    def _make_decision(
        self, tier: ModelTier, reason: str, is_upgrade: bool, context: Dict[str, Any]
    ) -> RouteDecision:
        """
        构建 RouteDecision 对象（内部方法）。

        映射关系：tier → (model_name, reasoning_effort)
        """
        # tier 到模型名和 reasoning_effort 的映射表
        model_map = {
            ModelTier.FLASH_NON_THINK: (self.flash_model, None),
            ModelTier.FLASH_THINK: (self.flash_model, "high"),
            ModelTier.PRO_THINK: (self.pro_model, "high"),
            ModelTier.PRO_MAX: (self.pro_model, "max"),
        }
        model_name, effort = model_map[tier]
        return RouteDecision(
            tier=tier,
            model_name=model_name,
            reasoning_effort=effort,
            reason=reason,
            is_upgrade=is_upgrade,
            context_tokens=context.get("context_tokens", 0),
        )

    def _log(self, decision: RouteDecision):
        """记录路由决策到日志和历史列表（内部方法）。"""
        self.route_log.append(decision)
        self._current_tier = decision.tier
        logger.info(
            "Model route: %s (%s) | effort=%s | reason: %s",
            decision.tier.value, decision.model_name,
            decision.reasoning_effort, decision.reason,
        )

    def get_route_history(self) -> List[Dict[str, Any]]:
        """
        获取路由历史（用于 evidence/diagnostics）。

        返回字典列表，每个字典包含路由决策的可序列化字段。
        """
        return [
            {
                "tier": d.tier.value,
                "model": d.model_name,
                "reasoning_effort": d.reasoning_effort,
                "reason": d.reason,
                "is_upgrade": d.is_upgrade,
                "timestamp": d.timestamp,
            }
            for d in self.route_log
        ]

    def force_upgrade(self, reason: str = "manual upgrade") -> RouteDecision:
        """
        强制升级到 Pro Think（供外部调用，如 checkpoint review、元指令请求）。
        """
        decision = self._make_decision(
            ModelTier.PRO_THINK, f"强制升级：{reason}", True, {}
        )
        self._log(decision)
        return decision

    def force_pro_max(self, reason: str = "manual max") -> RouteDecision:
        """强制升级到 Pro Max（不可逆操作、最终交付）。"""
        decision = self._make_decision(
            ModelTier.PRO_MAX, f"强制 Pro Max：{reason}", True, {}
        )
        self._log(decision)
        return decision
