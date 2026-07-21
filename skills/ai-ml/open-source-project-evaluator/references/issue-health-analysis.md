# Issue Health Analysis

> 用于评估一个开源项目的 Issue 真实健康度，特别是当大量 Issue 被批量关闭时。
> 核心问题不是"关闭了多少 Issue"，而是**"哪些是真的修了，哪些只是被关了"**。

---

## 适用场景

- 发现某项目的 Issue 被批量关闭，怀疑并非真实修复
- 选择二次开发项目前，评估维护者的 Issue 处理质量
- 分析项目的 Bug 分布，判断哪些子系统最不稳定
- 判断 master 分支的修复时效 vs develop 分支的状态

## 关键原则

| 信号 | 含义 | 行动 |
|------|------|------|
| **批量关闭** | 大量 Issue 在同一短时间内被关，状态为 "completed" | 大概率是临时封禁而非修复 |
| **Not planned / Skipped** | 维护者关闭但明确不处理 | 确认该 Issue 内容后再判断是否需自行解决 |
| **No fix commit** | Issue 有关闭动作但与 git log 无关联 | 90% 以上概率未修复 |
| **Fix only in develop** | 修复 commit 存在但未合并到 master | 功能存在但尚未发布 |
| **Fix in master** | 修复 commit 在 master 分支 | 已发布/可用的真实修复 |

## 核心工具链

### 1. 提取 Issue 列表

从 GitHub 的 Issues 页面获取全量数据（多个页面）：

```bash
# 全部已关闭 Issue（含全部页面）
https://github.com/{owner}/{repo}/issues?q=is%3Aissue+state%3Aclosed&page={N}
```

使用浏览器或 web_extract 逐页提取。排查时注意 GitHub 的搜索限制和登录墙。

### 2. 分类框架

将 Issue 按子系统归类。提供一个可复用的分类框架：

| 类别 | 说明 | 示例 |
|------|------|------|
| **Agent Runtime** | Agent 执行异常、Turn 生命周期、状态机 | Goal 模式中断、Kun Turn Failed |
| **Context Compiler** | 上下文编排、压缩、泄漏、Prefix Cache | 上下文丢失、历史污染 |
| **Tool Runtime** | 工具注册、执行、MCP 集成 | 工具未注册、MCP 异常 |
| **Provider Layer** | API 协议、模型适配、Streaming | 模型空响应、SSE 超时 |
| **Safety Layer** | 权限、沙箱、文件系统约束 | Sandbox 阻塞、权限错误 |
| **UI / GUI** | 前端渲染、布局、图标 | 白屏、图标糊掉、布局错位 |
| **Connectivity** | 后端连接、手机绑定 | 无法连接 kun serve |
| **Feature Request** | 新功能建议 | 代码回滚、订阅会员 |
| **Platform** | OS 兼容性问题 | Windows 路径、Linux IME |
| **Spam / Meta** | 恶意刷屏、机器人提交 | 无意义 Issue、灌水泥 |

### 3. 检查本地仓库

如果项目有本地 clone，从中获取修复证据：

```bash
# 搜含有 Issue 编号的 fix commit
git log --all --oneline --format="%h %s" | grep -iE "fix.*#\d+|close.*#\d+"

# 检查 commit 是否在 master（已发布）
git merge-base --is-ancestor <commit> master

# 检查 commit 在哪个分支
git branch -a --contains <commit>

# 查看 fix commit 的完整信息
git log --all --format="%h %s%n%b" | grep -B1 -iE "fix.*#\d+"
```

### 4. 分支状态判断

区分两个关键分支的修复状态：

| 分支 | 含义 | Issue 状态含义 |
|------|------|---------------|
| **master** | 已发布版本 | 修复可用 |
| **develop** | 待发布开发版 | 修复存在但未上线 |
| **feature branch** | 特定功能分支 | 尚未合入主流程 |

```bash
# 判断 fix 是否在 master 中
git branch -a --contains <hash> | grep -q "master" && echo "✅ 已发布" || echo "⚠️ 未发布"
```

## 分类后的底层分析

建议将 Issue 映射到目标项目的架构层（Harness / Runtime / UI 等），以便：

1. 快速识别**最大不稳定模块**（哪个层 Bug 最多）
2. 判断修复**覆盖了哪些层**（开发重点方向）
3. 评估**真实修复率**（去除批量关闭的水分）

### 修复率计算

```
真实修复率 = 有确认 fix commit 的 Issue 数 / 全部已关闭 Issue 数
```

通常批量关闭场景下，真实修复率在 10%~20% 之间。

## 典型 Pitfalls

### ❌ 把 "closed" 当 "fixed"
GitHub Issue 上 "closed (completed)" 不一定代表有代码修复。很多项目使用批量关闭来应对垃圾 Issue。

### ❌ 只看 master 不看 develop
修复可能已经在 develop 分支但尚未合并到 master。如果不检查 develop，会低估项目的实际修复进展。

### ❌ 把 PR merge 当 Issue fix
Merge commit 的 "#123" 引用的是 PR 号而非 Issue 号。需要看 PR 的描述是否真的引用了待修 Issue。

### ❌ 忽略 "Not planned"
很多 Issue 关闭时带有 "Not planned" 标签，意味着维护者关闭了但明确不打算修复。不应计入修复统计。

## 输出建议

推荐以 **Markdown 表格**呈现在云文档中（如飞书文档），格式：

| Issue | 标题 | 类别 | 修复状态 | 分支 | 关键证据 |
|-------|------|------|---------|------|---------|
| #361 | 上下文丢失 | Context Compiler | ❌ 未修复 | — | 无对应 commit |
| #144 | 工具失败未通知 | Tool Runtime | ✅ 已修复 | develop | a8d63d8 |

---

*本文件是 open-source-project-evaluator 的一种评估子技术，侧重 Issue 健康度分析而非项目横向对比。*
