# 外部 Agent 使用 Hermes 模型基础设施 — 参考文档

> 基于 2026-07-15 安装和配置 Agent TARS 的完整会话记录。

## Agent TARS CLI 安装

```bash
# MacBook / 任意有 Node.js >= 22 的环境
npm install -g @agent-tars/cli@latest

# AIPC（Linux/Deepin）先切换 nvm
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
npm install -g @agent-tars/cli@latest
```

### 验证安装

```bash
# MacBook 通过 npx 或全局命令
npx @agent-tars/cli --version
# → agent-tars/0.3.0 darwin-arm64 node-v26.0.0

# AIPC 需要先 nvm use 22
nvm use 22
agent-tars --version || npx @agent-tars/cli --version
# → agent-tars/0.3.0 linux-x64 node-v22.23.1
```

> **注意**：Homebrew 安装的 Node.js（MacBook）有时不会自动在 PATH 中加入全局 npm bin。如 `agent-tars` 命令找不到，用绝对路径或 `npx @agent-tars/cli`。

## UI-TARS Desktop 安装（macOS）

```bash
# 方法 A：brew（可能版本较旧）
brew install --cask ui-tars

# 方法 B：从 GitHub Releases 下载最新 DMG
# 1. 打开 https://github.com/bytedance/UI-TARS-desktop/releases/latest
# 2. 下载 UI-TARS-*-arm64.dmg（Apple Silicon）或 x64.dmg（Intel）
# 3. 挂载并拖入 /Applications
# 4. 授权：系统设置 → 隐私 → 辅助功能 + 屏幕录制
```

> **注意**：GitHub Release 在墙内下载可能不稳定。用 `curl -L -C -` 支持断点续传，或走代理。

## 模型链路架构

### 关键组件

| 组件 | 说明 |
|------|------|
| **Hermes** | AI Agent 框架，配置 provider 为 `opencode-go` |
| **OpenCode CLI** | 提供模型路由和认证，运行于 port 4096 |
| **opencode.ai/zen/go/v1** | OpenAI 兼容的 Chat Completions API 端点 |
| **AIPC passthrough** | 本地代理 `127.0.0.1:41428` → `opencode.ai/zen/go/v1` |
| **OPENCODE_API_KEY** | 共享 API Key（67 字符），存于环境变量 |

### 数据流

```
Agent TARS
  → [--model.provider openai]
  → [--model.baseURL https://opencode.ai/zen/go/v1]
  → [--model.apiKey $OPENCODE_API_KEY]
  → [--model.id kimi-k2.6]
  → OpenAI 格式 Chat Completions 请求
  → opencode.ai/zen/go/v1/chat/completions
  → opencode-go 内部路由 → 实际模型提供商
```

## Agent TARS 配置文件

### MacBook：`~/.agent-tars/agent.config.ts`

```typescript
export default {
  model: {
    provider: 'openai',
    id: 'kimi-k2.6',
    apiKey: process.env.OPENCODE_API_KEY,
    baseURL: 'https://opencode.ai/zen/go/v1',
  },
  browser: {
    control: 'hybrid',  // 视觉+DOM 混合，最稳定
  },
  thinking: {
    type: 'enabled',
  },
};
```

### AIPC（使用本地 passthrough，延迟更低）

```typescript
export default {
  model: {
    provider: 'openai',
    id: 'kimi-k2.6',
    apiKey: process.env.OPENCODE_API_KEY,
    baseURL: 'http://127.0.0.1:41428/v1',
  },
  browser: {
    control: 'hybrid',
  },
  thinking: {
    type: 'enabled',
  },
};
```

### 运行命令

```bash
# 交互模式（Web UI）
agent-tars --config ~/.agent-tars/agent.config.ts

# 无头模式（命令行）
agent-tars --config ~/.agent-tars/agent.config.ts \
  --headless --input "你的指令" --format text
```

## 模型选择指南

### 可用的多模态模型

通过 `opencode-go` provider 可用的模型（来源：Hermes 或 OpenCode 配置）：

- **kimi-k2.6** — 推荐！支持 text+image，标准 content 输出，262K context
- **kimi-k2.7-code** — 类似 K2.6 但更面向代码
- **mimo-v2.5** — 支持 text+image，但仅输出 reasoning_content（不兼容标准 OpenAI 格式）
- **mimo-v2.5-pro** — 同 V2.5，仅 reasoning_content

### 模型兼容性测试

```bash
curl -s https://opencode.ai/zen/go/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCODE_API_KEY" \
  -d '{
    "model":"kimi-k2.6",
    "messages":[{"role":"user","content":[{"type":"text","text":"Describe this"}]}],
    "max_tokens":100
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
msg=d['choices'][0]['message']
print('content:', repr(msg.get('content','')[:100]))
print('reasoning:', type(msg.get('reasoning_content')))
"
```

判断标准：
- `content` 字段有内容 ✅ 兼容
- `content` 为 null，仅有 `reasoning_content` ❌ 不兼容标准格式

## AIPC passthrough 代理

AIPC 上运行的 passthrough 代理（`/home/bluth/bin/opencode-passthrough.mjs`）是一个极简的 Node.js HTTP 代理：

```javascript
const TARGET = "https://opencode.ai/zen/go/v1";
// 监听 127.0.0.1:41428
// 将 Authorization header 透传给上游
// 仅 POST /v1/chat/completions 有效
```

该代理仅监听 `127.0.0.1`，无法跨机器访问。如需从 MacBook 使用：
1. **SSH 隧道**：`ssh -L 41428:127.0.0.1:41428 bluth@100.89.88.88`
2. **直接调用**：使用 `https://opencode.ai/zen/go/v1` 远程端点（MacBook 默认方案）

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `401 Invalid API key` | API Key 未正确传入 | 检查 `process.env.OPENCODE_API_KEY` 是否设置；TypeScript 配置中是否使用了 `process.env.X` |
| `Error: Invalid request body` | `agent-tars request` 命令的 body JSON 格式不符合预期 | 用标准的 `agent-tars run --config ... --headless` 方式，不要用 `request` 命令 |
| `Connection refused` (AIPC:41428) | passthrough 代理未运行 | 检查进程 `ps aux | grep opencode-passthrough`；手动启动 `node ~/bin/opencode-passthrough.mjs &` |
| `Missing API key` | 请求未带 Authorization header | 配置文件中 apiKey 为空或 env var 未导出 |
| 模型返回空内容 | 模型可能只输出了 reasoning_content | 换用 kimi-k2.6 替代 mimo-v2.5 |
