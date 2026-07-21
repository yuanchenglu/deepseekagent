# NewAPI 参数覆盖 & 模型映射参考

## 一、models 与 model_mapping 的核心区别

这是 NewAPI 配置中最容易混淆的概念。

| 字段 | 作用 | 路由依据？ |
|------|------|-----------|
| `channels.models` | **这个渠道能处理哪些模型**（路由白名单） | ✅ 是——路由只看 models |
| `channels.model_mapping` | **名字翻译器**——用户说的名 → 实际发的名 | ❌ 不是——mapping 只是翻译，不决定路由 |

### 请求处理链路

```
用户传 model = "gpt-4o"
  → 在 abilities 表（由 channels.models 生成）里找 "gpt-4o"
    → 找到吗？
      → 找到 → 直接路由
      → 没找到 → 查 model_mapping
        → "gpt-4o" → "kimi-k2.6"
          → 把请求 body 里的 model 改成 "kimi-k2.6"
            → 再去 abilities 找 "kimi-k2.6"
              → 找到了 → 路由
```

### 常见误解

**误解：** models 和 model_mapping 是两个独立的列表，用户传哪个名就走哪个。
**实际：** **路由只看 models（abilities）。** model_mapping 是传进来发现 models 里没有，才触发的翻译器。

所以同一个用户同一把 token，传 `gpt-4o` 和传 `kimi-k2.6` 都能工作——只要 kimi-k2.6 在 models 里、gpt-4o 在 mapping 里被翻译成 kimi-k2.6。**不需要两个渠道。**

### 渠道分组隔离（用户A只能用 gpt-4o，用户B只能用 deepseek）

只有当用户需要**严格隔离**（用户A不能调用 deepseek，用户B不能调用 gpt-4o）时，才需要多个渠道 + 不同 group：

1. 建两个渠道，分属不同 group（如 `gpt4o-plan`、`ds-plan`）
2. 每个渠道的 `models` 字段只放该 group 允许的模型名
3. 用户的 token 绑定到对应 group
4. 用户传越权的模型名 → 在该 group 的 abilities 里找不到 → 403

不需要在 mapping 上做文章，mapping 始终只是翻译。

### 警告"映射的上游模型也在此处列出"

当 `model_mapping` 的目标（右侧值）同时也在 `models` 字段里时，NewAPI 提示：

> "把被映射的目标从 models 里删掉，让 /v1/models 列表只显示友好名字"

**不影响功能**，只是 UI 洁癖提示。如果客户端经常直接传原始名（如 `deepseek-v4-flash`），保留它们也合理。

---

## 二、param_override 详解

### 它在哪

渠道编辑页面 → **参数覆盖** 文本框。存于 `channels.param_override` 字段（JSON）。

### 工作原理

param_override 中的键值对会在 NewAPI **转发请求给上游时**，**强制合并**到请求 body 中：
- 请求 body 已有的字段 → 被覆盖
- 请求 body 没有的字段 → 被注入

### 什么能改，什么不能改

| 设的值 | 效果 | 原理 |
|--------|------|------|
| `{"reasoning_effort":"max"}` | ✅ DeepSeek 强制最高推理 | 上游支持该参数，直接注入 |
| `{"max_tokens":4096}` | ✅ 强制限制输出长度 | 标准参数，直接覆盖 |
| `{"temperature":0.1}` | ✅ 强制低温度 | 标准参数，直接覆盖 |
| `{"messages":[{"role":"system","content":"你是GPT-4o"}]}` | ❌ 报错 | **替换了整个 messages 数组**，丢失用户消息 |
| `{"messages_prepend":[...]}` | ❌ 不支持 | v1.0.0-rc.14 没有这个字段，静默忽略 |
| `{"system":"你是GPT-4o"}` | 因模型而异 | OpenAI 格式没有顶级 `system` 字段；Anthropic 格式有，但模型不一定服从 |

**核心限制：** param_override 不能"追加"或"前置"数据到数组字段（如 messages），它只能是**整体替换**。这意味着你无法通过它来给用户的每条对话前插一条 system prompt。

### 实测结果（2026-06-25）

对 minimax-m3（Ch4，Anthropic 格式）设置：
```json
{"messages":[{"role":"system","content":"You are GPT-4o..."}]}
```
结果：HTTP 400 — `invalid params, chat content is empty (2013)`
原因：用户的 `[{"role":"user","content":"Tell me who you are"}]` 被完全替换成了 system 消息，没有 user message，上游拒绝。

### 安全字段：哪些参数可以被覆盖

- `reasoning_effort` ✅
- `max_tokens` ✅
- `temperature` / `top_p` ✅
- `stop` / `frequency_penalty` / `presence_penalty` ✅
- `messages` ❌ 整体替换，不能追加
- `stream` ❌ 改了这个可能导致返回格式不匹配

---

## 三、header_override 详解

### 它在哪

渠道编辑页面 → **请求头覆盖** 文本框。存于 `channels.header_override` 字段（JSON）。

### 作用

控制 NewAPI 发给上游的 HTTP 请求头。比如：
```json
{"X-Title": "My App", "X-Client": "hermes-agent"}
```

### 不能做什么

- **不能改变模型身份** — 模型不会因为 HTTP 头的不同就说自己是另一个模型
- **不能绕过认证** — 除非上游专门支持该头
- 主要用于调试标记、自定义追踪、或上游特定功能开关

---

## 四、能不能让模型自称是 GPT-4o？

**结论：中转站（NewAPI）做不到靠 param_override 或 header_override 让模型改变身份。**

原因很底层：**模型的自我认知是其训练数据的一部分。**

| 模型 | 问"你是谁"的回答 |
|------|----------------|
| deepseek-v4-flash | "I am DeepSeek, an AI assistant created by DeepSeek Company" |
| kimi-k2.6 | "I am Kimi, an AI assistant created by Moonshot AI" |
| minimax-m3 | "I am MiniMax-M3, an AI assistant developed by MiniMax" |

这些回答是模型权重中固化的，不是靠提示词能彻底覆盖的。即使注入 system prompt：
- 有些模型会服从（短期欺骗）
- 有些模型不会服从（坚持真实身份）
- 没有统一保证

### 谁管得了

**客户端（如 Hermes）**：客户端读自己的配置文件，知道用户配了 `gpt-4o`，所以它可以自己宣称"我是 GPT-4o"。这与上游实际返回无关。

但用户用什么客户端你控制不了。

**这就是中转站的边界。** NewAPI 的职责是路由请求、翻译名字、管理额度——不是给模型做人格改造。

---

## 五、相关字段在数据库中的位置

| 字段 | 表 | SQL 查询 |
|------|----|---------|
| model_mapping | channels | `SELECT model_mapping FROM channels WHERE id=?;` |
| param_override | channels | `SELECT param_override FROM channels WHERE id=?;` |
| header_override | channels | `SELECT header_override FROM channels WHERE id=?;` |
| settings | channels | `SELECT settings FROM channels WHERE id=?;`（内含 auto-sync 开关） |
