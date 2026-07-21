---
name: code-mode
description: "内置研发小组 — 将开发任务（编码、实现功能、修复bug等）派发给 Deep Agent 内置的隔离研发小组执行。当用户提出编程、开发、实现功能、写代码、修bug等指令时，使用此技能将任务路由到 Code Mode 调度器。"
---

## Code Mode — 内置研发小组

> ⚠️ **更新说明（2026-07-12）**：`deepagent_code_mode` 模块已不再维护。
> **禁止自己写代码。** 所有代码任务（含"改一行配置"）必须通过 OMO/OpenCode 执行。
> 详见 `product-rd-workflow` 的 `references/omo-handoff-pattern.md`。

### 铁律：禁止自己写代码

这条是硬约束，不是建议。当你遇到代码修改任务时：

```
❌ 错误：自己用 write_file/patch/terminal 改代码
✅ 正确：写手顺文档 → 交 OMO/OpenCode 执行 → 监控 → 验收
```

- 即使知道怎么修，即使只是改一行配置或加一个文件 — **不自己写**
- 手顺信息不够？更新 `.hermes/plans/` 手顺文档，重新交 OMO
- OMO 执行中发现问题？等它完成，分析输出，更新手顺再交下一轮
- 唯一例外：创建 `.hermes/plans/` 下的手顺文档本身

### 替代流程

1. 加载 `product-rd-workflow` skill
2. 编写 OMO 手顺文档到 `.hermes/plans/`（模板见 `references/omo-handoff-pattern.md`）
3. 一行指令启动 OMO
4. 监控 + 验收

### 触发关键词（不变）

- 实现 / 开发 / 写代码
- 修复 bug / bug fix
- 重构 / refactor
- 添加功能 / feature
- 创建 [文件/模块/函数]
- 搭建 / 构建 / 构造
- 前端 / 后端 / API
- 数据库 / 数据模型
- 测试 / unit test
