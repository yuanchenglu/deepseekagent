# LLM Agent Runtime 模型优化分析清单

当用户问"某个 Agent 产品对某个 LLM（如 DeepSeek）做了哪些独特优化"时，
使用这份分层分析清单，逐层检查源码。

## 分析分层

### 1. Cache-First Agent Loop（最重要）
- [ ] 是否有 immutable prefix 设计？系统提示词、工具定义是否稳定化？
- [ ] 工具 schema 是否 canonical sort？JSON key 顺序是否规范化？
- [ ] 是否优先使用 LLM 原生缓存命中字段（如 `prompt_cache_hit_tokens`）？
- [ ] 缓存命中率计算公式是什么？用 `hit/(hit+miss)` 还是 `hit/prompt_tokens`？
- [ ] 是否有 prefix fingerprint 校验机制？漂移时如何检测？
- [ ] 实测命中率数据？（文档或代码中的 benchmark）

**源码定位**：`cache/`、`loop/agent-loop.ts`、`adapters/model/` 下的 model client

### 2. Token Economy / 上下文卫生
- [ ] 发送给模型的历史是否在请求边界做过压缩？
- [ ] 超大 tool_result 如何处理？（截断、省略、signal line 保留？）
- [ ] base64/binary payload 是否被省略？
- [ ] 重复行是否合并？
- [ ] 压缩后磁盘数据是否保留完整？（即只压缩发送，不破坏记录）
- [ ] 是否有 token economy mode 开关？是否可配置？

**源码定位**：`loop/request-history-hygiene.ts`、`loop/token-economy.ts`

### 3. Context Compaction（长会话压缩）
- [ ] 压缩触发条件是什么？基于估算还是真实 usage.prompt_tokens？
- [ ] 分几级压缩模式？（soft/hard/force？）
- [ ] pinned constraints 是否跨越 compaction 保留？
- [ ] 压缩摘要由什么生成？本地规则还是额外调用模型？

**源码定位**：`loop/context-compactor.ts`、`loop/context-estimator.ts`

### 4. Model History Repair（消息合法性修复）
- [ ] 孤儿 `tool_result`（缺对应 tool_call）是否过滤？
- [ ] 缺 result 的 `tool_call` 是否过滤？
- [ ] 同一响应的多个 tool_call 是否重组为合法 assistant 消息？
- [ ] streamed tool-call delta 是否按 index/id 正确合并？
- [ ] fork/resume 时是否修复克隆历史的工具配对？

**源码定位**：`domain/model-history-repair.ts`、`loop/tool-call-repair.ts`

### 5. Tool Context Optimization（工具上下文优化）
- [ ] MCP 工具多了如何处理？全量塞进 prompt 还是渐进发现？
- [ ] 是否有 `mcp_search` → `mcp_describe` → `mcp_call` 三步法？
- [ ] 内置只读工具是否支持小批量并发？（read/grep/find/ls）
- [ ] 是否有重复工具调用阻断？（storm breaker）
- [ ] 工具输出写入顺序是否稳定？（不随完成顺序抖动）

**源码定位**：`adapters/tool/mcp-tool-search.ts`、`loop/tool-storm-breaker.ts`、`loop/agent-loop.ts`

### 6. Architecture（架构层）
- [ ] Agent 运行时是单例还是多实例？是否统一 HTTP/SSE 边界？
- [ ] GUI/UI 层是否直接参与 agent 逻辑还是只做 client？
- [ ] 是否可观测？（usage API、cache hit/miss 面板）
- [ ] 是否有 settings migration 兼容旧版本？

**源码定位**：`server/`、`cli/serve.ts`、架构文档（KUN_ARCHITECTURE.md 等）

## 实战案例

### DeepSeek-GUI/Kun for DeepSeek（2026-06-07 分析，2026-06-07 源码全量验证）

| 层次 | Kun 实现 | 关键源码 |
|------|---------|---------|
| Cache-First | immutable prefix + SHA-256 fingerprint + canonical sort tools + 原生缓存字段优先 + **prefix volatility 扫描**(UUID/ISO/hex/JWT) | `kun/src/cache/immutable-prefix.ts` L44-52, L162-170; `kun/src/cache/prefix-volatility.ts` (221行) |
| Token Economy | 请求边界三重约束(bytes/lines/tokens) + base64省略 + 重复合并 + **AI废话压缩**(filler/pleasantries/hedging/leaders/articles stripping, 保护代码/URL/标识符) | `kun/src/loop/request-history-hygiene.ts` (397行), `kun/src/loop/token-economy.ts` L143-158 |
| Compaction | usage.prompt_tokens 驱动 + 三级(soft/aggressive/hard) + pinned constraints 保留 + **本地规则摘要**(非LLM生成) + SHA-256 digest marker | `kun/src/loop/context-compactor.ts` L71-93, L101-167; `kun/src/loop/compaction-marker.ts` |
| History Repair | 孤儿tool_result过滤 + 缺result tool_call过滤 + multi-call重组 + fork修复 + **双层修复**(model adapter层修JSON parse + loop层修wrapper keys/oversized strings) | `kun/src/domain/model-history-repair.ts`; `kun/src/adapters/model/tool-argument-repair.ts`; `kun/src/loop/tool-call-repair.ts` |
| Tool Context | MCP BM25渐进发现 + 中英文分词 + 只读并发(max 3) + storm breaker(threshold=3,第3次抑制) + 工具结果按调用顺序落盘(不随完成顺序抖动) | `kun/src/adapters/tool/mcp-tool-search.ts`; `kun/src/loop/tool-storm-breaker.ts`; `kun/src/loop/agent-loop.ts` L74-75 |
| Architecture | 单Kun运行时 + HTTP/SSE边界 + GUI只做client + usage telemetry + **secret redaction** + settings migration | `kun/src/server/`; `docs/kun-architecture.md`; `kun/src/config/secret-redaction.ts` |

**实测命中率**：热身后 94.7%-98.1%（`docs/kun-cache-optimization.md` L288-292）

**V4 API 兼容性重要发现**：Kun 使用标准 OpenAI-compatible `role: 'tool'` + `tool_call_id` 发送工具结果（`deepseek-compat-model-client.ts` L392-397），说明 DeepSeek V4 API 层兼容此格式。是否 V4 在 native encoding 层使用不同协议（如 DSML）需单独验证——Kun 走的是 API 兼容路径而非 native encoding 路径。

## 输出格式

分析结果按层次组织，每层给出：
1. 优化名称和本质（1-2句）
2. 源码位置（文件路径 + 行号）
3. 为什么对目标模型重要
4. 实现细节摘要

最终给出总结表格，标注各层次的优化深度和影响。
