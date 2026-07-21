# Agent

## 创建 Agent SOP

用户说“创建一个 XXX agent / 智能体”时按下面链路执行，不要只拼一个 `agent create`。

1. `arkcli auth status --format json`，确认登录、profile、project、API key。
2. 如果用户没有给精确模型，先按用户意图增强模型白名单：`arkcli agent model list --query "<用户意图/领域>" --primary-only --format json`。它以 ArkModels 中 `agent_support=true` 的 Managed Agent 白名单为候选集合，再用模型目录 / `models search` 的能力、上下文、模态、排序信号补充 `detail` 字段并把命中项排前；把返回的 `items[].model` 原样作为 `--model`。
3. 把用户意图扩展成 skill 选择上下文。例：数据分析 -> `数据分析 Excel CSV 表格 BI SQL`；代码助手 -> `代码 编程 repo bash`；文档写作 -> `文档 写作 总结 Markdown`。
4. 创建 Agent 默认优先从本账号已有 custom skill 中选择，即使用户没有显式说“使用 custom skill”：按需执行 `arkcli agent skill list --source custom --limit 100 --format json`。由 AI agent 读取这一页全部 `Items`，按名称、描述、能力和版本判断；没有合适候选时，将响应中的 `NextPage` 原样传给 `--page` 继续拉下一页，直到命中或没有下一页。不要只调用 `search --source custom "<query>"` 后选第一条；用户明确要求完整清单或需要离线分析时才使用 `--page-all`。
5. custom skill 分页查完仍没有合适候选，或用户明确要求 market/SkillHub skill 时，再搜索：`arkcli agent skill search "<query>" --limit 10 --format json`。根据名称、描述、能力标签、版本选择 skill。不要臆造 `SkillId`；搜不到时可创建基础 agent，并说明未找到匹配 skill。
6. 组装参数：默认 speed `standard`，补领域化 system prompt，挂相关 skill。线上测试资源名使用 `arkcli` 前缀；用户没给名字时生成 `arkcli-<domain>-agent-<YYYYMMDDHHMMSS>`，如 `arkcli-data-agent-20260707153000`。
7. 先 `--dry-run --format json` 看 `Model`、`Skills`、默认 `Tools`、`McpServers`。
8. 真实创建时，CLI 会先检查 Managed Agent 能力和模型开通状态：模型未开通会走共享模型开通确认链路；非交互环境不会自动开通，返回 `model_activation_required`。Managed Agent 产品/能力未开通时，TTY 下会提示用户确认并调用前端同款 `OpenChargeItems(ResourceType=DataManagedAgentSum, ResourceNames=[sandbox, web_search])`，非交互环境返回 `managed_agent_activation_required`，不会自动开通。
   - 如果已在对话中拿到用户明确确认，非交互调用可重跑原命令并同时加 `--yes` 和环境变量 `ARKCLI_ALLOW_HEADLESS_ACTIVATION=1`。不要在没有用户确认时设置该环境变量。
9. 真实创建后立刻 `agent agent get <agent-id> --format json` 确认落库。对用户回显时必须展示服务端最终配置，不要只展示“已创建”或单独摘要某个字段。
10. 用户要求端到端验证时，再创建 env/session，发送一条最小消息，拉 events/thread/resources。除非用户明确要求清理，不要删除创建出的资源。

模型候选、skill 候选、MCP provider 候选互不依赖；创建前可以并行查：

```bash
arkcli agent model list --primary-only --format json
arkcli agent model list --query "<capability-query>" --primary-only --format json
arkcli agent skill search "<capability-query>" --limit 10 --format json
arkcli agent vault oauth-provider list --limit 100 --format json
```

## 模型选择

`agent agent create --model` 必须传精确可用的模型 ID。不要凭印象写裸模型名或展示名。

首选来源是按用户意图搜索：

```bash
arkcli agent model list --query "数据分析 Excel CSV SQL agent" --primary-only --format json
```

`--query` 模式仍以 ArkModels 白名单为主表，不从模型目录反向生成候选。它会调用 `models search` 拿详细信息并增强白名单模型：命中的白名单模型会带 `detail` 字段并排在前面；未命中的白名单模型仍保留，只是没有 `detail`。`detail` 字段包含用于判断适配度的信号，例如 `display_name`、`description`、`context_window`、`input_modalities`、`output_modalities`、`capabilities`、`lifecycle_status`。

只想列出可用白名单时：

```bash
arkcli agent model list --primary-only --format json
```

选择规则：

- 默认只从 `agent_support=true` 的结果里选；`agent model list` 默认已经过滤非 Agent 模型。
- 优先选 `primary_version=true` 的条目；同名多版本时不要跨条目混拼。
- 创建时传返回的 `model` 字段，例如 `items[0].model`，不要传返回里的 `id`。
- 用户明确要求某个模型族时，用 `--name <keyword>` 缩小 Agent 白名单范围；有自然语言意图时仍优先加 `--query`：

```bash
arkcli agent model list --query "复杂推理 Agent" --name doubao-seed-2-0-pro --primary-only --format json
```

- 需要排障或确认为什么某模型不可选时，加 `--include-all`，查看 `agent_support=false` 的条目。
- 有硬指标时使用结构化过滤：`--min-context-window 200000`、`--capability thinking`、`--capability functioncall`、`--multimodal`、`--input-modality text,image`、`--output-modality text`、`--strict-filter`。
- 用户已经给了完整模型 ID 时可以直接用，但如果创建失败提示模型不支持 / 不存在，回到 `agent model list` 重新选择。

模型值示例：

```bash
arkcli agent agent create \
  --name arkcli-data-analysis-agent-20260706 \
  --model <items[].model from agent model list> \
  --system "You are a data analysis agent. Help users inspect datasets, reason about metrics, write analysis code, and summarize findings clearly." \
  --format json
```

## 复制 Agent

用户说“复制 / fork / 基于已有 agent 改一个新版”时，优先用 `+new-agent --fork`，不要手动 get 后重新拼完整 create 请求。

```bash
arkcli +new-agent --fork agent-xxx --dry-run --format json
arkcli +new-agent --fork agent-xxx --format json
```

- 用户明确给了源 `agent-id` 但没给新名字时，不要停下来只问名字；CLI 会先 `GetAgent`，默认用源 Agent 的 `Name` 加 `copy-` 前缀，即 `copy-<source-agent-name>`。如果源 name 为空，才 fallback 到 `copy-<agent-id-tail>`。
- 如果用户只说“复制那个数据分析 agent”但没给 ID，先用 `agent agent list --name <keyword>` 查候选；候选唯一时可继续复制，候选多个时必须让用户确认准确 `agent-id`。
- 复制前先跑一次 `--dry-run --format json` 检查最终 request。若用户已经明确要求“复制/创建”，dry-run 通过且无多候选/缺权限等歧义时，继续执行真实 `+new-agent --fork ... --format json`。
- `--fork` / `--from` 会先 `GetAgent`，复制源 Agent 的 `Model`、`System`、`Description`、`Tools`、`Skills`、`McpServers`、`Multiagent`、`Metadata`、`Tags`，再调用 `CreateAgent` 创建新 Agent。
- `--name` 可显式覆盖默认复制名。
- 用户传入的 create flags 会覆盖复制来的配置，例如 `--system`、`--model`、`--description`、`--skill`、`--tool`、`--mcp-server`。
- P0 语义里，`--skill` / `--tool` / `--mcp-server` 是替换对应列表，不是追加；需要追加时先 dry-run 看源配置，再传完整列表。
- 默认创建成功后会再次 `GetAgent` 回显最终配置；只想拿 `CreateAgent` 响应用 `--no-echo`。
- 创建结果中的 `System` 就是实际生效的 system prompt。人类可读回显至少必须展示以下字段：
  - 身份：`Id`、`Name`、`Description`、`Version`、`ProjectName`
  - 模型：`Model.Id`、`Model.Speed` 及服务端返回的其他模型配置
  - Agent 行为：完整 `System`、`Tools`、`Skills`、`McpServers`
  - 扩展配置：`Multiagent`、`Metadata`、`Tags`
  - 服务端返回的时间字段：`CreateTime`/`CreatedAt`、`UpdateTime`/`UpdatedAt`
- 结构化输出使用 `agent agent get <agent-id> --format json` 或 `--format yaml` 保留服务端返回的全部非空字段；调用方不得丢弃、截断或用摘要替换配置字段。人类可读摘要可以压缩时间、ID 等展示格式，但不能隐藏上述配置内容。
- 如果提交的 `request.System` 非空但创建响应或 `GetAgent.Result.System` 为空，优先报告“服务端未回显/未落库”，不要假设 prompt 已生效，并保留请求值与服务端值供排查。
- `+new-agent` 当前不做 LLM 起草和 template；自然语言理解、参数选择、用户确认由调用 arkcli 的 AI agent 完成。
- `+new-agent` 与 `agent agent create` 共用创建链路：真实创建前会做 Managed Agent / 模型开通预检。遇到 `managed_agent_activation_required` 或 `model_activation_required` 时，不要通过自动加 `--yes`、自动购买套餐或自动调用开通接口绕过确认；需要真人在 TTY 确认，或用户显式要求无人值守并设置 `ARKCLI_ALLOW_HEADLESS_ACTIVATION=1`。

## 迭代 Agent 并新建 Session

用户说“改一下这个 agent 然后试试 / 更新 system 后跑一遍 / 调整 tools 后开新 session 验证”时，用 `+iterate`，不要手动串三四条命令。

`+iterate` 会：

1. `GetAgent` 读取当前版本。
2. 如果传了更新 flag，则用当前版本调用 `UpdateAgent`。
3. 调 `CreateSession` 起一个新 session。
4. 有 `--message` 时发送首条消息并流式输出；TTY 且无 `--message` 时进入 `+new session` REPL；非 TTY 无 message 时只输出结构化结果。

```bash
arkcli +iterate agent-xxx \
  --system @./prompts/da-v2.md \
  --message "用新版配置说明你会如何分析 sales.csv" \
  --format json
```

- `--environment-id` / `--env-id` 可选；省略时 CLI 使用当前项目最近创建的 Environment。对环境有明确要求时应显式传入。
- 不要因为用户没有提供环境 ID 就中断或要求补参：真实执行时 CLI 会用 `ListEnvironments` 按 `CreateTime Desc, Limit=1` 自动选择最新环境；只有没有可用环境时，才提示先创建环境或显式传入 `--environment-id`。
- `--diff` / `--dry-run` 不调用 `ListEnvironments`，会在预览的 `CreateSession.EnvironmentId` 中显示 `<auto-select-latest-environment>`；这是占位符，不要把它作为真实环境 ID 发送。
- `--resource`、`--vault-id` / `--vault-ids`、`--tags` 会传给新 session。
- `--diff` 或 `--dry-run` 只预览 `UpdateAgent`、`CreateSession`、chat send/stream 请求，不改远端；省略环境时预览会显示 `<auto-select-latest-environment>`。
- `--no-chat` 只更新 agent 并创建 session，不发送消息、不进 REPL。
- `--tool` / `--skill` / `--mcp-server` 在 iterate 中仍是全量替换语义。

## 脚本输出

`+new-agent` 输出兼容 `data.agent` 结构，适合脚本提取：

```bash
arkcli +new-agent --fork agent-xxx --format json --transform "data.agent.id"
arkcli +new-agent --fork agent-xxx --format yaml > new-agent.yaml
arkcli +new-agent --fork agent-xxx --no-echo --format json
```

- `--transform "data.agent.id"` 只输出新 Agent ID。
- `--format yaml` 会把结构化结果渲染成 YAML，适合落地为文件检查。
- `--no-echo` 跳过创建后的 `GetAgent` 回显，只输出 `CreateAgent` 响应；默认不加时会再次 `GetAgent` 并回显服务端最终配置。
- 需要确认最终 prompt 时不要使用 `--no-echo`；创建后读取 `data.agent.system`（`+new-agent`）或 `Result.System`（`agent agent create/get`），并原样展示给用户。
- PRD 里的 `arkcli +new-agent "..."` 自然语言起草模式当前未实现；AI agent 应先把自然语言转成结构化 flags，再调用 `+new-agent` 或 `agent agent create`。

## 查找 Agent

- `arkcli agent agent list` 默认只调用一次 TOP `ListAgents`，返回单页 `Items`、`NextPage`、`Total`。
- 需要完整遍历时加全局 `--page-all`；CLI 会沿服务端 `NextPage` 拉取并合并 `Items`，最多拉 `--page-limit` 页，页间隔由 `--page-delay` 控制：

```bash
arkcli agent agent list --page-all --page-limit 10 --format json
```

- 未加 `--page-all` 时，不要默认假设已经拿到账号下全部 Agent。可以读取返回的 `NextPage` 手动继续：

```bash
arkcli agent agent list --page <NextPage> --limit 50 --format json
```

- 用户给明确 Agent ID 时，直接用 `arkcli agent agent get <agent-id> --format json`。
- 用户只给名字或模糊描述时，先用过滤缩小范围：

```bash
arkcli agent agent list --name <keyword> --limit 20 --format json
```

- 如果筛出多个候选，不要臆造选择；列出候选的 `Id`、`Name`、`Description`、`UpdatedAt/UpdateTime` 让用户确认。
- 用户要“复制某个 agent”但没给 ID 时，先通过 `list --name/--ids` 或候选确认拿到准确 ID，再走 `+new-agent --fork <agent-id>`。

## 默认 Agent 工具

创建 Agent 时，如果用户没有显式传 `--tool`，且请求体里没有 `Tools`，CLI 调 CreateAgent 时自动传入默认 `Tools` 数组：

```yaml
Type: agent_toolset_20260701
Name: agent_toolset_20260701
Configs:
  - Name: bash
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: read
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: write
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: edit
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: glob
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: grep
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: web_fetch
    Enabled: true
    PermissionPolicy: { Type: always_allow }
  - Name: web_search
    Enabled: true
    PermissionPolicy: { Type: always_allow }
DefaultConfig:
  Enabled: true
  PermissionPolicy: { Type: always_allow }
```

- 用户明确传 `--tool '[]'` 表示关闭默认工具，必须尊重。
- 用户显式传任意 `--tool` 时，传入值就是完整 `Tools` 数组，CLI 不追加/合并默认工具。
- 需要 `advisor` 且保留默认工具时，必须显式传完整数组，例如 `--tool '[{Type: agent_toolset_20260701, Name: agent_toolset_20260701}, {Type: evolution, Configs: [{Name: advisor, Enabled: true}]}]'`。
- 不要重复手写默认工具，除非用户要调整权限或显式关闭。

### 修改默认工具权限

用户说“把 `<tool-name>` 策略设为总是询问 / 需要确认 / always ask”时，不要只传该工具的一项 config。由于 `--tool` 是完整数组替换，必须传完整默认 toolset，并只覆盖对应工具的 `PermissionPolicy.Type`。

权限策略值：

- 自动放行：`always_allow`
- 总是询问 / 需要用户确认：`always_ask`

例如“创建一个数据分析 agent，write 策略设为总是询问”：

```bash
arkcli agent agent create \
  --name arkcli-data-analysis-agent-20260706 \
  --model <items[].model from agent model list> \
  --system "You are a data analysis agent. Help users inspect datasets, reason about metrics, write analysis code, and summarize findings clearly." \
  --skill '{type: skill_hub, skill_id: skill-xxx, version: "1.0.0"}' \
  --tool '[{
    Type: agent_toolset_20260701,
    Name: agent_toolset_20260701,
    DefaultConfig: {Enabled: true, PermissionPolicy: {Type: always_allow}},
    Configs: [
      {Name: bash, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: read, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: write, Enabled: true, PermissionPolicy: {Type: always_ask}},
      {Name: edit, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: glob, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: grep, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: web_fetch, Enabled: true, PermissionPolicy: {Type: always_allow}},
      {Name: web_search, Enabled: true, PermissionPolicy: {Type: always_allow}}
    ]
  }]' \
  --format json
```

如果用户要求多个工具不同策略，同样在这一个完整 `agent_toolset_20260701` 的 `Configs` 里同时改，不要拆成多个 `agent_toolset`。

## 示例

```bash
# Agent + Skill
arkcli agent skill search "Excel 数据分析" --limit 10 --format json
arkcli agent agent create \
  --name arkcli-data-analysis-agent-20260706 \
  --model <items[].model from agent model list> \
  --system "You are a data analysis agent. Help users inspect datasets, reason about metrics, write analysis code, and summarize findings clearly." \
  --skill '{type: skill_hub, skill_id: skill-xxx, version: "1.0.0"}' \
  --format json

# Fork existing agent
arkcli +new-agent --fork agent-20260707063932-vbfjd --dry-run --format json
arkcli +new-agent --fork agent-20260707063932-vbfjd --format json
```
