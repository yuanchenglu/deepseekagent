---
name: hermes-reasoning-effort-config
description: 配置 Hermes Agent 的推理强度（reasoning_effort）—— 全局设置、会话级设置、per-model 映射表。基于 opencode-go provider 和 DeepSeek V4 / Kimi K2 / GLM 等模型的实测映射。
---

# Hermes Reasoning Effort 配置指南

## 背景

Hermes 支持通过 `reasoning_effort` 控制模型的推理强度。该值经过 opencode 网关时会被按模型类型映射到对应的 API 参数。

## Hermes 合法性值

来源：`hermes_constants.py` → `VALID_REASONING_EFFORTS`

```
none      → 关闭推理（{"enabled": false}）
minimal   → 最低推理强度
low       → 低
medium    → 中（默认值）
high      → 高
xhigh     → 最高（当前推荐配置）
```

## 映射表（opencode-go / opencode-zen provider）

| 模型 | 是否传 reasoning_effort | xhigh 映射结果 | 最高有效值 |
|---|---|---|---|
| **deepseek-v4-pro** | ✅ 传 | `xhigh` → `max` | `max` |
| **deepseek-v4-flash** | ✅ 传 | `xhigh` → `max` | `max` |
| **kimi-k2.5 / k2.6** | ✅ 传 | `xhigh` → 降级为 `high` | `high` |
| **glm-5.1 / glm-5** | ❌ 不传 | 服务器自决 | — |
| **mimo-v2.*** | ❌ 不传 | 服务器自决 | — |
| **minimax-m2.*** | ❌ 不传 | 服务器自决 | — |
| **qwen3.*** | ❌ 不传 | 服务器自决 | — |

> 映射逻辑在 opencode 网关服务端，不在 Hermes 插件中。

## 三种配置方式

### 方法一：全局默认（config.yaml）
```bash
hermes config set agent.reasoning_effort xhigh
```
写入 `~/.hermes/profiles/<profile>/config.yaml` 的 `agent:` 段。
**所有会话生效，重启后加载。**

### 方法二：单会话设置
```
/reasoning xhigh
```
仅当前会话生效，适合对特定群组设不同值。

### 方法三：全局持久化（从会话写入 config）
```
/reasoning xhigh --global
```
等价于方法一，但可在会话中直接完成。

## 注意事项

- opencode-go provider 的 `build_api_kwargs_extras()` 当前返回 `({}, {})`，不添加任何 `extra_body` 或 `top_level` 参数。opencode 网关侧根据模型名称在服务端处理映射。
- `delegation.reasoning_effort`（子代理配置）与 `agent.reasoning_effort`（主代理配置）是两个独立字段，互不影响。
- 目前不支持 per-model 配置，但可利用群组模型隔离实现差异化：在每个群组里跑 `/reasoning xhigh` 分别设置。

## 常见陷阱

### 陷阱 1：误用 `max` 而非 `xhigh`
`max` 是 opencode 网关侧的内部映射值，**不是 Hermes 合法值**。在 `config.yaml` 里写 `reasoning_effort: max` 会被 Hermes 忽略（降级默认 `medium`）。正确的写法是：

```yaml
# ❌ 错误
agent:
  reasoning_effort: max

# ✅ 正确 — Hermes 用 xhigh，opencode 网关自动映射为 max
agent:
  reasoning_effort: xhigh
```

### 陷阱 2：只配了 `delegation.reasoning_effort` 没配 `agent.reasoning_effort`
两者独立，需要分别设置。常见情况是只配了子代理的推理（`delegation.reasoning_effort`），主代理仍保持默认 `medium`。

```bash
# 需要同时设置两个
hermes config set agent.reasoning_effort xhigh
hermes config set delegation.reasoning_effort xhigh
```

### 陷阱 3：修改后未重启会话
`reasoning_effort` 在会话启动时读取，修改配置后需要 `/new`（新会话）或重启 gateway 才生效。`/reasoning xhigh` 可立即在当前会话生效。

## 验证方法

```bash
# 确认配置已写入（默认 profile）
grep -E 'reasoning_effort' ~/.hermes/config.yaml

# 如果使用命名 profile
grep -E 'reasoning_effort' ~/.hermes/profiles/<profile>/config.yaml

# 同时检查两个字段是否都已设置
grep -E 'reasoning_effort' ~/.hermes/config.yaml ~/.hermes/profiles/*/config.yaml 2>/dev/null
```
