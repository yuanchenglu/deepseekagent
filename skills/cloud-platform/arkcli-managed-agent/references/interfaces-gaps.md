# 接口链路与 Gap

## 接口链路

- Agent: `CreateAgent` / `GetAgent` / `ListAgents` / `UpdateAgent` / `DeleteAgent` / `ListAgentVersions`
- Skill: SkillHub `ListMarketSkills` + data-plane `POST /api/v3/skills` for `CreateSkill` + TOP `GetSkill`
- Env: `CreateEnvironment` / `GetEnvironment` / `ListEnvironments` / `UpdateEnvironment` / `DeleteEnvironment`
- Session: `CreateSession` / `GetSession` / `ListSessions` / `UpdateSession` / `DeleteSession`
- Session data-plane: `GET/POST /api/v3/sessions/:session_id/resources`, `GET/POST /api/v3/sessions/:session_id/events`, `GET /api/v3/sessions/:session_id/events/stream`, `GET /api/v3/sessions/:session_id/threads`, `GET /api/v3/sessions/:session_id/threads/:thread_id`
- Files data-plane: `GET/POST /api/v3/files`, `GET/DELETE /api/v3/files/:file_id`
- Memory: `ListMemoryStores` / `CreateMemoryStore` / `ListMemories` / `CreateMemory` 等
- Vault: `ListVaults` / `CreateVault` / `ListOAuthProviders` / `CreateVaultOAuthFlow` / `ListCredentials` / `CreateCredential` 等

## 当前已对齐 / 已有可接受替代

- Agent / Env / Session / Memory / Vault / Credential 主体 CRUD 已有命令面。
- Skill 搜索走 SkillHub `ListMarketSkills`；custom skill zip 上传走数据面 `POST /api/v3/skills`，避免 TOP 大小限制。
- Files API 已有 `list/get/upload/wait/delete`；`session resources add --path` 可自动 upload -> wait active -> mount。
- Session events/list/stream、threads/list/get 走数据面直联，不依赖 ArkBFF。
- Session 主体列表已对齐 `ListSessionsForTop`：`--agent-id` 发送 `AgentIds`，`--page/--limit` 发送 `PageNumber/PageSize`，`--page-all` 使用页码连续拉取。
- `+tail` 已有人类可读 pretty 输出；`+new session` 无参数时是 PRD 会话选择器入口，可继续已有 session 或选择 agent/env 起新 session；`+new session <agent-id> --environment-id <env-id>` 固定创建新 session 后 one-shot/stdin/TTY REPL，支持 `/allow`、`/deny`、`/interrupt`。`+chat <prompt>` 保留为 Responses API 快速对话。继续已有 session 也可走 `agent session events send/stream` 或 `+tail`。
- `+debug` 已聚合 session/events/resources/threads；`+export` 已导出可见诊断包。
- `+new-agent --fork` 已支持复制已有 Agent，并默认用 `copy-<source-name>` 命名。
- `+iterate` 已支持 GetAgent 当前版本 -> 可选 UpdateAgent -> CreateSession -> `--message` one-shot / TTY REPL；`--environment-id/--env-id` 是可选参数，未传时真实执行会用 `ListEnvironments` 自动选择当前项目最近创建的 Environment；没有可用环境才要求用户创建或显式传入。
- 默认 Tools 已对齐当前实现：不传 `--tool` 时发送 `agent_toolset_20260701`，含 bash/read/write/edit/glob/grep/web_fetch/web_search；传 `--tool` 时按完整数组全量覆盖。

## 当前 Gap

- PRD 中 `arkcli +new-agent "..."` 的 CLI 内置 LLM draft + confirm 未实现；当前由调用 arkcli 的 AI agent 负责自然语言理解、模型/skill/tools 选择，再调用结构化 `+new-agent` 或 `agent agent create`。
- PRD 中 `+outcome` shortcut 未实现。
- `+new session` 选择器已覆盖 P0 交互链路，但 token 数、近 7 天 session 次数等 PRD 展示字段依赖后端返回；当前只展示接口可可靠取得的 id/name/title/status/time/version。
- `+iterate` 尚未实现 PRD 的 TTY environment/resource 选择器和富 diff；当前省略 environment 时自动选择最近创建项，`--diff` 输出结构化请求预览。
- Session resources 原生 get/update/delete 未完全暴露；CLI get 由 list 派生，update/delete unsupported。
- `session resources add` 只封装了 file / local path 体验；`github_repository`、复杂 `memory_store` 等资源只能在 `session create --resource` 或底层 payload 中手写，缺少友好 typed flags 和 add 链路。
- Event send 已支持 `--events` 数组和基础 text/tool confirmation，但尚未覆盖 PRD 的多模态 `--image @file` / 自动 Files API upload 等便捷参数。
- `+export` 中 workspace tarball / memory snapshot 暂无可用读取接口，只能在 manifest 中标 unsupported。
- `arkcli agent +mcp-login` 只对后端 provider 列表中 `CredentialType=mcp_oauth` 的 URL 可靠；static bearer provider 走手动 credential create。Notion / Lark Base 等 provider 仍受后端 metadata discovery 可用性限制。
- PRD 示例中的 inline/local skill 目录形态未做成直接 `--skill '{type:inline,...}'`；当前推荐路径是本地 zip 用 `agent skill create --zip` 或 `agent agent create --skill-zip` 上传成 custom skill。
- `agent agent list` 默认拉单页；需要遍历全部候选时使用全局 `--page-all`，并按数据量设置 `--page-limit`。模糊复制/查找若仍返回多个候选，需要让用户确认。
- Env 创建对线上后端需要显式 `Config.Networking`；PRD 中只传 `{Type: cloud}` 的简写不够用，skill 文档已按线上行为改为 `{Type: cloud, Networking: {Type: unrestricted}}`。
