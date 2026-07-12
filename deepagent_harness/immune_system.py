"""
Agent 免疫系统
===============

【文件职责】
实现论文 I-01 的 Agent 免疫系统：Agent 执行完成后自动检查硬约束是否被遵守，
发现违反时生成纠正性 Skill（确定性检查逻辑），后续任务自动加载。

【三环节闭环】
1. 自查（post_execution_review）：只读硬约束列表+最终产出物，逐条检查
2. 固化（_generate_remediation_skill）：发现违反时生成纠正性 Skill
3. 外挂（_persist_skill）：Skill 注册到 Skill 系统，后续自动加载

【为什么免疫系统有效】
Transformer 的软注意力在长对话中会被稀释（注意力权重 ∝ 1/序列长度），
导致 System Prompt 中的约束在多轮后遵守率从 ~100% 降到 ~40%。
免疫系统将"是否遵守约束"从模型的概率性注意力问题，转化为 Harness 层的
确定性检查问题——违反率从概率性变为确定性地被检测。

【检查逻辑】
当前 MVP 使用启发式关键词检查：
- 禁止类约束：检查产出物中是否有禁止动作的执行迹象（如"已删除"等）
- 必须类约束：检查要求的关键词是否出现在输出中
未来可升级为 delegate_task spawn 独立审查 Agent。

【与其他模块的协作】
- 硬约束列表来自 HardConstraintExtractor.extract()
- 在 run_conversation() 返回结果后被调用（post-execution hook）
- 生成的 Skill 通过 PrefixManager.inject_mid_session_change() 通知下一 turn
- 违反数和合规率写入 result["harness_immune_violations"]
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from deepagent_harness.hard_constraint import HardConstraint

logger = logging.getLogger(__name__)

__all__ = ["ImmuneSystem", "Violation", "ImmuneResult"]


@dataclass
class Violation:
    """约束违反记录"""
    constraint_text: str   # 被违反的约束原文
    constraint_type: str   # "prohibition" / "requirement"
    severity: str          # "high"（禁止类违反）/ "medium"（必须类遗漏）/ "low"
    evidence: str          # 违反证据（从对话中提取的片段）
    suggested_fix: str     # 建议的修复方式


@dataclass
class ImmuneResult:
    """免疫系统审查结果"""
    violations: List[Violation] = field(default_factory=list)
    skills_generated: List[Dict[str, Any]] = field(default_factory=list)
    compliance_rate: float = 1.0
    passed: bool = True


class ImmuneSystem:
    """
    Agent 免疫系统

    【类职责】
    执行后自动审查 Agent 是否遵守了所有硬约束，发现违反时生成纠正性 Skill。

    【属性】
        skill_manager:    Skill 管理器（可选，用于固化 Skill）
        violation_log:    历史违反记录列表
        generated_skills: 已生成的纠正性 Skill 列表
        total_checks:     累计检查的约束总数
        total_violations: 累计发现的违反总数
    """

    def __init__(self, skill_manager=None):
        """
        初始化免疫系统。

        入参:
            skill_manager: Skill 管理器实例（可选，用于自动固化 Skill）
                           需要有 create_skill(name, content) 方法
        """
        self.skill_manager = skill_manager
        self.violation_log: List[Dict[str, Any]] = []
        self.generated_skills: List[Dict[str, Any]] = []
        self.total_checks = 0
        self.total_violations = 0

    def post_execution_review(
        self,
        hard_constraints: List[HardConstraint],
        task_output: str,
        conversation_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> ImmuneResult:
        """
        执行后审查：检查硬约束是否被遵守。

        【设计原则】只读约束列表和最终产出物，不读完整执行日志
        （论文 I-01：审查者不应陷入与执行者相同的注意力稀释困境）

        入参:
            hard_constraints:     任务开始时提取的硬约束列表
            task_output:          任务的最终输出文本
            conversation_messages: 对话消息（可选，只检查最近10条用于证据提取）

        返回:
            ImmuneResult 对象，包含违反列表、生成的Skill、合规率
        """
        result = ImmuneResult()

        if not hard_constraints:
            return result  # 无约束则自动通过

        # 构建检查文本：最终输出 + 最近消息的关键片段
        combined_text = task_output
        if conversation_messages:
            parts = []
            for msg in conversation_messages[-10:]:
                if msg.get("role") == "assistant":
                    content = msg.get("content") or ""
                    if content:
                        parts.append(content[:500])  # 每条最多 500 字符
                    for tc in (msg.get("tool_calls") or [])[:3]:
                        fn = tc.get("function", {})
                        parts.append(f"[调用工具: {fn.get('name', 'unknown')}]")
                elif msg.get("role") == "tool":
                    content = str(msg.get("content") or "")[:300]
                    parts.append(f"[工具结果: {content}]")
            combined_text = task_output + "\n" + "\n".join(parts)

        # 逐条检查约束
        for constraint in hard_constraints:
            self.total_checks += 1
            violation = self._check_single_constraint(constraint, combined_text)
            if violation:
                result.violations.append(violation)
                self.total_violations += 1
                # 生成纠正性 Skill
                skill = self._generate_remediation_skill(violation)
                if skill:
                    result.skills_generated.append(skill)
                    self.generated_skills.append(skill)
                    if self.skill_manager:
                        self._persist_skill(skill)

        # 计算合规率
        if hard_constraints:
            result.compliance_rate = 1.0 - (len(result.violations) / len(hard_constraints))
        result.passed = len(result.violations) == 0

        # 记录违反日志
        for v in result.violations:
            self.violation_log.append({
                "constraint": v.constraint_text,
                "severity": v.severity,
                "evidence": v.evidence,
            })

        if not result.passed:
            logger.warning(
                "Immune system: %d violations found (compliance: %.0f%%)",
                len(result.violations), result.compliance_rate * 100,
            )

        return result

    def _check_single_constraint(
        self, constraint: HardConstraint, text: str
    ) -> Optional[Violation]:
        """
        检查单条约束是否被违反。

        入参:
            constraint: 要检查的硬约束
            text:      用于检查的文本（输出+最近对话）

        返回:
            Violation 对象（违反时）或 None（遵守时）
        """
        text_lower = text.lower()

        if constraint.constraint_type == "prohibition":
            # 禁止类：检查是否有禁止动作被执行的迹象
            # 模式：已/已经 + (副词) + 动作关键词
            for keyword in constraint.keywords:
                if keyword and len(keyword) >= 2:
                    action_patterns = [
                        rf"已(?:经)?(?:.{{0,15}})?{re.escape(keyword)}",
                        rf"(?:deleted|removed|executed|ran|done|completed).{{0,30}}{re.escape(keyword.lower())}",
                        rf"✅.*{re.escape(keyword)}",
                    ]
                    for pattern in action_patterns:
                        if re.search(pattern, text_lower):
                            return Violation(
                                constraint_text=constraint.text,
                                constraint_type="prohibition",
                                severity="high",
                                evidence=f"发现禁止动作 '{keyword}' 的执行迹象",
                                suggested_fix=f"检查是否真的违反了约束「{constraint.text}」",
                            )

        elif constraint.constraint_type == "requirement":
            # 必须类：检查要求的关键词是否出现在输出中
            for keyword in constraint.keywords:
                if keyword and len(keyword) >= 2:
                    if keyword not in text and keyword.lower() not in text_lower:
                        return Violation(
                            constraint_text=constraint.text,
                            constraint_type="requirement",
                            severity="medium",
                            evidence=f"未在输出中找到要求的内容 '{keyword}'",
                            suggested_fix=f"确认是否满足了约束「{constraint.text}」",
                        )

        return None

    def _generate_remediation_skill(self, violation: Violation) -> Dict[str, Any]:
        """
        生成纠正性 Skill（确定性检查逻辑，非自然语言提示）。

        论文 I-01：固化的 Skill 应该是可执行的检查逻辑，而非"请记得遵守..."
        这样的自然语言提示。自然语言提示仍然依赖模型注意力，而确定性
        检查逻辑由 Harness 执行。
        """
        # 用 hash 生成唯一 Skill 名（避免重复）
        skill_name = f"immune-check-{abs(hash(violation.constraint_text)) % 10000}"
        return {
            "name": skill_name,
            "trigger": violation.constraint_text,
            "type": "constraint_check",
            "severity": violation.severity,
            "check_description": f"确保遵守：{violation.constraint_text}",
            "remediation": violation.suggested_fix,
            "check_type": violation.constraint_type,
            "auto_generated": True,
        }

    def _persist_skill(self, skill: Dict[str, Any]):
        """尝试通过 skill_manager 持久化 Skill（失败不阻塞）。"""
        try:
            if hasattr(self.skill_manager, "create_skill"):
                self.skill_manager.create_skill(
                    name=skill["name"],
                    content=(
                        f"# {skill['name']}\n\n"
                        f"## 触发条件\n{skill['trigger']}\n\n"
                        f"## 检查\n{skill['check_description']}\n\n"
                        f"## 修复\n{skill['remediation']}\n"
                    ),
                )
        except Exception as e:
            logger.debug("Failed to persist immune skill: %s", e)

    def get_stats(self) -> Dict[str, Any]:
        """获取免疫系统统计信息。"""
        return {
            "total_checks": self.total_checks,
            "total_violations": self.total_violations,
            "total_skills_generated": len(self.generated_skills),
            "overall_compliance_rate": (
                (self.total_checks - self.total_violations) / self.total_checks
                if self.total_checks > 0 else 1.0
            ),
        }

    def reset(self):
        """重置审查状态（新任务开始时调用）。"""
        self.violation_log.clear()
        self.total_checks = 0
        self.total_violations = 0
