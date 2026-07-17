# DeepAgent 需求文档

## 1. 产品定位

DeepAgent 是一款「CEO 数字分身」产品，基于 Hermes Agent 深度 Fork 和改造，为 DeepSeek V4 模型量身定制的 Harness 层优化。

**核心公式**：Model + Harness + Scene = Agent
- Model 决定下限
- Harness 层深度优化决定上限
- Scene 场景路由让不同任务自动适配策略

### 1.1 用户角色

| 角色 | 场景 |
|------|------|
| 董事长（用户） | 用自然语言下达指令：写代码、做研究、分析数据、部署运维 |
| CEO数字分身（DeepAgent） | 理解意图、路由任务、协调研发小组、保证质量、控制成本 |
| 内置研发小组（Code Mode） | 隔离环境中执行研发任务，独立完成代码编写/测试/调试 |

---

## 2. 功能需求

### 2.1 Harness 层八大核心模块（32期要求）

#### 模块一：Byte-Stable Prefix 架构
- **需求**：System Prompt 在 session 首次构建后冻结，后续变更不修改前缀字节
- **验收标准**：
  - [x] `freeze()` 方法锁定System Prompt，返回SHA-256指纹
  - [x] mid-session变更（Memory、Skill等）不修改前缀
  - [x] 变更通过`inject_mid_session_change()`排队，下轮注入用户消息头部
  - [x] `consume_turn_tail()`消费后清空队列，不重复注入
  - [x] 提供fingerprint诊断prefix drift

#### 模块二：KV Cache 硬约束前缀注入
- **需求**：从用户输入确定性提取"不能/必须/禁止"等硬约束，注入冻结前缀
- **验收标准**：
  - [x] 纯正则提取（零LLM调用，确定性）
  - [x] 禁止类/必须类分类标记
  - [x] 误匹配过滤（疑问句、个人表述、否定前缀）
  - [x] 格式化为Markdown嵌入System Prompt
  - [x] 关键词提取供免疫系统检查

#### 模块三：Flash/Pro 智能路由
- **需求**：默认Flash，高风险/复杂任务自动升级Pro，每次路由记录原因
- **验收标准**：
  - [x] 四级模型层级（FLASH_NON_THINK/FLASH_THINK/PRO_THINK/PRO_MAX）
  - [x] 9种升级触发条件（大上下文、多文件、失败重试、高风险等）
  - [x] 简单任务（格式化/翻译/摘要）走NON-THINK
  - [x] `force_upgrade()`/`force_pro_max()`外部强制升级接口
  - [x] route_log记录所有决策用于diagnostics

#### 模块四：Reasoning Content 管理
- **需求**：reasoning内容按Provider策略决定保留/剥离，不浪费token
- **验收标准**：
  - [x] DeepSeek：非tool轮剥离，tool轮保留（协议要求）
  - [x] Anthropic：不剥离（thinking blocks有签名）
  - [x] OpenAI：客户端不需要回传
  - [x] 本地归档完整reasoning供display/archive
  - [x] 超长reasoning截断保留首尾
  - [x] 操作副本不修改原始消息

#### 模块五：7+1 意图路由
- **需求**：8种任务类型自动识别，每种绑定四维执行策略
- **验收标准**：
  - [x] 7种基础意图：Refactor/New/Medium/Architecture/Research/Simple/Collaboration
  - [x] +1元机制：Spec-Driven
  - [x] 四维策略：面谈深度/计划粒度/审查标准/执行模式
  - [x] model_tier_hint传给ModelRouter
  - [x] toolsets推荐传给工具系统
  - [x] 与scene_router协同（粗分类→细分类）

#### 模块六：Agent 免疫系统
- **需求**：执行后自动检查硬约束遵守情况，违反时生成纠正性Skill
- **验收标准**：
  - [x] post_execution_review()逐条检查硬约束
  - [x] 禁止类违反检测（关键词出现）
  - [x] 必须类遗漏检测（关键词缺失）
  - [x] 生成纠正性Skill条目
  - [x] violation_log记录违反历史
  - [x] compliance_rate合规率统计

#### 模块七：双向 Agent 原语
- **需求**：LLM能主动向Harness发送四个元指令
- **验收标准**：
  - [x] need_more_context：请求更多上下文（记忆/文件/历史）
  - [x] request_specialized_model：请求升级Pro/Max
  - [x] trigger_self_review：触发L3反省审查
  - [x] propose_skill：提议固化可复用模式
  - [x] 作为tool_call实现，复用现有工具机制
  - [x] 处理结果返回给LLM

#### 模块八：StarRoad 三层认知引擎
- **需求**：L1荣辱观+L2方法论+L3三省吾身
- **验收标准**：
  - [x] L1核心价值原则（安全、诚实、用户主权等7条）
  - [x] L2按意图类型的方法论最佳实践
  - [x] L3反省清单（8个检查问题）
  - [x] L1注入冻结前缀（稳定）
  - [x] L2注入turn tail（随意图变化）
  - [x] L3给独立审查Agent（不进入主上下文）
  - [x] MEMORY_TIERS记忆分层标签定义

#### 模块九：Context Layout 管理器（配套）
- **需求**：基于sliding_window=128管理消息布局
- **验收标准**：
  - [x] 五区布局定义（stable_prefix/task_anchor/active_working/compressed_history/turn_tail）
  - [x] Task Anchor注入近端窗口（当前目标/步骤/约束/活跃文件）
  - [x] 不重复注入检测
  - [x] zone token估算diagnostics
  - [x] proximity警告（长回复可能挤出关键信息）

#### 模块十：Tool Schema 稳定器（配套）
- **需求**：工具schema跨轮次字节级稳定，最大化cache命中
- **验收标准**：
  - [x] 按工具名字母序排序
  - [x] parameters.properties递归规范化
  - [x] required列表排序
  - [x] fingerprint指纹诊断schema变化
  - [x] 深拷贝不修改原始列表

---

### 2.2 场景路由（Scene Router）
- **需求**：粗粒度分类用户指令，研发类自动路由Code Mode
- **验收标准**：
  - [x] 6种场景：CODE/RESEARCH/QUERY/PLANNING/OPERATION/OTHER
  - [x] 关键词分类规则
  - [x] CODE场景自动dispatch到Code Mode
  - [x] route_enhanced()三路由层增强版

### 2.3 Code Mode 隔离研发小组
- **需求**：研发任务在隔离环境执行，不污染主环境
- **验收标准**：
  - [x] Dispatcher派发任务到embedded/隔离环境
  - [x] MVP模式下返回completed状态
  - [x] 不读取用户本地配置
  - [x] 任务ID追踪

---

## 3. 非功能需求

### 3.1 性能要求
- 硬约束提取 < 1ms（纯正则）
- 路由决策 < 1ms
- 单元测试全部通过：`pytest tests/test_harness_*.py` 100% pass
- 不引入新的第三方依赖

### 3.2 质量要求
- 所有新增代码有简体中文注释
- 每个模块有对应的单元测试（覆盖率>80%）
- 技术文档完整（ARCHITECTURE/MAINTENANCE/REQUIREMENTS）
- Bug发现→记录→修复→验证闭环

### 3.3 兼容性要求
- 不破坏现有~3000个pytest测试
- 所有新功能在try-except后，导入失败时优雅降级
- 使用`get_hermes_home()`而非硬编码路径

---

## 4. 验收标准汇总

| # | 验收项 | 状态 | 证据 |
|---|--------|------|------|
| 1 | Byte-Stable Prefix (freeze/inject/consume) | ✅ | prefix_manager.py + 11个测试 |
| 2 | 硬约束提取（纯正则+分类+去重+误匹配过滤） | ✅ | hard_constraint.py + 15个测试 |
| 3 | Flash/Pro智能路由（4层级+9升级条件+reason记录） | ✅ | model_router.py + 15个测试 |
| 4 | Reasoning管理（Provider策略+归档+截断） | ✅ | reasoning_manager.py + 11个测试 |
| 5 | 7+1意图路由（8类型+四维策略+model_tier_hint） | ✅ | intent_router.py + 12个测试 |
| 6 | Agent免疫系统（事后审查+Skill固化） | ✅ | immune_system.py + 4个测试 |
| 7 | 双向Agent原语（4个元指令tool_call） | ✅ | bidirectional_primitives.py + 10个测试 |
| 8 | StarRoad三层认知（L1/L2/L3+MEMORY_TIERS） | ✅ | starroad_cognition.py + 6个测试 |
| 9 | Context Layout（五区布局+Anchor+不重复注入） | ✅ | context_layout.py + 7个测试 |
| 10 | Tool Schema稳定器（排序+规范化+指纹） | ✅ | tool_schema_stabilizer.py + 7个测试 |
| 11 | 场景路由（6场景+Code Mode dispatch+三路由层） | ✅ | scene_router.py + 15个测试 |
| 12 | 所有Harness模块单元测试通过 | ✅ | 145个测试全部pass |
| 13 | 所有函数有中文注释 | ✅ | grep抽查 |
| 14 | 技术文档完整（ARCHITECTURE/MAINTENANCE/REQUIREMENTS） | ✅ | docs/ |
| 15 | README更新说明Harness架构 | ⏳ | README.md |
