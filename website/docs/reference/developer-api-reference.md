---
sidebar_position: 7
title: "开发者 API 参考"
description: "ToolRegistry、SessionDB、Config API 的完整参考——供插件开发者和核心贡献者使用"
---

# 开发者 API 参考

本文档涵盖 DeepAgent 内部核心 API 的完整参考，供插件开发者、工具编写者和核心贡献者使用。

- [ToolRegistry API](#toolregistry-api) — 工具注册、调度、查询
- [SessionDB API](#sessiondb-api) — SQLite 会话存储与全文搜索
- [Config API](#config-api) — 配置加载、保存、路径解析

---

## ToolRegistry API

位置：`tools/registry.py`

`ToolRegistry` 是全局单例，管理所有工具的注册、调度、可用性检查和 schema 查询。每个工具文件在模块加载时调用 `registry.register()` 自注册。

```python
from tools.registry import registry, tool_error, tool_result

registry: ToolRegistry  # 模块级单例
```

### 注册

#### `registry.register(name, toolset, schema, handler, ...)`

注册一个工具。通常在工具文件的**模块层级**调用。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | — | 工具唯一名称（API schema 中使用） |
| `toolset` | `str` | — | 所属工具集名 |
| `schema` | `dict` | — | OpenAI 函数调用 schema（description + parameters） |
| `handler` | `Callable` | — | 工具执行函数 `(args: dict, task_id: str=None) -> str` |
| `check_fn` | `Callable` | `None` | 可选可用性检查 `() -> bool` |
| `requires_env` | `list` | `None` | 所需环境变量名列表（用于 UI 展示） |
| `is_async` | `bool` | `False` | handler 是否为异步协程 |
| `description` | `str` | `""` | 人类可读描述（缺省用 schema.description） |
| `emoji` | `str` | `""` | Spinner 展示用 emoji |
| `max_result_size_chars` | `int` | `None` | 结果大小限制（字符数） |

**行为**：
- 同名工具冲突时，MCP 工具可互相覆盖，非 MCP 工具不可覆盖内置工具
- 自动记录 `toolset` 级的 check_fn（首个注册的工具决定）

**示例**：
```python
registry.register(
    name="weather_get",
    toolset="weather",
    schema={
        "name": "weather_get",
        "description": "查询指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"}
            },
            "required": ["city"],
        },
    },
    handler=lambda args, **kw: tool_result(city=args["city"], temp=22),
    check_fn=lambda: bool(os.getenv("WEATHER_API_KEY")),
    requires_env=["WEATHER_API_KEY"],
)
```

#### `registry.deregister(name)`

从注册表中移除一个工具。用于 MCP 动态工具刷新。

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 工具名称 |

**行为**：如果该工具是其工具集的最后一个工具，自动清理工具集 check_fn 和别名。

#### `registry.register_toolset_alias(alias, toolset)`

为规范工具集名注册一个别名。

| 参数 | 类型 | 说明 |
|------|------|------|
| `alias` | `str` | 别名 |
| `toolset` | `str` | 规范工具集名 |

### 调度

#### `registry.dispatch(name, args, **kwargs) -> str`

按名称执行工具 handler。

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 工具名称 |
| `args` | `dict` | 工具参数 |
| `**kwargs` | — | 透传参数（如 `task_id`） |

**返回**：JSON 字符串。异常被统一捕获为 `{"error": "..."}`。

### 查询方法

#### `registry.get_entry(name) -> ToolEntry | None`

返回工具的 `ToolEntry` 元数据，或 None。

`ToolEntry` 属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `.name` | `str` | 工具名 |
| `.toolset` | `str` | 所属工具集 |
| `.schema` | `dict` | OpenAI schema |
| `.handler` | `Callable` | 执行函数 |
| `.check_fn` | `Callable | None` | 可用性检查 |
| `.requires_env` | `list[str]` | 所需环境变量 |
| `.is_async` | `bool` | 是否异步 |
| `.description` | `str` | 描述 |
| `.emoji` | `str` | 展示 emoji |
| `.max_result_size_chars` | `int | None` | 大小限制 |

#### `registry.get_definitions(tool_names, quiet=False) -> list[dict]`

返回指定工具名的 OpenAI 格式 schema 列表（已过滤不可用工具）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tool_names` | `Set[str]` | — | 要查询的工具名集合 |
| `quiet` | `bool` | `False` | 抑制不可用工具的日志 |

#### `registry.get_all_tool_names() -> list[str]`

返回所有已注册工具名的排序列表。

#### `registry.get_schema(name) -> dict | None`

返回工具的原始 schema dict（不经过 check_fn 过滤）。用于 token 估算等场景。

#### `registry.get_toolset_for_tool(name) -> str | None`

返回工具所属的工具集名。

#### `registry.get_emoji(name, default="⚡") -> str`

返回工具的 emoji，未设置时返回默认值。

#### `registry.get_tool_to_toolset_map() -> dict[str, str]`

返回 `{tool_name: toolset_name}` 映射字典。

#### `registry.get_registered_toolset_names() -> list[str]`

返回所有已注册工具集的排序列表。

#### `registry.get_tool_names_for_toolset(toolset) -> list[str]`

返回指定工具集下的所有工具名列表。

#### `registry.get_registered_toolset_aliases() -> dict[str, str]`

返回 `{alias: canonical_toolset}` 快照。

#### `registry.get_toolset_alias_target(alias) -> str | None`

返回别名的规范工具集名，或 None。

#### `registry.get_max_result_size(name, default=None) -> int`

返回工具的结果大小限制。

### 可用性检查

#### `registry.is_toolset_available(toolset) -> bool`

检查工具集的依赖是否满足。check_fn 抛出异常时返回 False。

#### `registry.check_toolset_requirements() -> dict[str, bool]`

返回 `{toolset: available_bool}` 字典。

#### `registry.get_available_toolsets() -> dict[str, dict]`

返回工具集元数据，用于 UI 展示：
```python
{
    "toolset_name": {
        "available": True/False,
        "tools": ["tool1", "tool2"],
        "description": "",
        "requirements": ["API_KEY"],
    }
}
```

#### `registry.get_toolset_requirements() -> dict[str, dict]`

返回与旧版 `TOOLSET_REQUIREMENTS` 兼容的字典。

#### `registry.check_tool_availability(quiet=False) -> (list, list)`

返回 `(available_toolsets, unavailable_info)` 元组。

### 序列化辅助函数

#### `tool_error(message, **extra) -> str`

返回 JSON 错误字符串。

```python
tool_error("file not found")
# → '{"error": "file not found"}'
tool_error("bad input", success=False)
# → '{"error": "bad input", "success": false}'
```

#### `tool_result(data=None, **kwargs) -> str`

返回 JSON 结果字符串。接受 dict 位置参数或关键字参数（二选一）。

```python
tool_result(success=True, count=42)
# → '{"success": true, "count": 42}'
tool_result({"key": "value"})
# → '{"key": "value"}'
```

### 自动发现

`discover_builtin_tools(tools_dir=None) -> list[str]`

扫描 `tools/*.py` 文件，通过 AST 分析找到包含顶层 `registry.register()` 调用的模块并导入。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tools_dir` | `Path | None` | `None` | 工具目录（默认 `tools/`） |

**返回**：成功导入的模块名列表。

内部流程：
1. 遍历目录下所有 `.py` 文件（排除 `__init__.py`、`registry.py`、`mcp_tool.py`）
2. AST 解析检查是否有顶层 `registry.register()` 调用
3. 自动 `importlib.import_module()` 导入

---

## SessionDB API

位置：`hermes_state.py`

`SessionDB` 是 SQLite 驱动的会话存储引擎，支持 WAL 模式并发读写和 FTS5 全文搜索。

```python
from hermes_state import SessionDB

db = SessionDB()  # 返回进程全局单例
```

### 单例模式

`SessionDB()`（无参数）总是返回同一个进程全局实例，通过全局连接注册表管理：

| 方法 | 说明 |
|------|------|
| `SessionDB(db_path)` | 使用指定路径创建新实例（仅测试用） |
| `SessionDB()` | 返回进程全局默认实例 |
| `SessionDB.get_default()` | 显式获取默认实例 |
| `SessionDB.close_default()` | 关闭默认实例（幂等） |

### 会话生命周期

#### `create_session(session_id, source, ...) -> str`

创建新会话记录。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `session_id` | `str` | — | 会话唯一 ID |
| `source` | `str` | — | 来源标识（`cli`、`telegram`、`discord`等） |
| `model` | `str` | `None` | 使用的模型名 |
| `model_config` | `dict` | `None` | 模型配置（JSON 序列化存储） |
| `system_prompt` | `str` | `None` | 系统提示 |
| `user_id` | `str` | `None` | 用户标识 |
| `parent_session_id` | `str` | `None` | 父会话 ID（压缩分割链） |

#### `end_session(session_id, end_reason)`

将会话标记为已结束。

#### `reopen_session(session_id)`

清除结束标记以便恢复会话。

#### `update_system_prompt(session_id, system_prompt)`

存储装配后的完整系统提示快照。

#### `ensure_session(session_id, source, model)`

确保会话行存在（如创建失败时恢复用）。

### Token 与成本追踪

#### `update_token_counts(session_id, ...)`

更新 token 计数器和模型信息。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `session_id` | `str` | — | 会话 ID |
| `input_tokens` | `int` | `0` | 输入 token 数 |
| `output_tokens` | `int` | `0` | 输出 token 数 |
| `model` | `str` | `None` | 模型名（回填） |
| `cache_read_tokens` | `int` | `0` | 缓存读取 token 数 |
| `cache_write_tokens` | `int` | `0` | 缓存写入 token 数 |
| `reasoning_tokens` | `int` | `0` | 推理 token 数 |
| `estimated_cost_usd` | `float` | `None` | 估算美元成本 |
| `actual_cost_usd` | `float` | `None` | 实际美元成本 |
| `cost_status` | `str` | `None` | 成本状态描述 |
| `cost_source` | `str` | `None` | 成本数据来源 |
| `pricing_version` | `str` | `None` | 定价版本 |
| `billing_provider` | `str` | `None` | 计费提供商 |
| `billing_base_url` | `str` | `None` | 计费端点 |
| `billing_mode` | `str` | `None` | 计费模式 |
| `absolute` | `bool` | `False` | `True`=直接设置，`False`=增量累加 |

### 会话查询

#### `get_session(session_id) -> dict | None`

按 ID 获取会话。

#### `resolve_session_id(session_id_or_prefix) -> str | None`

解析精确或前缀匹配的会话 ID。前缀唯一时返回全 ID。

#### `set_session_title(session_id, title) -> bool`

设置会话标题。标题全局唯一（非空时）。返回是否设置成功。

| 异常 | 触发条件 |
|------|----------|
| `ValueError` | 标题已被其他会话使用，或校验失败 |

#### `get_session_title(session_id) -> str | None`

获取会话标题。

#### `get_session_by_title(title) -> dict | None`

按精确标题查找会话。

#### `resolve_session_by_title(title) -> str | None`

按标题解析会话 ID，支持 `"#N"` 编号变体，返回最新续写。

#### `get_next_title_in_lineage(base_title) -> str`

生成标题族系中的下一个标题（如 `"my session"` → `"my session #2"`）。

#### `list_sessions_rich(source, exclude_sources, limit, offset, include_children) -> list[dict]`

列出会话（含摘要预览和最后活跃时间）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `str` | `None` | 按来源过滤 |
| `exclude_sources` | `list[str]` | `None` | 排除的来源列表 |
| `limit` | `int` | `20` | 返回条数 |
| `offset` | `int` | `0` | 分页偏移 |
| `include_children` | `bool` | `False` | 是否包含子会话 |

**返回字段**：`id`, `source`, `model`, `title`, `started_at`, `ended_at`, `message_count`, `preview`, `last_active`

#### `search_sessions(source, limit, offset) -> list[dict]`

按来源列出会话（基础版本）。

### 消息存储

#### `append_message(session_id, role, content, ...) -> int`

追加消息到会话。返回消息行 ID。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `session_id` | `str` | — | 会话 ID |
| `role` | `str` | — | 角色（`user`/`assistant`/`tool`/`system`） |
| `content` | `str` | `None` | 消息内容 |
| `tool_name` | `str` | `None` | 工具名（tool 角色时） |
| `tool_calls` | `Any` | `None` | 工具调用列表（JSON 序列化） |
| `tool_call_id` | `str` | `None` | 工具调用 ID |
| `token_count` | `int` | `None` | token 计数 |
| `finish_reason` | `str` | `None` | 结束原因 |
| `reasoning` | `str` | `None` | 推理内容 |
| `reasoning_details` | `Any` | `None` | 推理详情（JSON 序列化） |
| `codex_reasoning_items` | `Any` | `None` | Codex 推理条目（JSON 序列化） |

**自动行为**：递增 `message_count`，tool 角色或含 tool_calls 时递增 `tool_call_count`。

#### `get_messages(session_id) -> list[dict]`

加载会话的全部消息，按时间戳排序。

#### `get_messages_as_conversation(session_id) -> list[dict]`

加载消息为 OpenAI 对话格式（role + content dicts）。自动反序列化 tool_calls、reasoning 等 JSON 字段。

### 全文搜索

#### `search_messages(query, source_filter, exclude_sources, role_filter, limit, offset) -> list[dict]`

FTS5 全文搜索所有会话的消息。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | `str` | — | 搜索查询（支持 FTS5 语法） |
| `source_filter` | `list[str]` | `None` | 按来源过滤 |
| `exclude_sources` | `list[str]` | `None` | 排除来源 |
| `role_filter` | `list[str]` | `None` | 按角色过滤 |
| `limit` | `int` | `20` | 返回条数 |
| `offset` | `int` | `0` | 分页偏移 |

**FTS5 查询语法**：
- 简单关键词：`docker deployment`
- 精确短语：`"exact phrase"`
- 布尔运算：`docker OR kubernetes`、`python NOT java`
- 前缀匹配：`deploy*`

**返回字段**：`id`, `session_id`, `role`, `snippet`, `timestamp`, `tool_name`, `source`, `model`, `session_started`, `context`

### 统计

#### `session_count(source=None) -> int`

统计会话数（可选按来源过滤）。

#### `message_count(session_id=None) -> int`

统计消息数（可选按会话过滤）。

### 导出与清理

#### `export_session_as_markdown(session_id) -> str | None`

将会话导出为人可读的 Markdown 字符串。

#### `export_session(session_id) -> dict | None`

将会话及其消息导出为 dict。

#### `export_all(source=None) -> list[dict]`

导出所有会话（含消息）为 dict 列表。

#### `clear_messages(session_id)`

删除会话的所有消息并重置计数器。

#### `delete_session(session_id) -> bool`

删除会话及其消息。子会话被孤立（`parent_session_id` 置 NULL）。返回是否找到并删除。

#### `prune_sessions(older_than_days=90, source=None) -> int`

删除 N 天前的已结束会话。返回删除数。

---

## Config API

配置系统分为两部分：

1. **`hermes_constants.py`** — 路径解析和环境检测（零依赖）
2. **`hermes_cli/config.py`** — 配置加载、保存、环境变量管理

### 路径解析（hermes_constants.py）

```python
from hermes_constants import get_hermes_home, get_config_path, get_env_path
```

#### `get_deepagent_home() -> Path` / `get_hermes_home() -> Path`

返回 DeepAgent 主目录。优先级：
1. `DEEPAGENT_HOME` 环境变量
2. `HERMES_HOME` 环境变量（向后兼容）
3. `~/.deepagent`

**所有状态文件必须通过此函数获取根路径**，不可硬编码 `~/.deepagent`。

#### `get_default_hermes_root() -> Path`

返回 profile 操作的根目录。在 profile 模式下，`HERMES_HOME` 可能为 `<root>/profiles/<name>`，此函数返回 `<root>`。

#### `get_config_path() -> Path`

返回 `config.yaml` 路径：`get_hermes_home() / "config.yaml"`。

#### `get_env_path() -> Path`

返回 `.env` 文件路径。

#### `get_skills_dir() -> Path`

返回 skills 目录路径。

#### `get_optional_skills_dir(default=None) -> Path`

返回 optional-skills 目录路径，支持 `HERMES_OPTIONAL_SKILLS` 环境变量覆盖。

#### `get_subprocess_home() -> str | None`

返回子进程的 `HOME` 目录（用于 profile 隔离），`{HERMES_HOME}/home/` 存在时返回。

#### `display_hermes_home() -> str`

返回用户友好的显示路径（使用 `~/.deepagent` 简写）。

### 环境检测

#### `is_managed() -> bool`

是否运行在包管理器管理模式（NixOS/Homebrew）。

#### `is_termux() -> bool`

是否运行在 Termux（Android）环境。

#### `is_wsl() -> bool`

是否运行在 WSL 环境（结果进程级别缓存）。

#### `is_container() -> bool`

是否运行在 Docker/Podman 容器中。

#### `parse_reasoning_effort(effort) -> dict | None`

将推理强度字符串解析为配置 dict。有效值：`none`, `minimal`, `low`, `medium`, `high`, `xhigh`。

### 配置文件加载（hermes_cli/config.py）

```python
from hermes_cli.config import load_config, save_config, read_raw_config
```

#### `load_config() -> dict`

加载并合并 `config.yaml`，支持 `${ENV_VAR}` 变量展开。返回完整配置字典。

#### `read_raw_config() -> dict`

读取原始 YAML 配置（不展开环境变量）。

#### `save_config(config)`

保存配置字典到 `config.yaml`。

### 环境变量管理

#### `get_env_value(key) -> str | None`

从 `.env` 文件读取环境变量值。

#### `save_env_value(key, value)`

写入环境变量到 `.env` 文件。

#### `save_env_value_secure(key, value) -> dict`

安全写入环境变量（文件权限 0600）。返回 `{"success": True}` 或 `{"error": ...}`。

### 默认配置

`DEFAULT_CONFIG` 定义在 `hermes_cli/config.py` 中，包含所有配置键的默认值。主要结构：

```yaml
model:
  default: ""              # 默认模型
  provider: ""             # 默认提供商
  context_length: null     # 上下文长度覆盖
  max_tokens: null         # 最大 token 覆盖

agent:
  max_turns: 90            # 最大工具调用轮数
  gateway_timeout: 600     # 网关超时秒数
  tool_use_enforcement: "auto"

terminal:
  backend: "local"         # 终端后端
  cwd: null                # 工作目录

display:
  skin: "default"          # 皮肤主题
  stream: true             # 流式输出
  busy_input_mode: "interrupt"

compression:
  enabled: true
  threshold: 0.50          # 触发压缩的上下文占比
  target_ratio: 0.20       # 压缩后目标占比

memory:
  enabled: false
  provider: ""             # 外置记忆提供者

plugins:
  disabled: []             # 禁用的插件列表

skills:
  creation_nudge_interval: 10
```

### 环境变量定义

`OPTIONAL_ENV_VARS` 是受支持的环境变量元数据字典，定义在 `hermes_cli/config.py` 中。每个条目：

```python
"OPENROUTER_API_KEY": {
    "description": "OpenRouter API key",
    "prompt": "OpenRouter API Key",
    "url": "https://openrouter.ai/keys",
    "password": True,         # 密码输入模式
    "category": "provider",   # provider/tool/messaging/setting
}
```

### 自定义提供商解析

`get_compatible_custom_providers(cfg) -> list`

从配置中提取所有已配置的自定义 LLM 提供商端点。
