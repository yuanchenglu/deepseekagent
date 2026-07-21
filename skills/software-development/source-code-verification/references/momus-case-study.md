# Momus 案例：不看源码的代价

## 背景

在创作 `Plan架构深度分析-Plan-Architecture-Deep-Analysis.md` 时，初版对 OMO 的 Momus 审查 Agent 做了如下描述：

> "Momus 按 4 个标准验证 Plan：Clarity / Verification / Context / Big Picture"
> "批准条件：≥80% 任务有清晰参考来源、≥90% 任务有具体验收标准"

## 源码验证结果

另一个 AI 会话通过逐文件对照 OMO 源码（`src/agents/momus.ts`，450 行），发现实际行为完全相反：

**Momus 的实际核心原则**：
> "APPROVAL BIAS: When in doubt, APPROVE. A plan that's 80% clear is good enough."
> "You are NOT here to nitpick every detail. You are NOT here to demand perfection."

Momus 是**偏向批准的实用主义审查员**，而非我们描述的"严格门禁"。

## 根因

1. 初版分析基于 OMO 的**概念文档**（docs/guide/orchestration.md），而非源码
2. 概念文档描述的是"理想设计"，源码实现的是"实用妥协"
3. 从文档推断代码行为 = 必然会犯错

## 教训

- 任何对产品功能的描述，必须对照源码
- 文档（README/docs）描述的是产品**声称**做了什么
- 源码描述的是产品**实际**做了什么
- 两者经常不一致
