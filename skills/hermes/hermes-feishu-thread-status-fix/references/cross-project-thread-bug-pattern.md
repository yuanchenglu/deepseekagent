# Cross-Project Feishu Thread Reply Bug Pattern

## Premise

When you discover that one project's Feishu/Lark integration has a "bot
messages create standalone topics instead of replying in-thread" bug,
**check other projects that integrate with Feishu for the same pattern**.
The root cause is almost universal: developers default to `create` API
and forget to call `reply` for thread groups.

## Affected Projects (Confirmed)

| Project | File | Function | Fix PR |
|---------|------|----------|--------|
| Hermes Agent (Python) | `gateway/platforms/feishu.py` → `_prepare_reply_context` | Status messages missing `reply_to` | NosResearch/hermes-agent#internal |
| CodeWhale (Node.js) | `integrations/feishu-bridge/src/index.mjs` → `sendText()` | `client.im.message.create()` used instead of `reply()` for ALL messages | Hmbown/CodeWhale#2148 |

## Diagnostic Checklist

To check if a Feishu bridge has the same bug:

1. **Find the send/reply function** — look for where bot messages are sent
   to Feishu. Common names: `sendText`, `sendMessage`, `_send_raw_message`,
   `_build_message_request`.

2. **Check API call type**:
   - ✅ Uses `reply` API with `message_id` → probably correct
   - ❌ Uses `create` API with only `chat_id` → **will create standalone topics**
   - ❔ Uses `create` with `chat_id` + optional params → check if `thread_id`
     or `root_id` is passed

3. **Feishu/Lark SDK API surface**:
   ```
   client.im.message.create(    { params: { receive_id_type }, data: { receive_id, msg_type, content } })
   client.im.message.reply(     { path: { message_id }, data: { msg_type, content } })
   ```

4. **Check incoming message handler** — does it extract and propagate
   `message_id` / `parent_id` / `root_id` / `thread_id` through the
   call chain, or does it only pass `chat_id`?

## Root Cause Pattern

```
Incoming message
  └─ handler extracts only chat_id (loses thread context)
       └─ passes chat_id to sendText()
            └─ sendText() uses create(chat_id) → new standalone topic ✗

Fixed:
Incoming message
  └─ handler extracts message_id + chat_id (preserves thread context)
       └─ stores message_id as replyToMessageId
            └─ sendText() uses reply(message_id) → stays in thread ✓
```

## Why Developers Miss This

- `client.im.message.create()` works fine in non-thread groups (普通群)
- The bug is **only visible** in thread-enabled groups (话题群)
- Even in topic groups, the first bot response often looks correct
  because Feishu auto-groups it; the problem shows up on subsequent
  messages (status updates, approval prompts, streaming chunks)
- The `create` API does not return an error when called without thread
  context in a topic group — it silently creates a new topic
