---
sidebar_position: 3
title: "Python API 参考"
description: "AIAgent 类的完整 API 参考 —— 构造函数、公共方法、回调签名、返回值模式"
---

# Python API 参考

本文提供 `AIAgent` 类的完整 API 参考。使用指南见 [Python 库使用指南](../guides/python-library.md)。

---

## AIAgent

```python
from run_agent import AIAgent

agent = AIAgent(model="anthropic/claude-sonnet-4", quiet_mode=True)
response = agent.chat("Hello")
```

### 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | `str` | `""` | 模型名（OpenRouter 格式 `provider/model`）。为空时由运行时决定。 |
| `base_url` | `str` | `None` | API 端点 URL。不传则从 provider 路由自动解析。 |
| `api_key` | `str` | `None` | API 密钥。不传则 fallback 到环境变量。 |
| `provider` | `str` | `None` | 提供商标识（用于遥测/路由提示）。自动检测 `api_mode`。 |
| `api_mode` | `str` | `None` | API 模式覆盖：`"chat_completions"` / `"codex_responses"` / `"anthropic_messages"`。自动检测，一般无需显式设置。 |
| `max_iterations` | `int` | `90` | 每次对话的最大工具调用迭代次数。父 agent 和子 agent 共享此预算。 |
| `tool_delay` | `float` | `1.0` | 工具调用间的延迟秒数。 |
| `enabled_toolsets` | `List[str]` | `None` | 白名单：只启用这些工具集中的工具。 |
| `disabled_toolsets` | `List[str]` | `None` | 黑名单：禁用这些工具集中的工具。 |
| `save_trajectories` | `bool` | `False` | 是否将对话轨迹保存到 JSONL 文件。 |
| `verbose_logging` | `bool` | `False` | 启用详细日志用于调试。 |
| `quiet_mode` | `bool` | `False` | 抑制进度输出。嵌入到其他应用时**必须设为 `True`**。 |
| `ephemeral_system_prompt` | `str` | `None` | 自定义系统提示，不会保存到轨迹文件中。 |
| `log_prefix_chars` | `int` | `100` | 工具调用/响应的日志预览字符数。 |
| `log_prefix` | `str` | `""` | 日志消息前缀，用于并行处理中区分不同实例。 |
| `providers_allowed` | `List[str]` | `None` | OpenRouter 允许的提供商列表。 |
| `providers_ignored` | `List[str]` | `None` | OpenRouter 忽略的提供商列表。 |
| `providers_order` | `List[str]` | `None` | OpenRouter 提供商优先级顺序。 |
| `provider_sort` | `str` | `None` | 按 `price` / `throughput` / `latency` 排序提供商。 |
| `provider_require_parameters` | `bool` | `False` | 是否要求提供商支持参数化调用。 |
| `provider_data_collection` | `str` | `None` | OpenRouter 数据收集策略。 |
| `session_id` | `str` | `None` | 预生成的会话 ID。不传则自动生成。 |
| `tool_progress_callback` | `callable` | `None` | `(tool_name, args_preview) -> None`。工具执行过程中的进度通知。 |
| `tool_start_callback` | `callable` | `None` | `(tool_name, args_preview) -> None`。工具开始执行时触发。 |
| `tool_complete_callback` | `callable` | `None` | `(tool_name, result_preview) -> None`。工具完成时触发。 |
| `thinking_callback` | `callable` | `None` | 模型思考/推理过程中的回调。 |
| `reasoning_callback` | `callable` | `None` | `(reasoning_text) -> None`。模型推理内容 delta 回调。 |
| `clarify_callback` | `callable` | `None` | `(question, choices) -> str`。交互式用户澄清回调。由 CLI 或 gateway 提供。 |
| `step_callback` | `callable` | `None` | `(step_info) -> None`。每一步的回调。 |
| `stream_delta_callback` | `callable` | `None` | `(delta_text) -> None`。流式输出的文本 delta 回调。用于实时展示。 |
| `interim_assistant_callback` | `callable` | `None` | 当流式模式下产生完整 assistant 消息时的回调。 |
| `tool_gen_callback` | `callable` | `None` | 工具生成过程中的回调。 |
| `status_callback` | `callable` | `None` | `(status_text) -> None`。状态消息回调，用于 gateway 平台的状态推送。 |
| `max_tokens` | `int` | `None` | 模型响应的最大 token 数。不传则使用模型默认值。 |
| `reasoning_config` | `Dict[str, Any]` | `None` | 推理配置覆盖（如 `{"effort": "none"}`）。不传时 OpenRouter 默认 medium。 |
| `service_tier` | `str` | `None` | API 服务层级（如 `"auto"`、`"default"`）。 |
| `request_overrides` | `Dict[str, Any]` | `None` | 每次 API 调用的额外请求参数覆盖。 |
| `prefill_messages` | `List[Dict]` | `None` | 预填充消息列表（few-shot 示例）。不会保存到会话/轨迹中。 |
| `platform` | `str` | `None` | 用户所在的平台标识（`"cli"`、`"telegram"`、`"discord"` 等）。影响输出格式。 |
| `user_id` | `str` | `None` | 平台用户标识（gateway 会话用）。 |
| `skip_context_files` | `bool` | `False` | 跳过自动加载 SOUL.md、AGENTS.md 等上下文文件。 |
| `skip_memory` | `bool` | `False` | 禁用持久化记忆的读写。 |
| `session_db` | `SessionDB` | `None` | 外部传入的会话数据库实例。 |
| `parent_session_id` | `str` | `None` | 父会话 ID（用于 subagent 的会话层级追踪）。 |
| `iteration_budget` | `IterationBudget` | `None` | 外部传入的迭代预算。不传则基于 `max_iterations` 创建。 |
| `fallback_model` | `Dict[str, Any]` | `None` | 降级模型配置。主模型失败时自动切换。 |
| `credential_pool` | `CredentialPool` | `None` | 凭证池，用于多个 API 密钥之间的轮换和故障切换。 |
| `checkpoints_enabled` | `bool` | `False` | 启用检查点/回滚功能。 |
| `checkpoint_max_snapshots` | `int` | `50` | 最大检查点快照数。 |
| `pass_session_id` | `bool` | `False` | 将会话 ID 注入系统提示。 |
| `persist_session` | `bool` | `True` | 是否持久化会话到数据库。 |
| `acp_command` | `str` | `None` | ACP 运行时的执行命令（替代 `command`）。 |
| `acp_args` | `list[str]` | `None` | ACP 运行时的执行参数（替代 `args`）。 |

---

## 公共方法

### `chat(message, stream_callback=None) -> str`

最简聊天接口。内部调用 `run_conversation()`，只返回最终回复文本。

```python
response = agent.chat("What is the capital of France?")
print(response)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | `str` | — | 用户消息 |
| `stream_callback` | `callable` | `None` | 流式文本 delta 回调 |

**返回**: `str` — 最终回复文本。

---

### `run_conversation(user_message, system_message=None, conversation_history=None, task_id=None, stream_callback=None, persist_user_message=None) -> dict`

完整的对话执行方法。处理系统提示构建、工具调用循环、错误重试、轨迹保存、会话持久化等全部逻辑。

```python
result = agent.run_conversation(
    user_message="Search for Python 3.13 features",
    task_id="my-task-1",
)
print(result["final_response"])
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_message` | `str` | — | 用户消息 |
| `system_message` | `str` | `None` | 自定义系统消息。覆盖 `ephemeral_system_prompt` |
| `conversation_history` | `List[Dict]` | `None` | 之前的对话消息列表，用于多轮对话 |
| `task_id` | `str` | `None` | 任务唯一标识。用于并发任务间的 VM 隔离。自动生成 |
| `stream_callback` | `callable` | `None` | 流式文本 delta 回调。用于 TTS 等场景 |
| `persist_user_message` | `str` | `None` | 替代 `user_message` 存入历史记录。用于 `user_message` 包含 API 专用前缀的场景 |

**返回 dict 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `final_response` | `str` | 模型最终回复文本 |
| `last_reasoning` | `str` | 最后一条 assistant 消息中的推理内容 |
| `messages` | `list[dict]` | 完整消息历史（system/user/assistant/tool） |
| `api_calls` | `int` | 本轮实际 API 调用次数 |
| `completed` | `bool` | 是否正常完成（`True` = 模型主动结束，非迭代上限终止） |
| `partial` | `bool` | 是否因无效工具调用而提前结束 |
| `interrupted` | `bool` | 是否被中断 |
| `interrupt_message` | `str` | 中断触发消息（仅 `interrupted=True` 时存在） |
| `response_previewed` | `bool` | 响应是否已被预览（gateway 预检查用） |
| `model` | `str` | 实际使用的模型名 |
| `provider` | `str` | 实际使用的提供商 |
| `base_url` | `str` | 实际使用的 API 端点 URL |
| `input_tokens` | `int` | 本轮输入 token 总数 |
| `output_tokens` | `int` | 本轮输出 token 总数 |
| `cache_read_tokens` | `int` | 缓存读取 token 数（仅 Anthropic） |
| `cache_write_tokens` | `int` | 缓存写入 token 数（仅 Anthropic） |
| `reasoning_tokens` | `int` | 推理 token 数 |
| `prompt_tokens` | `int` | 本轮提示 token 数 |
| `completion_tokens` | `int` | 本轮补全 token 数 |
| `total_tokens` | `int` | 本轮总 token 数 |
| `last_prompt_tokens` | `int` | 压缩后最后一次提示的 token 数 |
| `estimated_cost_usd` | `float` | 估算的美元成本 |
| `cost_status` | `str` | 成本状态描述 |
| `cost_source` | `str` | 成本数据来源 |

---

### `clear_interrupt() -> None`

清除中断请求信号。在每次新对话开始前自动调用。

---

### `get_activity_summary() -> dict`

获取 agent 当前活动的快照。用于 gateway 超时处理和"仍在工作中"通知。

**返回 dict**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `last_activity_ts` | `float` | 最后活动时间戳 |
| `last_activity_desc` | `str` | 最后活动描述 |
| `seconds_since_activity` | `float` | 从最后活动至今的秒数 |
| `current_tool` | `str` | 当前正在执行的工具名 |
| `api_call_count` | `int` | 本轮 API 调用计数 |
| `max_iterations` | `int` | 最大迭代次数 |
| `budget_used` | `int` | 已用迭代预算 |
| `budget_max` | `int` | 迭代预算上限 |

---

### `get_rate_limit_state() -> Optional[RateLimitState]`

返回最后一次捕获的速率限制状态，或 `None`。

```python
state = agent.get_rate_limit_state()
if state:
    print(f"Remaining: {state.remaining}/{state.limit}")
```

---

### `shutdown_memory_provider(messages=None) -> None`

关闭记忆提供器和上下文引擎。在真正的会话边界（CLI 退出、`/reset`、gateway 会话过期等）调用。**非每轮调用**。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `messages` | `list` | `None` | 当前会话的消息列表，用于 `on_session_end()` 回调 |

---

### `close() -> None`

释放 agent 实例持有的所有资源。幂等，可多次调用。

清理的资源包括：
- 后台进程（通过 `ProcessRegistry`）
- 终端沙箱环境（VM）
- 浏览器守护进程会话
- 活跃的子 agent（subagent 委派）
- OpenAI/httpx 客户端连接

---

## 回调签名

所有回调均为可选，平台层（CLI/gateway）设置后 agent 会在相应时机触发。

| 回调 | 签名 | 触发时机 |
|------|------|----------|
| `tool_progress_callback` | `(tool_name: str, args_preview: str) -> None` | 工具执行过程中 |
| `tool_start_callback` | `(tool_name: str, args_preview: str) -> None` | 工具开始执行 |
| `tool_complete_callback` | `(tool_name: str, result_preview: str) -> None` | 工具执行完成 |
| `thinking_callback` | `(text: str) -> None` | 模型思考过程（原始） |
| `reasoning_callback` | `(reasoning_text: str) -> None` | 模型推理内容（结构化 delta） |
| `clarify_callback` | `(question: str, choices: list) -> str` | 需要用户澄清时。返回用户的选择 |
| `step_callback` | `(step_info: dict) -> None` | 每个步骤结束时 |
| `stream_delta_callback` | `(delta_text: str) -> None` | 流式输出每个文本 delta |
| `interim_assistant_callback` | `(message: dict) -> None` | 流式模式下产生完整 assistant 消息 |
| `tool_gen_callback` | `(tool_call: dict) -> None` | 工具调用生成时 |
| `status_callback` | `(status_text: str) -> None` | 状态消息更新（用于 gateway 平台） |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `model` | `str` | 当前使用的模型名 |
| `base_url` | `str` | 当前 API 端点 URL（可写属性，setter 会同步更新内部缓存） |
| `provider` | `str` | 当前提供商标识 |
| `api_mode` | `str` | 自动检测的 API 模式（`chat_completions` / `codex_responses` / `anthropic_messages`）|
| `platform` | `str` | 用户平台标识 |
| `session_id` | `str` | 当前会话 ID |
| `quiet_mode` | `bool` | 是否抑制 CLI 输出 |
| `max_iterations` | `int` | 最大迭代次数 |
| `save_trajectories` | `bool` | 是否保存轨迹 |
| `ephemeral_system_prompt` | `str` | 自定义系统提示 |
| `iteration_budget` | `IterationBudget` | 迭代预算对象 |

---

## API 模式

`api_mode` 自动检测，也可显式设置：

| 模式 | 适用场景 | API 协议 |
|------|---------|---------|
| `chat_completions` | OpenAI 兼容 / OpenRouter / 大多数第三方 | `/v1/chat/completions` |
| `codex_responses` | OpenAI Codex / GPT-5.x / 直接 OpenAI URL | Responses API |
| `anthropic_messages` | Anthropic 原生 / Anthropic 兼容第三方 | Messages API |

自动检测逻辑：
- URL 含 `anthropic.com` → `anthropic_messages`
- provider 为 `openai-codex` → `codex_responses`
- GPT-5.x 模型 → 自动升级 `codex_responses`
- URL 以 `/anthropic` 结尾 → `anthropic_messages`（第三方兼容端点）
- 其他情况 → `chat_completions`

---

## 线程安全

**`AIAgent` 实例不是线程安全的。** 每个线程/任务必须创建独立的实例：

```python
# ✅ 正确
def process_task(prompt):
    agent = AIAgent(model="...", quiet_mode=True, skip_memory=True)
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor() as ex:
    results = list(ex.map(process_task, prompts))

# ❌ 错误 - 共享实例
agent = AIAgent(model="...")
with concurrent.futures.ThreadPoolExecutor() as ex:
    results = list(ex.map(agent.chat, prompts))  # 数据竞争！
```

---

## 资源清理

- `chat()` 和 `run_conversation()` 完成后自动清理资源
- 长时间运行的程序应确保每个对话正常完成
- `close()` 提供额外的安全网，清理可能残留的后台进程
- `shutdown_memory_provider()` 在真正的会话边界调用，非每轮调用
