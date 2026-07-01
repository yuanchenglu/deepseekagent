# DeepAgent Harness

**Harness 层核心实现** — 场景路由、组织融合、记忆增强。

基于公式：`Modern + Harness + Scene = Agent`

- Modern 决定下限
- Harness 层决定上限

## 模块

### scene_router.py — 场景路由器

用户指令自动分类，研发类→Code Mode，其他→ Agent 直处理。

```
指令 → SceneRouter.classify() → SceneType
  ├─ CODE     → route_to_code_mode() → 内置研发小组
  ├─ RESEARCH → Agent 直接处理
  ├─ QUERY    → Agent 直接处理
  ├─ PLANNING → Agent 直接处理（可强化）
  └─ OTHER    → Agent 直接处理
```

### 后续扩展

- `memory_augmenter.py` — 记忆增强（基于 Honcho 或自有系统）
- `prompt_optimizer.py` — 针对 DeepSeek 模型的 prompt 优化
- `skill_learner.py` — 自动从 Code Mode 执行中提炼新技能

详见 `docs/specs/04-Engineering-and-Harness.md`。