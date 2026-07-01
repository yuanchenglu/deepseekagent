## 任务：DeepAgent Release 安装系统 — 详细实施规划

### 角色

你是 DeepAgent 项目的**技术规划者（Planner）**。你的任务是基于已确认的 PRD 文档，产出完整、可执行的实施计划。

### 输入文档

请先阅读以下文件：
- `~/Code/DeepAgent/docs/specs/05-Release-Installation.md` — 完整的 PRD（已确认）

部署凭证在 `~/.deepagent/.env`（末尾 CF_ 和 R2_ 开头）。

### 你需要产出的内容

请输出一份完整的实施计划，包含以下 10 个部分：

#### 1. 整体架构方案
- Pages + R2 混合方案的选择理由（为什么要这样，不是纯 Pages 也不是纯 R2）
- 域名 `deepseekagent.starseas.org` 的路由设计（/ → landing, /docs/* → docs, /install.sh → redirect to R2）
- CLI 和 Desktop 共用后端的设计图

#### 2. install.sh 设计方案
- 完整流程：依赖检测 → 双源下载 → sha256 校验（checksum 从 GitHub、tarball 从 R2，不同信任域） → 解压 → uv sync → skills_sync → .env 保留 → PATH 配置 → 自动下载 DMG（install.sh 最后一步，非独立命令）→ 完成提示
- 注意：不包含 electron-builder 或 npm build
- 注意：Node.js 仅警告不自动安装
- 注意：DMG 下载失败时跳过，不影响安装结果
- 双源降级的发布顺序：先上 GitHub Releases → 确认后上 R2

#### 3. Release 包结构
- tarball 包含：deepagent/（Python 包 + embedded/opencode/ 预编译二进制 + skills/ + tools/）、webui/（预构建 dist/ + 源码 + electron/）、VERSION
- sha256 校验和文件

#### 4. Desktop 客户端方案
- Electron Desktop 在 CI 中预构建 DMG
- install.sh 不构建 Desktop，只自动下载已构建好的 DMG
- macOS DMG → 自动挂载 → 用户可拖到 Applications（或关掉）
- CLI 和 Desktop 共用 `~/.deepagent/` 后端
- 首次启动 Desktop 时检测后端是否已存在，不存在则静默执行 install.sh（无需 sudo，写用户目录）

#### 5. 落地页设计方案
- 静态 HTML（深色主题，对标 DeepSeek 官方风格）
- 一键复制安装命令
- 可选 DMG 下载链接
- 介绍：为 DeepSeek 定制、AI Native、内置虚拟研发团队、基于 Hermes+OpenCode 二次开发
- 放在 `website/landing/` 同一 repo

#### 6. 域名配置策略
- 先用 Pages 临时域名 `*.pages.dev` 全量验证，再绑自定义域名
- 备选回退方案（Plan B/C）
- 先评估当前 DNS 状态，不要直接操作

#### 7. 任务拆解
- 按 Phase 1-7 拆解到具体子任务
- 每个子任务标注：输入依赖、输出产物、验收方法、预估耗时

#### 8. 测试与验收方案（重点）
- 验收脚本 install-verify.sh（3 Phase：Release 包验证 → 模拟安装 → 实际安装）
- 测试环境：本机 + CI runner + 虚拟机 + 干净 VM + 国内网络
- 覆盖：全新安装、更新安装、回滚、配置保留、双源降级、Desktop 共享后端
- **必须包含功能测试，不能只有接口测试**
- 每一阶段提交后有可执行的验证命令

#### 9. 风险评估
- 域名配置（已知坑，另一个 Agent 20 分钟未解决）
- 双源版本一致性
- skills_sync 用户修改判定
- 回滚状态一致性
- 每个风险附缓解措施

#### 10. 需要确认的决策点
- 列出尚不确定、需要用户最终拍板的点

### 输出格式

用 Markdown 输出，存为 `.omo/plans/release-installation-plan.md`。
要足够详细，让一个弱一些的 AI 也能按照此计划执行。

### 约束

- 不要修改任何代码或配置，只出计划
- 聚焦可执行性，不要空泛的理论分析
- 不确定的地方标注 [TODO: 需要确认] 而不是跳过
