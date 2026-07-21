# Session 与 Files

## Env / Session

```bash
arkcli agent env create --name arkcli-<domain>-env-<timestamp> --config '{Type: cloud, Networking: {Type: unrestricted}}' --format json
arkcli agent session create --agent-id <agent-id> --environment-id <env-id> --title arkcli-<domain>-session-<timestamp> --format json
arkcli agent session get <session-id> --format json
```

Session 标准 CRUD 走 OpenTOP；Session resources / events / threads 走数据面直联。
线上创建 cloud env 时需要显式带 `Networking: {Type: unrestricted}`；只传 `{Type: cloud}` 会被后端校验为缺少 `config.networking`。

### Environment 状态筛选

当前 `arkcli agent env list` **没有注册 `--status`**，不要生成下面这种命令：

```bash
arkcli agent env list --status active
```

`ListEnvironments` 后端请求也没有 `Status` 过滤字段；返回的 Environment 对象只有可选的 `ArchiveTime`。需要按状态找环境时，先拉全量，再由调用 arkcli 的 AI Agent 本地筛选：

```bash
arkcli agent env list --page-all --format json
```

- `ArchiveTime` 非空：`archived`
- `ArchiveTime` 为空或字段缺失：`active`
- 前端领域类型虽然预留了 `updating`，但当前返回契约没有可可靠推导它的字段；不要声称支持 `updating` 筛选。
- 不要只过滤默认第一页；状态筛选必须配合 `--page-all`，并关注全局 `--page-limit` 是否导致结果仍被截断。
- env `--page-all` 默认使用 `Limit=100`，并把每页响应的 `NextPage` 作为下一次请求的 `Page`；`--page-limit` 限制的是最多请求页数，不是结果条数。

## Files 与 Session Resources

- 本地文件上传到 Files API：`arkcli agent file upload --path ./data.csv --purpose user_data --wait-active`。
- URL/TOS 注册：`arkcli agent file upload --url https://... --purpose user_data` 或 `--url tos://bucket/path/file --tos '{bucket: b, prefix: arkfiles/}'`。
- 视频/特殊文件预处理可传 `--preprocess-configs`；有效期可传 `--expire-at <unix-seconds>`。
- 上传后等待状态：`arkcli agent file wait <file-id>`。
- 查询已有文件：`arkcli agent file list --purpose user_data --limit 20`；全量遍历用 `arkcli --page-all agent file list`，CLI 默认 `limit=100` 并沿 `has_more + last_id -> after` 拉取。
- 用户给本地路径并要挂到已有 session 时，优先一步完成：

```bash
arkcli agent session resources add <session-id> --path ./data.csv --mount-path data.csv
```

这会先上传 file，再等待 active，最后 add session resource。
`session resources add --path` 支持透传上传相关参数：`--purpose`、`--tos`、`--preprocess-configs`、`--expire-at`、`--wait-timeout`、`--wait-interval`。

边界：

- `session resources add` 当前只支持 `type=file`、`file_id`、`mount_path`，不支持 PRD 中更复杂的 `github_repository` / `memory_store` 参数。
- 后端会自动在 `mount_path` 前添加 `/mnt/session/uploads/`。CLI 在 add 前会向 stderr 提示这一点，但不会改写用户传入的路径；例如传 `reports/data.csv`，最终路径为 `/mnt/session/uploads/reports/data.csv`。避免重复传入 `uploads/` 或完整受管前缀，并且不要传包含 `..` 的越界路径。
- `resources get` 是 CLI 派生能力：调用 list 后按 `resource_id` / `file_id` / `mount_path` 本地筛选。
- 线上数据面当前没有原生 resources update/delete，CLI 保持 fail-fast unsupported。
- `session resources add` 后端会复制源文件到 session 受管 uploads 路径，因此 resources list 看到的 file_id 可能不同于 add 时传入的源 file_id。
- 不要调用 ArkBFF/NodeBFF 获取文件；CLI 只直连 `/api/v3/files` 数据面。

## 示例

```bash
arkcli agent file upload --path ./sales.csv --purpose user_data --wait-active --format json
arkcli agent session resources add sess-xxx --path ./sales.csv --mount-path sales.csv --format json
```
