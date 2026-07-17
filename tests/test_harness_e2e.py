#!/usr/bin/env python3
"""
DeepAgent Harness 端到端集成测试
================================

验证 32 期 Harness 改造的完整流程：
用户输入（含硬约束）→ 场景路由 → 意图分类 → 硬约束提取 →
Prefix 冻结 → Flash/Pro 路由 → Reasoning 剥离 → 免疫系统审查 → 输出

对应方舟众测 32 期任务步骤 3.9：
"端到端集成测试：用户输入包含硬约束的复杂中文任务→场景路由识别→意图分类→
Byte-Stable Prefix 注入→Flash/Pro 路由→推理执行→Reasoning 剥离→免疫系统审查→输出结果"

测试策略：
- 所有 Harness 模块使用真实实现（纯 Python 逻辑，无 LLM 调用）
- CodeModeDispatcher.dispatch 使用 mock（避免子进程调用 OpenCode 二进制）
- 验证每个管线阶段的输入输出符合预期
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入所有 Harness 模块
from deepagent_harness import (
    SceneRouter, SceneType, route_instruction,
    PrefixManager,
    HardConstraintExtractor, extract_hard_constraints,
    format_constraints_for_prefix,
    ModelRouter, ModelTier,
    ReasoningManager,
    IntentRouter, IntentType,
    ImmuneSystem,
)


@pytest.fixture
def mock_dispatch():
    """模拟 CodeModeDispatcher.dispatch，避免实际调用子进程导致超时

    端到端测试验证 Harness 管线逻辑，不需要实际执行研发任务。
    子进程调用 embedded/run_task.sh 会触发 OpenCode 二进制执行，
    在测试环境中会超时（30秒），因此用 mock 替代。
    """
    with patch("deepagent_code_mode.CodeModeDispatcher.dispatch") as mock:
        mock.return_value = {
            "status": "completed",
            "task_id": "e2e-mock-001",
            "task": {"instruction": "", "task_type": "general_development"},
            "pid": None,
            "result": {"summary": "（E2E 测试模拟）任务已完成"},
            "message": "任务 [e2e-mock-001] 已派发给内置研发小组",
        }
        yield mock


# ============================================================
# 主测试：完整管线验证
# ============================================================
class TestHarnessE2E:
    """端到端集成测试：验证完整 Harness 流程"""

    def test_full_pipeline_with_hard_constraints(self):
        """
        完整流程测试：包含硬约束的复杂中文任务

        输入："帮我重构这个模块，不要删除任何文件，必须先备份"

        验证步骤：
        1. 场景路由识别为 CODE（研发类）
        2. 意图分类为 REFACTOR（重构）
        3. 硬约束提取到"不要删除任何文件"（禁止类）和"必须先备份"（必须类）
        4. PrefixManager 冻结前缀（含约束注入）
        5. ModelRouter 选择 Pro（重构任务高风险）
        6. ReasoningManager 剥离非 tool 轮的 reasoning
        7. 免疫系统审查约束是否被遵守
        """
        # ── 测试输入（包含硬约束的复杂中文任务）──
        instruction = "帮我重构这个模块，不要删除任何文件，必须先备份"

        # ── Step 1: 场景路由 ──
        # SceneRouter 使用关键词分类，"重构"属于 CODE 场景
        router = SceneRouter()
        scene_type = router.classify(instruction)
        assert scene_type == SceneType.CODE, \
            f"场景路由应为 CODE（研发类），实际为 {scene_type}"

        # ── Step 2: 意图分类 ──
        # IntentRouter 细粒度分类，"重构"属于 REFACTOR 意图
        intent_router = IntentRouter()
        intent, strategy = intent_router.classify_and_get_strategy(
            instruction, scene_type.value
        )
        assert intent == IntentType.REFACTOR, \
            f"意图应为 REFACTOR（重构），实际为 {intent}"
        # 重构任务的四维策略验证
        assert strategy.interview_depth == "deep", "重构需要深度面谈"
        assert strategy.plan_granularity == "detailed", "重构需要详细计划"
        assert strategy.review_standard == "deep", "重构需要深度审查"
        assert strategy.model_tier_hint == "pro_think", "重构建议使用 Pro Think"
        assert strategy.execution_mode == "plan_first", "重构应先规划再执行"

        # ── Step 3: 硬约束提取 ──
        # HardConstraintExtractor 使用正则提取，零 LLM 调用
        constraints = extract_hard_constraints(instruction)
        # 应提取到至少 2 条约束
        assert len(constraints) >= 2, \
            f"应提取到至少 2 条硬约束，实际 {len(constraints)} 条"

        # 验证禁止类约束（"不要删除任何文件"）
        prohibition_constraints = [
            c for c in constraints if c.constraint_type == "prohibition"
        ]
        assert len(prohibition_constraints) >= 1, "应至少有 1 条禁止类约束"
        has_delete_prohibition = any("删除" in c.text for c in prohibition_constraints)
        assert has_delete_prohibition, \
            f"应提取到包含'删除'的禁止约束，实际: {[c.text for c in prohibition_constraints]}"

        # 验证必须类约束（"必须先备份"）
        requirement_constraints = [
            c for c in constraints if c.constraint_type == "requirement"
        ]
        assert len(requirement_constraints) >= 1, "应至少有 1 条必须类约束"
        has_backup_requirement = any("备份" in c.text for c in requirement_constraints)
        assert has_backup_requirement, \
            f"应提取到包含'备份'的必须约束，实际: {[c.text for c in requirement_constraints]}"

        # ── Step 4: Prefix 冻结（含约束注入）──
        # PrefixManager 冻结 System Prompt，计算 SHA-256 指纹
        prefix_manager = PrefixManager()
        # 构建 System Prompt（模拟，包含约束格式化文本）
        constraint_text = format_constraints_for_prefix(constraints)
        system_prompt = f"你是 DeepAgent，一个 AI 研发助手。\n\n{constraint_text}"

        # 冻结前缀
        fingerprint = prefix_manager.freeze(system_prompt)
        assert prefix_manager.is_frozen, "前缀应已冻结"
        assert fingerprint != "unfrozen", "指纹不应为 'unfrozen'"
        assert len(fingerprint) == 16, f"指纹长度应为 16 字符，实际 {len(fingerprint)}"

        # 验证冻结的前缀包含约束文本
        frozen = prefix_manager.frozen_prefix
        assert "硬性约束" in frozen, "冻结前缀应包含硬性约束标记"
        assert "删除" in frozen, "冻结前缀应包含'删除'约束内容"
        assert "备份" in frozen, "冻结前缀应包含'备份'约束内容"
        # 验证约束格式（禁止类用 ❌，必须类用 ✅）
        assert "❌" in frozen, "禁止类约束应用 ❌ 标记"
        assert "✅" in frozen, "必须类约束应用 ✅ 标记"

        # 验证冻结后前缀不可变（Byte-Stable 原则）
        original_fingerprint = fingerprint
        # 再次调用 freeze 会覆盖（但在正常使用中不会发生）
        # 这里验证指纹一致性
        assert prefix_manager.fingerprint == original_fingerprint

        # ── Step 5: Flash/Pro 路由 ──
        # ModelRouter 根据 IntentRouter 的 route_context 做路由决策
        model_router = ModelRouter()
        route_context = intent_router.get_route_context(intent, strategy)
        # 重构任务 review_standard="deep" → risk_level="high"
        assert route_context["risk_level"] == "high", \
            f"重构任务风险等级应为 high，实际为 {route_context['risk_level']}"

        route_decision = model_router.route(route_context, instruction)
        # 高风险应升级到 Pro
        assert route_decision.tier in (ModelTier.PRO_THINK, ModelTier.PRO_MAX), \
            f"高风险任务应路由到 Pro，实际为 {route_decision.tier}"
        assert "deepseek-v4-pro" in route_decision.model_name, \
            f"应使用 Pro 模型，实际为 {route_decision.model_name}"
        assert route_decision.is_upgrade, "高风险任务应标记为升级"
        # 验证路由原因不为空（用于 diagnostics）
        assert route_decision.reason, "路由原因不应为空"

        # ── Step 6: Reasoning 剥离 ──
        # ReasoningManager 在 API 请求前过滤 reasoning_content
        reasoning_mgr = ReasoningManager(provider="deepseek")
        # 模拟带 reasoning 的 assistant 消息（非 tool 轮）
        messages_with_reasoning = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
            {
                "role": "assistant",
                "content": "我来帮你重构这个模块。",
                "reasoning": (
                    "用户要求重构模块，需要先分析现有代码结构。"
                    "约束：不能删除文件，必须先备份。"
                ),
                "tool_calls": None,
            },
        ]

        # 过滤非 tool 轮的 reasoning（DeepSeek 策略：非 tool 轮剥离）
        filtered = reasoning_mgr.filter_messages_for_api(
            messages_with_reasoning, is_tool_loop=False
        )

        # assistant 消息的 reasoning 应被剥离
        assistant_msg = filtered[2]
        assert "reasoning" not in assistant_msg, \
            "非 tool 轮的 reasoning 应被剥离"
        assert "reasoning_content" not in assistant_msg, \
            "reasoning_content 字段也应被剥离"
        # content 应保留
        assert assistant_msg["content"] == "我来帮你重构这个模块。", \
            "content 内容不应被修改"

        # 验证剥离统计
        summary = reasoning_mgr.get_summary()
        assert summary["total_reasoning_archived"] >= 1, \
            "应归档至少 1 条 reasoning"
        assert summary["total_chars_stripped"] > 0, \
            "应剥离了字符"
        assert summary["strip_policy"] is True, \
            "DeepSeek provider 应启用剥离策略"
        # 归档的 reasoning 仍可在本地访问
        archived = reasoning_mgr.get_archived_reasoning()
        assert len(archived) >= 1, "归档的 reasoning 应可访问"

        # ── Step 7: 免疫系统审查 ──
        # ImmuneSystem 在执行后检查硬约束是否被遵守
        immune = ImmuneSystem()

        # 场景 A：Agent 遵守了所有约束
        # - 提到"先备份"（满足必须类约束）
        # - 没有"已...删除任何文件"模式（未违反禁止类约束）
        good_output = (
            "已完成重构。已先备份了所有文件到 backup/ 目录，"
            "然后进行了代码重构，没有删除任何文件。"
        )
        result_good = immune.post_execution_review(constraints, good_output)
        # 合规输出应通过审查
        assert result_good.passed, \
            f"遵守约束的输出应通过免疫审查，违反: {result_good.violations}"
        assert result_good.compliance_rate == 1.0, "合规率应为 100%"
        assert len(result_good.violations) == 0, "不应有违反记录"

        # 场景 B：Agent 违反了约束
        # - "已经删除任何文件"触发禁止类约束检测
        # - 缺少"先备份"触发必须类约束检测
        bad_output = "已完成重构。已经删除任何文件，然后进行了代码重构。"
        result_bad = immune.post_execution_review(constraints, bad_output)
        # 违反约束应被检测到
        assert not result_bad.passed, \
            "违反约束的输出不应通过免疫审查"
        assert len(result_bad.violations) > 0, \
            "应检测到违反记录"
        assert result_bad.compliance_rate < 1.0, \
            "合规率应低于 100%"

        # 验证违反类型：应检测到禁止类违反
        has_prohibition_violation = any(
            v.constraint_type == "prohibition" for v in result_bad.violations
        )
        assert has_prohibition_violation, \
            "应检测到禁止类约束违反（删除文件）"

        # 验证生成了纠正性 Skill（免疫系统三环节闭环：自查→固化→外挂）
        assert len(result_bad.skills_generated) > 0, \
            "应生成纠正性 Skill 用于后续任务自动加载"
        # 验证 Skill 结构
        skill = result_bad.skills_generated[0]
        assert "name" in skill, "Skill 应有名称"
        assert "trigger" in skill, "Skill 应有触发条件"
        assert "check_description" in skill, "Skill 应有检查描述"
        assert skill["auto_generated"] is True, "应为自动生成的 Skill"

        # 验证免疫系统统计
        stats = immune.get_stats()
        assert stats["total_checks"] >= len(constraints), \
            "应检查了所有约束"
        assert stats["total_violations"] > 0, \
            "应记录了违反总数"

    def test_full_pipeline_route_with_mock(self, mock_dispatch):
        """
        验证 route() 完整路由链（mock 子进程）

        从 route_instruction() 入口出发，验证：
        场景路由 → route_to_code_mode → handle_development_request → dispatch
        整条链路不报错，且返回正确的结果结构。
        """
        instruction = "帮我重构这个模块，不要删除任何文件，必须先备份"

        # 调用快捷路由入口
        result = route_instruction(instruction)

        # 验证路由结果
        assert isinstance(result, dict), "路由结果应为字典"
        assert result["status"] == "completed", \
            f"任务状态应为 completed，实际为 {result.get('status')}"
        assert result.get("via_harness") is True, \
            "应标记为经由 Harness 路由"
        assert result.get("scene_type") == "code", \
            f"场景类型应为 code，实际为 {result.get('scene_type')}"
        assert result.get("scene") == "code", \
            "应包含 scene 字段"

        # 验证 dispatch 被调用
        mock_dispatch.assert_called_once_with(instruction)


# ============================================================
# 辅助测试：各阶段独立验证
# ============================================================
class TestPipelineStages:
    """管线各阶段独立验证（细化边界情况）"""

    def test_scene_router_non_code_passthrough(self):
        """非研发类指令应 passthrough，不进入 Code Mode"""
        router = SceneRouter()
        result = router.route("今天天气怎么样")
        assert result["status"] == "passthrough"
        assert result["scene_type"] == "other"

    def test_hard_constraint_double_negation_filtered(self):
        """
        硬约束提取边界：双重否定不应提取为约束

        "我不是说不要删除文件" 中 "不要" 前有 "不是说"，
        属于引述性否定，不是对 Agent 的约束。
        """
        extractor = HardConstraintExtractor()
        constraints = extractor.extract("我不是说不要删除文件")
        # "不要删除文件" 前有 "不是说"，应被过滤
        delete_constraints = [c for c in constraints if "删除" in c.text]
        assert len(delete_constraints) == 0, \
            f"双重否定'我不是说不要删除'不应提取为约束，实际: {[c.text for c in constraints]}"

    def test_hard_constraint_normal_extraction(self):
        """正常约束应被正确提取"""
        extractor = HardConstraintExtractor()
        constraints = extractor.extract("不要修改配置文件，必须使用中文回复")
        assert len(constraints) >= 2, \
            f"应提取到 2 条约束，实际 {len(constraints)} 条"

        # 验证禁止类
        prohibitions = [c for c in constraints if c.constraint_type == "prohibition"]
        assert len(prohibitions) >= 1, "应有禁止类约束"
        assert any("修改" in c.text or "配置" in c.text for c in prohibitions)

        # 验证必须类
        requirements = [c for c in constraints if c.constraint_type == "requirement"]
        assert len(requirements) >= 1, "应有必须类约束"
        assert any("中文" in c.text or "回复" in c.text for c in requirements)

    def test_model_router_flash_default(self):
        """低风险简单任务应路由到 Flash（Flash-first 策略）"""
        model_router = ModelRouter()
        # 低风险、无文件、无工具调用
        context = {
            "context_tokens": 1000,
            "active_files": 0,
            "risk_level": "low",
            "tool_calls_so_far": 0,
        }
        decision = model_router.route(context, "格式化这段代码")
        assert decision.tier == ModelTier.FLASH_NON_THINK, \
            f"简单任务应路由到 FLASH_NON_THINK，实际为 {decision.tier}"
        assert "flash" in decision.model_name, "应使用 Flash 模型"
        assert not decision.is_upgrade, "简单任务不应标记为升级"

    def test_model_router_pro_max_irreversible(self):
        """不可逆操作应路由到 Pro Max（最高优先级）"""
        model_router = ModelRouter()
        context = {
            "context_tokens": 1000,
            "risk_level": "irreversible",
        }
        decision = model_router.route(context, "删除生产数据库")
        assert decision.tier == ModelTier.PRO_MAX, \
            f"不可逆操作应路由到 PRO_MAX，实际为 {decision.tier}"
        assert decision.reasoning_effort == "max", "Pro Max 应使用 max reasoning effort"
        assert "deepseek-v4-pro" in decision.model_name, "应使用 Pro 模型"

    def test_model_router_pro_on_high_risk(self):
        """高风险操作应升级到 Pro Think"""
        model_router = ModelRouter()
        context = {
            "context_tokens": 5000,
            "risk_level": "high",
        }
        decision = model_router.route(context, "重构核心模块")
        assert decision.tier == ModelTier.PRO_THINK, \
            f"高风险应路由到 PRO_THINK，实际为 {decision.tier}"
        assert decision.is_upgrade, "高风险应标记为升级"

    def test_reasoning_tool_loop_kept(self):
        """
        Tool loop 中的 reasoning 应被保留（DeepSeek API 协议要求）

        DeepSeek API 要求 tool-calling 轮次保留 reasoning_content，
        否则多步工具调用会报 400 错误。
        """
        reasoning_mgr = ReasoningManager(provider="deepseek")
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "执行任务"},
            {
                "role": "assistant",
                "content": "我来执行",
                "reasoning": "需要先调用工具获取信息",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "terminal", "arguments": "{}"},
                    }
                ],
            },
        ]
        # 在 tool loop 中，reasoning 应保留
        filtered = reasoning_mgr.filter_messages_for_api(
            messages, is_tool_loop=True
        )
        assistant_msg = filtered[2]
        assert "reasoning" in assistant_msg, \
            "Tool loop 中的 reasoning 应被保留"
        assert assistant_msg["reasoning"] == "需要先调用工具获取信息", \
            "reasoning 内容不应被修改"

    def test_reasoning_anthropic_never_stripped(self):
        """
        Anthropic provider 的 thinking blocks 不应被剥离

        Anthropic 的 thinking blocks 有签名验证，剥离会导致 API 报错。
        """
        reasoning_mgr = ReasoningManager(provider="anthropic")
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "执行任务"},
            {
                "role": "assistant",
                "content": "我来执行",
                "reasoning": "思考过程...",
                "tool_calls": None,
            },
        ]
        # Anthropic 策略：不剥离非 tool reasoning
        filtered = reasoning_mgr.filter_messages_for_api(
            messages, is_tool_loop=False
        )
        assistant_msg = filtered[2]
        assert "reasoning" in assistant_msg, \
            "Anthropic 的 reasoning 不应被剥离"

    def test_immune_system_no_constraints(self):
        """无约束时应自动通过免疫审查"""
        immune = ImmuneSystem()
        result = immune.post_execution_review([], "任意输出")
        assert result.passed, "无约束时应自动通过"
        assert result.compliance_rate == 1.0
        assert len(result.violations) == 0

    def test_prefix_manager_mid_session_injection(self):
        """
        PrefixManager mid-session 变更注入

        前缀冻结后，mid-session 变更（如 memory 更新）不应修改前缀，
        而是通过 turn tail injection 注入到下一轮用户消息头部。
        """
        pm = PrefixManager()
        # 冻结前缀
        pm.freeze("初始 System Prompt")

        # 模拟 mid-session 变更
        pm.inject_mid_session_change("memory_update", "用户偏好已更新：喜欢简洁代码")
        pm.inject_mid_session_change("skill_added", "新技能已安装：python-linter")

        # 验证有待注入内容
        assert pm.has_pending_injections, "应有待注入的变更"

        # 消费 turn tail
        injection = pm.consume_turn_tail()
        assert "memory_update" in injection, "注入内容应包含 memory_update"
        assert "skill_added" in injection, "注入内容应包含 skill_added"
        assert "简洁代码" in injection, "注入内容应包含 memory 更新内容"

        # 消费后队列应清空
        assert not pm.has_pending_injections, "消费后应无待注入内容"
        assert pm.consume_turn_tail() == "", "再次消费应返回空字符串"

        # 前缀不应被修改（Byte-Stable 原则）
        assert pm.frozen_prefix == "初始 System Prompt", \
            "前缀不应被 mid-session 变更修改"
