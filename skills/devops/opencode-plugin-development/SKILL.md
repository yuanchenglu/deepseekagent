---
name: opencode-plugin-development
description: >-
  Develop plugins for OpenCode/DeepCode using Effect-TS v4 and Bun runtime.
  Covers plugin registration via opencode.jsonc, PlatformAdapter pattern for
  messaging platforms (Feishu, WeChat), HTTP gateway server lifecycle,
  Bun.serve() integration with Effect, webhook event parsing (including
  Feishu URL verification challenge), and subprocess management with Bun
  Web Streams API. Use when building bot/messaging integrations, gateway
  plugins, or any custom OpenCode plugin that needs HTTP server and
  external message processing.
trigger:
  - "develop OpenCode plugin"
  - "build gateway for OpenCode"
  - "Feishu/WeChat bot with OpenCode"
  - "Effect TS plugin for OpenCode"
  - "message gateway with bun serve"
domain: software-engineering
type: workflow-reference
---

# OpenCode Plugin Development

## ⚠️ User Workflow Rule
**Do NOT write code yourself. Always delegate implementation to OMO via \`opencode run -c\` with full context.** The assistant's role is: context preparation → OMO dispatch → verification. 

Key rules:
- **One flow, not many sessions** — Don't split work into multiple background OMO sessions. Give full context upfront in a single call.
- **Direction corrected? Kill and restart** — If the user corrects the approach, immediately kill the running OMO process and restart with corrected context. Don't let it continue down the wrong path.
- **Test everything yourself. Do NOT ask the user to test.** — After OMO completes, run ALL verification commands yourself (curl, typecheck, queue injection, simulated events). If the gateway says "connected" but events don't arrive, write diagnostic scripts to probe deeper, compare working vs non-working SDKs, and check raw WebSocket traffic. The user will not tolerate being used as a test subject.
- **Understand who you are in context** — When the user says "you ARE Hermes" or "our gateway", recognize that this conversation IS running on the Hermes gateway. The project you're building may be a completely separate entity. Keep identities straight — don't confuse Hermes (your runtime) with the project's own bot.
- **Check existing code first** — Before implementing platform integrations (Feishu, WeChat, etc.), look at Hermes's existing implementations (e.g., `gateway/platforms/feishu.py`) and official SDKs. Don't build from scratch.
- **Use the same SDK for comparison** — When debugging a Node.js Feishu SDK, use the Python `lark_oapi` SDK (already installed in Hermes venv) as a baseline: if the Python SDK receives events but Node doesn't, the issue is SDK-specific. If neither receives events, the issue is app configuration or Feishu server side.

## Architecture Pattern

A messaging gateway plugin for OpenCode/DeepCode follows one of two message paths:

### Webhook Mode
```
External Platform (Feishu/WeChat)
  → Webhook POST → HTTP Server (Bun.serve)
  → Router (parse event → push to Queue)
  → Consumer (read from Queue → process → reply)
  → Platform Adapter (send reply via platform API)
```

### Long Connection Mode (Feishu WSClient)
```
Feishu Server
  → Lark.WSClient WebSocket ← Gateway starts this connection
  → EventDispatcher routes im.message.receive_v1
  → parseFeishuEvent → push to Queue
  → Consumer (read from Queue → process → reply)
  → FeishuAdapter.send (via REST API)
```

When to use each:
- **Webhook**: External platform supports webhook, you have a public URL (Cloudflare Tunnel, public IP)
- **Long Connection (WSClient)**: Feishu/Lark bot, no public URL needed, bot SDK manages connection lifetime

## Project Structure

```
packages/<your-plugin>/
├── package.json          # "effect": "catalog:", "@opencode-ai/plugin": "workspace:*"
├── tsconfig.json         # "extends": "@tsconfig/bun/tsconfig.json"
└── src/
    ├── index.ts          # Re-export all public APIs
    ├── server.ts         # Bun.serve() wrapped in Effect
    ├── router.ts         # Webhook event router (parsing + queue dispatch)
    ├── lifecycle.ts      # Startup/shutdown orchestration
    ├── session-bridge.ts # Message consumer + execution bridge
    ├── plugin.ts         # OpenCode plugin registration (define + register)
    ├── adapter.ts        # PlatformAdapter interface
    ├── message.ts        # Unified message model
    ├── config.ts         # Config + env var keys
    ├── error.ts          # Typed error codes
    └── feishu/           # Platform-specific adapters
        ├── adapter.ts
        └── api.ts
```

## Implementation Guide

### 1. OpenCode Plugin Registration

In `.opencode/opencode.jsonc`:

```jsonc
{
  "plugin": [
    {
      "package": "./packages/<your-plugin>",
      "options": {
        "gateway": {
          "port": 3099,
          "feishu": {
            "enabled": true,
            "appId": "cli_xxx",
            "appSecret": "xxx"
          }
        }
      }
    }
  ]
}
```

The plugin's `effect` function receives `PluginContext` with access to all OpenCode services:

```typescript
import { define } from "@opencode-ai/plugin/v2/effect/plugin"

export const gatewayPlugin = define({
  id: "@deepcode/gateway",
  effect: (context) =>
    Effect.gen(function* () {
      const config = context.options?.gateway
      if (config?.feishu?.enabled) {
        registerAdapter(new FeishuAdapter(config.feishu))
      }
      yield* Effect.ignore(startGateway(config?.port ?? 3099))
    }),
})
```

### 2. HTTP Server with Bun.serve()

Key patterns (Bun 1.3+):

```typescript
// startServer.ts — Bun.serve() wrapped in Effect
let serverInstance: ReturnType<typeof Bun.serve> | null = null

export function startServer(port: number, router: Router): Effect.Effect<void> {
  return Effect.sync(() => {
    serverInstance = Bun.serve({
      port,
      development: false,
      fetch(req: Request): Response | Promise<Response> {
        // Handle routes
      },
    })
  })
}

export function stopServer(): Effect.Effect<void> {
  return Effect.sync(() => {
    serverInstance?.stop()
    serverInstance = null
  })
}
```

### 3. Feishu URL Verification Challenge

Feishu sends a challenge verification when configuring webhook. Must respond with the challenge value:

```typescript
if (path.startsWith("/webhook/feishu")) {
  const body = await req.json() as Record<string, unknown>
  if (body.type === "url_verification") {
    return Response.json({ challenge: body.challenge })
  }
}
```

### 4. Feishu Long Connection (WebSocket) via SDK

For Feishu/Lark bots in long connection mode (no HTTP webhook), use the official `@larksuiteoapi/node-sdk` package. **Do not implement WebSocket manually** — the SDK handles auth, heartbeat, reconnect, and event dispatching.

```bash
bun add @larksuiteoapi/node-sdk
```

```typescript
import * as Lark from "@larksuiteoapi/node-sdk"

class FeishuAdapter {
  start(): Effect.Effect<void, GatewayError> {
    return Effect.gen(function* () {
      // Get tenant access token first (needed for sending replies)
      yield* self.getToken()

      // Create WSClient — SDK handles auth, heartbeat, reconnect
      const wsClient = new Lark.WSClient({
        appId: self.cfg.appId,
        appSecret: self.cfg.appSecret,
        loggerLevel: Lark.LoggerLevel.info,
        // Default domain is Feishu (Chinese); Lark (international) needs explicit override
        // domain: "feishu" | "lark"
        onReady: () => console.log("[FeishuAdapter] 飞书长连接已就绪"),
        onReconnecting: () => console.log("重连中..."),
        onReconnected: () => console.log("重连成功"),
      })

      // Register event handlers
      const dispatcher = new Lark.EventDispatcher({}).register({
        "im.message.receive_v1": async (data: unknown) => {
          const eventData = data as Record<string, unknown>
          // Parse and push to queue
          const msg = parseFeishuEvent(eventData)
          if (msg) Effect.runFork(Queue.offer(queue, msg))
        },
      })

      // Start the connection (non-blocking — returns immediately)
      yield* Effect.tryPromise({
        try: () => wsClient.start({ eventDispatcher: dispatcher }),
        catch: (err) => new GatewayError("NETWORK_ERROR", `启动失败: ${err.message}`),
      })
    })
  }
}
```

**Important notes:**
- The WSClient default domain is **Feishu (Chinese)**. For Lark (international), pass `domain: "lark"` explicitly. If ECONNREFUSED on initial connection, check this first.
- `start()` returns immediately — connection happens in background via `onReady`/`onReconnecting`/`onReconnected` callbacks. The startup sequence continues before the WS is ready.
- ECONNREFUSED during reconnection is usually transient — the SDK retries automatically with exponential backoff. Don't restart the gateway for this.
- **The user must configure the Feishu app** in Developer Console → Events & Callbacks to use "long connection" mode AND subscribe `im.message.receive_v1`. Without subscription, the SDK connects but receives zero messages.
- **Verify credentials first** by calling the Feishu Auth API directly: `curl https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal -d '{"app_id":"cli_xxx","app_secret":"xxx"}'`. If this returns `code: 0`, credentials are valid.
- **⚠️ KNOWN ISSUE: The Node SDK WSClient may connect but receive ZERO events** even with correct app configuration. Confirmed on `@larksuiteoapi/node-sdk` v1.70.0 with Bun 1.3.14. The Python `lark_oapi` SDK works correctly with the same app ID/secret. If you encounter this, switch to the Python bridge architecture (see `references/python-ws-bridge-alternative.md`).

### 5. Standalone Startup (No OpenCode Plugin System)

When OpenCode server can't start from the project directory or you need to test the gateway independently, create a `startup.ts` entry point:

```typescript
import { Effect } from "effect"
import { FeishuAdapter, registerAdapter, startGateway } from "./src/index"

registerAdapter(new FeishuAdapter({
  enabled: true,
  appId: process.env.OPENCODE_FEISHU_APP_ID!,
  appSecret: process.env.OPENCODE_FEISHU_APP_SECRET!,
}))

// Effect.never keeps Scope alive so forkScoped fibers don't get cancelled
const program = Effect.gen(function* () {
  yield* Effect.ignore(startGateway(3099))
  yield* Effect.never
})

Effect.runFork(program.pipe(Effect.scoped))
```

This pattern is necessary because `Effect.runPromise(Effect.scoped(program))` would close the Scope when the promise resolves, killing all `forkScoped` background fibers (including the message consumer).

### 6. Effect v4 Beta API Patterns

**Effect v4 beta (4.x) differs from Effect v3. Common replacements:**

| v3 / assumed API | v4 beta replacement |
|---|---|
| `Effect.catchAll(handler)` | `Effect.catchIf(() => true, handler)` or `Effect.ignore({ log: true })` |
| `Effect.fork(eff)` | `Effect.forkScoped(eff)` |



Bun 1.3+ replaced Node.js-style streams on `Bun.spawn` with Web `ReadableStream`:

```typescript
const proc = Bun.spawn(["bun", "run", "opencode", "run", "-c", prompt], {
  cwd: workdir,
  stdio: ["ignore", "pipe", "pipe"],
})

// Read stdout with Web Streams API (NOT stream.on("data"))
const stdout: Buffer[] = []
const reader = proc.stdout.getReader()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  stdout.push(Buffer.from(value))
}

// Wait for exit with Promise (NOT proc.on("exit"))
const { exitCode } = await proc.exited

// Race with timeout
const result = await Promise.race([
  proc.exited.then(code => ({ exitCode: code })),
  new Promise(resolve => setTimeout(() => {
    proc.kill("SIGTERM")
    resolve({ exitCode: -1 })
  }, 120_000)),
])
```

### 7. Subprocess CLI Execution for Message Processing

When processing incoming messages by spawning a CLI subprocess (e.g., `opencode run`):

```typescript
async function executeCli(text: string, sessionId: string, workdir: string): Promise<string> {
  const proc = Bun.spawn(
    ["bun", "run", "opencode", "run", "-c", text],
    { cwd: workdir, stdio: ["ignore", "pipe", "pipe"] }
  )
  // ... read output with Web Streams API, race with timeout
}
```

**Critical: determine the correct CLI command for the project.**
- If the project IS a custom fork (like DeepCode), its CLI entry point is under `packages/<cli>/` — check `package.json` for bin/scripts
- `bun run opencode` only works if there's an "opencode" script in the root package.json
- Test with `bun run <command> --help` before hardcoding in executeCli

### 8. PlatformAdapter Interface

```typescript
export interface PlatformAdapter {
  readonly name: string
  start(): Effect.Effect<void, GatewayError>
  stop(): Effect.Effect<void>
  send(msg: OutboundMessage): Effect.Effect<SendResult, GatewayError>
  readonly messages: Stream.Stream<GatewayMessage, GatewayError>
}
```

### 7. Type Resolution

If `tsgo` typecheck can't find Bun globals (Bun, Request, Response, fetch, URL, console, process, Buffer, setTimeout):

```bash
# Add @types/bun to devDependencies
# In packages/<your-plugin>/package.json:
"devDependencies": {
  "@types/bun": "catalog:"
}

# Then run bun install from workspace root
cd /Volumes/Doc/Code/deepcode && bun install
```

Don't rely on `tsconfig.json` `"types": ["bun"]` alone — it won't work if `@types/bun` isn't installed in the package's own node_modules resolution path.

### 8. Verification Pattern

Write a standalone test script to verify the HTTP server independently before full OpenCode integration:

```typescript
import { startServer, stopServer } from "./src/server"
import { Router } from "./src/router"
import { Queue, Effect } from "effect"

async function main() {
  const mq = await Effect.runPromise(Queue.unbounded())
  const router = new Router()
  router.register({ path: "/webhook/feishu", platform: "feishu" }, mq)
  await Effect.runPromise(startServer(3099, router))

  // Test health check
  const h = await fetch("http://localhost:3099/health")
  console.log(await h.json())

  // Test Feishu challenge
  const c = await fetch("http://localhost:3099/webhook/feishu", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "url_verification", challenge: "test" }),
  })
  console.log(await c.json())

  await Effect.runPromise(stopServer())
}
main().catch(console.error)
```

## Configuration (Environment Variables)

```typescript
export const ENV_KEYS = {
  FEISHU_APP_ID: "OPENCODE_FEISHU_APP_ID",
  FEISHU_APP_SECRET: "OPENCODE_FEISHU_APP_SECRET",
  WECHAT_CORP_ID: "OPENCODE_WECHAT_CORP_ID",
  WECHAT_AGENT_ID: "OPENCODE_WECHAT_AGENT_ID",
  WECHAT_SECRET: "OPENCODE_WECHAT_SECRET",
} as const
```

## Pitfalls

1. **Effect.catchAll doesn't exist in v4 beta** — Use `catchIf(() => true, handler)` or `Effect.ignore({ log: true })` instead
2. **Effect.fork doesn't exist in v4 beta** — Use `Effect.forkScoped(eff)` which requires `Scope.Scope` in the effect's `R` type
3. **Bun 1.3+ streams changed** — `proc.stdout.on("data")` → `proc.stdout.getReader()`, `proc.on("exit")` → `proc.exited.then()`
4. **@types/bun must be installed** — Adding `"types": ["bun"]` to tsconfig alone won't resolve globals; actually install the package
5. **Plugin loads global config first** — OpenCode reads `~/.config/opencode/opencode.jsonc` before project `.opencode/opencode.jsonc`
6. **Effect.ignore({ log: true }) hides failures** — It swallows ALL errors including send failures. The user won't know if messages are being processed or silently failing. Prefer logging the error before ignoring, or use `Effect.catchIf` with explicit error handling.
7. **opencode.jsonc plugin field format** — The field is `"plugin"` (singular), and entries are strings (simple references) or objects with `package` + `options` keys. The plural `"plugins"` is rejected by validation.
8. **Scope lifecycle in standalone startup** — `Effect.runPromise(Effect.scoped(program))` closes the Scope when the promise resolves, killing all `forkScoped` fibers. Use `Effect.runFork` + `Effect.never` instead to keep the Scope alive indefinitely.
9. **CLI path must match project** — Don't hardcode `bun run opencode run` for all projects. If the project is a custom fork (DeepCode), find the actual CLI entry point under `packages/<cli>/`.
10. **Feishu event subscription required even in long connection mode** — The Feishu app must have `im.message.receive_v1` explicitly subscribed in Developer Console → Events & Callbacks → Events → Messages & Groups → "Receive Message (im.message.receive_v1)". The SDK connects the WebSocket but the server won't push events without this subscription.
12. **CLI binary may not be built** — `packages/opencode/bin/opencode` is a wrapper that looks for a platform-specific binary. If running it gives `"platform-specific binary not installed"`, run `bun run packages/opencode/script/build.ts` to build all platform binaries, then symlink `dist/opencode-darwin-arm64/bin/opencode → node_modules/opencode-darwin-arm64/bin/opencode`.
13. **Feishu v2.0 event structure: chat_id is nested** — In Feishu v2.0 events (`schema: "2.0"`), the `chat_id` is at `event.message.chat_id`, NOT `event.chat_id`. The sender's `open_id` is at `event.sender.sender_id.open_id`. Using `eventBody.chat_id` returns undefined → reply goes to nowhere. Always use `message?.chat_id` first, with `eventBody.chat_id` as fallback.
14. **Node SDK WSClient may receive zero events** — The `@larksuiteoapi/node-sdk` WSClient has a confirmed compatibility issue where it connects successfully (state=`connected`) but receives zero protobuf frames. The Python `lark_oapi` SDK works correctly. If you hit this, switch to the Python bridge architecture (see `references/python-ws-bridge-alternative.md`).

## Reference: Feishu Event SDK

For long connection mode, the `@larksuiteoapi/node-sdk` `WSClient`:
- Default domain = Feishu (Chinese站). For Lark (international), pass `domain: "lark"`
- `start()` returns immediately; connection lifecycle via callbacks
- Register `im.message.receive_v1` handler for inbound messages
- SDK handles: auth via appId+appSecret, heartbeat/ping-pong, automatic reconnect with exponential backoff
- ECONNREFUSED during reconnect is transient — SDK retries
- User must switch subscription mode in Developer Console to "long connection"
