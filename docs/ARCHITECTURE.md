# DeepAgent 技术架构文档

## 1. 项目概述

DeepAgent 是一款基于 Hermes Agent 深度改造的「CEO 数字分身」产品，核心定位是：

**Model + Harness + Scene = Agent**

- **Model**：基座大语言模型（默认 DeepSeek V4，支持 Flash/Pro 双模型路由）
- **Harness**：深度优化层（本项目核心，最大化发挥模型物理特性）
- **Scene**：场景路由层（研发/研究/问答/规划等场景自动适配策略）

### 1.1 核心设计理念

DeepSeek V4 的物理特性决定了 Harness 层设计：

| 物理特性 | Harness 层适配 |
|---------|---------------|
| 1M 上下文窗口 | 五区上下文布局，sliding_window=128 近端锚点 |
| Byte-Stable Prefix Cache | System Prompt 冻结，变更注入尾部 |
| Flash/Pro 双模型 | 智能路由器，Flash-first Pro-on-checkpoint |
| Reasoning Content | Provider感知的消息过滤，tool轮保留非tool轮剥离 |
| CSA+HCA 混合注意力 | Task Anchor 近端注入，历史信息结构化 |

---

## 2. 系统分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  CLI (cli.py)  │  WebUI  │  Gateway (Telegram/Discord/...)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    核心 Agent 循环                           │
│                  run_agent.py (AIAgent)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              DeepAgent Harness 层（核心）             │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │ 场景+意图   │→ │  Prefix +    │→ │  模型路由  │ │   │
│  │  │ SceneRouter │  │  HardConst   │  │ ModelRouter│ │   │
│  │  │ IntentRouter│  │ PrefixManager│  │            │ │   │
│  │  └─────────────┘  └──────────────┘  └─────┬──────┘ │   │
│  │                                             │        │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────▼──────┐ │   │
│  │  │ 认知引擎    │  │ 免疫系统      │  │  Reasoning │ │   │
│  │  │ StarRoad    │  │ ImmuneSystem │  │ Manager    │ │   │
│  │  │ (L1/L2/L3)  │  │              │  │            │ │   │
│  │  └─────────────┘  └──────────────┘  └─────┬──────┘ │   │
│  │                                             │        │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────▼──────┐ │   │
│  │  │ 上下文布局  │  │ Tool Schema  │  │ 双向原语   │ │   │
│  │  │ Context     │  │ Stabilizer   │  │ Bidirect   │ │   │
│  │  │ Layout      │  │              │  │ Primitives │ │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                       工具系统                               │
│  tools/registry.py  │  terminal  │  file  │  web  │  delegate│
│  code_execution  │  browser  │  mcp  │  bidirectional meta  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Code Mode 隔离层                          │
│         deepagent_code_mode/  +  embedded/OpenCode           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块详解

### 3.1 Byte-Stable Prefix 架构 (`prefix_manager.py`)

**设计目标**：最大化 DeepSeek V4 Context Cache 命中率

**工作机制**：
1. Session 首次 System Prompt 构建后调用 `freeze()` 锁定前缀
2. 计算 SHA-256 指纹用于诊断 prefix drift
3. Session 期间任何变更（Memory更新、Skill新增）不修改前缀
4. 变更通过 `inject_mid_session_change()` 排队，下一轮 `consume_turn_tail()` 注入到用户消息头部

**缓存命中率提升**：
- 冻结前缀字节稳定 → 每轮都命中 prefix cache
- 输入 token 成本降低 ~60%（cache miss 价格是 hit 的 50-120 倍）
- 首 token 延迟大幅降低

### 3.2 硬约束前缀注入 (`hard_constraint.py`)

**设计目标**：确定性提取用户硬约束，物理隔离不参与压缩

**工作机制**：
- 纯正则提取（零 LLM 调用，确定性，零成本）
- 禁止类："不要/不能/禁止/严禁/千万别/..."
- 必须类："必须/一定要/务必/需要/确保/..."
- 误匹配过滤（疑问句、个人表述、否定前缀检测）
- 提取后注入 System Prompt 冻结前缀区

### 3.3 Flash/Pro 智能路由 (`model_router.py`)

**设计目标**：Flash-first 策略大幅降低成本，关键节点自动升级 Pro

**路由层级**：
| 层级 | 模型 | reasoning_effort | 适用场景 |
|------|------|-----------------|---------|
| FLASH_NON_THINK | deepseek-v4-flash | None | 简单格式化/翻译/摘要 |
| FLASH_THINK | deepseek-v4-flash | high | 常规任务（默认） |
| PRO_THINK | deepseek-v4-pro | high | 复杂/高风险/多文件任务 |
| PRO_MAX | deepseek-v4-pro | max | 不可逆操作/最终审查 |

**升级触发条件**（任一触发即升级）：
- 上下文 > 128K tokens
- 活跃文件 ≥ 5 个
- 依赖深度 ≥ 3
- 失败重试 ≥ 2 次
- 工具调用 ≥ 8 次
- 风险等级 = high/irreversible
- 最终审查 / 证据冲突

### 3.4 Reasoning Content 管理 (`reasoning_manager.py`)

**设计目标**：剥离无用 reasoning 节省 token，tool 轮保留符合协议

**Provider 策略差异**：
| Provider | 非tool轮剥离 | tool轮保留 | reasoning字段 |
|----------|-------------|-----------|--------------|
| DeepSeek | ✅ | ✅（必须） | reasoning_content |
| Anthropic | ❌（有签名） | ✅ | thinking |
| OpenAI | ✅ | ❌ | reasoning |

**截断策略**：保留首尾（开头分析+结尾结论），中间省略。

### 3.5 7+1 意图路由 (`intent_router.py`)

**设计目标**：任务开始前识别类型，自动绑定执行策略

**7+1 意图体系**：
| 意图 | 面谈深度 | 计划粒度 | 审查标准 | 模型提示 |
|------|---------|---------|---------|---------|
| Refactor 重构 | deep | detailed | deep | pro_think |
| New 新建 | standard | detailed | standard | flash_think |
| Medium 中等 | shallow | outline | standard | flash_think |
| Architecture 架构 | deep | okr_cascade | max | pro_max |
| Research 研究 | none | outline | shallow | flash_think |
| Simple 简单 | none | none | none | flash_non_think |
| Collaboration 协作 | standard | detailed | standard | pro_think |
| Spec-Driven | none | from_spec | from_spec | from_spec |

### 3.6 Agent 免疫系统 (`immune_system.py`)

**设计目标**：执行后自动审查硬约束遵守情况，违反时生成纠正性 Skill

**三环节闭环**：
1. **自查**：只读硬约束列表+最终产出物，逐条关键词匹配检查
2. **固化**：发现违反时生成纠正性 Skill
3. **外挂**：通过 PrefixManager 通知下一回合，Skill 可持久化

### 3.7 StarRoad 三层认知引擎 (`starroad_cognition.py`)

| 层级 | 内容 | 注入位置 | 稳定性 |
|------|------|---------|--------|
| L1 荣辱观 | 核心价值原则（安全、诚实、用户主权...） | 冻结前缀 | Session级稳定 |
| L2 方法论 | 按意图类型的最佳实践 | Turn tail注入 | 随意图变化 |
| L3 反省清单 | Checkpoint审查问题 | 独立审查Agent | 不进入主上下文 |

### 3.8 Context Layout 管理器 (`context_layout.py`)

**五区布局**（基于 Hybrid Attention = CSA + HCA, sliding_window=128）：
1. **stable_prefix**：冻结的 System Prompt
2. **task_anchor**：当前目标/步骤/约束摘要（近端便签）
3. **active_working**：当前轮次消息（sliding window内）
4. **compressed_history**：旧消息（压缩路径，Indexer检索）
5. **turn_tail**：L2方法论、mid-session变更

### 3.9 Tool Schema 稳定器 (`tool_schema_stabilizer.py`)

**设计目标**：工具 schema 跨轮次字节级稳定，确保 prefix cache 命中

**处理内容**：
- 按工具名字母序排序
- parameters.properties 按 key 排序
- required 列表排序
- 使用 sort_keys=True 的紧凑 JSON 规范化

### 3.10 双向 Agent 原语 (`bidirectional_primitives.py`)

**设计目标**：LLM ⇄ Harness 协同决策通道

四个元指令（作为 tool_call 实现）：
1. **need_more_context**：请求更多上下文（记忆/文件/历史）
2. **request_specialized_model**：请求升级到 Pro/Pro Max
3. **trigger_self_review**：触发 L3 反省审查
4. **propose_skill**：提议固化可复用模式为 Skill

---

## 4. 核心数据流

```
用户消息
    ↓
[SceneRouter.classify()] → CODE/RESEARCH/QUERY/PLANNING/OPERATION/OTHER
    ↓
[IntentRouter.classify()] → 7+1细分类 → 四维策略绑定
    ↓
[HardConstraintExtractor.extract()] → 提取硬约束
    ↓
[StarRoad.get_l1_prompt_section()] → L1荣辱观
[HardConstraint.format_for_prefix()] → 硬约束清单
    ↓
[PrefixManager.freeze()] → 冻结System Prompt（仅首次）
    ↓
每轮循环：
    ├─ [ModelRouter.route()] → Flash/Pro决策 + reason记录
    ├─ [StarRoad.get_l2_prompt_section()] → 按意图注入方法论
    ├─ [PrefixManager.consume_turn_tail()] → mid-session变更
    ├─ [ContextLayout.set_task_context() + inject_anchor_to_messages()]
    │  → Task Anchor注入到近端窗口
    ├─ [stabilize_tool_schemas()] → 工具schema字节稳定
    ├─ [ReasoningManager.filter_messages_for_api()] → 剥离无用reasoning
    ├─ 调用API
    ├─ [处理工具调用/双向原语]
    │   └─ 是元指令? → BidirectionalPrimitives.handle()
    └─ 返回结果前:
        [ImmuneSystem.post_execution_review()] → 约束违反审查
```

---

## 5. 关键设计决策

1. **纯正则硬约束提取而非 LLM 提取**：零成本、确定性、结果稳定
2. **Byte-Stable Prefix 而非动态重建 System Prompt**：最大化 cache 命中率
3. **Flash-first 而非默认 Pro**：成本降低 ~70%，关键节点才升级
4. **Reasoning 按 Provider 策略差异化处理**：DeepSeek可剥离、Anthropic有签名不能动
5. **免疫系统 MVP 用关键词匹配而非 spawn 审查 Agent**：轻量，可后续升级
6. **双向原语作为 tool_call 而非特殊消息类型**：复用现有工具调用机制，Agent自然使用

---

## 6. 模块依赖关系

```
run_agent.py (AIAgent)
    ├── deepagent_harness.* (全部Harness模块)
    │     ├── prefix_manager.py ← (被所有需要注入变更的模块依赖)
    │     ├── hard_constraint.py → immune_system.py
    │     ├── model_router.py ← bidirectional_primitives.py
    │     ├── reasoning_manager.py
    │     ├── intent_router.py → model_router.py (model_tier_hint)
    │     ├── immune_system.py
    │     ├── starroad_cognition.py ← bidirectional_primitives.py
    │     ├── context_layout.py
    │     ├── tool_schema_stabilizer.py
    │     ├── bidirectional_primitives.py → prefix_manager, model_router, starroad
    │     └── scene_router.py → intent_router.py (route_enhanced)
    ├── tools/registry.py
    ├── agent/prompt_builder.py
    └── deepagent_code_mode/
```
