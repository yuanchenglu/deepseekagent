# DeepCode 飞书 Gateway 实现笔记

> 对接飞书 Bot 时必须使用**长连接（WebSocket）**模式，而非 HTTP Webhook。
> 飞书 WebSocket 地址：`wss://open.feishu.cn/events/v2/ws/connect`

## 两种接收模式对比

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **HTTP Webhook** | 实现简单，只需 HTTP Server | 需要公网可达 URL，需要 Cloudflare Tunnel | 已有公网服务的项目 |
| **WebSocket 长连接** | 不需要公网 URL，实时性好 | 需要实现 WebSocket 客户端和心跳 | 服务在本地/内网的场景 |

## 参考实现

Hermes Agent 的飞书通道（Python，生产级）：
- `~/Code/deepseekagent/gateway/platforms/feishu.py`
- 使用 `lark_oapi.ws.Client`（飞书官方 Python SDK 的内置 WebSocket 客户端）
- 支持事件认证（token 校验）、自动重连、消息去重、媒体文件缓存等

TypeScript 项目可用的官方 SDK：
- `@larksuiteoapi/node-sdk` — 飞书 Node.js 官方 SDK
- `@larksuiteoapi/lark-mcp` — 飞书 MCP 服务器（已在全局 opencode 配置中使用）

## WebSocket 连接流程

```
1. 获取 tenant_access_token（POST /open-apis/auth/v3/tenant_access_token/internal）
2. 连接 wss://open.feishu.cn/events/v2/ws/connect
3. 发送认证消息：{"type": "auth", "token": "<tenant_access_token>"}
4. 接收事件（二进制/JSON 帧）
5. 心跳：服务器定期发 ping，回复 pong
6. 重连：断开后自动重连（指数退避）
```

## gateway 配置注意事项

OpenCode 项目配置 `.opencode/opencode.jsonc` 中 `"plugin"` 字段：
- 字段名是 `"plugin"`（单数），不是 `"plugins"`（复数）
- 值必须是字符串数组，不支持 `{package, options}` 对象格式
- 插件配置通过环境变量传递（插件内部读取 `process.env.ENV_KEY`）

## Effect-based 后台服务常见坑

Gateway 作为 OpenCode Plugin 或独立进程运行时：

```typescript
// ❌ 错误：startGateway 返回后 Scope 关闭，forkScoped 的 Fiber 被中断
Effect.runPromise(Effect.scoped(program))

// ✅ 正确：用 Effect.never 保持 Scope 不关闭
const program = Effect.gen(function* () {
  yield* Effect.ignore(startGateway(3099))
  yield* Effect.never  // 保持 Scope 存活
})
Effect.runFork(program.pipe(Effect.scoped))
```

## 已知故障

- `opencode web` 在项目目录启动报 `ServeError`，但从 `/tmp` 可以启动 → 问题在项目目录的 `.opencode/` 配置，非全局问题
- 即使 `--pure`（跳过所有外部插件）也失败 → 不是插件问题，是 workspace/数据库初始化失败
