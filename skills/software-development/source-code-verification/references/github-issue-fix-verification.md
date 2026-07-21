# GitHub Issue 修复状态验证工作流

> 本文件记录 KunAgent/Kun 仓库全部 205 个已关闭 Issue 的修复状态验证过程。方法可复用于任何 GitHub 仓库。

## 背景

用户指出 KunAgent/Kun 的 205 个 Issue 是恶意刷屏后被批量关闭的，并非真实修复。需要逐条验证哪些真正合入了代码。

## 执行步骤

### 1. 获取全部 Issue 内容

GitHub Issues 的 Web 页面有 9 页（每页 ~25 条，共 205 条）：

```bash
# 通过 web_extract 逐页抓取
web_extract(urls=[
  "https://github.com/KunAgent/Kun/issues?q=is%3Aissue+state%3Aclosed&page=1",
  ...
  "https://github.com/KunAgent/Kun/issues?q=is%3Aissue+state%3Aclosed&page=9"
])
```

### 2. 分类整理（9 大类别）

| 类别 | 数量 | 说明 |
|------|------|------|
| Agent 执行异常 | ~35 | Agent 卡死、中断、静默失败 |
| 功能请求 | ~35 | 新功能建议，大部分被拒 |
| GUI/UI 显示 | ~20 | 渲染、布局、图标问题 |
| 连接与网络 | ~18 | 后端连接、SSE、手机绑定 |
| 模型与提供商 | ~15 | API 兼容性、模型配置 |
| MCP/插件/Skill | ~10 | 工具注册、Skill 加载 |
| 文件系统与编辑器 | ~8 | 路径解析、Git 检测 |
| 平台兼容性 | ~6 | Windows/Linux 特定问题 |
| 非技术/恶意刷屏 | ~8 | 纯吐槽或无内容 |

### 3. 筛选底层 Harness 问题

基于 Agent = Model × Harness × Environment × Evidence 理论：

**Harness 子系统定义：**

| 子系统 | 识别信号 | 典型问题 |
|--------|---------|---------|
| Context Compiler | 上下文丢失/压缩/泄漏、byte-stable prefix | #361 #247 #155 |
| Tool Runtime | 工具注册/执行/生命周期、MCP 集成 | #331 #342 #341 |
| Safety Layer | 权限/沙箱/workspace 约束 | #270 #17 |
| Provider Layer | API 协议兼容/Streaming/路由 | #303 #237 #450 |
| Orchestrator | Turn 生命周期、Goal 状态机 | #370 #357 #178 |
| Evidence & Monitoring | 可观测/度量/持久化 | #405 #404 #214 |

### 4. 验证修复状态（关键步骤）

核心命令序列：

```bash
# Step A: 找最新 clone（重要！）
find ~/Code -maxdepth 4 -name ".git" -path "*Kun*" 2>/dev/null
ls -ld ~/Code/Kun ~/Code/fangzhouzhongce/*/Kun 2>/dev/null | sort -k6

# Step B: 进入最新 clone，搜 fix commit
cd <latest_clone>
git log --all --format="%h %s" | grep -iE "(fix|close|resolve).*(#[0-9]+)"

# Step C: 验证是否在 master
git merge-base --is-ancestor <hash> master && echo "✅" || echo "❌"

# Step D: 不在 master 则查所在分支
git branch -a --contains <hash>
```

**关键发现（KunAgent/Kun 案例）：**

- ~/Code/Kun 的 master 比 fangzhouzhongce/第30期_yanzi/Kun 落后大量 commit。先检查了旧 clone，得出"大部分未修"的错误结论。
- 切换到最新 clone（HEAD at 8602476）后发现：实际底层修复率 ~63%（27/43），而非之前估算的极低比例。
- 仍有 ~12 个底层 Bug 在最新 master 中无对应修复代码。

### 5. 输出格式

```text
=== 模块统计 ===
Context Compiler: 3/7 ✅ | 1 ⚠️ | 3 ❌
Tool Runtime: 7/11 ✅ | 2 ⚠️ | 2 ❌
...

=== 未修复列表 ===
#247 - 上下文理解异常 — Context 核心
#281 - 思考强度未传到后端 — Provider 协议
...
```

## 常见陷阱

- **issue 和 PR 共享编号空间** — `Merge pull request #123` ≠ 修复 #123
- **同一仓库多个 clone 可能不同步** — 找日期最新的
- **develop 分支有 fix ≠ 已发布** — 必须合入 master 才算
- **"移除"型 fix** 如 `remove MCP recommendation` 不是真修复
- **批量关闭 ≠ 批量修复** — 恶意刷屏后管理员可能一键关

---

## 变体：本地 Patch 集成验证（Integration Patch Audit）

当验证的**不是已合入的 GitHub commit**，而是一组**本地分支上的 patch（整合包）**，声称修复了多个 Issue 时，使用以下专门流程：

### 适用场景

- 用户给了一个整合包/代码目录，有多个 commit 声称修复了不同 Issue
- 代码在本地分支上，尚未 push 到远程/提 PR
- 需要判断"这些代码是否真的解决了 Issue 描述的问题"

### 执行步骤

#### 第 1 步：检查仓库状态（确认基线）

```bash
cd <integration_package>
git log --oneline -20          # 看所有最近提交
git remote -v                  # 确认上游仓库
git branch -a                  # 查看分支结构
git log origin/master..HEAD --oneline  # 未推送的 commit
```

#### 第 2 步：逐 Patch 分析 — 三问法

对每个声称修复 Issue 的 commit，执行以下三问：

**第一问：这个 commit 改了哪些文件？（看 diff stat）**

```bash
git diff <commit>^..<commit> --stat
```

判断标准：修改的文件数、新增/修改行数。如果 commit 只新增了独立模块但没改现有调用点，就是潜在风险信号。

**第二问：新代码是否被接入到运行链路中？（关键！）**

这是本验证流的核心步骤，也是最容易出错的步骤。**不要只搜一次就下结论**——搜索模式的选择直接影响结果。

**标准 grep 命令（用类名/导出名搜索）：**

```bash
# 搜索新模块的导出类/函数名（不是文件名，因为 import 引用的是类名/函数名）
grep -rn "ModuleName\\|ClassName\\|ExportedFunction" --include="*.ts" --include="*.js" \
  --include="*.tsx" . | grep -v node_modules | grep -v ".git/"
```

**关键排除规则：**
- ❌ 排除测试文件本身（`| grep -v ".test."` 或 `| grep -v "__tests__"`）
- ❌ 排除模块自身所在目录（`| grep -v "module-name/"`）
- ❌ 排除 node_modules 和 .git
- ✅ **结果必须包含模块所在目录之外的引用**才算接入

**辅助检查 1 — 核心编排器是否被修改：**

```bash
# 如果 patch 声称修复了运行时行为，检查核心编排器文件是否变更
for sha in $(git log origin/master..HEAD --oneline | cut -d' ' -f1); do
  echo "$sha: $(git diff ${sha}^..${sha} -- <orchestrator>.ts | wc -l) lines changed"
done

# 如果核心编排器（如 agent-loop.ts）0 行变更，新模块肯定没被接入
```

**辅助检查 2 — 桶导出文件（barrel export）是否包含新模块：**

```bash
# 查看模块所在目录的 index.ts，确认它是否被导出
cat <directory>/index.ts

# 查看上一级 barrel export，确认是否引用了该目录
cat <parent>/index.ts

# 如果 barrel export 链不完整，新模块就不会被任何外部代码发现
```

**辅助检查 3 — 用文件名搜索二次确认：**

```bash
# 有时候 import 用的是文件路径而非类名（尤其是动态加载）
grep -rn "new-module-file\|module-dir-name" --include="*.ts" --include="*.js" \
  --include="*.tsx" . | grep -v node_modules | grep -v ".git/" \
  | grep -v "module-dir-name/" | grep -v ".test."
```

**核心规则：** 如果新模块只被测试文件和自身文件引用，则**没有接入运行链路**，等于没修。

**常见陷阱（来自真实案例）：**

- ⚠️ **只搜一次文件名就下结论** — 用户说"你确定吗？"才发现搜索模式不够全，需要搜类名+文件名+函数名三种模式
- ⚠️ **只看 diff stat 就判断** — 1897 行新增看起来像大修复，但实际全没接入；6 行常量修改才是真修好
- ⚠️ **忘记检查核心编排器** — agent-loop.ts 是 agent 的中央枢纽，它 0 行变更意味着所有声称修复运行时行为的模块都不可信
- ⚠️ **忽略 barrel export 链** — 模块可以自成一目录、有 index.ts 导出，但如果父级 index.ts 没有 re-export，它就是个孤岛

**第三问：commit message 是否有"未接入"的自我声明？**

很多开发者会在 commit body 中诚实标注 tech debt：

```text
Tech debt: ComplexityEstimator is not yet wired into auto-model-router.ts
```

如果看到这类声明，直接判定为 ❌ 未修。不能因为"代码写了"就认为"问题修了"。

#### 第 3 步：对照 Issue 描述做精确匹配

将 Issue 的期望行为和代码的实际行为做对照：

```text
Issue 要求: "前端 /v1/tools 应该返回200，而不是404"
代码做了什么: 创建了 RouteRegistry 前端路由表，但前端仍然硬编码 /v1/tools
结论: ❌ 未修 — 路由表存在但无人使用
```

#### 第 4 步：综合判断矩阵

| 代码状态 | 含义 | 结论 |
|---------|------|------|
| 改现有文件 + 接入了 | 真实修复 | ✅ 已修 |
| 新模块 + 被引用 | 扩展功能 | ✅ 已修（需验证引用点正确） |
| 新模块 + 仅自引用 | 写了但没接 | ❌ 未修 |
| 新模块 + commit 自述"未接入" | 诚实的未完成 | ❌ 未修 |
| 改常量（如 depth 6→10） | 简单调参 | 🟡 部分修 |
| 仅关闭 Issue 但无对应代码 | 假修复 | ❌ 未修 |

#### 第 5 步：输出格式

```text
=== Patch 审计结果 ===

Patch 1: <commit title>
  声称修复: #68、#168
  改了什么: 3个新文件 (936行新增)
  接入检查: McpConnectionManager 被 McpRuntimeManager 引用 → ✅
  Issue 匹配: #68 状态可观测性已覆盖, #168 的 npx PATH 问题未处理
  结论: 🟡 部分修（#168 核心原因未触达）

Patch 2: <commit title>
  声称修复: #237、#281、#299
  改了什么: 4个新文件 + 3个现有文件 (485行新增)
  接入检查: RouteRegistry 无任何引用 → ❌
  commit 自述: "Stream timeout tracker is not yet integrated"
  结论: ❌ 三个都没修 — 全写了模块但全没接入

...

=== 汇总 ===
#68: ✅ 修了
#237: ❌ 没接入
#299: ❌ 自述未接入
#340: 🟡 改常量
...
```

### 关键区分：独立模块 vs 集成修复

这是最常见的误判来源：

- **独立模块**：新增一个 .ts 文件，有完整的类、测试、导出。看起来像"修了"，但如果没有任何调用链引用它，它就是个孤岛代码。
- **集成修复**：修改现有文件中的 1-2 行代码（如把硬编码路径改成变量引用），虽然改动量小，但真正修复了问题。

**不要被代码行数欺骗。** 517 行的 fact-anchor.ts 比 6 行的常量修改更容易让人误以为"修了"。

### 案例：KunAgent 5-Patch 审计

参考 `references/kunagent-5patch-audit-20260624.md`（如果存在），展示了 5 个 Patch、15 个声称修复的 Issue 中，只有改常量和部分全局 skill 加载是真正修好的，其余全部"写了但没接入"。
