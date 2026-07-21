# Skills

## Skill 选择

- 创建 Agent 的默认 Skill 选择顺序是 custom 优先、market 兜底。只要用户没有明确指定 market，先查本账号 custom skill；custom 没有合适候选后再搜索 market。用户明确指定 market 时可以跳过 custom。
- Market skill：custom 没有命中或用户明确要求 market 时使用 `agent skill search/list`，创建时传 `{type: skill_hub, skill_id: <id>, version: <version>}`。
- Custom skill：本账号已有 custom skill 的默认选择流程是按需分页：先取第一页 100 条，由调用 arkcli 的 AI agent 按名称、描述和能力判断；没有合适候选时，再使用返回的 `NextPage` 继续取下一页，直到命中或没有下一页。不要一开始用用户描述做服务端 `Name` 过滤，也不要默认一次性拉完整 catalog。CLI 内部入口叫 `ListSkillsForTop`，实际 TOP Action 是 `ListSkills`。只使用该接口返回的 `skill-...` ID；同接口返回的 `s-...` 不作为 custom skill 使用。
- 创建 Agent 时可直接传裸 custom ID：`--skill skill-xxx`，CLI 会按 custom skill 调 TOP `ListSkills` 补 `LatestVersion`。裸 `--skill s-xxx` 会被拒绝；`s-...` 只从 `ListMarketSkills`/SkillHub 链路来。
- Custom skill：用户给本地 zip 时，用 `agent skill create --zip` 或 `agent agent create --skill-zip`，返回后作为 `{Type: custom, SkillId, Version}` 注入。
- Custom skill 上传走数据面 `POST /api/v3/skills`，不是 TOP `CreateSkill`；需要当前 profile 有可用 ARK API Key。
- `agent skill get <id>` 调的是 TOP `GetSkill`，用于本账号 custom skill；批量查本账号 custom skill 用 `list --source custom`。market skill 详情不要拿它查。
- `agent skill search/list` 调 SkillHub `ListMarketSkills`。SSO 登录态走本地 STS 直签，AK/SK profile 走 AK/SK 直签；不要走 ArkBFF 或 top_proxy pre-sign。
- 选择 market skill 时看 `Items[].Name`、`Description`、`Keywords`、`EvaluationScore`、`LatestVersionStatus.Version`；创建入参可直接取返回的 `AgentSkills` 或手动组 `{Type: skill_hub, SkillId, Version}`。
- 选择 custom skill 时先读取第一页完整 `Items`，综合比较 `Id`、`Name`、`Description`、`LatestVersion`，不要只看第一条或只依赖服务端关键词匹配；如果没有足够相关的候选，再用 `NextPage` 继续读取下一页。`AgentSkills` 只会包含 `skill-...` custom skill。确认候选后可直接取 `AgentSkills`，或传裸 `--skill <Items[].Id>`。
- 多个候选接近时列候选让用户选；用户要求自动完成时选相关度最高、版本最明确的一项。通用数据分析优先考虑覆盖面广的分析 skill，再按需要追加 Excel/CSV/报表/可视化类 skill。
- 分页选择优先使用“按需读取”：第一页使用 `--limit 100`，后续把上一次响应的 `NextPage` 原样传给 `--page`。只有用户明确要求完整清单、需要离线分析全部 Skill，或多页都没有命中时，才使用 `--page-all`；它受全局 `--page-limit` 限制，不能把截断的 catalog 当成完整候选集。
- 不要把 `Items[].Id` 和 `LatestVersionStatus.VersionId` 混用：创建 Agent 要传 `SkillId` + 语义版本 `Version`，不是 `VersionId`。

## 常用命令

```bash
arkcli agent skill search "Excel 数据分析" --limit 10 --format json
arkcli agent skill list --query "Excel 数据分析" --limit 20 --format json
arkcli agent skill list --source custom --name "我的数据分析" --limit 20 --format json
arkcli agent skill list --source custom --limit 100 --format json
# 若上一页返回 NextPage 且没有合适候选，再继续：
arkcli agent skill list --source custom --limit 100 --page '<NextPage>' --format json
arkcli --page-all --page-limit 20 agent skill list --source market --format json
arkcli agent skill create --zip ./my-skill.zip --display-title "My Skill" --format json
arkcli agent agent create --name arkcli-local-skill-agent --model <items[].model from agent model list> --skill-zip ./my-skill.zip --format json
arkcli agent agent create --name arkcli-existing-custom-skill-agent --model <items[].model from agent model list> --skill skill-xxx --format json
```

`agent skill list --source custom` 默认先输出一页 custom catalog 和 `AgentSkills`。调用 arkcli 的 AI agent 应先判断这一页；没有合适候选时沿 `NextPage` 继续请求，不要臆造 `SkillId`，也不要在当前页没有相关性判断时直接选第一条。需要完整 catalog 时再加 `--page-all`。

`agent skill search --source custom "<name>"` 仍可用于用户明确指定 skill 名称、目录很大需要缩小候选，或对全量 catalog 做二次检索；它不是自然语言创建 Agent 时的默认入口。

`agent skill list --page-all` 会自动使用每页 100 条：custom skill 沿 TOP `NextPage -> Page` 拉取；market skill递增 `PageNumber`，并根据 `TotalCount` 停止。全局 `--page-limit` 仍是最多请求页数。按需分页时，custom skill 的 `--page` 对应 TOP 的 `Page` token。
