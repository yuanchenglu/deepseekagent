# DeepAgent 三阶段产品与开源发布计划

> **版本**：v2.4.0  
> **最后更新**：2026-07-28  
> **唯一事实源**：GitHub 远程仓库 `yuanchenglu/deepseekagent`  
> **开发分支**：`develop`  
> **发布分支**：`master`  
> **当前结论**：主体功能开发已基本完成，项目进入发布收敛阶段；三个阶段当前均为 **No-Go**，不得因代码或 CI 局部通过而提前宣称已发布。

---

## 1. 计划目标与范围

项目按三个阶段交付：

1. **CLI Alpha**：公开仓库、可安装、可运行真实 Agent 任务。
2. **WebUI Beta**：为普通用户提供本地无感登录、稳定生命周期和浏览器界面。
3. **Electron Preview**：提供 DeepAgent + DeepCode 双模式 Apple Silicon 客户端。

详细阶段契约：

- `07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`
- `08-PHASE-2-WEBUI-STABLE-BETA.md`
- `09-PHASE-3-DUAL-MODE-ELECTRON.md`
- `10-ELECTRON-PREVIEW-STATUS.md`

真实进度与阻断项：

- `00-THREE-PHASE-DELIVERY-STATUS.md`

新会话交接：

- `HANDOFF_2026-07-28.md`

许可口径固定为：

> DeepAgent Core 使用 MIT，是开源软件；WebUI/Desktop 使用 BSL-1.1，是源码可见软件。README、官网和发布说明不得把整个仓库描述为 MIT。

---

## 2. 当前远程基线

截至本版本更新前，以下 PR 已合入 `develop`：

| PR | 结果 | 关键产出 |
|---|---|---|
| #1 | 已合入 | 三阶段主体实现、CLI/WebUI/Electron 基础 |
| #3 | 已合入 | 无签名 Electron Preview 打包收尾 |
| #4 | 已合入 | Browser E2E workflow |
| #5 | 已合入 | Browser E2E 真实通过与认证场景扩展 |
| #6 | 已合入 | Electron Preview 自动 DMG 门禁、i18n、品牌契约和安全扫描 |
| #10 | 已合入 | Workspace Lock Renderer 所有权隔离和崩溃自动回收 |
| #11 | 已合入 | Electron Preview 状态文档同步 |

更新前的 `develop` 快照为 `1fc31324343c574a9e03bac8e2435f72b474d45a`。新会话必须重新读取远程最新 Head，不得把该 SHA 当作永久基线。

过期 PR #2 已关闭且不合并，原因是它基于旧基线并包含 171 个已被后续 PR 替代的文件变更。

当前不存在仅保存在旧容器或旧工作区中的代码；本次计划和交接更新也必须保存在远程功能分支或 PR 中。

---

## 3. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前判断 |
|---|---:|---|---|
| 第一阶段：CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成，外部安全和干净机门禁未关闭 |
| 第二阶段：WebUI Beta | 约 90% | **No-Go** | 浏览器 E2E 与核心自动化已通过，迁移、共存和正式渠道验收未关闭 |
| 第三阶段：Electron Preview | 约 87%–90% | **No-Go** | 自动 DMG 和 Main IPC 锁边界已完成，发布事务、Runtime 租约和真实环境验收未完成 |

**整体判断**：工程主体约九成完成，但“功能完成度”不能等同于“可公开发布程度”。现阶段不继续扩张功能，优先关闭安全、发布事务、真实生命周期、共存、迁移、故障恢复和用户验收门禁。

---

# 第一阶段：CLI Alpha

## 4. 阶段目标

面向命令行早期用户，交付只支持 macOS Apple Silicon 的公开 CLI Alpha：

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
- 清单驱动卸载与 realpath 边界校验。
- Core-only Apple Silicon 制品构建路径。
- 开源治理、许可矩阵、安全政策和第三方依赖声明。
- 官网与安装文档的 DeepAgent 入口收敛。

## 6. 未完成的发布阻断项

1. 轮换所有曾进入代码、配置、日志或 Git 历史的对象存储、发布和服务凭据。
2. 确认旧凭据已失效，再清理 Git 历史中的有效秘密。
3. 对全部 Git refs 重扫，达到零有效秘密。
4. 在干净 macOS Apple Silicon 环境验证首次安装、覆盖安装、升级、故意失败升级、自动/显式回滚、保留数据卸载和完全卸载。
5. 验证 DeepAgent 对 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期影响。
6. 使用至少一个正式支持的模型完成真实 Agent 任务。
7. 清零发布范围内 P0/P1。

**阶段出口**：上述门禁全部通过后，才能发布 CLI Alpha，并更新 Alpha 渠道指针。

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

默认只监听 `127.0.0.1`。本地启动采用一次性 Ticket 换取 HttpOnly Session Cookie，不使用固定默认密码；LAN/公网不属于首版 Beta 承诺。

## 8. 已完成

- 一次性 Ticket、失效/非法 Ticket、重放防护和 URL 清理。
- HttpOnly Session Cookie 和浏览器 Secret 边界。
- Browser E2E 在 GitHub Actions 中真实通过。
- WebUI 单元测试、构建、静态 i18n 和 NPM 许可证审计门禁。
- `deepagent webui` 生命周期命令和本地端口选择。
- 默认 loopback、独立 PID/日志/端口和数据目录。
- WebUI 与 CLI 共用 DeepAgent Runtime 主路径。
- Hermes → DeepAgent 面向用户品牌契约收敛。
- 无固定默认密码、无默认 LAN 监听。

## 9. 未完成的发布阻断项

1. Alpha → Beta 数据升级、迁移失败回滚和干净机完整生命周期。
2. CLI、WebUI、Hermes、用户 OpenCode 的真实共存矩阵。
3. 正式 Beta 官网构建、发布制品和渠道验证。
4. 至少一个外部测试周期，并清零 Beta 范围 P0/P1。
5. LAN/公网继续作为独立后续评估，不阻塞本地 Beta，也不得未经设计直接开放。

**阶段出口**：迁移、共存、渠道和真实用户门禁全部通过后发布 WebUI Beta；经历完整外测周期后再评估 Stable。

---

# 第三阶段：Electron Preview

## 10. 阶段目标

交付一个 Apple Silicon Electron 客户端：默认进入 DeepAgent，左上角无重启切换 DeepCode。两个模式共享当前项目与公共设置，但会话、任务、布局和 Runtime 状态相互隔离。

当前 Preview 明确采用**无签名、未公证 DMG**；不得描述为已签名、公证或 Stable。

## 11. 已完成

### 双模式与安全边界

- DeepAgent / DeepCode 双模式架构与模式切换。
- Main Process 负责系统、安全、窗口、进程、更新和 Keychain 边界。
- DeepAgent Runtime 与 DeepCode Runtime 独立进程、状态目录和 IPC 命名空间。
- DeepCode 使用项目内置 OpenCode，不调用用户全局版本。
- Renderer 不持有根 Secret，子进程使用环境变量白名单。
- Desktop 命令为 `deepagent-desktop`，不覆盖 CLI 的 `deepagent`。

### Workspace Lock 已完成子项

- 标准多读单写算法：reader-reader 并行、reader-writer 互斥、writer-writer 互斥。
- 锁持有者使用 `webContents.id + taskId` 复合身份。
- Renderer 无法越权释放其他 Renderer 的锁。
- Renderer 崩溃或销毁后，Main 自动回收其全部租约。
- 所有者隔离、并发竞争、升级和销毁回收测试已通过。

> 边界：以上只完成 Main IPC 所有权与 Renderer 故障回收，不能等同于真实 Runtime 任务协议已强制接入。

### Electron Preview 自动门禁

- PR 修改 Desktop/版本/workflow 时，在 `macos-15` arm64 runner 自动构建无签名 DMG。
- 正式发布仅允许 `workflow_dispatch`、显式 `X.Y.Z-preview.N` 和 `publish=true`。
- 全 refs Gitleaks 扫描。
- WebUI 安装、全量测试、构建、i18n 和许可证审计。
- Electron Main 测试、TypeScript 构建和 Runtime 复用约束。
- DMG、Bundle ID、版本、arm64、安装脚本和未签名状态验证。
- Manifest、SHA-256 和 workflow artifact 生成。
- Browser E2E 在 PR #5、#6、#10 中真实通过。

## 12. 未完成的发布阻断项

### P0/P1 工程收口

1. **修复发布 concurrency**：当前 workflow 使用 `cancel-in-progress: true`；PR 验证可取消，但正式 `publish=true` 发布必须串行且不可被后续运行取消，避免 GitHub prerelease 与 R2 Preview channel 不一致。
2. **固化 Runtime Task / Workspace Lease 协议**：真实任务启动、结束、取消、超时和崩溃事件必须由 Main 租约协调器强制管理，不依赖 Renderer 自愿调用。
3. **绑定 task/PID 生命周期**：处理心跳、超时、进程树退出、Runtime 重启和异常回收。
4. **双 Runtime 真实并发 E2E**：同一 Workspace 验证 reader-reader、reader-writer、writer-writer、取消和崩溃回收。

### 外部和真实环境收口

5. 下载 DMG artifact，在干净 Apple Silicon Mac 完成安装和首次启动。
6. 验证 Gatekeeper 右键打开、升级、卸载和 CLI/Desktop 共存。
7. 验证两个 Runtime 独立崩溃恢复、后台任务和模式切换。
8. 完成真实用户 Preview 测试，清零 P0/P1。
9. 满足全部门禁后创建 `preview.N` Tag，再执行 `workflow_dispatch(publish=true)`。

**阶段出口**：只允许先发布无签名 Electron Preview；完成真实外测且无 P0/P1 后再评估签名、公证和 Stable。

---

## 13. 统一执行顺序

```text
A. 修复 Electron 发布 workflow concurrency
→ B. 固化 Runtime Task / Workspace Lease 协议
→ C. 将租约绑定真实 task/PID 生命周期
→ D. 双 Runtime 同 Workspace 并发与故障 E2E
→ E. 轮换外部凭据并确认旧凭据失效
→ F. 清理 Git 历史并重扫全部 refs
→ G. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
→ H. 正式模型任务和真实用户 Preview 测试
→ I. 清零 P0/P1
→ J. 按各阶段 Go/No-Go 提升对应发布渠道
```

每次只锁定一个可验收工作单元，避免同时启动多个跨阶段任务。

---

## 14. 开发流程规范

适用于以下 5 个项目：

- `deepseekagent`
- `deepcode`
- `deepseek_runtime`
- `llm-harness-agent`
- `oh-my-deepseek-harness`

Remote：`https://github.com/yuanchenglu/<项目名>.git`

### 第一优先：PR 流程

1. 从最新 `develop` 创建功能分支。
2. 按 `docs/` 计划执行单一任务。
3. 提交标题和描述清晰的 Pull Request。
4. 等待相关 CI 真实通过。
5. 处理 review 后合入 `develop`。

### 第二优先：异常处理与直推

PR 流程持续因 CI 环境、依赖、规则冲突等无法推进时：

1. 先定位是代码问题还是环境问题。
2. 代码问题直接修复并重跑。
3. 无法在当前环境解决时，才允许直推 `develop`，不得默认绕过 PR。

直推 Commit 必须包含：

```text
<type>(<scope>): <变更说明>

## 问题原因
[PR/CI 无法通过的根因]

## 技术债务
- [本次遗留问题]
```

技术债务也可记录到：

- deepseekagent → `docs/TECH_DEBT.md` 或 `docs/BUG_LIST.md`
- deepcode → `docs/BUG_LIST.md`
- deepseek_runtime → `docs/TECH_DEBT.md`
- oh-my-deepseek-harness → `docs/TECH_DEBT.md`
- llm-harness-agent → 根目录 `TECH_DEBT.md`

格式：`[日期] 描述 | 遗留原因 | 状态`

---

## 15. Go/No-Go 判断纪律

不得出现以下误判：

- 把“代码已写”描述为“发布门禁已通过”。
- 把自动 DMG 构建通过描述为 Electron Preview 已发布。
- 把无签名 DMG描述为已签名、公证或 Stable。
- 把 Main IPC 锁测试通过描述为真实 Runtime 租约闭环完成。
- 把 Browser E2E 通过描述为 WebUI Beta 的迁移、共存和渠道全部完成。
- 在凭据轮换和历史清理前公开包含有效秘密的仓库。
- 依赖旧容器、旧工作区或未推送文件；GitHub 远程始终是唯一事实源。
