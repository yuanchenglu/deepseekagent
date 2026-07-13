# DeepAgent 源码地图 (SOURCE_MAP)

## 项目概览

- **项目类型**：Python AI Agent 框架（基于 Hermes Agent 深度 Fork）
- **Python 文件总数**：约 2693 个（含测试）
- **核心代码行数**：run_agent.py ~11457行、cli.py ~11000行、model_tools.py ~600行
- **测试用例**：约 3000 个 pytest 测试

---

## 核心模块文件清单

### 1. 入口与核心循环

| 文件 | 行数 | 功能摘要 | 关键函数/类 |
|------|------|---------|------------|
| `run_agent.py` | ~11457 | AIAgent核心对话循环 | `AIAgent`, `run_conversation()`, `chat()` |
| `cli.py` | ~11000 | HermesCLI交互式命令行界面 | `HermesCLI`, `process_command()` |
| `model_tools.py` | ~600 | 工具编排和函数调用分发 | `discover_builtin_tools()`, `handle_function_call()` |
| `toolsets.py` | ~580 | 工具集定义 | `_HERMES_CORE_TOOLS` 列表 |
| `hermes_state.py` | ~1200 | SQLite会话存储(FTS5搜索) | `SessionDB` |
| `hermes_constants.py` | ~270 | 常量定义和路径配置 | `get_hermes_home()` |
| `batch_runner.py` | ~1400 | 并行批处理 | `BatchRunner` |
| `utils.py` | ~160 | 工具函数 | 各种辅助函数 |

### 2. DeepAgent Harness 层（DeepSeek V4 适配）⭐新增模块

| 文件 | 行数 | 功能摘要 | 关键函数/类 |
|------|------|---------|------------|
| `deepagent_harness/__init__.py` | 48 | 包导出 | 导出所有Harness模块 |
| `deepagent_harness/prefix_manager.py` | 204 | Byte-Stable Prefix管理器 | `PrefixManager.freeze()`, `inject_mid_session_change()`, `consume_turn_tail()` |
| `deepagent_harness/hard_constraint.py` | 265 | 硬约束提取器（纯正则） | `HardConstraintExtractor.extract()`, `format_for_prefix()` |
| `deepagent_harness/model_router.py` | 354 | Flash/Pro智能路由器 | `ModelRouter.route()`, `force_upgrade()`, `force_pro_max()` |
| `deepagent_harness/reasoning_manager.py` | 249 | Reasoning Content管理器 | `ReasoningManager.filter_messages_for_api()` |
| `deepagent_harness/intent_router.py` | 255 | 7+1意图路由器 | `IntentRouter.classify()`, `classify_and_get_strategy()` |
| `deepagent_harness/immune_system.py` | 275 | Agent免疫系统 | `ImmuneSystem.post_execution_review()` |
| `deepagent_harness/starroad_cognition.py` | 245 | StarRoad三层认知引擎 | `get_l1_prompt_section()`, `get_l2_prompt_section()`, `get_l3_review_prompt()` |
| `deepagent_harness/context_layout.py` | 245 | Context Layout管理器 | `ContextLayoutManager.set_task_context()`, `inject_anchor_to_messages()` |
| `deepagent_harness/tool_schema_stabilizer.py` | 160 | Tool Schema稳定器 | `stabilize_tool_schemas()`, `get_tools_fingerprint()` |
| `deepagent_harness/scene_router.py` | 186 | 场景路由器 | `SceneRouter.classify()`, `route()`, `route_enhanced()` |
| `deepagent_harness/bidirectional_primitives.py` | ❌缺失 | 双向Agent原语 | **缺失：待实现need_more_context等四个元指令** |

### 3. Agent 内部模块

| 文件 | 行数 | 功能摘要 |
|------|------|---------|
| `agent/prompt_builder.py` | ~ | System Prompt组装 |
| `agent/context_compressor.py` | ~ | 自动上下文压缩 |
| `agent/prompt_caching.py` | ~ | Anthropic prompt缓存 |
| `agent/auxiliary_client.py` | ~ | 辅助LLM客户端（视觉、摘要） |
| `agent/model_metadata.py` | ~ | 模型上下文长度和token估算 |
| `agent/models_dev.py` | ~ | models.dev注册表集成 |
| `agent/display.py` | ~ | KawaiiSpinner动画、工具预览格式化 |
| `agent/skill_commands.py` | ~ | Skill斜杠命令 |
| `agent/trajectory.py` | ~ | 轨迹保存辅助 |

### 4. 工具系统

| 文件 | 行数 | 功能摘要 |
|------|------|---------|
| `tools/registry.py` | ~ | 中心工具注册表（schemas、handlers、dispatch） |
| `tools/approval.py` | ~ | 危险命令检测 |
| `tools/terminal_tool.py` | ~ | 终端工具编排 |
| `tools/process_registry.py` | ~ | 后台进程管理 |
| `tools/file_tools.py` | ~ | 文件读写搜索patch工具 |
| `tools/web_tools.py` | ~ | Web搜索/提取 |
| `tools/browser_tool.py` | ~ | Browserbase浏览器自动化 |
| `tools/code_execution_tool.py` | ~ | execute_code沙箱 |
| `tools/delegate_tool.py` | ~ | 子代理委派 |
| `tools/mcp_tool.py` | ~1050 | MCP客户端 |

### 5. CLI 子系统

| 文件 | 功能摘要 |
|------|---------|
| `hermes_cli/main.py` | 入口点 - 所有`deepagent`子命令 |
| `hermes_cli/config.py` | DEFAULT_CONFIG、OPTIONAL_ENV_VARS、配置迁移 |
| `hermes_cli/commands.py` | 斜杠命令定义 + SlashCommandCompleter |
| `hermes_cli/callbacks.py` | 终端回调（clarify、sudo、approval） |
| `hermes_cli/setup.py` | 交互式设置向导 |
| `hermes_cli/skin_engine.py` | 皮肤/主题引擎 |
| `hermes_cli/skills_config.py` | `deepagent skills` - 平台级skill启用/禁用 |
| `hermes_cli/tools_config.py` | `deepagent tools` - 平台级工具启用/禁用 |
| `hermes_cli/models.py` | 模型目录、provider模型列表 |
| `hermes_cli/model_switch.py` | 共享/model切换管道（CLI+gateway） |
| `hermes_cli/auth.py` | Provider凭证解析 |

### 6. 其他关键目录

| 目录 | 功能摘要 |
|------|---------|
| `gateway/` | 消息平台网关（telegram、discord、slack、whatsapp等） |
| `deepagent_code_mode/` | Code模式（子进程任务分发、隔离会话管理） |
| `embedded/` | 隔离研发小组环境（OpenCode集成） |
| `cron/` | 定时任务调度器 |
| `acp_adapter/` | ACP服务器（VS Code/Zed/JetBrains集成） |
| `environments/` | RL训练环境、终端后端（local/docker/ssh等） |
| `tests/` | pytest测试套件（~3000测试） |
| `skills/` | 内置Skill插件 |
| `webui/` | WebUI工作台（Electron桌面端） |
| `plugins/` | 插件系统 |

---

## Harness层集成点（run_agent.py中的关键位置）

| 行号 | 集成内容 |
|------|---------|
| 1095-1157 | Harness模块初始化（try-except包裹，默认启用） |
| ~3580 | PrefixManager注入检查 |
| ~7040 | PrefixManager freeze逻辑 |
| ~7055 | ModelRouter路由决策 |
| ~7070-7090 | StarRoad L1/L2注入 |
| ~8193 | IntentRouter意图分类 |
| ~8203-8204 | ContextLayout设置任务上下文 |
| ~8269-8287 | StarRoad + PrefixManager注入 |
| ~8522-8533 | StarRoad + PrefixManager（多轮） |
| ~8583 | ReasoningManager过滤messages |
| ~8708 | Tool Schema稳定器 |
| ~8727 | ContextLayout anchor注入 |
| ~11160 | ImmuneSystem事后审查 |
| ~11176-11178 | Harness诊断结果收集 |

---

## 关键数据流

```
用户消息
    ↓
[Scene Router] → 粗分类（CODE/RESEARCH/QUERY/...）
    ↓
[Intent Router] → 7+1细分类（Refactor/New/Architecture/...）→ 策略绑定
    ↓
[Hard Constraint Extractor] → 提取硬约束（纯正则）
    ↓
[StarRoad L1 + Hard Constraints] → 冻结到System Prompt（Byte-Stable Prefix）
    ↓
[PrefixManager.freeze()] → 锁定前缀，计算指纹
    ↓
每轮循环：
    ├─ [ModelRouter.route()] → Flash/Pro决策 + reason记录
    ├─ [PrefixManager.consume_turn_tail()] → mid-session变更注入
    ├─ [StarRoad L2] → 按意图注入方法论
    ├─ [ContextLayout] → Task Anchor注入到近端
    ├─ [tool_schema_stabilizer] → 工具schema字节稳定
    ├─ [ReasoningManager.filter_messages_for_api()] → 剥离无用reasoning
    ├─ 调用API
    └─ [ImmuneSystem.post_execution_review()] → 约束违反检查
```
