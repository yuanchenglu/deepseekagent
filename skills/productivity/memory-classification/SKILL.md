---
name: memory-classification
description: "AI Agent 记忆分层体系 — 把平铺的记忆（MEMORY.md）重组为四层架构：SOUL.md（灵魂）→ MEMORY（活跃规则）→ memories/*.md（嵌套参考）→ Skills（工作流）。解决 memory 超过 2000 字符后模型性能下降的问题。"
version: 1.0.0
tags: [memory, classification, architecture, knowledge-management, digital-twin]
---

# 记忆分层体系

> 当我的 memory 超过 2000 字符时，性能开始下降。超过 5000 后幻觉率飙升。
> 根本原因是 Hermes 把所有 memory 全量注入 system prompt，模型被噪声淹没。
> 解决方案是不改 Hermes 代码，把 memory 从平面结构改为分层索引结构。

---

## 一、四层记忆架构

```
┌─────────────────────────────────────────────────────────────┐
│  SOUL.md（灵魂层 — 自动加载到 system prompt 身份槽位）       │
│  ~/.hermes/SOUL.md                                          │
│  身份定义 · 三层认知框架 · 方法论铁律 · 沟通方法论           │
│  特性：永不变化，定义了「我是谁」                            │
│  注入方式：Hermes 自动 load_soul_md()                        │
├─────────────────────────────────────────────────────────────┤
│  MEMORY（活跃规则 — memory 工具 target=memory）              │
│  8-15 条 · ≤200 字符/条 · 总 ≤2000 字符                    │
│  仅放：当前有效的操作规则、项目状态索引、铁律合集            │
│  不放：参考数据、过期状态、详细流程                          │
├─────────────────────────────────────────────────────────────┤
│  USER.md（用户画像 — memory 工具 target=user）               │
│  谁是小路 · 偏好/风格/身份信息 · 决策边界                    │
├─────────────────────────────────────────────────────────────┤
│  memories/*.md（嵌套参考 — ~/.hermes/memories/）             │
│  按需加载：read_file / skill_view                            │
│  类型：凭证引用（$VAR_NAME）、机器配置、教训备忘录、详细规则  │
├─────────────────────────────────────────────────────────────┤
│  Skills（工作流 — ~/.hermes/skills/）                        │
│  可执行的方法论：方舟众测系列、产品研发流程、认知循环        │
│  用 skill_view 按需加载                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心原则

### 原子原则
**单个 memory 项不超过 200 字符。** 超过就外化到 skill、memories/*.md 或外部文档，memory 只放指针和索引。

### 安全原则
**密钥、密码、敏感商业信息 → 绝对不进任何记忆层。** 只在 `.env` 中存明码值，memory/memories/*.md 中引用 `$VAR_NAME`。

### 频次原则
| 使用频率 | 存放位置 |
|---------|---------|
| 每周 ≥ 1 次 | MEMORY（工具中的活跃 memory） |
| 每月 1 次 | memories/*.md 导航（放在 ~/.hermes/memories/ 下） |
| 更少 | skill 或外部文档 |

---

## 三、分类决策树

```
收到一条新的记忆需求
  ↓
是身份/价值观/方法论类的？
  ├─ YES → SOUL.md（手动写入，非 memory 工具）
  ├─ 是小路个人信息？→ USER.md（memory target=user）
  └─ NO → 继续↓
  
是当前有效的操作规则/铁律？
  ├─ YES AND ≤200字符 → MEMORY（memory target=memory）
  ├─ YES BUT >200字符 → 精简到200字符放MEMORY，详细版放memories/*.md
  └─ NO → 继续↓

是可执行的流程/方法论？
  ├─ YES → SKILL（~/.hermes/skills/）
  └─ NO → 继续↓

是静态参考数据（凭证/配置/历史教训）？
  ├─ YES AND 含明码值 → .env 存值，memories/*.md 引用 $VAR_NAME
  ├─ YES AND 无明码 → memories/*.md按需加载
  └─ NO → 删除，不存（用 session_search 检索历史）
```

---

## 四、SOUL.md 内容大纲

写入 `~/.hermes/SOUL.md`（Hermes 自动加载，无需配置）：

```markdown
# 数字分身灵魂定义
## 一、我的角色（我是谁）
## 二、三层认知框架（L1 荣辱观 / L2 思维方式 / L3 三省吾身）
## 三、方法论铁律（假设先行/证据说话/最小改动/带置信度等）
## 四、沟通方法论（苏格拉底递进式/先内后外）
## 五、核心洞察
## 六、版本信息
```

---

## 五、记忆维护策略

### 定期清理（cron 自动）
- 每天 5AM 三省吾身：检查 memory 是否超过 2000 字符，超过则触发瘦身
- 每周日 3AM 自动过期：删除 30 天前未引用的 plan 状态、已过时的项目条目

### 记忆迁移
- 当某个 memory 条目被证明是稳定的（3 周未修改），考虑降级到 memories/*.md
- 当某个 memories/*.md 文件被频繁引用（每周 ≥ 3 次），考虑升级到 MEMORY

### 冲突处理
- SOUL.md 和 MEMORY 内容冲突时 → SOUL.md 优先（灵魂身份 > 操作规则）
- MEMORY 和 memories/*.md 冲突时 → MEMORY 优先（活跃规则 > 参考数据）
- 用户当面纠正 → 立即更新 MEMORY，同时考虑是否同步到 SOUL.md
