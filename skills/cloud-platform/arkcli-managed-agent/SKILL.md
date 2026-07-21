---
name: arkcli-agent
version: 1.1.0
description: "arkcli agent：管理 ARK Managed Agents，包括 Agent / Skill / Env / Session / File / Memory Store / Vault / MCP OAuth。控制面优先走 ForTop/OpenTOP，Session 运行时和 Files 走数据面直联。"
metadata:
  requires:
    bins: ["arkcli"]
  cliHelp: "arkcli agent --help"
---

# arkcli agent

**CRITICAL — 开始前 MUST 先读取 [`../arkcli-shared/SKILL.md`](../arkcli-shared/SKILL.md)。**

当用户需要创建、查询、调试或联通 ARK Managed Agent 时使用本 skill。核心原则：先用稳定产品命令，不要直接猜 OpenTOP Action；Session 运行时资源、事件、线程、Files API 走数据面直联；MCP OAuth 登录先查后端 provider，再用 `arkcli agent +mcp-login`。

执行前按“先选路径”读取对应 reference；只读相关 reference，不需要一次性加载全部细节。用户请求如果已经明确是创建、复制、挂文件、聊天、MCP 登录等写操作，完成必要确认/消歧后直接执行，不要只给命令建议。

## 先选路径

| 用户意图 | 首选命令 | 细节 |
| ---- | ---- | ---- |
| 创建 / 更新 / 删除 Managed Agent | `arkcli agent agent ...` | [`references/agent.md`](references/agent.md) |
| 复制已有 Agent 并改名 / 局部覆盖配置 | `arkcli +new-agent --fork <agent-id> [--name <new-name>]` | [`references/agent.md`](references/agent.md#复制-agent) |
| 为创建 Agent 选择可用模型 | `arkcli agent model list` | [`references/agent.md`](references/agent.md#模型选择) |
| 创建 Agent 时选择 Skill | 默认先查 custom，未命中再查 market；用户明确指定 market 时跳过 custom | [`references/skills.md`](references/skills.md) |
| 查询/使用本账号 custom skill | 先 `agent skill list --source custom --limit 100`，无匹配时沿 `NextPage` 传 `--page` 继续；需要完整候选时再用 `--page-all` / `--skill <skill-id>` | [`references/skills.md`](references/skills.md) |
| 上传本地 custom skill zip | `arkcli agent skill create --zip <file>` 或 `agent agent create --skill-zip <file>` | [`references/skills.md`](references/skills.md) |
| 创建运行环境 / 会话 | `arkcli agent env ...` / `arkcli agent session ...` | [`references/session-files.md`](references/session-files.md) |
| 选择/继续 Managed Agent 会话 | `arkcli +new session` | [`references/events-chat.md`](references/events-chat.md) |
| 直接创建新会话并聊天 | `arkcli +new session <agent-id> --environment-id <env-id>` | [`references/events-chat.md`](references/events-chat.md) |
| 给已有会话发消息或实时看回复 | `arkcli agent session events send <session-id>` / `arkcli +tail <session-id>`；多事件按顺序串行发送且非原子，支持异类 event 顺序组合 | [`references/events-chat.md`](references/events-chat.md) |
| 看 session 诊断 / 导出诊断包 | `arkcli +debug <session-id>` / `arkcli +export <session-id>` | [`references/debug-export.md`](references/debug-export.md) |
| 上传文件并挂到已有 session | `arkcli agent session resources add <session-id> --path <file>` | [`references/session-files.md`](references/session-files.md) |
| 只上传 / 查询 Files API 文件 | `arkcli agent file upload/list/get/wait/delete` | [`references/session-files.md`](references/session-files.md) |
| 管理 memory store / memories | `arkcli agent memory-store ...` | [`references/interfaces-gaps.md`](references/interfaces-gaps.md) |
| 查询可挂载 MCP / 管理 Vault / Credential / MCP OAuth | `arkcli agent vault oauth-provider list` / `arkcli agent vault ...` / `arkcli agent +mcp-login ...` | [`references/mcp-vault.md`](references/mcp-vault.md) |

## 认证与 Profile

- 业务命令前先 `arkcli auth status --format json`。未登录、SSO 过期、STS refresh 失败时先处理登录。
- 当前数据面 Files / Session resources / events / threads 需要可用 ARK API Key。CLI 会优先使用 profile 里的 `api_key`，也可用全局 `--api-key` 覆盖。
- 线上环境已就位，默认走 `--env prod`，不要再默认跑 stg。
- 非交互 SSO 登录是两段式：先 `arkcli auth login --no-browser` 拿 URL；用户贴回 base64 code 后，再跑 `arkcli auth login --no-browser --code <code>`。

## List 分页

- 支持分页契约的列表可加全局 `--page-all`；未显式传单页大小时，CLI 默认每页取 100 条。默认最多请求 10 页，可用 `--page-limit <N>` 调高，`--page-delay <ms>` 控制页间隔。
- 已支持：Agent/版本、Env、Session、Skill market/custom、Memory Store/Memories、Vault/Credentials/OAuth Provider、Files、Session Events/Threads。CLI 会分别按后端契约使用 `Page`、`PageNumber`、`PageToken`、`after`，并合并结果。
- `agent model list`、`memory-store creators`、`session resources list` 没有可用分页契约，不要为它们假设 `--page-all` 能补全结果。命中 `--page-limit` 后应检查返回的 `NextPage`、`has_more` 或 `TotalCount`，判断是否仍有未拉取数据。

## 删除确认

- Managed Agent 的破坏性 `delete` 命令在真实 TTY 且未传 `--yes` 时会显示不可逆警告并询问 `[y/N]`；输入 `y/yes` 才会调用后端，其他输入会取消。
- 非交互环境（AI Agent、CI、管道）不会读取 stdin；未传 `--yes` 时返回 `type=requires_confirmation`，不会调用后端。只有用户已经明确确认删除目标后，调用方才可以补 `--yes` 重试。
- `--dry-run` 只预览请求，不删除资源，也不弹确认。

## 命令速查

| 命令 | 说明 |
| ---- | ---- |
| `arkcli agent agent list/get/create/update/delete/versions` | Agent CRUD + 版本 |
| `arkcli agent model list` | 查询 Managed Agent 模型白名单；`--query` 用模型目录详情增强/排序白名单；输出 `items[].model` 可直接作为 `--model` |
| `arkcli +new-agent` | Agent create 增强入口；支持 `--fork/--from` 复制已有 Agent 后创建新 Agent |
| `arkcli +iterate` | 更新 Agent 配置，创建新 Session，并进入 one-shot/REPL 试运行；`--environment-id/--env-id` 可选，省略时自动选择最新环境 |
| `arkcli agent skill search/list/get/create` | Market skill 检索、本账号 custom skill 查询、本地 zip 上传；`list/search --source custom` 走 TOP `ListSkills` |
| `arkcli agent env list/get/create/update/delete` | Environment CRUD；当前 `env list` 没有 `--status`，状态筛选规则见 `session-files.md` |
| `arkcli agent session list/get/create/update/delete` | Session CRUD |
| `arkcli agent session resources list/add/get` | 数据面 session resources；get 是 CLI 基于 list 的本地筛选 |
| `arkcli agent session events list/send/stream` | 数据面 events；stream 输出 SSE/NDJSON 行；`user.custom_tool_result` 必须带 `custom_tool_use_id`，`user.tool_result` 仅允许 self_hosted，CLI 会前置校验 |
| `arkcli agent session threads list/get` | 数据面 threads |
| `arkcli agent file list/get/upload/wait/delete` | 数据面 Files API |
| `arkcli agent memory-store list/get/create/update/delete` | Memory Store CRUD |
| `arkcli agent memory-store memories list/get/create/batch-create/update/delete` | Memory CRUD |
| `arkcli agent vault list/get/create/update/delete` | Vault CRUD |
| `arkcli agent vault oauth-provider list` | 查询后端已注册 MCP Provider；返回的 MCP server 信息可用于 Agent `--mcp-server` |
| `arkcli agent vault oauth-flow create` | 裸创建 Vault OAuth Flow，适合脚本自带 redirect URL |
| `arkcli agent vault credentials list/get/create/update/delete` | Credential CRUD |
| `arkcli agent +mcp-login` | 托管 MCP OAuth 登录：本地 callback + CreateVaultOAuthFlow + 等待 credential 创建 |
| `arkcli +chat <prompt>` | Responses API 快速对话；不要把它当 Managed Agent session 入口 |
| `arkcli +tail <session-id>` | 人类可读 event stream |
| `arkcli +new session` | Managed Agent session 选择器；可继续已有 session，或选 agent/env 起新 session |
| `arkcli +new session <agent-id> --environment-id <env-id>` | Managed Agent 新 session 直达入口；固定先创建新 session，再 REPL / one-shot |
| `arkcli +debug <session-id>` | 聚合 session、events、resources、threads 做诊断 |
| `arkcli +export <session-id>` | 导出诊断 tar.gz |

复杂字段如 `Tools`、`Skills`、`McpServers`、`Multiagent`、`Metadata`、`Tags` 支持 JSON/YAML 文件、stdin 或结构化 flags。请求结构与 TOP CamelCase 对齐；inline 对象兼容常见 lower/snake case alias。创建成功回显必须展示服务端最终的身份、模型、`System`、Tools、Skills、MCP 和扩展配置，不能只展示摘要；需要核对完整结果时用 `agent agent get <agent-id> --format json` 或 `--format yaml`。

Memory get 的 `--view` 语义：默认按 `basic` 请求，只返回 metadata 和 `ContentSha256`；`--view full` 保留 Content。若服务端仍在 basic 下返回 Content，CLI 会在输出层剥离 Content，但这只能控制输出，不能挽回已经产生的网络传输；服务端仍需正确实现 View 参数以节省带宽。

## 参考

- [`references/agent.md`](references/agent.md)：创建、复制、查找 Agent、默认工具。
- [`references/skills.md`](references/skills.md)：Market skill 搜索、custom skill zip 上传、skill ref 组装。
- [`references/session-files.md`](references/session-files.md)：Env / Session / Files API / Session resources。
- [`references/events-chat.md`](references/events-chat.md)：events send/list/stream、`+new session` 选择器、`+tail`。
- [`references/mcp-vault.md`](references/mcp-vault.md)：Vault、Credential、MCP OAuth、Agent 挂 MCP。
- [`references/debug-export.md`](references/debug-export.md)：`+debug`、`+export`、端到端验证模板。
- [`references/interfaces-gaps.md`](references/interfaces-gaps.md)：接口链路和当前 gap。
