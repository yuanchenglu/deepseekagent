# DeepAgent Web API 参考

**版本**: 基于源码主干
**实现文件**: `hermes_cli/web_server.py`
**启动方式**: `python -m hermes_cli.main web`（默认 `http://127.0.0.1:9119`）

该文档描述 Web UI 仪表盘暴露的 REST API。所有接口均返回 JSON。前端 `web/src/lib/api.ts` 是与本 API 一一对应的 TypeScript 客户端。

---

## 目录

1. [启动与基础信息](#1-启动与基础信息)
2. [认证与授权](#2-认证与授权)
3. [通用约定](#3-通用约定)
4. [认证接口](#4-认证接口)
5. [系统状态](#5-系统状态)
6. [会话管理](#6-会话管理)
7. [配置管理](#7-配置管理)
8. [环境变量](#8-环境变量)
9. [模型信息](#9-模型信息)
10. [OAuth 提供商](#10-oauth-提供商)
11. [日志查看](#11-日志查看)
12. [定时任务](#12-定时任务)
13. [Skills 与 Toolsets](#13-skills-与-toolsets)
14. [用量分析](#14-用量分析)
15. [错误码与安全说明](#15-错误码与安全说明)

---

## 1. 启动与基础信息

```bash
python -m hermes_cli.main web                 # 默认 127.0.0.1:9119
python -m hermes_cli.main web --port 8080     # 指定端口
```

- **基础路径**: `http://127.0.0.1:9119`
- **CORS 限制**: 仅允许 `http://localhost` / `http://127.0.0.1` 任意端口的来源，防止任意网站读取/修改本地配置与密钥。
- **前端静态资源**: 构建产物位于 `hermes_cli/web_dist/`，由 SPA fallback 路由提供；未构建时 `/` 返回 `404` 与提示。

---

## 2. 认证与授权

仪表盘采用**双层认证**：

1. **临时会话 Token**：每次服务器启动生成（`secrets.token_urlsafe(32)`），注入到 SPA 的 `index.html`（`window.__HERMES_SESSION_TOKEN__`）。进程退出即失效。
2. **登录会话 Token**：`POST /api/auth/register`（首个账户）或 `POST /api/auth/login` 签发，有效期 7 天，存于内存；前端持久化在 `localStorage`。

### 受保护端点

所有 `/api/` 路径（除下列公开列表外）都经过 `auth_middleware` 校验。`Authorization` 头需为：

```
Authorization: Bearer <临时Token 或 登录Token>
```

两种 Token 任一有效即可。临时 Token 使用 `hmac.compare_digest` 常量时间比较，防时序侧信道。

### 公开端点（无需认证）

```
/api/status
/api/config/defaults
/api/config/schema
/api/model/info
/api/auth/status
/api/auth/me
/api/auth/login
/api/auth/register
/api/auth/logout
```

### 额外防护

- `POST /api/env/reveal` 与 `DELETE /api/providers/oauth/{id}`、OAuth `start/submit`、会话取消接口额外调用 `_require_token()`（仅接受临时 Token）。
- `POST /api/env/reveal` 有速率限制：每 30 秒窗口最多 5 次，超出返回 `429`。

---

## 3. 通用约定

### 请求体

接口使用 `application/json`。请求体由 Pydantic 模型校验，字段缺失/类型错误返回 `422`。

### 错误响应

所有错误返回 JSON，`detail` 字段为人类可读信息：

```json
{ "detail": "Session not found" }
```

| HTTP 状态码 | 含义 |
|---|---|
| `400` | 参数非法 / YAML 无效 / 未知文件或组件 / provider 不支持 |
| `401` | 未认证或 Token 无效 |
| `403` | 已存在账户（重复注册）等权限拒绝 |
| `404` | 资源不存在 |
| `422` | 请求体校验失败（Pydantic） |
| `429` | 触发速率限制（env reveal） |
| `500` | 服务器内部错误 |
| `501` | 功能不可用（如 Anthropic OAuth 适配器缺失） |
| `504` | 设备码流程超时未返回 user_code |

---

## 4. 认证接口

### `GET /api/auth/status`

返回是否已有账户，驱动首启设置流程。

```json
{ "has_users": false }
```

### `GET /api/auth/me`

返回当前登录会话（若请求携带有效 Token）。始终 `200`，方便前端检测登出。

```json
{ "authenticated": true, "user": { "username": "admin" } }
```

未登录：`{ "authenticated": false, "user": null }`

### `POST /api/auth/login`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `login` | string | 是 | 用户名、邮箱或手机号 |
| `password` | string | 是 | 密码 |

校验失败返回 `401`。成功：

```json
{ "ok": true, "token": "<登录Token>", "user": { "username": "admin" } }
```

### `POST /api/auth/register`

创建**首个**账户（已存在账户时返回 `403`）。后续注册被拒绝。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `username` | string | 是 | 至少 2 个字符 |
| `password` | string | 是 | 至少 6 个字符 |
| `email` | string | 否 | |
| `phone` | string | 否 | |

成功响应同 `login`。密码使用 PBKDF2-HMAC-SHA256（26 万次迭代、每用户随机盐）哈希，存储于 `HERMES_HOME/web_users.json`（权限 `0600`）。

### `POST /api/auth/logout`

使当前请求携带的 Token 失效。始终 `200`：

```json
{ "ok": true }
```

---

## 5. 系统状态

### `GET /api/status`（公开）

返回版本、配置路径与网关运行状态。

```json
{
  "version": "0.1.0",
  "release_date": "2026-08-03",
  "hermes_home": "/Users/me/.deepagent",
  "config_path": "/Users/me/.deepagent/config.yaml",
  "env_path": "/Users/me/.deepagent/.env",
  "config_version": 5,
  "latest_config_version": 5,
  "gateway_running": true,
  "gateway_pid": 12345,
  "gateway_state": "running",
  "gateway_platforms": { "telegram": { "state": "running", "updated_at": "..." } },
  "gateway_exit_reason": null,
  "gateway_updated_at": null,
  "active_sessions": 3
}
```

网关存活检测：优先本机 PID 检查（`gateway.status.get_running_pid`）；失败且配置了 `GATEWAY_HEALTH_URL` 时，通过 HTTP 健康端点跨容器探测（支持 `http://gateway:8642`、`/health`、`/health/detailed` 三种形式）。`gateway_state` 为 `"running"` / `"stopped"` / `"startup_failed"` 等。`active_sessions` 统计最近 5 分钟内有活跃、未结束的会话数。

---

## 6. 会话管理

数据来自 SQLite（`hermes_state.SessionDB`）。

### `GET /api/sessions`

查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `limit` | int | `20` | 每页条数 |
| `offset` | int | `0` | 偏移量 |

```json
{
  "sessions": [
    {
      "id": "abc123",
      "source": "cli",
      "model": "anthropic/claude-opus-4.6",
      "title": "我的会话",
      "started_at": 1754200000,
      "ended_at": null,
      "last_active": 1754201000,
      "is_active": true,
      "message_count": 12,
      "tool_call_count": 8,
      "input_tokens": 10000,
      "output_tokens": 5000,
      "preview": "……最后一条消息摘要"
    }
  ],
  "total": 57,
  "limit": 20,
  "offset": 0
}
```

`is_active` = 未结束且最近 5 分钟内有活跃。

### `GET /api/sessions/{session_id}`

获取会话完整记录。`session_id` 支持前缀解析（`resolve_session_id`）。不存在返回 `404`。

### `GET /api/sessions/{session_id}/messages`

```json
{
  "session_id": "abc123",
  "messages": [
    { "role": "user", "content": "你好", "timestamp": 1754200000 },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [{ "id": "call_1", "function": { "name": "web_search", "arguments": "{}" } }]
    },
    { "role": "tool", "content": "{\"results\":[]}", "tool_name": "web_search", "tool_call_id": "call_1" }
  ]
}
```

### `GET /api/sessions/search`

FTS5 全文搜索会话消息。查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `q` | string | `""` | 搜索词。自动追加前缀通配符（`nimb` → `nimb*`），保留引号短语与现有通配符 |
| `limit` | int | `20` | 结果上限 |

按会话去重，返回最佳摘要：

```json
{
  "results": [
    {
      "session_id": "abc123",
      "snippet": "……匹配片段……",
      "role": "user",
      "source": "cli",
      "model": "anthropic/claude-opus-4.6",
      "session_started": 1754200000
    }
  ]
}
```

`q` 为空时返回 `{ "results": [] }`。

### `DELETE /api/sessions/{session_id}`

删除会话及其全部消息。

```json
{ "ok": true }
```

不存在返回 `404`。

---

## 7. 配置管理

配置以 `config.yaml` 存于 `HERMES_HOME`。

### `GET /api/config`（受保护）

返回当前配置（已剥离 `_` 前缀内部键）。`model` 字段被规范化为字符串形式，并额外暴露 `model_context_length`（`0` = 自动检测）：

```json
{
  "model": "anthropic/claude-sonnet-4.6",
  "model_context_length": 0,
  "timezone": "Asia/Shanghai",
  "terminal": { "backend": "local" }
}
```

### `PUT /api/config`（受保护）

整体覆盖配置。请求体：`{ "config": { ... } }`。

保存前通过 `_denormalize_config_from_web` 反向重建 `model` 字典：读取磁盘配置恢复 `provider` / `base_url` 等子键；`model_context_length` > 0 时写入 `model.context_length`，否则移除该键（保持自动检测）。

```json
{ "ok": true }
```

### `GET /api/config/defaults`（公开）

返回 `DEFAULT_CONFIG` 全量默认值。

### `GET /api/config/schema`（公开）

返回前端渲染用的字段 schema：

```json
{
  "fields": {
    "model": { "type": "string", "description": "Default model (...)", "category": "general" },
    "terminal.backend": { "type": "select", "description": "Terminal execution backend", "options": ["local", "docker", "ssh"], "category": "terminal" }
  },
  "category_order": ["general", "agent", "terminal", "display", "delegation", "memory", "compression", "security", "browser", "voice", "tts", "stt", "logging", "discord", "auxiliary"]
}
```

字段类型：`boolean` / `number` / `string` / `list` / `object` / `select`。小类别合并到 `general` / `agent` / `display` / `security`。

### `GET /api/config/raw`（受保护）

返回 `config.yaml` 原文：

```json
{ "yaml": "model: anthropic/claude-sonnet-4.6\n..." }
```

文件不存在时返回 `{ "yaml": "" }`。

### `PUT /api/config/raw`（受保护）

以 YAML 文本整体保存配置。请求体：`{ "yaml_text": "..." }`。

- YAML 非法 → `400`（`Invalid YAML: ...`）
- YAML 根节点不是 mapping → `400`

```json
{ "ok": true }
```

---

## 8. 环境变量

### `GET /api/env`（受保护）

返回 `OPTIONAL_ENV_VARS` 中所有已知变量的状态（值永远脱敏）：

```json
{
  "ANTHROPIC_API_KEY": {
    "is_set": true,
    "redacted_value": "…abcd",
    "description": "Anthropic API key",
    "url": "https://console.anthropic.com/",
    "category": "provider",
    "is_password": true,
    "tools": ["..."],
    "advanced": false
  }
}
```

### `PUT /api/env`（受保护）

设置环境变量。请求体：`{ "key": "...", "value": "..." }`。

```json
{ "ok": true, "key": "ANTHROPIC_API_KEY" }
```

### `DELETE /api/env`（受保护）

删除环境变量。请求体：`{ "key": "..." }`。变量不在 `.env` 中返回 `404`。

```json
{ "ok": true, "key": "ANTHROPIC_API_KEY" }
```

### `POST /api/env/reveal`（受保护，额外 Token + 限流）

返回单个变量的真实值。请求体：`{ "key": "..." }`。

```json
{ "key": "ANTHROPIC_API_KEY", "value": "sk-ant-..." }
```

防护：仅接受临时 Token、每 30 秒限 5 次（超出 `429`）、写审计日志、变量不存在 `404`。

---

## 9. 模型信息

### `GET /api/model/info`（公开）

返回当前配置模型的解析元数据（上下文长度走与 Agent 相同的解析链路）。

```json
{
  "model": "anthropic/claude-opus-4.6",
  "provider": "anthropic",
  "auto_context_length": 200000,
  "config_context_length": 0,
  "effective_context_length": 200000,
  "capabilities": {
    "supports_tools": true,
    "supports_vision": true,
    "supports_reasoning": true,
    "context_window": 200000,
    "max_output_tokens": 32000,
    "model_family": "claude"
  }
}
```

- `auto_context_length`：忽略覆盖值的纯自动检测结果。
- `config_context_length`：配置中的显式覆盖（无则 `0`）。
- `effective_context_length`：实际生效值（优先覆盖值，否则自动值）。
- 未配置模型或解析失败时返回全零/空值，不报错。

---

## 10. OAuth 提供商

提供商目录（`id` / `flow`）：

| id | 名称 | flow |
|---|---|---|
| `anthropic` | Anthropic (Claude API) | `pkce` |
| `claude-code` | Claude Code (subscription) | `external`（委托 CLI） |
| `nous` | Nous Portal | `device_code` |
| `openai-codex` | OpenAI Codex (ChatGPT) | `device_code` |
| `qwen-oauth` | Qwen (via Qwen CLI) | `external`（委托 CLI） |

### `GET /api/providers/oauth`（受保护）

枚举全部提供商与当前状态：

```json
{
  "providers": [
    {
      "id": "anthropic",
      "name": "Anthropic (Claude API)",
      "flow": "pkce",
      "cli_command": "hermes auth add anthropic",
      "docs_url": "https://docs.claude.com/en/api/getting-started",
      "status": {
        "logged_in": true,
        "source": "hermes_pkce",
        "source_label": "Hermes PKCE (~/.hermes/.anthropic_oauth.json)",
        "token_preview": "…aB3dEf",
        "expires_at": 1754800000,
        "has_refresh_token": true
      }
    }
  ]
}
```

`token_preview` 永不暴露完整 token（仅末尾 6 字符；JWT 时只显示签名段末尾）。

### `DELETE /api/providers/oauth/{provider_id}`（受保护，额外 Token）

断开指定提供商。未知 provider → `400`。

```json
{ "ok": true, "provider": "anthropic" }
```

`anthropic` / `claude-code` 会删除 Hermes 管理的 PKCE 文件并清理凭证池。

### `POST /api/providers/oauth/{provider_id}/start`（受保护，额外 Token）

发起登录流程。`external` 提供商 → `400`（提示手动运行 CLI）。

**PKCE（anthropic）响应：**

```json
{
  "session_id": "sess_xxx",
  "flow": "pkce",
  "auth_url": "https://claude.ai/oauth/authorize?...",
  "expires_in": 900
}
```

**device_code（nous / openai-codex）响应：**

```json
{
  "session_id": "sess_xxx",
  "flow": "device_code",
  "user_code": "ABCD-EFGH",
  "verification_url": "https://auth.openai.com/codex/device",
  "expires_in": 900,
  "poll_interval": 5
}
```

服务器会启动后台轮询线程驱动流程直至完成/失败/过期。会话 TTL 15 分钟，每次 `/start` 顺带 GC 过期会话。

### `POST /api/providers/oauth/{provider_id}/submit`（受保护，额外 Token）

提交 PKCE 回调码。请求体：`{ "session_id": "...", "code": "..." }`。仅 `anthropic` 支持，其余 `400`。

```json
{ "ok": true, "status": "approved" }
```

失败时 `{ "ok": false, "status": "error", "message": "..." }`。会话不存在/过期 → `404`。

### `GET /api/providers/oauth/{provider_id}/poll/{session_id}`（公开）

轮询 device_code 会话状态（只读，无需认证）：

```json
{
  "session_id": "sess_xxx",
  "status": "pending",
  "error_message": null,
  "expires_at": 1754800000
}
```

`status`：`pending` | `approved` | `denied` | `expired` | `error`。会话不存在 → `404`，provider 不匹配 → `400`。

### `DELETE /api/providers/oauth/sessions/{session_id}`（受保护，额外 Token）

取消挂起的 OAuth 会话。

```json
{ "ok": true, "session_id": "sess_xxx" }
```

---

## 11. 日志查看

### `GET /api/logs`（受保护）

查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `file` | string | `"agent"` | 日志文件名键（见 `hermes_cli/logs.py` 的 `LOG_FILES`） |
| `lines` | int | `100` | 返回行数上限（有过滤时上限 500，搜索时读取上限 2000） |
| `level` | string | 无 | 最小级别过滤（`"ALL"` / 空 = 不过滤） |
| `component` | string | 无 | 组件过滤（`"all"` / 空 = 不过滤） |
| `search` | string | 无 | 大小写不敏感的子串过滤 |

```json
{
  "file": "agent",
  "lines": ["2026-08-03 10:00:00 INFO  ...", "..."]
}
```

未知日志文件 → `400`；未知组件 → `400`（`detail` 附带可用组件列表）。文件不存在返回空 `lines`。

---

## 12. 定时任务

### `GET /api/cron/jobs`（受保护）

```json
[
  {
    "id": "job_xxx",
    "name": "每日报告",
    "prompt": "生成今日报告",
    "schedule": { "kind": "cron", "expr": "0 9 * * *", "display": "每天 09:00" },
    "schedule_display": "每天 09:00",
    "enabled": true,
    "state": "active",
    "deliver": "local",
    "last_run_at": null,
    "next_run_at": "2026-08-04 09:00:00",
    "last_error": null
  }
]
```

### `GET /api/cron/jobs/{job_id}`（受保护）

单任务详情。不存在 → `404`。

### `POST /api/cron/jobs`（受保护）

创建任务。请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `prompt` | string | 是 | 任务提示词 |
| `schedule` | string | 是 | 调度表达式（cron 语法） |
| `name` | string | 否 | 任务名 |
| `deliver` | string | 否 | 交付方式（默认 `"local"`） |

创建失败 → `400`（`detail` 携带错误原因）。成功返回任务对象。

### `PUT /api/cron/jobs/{job_id}`（受保护）

更新任务。请求体：`{ "updates": { ... } }`。返回更新后的任务；不存在 → `404`。

### `POST /api/cron/jobs/{job_id}/pause`（受保护）

暂停任务。返回任务对象；不存在 → `404`。

### `POST /api/cron/jobs/{job_id}/resume`（受保护）

恢复任务。返回任务对象；不存在 → `404`。

### `POST /api/cron/jobs/{job_id}/trigger`（受保护）

立即触发一次。返回任务对象；不存在 → `404`。

### `DELETE /api/cron/jobs/{job_id}`（受保护）

```json
{ "ok": true }
```

不存在 → `404`。

---

## 13. Skills 与 Toolsets

### `GET /api/skills`（受保护）

```json
[
  {
    "name": "gif-search",
    "description": "搜索并返回 GIF",
    "category": "media",
    "enabled": true
  }
]
```

`enabled` 依据 `config.yaml` 中禁用列表计算（跳过 `skip_disabled`）。

### `PUT /api/skills/toggle`（受保护）

启用/禁用 Skill。请求体：`{ "name": "...", "enabled": true }`。

```json
{ "ok": true, "name": "gif-search", "enabled": true }
```

### `GET /api/tools/toolsets`（受保护）

返回可配置工具集及平台启用状态（CLI 平台视角）：

```json
[
  {
    "name": "web",
    "label": "Web",
    "description": "网页搜索与内容提取",
    "enabled": true,
    "available": true,
    "configured": true,
    "tools": ["web_search", "web_extract"]
  }
]
```

- `enabled` / `available`：当前平台是否启用。
- `configured`：是否已配置所需 API 密钥。

---

## 14. 用量分析

### `GET /api/analytics/usage`（受保护）

查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `days` | int | `30` | 统计窗口天数 |

```json
{
  "daily": [
    {
      "day": "2026-08-03",
      "input_tokens": 100000,
      "output_tokens": 50000,
      "cache_read_tokens": 40000,
      "reasoning_tokens": 10000,
      "estimated_cost": 1.23,
      "actual_cost": 1.1,
      "sessions": 10
    }
  ],
  "by_model": [
    {
      "model": "anthropic/claude-opus-4.6",
      "input_tokens": 100000,
      "output_tokens": 50000,
      "estimated_cost": 1.23,
      "sessions": 10
    }
  ],
  "totals": {
    "total_input": 100000,
    "total_output": 50000,
    "total_cache_read": 40000,
    "total_reasoning": 10000,
    "total_estimated_cost": 1.23,
    "total_actual_cost": 1.1,
    "total_sessions": 10
  },
  "period_days": 30
}
```

---

## 15. 错误码与安全说明

### 状态码速查

| 状态码 | 典型场景 |
|---|---|
| `200` | 成功 |
| `400` | 参数非法、未知日志/组件/provider、YAML 无效、不支持的 flow |
| `401` | `Authorization` 缺失/无效 |
| `403` | 已有账户时重复注册 |
| `404` | 会话/任务/provider 会话不存在、env 变量未设置、前端未构建 |
| `422` | Pydantic 请求体校验失败 |
| `429` | `/api/env/reveal` 超出限流窗口 |
| `500` | 服务器内部异常 |
| `501` | OAuth 适配器不可用（如缺少 `agent.anthropic_adapter`） |
| `504` | Codex 设备码流程超时未拿到 user_code |

### 安全要点

1. **本地绑定**：默认仅绑定 `127.0.0.1`。绑定其他主机需 `--insecure` 显式覆盖（会打印警告）。
2. **CORS**：白名单正则仅放行 `localhost` / `127.0.0.1` 来源。
3. **凭据保护**：`.env` 值默认脱敏，仅 `/api/env/reveal`（受临时 Token + 限流保护）能返回明文。
4. **密码存储**：PBKDF2-HMAC-SHA256，26 万次迭代，每用户随机盐，文件权限 `0600`。
5. **临时 Token**：`hmac.compare_digest` 常量时间比较，防时序侧信道；进程退出即失效。
6. **日志与审计**：`reveal`、OAuth 断开/登录均写审计日志。

### 快速自测

```bash
# 获取状态（公开端点）
curl http://127.0.0.1:9119/api/status

# 受保护端点需带 Token（从 index.html 的 __HERMES_SESSION_TOKEN__ 获取）
curl -H "Authorization: Bearer <token>" http://127.0.0.1:9119/api/sessions

# 完整流程：注册 → 用登录 Token 访问
curl -X POST http://127.0.0.1:9119/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret123"}'
curl -H "Authorization: Bearer <login-token>" http://127.0.0.1:9119/api/config
```
