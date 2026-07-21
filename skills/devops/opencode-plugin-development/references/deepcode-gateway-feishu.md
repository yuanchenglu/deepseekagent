# Feishu Long Connection Gateway — DeepCode Implementation Notes

## Architecture

```
Feishu Server ←→ Lark.WSClient (WebSocket, initiated by gateway)
                         ↓
                  EventDispatcher
                         ↓
            im.message.receive_v1 handler
                         ↓
             parseFeishuEvent() → GatewayMessage
                         ↓
           Queue.offer(queue, msg) → Consumer
                         ↓
              executeCli(text, sessionId, workdir)
                         ↓
              FeishuAdapter.send(reply) via REST API
```

**Note:** The Node.js `@larksuiteoapi/node-sdk` WSClient has a known issue: it connects successfully but receives ZERO events. The Python `lark_oapi` SDK works correctly. For production use, see `references/python-ws-bridge-alternative.md` for the Python bridge architecture.

## Key Components

### WSClient Setup (adapter.ts)
```typescript
const wsClient = new Lark.WSClient({
  appId: config.appId,
  appSecret: config.appSecret,
  loggerLevel: Lark.LoggerLevel.info,
  onReady: () => console.log("长连接已就绪"),
  onReconnecting: () => console.log("重连中..."),
  onReconnected: () => console.log("重连成功"),
})

const dispatcher = new Lark.EventDispatcher({}).register({
  "im.message.receive_v1": async (data) => {
    await handleEvent(data, queue)
  },
})

yield* Effect.tryPromise({
  try: () => wsClient.start({ eventDispatcher: dispatcher }),
  catch: (err) => handleError(err),
})
```

### Standalone Startup (startup.ts)
```typescript
const program = Effect.gen(function* () {
  yield* Effect.ignore(startGateway(PORT))
  yield* Effect.never  // Keep Scope alive indefinitely
})
Effect.runFork(program.pipe(Effect.scoped))
```

**Critical:** Must use `Effect.runFork` + `Effect.never`, NOT `Effect.runPromise(Effect.scoped(...))`. The latter closes the Scope when the promise resolves, killing all `forkScoped` fibers.

### Consumer (session-bridge.ts)
```typescript
export function processMessage(msg, adapter, workdir) {
  return Effect.gen(function* () {
    const output = yield* Effect.tryPromise({
      try: () => executeCli(text, sessionId, workdir),
      catch: (err) => new Error(`CLI执行失败: ${err.message}`),
    })
    const reply: OutboundMessage = { chatId: msg.chat.id, type: "text", content: output }
    yield* adapter.send(reply)
  }).pipe(Effect.ignore({ log: true }))
}
```

**Pitfall:** `Effect.ignore({ log: true })` swallows ALL errors silently. If the CLI command fails or the send fails, the consumer logs the error but the user sees nothing. For debugging, temporarily replace with explicit error logging.

**⚠️ Feishu v2.0 Event Structure — `chat_id` is nested**

When parsing Feishu v2.0 events (`schema: "2.0"`), the `chat_id` is NOT at the top level of `event`:

```json
{
  "schema": "2.0",
  "header": { "event_type": "im.message.receive_v1" },
  "event": {
    "message": { "chat_id": "oc_xxx", ... },   ← chat_id HERE
    "sender": { "sender_id": { "open_id": "ou_xxx" } },
    "chat_type": "p2p"  ← chat type is also at event level
  }
}
```

The correct extraction path:
```typescript
const message = eventBody.message as Record<string, unknown> | undefined
chat: {
  id: (message?.chat_id as string) || (eventBody.chat_id as string) || "",
  type: eventBody.chat_type === "p2p" ? "private" : "group",
},
```

A common bug is using `eventBody.chat_id` directly (which is undefined in v2.0 events), causing messages to be processed with an empty chat_id — the reply gets sent to nowhere.

**⚠️ Bot sender info vs user sender info**
- The bot's own `open_id` is returned by `GET /open-apis/bot/v3/info`
- The user's `open_id` is in `event.sender.sender_id.open_id`
- When sending a reply via Feishu API, use `chat_id` as `receive_id` with `receive_id_type=chat_id`

## SDK Details

### @larksuiteoapi/node-sdk v1.70.0

- **WSClient** connects to Feishu via the OAuth2 WebSocket endpoint
- Default domain: `Domain.Feishu` (Chinese站, `open.feishu.cn`)
- For Lark (international): pass `domain: "lark"` in constructor
- `start()` is non-blocking — returns immediately after calling `reConnect(true)`
- Connection lifecycle managed via callbacks: `onReady`, `onError`, `onReconnecting`, `onReconnected`
- Event dispatching uses protobuf-encoded frames decoded by SDK
- Inbound event → `dataCache.mergeData()` reassembles chunks → `EventDispatcher.invoke()` → handler
- `EventDispatcher.register()` returns `this` (fluent), handler key is event type string like `"im.message.receive_v1"`
- `RequestHandle.parse(data)` extracts `event_type` from header for v2 events or `event.type` for v1
- Use `wsClient.getConnectionStatus()` to get `{state, lastConnectTime, nextConnectTime, reconnectAttempts}` for diagnostics
- `state` values: `'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed'`

### Python lark_oapi WSClient (for comparison)

The Python SDK's WSClient (used by Hermes Agent) works differently from the Node SDK:

- `start()` is **blocking** — runs `loop.run_until_complete(self._connect())` then `loop.run_until_complete(_select())` forever
- Hermes runs it in a **separate thread** via `loop.run_in_executor(None, _run_official_feishu_ws_client, ws_client, adapter)`
- Event handling uses `event_handler._do_without_validation(pl)` (raw bytes), not `eventDispatcher.invoke(data)` (JSON)
- Uses `asyncio` with `websockets` library (not `ws` npm package)
- Connection URL is obtained via the same `_get_conn_url()` → POST to `{domain}/callback/ws/endpoint` with `{AppID, AppSecret}`
- On connect, the server pongs back with `ClientConfig` (ping interval, reconnect count/interval/nonce)

**Key testing insight:** If the Node SDK WSClient connects but receives no events, test with the Python SDK. If Python ALSO receives no events, the issue is Feishu app configuration, not SDK. If Python receives events but Node doesn't, the issue is SDK-specific.

## Debugging Feishu WebSocket: Step-by-Step

When the WSClient reports "connected" but no events arrive:

### 1. Verify credentials independently
```bash
curl -s -X POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -H "Content-Type: application/json" \
  -d '{"app_id":"cli_xxx","app_secret":"xxx"}' | jq .
```
Expected: `{"code": 0, "tenant_access_token": "..."}`

### 2. Verify the event subscription exists
In Feishu Developer Console → Events & Callbacks, confirm `im.message.receive_v1` is subscribed AND the subscription mode is "长连接" (long connection).

Also click the **"验证连接" (Verify Connection)** button after the WebSocket is connected. This only confirms the WebSocket handshake — it does NOT send a test `im.message.receive_v1` event.

### 3. Verify the bot can SEND messages
```bash
TOKEN=$(curl ... | jq -r '.tenant_access_token')
curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"test\"}"}'
```
If this succeeds but events don't arrive, the issue is event delivery, not credentials.

### 4. Test the internal pipeline (queue → consumer → send)
Write a test script that directly offers a message to the shared queue:
```typescript
import { getMessageQueue } from "./src/lifecycle"
import { Queue, Effect } from "effect"

const mq = getMessageQueue()
if (mq) Effect.runFork(Queue.offer(mq, {
  id: "test", platform: "feishu", type: "text",
  content: "测试消息",
  sender: {id:"test",name:"test"},
  chat: {id:"oc_test",type:"private"},
  timestamp: Date.now(), raw: {}
}))
```
If the consumer processes it and sends a reply, the internal pipeline is healthy.

### 5. Test raw WebSocket (bypass SDK)
Create a test script using Bun's native `WebSocket` to connect directly and log ALL incoming data:
```typescript
const resp: any = await fetch("https://open.feishu.cn/callback/ws/endpoint", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ AppID: "cli_xxx", AppSecret: "xxx" }),
}).then(r => r.json())

const ws = new WebSocket(resp.data.URL)
ws.onopen = () => console.log("✅ 已连接")
ws.onmessage = (e) => console.log("📩 收到:", e.data)
ws.onerror = (e) => console.log("❌ 错误:", (e as any).message)
ws.onclose = (e) => console.log("🔒 关闭:", e.code, e.reason)
```
Run for 60+ seconds. If `onmessage` never fires, the Feishu server is NOT sending any data through this WebSocket.

### 6. Compare with Python SDK baseline
Use the Python `lark_oapi` SDK (available in Hermes venv) with the SAME credentials:
```python
from lark_oapi.ws import Client as FeishuWSClient
client = FeishuWSClient(app_id="cli_xxx", app_secret="xxx",
    log_level=LogLevel.DEBUG, event_handler=handler)
client.start()
```
If Python SDK receives events but Node SDK doesn't, the issue is in the Node SDK's protocol implementation. If neither receives events, the issue is app configuration on Feishu side.

### 7. Enable DEBUG logging in Node SDK
```typescript
const wsClient = new Lark.WSClient({
  appId, appSecret,
  loggerLevel: Lark.LoggerLevel.debug, // ← DEBUG
})
```
This logs: raw WebSocket URL, connect success, every ping/pong, every received message (event type + message_id), and every executed handler.

### 8. Reading SDK internal state
```typescript
const status = wsClient.getConnectionStatus()
// { state: 'connected', lastConnectTime: 123, nextConnectTime: 456, reconnectAttempts: 0 }
```
This is non-invasive and works even when `onError` hasn't fired.

## Diagnostic Scripts

### ws-diagnose.ts — Full Node SDK diagnostic with DEBUG logging
```typescript
import * as Lark from "@larksuiteoapi/node-sdk"

const dispatcher = new Lark.EventDispatcher({
  loggerLevel: Lark.LoggerLevel.debug,
}).register({
  "im.message.receive_v1": async (data) => {
    console.log("*** [收到消息事件] ***", JSON.stringify(data).slice(0, 500))
  },
})

const wsClient = new Lark.WSClient({
  appId: process.env.OPENCODE_FEISHU_APP_ID!,
  appSecret: process.env.OPENCODE_FEISHU_APP_SECRET!,
  loggerLevel: Lark.LoggerLevel.debug,
  onReady: () => console.log("[onReady] 连接就绪"),
  onReconnecting: () => console.log("[onReconnecting] 重连中"),
  onReconnected: () => console.log("[onReconnected] 重连成功"),
  onError: (err) => console.log("[onError]", err.message),
})

wsClient.start({ eventDispatcher: dispatcher })

setInterval(() => {
  const s = wsClient.getConnectionStatus()
  console.log(`[状态] state=${s.state}, reconnectAttempts=${s.reconnectAttempts}`)
}, 10000)
```

### test_pyws.py — Python SDK baseline test
```python
import asyncio
from lark_oapi.ws import Client as FeishuWSClient
from lark_oapi.core.enum import LogLevel

class Handler:
    def _do_without_validation(self, data):
        print(f"收到事件: {data.decode('utf-8')[:200]}")
        return {"code": 0}

client = FeishuWSClient(app_id="xxx", app_secret="xxx",
    log_level=LogLevel.DEBUG, event_handler=Handler())
client.start()
```

## Known Issues

- **ECONNREFUSED on reconnect**: Usually transient. SDK retries with exponential backoff (`reconnectCount`, `reconnectInterval` from server response).
- **"ws client ready" but no events**: The `@larksuiteoapi/node-sdk` WSClient may connect successfully but receive ZERO events even with correct app configuration. This is a known SDK compatibility issue. Use Python `lark_oapi` SDK as bridge (see `references/python-ws-bridge-alternative.md`).
- **Config field**: The opencode.jsonc field is `"plugin"` (singular), not `"plugins"` (plural). Entries can be strings or objects with `package` + `options`.
- **Two Feishu bots on same machine**: If Hermes (cli_a9255c26047adbc6) and AirDeepCode (cli_aabbc8199ab89bea) run simultaneously, they use different app IDs and don't conflict. However, they share the same host and WS endpoint (`msg-frontier.feishu.cn`).
- **Verify Connection button**: In Developer Console → Events & Callbacks, clicking "Verify Connection" only confirms the WebSocket handshake succeeded. It does NOT send a test `im.message.receive_v1` event and does NOT guarantee that message events will flow.
- **Bot accessibility**: If the API returns `"Bot has NO availability to this user"` (code 230013), the bot hasn't been added by the user. The user must open a 1-on-1 chat with the bot. For self-built apps, the bot is visible to all tenant members by default.
- **Python vs Node SDK behavior**: Both SDKs connect to the same endpoint (`wss://msg-frontier.feishu.cn/ws/v2?aid=...`) with the same access_key/ticket pattern. If Python SDK receives events but Node SDK doesn't, look for differences in: WebSocket subprotocol negotiation, protobuf decode/encode, or EventDispatcher event routing.
- **v2.0 event structure bug**: The `chat_id` is at `event.message.chat_id`, NOT `event.chat_id`. Parsing `event.chat_id` returns undefined, causing messages to process with empty chat_id and replies sent to nowhere.
- **Python bridge forwarding log level**: The bridge's `_forward_event` success log defaults to `logger.debug`. When debugging, change to `logger.info` so you can see events being forwarded in the logs.

## CLI Binary Build

When the deepcode CLI (`packages/opencode/bin/opencode`) fails with "platform-specific binary not installed":

```bash
# Upgrade bun if needed (build script checks version)
bun upgrade

# Build the CLI
cd /Volumes/Doc/Code/deepcode && bun run packages/opencode/script/build.ts

# Symlink the binary so the wrapper can find it
ln -sf dist/opencode-darwin-arm64/bin/opencode node_modules/opencode-darwin-arm64/bin/opencode
```

The build script produces binaries under `dist/opencode-{os}-{arch}[/bin/opencode]`.

## Verification Commands

```bash
# Health check
curl http://localhost:3099/health

# Feishu challenge
curl -X POST http://localhost:3099/webhook/feishu \
  -d '{"type":"url_verification","challenge":"test123"}'

# Simulated message event via webhook
curl -X POST http://localhost:3099/webhook/feishu \
  -H "Content-Type: application/json" \
  -d '{
    "header": {"event_type": "im.message.receive_v1"},
    "event": {
      "sender": {"sender_id": {"open_id":"user"}, "sender_type":"user"},
      "message": {"message_id":"test","message_type":"text","content":"{\"text\":\"hello\"}"},
      "chat_id":"oc_test"
    }
  }'

# Direct queue injection test (writes test message to the running gateway queue)
bun run -e '
import { getMessageQueue } from "./src/index"
import { Queue, Effect } from "effect"
const mq = getMessageQueue()
if (mq) Effect.runFork(Queue.offer(mq, {
  id: "test", platform: "feishu", type: "text",
  content: "测试消息", sender: {id:"test",name:"test"},
  chat: {id:"oc_test",type:"private"}, timestamp: Date.now(), raw: {}
}))
console.log("消息已注入队列，检查网关日志看消费结果")
'
```
