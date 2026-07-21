# Debug / Export / 验证

## Debug / Export

- `+debug <session-id>` 聚合 session get、最近 events、resources、threads，输出状态、错误事件、pending action、warnings。用 `--limit` 控制事件数量，`--session-thread-id` 聚焦单线程。
- `+export <session-id>` 写 `arkcli-session-<session-id>-<timestamp>.tar.gz`，可用 `--output` 指定路径。归档包含 `manifest.json`、`session.json`、`events.json`、`resources.json`、`threads.json`、`notes.md`。
- 当前 workspace tarball 和 memory snapshot 没有可用读取接口，导出时只在 manifest 标为 unsupported，不伪造内容。

## 端到端验证模板

```bash
arkcli agent agent get <agent-id> --format json
arkcli agent env create --name arkcli-<domain>-env-<timestamp> --config '{Type: cloud, Networking: {Type: unrestricted}}' --format json
arkcli agent session create --agent-id <agent-id> --environment-id <env-id> --title arkcli-<domain>-session-<timestamp> --format json
arkcli agent session events send <session-id> --type user.message --text "<one small test task>" --format json
arkcli agent session events list <session-id> --limit 20 --format json
arkcli +tail <session-id> --session-thread-id <thread-id>
arkcli agent session threads list <session-id> --limit 10 --format json
arkcli agent session resources list <session-id> --format json
```

用户要求“不要删资源”时，保留创建出的 agent/env/session/vault/credential。
