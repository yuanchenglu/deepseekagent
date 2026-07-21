# OMO Plan 级联缺陷：扁平清单 vs 依赖图

## 背景

用户袁成路在实际使用 OMO 时发现一个高频问题：执行中修改某一步的需求，后续步骤不受影响，仍按原始策略执行。他直觉怀疑 OMO 的 Plan 只是扁平清单，没有依赖图。

## 用户描述

> 假设它的计划总共有 8 个阶段。在执行完前两个阶段后，我发现第三阶段相关的需求有了变化，甚至是反向推翻了。结果它只改了第三阶段的计划，而第四到第七阶段都没有动，还是按照原来错误的策略在执行。这是让人非常抓狂的一个问题。

## 源码验证过程

### 第一步：定位核心类型

**文件**: `packages/boulder-state/src/types.ts` (L39-43)

```typescript
export interface PlanProgress {
  total: number
  completed: number
  isComplete: boolean
}
```

**发现**: 不存在 `step_id`、`parent_id`、`dependency_ids`、`association_strength`、`children` 等任何依赖图字段。Plan 被建模为扁平的 checkbox 清单。

### 第二步：追踪进度解析逻辑

**文件**: `packages/boulder-state/src/storage/plan-progress.ts` (L62-100)

`getStructuredPlanProgress()` 的核心逻辑：
- 扫描 `## TODOs` 和 `## Final Verification Wave` 两个 markdown section
- 正则匹配 `- [ ]` / `- [x]` checkbox 行
- 只统计 `total` 和 `completed` 两个数字
- **完全不解析步骤间的依赖关系**

### 第三步：搜索级联重规划代码路径

全局搜索模式: `plan.*modif|modif.*plan|change.*requirement|requirement.*change|cascade|mid.*execution`

**结果**: 0 个相关代码路径。不是实现得不好，而是架构层面没有"步骤间依赖关系"这个概念，因此不可能有级联修正。

### 第四步：验证 "update_plan" 的真实性质

**文件**: `src/agents/hephaestus/gpt-5-5.ts` (L98)

```
"Use update_plan for non-trivial work... Update the plan after each sub-task."
```

这是对 LLM 说的 **Prompt 指令**，不是运行时机制。系统不检查依赖关系、不追踪关联步骤、不会因一个步骤的需求变化而自动标记后续步骤。

## 根因

OMO 的 Plan 是一个**文档**（flat markdown），不是一张**图**（step dependency graph）。文档式 Plan 的优点是简单、人类可读，但在执行中修改需求时，没有结构化依赖关系的副作用是：系统不知道自己不知道。

## 这个缺陷暴露的更深问题

"update_plan" 只是 Prompt 指令而非代码机制，意味着：
- Prompt 指令在大上下文/多轮对话中会被遗忘
- 模型惰性导致某些 Prompt 指令不被执行
- 系统没有自查 Prompt 合规性的机制

这引出了 I-13（Prompt→Skill 自结晶），本质是为 Agent 建立免疫系统：识别不合规行为 → 自动生成 Skill（抗体）→ 固化约束。

## 教训

1. **Plan 的数据结构决定其行为上限**: 扁平清单 → 无级联修正；有向图 → 可级联修正
2. **Prompt 指令不是机制**: LLM 不执行 Prompt 不会报错，系统不知道 Prompt 被跳过了
3. **"Code + Prompt 混合架构"需要自增强闭环**: Prompt 覆盖灵活场景，但必须通过自查+Skill固化来保证 Prompt 被持续执行
