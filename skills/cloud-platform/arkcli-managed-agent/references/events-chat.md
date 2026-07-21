# Events 与 Chat

## Event / Chat 体验

- `agent session list --agent-id <agent-id>` 按 Agent 过滤；CLI 会按 `ListSessionsForTop` 契约发送 `AgentIds` 数组。
- Session 列表使用页码分页：`--page` 对应 `PageNumber`，`--limit` 对应 `PageSize`。需要遍历时使用全局 `--page-all`，并通过 `--page-limit` 控制最多页数。

- `events send` 主动发事件。常用：

```bash
arkcli agent session events send <session-id> --type user.message --text "帮我分析这个数据"
```

- `--events` / `--file` 可以提供多条事件。由于当前线上数据面接口实际只接受单条 event，CLI 会按数组顺序逐条发送；这保证顺序，但不保证原子性。返回结果会标记 `transport=serial`、`atomic=false` 和 `sent` 数量。中途失败时不会自动重试，错误会指出失败的 `event[index]` 以及已经发送的数量。
- 不要把这种 CLI 兼容行为理解成服务端已经支持原子 batch；如果业务必须原子提交，应等待服务端支持多事件请求。
- 多事件可以包含不同 `type`，CLI 不会按类型重排。例如先发送 `user.message` 再发送 `user.interrupt`，服务端会先启动消息对应的 turn，再处理 interrupt；回查时应看到原始 `user.message`、`user.interrupt`，以及被中断的 model request。`user.interrupt` 要在存在 active turn 时发送；对 idle session 发送会产生 `session.error: no active turn to cancel`。

- `events list` 拉历史，支持 `--after/--before` event cursor，`--since/--created-after/--created-before` 时间过滤，`--type` 可重复或逗号分隔。加全局 `--page-all` 后默认 `limit=100`，沿响应 `next_page -> page` 拉取并合并 `data`。
- `threads list` 同样支持全局 `--page-all` 和 `next_page -> page`；`resources list` 当前没有分页契约，不要伪造 page 参数。
- `events stream` 输出机器友好的 SSE data / NDJSON 行。
- `/compact` 验证建议：发送后用 `events list` 或 `+tail` 检查 `agent.thread_context_compacted`。如果只看到对应的 `user.message`、`thread_status_idle`，但没有 compacted 事件，说明 CLI 已正确提交协议，但线上服务端没有实际执行手动压缩，应按服务端能力开关、版本或路由排查；不能把该结果报告为“已压缩”。
- `+tail` 输出人类可读短行，默认归类 `[user]`、`[agent]`、`[thinking]`、`[tool]`、`[tool_result]`、`[model]`、`[status]`、`[action]`、`[error]`、`[outcome]`。机器读取用 `+tail --raw`。
- `+chat <prompt>` 保留为 Responses API 快速对话，不进入 Managed Agent。
- `+new session` 是 Managed Agent session 入口（PRD 早期写作 `+chat` 的地方都按这个命令理解）：
  - `arkcli +new session`：打开交互选择器，先 `ListSessions`，可选择已有 session 进入 REPL；也可选 `[新建]` 后 `ListAgents`、`ListEnvironments`，再 `CreateSession` 进入 REPL。
  - `arkcli +new session <agent-id> --environment-id <env-id>`：直达创建新 session，再发送首条消息或进入 REPL。
  - TTY 下进入 REPL。
  - 非 TTY stdin 或 `--message` 是 one-shot。
  - `/exit` 退出，`/interrupt` 发 `user.interrupt`。
  - `/compact` 和 `/clear` 会按前端同样的 slash envelope 发送 `user.message`；这是协议触发入口，不要仅凭发送成功判断后端已完成操作。`/compact` 成功执行时应在事件流中看到 `agent.thread_context_compacted`，并按服务端语义保留摘要；`/clear` 的具体结果以服务端返回事件为准。二者都等待本轮完成后继续 REPL。
  - `/allow [tool_use_id]`、`/deny [tool_use_id] [reason]` 发送 tool confirmation。
- 已知 `session-id` 的脚本/非交互场景不要用选择器，改用 `arkcli agent session events send <session-id>`、`arkcli agent session events stream <session-id>` 或 `arkcli +tail <session-id>`。
- `+new session` 选择器里的 `[全部]` 会用已知状态集合重新拉取 session，尽量包含 terminated/archived；如果后端新增状态枚举，需要同步更新。
- `+new session` 选择器里的 `[起新 agent]` 目前只提示转去 `arkcli +new-agent "..."`，不会在选择器内嵌自然语言建 agent 流程。
- `events send` 支持多模态便捷参数：
  - `--image file-xxx` 直接发送图片 file source；`--image @./a.png` 或 `--image ./a.png` 会先上传 Files API、等待 active，再发送图片。
  - `--document file-xxx` 直接发送文档/PDF file source；`--document @./a.pdf` 或 `--document ./a.pdf` 会先上传 Files API、等待 active，再发送文档。
  - 图片 content schema：`{type: image, source: {type: file, file_id: ...}}`。
  - 文档/PDF content schema：`{type: document, source: {type: file, file_id: ...}}`。
  - `--image/--document` 不能和 `--event/--events` 混用；手写事件时直接在 `--event/--events` 里按上述 schema 传完整 content。
- Event 关联字段会在 CLI 发送前统一校验，typed flags、`--event`、`--events`、`--file` 行为一致：
  - `user.custom_tool_result` 必须带 `custom_tool_use_id`（typed flag 为 `--custom-tool-use-id`）。它不是所有 event 的全局必填字段，但对 custom tool result 是语义必填，否则结果无法关联到具体的 custom tool 调用。
  - 旧版服务端曾经错误放行缺少该字段的事件，并将它落成空字符串；不要依赖这种兼容行为。当前 CLI 会在请求前 fail-fast，避免产生孤儿事件；服务端也应拒绝该请求。
  - CLI 只校验字段非空，ID 是否存在、是否属于当前 session、是否仍待处理由服务端判断。
  - `user.tool_confirmation` 必须带 `tool_use_id`，且 `result` 只能是 `allow` 或 `deny`。
  - `user.tool_result` 只允许用于 `self_hosted` environment。实际发送时 CLI 会通过 `GetSession -> GetEnvironment` 预检 `Config.Type`；`--dry-run` 不发起预检请求，最终约束仍由服务端负责。
  - raw payload 可使用数据面 snake_case；兼容的 PascalCase 别名会在发送前归一化成 snake_case。

### Custom tool result

`user.custom_tool_result` 用于回传某次 custom tool 调用的结果，必须提供对应的 `custom_tool_use_id`：

```bash
arkcli agent session events send <session-id> \
  --type user.custom_tool_result \
  --custom-tool-use-id <custom-tool-use-id> \
  --content "tool output" \
  --format json
```

等价的结构化事件：

```json
{
  "type": "user.custom_tool_result",
  "custom_tool_use_id": "ctu-xxx",
  "content": [{"type": "text", "text": "tool output"}]
}
```

缺少或传空 `custom_tool_use_id` 时，CLI 返回 validation 错误且不会调用数据面 API。不要用 `user.tool_confirmation` 的 `tool_use_id` 代替；两者属于不同 event 类型。

## 示例

```bash
arkcli agent session list --agent-id <agent-id> --page 1 --limit 20 --format json
arkcli --page-all --page-limit 10 agent session list --agent-id <agent-id> --limit 100 --format json
arkcli agent session events send <session-id> --type user.message --text "<one small test task>" --format json
arkcli agent session events send <session-id> --events '[{"type":"user.message","content":[{"type":"text","text":"先执行一个短任务"}]},{"type":"user.interrupt"}]' --format json
arkcli agent session events send <session-id> --text "看这张图" --image file-xxx --format json
arkcli agent session events send <session-id> --text "总结这个 PDF" --document @./report.pdf --format json
arkcli agent session events list <session-id> --limit 20 --format json
arkcli +new session
arkcli +tail <session-id> --session-thread-id <thread-id>
arkcli +new session <agent-id> --environment-id <env-id> --message "帮我分析这个数据" --format json
```
