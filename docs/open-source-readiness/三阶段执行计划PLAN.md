# DeepAgent 三阶段产品与开源发布计划

> **版本**：v2.7.0  
> **最后更新**：2026-07-28  
> **唯一事实源**：GitHub 远程仓库 `yuanchenglu/deepseekagent`  
> **开发分支**：`develop`  
> **发布分支**：`master`  
> **当前结论**：项目主体工程约九成完成，已进入发布收敛阶段；CLI Alpha、WebUI Beta、Electron Preview 当前均为 **No-Go**。

---

## 1. 目标、范围与事实层级

项目按三个阶段交付：

1. **CLI Alpha**：公开仓库、可安装、可运行真实 Agent 任务。
2. **WebUI Beta**：本地无感认证、稳定生命周期和浏览器界面。
3. **Electron Preview**：DeepAgent + DeepCode 双模式 Apple Silicon 客户端。

阶段契约：

- `07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`
- `08-PHASE-2-WEBUI-STABLE-BETA.md`
- `09-PHASE-3-DUAL-MODE-ELECTRON.md`
- `10-ELECTRON-PREVIEW-STATUS.md`
- `11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md`

事实状态与交接：

- `00-THREE-PHASE-DELIVERY-STATUS.md`
- `HANDOFF_2026-07-28.md`

事实优先级：

```text
最新远程代码、PR、CI、review
→ 本 PLAN
→ 00 状态与 10 Electron 专项状态
→ 07/08/09 阶段契约
→ docs/HANDOFF-DEVELOPER.md（仅历史资料）
```

许可口径固定为：

> DeepAgent Core 使用 MIT，是开源软件；WebUI/Desktop 使用 BSL-1.1，是源码可见软件。README、官网和发布说明不得把整个仓库描述为 MIT。

---

## 2. 当前远程基线

截至 v2.7.0，以下关键 PR 已合入 `develop`：

| PR | 关键产出 |
|---|---|
| #1 | 三阶段主体实现、CLI/WebUI/Electron 基础 |
| #3 | 无签名 Electron Preview 打包收尾 |
| #4–#6 | Browser E2E、认证安全场景、DMG/i18n/品牌/安全门禁 |
| #10 | Workspace Lock Renderer 所有权隔离和销毁自动回收 |
| #12 | 三阶段计划 v2.4.0 与远程优先交接 |
| #13 | PR 验证可取消、正式发布不可取消、发布事务串行排队 |
| #14 | 三阶段计划 v2.5.0，将优先级切换到 Runtime Lease 协议 |
| #15 | Main 权威 Runtime Task / Workspace Lease 协议、状态机与契约测试 |
| #16 | 三阶段计划 v2.6.0，将优先级切换到真实 task/PID 生命周期 |
| #17 | Electron Main 监督器、DeepAgent/DeepCode 真实 task/PID 生命周期、持久化恢复与跨平台进程证据 |

本次更新远程快照：

- PR #17 最终 Head：`aba94fab7b36f9bd140752c455acdd4838bd3835`
- PR #17 squash merge：`e0f2f407daa6f273ee4c927934efc2e3b27293a0`
- `master` 在本工作单元中未更新；发布分支仍不得提前接收 Preview 代码。

PR #17 最终 Head 已真实通过：

- WebUI Chromium Browser E2E。
- Electron Preview concurrency contract。
- 全 Git refs Secret 扫描。
- WebUI 全量测试、共享构建和 NPM 许可证审计。
- Electron Main Vitest 与 TypeScript Main 构建。
- Runtime 复用与无签名 Preview 目标约束。
- 无签名 Apple Silicon DMG 构建。
- Bundle ID、版本、arm64、安装器、Manifest、SHA-256 和 artifact 验证。

Electron workflow 首轮出现一个与本工作单元无关的 MCU TTS 异步断言抖动；同一最终 Head 的失败 Job 重跑后全链路成功。Publish Job 在 PR 场景按预期跳过；没有创建 Tag、Release 或公开 Preview channel。

新会话必须重新读取远程最新 Head、开放 PR、Actions 和 review，不得把上述 SHA 当作永久基线。

---

## 3. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前判断 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90% | **No-Go** | Browser E2E 与核心自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 94% | **No-Go** | Runtime 协议及真实 task/PID 生命周期完成；双 Runtime 真实并发、干净机、共存和外测未关闭 |

**整体判断**：不继续扩张功能。当前只关闭真实并发、故障恢复、凭据、迁移、共存、干净机和用户验收门禁。

---

# 第一阶段：CLI Alpha

## 4. 阶段目标

面向命令行早期用户，交付只支持 macOS Apple Silicon 的 CLI Alpha：

```bash
deepagent --version
deepagent setup
deepagent doctor
deepagent
deepagent update
deepagent uninstall
```

安装入口：

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
```

第一阶段制品只包含允许分发的 Core 和必要依赖，不包含 BSL WebUI/Desktop 或 OpenCode 制品。

## 5. 已完成

- `DEEPAGENT_HOME` 与 `~/.deepagent` 产品目录隔离。
- 不读取、覆盖或删除 Hermes/OpenCode 用户目录。
- `~/.local/bin/deepagent` 为唯一全局命令。
- Manifest、SHA-256、渠道指针和版本一致性检查。
- 版本目录、原子切换、失败回滚和清单驱动卸载主体。
- realpath 边界校验和未知文件保护。
- Core-only Apple Silicon 制品构建路径。
- 开源治理、许可矩阵、安全政策和第三方依赖声明。
- 官网与安装文档的 DeepAgent 入口收敛。

## 6. 发布阻断项

1. 轮换所有曾进入代码、配置、日志或 Git 历史的对象存储、发布和服务凭据。
2. 确认旧凭据失效后，清理 Git 历史中的有效秘密。
3. 对全部 Git refs 重扫，达到零有效秘密。
4. 在干净 Apple Silicon Mac 验证首次安装、覆盖、升级、故意失败升级、自动/显式回滚和两种卸载。
5. 验证 DeepAgent 对 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期影响。
6. 使用至少一个正式支持模型完成真实 Agent 任务。
7. 清零发布范围内 P0/P1。

**阶段出口**：以上条件全部满足后，才能发布 CLI Alpha 并更新 Alpha 渠道指针。

---

# 第二阶段：WebUI Beta

## 7. 阶段目标

面向普通用户提供本地优先的 DeepAgent WebUI：

```bash
deepagent webui start
deepagent webui open
deepagent webui status
deepagent webui stop
```

默认只监听 `127.0.0.1`。本地启动采用一次性 Ticket 换取 HttpOnly Session Cookie，不使用固定默认密码。LAN/公网不属于首版 Beta 承诺。

## 8. 已完成

- 一次性 Ticket、非法/失效 Ticket、重放防护和 URL 清理。
- HttpOnly Session Cookie 和浏览器 Secret 边界。
- Browser E2E 在 GitHub Actions 中真实通过。
- WebUI 单元测试、构建、静态 i18n 和 NPM 许可证审计门禁。
- `deepagent webui start/open/status/stop` 生命周期主体。
- 默认 loopback、独立 PID/日志/端口和数据目录。
- WebUI 与 CLI 共用 DeepAgent Runtime 主路径。
- Hermes → DeepAgent 面向用户品牌契约收敛。
- 无固定默认密码、无默认 LAN 监听。

## 9. 发布阻断项

1. Alpha → Beta 数据升级、迁移失败回滚和干净机完整生命周期。
2. CLI、WebUI、Hermes、用户 OpenCode 的真实共存矩阵。
3. 正式 Beta 官网构建、发布制品和渠道验证。
4. 至少一个外部测试周期。
5. 清零 Beta 范围 P0/P1。

**阶段出口**：迁移、共存、渠道和真实用户门禁全部通过后发布 WebUI Beta；完成一个完整外测周期后再评估 Stable。

---

# 第三阶段：Electron Preview

## 10. 阶段目标

交付 Apple Silicon Electron 客户端：默认进入 DeepAgent，左上角无重启切换 DeepCode。两个模式共享当前项目与公共设置，但会话、任务、布局和 Runtime 状态相互隔离。

当前 Preview 明确采用**无签名、未公证 DMG**；不得描述为已签名、公证或 Stable。

## 11. 已完成

### 11.1 双模式、安全与 Renderer 边界

- DeepAgent / DeepCode 双模式架构与模式切换。
- Main Process 负责窗口、进程、更新、Keychain、权限和系统能力。
- DeepAgent Runtime 与 DeepCode Runtime 独立进程、状态目录和 IPC 命名空间。
- DeepCode 使用项目内置 OpenCode，不调用用户全局版本。
- Renderer 不持有根 Secret，子进程使用环境变量白名单。
- Desktop 命令为 `deepagent-desktop`，不覆盖 CLI 的 `deepagent`。
- 标准多读单写 Workspace Lock。
- `webContents.id + taskId` Renderer 所有权隔离和 Renderer 销毁自动回收。

### 11.2 自动构建与发布事务

- PR 自动执行 Browser E2E、全 refs Secret 扫描、WebUI/许可证/Electron Main 和无签名 DMG 全链路。
- 正式发布只允许 `workflow_dispatch + X.Y.Z-preview.N + publish=true`。
- PR 验证与正式发布使用不同 concurrency group。
- 正式发布运行不可被后续运行取消。
- GitHub prerelease 与 R2 Preview channel 发布事务使用固定 group 串行排队。

### 11.3 Runtime Task / Workspace Lease 协议

PR #15 已完成：

- Main 权威类型、状态机和多读单写不变量。
- Runtime、规范化 Workspace、taskId、显式 `read` / `write` 和可选进程身份。
- acquire、heartbeat、release、cancel Runtime Adapter。
- Main-only bind-process、timeout、process-exit、runtime-crash、recover。
- `(runtime, eventId)` 幂等和默认 4,096 条有界重放缓存。
- orphaned 失败关闭和明确恢复证据。

### 11.4 真实 Runtime task/PID 生命周期

PR #17 已完成：

1. Electron Main 运行单一持久化 Runtime Task Supervisor。
2. 本地 Unix Socket / Windows Named Pipe 使用 Bearer Token 认证。
3. Supervisor 状态、Token 与 Socket 身份跟随 `webUiHome()` 隔离。
4. DeepAgent 任务按稳定 session taskId 接入，共享并验证 Agent Bridge PID。
5. DeepCode 每个真实回合在 spawn 前 acquire，spawn 后绑定独立子进程 PID。
6. POSIX 使用进程启动时间和命令生成 PID 指纹；Windows 使用 PowerShell/CIM 创建时间、可执行文件和命令行生成指纹。
7. Runtime heartbeat、进程退出、取消、Runtime crash 和 Main restart 驱动权威状态机。
8. heartbeat 丢失时，同一 Runtime 的全部 active 任务统一进入 orphaned 并继续持锁。
9. Main 重启后只恢复 PID 指纹仍匹配的任务，并要求 Runtime 显式 resume；无法证明安全时失败关闭。
10. DeepAgent 可复用 task 保留 generation；DeepCode 一次性 task 不累积持久历史。
11. Supervisor 凭据不会继续传递给 Agent、npm、Tool 或 Bridge 子进程。
12. 每次 Supervisor RPC 使用独立连接，Main 响应显式关闭连接，避免 Main 重启后 stale Unix socket `EPIPE`。
13. 非 Desktop / 未配置 Supervisor 的 WebUI 保持原有 no-op 兼容；Desktop Supervisor 缺失、PID 或 Workspace 无法验证时失败关闭。

> 真实 task/PID 生命周期完成，不等于双 Runtime 在同一真实 Workspace 的并发与故障 E2E 已完成。

---

## 12. 当前唯一第一优先工程任务

### 12.1 双 Runtime 同 Workspace 并发与故障 E2E

必须在真实 Electron Preview 环境中验证：

1. DeepAgent reader + DeepCode reader 可以并行。
2. reader + writer 双向互斥。
3. writer + writer 严格互斥。
4. acquire 被拒绝时，目标 Runtime 不得 spawn 写任务进程。
5. 正常完成后租约释放，后续任务可获取。
6. 用户取消确认后租约释放；取消状态不确定时继续失败关闭。
7. heartbeat timeout 后不产生双写窗口。
8. DeepAgent Bridge 或 DeepCode 子进程崩溃后，相关 Runtime 租约进入正确终态或 orphaned。
9. 一个 Runtime 崩溃不错误释放另一个 Runtime 的有效租约。
10. Main 重启后，PID 指纹匹配任务可显式 resume；不匹配任务安全清理或保持阻断。
11. 同一 Runtime 多任务共享进程和不同 Runtime 独立进程的语义均可观测、可断言。
12. E2E 必须基于真实 task、真实 Workspace、真实进程和 Main 监督器；不得用纯 mock 替代。

完成证据：

- 可重复运行的双 Runtime E2E 测试或真实环境测试脚本。
- reader-reader、reader-writer、writer-writer、取消、超时、崩溃和重启证据。
- Browser E2E 与完整 Electron Main/DMG workflow 继续全绿。
- 所有 actionable review 关闭。
- PLAN、00、10 和交接文档同步。

完成该工作单元前，不并行启动干净机、凭据清理或公开发布任务。

### 12.2 后继工程任务

1. 轮换外部凭据并确认旧凭据失效。
2. 清理 Git 历史并重扫全部 refs。
3. 干净 Apple Silicon Mac 安装、Gatekeeper、升级和卸载。
4. CLI/Desktop/Hermes/OpenCode 共存。
5. 真实模型任务、真实用户 Preview 测试和 P0/P1 清零。

**阶段出口**：真实并发、凭据、干净机、共存和用户验收全部通过后，才允许创建公开 Preview prerelease。

---

## 13. 统一执行顺序

```text
A. 双 Runtime 同 Workspace 并发与故障 E2E
→ B. 轮换外部凭据并确认旧凭据失效
→ C. 清理 Git 历史并重扫全部 refs
→ D. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
→ E. 正式模型任务和真实用户 Preview 测试
→ F. 清零 P0/P1
→ G. 按各阶段 Go/No-Go 提升对应发布渠道
```

每次只锁定一个可独立验收的工作单元。

---

## 14. 开发流程规范

适用于：`deepseekagent`、`deepcode`、`deepseek_runtime`、`llm-harness-agent`、`oh-my-deepseek-harness`。

Remote：`https://github.com/yuanchenglu/<项目名>.git`

### 第一优先：PR 流程

1. 从最新 `develop` 创建功能分支。
2. 按 `docs/` 计划执行单一任务。
3. 提交标题和描述清晰的 Pull Request。
4. 等待相关 CI 真实通过。
5. 处理所有 actionable review。
6. 合入 `develop`。
7. 合入后更新计划、状态和交接文档。

PR 描述必须包含：问题根因、技术方案、修改范围、测试结果、未验证内容和技术债务。

### 第二优先：异常处理与直推

PR 流程持续因 CI 环境、依赖或规则冲突无法推进时：

1. 先定位代码问题或环境问题。
2. 代码、缺失文件或配置错误必须直接修复。
3. 无法解决时才允许直推 `develop`。
4. 直推 Commit 必须包含“问题原因”和“技术债务”。
5. 会话结束前所有工作必须存在于 GitHub 远程。

---

## 15. Go/No-Go 判断纪律

不得出现以下误判：

- 把“代码已写”描述为“发布门禁已通过”。
- 把无签名 DMG 构建通过描述为 Electron Preview 已发布。
- 把无签名 DMG 描述为已签名、公证或 Stable。
- 把 Renderer Workspace Lock 测试描述为真实 Runtime 生命周期闭环。
- 把 Runtime Lease 协议测试描述为真实 task/PID 生命周期已接入。
- 把真实 task/PID 生命周期描述为双 Runtime 同 Workspace E2E 已完成。
- 把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 在凭据轮换和历史清理前公开包含有效秘密的仓库。
- 依赖旧容器、旧工作区或未推送文件；GitHub 远程始终是唯一事实源。
