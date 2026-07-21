# Python WS Bridge — 飞书长连接替代方案

## 背景

`@larksuiteoapi/node-sdk` 的 `WSClient` 存在已知兼容性问题：**成功连接 WebSocket（`ws client ready`）后，飞书服务器不推送任何事件**。即使事件订阅正确、权限已授权、WebSocket 状态为 `connected`，`onmessage` 回调从未触发。

经实测验证，Python `lark_oapi` SDK 的 `WSClient` 使用相同凭证、相同 App，**能正常接收事件**。

## 现象对比

| SDK | 连接状态 | 收到 ping/pong | 收到事件 |
|-----|---------|---------------|---------|
| `@larksuiteoapi/node-sdk` v1.70.0 WSClient | `connected` | ✅ 自动处理 | ❌ 零事件 |
| Bun 原生 `new WebSocket(url)` | `readyState=1 (OPEN)` | ❌ 无数据 | ❌ 零事件 |
| Python `lark_oapi` WSClient | `connected` | ✅ | ✅ `im.message.receive_v1` |
| Python `websockets.connect()` raw | `open` | ✅ | ✅ 原生 protobuf 帧 |

## 根因推测

Node SDK 的 WSClient 实现与 Feishu 服务器之间的 WebSocket 协议存在兼容性问题。具体可能包括：
- protobuf 帧的解码/处理差异
- WebSocket 子协议或扩展协商不一致
- Node `ws` 库（v8.19.0）与 Feishu 服务端的二进制帧交互问题

## 解决方案：Python WS Bridge

不替换 Node Gateway 架构，只把 WebSocket 长连接部分换成 Python SDK：

```
飞书 WS → Python WSClient → HTTP POST → Node Gateway → 队列 → 消费者 → CLI → API 回发
```

### 架构要点

1. **Python 脚本**使用 `lark_oapi.ws.Client` 建立长连接
2. 注册 `im.message.receive_v1` 等事件处理器
3. 收到事件后，通过 `aiohttp` 以 HTTP POST 转发原始 payload 到 Node Gateway 的 `/webhook/feishu/bridge` 端点
4. **Node Gateway** 的 Router 增加前缀匹配：`/webhook/feishu/bridge` → 同一队列
5. 现有消费者、CLI 执行、API 回发链路不变

### Python 桥接脚本核心代码

```python
class BridgeClient(FeishuWSClient):
    def __init__(self, forward_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._forward_url = forward_url
        self._http_session = None

    async def _handle_data_frame(self, frame) -> None:
        """覆盖父类方法：在 SDK 事件分发之前拿到原始 payload"""
        hs = frame.headers
        type_ = _get_by_key(hs, HEADER_TYPE)
        message_type = MessageType(type_)
        if message_type != MessageType.EVENT:
            return
        pl = frame.payload
        # 异步转发到 Node Gateway
        asyncio.get_event_loop().create_task(self._forward_event(pl))
        # 回 ack
        resp = Response(code=200)
        frame.payload = JSON.marshal(resp).encode("utf-8")
        await self._write_message(frame.SerializeToString())

    async def _forward_event(self, payload: bytes) -> None:
        async with self._http_session.post(
            self._forward_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status != 200:
                logger.error("转发失败 HTTP %s", resp.status)
```

### Node 端改动

```typescript
// adapter.ts — spawn Python bridge as subprocess
const bridgeProcess = Bun.spawn(
  ["/path/to/python", "scripts/feishu-bridge.py"],
  { env: { ...process.env }, stdio: ["ignore", "pipe", "pipe"] }
)

// router.ts — 前缀匹配
dispatch(path: string, body: unknown) {
  let queue = this.routes.get(path)
  if (!queue) {
    for (const [registered, q] of this.routes) {
      if (path.startsWith(registered + "/") || path === registered) {
        queue = q; break
      }
    }
  }
  // ...
}
```

### 注意事项

- **Python 路径**：使用 Hermes venv 的 Python（已有 `lark_oapi`），或者安装 `pip install lark-oapi` 在项目虚拟环境
- **日志级别**：桥接脚本的 `_forward_event` 成功日志默认设为 DEBUG，调试时改为 INFO
- **自动重连**：Python SDK 自带 `auto_reconnect`，在 `ClientConfig` 中控制重连参数
- **合包处理**：大量事件会分片传输，桥接脚本继承父类的 `_combine` 方法处理合包
- **Router 前缀匹配**注册路径时注册基础路径（如 `/webhook/feishu`），桥接路径（如 `/webhook/feishu/bridge`）通过前缀匹配路由
