# DeepAgent 三阶段产品与开源发布计划

> **版本**：v2.6.0  
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

截至 v2.6.0，以下关键 PR 已合入 `develop`：

| PR | 关键产出 |
|---|---|
| #1 | 三阶段主体实现、CLI/WebUI/Electron 基础 |
| #3 | 无签名 Electron Preview 打包收尾 |
| #4 | Browser E2E workflow |
| #5 | Browser E2E 认证安全场景扩展并真实通过 |
| #6 | Electron Preview 自动 DMG 门禁、i18n、品牌契约和安全扫描 |
| #10 | Workspace Lock Renderer 所有权隔离和销毁自动回收 |
| #11 | Electron Preview 状态同步 |
| #12 | 三阶段计划 v2.4.0 与远程优先交接 |
| #13 | PR 验证可取消、正式发布不可取消、发布事务串行排队 |
| #14 | 三阶段计划 v2.5.0，将优先级切换到 Runtime Lease 协议 |
| #15 | Main 权威 Runtime Task / Workspace Lease 协议、状态机与契约测试 |

本次更新前远程快照：

- `develop`：`cb2885ed1a31cf559640ec62d97caa6047a6b1ad`
- `master`：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`
- PR #15 最终 Head：`b3c2b07e1c8508af10d217b8d0b3581657617639`
- PR #15 squash merge：`cb2885ed1a31cf559640ec62d97caa6047a6b1ad`

PR #15 已真实通过：

- WebUI Browser E2E。
- Electron concurrency contract。
- 全 refs Gitleaks。
- WebUI 全量测试、构建和许可证审计。
- Electron Main Vitest，包括新增 Runtime Lease 契约测试。
- Runtime 复用与无签名目标约束。
- 无签名 Apple Silicon DMG、Bundle ID、版本、arm64 和安装器验证。
- Manifest、SHA-256 和 artifact 生成。

PR 场景的 Publish Job 按预期跳过；没有创建 Tag、Release 或公开 Preview channel。

新会话必须重新读取远程最新 Head、开放 PR、Actions 和 review，不得把上述 SHA 当作永久基线。

---

## 3. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前判断 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90% | **No-Go** | Browser E2E 与核心自动化已完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 92% | **No-Go** | concurrency 与 Runtime Lease 协议已完成；真实 task/PID、真实并发和真实环境未关闭 |

**整体判断**：不继续扩张功能。优先关闭真实生命周期、故障恢复、安全、迁移、共存、干净机和用户验收门禁。

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

### 11.1 双模式与安全边界

- DeepAgent / DeepCode 双模式架构与模式切换。
- Main Process 负责窗口、进程、更新、Keychain、权限和系统能力。
- DeepAgent Runtime 与 DeepCode Runtime 独立进程、状态目录和 IPC 命名空间。
- DeepCode 使用项目内置 OpenCode，不调用用户全局版本。
- Renderer 不持有根 Secret，子进程使用环境变量白名单。
- Desktop 命令为 `deepagent-desktop`，不覆盖 CLI 的 `deepagent`。

### 11.2 Workspace Lock 与 Renderer 所有权

- 标准多读单写：reader-reader 并行、reader-writer 互斥、writer-writer 互斥。
- 锁持有者使用 `webContents.id + taskId` 复合身份。
- Renderer 无法释放其他 Renderer 的锁。
- Renderer 崩溃或销毁后，Main 自动回收其全部 Renderer 租约。

> Renderer 锁边界不能等同于真实 Runtime task/PID 生命周期闭环。

### 11.3 Electron Preview 自动门禁

- PR 修改 Desktop、版本或 workflow 时，在 `macos-15` arm64 runner 自动构建无签名 DMG。
- 正式发布仅允许 `workflow_dispatch`、显式 `X.Y.Z-preview.N` 和 `publish=true`。
- 全 refs Gitleaks、WebUI 测试/构建/许可证、Electron Main、Runtime 复用约束、DMG、Bundle、arm64、安装器、Manifest、SHA-256 和 artifact 门禁。
- Browser E2E 真实通过。

### 11.4 正式发布 concurrency

PR #13 建立以下契约：

1. 同一 PR 的新提交可取消该 PR 的旧验证运行。
2. PR 验证与正式发布使用清晰分离的 concurrency group。
3. `publish=true` 正式运行不被后续运行取消。
4. 修改 GitHub prerelease 与 R2 Preview channel 的 Publish Job 使用固定 group 串行排队。
5. concurrency 表达式和事件真值表由静态检查失败关闭。
6. 无签名定位、版本、Tag、Manifest、SHA-256 和 `publish=true` 边界未改变。

### 11.5 Runtime Task / Workspace Lease 协议

PR #15 完成协议工作单元：

1. Main Process 是唯一权威协调器。
2. 任务身份包含 Runtime、规范化 Workspace、taskId、显式 `read` / `write` 和可选 PID/进程树。
3. 状态机覆盖 pending、active、releasing、released、expired、orphaned、recovered。
4. acquire 后由 Main-only `bind-process` 一次性绑定进程身份；相同绑定幂等，替换拒绝。
5. Runtime Adapter 只能发送 acquire、heartbeat、release、cancel。
6. timeout、process-exit、runtime-crash、recover 和 bind-process 为 Main-only 监督事件，动态注入也失败关闭。
7. 幂等键按 `(runtime, eventId)` 隔离；重放缓存默认最多 4,096 条。
8. Runtime 崩溃后 orphaned 租约继续持锁，只有 Main recover 或确认 process-exit 才释放。
9. 冲突 acquire 不留下幽灵 pending；快照和转换历史不能被外部修改。
10. 契约测试覆盖正常、冲突、取消、超时、重放、进程绑定、权限、崩溃和恢复。

> 协议与契约测试完成，不等于真实 Runtime task/PID 生命周期已经接入。

## 12. 当前唯一第一优先工程任务

### 12.1 真实 Runtime task/PID 生命周期接入

必须完成：

1. Electron Main 实例化单一 `RuntimeTaskLeaseCoordinator`。
2. DeepAgent 和 DeepCode 分别通过固定 Runtime Adapter 接入，不能冒充另一 Runtime。
3. 真实任务启动前 acquire；进程 spawn 后由 Main-only `bind-process` 绑定 PID/进程树。
4. Runtime 周期性发送 heartbeat；Main 负责 timeout、process-exit、runtime-crash 和 recover。
5. 正常结束、取消、超时、进程树退出、Runtime 重启和异常回收严格驱动协议终态。
6. 任何故障都不得产生 reader/writer 或 writer/writer 双写窗口。
7. Main 重启后从持久状态和真实存活进程重建；无法证明安全时保持 orphaned 失败关闭。
8. Renderer 与 Runtime 无法调用 Main-only 监督事件。
9. 增加真实监督器集成测试。

完成真实生命周期接入前，不并行启动双 Runtime 同 Workspace E2E。

### 12.2 后继工程任务

1. 双 Runtime 同 Workspace reader-reader、reader-writer、writer-writer、取消、超时、崩溃和重启 E2E。
2. 干净 Apple Silicon Mac 安装、Gatekeeper、升级和卸载。
3. CLI/Desktop/Hermes/OpenCode 共存。
4. 真实用户 Preview 测试和 P0/P1 清零。

**阶段出口**：Runtime 生命周期、真实并发、干净机、共存和用户验收全部通过后，才允许创建公开 Preview prerelease。

---

## 13. 统一执行顺序

```text
A. 将租约绑定真实 Runtime task/PID 生命周期
→ B. 双 Runtime 同 Workspace 并发与故障 E2E
→ C. 轮换外部凭据并确认旧凭据失效
→ D. 清理 Git 历史并重扫全部 refs
→ E. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
→ F. 正式模型任务和真实用户 Preview 测试
→ G. 清零 P0/P1
→ H. 按各阶段 Go/No-Go 提升对应发布渠道
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

PR 描述必须包含：

- 问题根因。
- 技术方案。
- 修改范围。
- 测试结果。
- 未验证内容。
- 技术债务。

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
- 把 Runtime Lease 协议单元测试描述为真实 task/PID 生命周期或双 Runtime E2E 已完成。
- 把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 把 concurrency 修复完成描述为 Electron Preview 已达到发布条件。
- 在凭据轮换和历史清理前公开包含有效秘密的仓库。
- 依赖旧容器、旧工作区或未推送文件；GitHub 远程始终是唯一事实源。
