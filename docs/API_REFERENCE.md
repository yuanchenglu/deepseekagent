# DeepAgent API 参考

**版本**: 基于源码主干

---

## 目录

1. [AIAgent —— 核心 Agent 类](#1-aiagent--核心-agent-类)
2. [model_tools —— 工具编排层](#2-model_tools--工具编排层)
3. [tools.registry.ToolRegistry —— 工具注册中心](#3-toolsregistrytoolregistry--工具注册中心)
4. [hermes_state.SessionDB —— 会话持久化存储](#4-hermesstatesessiondb--会话持久化存储)
5. [hermes_constants —— 共享常量与路径工具](#5-hermes_constants--共享常量与路径工具)
6. [gateway.run —— 消息平台网关](#6-gatewayrun--消息平台网关)
7. [gateway.session —— 网关会话管理](#7-gatewaysession--网关会话管理)
8. [toolsets —— 工具集定义](#8-toolsets--工具集定义)
9. [agent.prompt_builder —— 系统提示词组装](#9-agentprompt_builder--系统提示词组装)

---

## 1. AIAgent —— 核心 Agent 类

**文件**: `run_agent.py`

### class AIAgent

AI 对话 Agent，管理对话流程、工具执行和响应处理。

```python
agent = AIAgent(
    base_url: str = None,
    api_key: str = None,
    model: str = "anthropic/claude-opus-4.6",
    max_iterations: int = 90,
    tool_delay: float = 1.0,
    enabled_toolsets: List[str] = None,
    disabled_toolsets: List[str] = None,
    save_trajectories: bool = False,
    quiet_mode: bool = False,
    session_id: str = None,
    platform: str = None,
    ...
)
```

#### 构造参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `base_url` | `str` | `None` | 模型 API 的基础 URL |
| `api_key` | `str` | `None` | API 密钥（不传则从环境变量读取） |
| `model` | `str` | `"anthropic/claude-opus-4.6"` | 模型名称 |
| `max_iterations` | `int` | `90` | 最大工具调用轮次 |
| `tool_delay` | `float` | `1.0` | 工具调用间延迟（秒） |
| `enabled_toolsets` | `List[str]` | `None` | 仅启用指定工具集 |
| `disabled_toolsets` | `List[str]` | `None` | 禁用指定工具集 |
| `save_trajectories` | `bool` | `False` | 是否保存轨迹 JSONL |
| `quiet_mode` | `bool` | `False` | 静默模式 |
| `ephemeral_system_prompt` | `str` | `None` | 临时系统提示词（不保存到轨迹） |
| `session_id` | `str` | `None` | 预生成会话 ID |
| `platform` | `str` | `None` | 平台标识（`"cli"`, `"telegram"`, `"discord"` 等） |
| `max_tokens` | `int` | `None` | 模型响应最大 token 数 |
| `reasoning_config` | `Dict` | `None` | 推理配置，如 `{"effort": "medium"}` |
| `prefill_messages` | `List[Dict]` | `None` | 预填消息（few-shot 示例） |
| `skip_context_files` | `bool` | `False` | 跳过 SOUL.md/AGENTS.md 自动注入 |
| `skip_memory` | `bool` | `False` | 跳过记忆加载 |
| `iteration_budget` | `IterationBudget` | `None` | 迭代预算对象（子 agent 继承） |
| `session_db` | `SessionDB` | `None` | 会话数据库实例 |
| `parent_session_id` | `str` | `None` | 父会话 ID（压缩续接链） |

#### 核心方法

##### `chat(message: str) -> str`

简单接口——单次对话，返回最终响应字符串。

```python
response = agent.chat("Tell me about the latest Python updates")
```

##### `run_conversation(user_message, system_message, conversation_history, task_id) -> dict`

完整接口——返回包含 `final_response` + `messages` 的字典。

```python
result = agent.run_conversation(
    user_message="写一个 Python 脚本",
    system_message="你是一个 Python 专家",
    conversation_history=[],  # 可选：已有消息历史
    task_id="task-001",
)
print(result["final_response"])
```

##### `flush_session() -> None`

将会话数据持久化到 SQLite。在 `run_conversation` 返回后调用。

```python
agent.flush_session()
```

---

### class IterationBudget

线程安全的迭代计数器。

```python
budget = IterationBudget(max_total=90)
ok = budget.consume()      # 消耗一次，返回 True/False
budget.refund()             # 退还一次（如 execute_code 这类程序调用）
used = budget.used          # 已用次数
remaining = budget.remaining  # 剩余次数
```

---

## 2. model_tools —— 工具编排层

**文件**: `model_tools.py`

工具发现、过滤、调度的核心入口。

### 模块级函数

##### `get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode) -> List[Dict]`

获取模型 API 调用用的工具定义（OpenAI 格式），支持工具集过滤。

```python
tools = get_tool_definitions(
    enabled_toolsets=["web", "file"],
    quiet_mode=True,
)
```

##### `handle_function_call(function_name, function_args, task_id, ...) -> str`

主调度器，将函数调用路由到工具注册表。

```python
result = handle_function_call(
    function_name="web_search",
    function_args={"query": "Python 3.13 新特性"},
    task_id="task-001",
    tool_call_id="call_xxx",
    session_id="session-xxx",
    user_task="搜索 Python 更新",
    enabled_tools=["web_search", "read_file"],
)
```

##### `get_all_tool_names() -> List[str]`

返回所有已注册工具名称。

##### `get_toolset_for_tool(tool_name) -> Optional[str]`

返回工具所属的工具集名称。

##### `get_available_toolsets() -> Dict[str, dict]`

返回工具集及其可用状态、工具列表、环境要求。

##### `check_toolset_requirements() -> Dict[str, bool]`

返回 `{工具集名: 是否可用}` 字典。

##### `check_tool_availability(quiet) -> Tuple[List[str], List[dict]]`

返回 `(可用工具集列表, 不可用工具集信息列表)`。

##### `coerce_tool_args(tool_name, args) -> Dict`

将工具调用的字符串参数强制转换为其 JSON Schema 声明的类型（如 `"42"` → `42`）。

---

## 3. tools.registry.ToolRegistry —— 工具注册中心

**文件**: `tools/registry.py`

所有工具的中心注册表。每个工具文件在模块加载时调用 `registry.register()` 自注册。

### 模块级单例

```python
from tools.registry import registry
```

### 方法

##### `register(name, toolset, schema, handler, ...)`

注册一个工具。由工具文件在模块导入时调用。

```python
registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(param=args.get("param", "")),
    check_fn=check_requirements,       # 可选：可用性检查函数
    requires_env=["EXAMPLE_API_KEY"],   # 可选：所需环境变量
    is_async=False,
    description="示例工具",
    emoji="🔧",
)
```

##### `deregister(name)` —— 注销工具（MCP 动态刷新用）

##### `get_entry(name) -> Optional[ToolEntry]` —— 获取工具元数据

##### `get_definitions(tool_names, quiet=False) -> List[dict]` —— 获取 OpenAI 格式 schema

##### `dispatch(name, args, **kwargs) -> str` —— 执行工具（自动桥接 async handler）

##### `get_all_tool_names() -> List[str]` —— 所有注册工具名

##### `get_toolset_for_tool(name) -> Optional[str]` —— 查询工具所属集

##### `get_schema(name) -> Optional[dict]` —— 获取原始 schema（绕过 check_fn）

##### `get_emoji(name, default="⚡") -> str` —— 获取工具 emoji

##### `is_toolset_available(toolset) -> bool` —— 工具集是否可用

##### `check_toolset_requirements() -> Dict[str, bool]` —— 所有工具集可用性

##### `get_available_toolsets() -> Dict[str, dict]` —— 用于 UI 展示

##### `register_toolset_alias(alias, toolset) -> None` —— 注册工具集别名

##### `get_toolset_alias_target(alias) -> Optional[str]` —— 解析别名

### 工具响应辅助函数

```python
from tools.registry import tool_error, tool_result

tool_error("file not found")                    # → '{"error": "file not found"}'
tool_error("bad input", success=False)          # → '{"error": "bad input", "success": false}'
tool_result(success=True, count=42)             # → '{"success": true, "count": 42}'
tool_result({"key": "value"})                   # → '{"key": "value"}'
```

---

## 4. hermes_state.SessionDB —— 会话持久化存储

**文件**: `hermes_state.py`

SQLite 后端会话存储，支持 FTS5 全文搜索。线程安全（WAL 模式）。

```python
db = SessionDB()  # 单例，始终返回同一实例
```

### 会话生命周期

##### `create_session(session_id, source, model, ...) -> str`

创建新会话。自动将 `session_id` 作为主键写入 `sessions` 表。

##### `end_session(session_id, end_reason) -> None`

标记会话结束。设置 `ended_at` 和 `end_reason`。

##### `reopen_session(session_id) -> None`

清除 `ended_at`/`end_reason` 以恢复会话。

##### `get_session(session_id) -> Optional[Dict]`

获取会话完整记录。

##### `resolve_session_id(prefix) -> Optional[str]`

按前缀查找唯一匹配的会话 ID。

##### `ensure_session(session_id, source, model) -> None`

确保会话行存在（INSERT OR IGNORE）。

### 标题管理

##### `sanitize_title(title) -> Optional[str]`

清理标题：去除控制字符、零宽字符、过长等。

##### `set_session_title(session_id, title) -> bool`

设置标题。返回是否找到并更新。不同会话间标题唯一。

##### `get_session_title(session_id) -> Optional[str]`

获取标题。

##### `get_session_by_title(title) -> Optional[Dict]`

按精确标题查会话。

##### `resolve_session_by_title(title) -> Optional[str]`

按标题查 ID，支持 `#N` 后缀线链。

##### `get_next_title_in_lineage(base_title) -> str`

生成线链中下一个标题（`"标题"` → `"标题 #2"`）。

### Token 与费用

##### `update_token_counts(session_id, input_tokens, output_tokens, ...)`

更新 token 计数和费用信息。`absolute=False` 时累加，`True` 时覆写。

### 消息存储

##### `append_message(session_id, role, content, ...)`

追加消息到会话。

##### `get_messages(session_id) -> List[Dict]`

获取会话所有消息。

##### `search_messages(query, limit=10) -> List[Dict]`

全文搜索会话消息（FTS5）。

### 列表与统计

##### `list_sessions_rich(source, exclude_sources, limit, offset) -> List[Dict]`

列出会话（含预览文本、最后活跃时间）。

##### `get_stats(source, since_days) -> Dict`

获取会话统计数据（总数、总 token 等）。

##### `count_sessions(source) -> int`

计数会话。

##### `delete_session(session_id) -> None`

删除会话及其消息。

### 类方法

- `get_default()` —— 获取全局单例
- `close_default()` —— 关闭全局单例

---

## 5. hermes_constants —— 共享常量与路径工具

**文件**: `hermes_constants.py`

### 路径函数

##### `get_deepagent_home() -> Path`

返回 DeepAgent 主目录（默认 `~/.deepagent`）。优先读取环境变量 `DEEPAGENT_HOME` → `HERMES_HOME`。

`get_hermes_home()` 是同一函数的别名（向后兼容）。

##### `display_hermes_home() -> str`

返回用户友好的路径字符串，如 `~/.deepagent` 或 `~/.deepagent/profiles/coder`。

##### `get_hermes_dir(new_subpath, old_name) -> Path`

获取子目录，向后兼容旧路径。如旧路径存在则用它，否则用新路径。

##### `get_config_path() -> Path`

返回 `config.yaml` 路径：`HERMES_HOME / "config.yaml"`。

##### `get_skills_dir() -> Path`

返回 `HERMES_HOME / "skills"`。

##### `get_env_path() -> Path`

返回 `.env` 文件路径。

##### `get_optional_skills_dir(default=None) -> Path`

返回可选 skills 目录。

##### `get_subprocess_home() -> Optional[str]`

返回子进程 HOME 目录（Profile 隔离用），不存在则返回 None。

### 环境检测

##### `is_termux() -> bool`

是否在 Android Termux 中运行。

##### `is_wsl() -> bool`

是否在 WSL 中运行。

##### `is_container() -> bool`

是否在 Docker/Podman 容器中运行。

### 网络工具

##### `apply_ipv4_preference(force=False) -> None`

按需猴子补丁 `socket.getaddrinfo` 优先用 IPv4。

### 推理强度

##### `parse_reasoning_effort(effort) -> Dict | None`

解析推理强度字符串（`"none"`, `"low"`, `"medium"`, `"high"`, `"xhigh"`）为配置字典。

### 常量

- `OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"`
- `AI_GATEWAY_BASE_URL = "https://ai-gateway.vercel.sh/v1"`

---

## 6. gateway.run —— 消息平台网关

**文件**: `gateway/run.py`

### 核心类

##### `GatewayRunner`

管理网关生命周期的主类。

```
python -m gateway.run          # 启动
python cli.py --gateway        # 从 CLI 启动
```

##### `start_gateway()`

启动所有配置的平台适配器。

### config.yaml 映射

网关启动时会从 `config.yaml` 读取配置桥接到环境变量：

| 配置路径 | 环境变量 |
|---|---|
| `terminal.backend` | `TERMINAL_ENV` |
| `terminal.cwd` | `TERMINAL_CWD` |
| `terminal.timeout` | `TERMINAL_TIMEOUT` |
| `terminal.docker_image` | `TERMINAL_DOCKER_IMAGE` |
| `terminal.ssh_host` | `TERMINAL_SSH_HOST` |
| `agent.max_turns` | `HERMES_MAX_ITERATIONS` |
| `agent.gateway_timeout` | `HERMES_AGENT_TIMEOUT` |
| `auxiliary.vision.model` | `AUXILIARY_VISION_MODEL` |
| `auxiliary.web_extract.model` | `AUXILIARY_WEB_EXTRACT_MODEL` |
| `timezone` | `HERMES_TIMEZONE` |
| `security.redact_secrets` | `HERMES_REDACT_SECRETS` |

### 平台适配器

所有适配器继承自 `gateway/platforms/base.py` 的 `BasePlatformAdapter`。

- `telegram` — Telegram Bot API
- `discord` — Discord Bot
- `slack` — Slack App
- `whatsapp` — WhatsApp Cloud API
- `signal` — Signal Messenger
- `homeassistant` — Home Assistant
- `qqbot` — QQ Bot

---

## 7. gateway.session —— 网关会话管理

**文件**: `gateway/session.py`

### SessionSource

描述消息来源的数据类。

```python
@dataclass
class SessionSource:
    platform: Platform
    chat_id: str
    chat_name: Optional[str] = None
    chat_type: str = "dm"  # "dm" | "group" | "channel" | "thread"
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    thread_id: Optional[str] = None
    chat_topic: Optional[str] = None
    user_id_alt: Optional[str] = None
    chat_id_alt: Optional[str] = None
```

### SessionContext

```python
@dataclass
class SessionContext:
    key: str                # 会话唯一键（用于 session_manager）
    source: SessionSource   # 消息来源
    session_id: str         # 本地会话 ID
    thread_id: str          # 平台线程 ID
```

### 核心函数

- `build_session_source(platform, chat_id, ...) -> SessionSource`
- `build_session_context(source) -> SessionContext`
- `build_session_key(source) -> str` —— 构建会话唯一键
- `build_session_context_prompt(ctx) -> str` —— 构建系统提示词上下文

### SessionStore

```python
store = SessionStore(storage_path="/path/to/sessions")
```

- `load_context(key) -> Optional[SessionContext]`
- `save_context(ctx)`
- `delete_context(key)`

---

## 8. toolsets —— 工具集定义

**文件**: `toolsets.py`

### _HERMES_CORE_TOOLS

所有平台共享的核心工具列表：

```python
web_search, web_extract,              # Web
terminal, process,                     # 终端
read_file, write_file, patch, search_files,  # 文件
vision_analyze, image_generate,        # 视觉
skills_list, skill_view, skill_manage, # Skills
browser_navigate, browser_snapshot,    # 浏览器
browser_click, browser_type,           # 浏览器操作
browser_scroll, browser_back,          # 浏览器导航
text_to_speech,                        # TTS
todo, memory,                          # 规划与记忆
session_search,                        # 会话搜索
clarify,                              # 追问
execute_code, delegate_task,           # 代码执行与委托
cronjob,                              # 定时任务
send_message,                          # 跨平台消息
ha_*                                  # Home Assistant
```

### 内置工具集

| 工具集 | 说明 |
|---|---|
| `web` | 网页搜索与内容提取 |
| `search` | 仅网页搜索 |
| `vision` | 图片分析 |
| `image_gen` | 图片生成 |
| `terminal` | 终端命令 |
| `file` | 文件读写操作 |
| `browser` | 浏览器自动化 |
| `skills` | Skill 管理 |
| `cronjob` | 定时任务 |
| `messaging` | 跨平台消息 |
| `code_execution` | Python 代码执行 |
| `delegation` | 子 agent 委托 |
| `memory` | 持久记忆 |
| `todo` | 任务规划 |
| `session_search` | 会话搜索 |
| `clarify` | 追问用户 |
| `meta` | 元指令（请求上下文、升级模型、自审查、提议 Skill） |
| `homeassistant` | 智能家居控制 |
| `debugging` | 调试组合（terminal + web + file） |
| `safe` | 安全模式（无终端访问） |
| `rl` | 强化学习训练 |
| `tts` | 文本转语音 |

### 平台专属工具集

| 工具集 | 适用平台 |
|---|---|
| `hermes-cli` | 交互式 CLI |
| `hermes-acp` | VS Code / Zed / JetBrains 编辑器 |
| `hermes-api-server` | OpenAI 兼容 API 服务器 |
| `hermes-telegram` | Telegram Bot |
| `hermes-discord` | Discord Bot |
| `hermes-slack` | Slack App |
| `hermes-whatsapp` | WhatsApp |

### 关键函数

- `get_all_toolsets() -> List[str]` —— 所有工具集名称
- `resolve_toolset(name) -> List[str]` —— 展开工具集为工具名列表（含 includes）
- `validate_toolset(name) -> bool` —— 验证工具集名称

---

## 9. agent.prompt_builder —— 系统提示词组装

**文件**: `agent/prompt_builder.py`

所有函数为**无状态**。`AIAgent._build_system_prompt()` 调用这些函数组装各部分。

### 关键函数

##### `build_context_files_prompt(cwd) -> str`

扫描当前目录及父目录的 `.hermes.md`、`HERMES.md`、`AGENTS.md`、`.cursorrules` 等上下文文件，组装为提示词块。内置注入检测以防范提示词攻击。

##### `build_memory_context_block(memory_data) -> str`

从记忆数据构建上下文块。根据记忆分类（SOUL / MEMORY / USER / 项目记忆）分层注入。

##### `build_skills_system_prompt(platform, skills_dir) -> str`

扫描 Skills 目录，构建可用 Skill 的索引提示词块。

##### `build_environment_hints() -> str`

检测运行时环境（Termux / WSL / 容器/Podman），生成对应提示。

##### `load_soul_md() -> Optional[str]`

加载 SOUL.md 文件（Agent 核心身份定义）。

##### `build_nous_subscription_prompt(messages) -> str`

为 Nous 订阅构建提示（OpenRouter / Nous 专属）。

### 注入检测

`_scan_context_content(content, filename)` 扫描上下文内容中的提示词攻击模式：

- `ignore previous/all instructions`
- `do not tell the user`
- `system prompt override`
- `translate ... and execute`
- 隐式 Unicode 字符（零宽、方向覆盖等）

命中时，内容被替换为 `[BLOCKED: ...]` 占位符而非注入到系统提示词中。

---

## 附录：工具注册工作流

以 `tools/web_tools.py` 为例演示新工具添加流程：

```python
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("WEB_SEARCH_API_KEY"))

def web_search_tool(query: str, task_id: str = None) -> str:
    # ... 实现 ...
    return json.dumps({"results": [...]})

registry.register(
    name="web_search",
    toolset="web",
    schema={
        "name": "web_search",
        "description": "搜索互联网",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"],
        },
    },
    handler=lambda args, **kw: web_search_tool(
        query=args.get("query", ""),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_requirements,
    requires_env=["WEB_SEARCH_API_KEY"],
)
```

自动发现：任何 `tools/*.py` 中含有顶层 `registry.register()` 调用的文件会被自动导入——无需维护导入列表。
