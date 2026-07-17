# DeepAgent Harness

**Harness 层核心实现** — DeepSeek V4 深度适配。

基于公式：`Model + Harness + Scene = Agent`

- Model 决定下限
- **Harness 层决定上限**

## 模块总览

| 模块 | 文件 | 职责 |
|------|------|------|
| 场景路由 | `scene_router.py` | 用户指令分类，研发→Code Mode；增强版支持三路由层 |
| Byte-Stable Prefix | `prefix_manager.py` | System Prompt 字节级冻结，变更通过 turn tail 注入 |
| 硬约束注入 | `hard_constraint.py` | 确定性正则提取"禁止/必须"约束，注入冻结前缀区 |
| Flash/Pro 路由 | `model_router.py` | Flash-first 默认策略，8种升级条件触发 Pro/Pro Max |
| Reasoning 管理 | `reasoning_manager.py` | Provider 感知的 reasoning 过滤（DeepSeek/Anthropic/OpenAI） |
| 7+1 意图路由 | `intent_router.py` | 8种意图类型（Refactor/New/Architecture等）→ 四维策略绑定 |
| 免疫系统 | `immune_system.py` | 执行后约束遵守审查，发现违反自动生成纠正 Skill |
| StarRoad 认知 | `starroad_cognition.py` | 三层认知：L1荣辱观/L2方法论/L3反省 |
| Context Layout | `context_layout.py` | V4 Hybrid Attention 物理适配，sliding_window=128 近端锚点 |
| Tool Schema 稳定器 | `tool_schema_stabilizer.py` | Tool schema 字节级确定性排序，最大化 cache 命中率 |

## 数据流

```
用户输入
  → scene_router.classify()         # 粗分类：CODE/RESEARCH/QUERY/...
  → intent_router.classify()        # 细分类：Refactor/Simple/Architecture/...
  → hard_constraint.extract()       # 提取禁止/必须类硬约束
  → prompt_builder 组装 System Prompt
  → prefix_manager.freeze()         # 冻结前缀（SHA-256 指纹）
  → StarRoad L1 荣辱观（前缀追加）
  → [主循环]
      → StarRoad L2 方法论（turn tail 注入）
      → reasoning_manager.filter()  # 剥离非tool轮reasoning
      → model_router.route()        # Flash/Pro 决策
      → API 调用
      → tool 执行
  → immune_system.review()          # 执行后合规审查
  → 返回结果 + harness diagnostics
```

## 快速开始

```python
from deepagent_harness import (
    PrefixManager, extract_hard_constraints, ModelRouter,
    ReasoningManager, IntentRouter, ImmuneSystem, StarRoadCognition
)

# 硬约束提取
constraints = extract_hard_constraints("必须使用中文，禁止删除数据库")
# → [HardConstraint("必须使用中文", requirement), HardConstraint("禁止删除数据库", prohibition)]

# Flash/Pro 路由
router = ModelRouter({"enabled": True})
decision = router.route({"risk_level": "irreversible"}, "删除生产数据库")
# → tier=PRO_MAX

# 意图路由
ir = IntentRouter()
intent, strategy = ir.classify_and_get_strategy("帮我重构登录模块", "code")
# → intent=refactor, model_hint=pro_think
```

## 配置参考

ModelRouter 支持通过 config.yaml 的 `deepseek_routing` 段配置：

```yaml
deepseek_routing:
  enabled: true
  flash_model: deepseek-v4-flash
  pro_model: deepseek-v4-pro
  flash_first: true
```

详见 `docs/specs/04-Engineering-and-Harness.md`。