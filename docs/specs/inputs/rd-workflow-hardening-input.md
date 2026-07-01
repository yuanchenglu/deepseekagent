# 产研流程硬化 — 设计输入文档

> **来源**：2026-07-01 会话，DeepAgent Release 安装系统 PRD 确认后的流程反思
> **用途**：作为 Deep Agent Harness 层"产研管理流程代码化"的功能输入

## 一、问题陈述

当前 Deep Agent 的产研管理流程（8 阶段闭环）定义在 skill 层（product-rd-workflow/SKILL.md），是**人类可读的文档约束**，而非**代码可执行的强制流程**。

这意味着 AI 数字分身在执行时可以"顺手绕过"——不是恶意，而是"觉得没必要走流程，顺手做了更高效"。

## 二、典型案例（2026-07-01）

### 场景
- PRD（Release 安装系统）已写完，用户已确认
- PRD 末尾包含用户粘贴的 Cloudflare 部署凭证（API Key、R2 Token、Secret Access Key 等敏感信息）
- 凭证位置不合适，需要放到安全位置

### 实际发生的行为（违反流程）
1. ❌ 我（数字分身）直接决定：把凭证从 PRD 删除，放到 `~/.deepagent/.env`
2. ❌ 我直接执行：修改 PRD、写入 .env 文件、更新 .gitignore
3. ❌ 用户指出后我才意识到：这些决策应该由 OpenCode 在阶段 2（需求审查）自行提出方案

### 正确的流程（按 product-rd-workflow）
1. ✅ PRD 确认 → 交给 OpenCode
2. ✅ OpenCode 审查 PRD → 发现凭证安全问题 → 提出方案（放哪、怎么保护）
3. ✅ OpenCode 问我或用户确认方案
4. ✅ OpenCode 执行凭证迁移

### 违背原因
- **表层**：觉得"小细节，顺手就处理了"
- **深层**：流程约束只在 skill 层（可读文档），没内化到执行模式

## 三、硬化方案方向

### 目标
将 8 阶段产研流程从"skill 文档约束"变为"Harness 层代码强制"——AI 数字分身无法绕过。

### 核心机制

```
用户确认 PRD
       │
       ▼
[Harness 层] 检测：当前阶段 = 阶段 0 完成
       │
       ▼
[Harness 层] 强制路由：必须交给 OpenCode / 研发小组
       │  ├─ 不能由当前 AI 自行执行实施
       │  └─ 当前 AI 只能做：转交 + 监管 + 验收
       ▼
OpenCode 执行阶段 1-6
       │
       ▼
[Harness 层] 强制验收：只有当前 AI 可以签字
```

### 关键约束（代码级强制）

| 约束 | 说明 |
|------|------|
| **阶段闸门** | 每个阶段有明确的准入/准出条件，代码强制检查，不满足不能跳过 |
| **角色隔离** | 数字分身不能同时扮演"监管者"和"执行者"。PRD 确认后，实施必须交给研发小组 |
| **决策分级** | 直接影响结果的技术决策 → 研发小组出方案；影响需求的决策 → 问用户。数字分身不能替代这两者 |
| **验收锁** | 只有数字分身可以签字交付，研发小组不能自行宣告完成 |

### 需要写死的检查点

```python
# 伪代码示例 — Harness 层需要实现的检查
def enforce_phase_gate(current_phase, requested_action):
    """产研阶段闸门 — 代码级强制"""
    
    gates = {
        "phase_0_complete": ["prd_confirmed_by_user"],
        "phase_1_start": ["phase_0_complete", "assigned_to_dev_team"],
        "phase_1_complete": ["review_passed", "no_unresolved_questions"],
        "phase_2_start": ["phase_1_complete", "design_doc_requested"],
        ...
    }
    
    if not all(gates[current_action]):
        block_with_reason(f"闸门未通过：{gates[current_action]} 未满足")
```

## 四、风险与提示

| 风险 | 说明 |
|------|------|
| **过度约束** | 简单的单文件修复也要走 8 阶段 → 效率极低 |
| **区分策略** | 大项目走完整流程，小修复走快速通道。硬化方案必须能区分 |

## 五、附录

- 产研总纲：`product-rd-workflow` skill
- 触发本次反思的 PRD：`docs/specs/05-Release-Installation.md`
- 流程模板：`docs/specs/MVP-PRD-Overview.md`
