# DeepSeek V4 Reasoning Effort 映射真相

## 关键发现：OpenCode Go 和 Hermes 用不同的值

| 场景 | 正确值 | 为什么 |
|------|--------|--------|
| **NewAPI param_override** | `max` | OpenCode Go 直接接受 `max`，不需要中间层 |
| **Hermes config.yaml** | `xhigh` | Hermes 合法值，opencode-go provider 自动映射为 `max` |
| **直接 curl / 客户端** | `max` | 和 NewAPI 一样，直达 OpenCode Go |

## 实证对比（2026-06-10 实测，同一 prompt "1+1=?"）

通过 NewAPI → OpenCode Go，DS V4 Flash：

| reasoning_effort | 推理 tokens | 总 tokens | 结论 |
|-----------------|------------|----------|------|
| `max` | **60** | **147** | 真正最高档 ✅ |
| `high` | 33 | 126 | 次高档 |
| `xhigh` | 31 | 124 | OpenCode Go 不认识，降级 |
| `x-high` | 31 | 124 | 和 xhigh 一样，也降级 |

## 陷阱

- Hermes config 写 `max` → **无效**，被 Hermes 忽略降级为默认 `medium`
- Hermes config 写 `xhigh` → **正确**，opencode-go provider 服务端映射为 `max`
- NewAPI param_override 写 `xhigh` → **错误**，OpenCode Go 不认识，降级为中档
- NewAPI param_override 写 `max` → **正确**，OpenCode Go 直接接受

## 成本影响

`max` 比 `high` 多消耗 ~60% 推理 tokens。但对总体成本影响极小，因为输出 tokens（含推理）在 Agent 场景中只占总 token 消耗的 0.4%-0.65%。
