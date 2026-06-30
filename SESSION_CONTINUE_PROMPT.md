# DeepAgent 项目续接提示词

## 项目概况

项目名称 **DeepAgent**，位于 `~/Code/DeepAgent/`。
这是从 Hermes Agent v0.17.0 fork 出来的独立项目，目标是实现 **StarRoad Cognition（星辰路认知法）**——在 Hermes 基础上增加三层认知引擎架构。

## 已完成的部分

- [x] `~/Code/DeepAgent/` 已创建，Hermes 源码已复制并初始化 git
- [x] `STARROAD_COARSE_PLAN.md` — 粗框架方案（含三层认知框架定义、5 个新模块接口设计、3 个已有文件修改方案、三路由层架构图、完整认知循环流程）
- [x] `STARROAD_IMPL_PLAN.md` — OpenCode 审评后出的详细实施计划（2514 行）

## 当前状态：等待用户审阅 OpenCode 的详细计划

OpenCode 读取了 1500+ 行 Hermes 源码，对粗方案做了审评，发现了 **9 个问题**（5 高 + 2 中 + 2 低），然后出了一份 10 个任务、2514 行的详细实施计划（在 `STARROAD_IMPL_PLAN.md` 中）。

## 你要做的事

### 第一步：读关键文件
1. `~/Code/DeepAgent/STARROAD_COARSE_PLAN.md` — 粗框架方案，理解三层认知框架和整体架构
2. `~/Code/DeepAgent/STARROAD_IMPL_PLAN.md` — OpenCode 出的详细实施计划，重点是**一、粗方案审评结果**部分（9 个问题的修复方案）和**二、详细实施任务**

### 第二步：等用户确认
用户会看这两份文件，可能有修改意见。你要：
1. 听用户对星宸路三框架方案和计划的反馈
2. 如果用户有修改意见，记下来
3. 把修改意见整理好后重新发给 OpenCode 讨论
4. OpenCode 出更新后的详细计划 → 用户再确认
5. 确认后，让 OpenCode 按详细计划直接执行（`opencode run` 模式）

### 第三步：执行阶段

OpenCode 的计划把实现分为 5 个阶段、10 个任务：

**阶段 1：创建 5 个新模块（可完全并行）**
- Task 1: `agent/cognitive_gate.py` — 三层认知评估器（约 280 行代码 + 180 行测试）
- Task 2: `agent/memory_index.py` — Memory 嵌套索引（约 220 行代码 + 150 行测试）
- Task 3: `agent/plan_tracker.py` — Plan 状态机（约 180 行代码 + 120 行测试）
- Task 4: `agent/expert_matcher.py` — 专家匹配器（约 190 行代码 + 140 行测试）
- Task 5: `agent/router.py` — 语义路由总控（约 80 行代码 + 90 行测试）

**阶段 2：修改 3 个已有文件（可并行）**
- Task 6: `agent/prompt_builder.py` — 注入认知循环引导 + Memory 导航段（约 15 行修改）
- Task 7: `agent/context_compressor.py` — KV Cache 围栏保护（约 10 行修改）
- Task 8: `tools/memory_tool.py` — 增加 `read_nested` 动作（约 10 行修改）

**阶段 3：集成到 agent loop（串行）**
- Task 9: `run_agent.py` — 插入 Pre-turn/Post-turn hook points（约 80 行修改）

**阶段 4：数据文件（串行）**
- Task 10: 创建 `MAP.md` + 更新 `SOUL.md`（约 20 行）

**阶段 5：验证**
- 跑 pytest 验证新模块的单元测试
- 跑已有的测试确保没破坏现有功能
- 做集成测试（启动 Hermes 发送测试消息看三层评估日志）

### 执行方式
- 所有编码任务通过 `opencode run` 执行，不用 PTY/TUI
- 模型选择：实现任务用 `opencode/deepseek-v4-flash-free`（便宜），复杂架构决策用 `clawadmin/deepseek-v4-flash`
- 每个 task 产出一个 commit，commit 信息用双语格式
- 每完成一个 task 跑 pytest 验证
- 所有代码写中文注释

### 关键注意事项
- 所有新模块不替换现有代码，通过 hook points 插入
- Memory Index 只存导航指引（1-2KB），深度内容存子文档按需加载
- ExpertMatcher 使用两级缓存：registry（元数据）+ prompt（内容），避免每次扫 232 个文件
- CognitiveGate 只在 text response 后做全面评估，tool call 后只做轻量 L1 检查
- KV Cache 保护使用 `-----COGNITIVE_INDEX_START-----`/`-----COGNITIVE_INDEX_END-----` 围栏标记
- PlanTracker 是 todo 的上层抽象，不管理原子任务细节
- 所有文件路径使用 `get_hermes_home()` 而非硬编码 `~/.hermes`
- 修改已有文件时用 `# === DeepAgent: StarRoad Cognition ===` 标记

## 参考路径

| 资源 | 路径 |
|------|------|
| 项目根目录 | `~/Code/DeepAgent/` |
| 粗框架方案 | `~/Code/DeepAgent/STARROAD_COARSE_PLAN.md` |
| OpenCode 详细计划 | `~/Code/DeepAgent/STARROAD_IMPL_PLAN.md` |
| The Agency 认知框架文档 | `~/.hermes/skills/autonomous-ai-agents/the-agency/references/cognitive-workflow.md` |
| The Agency 专家库 | `~/.config/opencode/agents/`（232 个 .md 文件） |
