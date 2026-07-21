# Integration Patch Audit — KunAgent 5-Patch Case Study

> 验证日期: 2026-06-24
> 仓库: KunAgent/Kun (https://github.com/KunAgent/Kun)
> 整合包路径: fangzhouzhongce/整合任务_DeepKun_20260623/整合包/DeepKun

## 基线

- 上游: https://github.com/KunAgent/Kun.git
- 本地 master 基于 v0.2.15 (8602476)
- 5 个本地 commit 未推送
- 每个 commit 声称修复了多个 GitHub Issue

## Patch 逐一审计

### Patch 1: `feat(mcp)` — 声称修复 #68、#168

```
27c0b6d feat(mcp): add MCP connection manager with state machine and config hot-reload
6 files changed, 936 insertions(+), 3 deletions(-)
```

- 新文件: mcp-config-file.ts (331行), mcp-connection-manager.ts (263行), mcp-runtime-manager.ts (140行)
- 改现有: mcp-tool-provider.ts (21行), events.ts (18行)
- **接入检查**: McpConnectionManager 被 McpRuntimeManager 引用; McpRuntimeManager 调用了 readMcpConfigFile → ✅ 已接入
- **Issue 匹配**:
  - #68 (MCP配置了但无法使用): 状态机+配置解析已覆盖，但核心问题可能是 npx PATH 或 IPC 路由
  - #168 (MCP状态不可观测): McpConnectionStateInfo + onStatusChange 回调已覆盖
- **结论**: 🟡 覆盖了问题领域，但 #68 的 root cause 可能没触及（IPC handler 路由修正已在 #77 中单独处理）

### Patch 2: `feat(provider)` — 声称修复 #237、#281、#299

```
9839ac9 feat(provider): add route registry, parameter validation, and stream timeout
7 files changed, 485 insertions(+)
```

- 新文件: model-request-validator.ts (173行), stream-timeout.ts (121行), route-registry.ts (137行)
- 改现有: router.ts, routes/index.ts, stream-timeout-telemetry.ts, kun-endpoints.ts
- **接入检查**:
  - RouteRegistry: 搜索整个项目，无任何引用 → ❌ 没接入
  - model-request-validator: 搜索整个项目，无任何引用 → ❌ 没接入
  - stream-timeout: 搜索整个项目，无任何引用 → ❌ 没接入
- **commit 自述**: "RouteRegistry is not yet wired into kun-runtime.ts runtimeClient" / "Stream timeout tracker is not yet integrated into compat-model-client.ts"
- **Issue 匹配**:
  - #237 (GUI /v1/tools 404): 路由表存在但无人使用，前端仍硬编码 /v1/tools
  - #281 (reasoning_effort 丢失): 校验框架存在但无人调用，实际请求路径未修改
  - #299 (流超时 45000ms): 超时追踪存在但未集成到流式调用路径
- **结论**: ❌ 三个都没修 — 全写了模块但全没接入

### Patch 3: `feat(tool-runtime)` — 声称修复 #149、#340、#238

```
0c4f927 feat(tool-runtime): add global skill loading, source tracking, and deep file search
6 files changed, 46 insertions(+), 11 deletions(-)
```

- **#149 (全局 skill 无法加载)**: skills-capability-config 新增 globalRoots 字段; discoverSkills() 新增全局目录扫描; 每个 LoadedSkill 带 source 标记
  - 接入检查: SkillRuntime 内部调用了 discoverSkills → ✅ 已接入
  - 但需要用户在配置中设置 globalRoots，不是自动发现 → 🟡 需配置
- **#340 (@深路径找不到文件)**: workspace-file-index.ts 改常量: depth 6→10, dirs 140→200, files 1200→1600
  - 改现有文件，直接生效 → ✅ 已修
- **#238 (环节卡死)**: commit 自述 "Deferred — requires integration into agent-loop.ts" → ❌ 没修
- **结论**: #340 ✅, #149 🟡, #238 ❌

### Patch 4: `feat(router)` — 声称修复 #364

```
8d875b2 feat(router): add complexity-aware model routing with quality assessment
4 files changed, 422 insertions(+)
```

- 新文件: complexity-estimator.ts (178行), routing-history.ts (86行)
- **接入检查**: 搜索整个 kun/src，无任何引用 → ❌ 没接入
- **commit 自述**: "ComplexityEstimator is not yet wired into auto-model-router.ts or agent-loop.ts"
- **Issue 匹配**:
  - #364 (自动选最便宜模型): 评估框架存在但无调用点，模型选择逻辑仍是"永远选最便宜的"
- **结论**: ❌ 没修

### Patch 5: `feat(context-compiler)` — 声称修复 #247、#155、#229

```
f2f71ac feat(context-compiler): add fact anchors, turn isolation, and stable prefix
6 files changed, 1897 insertions(+)
```

- 新文件: fact-anchor.ts (517行), turn-isolator.ts (274行), stable-prefix.ts (336行), context-compiler.ts (195行)
- 测试文件: context-compiler.test.ts (504行)
- **接入检查**: 搜索整个项目，context-compiler 目录下任何模块均无外部引用 → ❌ 没接入
- **Issue 匹配**:
  - #247 (上下文理解漂移): fact-anchor.ts 有完整的事实锚点提取逻辑，但未被 agent-loop 调用
  - #155 (上下文泄漏): turn-isolator.ts 有 turn 隔离逻辑，但未被编译管线调用
  - #229 (O(n²) 重处理): stable-prefix.ts 有前缀稳定性保证，但未被编译管线调用
- **结论**: ❌ 三个都没修 — 1897行代码 + 504行测试，全是独立的，没有被任何调用链引用

## 汇总

| Issue | 结论 | 原因 |
|-------|------|------|
| #68 | 🟡 | MCP 状态管理修了，但 root cause 可能未触及 |
| #168 | ✅ | 状态可观测性已暴露 |
| #237 | ❌ | RouteRegistry 无人引用 |
| #281 | ❌ | 参数校验框架无人引用 |
| #299 | ❌ | stream-timeout 未集成 |
| #149 | 🟡 | 加了 globalRoots 但需用户配置 |
| #340 | ✅ | 直接改常量，立即生效 |
| #238 | ❌ | 自述 deferred |
| #364 | ❌ | complexity-estimator 无人引用 |
| #247 | ❌ | fact-anchor 无人引用 |
| #155 | ❌ | turn-isolator 无人引用 |
| #229 | ❌ | stable-prefix 无人引用 |

**最终统计**: ✅ 2 真正修好 | 🟡 2 部分修 | ❌ 8 没修

## 关键教训

1. **代码行数 ≠ 修复程度** — 1897行的 context-compiler 全没修，6行的常量修改修了
2. **"写了新模块"不是"修了Issue"** — 新模块不被调用等于不存在
3. **commit 自述是最诚实的证据** — 开发者明确标注的 tech debt 比代码本身更可信
4. **搜索引用是最直接的验证** — 一条 grep 命令就能判断模块是否接入
5. **不要只搜一次就下结论** — 用户反问"你确定吗？"后，发现需要扩展搜索范围：不仅要搜文件名，还要搜类名、函数名、导出名；不仅要搜 kun/src/，还要搜 src/（前端）；不仅要搜内容，还要确认 barrel export 链是否完整
6. **核心编排器 0 行变更是最强反证** — agent-loop.ts 在 5 个 patch 中全部 0 行变更，比任何单个模块的接入检查都更有说服力。这是验证流程中应作为第一道关口的检查
