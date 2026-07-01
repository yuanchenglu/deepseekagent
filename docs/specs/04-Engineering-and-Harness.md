# 04 - 工程质量与 Harness 层优化（Engineering and Harness）

**版本**：v0.1  
**日期**：2026-07-01  
**状态**：草案  
**关联 Overview**：MVP-PRD-Overview.md

---

## 1. 问题背景

当前 Deep Agent 作为 DeepAgent 的深度 fork，积累了大量本地修改。

在追求“Modern + Harness + Scene = Agent”的同时，必须保证：

- 基础工程质量不崩
- Harness 层（场景对接、记忆、技能、组织融合）的深度优化真正落地

MVP 阶段前三项打牢后，本方向进入系统性建设。

---

## 2. 目标

1. 建立可持续的工程质量体系（测试、CI、文档）。
2. 把已有的 Harness 研究（14 篇文章洞察）转化为实际代码与配置。
3. 实现 DeepSeek V4 Flash / PRO 在真实场景下的性能跃升。
4. 保持与上游 DeepAgent 的兼容性，便于持续吸收创新。

---

## 3. Harness 层优化重点

基于用户过往 Harness 深度研究，MVP 阶段优先落地：

### 3.1 场景（Scene）优先
- 任务分类：研发 vs 非研发
- 自动路由到 Code Mode 或直接 Agent 处理
- 场景记忆（用户偏好、项目上下文）注入

### 3.2 组织融合（Model + Harness 协作）
- Deep Agent 作为 CEO 层
- 内置 OpenCode 作为专业研发子团队
- 清晰的分工协议（指令 → 任务 → 结果 → 总结）

### 3.3 记忆与技能闭环
- 强化现有 memory + skills 系统
- 自动从 Code Mode 执行中提炼新技能
- 跨会话 FTS5 + 向量化召回

### 3.4 提示与上下文工程
- 针对 DeepSeek 模型的优化 system prompt
- 动态上下文压缩 + 缓存策略

---

## 4. 工程质量体系

### 4.1 测试
- 保留并扩展现有 pytest 套件
- 增加 Code Mode 集成测试（隔离环境）
- 关键路径的 E2E（使用 terminal + browser tools）

### 4.2 CI / 自动化
- GitHub Actions：lint + test + build
- 每周上游同步自动触发 smoke test
- 品牌替换后自动验证

### 4.3 文档与可维护性
- 所有新功能必须配 AGENTS.md 风格指导
- PR 必须包含中英双语 commit
- 关键模块加中文注释（按用户要求）

### 4.4 稳定性
- 错误恢复、进程隔离、资源限制
- 长期运行的 gateway + cron 监控

---

## 5. 阶段划分

**MVP 阶段 4**：
- [ ] 完成品牌替换后的全量测试
- [ ] 建立上游同步 + CI 流水线
- [ ] 落地 2-3 个核心 Harness 优化（场景路由 + 内置团队协议 + 记忆增强）

**后续**：
- 性能 benchmark（真实任务完成度）
- 更多场景适配（产品、运营、研究等）
- 发布 DeepAgent 专用模型微调数据（如果条件成熟）

---

## 6. 验收标准

- 代码库干净（无大量 DeepAgent 残留）
- 新功能有测试覆盖
- Deep Agent 在典型研发任务上的表现明显优于裸 DeepSeek + 普通 agent
- 每周同步流程顺畅，无重大回归

---

## 7. 后续行动

1. 扫描现有测试覆盖率，补齐关键路径。
2. 实现场景路由 skill / 路由器。
3. 把用户已有的 Harness 分析文档转化为具体 prompt 模板和配置。
4. 建立 benchmark 任务集（内部使用）。

**备注**：本方向是长期竞争力来源，MVP 阶段以“打基础 + 验证核心公式”为主。