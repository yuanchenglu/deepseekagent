---
name: harness-scene-router
description: "Harness 场景路由 — 自动分析用户指令场景类型（研发/研究/问答/规划/运维），研发类任务自动路由到 Code Mode 内置研发小组，其他任务由 Agent 直接处理。"
---

## Harness 场景路由

当用户发出指令时，先用场景路由器分析场景类型，再决定处理方式。

### 分类规则

| 场景 | 关键词 | 路由目标 |
|------|--------|----------|
| **code** (研发) | 实现、开发、修复bug、重构、写代码 | → CodeModeDispatcher |
| **research** (研究) | 调研、对比、分析、技术选型 | Agent 直接处理 |
| **query** (问答) | 什么是、怎么用、解释 | Agent 直接处理 |
| **planning** (规划) | 方案、设计、架构、规划 | Agent 直接处理 |
| **operation** (运维) | 部署、配置、安装、监控 | Agent 直接处理 |
| **other** (其他) | 无匹配 | Agent 直接处理 |

### 调用方式

```python
from deepagent_harness import route_instruction

result = route_instruction("用户的指令")
# 如果是研发类: result["status"] == "completed", result["via_harness"] == True
# 其他类:      result["status"] == "passthrough"
```

### 当前限制（MVP）

- 基于关键词分类，精确度约 85%。后续升级为小模型分类。
- 研发类指令路由到的 Code Mode 当前为 MVP 模拟模式，无真实代码变更。
- 非研发类指令仅提供路由建议，Agent 需自行决定是否采纳。
