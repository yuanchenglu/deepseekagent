---
name: source-code-verification
description: 所有对产品的分析和结论，必须基于源码验证，而非揣测。不看源码的分析违背第一性原理。适用于所有产品分析、竞品对比、架构讨论场景。
version: 1.3.0
metadata:
  triggers:
    - "分析.*产品"
    - "对比.*架构"
    - "调研.*机制"
    - "Plan.*分析"
    - "Agent.*分析"
    - "分析技术优劣"
    - "三步走.*clone"
    - "clone.*分析"
    - "下载.*代码.*论文"
    - "开源.*下载"
    - "下载.*论文"
  related_skills:
    - arxiv
    - academic-literature-research
    - agent-architecture-analysis
    - github-access-troubleshoot-china
---

# 源码验证原则 (Source Code Verification)

## 核心原则

**所有对产品的分析和结论，必须基于源码验证。不看源码的分析 = 揣测，违背第一性原理。**

这条原则来自与袁老师的深度对话中的教训：在分析 Plan 架构时，初版文档未经源码验证就写了"正好相反"这样的结论性判断——后来被证明是错误的。而另一个 AI 会话通过逐文件对照 OMO 源码，发现了 Momus 的实际行为（偏批准）与文档描述（严格门禁）完全相反的关键差异。

## 何时必须读源码

| 场景 | 触发条件 |
|------|---------|
| 描述某个产品的功能机制 | 如 "OMO 的 Momus 按 4 个标准验证 Plan" — 必须对照源码确认 |
| 对比两个产品的架构差异 | 如 "CodeWhale 的 Plan 是扁平的" — 必须读过 plan.rs 才能说 |
| 给出改进建议 | 如 "建议 CodeWhale 增加 XXX" — 必须先确认这个功能是否已经存在 |
| 引用产品的设计决策 | 如 "Momus 的核心原则是 APPROVAL BIAS" — 必须从源码中引用，不能从文档推断 |
| 判断一个产品/网站是否开源 | 用户问"这个是开源项目吗" — 必须到 GitHub 上搜，不止做网页搜索 |

## 判断一个产品/网站是否开源

用户问"这个是开源项目吗"时，不要只做网页搜索。**必须到 GitHub 上搜，多角度交叉验证。**

### 标准搜索流程

```text
用户: "这个网站/产品是开源的吗？"
    ↓
Step 1: 网页搜索（快速筛掉明显不开源的）
  web_search("<产品名> open source github")
  web_search("<产品名> 开源 源码")
  如果网页明确说"不开源"或"保留所有权利" → 初步标注
    ↓
Step 2: 直接搜 GitHub（核心步骤）
  web_search("site:github.com <产品名>")
  web_search("site:github.com <域名关键词>")  // 如 aicosmos
  web_search("site:github.com/organizations/<相关组织> <产品名>")
    ↓
Step 3: 搜相关研究组织/公司
  // 如果是学术团队的产品，找到他们在 GitHub 的组织
  // 如清华 CoAI 课题组 → github.com/thu-coai
  // 然后 scan 该组织的全部仓库
  web_search("github.com/orgs/<组织名>/repositories")
  // 检查有没有同名或相关仓库
    ↓
Step 4: 搜学术界论文对应代码
  // 如果产品来自论文，论文通常有开源代码仓库
  web_search("site:github.com <论文关键词>")
    ↓
Step 5: 综合判断
  ✅ 找到源码仓库 → 读 README 确认许可证
  ❌ 所有角度都搜不到 → 谨慎判断"不开源"
  ⚠️ 只有论文代码没有产品代码 → 科研算法开源，产品闭源
```

### 判断标准

| 证据 | 结论 | 示例 |
|------|------|------|
| GitHub 有仓库 + 开源许可证 | ✅ 开源 | MIT/Apache/GPL 等 |
| GitHub 有仓库但无许可证 | ⚠️ 不确定 | 需读 README 确认 |
| 官网底部"保留所有权利" | ❌ 不开源 | 即使免费使用也不开源 |
| 只有论文代码没有产品代码 | ❌ 产品不开源 | 学术团队常见模式（如 thu-coai） |
| 所有角度搜不到任何仓库 | ❌ 大概率不开源 | 商业产品/闭源 |

### 常见陷阱

- ⚠️ **不要混淆同名项目** — NVIDIA Cosmos ≠ 清华 AI Cosmos，搜到的是不同的东西
- ⚠️ **"免费" ≠ "开源"** — 免费使用是商业模式，开源是许可证状态
- ⚠️ **学术团队的产品往往闭源** — 论文和算法可能开源，但产品层（UI/服务/工程化）不开源
- ⚠️ **不要只搜一次就下结论** — 多角度搜索互补，用户反问"你在github上搜下"意味着搜索覆盖不足

## 如何读源码（不爆上下文）

**五步法**：

1. **先读项目自述文档**（README、ARCHITECTURE.md、AGENTS.md）— 了解项目自称做了什么
2. **确认远程版本状态** — 对 git clone 下来的项目，在基于代码结构做任何结论前，先对比远程。**本地仓库可能严重过时**。
   ```bash
   git remote -v                                    # 查看远程仓库地址
   git fetch --dry-run                              # 看远程是否有更新
   git log --oneline HEAD..origin/main | wc -l      # 本地落后多少个提交
   git diff --stat HEAD..origin/main | tail -5      # 差异规模
   ```
   如果远程有大量更新，你的所有分析结论都可能过时。必须先基于远程版本（`git show origin/main:path/to/file`）重新验证，或者拉取最新代码。
3. **用 search_files 定位关键实现** — 对声称的功能，搜索源码中的具体文件名/关键字
4. **只读相关片段**（read_file + offset + limit）— 不要全量读文件，只读相关的 50-200 行
5. **只 clone 关键仓库** — OMO 用 `--depth 1` 浅克隆，ucolorclaw 不读内容

**平衡策略**：

```
分析一个产品功能时的决策树:

  这个功能代码规模多大？
  ├── 单文件 (< 500行) → 可以全读
  ├── 中等规模 (500-2000行) → 读关键部分 (50-200行)
  └── 大型模块 (> 2000行) → 只搜索关键词 + 读匹配片段

  clone 策略:
  ├── 可公开访问的 GitHub → git clone --depth 1
  ├── 本地已有 → 直接用
  └── 超过 100MB 的仓库 → 只通过 GitHub API 浏览，不 clone
```

## 输出规范

在做任何产品分析时，必须标注信息来源：

```
✅ 正确:
  "Momus 的核心原则是 APPROVAL BIAS（源码: src/agents/momus.ts, L45-52）"

❌ 错误:
  "Momus 似乎倾向于批准..."（没有源码引用 = 揣测）

⚠️ 推断（需标注）:
  "Atlas 的 Wisdom 系统在 prompt 中没有显式实现（源码验证: atlas prompt 18KB 中无 Wisdom 分类），
   文档中的描述可能是概念设计而非已实现功能"
```

## 修正文化

当发现之前的分析有误时：
1. 在文档更新记录中明确标注"修正"和原因
2. 保留原始错误痕迹（不删除，标注 ⚠️ 修正）
3. 引用源码中导致修正的具体证据

## 文档组织

分析产出文档应遵循 KV Cache 优化结构：Header(稳定) → 结论正文(相对稳定) → Q&A附录(增长)。详见 `references/document-structure-kv-cache.md`

## 项目尽职调查工作流 (Project Due Diligence)

当用户问"某个开源项目/进程实际是干什么的？有什么意义？"时，不是在问文档写了什么，而是在问**代码里真正做了什么**。

### 标准流程

1. **进程溯源**（如果是正在运行的进程）
   ```bash
   ps aux --sort=-%cpu | head -10          # 找到目标进程 PID
   ps -p <PID> -o pid,cmd --no-headers       # 看完整启动命令
   ```
   从启动命令定位到源文件位置，然后 `read_file` 读代码。

2. **systemd 服务检测**（进程可能由 systemd 管理，只查 ps 不够）
   ```bash
   systemctl list-units --type=service | grep -i <进程名或项目名>
   # 如果找到，查看服务文件确定启动命令和自启策略
   cat /etc/systemd/system/<service-name>.service
   systemctl is-enabled <service-name>
   ```
   这一步同时回答"这个进程会不会开机自启"——systemd services 即使当前停止了，重启后还会回来。

3. **读源码判断实际功能**
   - 如果是一个聊天界面/web UI — 看是否只是套壳调 API，还是有自主逻辑
   - 如果是服务/框架 — 看核心逻辑的复杂度
   - **注意：读到的代码可能严重过时** — 如果是 git clone 的项目，先检查远程版本状态（见下文）

4. **项目级尽调**（用户问"这个项目有什么意义"时执行）
   ```bash
   # 第 1 步：先确认本地代码版本是否最新！
   git remote -v
   git fetch --dry-run
   git log --oneline HEAD..origin/main | wc -l       # 落后提交数
   git diff --stat HEAD..origin/main | tail -5        # 差异规模

   # 如果远程有大量更新，说明本地仓库严重过时。
   # ❌ 不要基于本地版本做结论性判断
   # ✅ 用 git show origin/main:path 基于远程版本分析，或拉取后重做

   # 第 2 步：统计各语言代码行数（排除依赖目录）
   find . -name "*.py" -o -name "*.rs" -o -name "*.go" -o -name "*.ts" \
     -o -name "*.c" -o -name "*.cpp" -o -name "*.h" \
     | grep -v venv | grep -v node_modules | grep -v .git \
     | xargs wc -l | sort -rn

   # 第 3 步：识别空文件 — 声称有实现但实际是空壳的模块
   find . -name "*.py" -o -name "*.rs" -name "*.go" -o -name "*.ts" \
     -o -name "*.c" -o -name "*.cpp" \
     | grep -v venv | grep -v node_modules | grep -v .git \
     | xargs wc -l | grep "0 "

   # 第 4 步：检查 git 活跃度
   git log --oneline -10
   git remote -v

   # 第 5 步：试图编译/构建（如果项目有 Makefile/CMake）
   ls CMakeLists.txt Makefile Cargo.toml package.json 2>/dev/null
   ```

5. **交叉验证 README vs 代码**
   - README 声称的核心功能 → 是否有对应代码文件？
   - README 提到多语言 SDK → 各语言的代码是否真实存在且有内容？
   - README 提到测试 → 测试文件是否为空？
   - README 提到应用层 → 应用目录下是否有代码？

6. **输出规范**
   ```
   ✅ 有代码支撑的功能：
     "C 内核有 13,740 行代码，包含 IPC Binder、内存池、任务调度（coreadd/core/src/task/scheduler.c）"

   ❌ 文档声称但无代码：
     "Rust SDK 声称支持，但 coresdk/rust/src/*.rs 共 0 行代码（空文件）"

   ⚠️ 部分实现：
     "微内核架构有 C 代码支撑（70% 完成度），但系统调用层标记为 60%"
   ```

7. **结论框架**
   ```
   好的方面：[实际有代码、有架构亮点的部分]
   实际的问题：[空壳模块、停更、文档超越实现]
   对你的价值：[要不要留/继续用/关掉]
   ```

8. **行动后验证**（如果用户决定停止/关闭进程或服务）
   ```bash
   # 停止 + 禁用开机自启
   sudo systemctl stop <service-name>.service
   sudo systemctl disable <service-name>.service

   # 验证效果
   top -bn1 | head -4                         # CPU+内存变化
   systemctl status <service-name>.service    # 确认 inactive + disabled
   ```
   在答复中给出"操作前 vs 操作后"的对比数据（CPU、可用内存、Load Average），让用户直观看到收益。

## GitHub Issue 修复状态验证

当用户需要判断一个 GitHub issue 是否**真正在代码中修复**（不只是被关闭），使用以下标准化流程：

### 前提：找到正确的本地仓库

用户可能同时有**多个 clone**（例如 ~/Code/Kun、fangzhouzhongce/第XX期_yanzi/Kun 等）。**总是优先检查日期最新的那个。** 多做一次 `ls -la` 比写错结论好。

```bash
# 寻找所有 clone
find ~/Code -maxdepth 4 -name ".git" -path "*Kun*" -o -name ".git" \
  -path "*ProjectName*" 2>/dev/null

# 比较哪个最新
ls -ld ~/Code/Kun ~/Code/fangzhouzhongce/*/Kun 2>/dev/null
```

### 第 1 步：检查仓库状态

```bash
git remote -v
git log --oneline -3
git branch -a | head -10
```

### 第 2 步：搜索所有 fix 相关 commit

```bash
# 搜索 commit message 中引用 issue 编号的提交
git log --all --oneline --format="%h %s" | grep -iE "#[0-9]+"

# 仅 fix/close/resolve 类
git log --all --oneline --format="%h %s" | grep -iE \
  "(fix|close|resolve).*(#[0-9]+)"

# 包含 commit body 的深度搜索
git log --all --format="%h %s%n%b" | grep -B1 -iE \
  "fix(es|ed)?.*#\d+|close[sd]?.*#\d+"
```

### 第 3 步：验证是否合入 master

```bash
git merge-base --is-ancestor <commit_hash> master \
  && echo "✅ in master" || echo "❌ NOT in master"
```

如果不在 master，查明在哪条分支：
```bash
git branch -a --contains <commit_hash>
```

### 第 4 步：区分 fix 类型与可靠度

| 类型 | 含义 | 可靠度 |
|------|------|--------|
| 直接 commit `fix: #123` | 明确为该 issue 提交的修复 | ✅ 高 |
| Merge PR body `fixes #123` | 通过 PR 修复 | ✅ 高 |
| 大型 refactor 顺带修了 | commit message 不明确 | ⚠️ 需验证 |
| 仅关闭未修复 | "Not planned" 或批量关闭 | ❌ 不可信 |
| 移除有问题的功能 | 不是修复是规避 | ⚠️ 需区分 |

### 第 5 步：整理结论

输出示例：
```text
#123 — 标题名（Harness 层）
✅ 已修复 | <hash> <msg> | master
⚠️ 间接修 | <关联 fix>
❌ 未找到修复 | 搜索关键词
```

### 常见陷阱

- ⚠️ **issue 和 PR 共享编号空间** — `Merge pull request #123` 是 PR，`fix: #123` 才是修 issue
- ⚠️ **多个 clone 的 HEAD 可能不同** — 确认最新的那个
- ⚠️ **develop 的修复 ≠ 用户能拿到** — 未合入 master 就不算发布
- ⚠️ **"移除"不是修复** — 如 `remove MCP recommendation` 是文档级规避
- ⚠️ **批量关闭 ≠ 批量修复** — 需要逐条验证代码

## 变体：新发布开源模型材料收集（Pre-Analysis Workflow）

当用户说"XXX 发布了/开源了，帮我下载代码和论文"时，在执行深入分析之前，先完成系统性的**材料收集**。这个阶段的目标是：把所有可能的分析素材一次收集齐，避免反复返工。

### 触发条件

- 用户说"XXX 刚开源了，帮我下载代码"
- 用户说"下载论文"或"所有论文都下载"
- 用户说"后续要做深度分析/对比"（如与 DeepSeek V4 对比）

### 工作流

#### Phase 1: 发布状态核实

新模型发布时，往往**API、权重、代码、论文不是同时开放的**。先核实：

| 状态 | 含义 | 用户预期 |
|------|------|---------|
| ✅ API 已上线 | 可通过官网/API 调用 | 代码可能还没有开源 |
| ⏳ 权重 / 代码 7月27日开放 | 权重文件未来某天开放 | 模型本身的实现代码可能那时一起出 |
| ✅ 架构代码已开源 | 论文中提到的关键技术已有独立仓库 | 可以 clone 这部分先看 |
| ❌ 技术报告未发布 | 论文/技术报告还没上 arXiv | 需要定期重检查 |

**怎么做：**
```text
1. 搜新闻（VentureBeat / TechCrunch / 36氪）→ 看发布状态
2. 搜官方公告 → 看权重和技术报告的发布日期
3. 直接搜 GitHub/HuggingFace → 看代码是否已放出
4. 对比信息 → 如果多个来源冲突，以官方 GitHub/HF 为准
```

**常见模式：** 模型的 API 和宣传先放出来，权重文件要等 7-14 天，代码有时和权重同时出。这时候能下载的是论文中提到的**架构组件**的独立实现仓库（如 Kimi Delta Attention / FlashKDA）。

#### Phase 2: 查找所有代码仓库

```text
1. 搜索官方 GitHub 组织
   → web_search("site:github.com/<组织名>")
   → 到 org 的 repos 页面看所有仓库
   → 特别留意名字带架构关键字的（如 Linear / Flash / Attention）

2. 搜索 HuggingFace
   → 到 huggingface.co/<组织名>/models 查看所有模型
   → ⚠️ **不要默认 HF 模型仓库 = 只有权重文件！** 很多 LLM 的模型实现代码
     直接放在 HF 仓库的 inference/ 或 modeling_*.py 目录下
     （如 DeepSeek V4 的 inference/model.py + kernel.py 在 HF 而非 GitHub）
   → 先用 GIT_LFS_SKIP_SMUDGE=1 浅克隆验证文件结构
   → 只删除实际的模型权重文件（model-*.safetensors, *.bin 等），保留代码

3. 确定需要 clone 的仓库
   ✅ 架构实现仓库（如 KDA / FlashKDA / Attention 实现）→ clone
   ⚠️ **HuggingFace 模型权重仓库** → 先用代码模式验证是否有源代码
       标准做法：`GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 <HF_URL>`
       然后 `find . -name "*.py" -not -path '*/.git/*'` 看有无 Python 代码
       如果有 inference_*.py / modeling_*.py / kernel.py → 这就是代码仓库
       如果只有 model-*.safetensors → 确实只有权重，删除即可
   ⚠️ 论文/文档仓库（只有 PDF+README）→ 如果后续下载了 arXiv 版就不需要
```

#### Phase 3: 浅克隆代码（仅代码）

```bash
# 标准做法：depth=1 避免历史，只下载当前代码
git clone --depth 1 https://github.com/USER/REPO.git

# 如果在中国网络环境遇到 TLS 握手失败（gnutls_handshake failed）：
GIT_SSL_NO_VERIFY=1 git clone --depth 1 https://github.com/USER/REPO.git
# ⚠️ 公共仓库专用，不用于私有仓库

# HuggingFace 仓库特殊处理（同时包含代码+模型权重）：
# GIT_LFS_SKIP_SMUDGE=1 阻止 LFS 下载大文件（权重文件），只保留指针
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://huggingface.co/USER/MODEL
cd MODEL

# 清理：删除权重文件和 git 历史，只保留代码
rm -f model-*.safetensors model.safetensors.index.json *.bin pytorch_model*.bin
rm -rf .git
```

**为什么 depth=1：**
- 模型代码仓库通常很小（几 MB 到十几 MB）
- 不需要完整的 git 历史
- 避免无意中触发大文件下载（有些仓库在 git 历史中不慎提交过模型文件）

#### Phase 4: 找到该实验室的全部论文

不局限于本次发布的模型的论文。用户说"所有论文"时，是**该实验室的全部研究论文**。

**查找途径：**

| 途径 | 方法 |
|------|------|
| arXiv 搜索 | `site:arxiv.org <实验室名/团队名>` |
| 官方博客 | 实验室官网的 Research/Blog 页面 |
| GitHub 仓库 | 每个仓库的 README 通常会引用论文 |
| 交叉验证 | 论文之间的互相引用 |

**典型产出清单的维度：**
```text
按技术领域分类：
├── 🔑 本次模型核心技术
│   ├── 注意力机制创新（如 KDA / Linear Attention）
│   ├── 架构创新（如 Attention Residuals）
│   └── 高性能实现（如 CUDA Kernels）
├── 📐 模型架构（之前的系列模型）
│   ├── 前代模型（如 K2 / K2.5）
│   └── 基础组件（如 MoBA / VL）
├── 🎯 训练与优化
│   ├── 优化器（如 Muon）
│   ├── RL 训练方法（如 K1.5）
│   └── 训练系统（如 Seer）
└── 🔧 系统工程
    ├── 推理架构（如 Mooncake）
    └── 专项能力（如 Audio / Prover）
```

#### Phase 5: 批量下载论文 PDF

从 arXiv 下载已知 ID 的论文：

```bash
mkdir -p papers && cd papers

# 批量下载模式
for id in 2510.26692 2603.15031 2507.20534; do
  curl -sL -o "paper-name-$id.pdf" "https://arxiv.org/pdf/$id"
done
```

**去重检查：** 有些论文已存在于 clone 的仓库中（如 `tech_report.pdf`），跳过重复下载。

#### Phase 6: 输出交付报告

报告要让用户一目了然地知道：

1. **目录结构** — 代码放哪里，论文放哪里
2. **当前状态** — 哪些已下载，哪些还没发布（如 K3 技术报告 7月27日）
3. **后续计划** — 哪些需要未来再检查
4. **分析入口** — 如果要开始分析，推荐从哪个文件/论文开始

#### Phase 7: 后续重检查（如适用）

如果某些材料尚未发布（如技术报告、模型代码），在交付时**同时设定期望**：这是一个分批交付，不是一次性搞定。

### 常见陷阱

1. ⚠️ **API 已上线 ≠ 代码已开源** — 很多模型先发 API，代码几周后才释放
2. ⚠️ **模型权重仓库 ≠ 代码仓库** — HuggingFace 上的模型仓库通常几十 GB，只含权重文件，不是代码
3. ⚠️ **一个模型系列可能有十几个仓库** — 全部找齐需要多次搜索
4. ⚠️ **论文和技术报告可能分散在不同平台** — arXiv、GitHub、官方 blog、学术会议网站
5. ⚠️ **技术报告可能需要多次重检查** — 有些论文在模型发布时还没上 arXiv，需要后续跟踪
6. ⚠️ **GitHub 在中国可能 TLS 握手失败** — 用 `GIT_SSL_NO_VERIFY=1` 解决（仅限公共仓库）
7. ⚠️ **多模型批量下载时注意区分代码来源** — 不同模型的代码分布模式不同：
   - Kimi 系：代码在 GitHub 独立仓库（FlashKDA / Kimi-Linear / Kimi-K2）
   - DeepSeek V4：代码在 HuggingFace（inference/*.py，非 GitHub）
   - GLM-5 / Qwen3.6：代码不在独立仓库，集成在 vLLM/Transformers
   - **不要因为 GitHub 上没有就断言\"没有代码\"** — 先检查 HuggingFace

### 与后续分析的衔接

材料收集完毕后，进入正常分析流程：
1. 加载本 skill（source-code-verification）进行代码分析
2. 如需架构对比（如 KDA vs DeepSeek V4 Attention），用 `agent-architecture-analysis` skill
3. 逐篇阅读论文时，用 `academic-literature-research` skill 的 paper-reading 方法

---

## 禁止事项

- ❌ 从 README 直接推断实现细节
- ❌ 从概念文档推断代码行为
- ❌ 用"似乎"、"可能"、"应该"替代源码验证
- ❌ 全量读大型代码库（会爆上下文）
- ❌ 对同一个产品重复做全量分析（用增量 + 已有文档）
- ❌ **假设本地 clone 就是项目最新状态** — 优先检查 fangzhouzhongce/ 中有无更新 clone
- ❌ **找到第一个 clone 就下结论** — 用户可能有多个 clone，选日期最新的
- ❌ 基于过时版本得出消极结论
- ❌ **只搜一次就下结论** — 验证模块是否接入时，需要搜类名 + 文件名 + 函数名 + barrel export 链 + 核心编排器变更检查，五种模式互补。用户反问"你确定吗？"往往意味着搜索覆盖不足

## 变体：本地 Patch 集成验证（Integration Patch Audit）

当用户给出一组**本地分支上的 commit（整合包）**，声称修复了多个 GitHub Issue 时，需要使用专门的验证流程。核心问题是：**新模块是否被接入到运行链路中？** 代码写得再好，不被调用就等于没修。

详见 `references/github-issue-fix-verification.md` 的"变体：本地 Patch 集成验证"章节。其中包含了完整的三问法（改了什么 → 接入检查 → commit 自述对照）、综合判断矩阵，以及核心编排器变更检查。完整的审计案例参见 `references/integration-patch-audit-case-study.md`。

## 变体：参考实现分析（Reference Implementation Analysis）

当分析某个开源项目的目的是**验证一个技术想法、提取经验参数、指导自己的方案设计**（而不是二开选型或项目尽调）时，使用以下增量步骤：

1. **先读自述文档**（README）— 了解他们自称做了什么
2. **定位核心算法** — 用 `search_files` 找到检测/判断逻辑的具体文件和行号
3. **提取经验参数** — 他们在代码中 hardcode 的阈值、窗口大小、去重间隔等，这些都是用真实数据调出来的，可以直接继承或作为基准
4. **提取踩坑记录** — README 中的问题描述（如 EMI 干扰、校准困难）是免费的技术顾问
5. **识别缺失能力** — 他们没有做的、做不了的，就是你的差异化空间
6. **输出对比矩阵** — 他们的方案 vs 你的方案，标注每个关键参数的来源（源码行号）

**与项目尽调的区别**：
- 尽调：回答"这个项目有没有价值、能不能用"
- 参考实现分析：回答"这个项目验证了哪些假设、踩了哪些坑、我该怎么改"

**案例**：`business/hardware-product-feasibility-analysis/references/mosquito-swatter-case-study.md` — MosquitoKiller 源码分析 → 提取 700ms 去重窗口、50% 跌落阈值、EMI 屏蔽教训

## 模型特定优化分析

当用户问"某个 Agent 产品对特定 LLM 做了哪些独特优化"时，使用专门的 6 层分析清单。详见 `references/llm-agent-optimization-checklist.md`

## 变体：LLM 物理特性兼容性分析

当用户问"某个 Agent 平台能否发挥特定 LLM 的物理特性"时（如 MLA、MoE 稀疏激活、1M Context、reasoning_effort），使用另一套分析框架。详见 `references/llm-physical-characteristic-compatibility.md`

**与模型特定优化分析的区别**：
- 优化分析：平台视角 → 平台为模型做了什么
- 兼容性分析：模型视角 → 平台架构能否发挥模型的独特物理特性
- 兼容性分析的关键产出是**抽象层不匹配分析**— 追问特性影响的抽象层 vs 平台感知的抽象层是否一致

## 参考案例

- `references/agentos-due-diligence.md` — AgentOS 项目尽调：展示了从过时本地版本（v1.0.0.3, ~14K 行）到远程最新版（v0.1.0, ~438K 行）的分析差距，以及不检查远程就下结论的教训
- `references/momus-case-study.md` — Momus 审查机制：从概念文档推断代码行为，导致对审查机制的描述完全相反
- `references/omo-plan-cascade-defect.md` — OMO Plan 级联缺陷：验证 Plan 是扁平 checklist 而非依赖图，导致中途需求变更时无法级联修正。附带揭示了 Prompt 指令被遗忘的深层问题（→ I-13 Prompt→Skill 自结晶）
- `references/integration-patch-audit-case-study.md` — KunAgent 5-Patch 集成审计：展示了"写了但没接"的经典模式，以及用户反问"你确定吗？"后扩展搜索范围发现更多证据的教训
