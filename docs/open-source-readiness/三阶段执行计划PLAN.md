# DeepAgent 三阶段产品与开源发布计划

> **版本**：v2.8.0  
> **最后更新**：2026-07-29  
> **唯一事实源**：GitHub 远程仓库 `yuanchenglu/deepseekagent`  
> **开发分支**：`develop`  
> **发布分支**：`master`  
> **当前结论**：CLI Alpha、WebUI Beta、Electron Preview 均为 **No-Go**。双 Runtime 同 Workspace 并发与故障 E2E 已完成，当前唯一任务是 Owner 外部凭据轮换与旧凭据失效确认；不得并行跳过安全依赖。

---

## 1. 目标与事实纪律

项目按三个阶段交付：

1. **CLI Alpha**：公开仓库、可安装、可运行真实 Agent 任务。
2. **WebUI Beta**：本地无感认证、稳定生命周期和浏览器界面。
3. **Electron Preview**：DeepAgent + DeepCode 双模式 Apple Silicon 客户端。

事实优先级：

```text
最新远程代码、PR、CI、review
→ 本 PLAN
→ 00-THREE-PHASE-DELIVERY-STATUS.md
→ 10-ELECTRON-PREVIEW-STATUS.md
→ 07/08/09 阶段契约
→ 历史交接和旧计划
```

必须区分：

- 代码已经实现；
- 自动化测试已经通过；
- 真实环境验收已经完成；
- 发布渠道已经开放。

上述状态不得相互替代。

许可口径固定为：

> DeepAgent Core 使用 MIT，是开源软件；WebUI/Desktop 使用 BSL-1.1，是源码可见软件。不得把整个仓库描述为 MIT。

---

## 2. 已确认远程基线

以下为稳定合并基线，不代表永久最新 Head：

- PR #15：Main 权威 Runtime Task / Workspace Lease 协议和契约测试。
- PR #17 最终 Head：`aba94fab7b36f9bd140752c455acdd4838bd3835`。
- PR #17 squash merge：`e0f2f407daa6f273ee4c927934efc2e3b27293a0`。
- PR #18 squash merge：`9e26f290c60544fc8a99cff8c31cecfbb8c99fd9`，同步 PLAN v2.7.0、状态和交接。
- PR #19 最终 Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`。
- PR #19 squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`，完成双 Runtime E2E 和失败关闭修复。
- `master` 快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。

PR #17 已真实通过：

- Browser E2E；
- Electron concurrency contract；
- 全 Git refs 密钥扫描；
- WebUI 全量测试、构建和 NPM 许可证审计；
- Electron Main Vitest 和 TypeScript 构建；
- Runtime 复用与无签名 Preview 约束；
- 无签名 Apple Silicon DMG；
- Bundle ID、版本、arm64、安装器、Manifest、SHA-256 和 artifact；
- 所有 actionable review 已处理，未解决 review thread 为 0。

Publish Job 在 PR 场景按预期跳过。未创建 Tag、Release 或公开 Preview channel。

> 新会话必须实时读取 `develop`、`master`、开放 PR、Actions 和 review。文档不递归硬编码“永远最新”的 Head。

---

## 3. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前判断 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体工程接近完成；外部凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90%–92% | **No-Go** | Browser E2E 和核心生命周期自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 95%–96% | **No-Go** | 双 Runtime 真实并发与故障 E2E 已完成；凭据、历史、干净机、共存和用户验收未关闭 |

**整体判断**：主体工程约九成以上，项目处于发布收敛后半程。

---

# 第一阶段：CLI Alpha

## 4. 已完成

- `DEEPAGENT_HOME` / `~/.deepagent` 产品目录隔离。
- 不读取、覆盖或删除 Hermes/OpenCode 用户目录。
- `~/.local/bin/deepagent` 为唯一全局 CLI 命令。
- Core-only Apple Silicon 制品路径。
- Manifest、SHA-256、渠道指针和版本一致性契约。
- 版本目录、原子切换、失败回滚和清单驱动卸载主体。
- realpath 边界校验和未知文件保护。
- CLI 入口、错误边界、开源治理和许可矩阵。

## 5. 发布阻断项

1. 轮换所有曾进入代码、配置、日志或 Git 历史的对象存储、发布和服务凭据。
2. 确认旧凭据失效。
3. 清理 Git 历史中的有效秘密，并重扫全部 refs。
4. 在干净 Apple Silicon Mac 验证首次安装、升级、故意失败升级、回滚和卸载。
5. 验证 DeepAgent 对 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期影响。
6. 使用至少一个正式支持模型完成真实 Agent 任务。
7. 清零 Alpha 发布范围内 P0/P1。

**阶段出口**：以上条件全部满足后，才允许发布 CLI Alpha。

---

# 第二阶段：WebUI Beta

## 6. 已完成

- 一次性 Ticket → HttpOnly Session Cookie。
- 非法、失效和重放 Ticket 防护。
- 登录 URL 清理和浏览器 Secret 边界。
- Browser E2E 在 GitHub Actions 中真实通过。
- WebUI 单元测试、构建、静态 i18n 和 NPM 许可证审计。
- `deepagent webui start/open/status/stop` 生命周期主体。
- 默认 loopback，独立 PID、日志、端口和数据目录。
- WebUI 与 CLI 共用 DeepAgent Runtime 主路径。
- 无固定默认密码、无默认 LAN 暴露。

## 7. 发布阻断项

1. Alpha → Beta 数据升级、迁移失败回滚和干净机完整生命周期。
2. CLI、WebUI、Hermes、用户 OpenCode 的真实共存矩阵。
3. 正式 Beta 官网构建、发布制品和渠道验证。
4. 至少一个外部测试周期。
5. 清零 Beta 范围 P0/P1。

**阶段出口**：迁移、共存、渠道和真实用户门禁全部通过后，才允许发布 WebUI Beta。

---

# 第三阶段：Electron Preview

## 8. 已完成

### 8.1 双模式与发布基础

- DeepAgent / DeepCode 双模式架构和无重启模式切换。
- Main Process、独立 Runtime、Keychain、环境白名单和状态目录边界。
- DeepCode 使用项目内置 Runtime 路径，不依赖用户全局 OpenCode。
- Renderer 不持有根 Secret。
- 独立 `deepagent-desktop` 命令，不覆盖 CLI `deepagent`。
- 无签名、未公证 Apple Silicon DMG 自动构建和验证。

### 8.2 Workspace Lock 与 Renderer 所有权

- reader-reader 并行。
- reader-writer 双向互斥。
- writer-writer 互斥。
- `webContents.id + taskId` Renderer 所有权隔离。
- Renderer 无法释放其他 Renderer 的锁。
- Renderer 销毁后 Main 自动回收其 Renderer 租约。

### 8.3 正式发布 concurrency

PR #13 已完成：

- 同一 PR 新提交取消旧验证；
- PR 验证和正式发布使用不同 concurrency group；
- `publish=true` 正式运行不被后续运行取消；
- GitHub prerelease 和 R2 Preview channel 发布事务串行排队；
- 静态契约脚本失败关闭。

### 8.4 Runtime Task / Workspace Lease 协议

PR #15 已完成：

- Main Process 唯一权威协调器；
- `(runtime, taskId)` 任务身份；
- 规范化 Workspace 和显式 `read` / `write`；
- acquire、heartbeat、release、cancel Runtime Adapter；
- Main-only bind-process、timeout、process-exit、runtime-crash、recover；
- `(runtime, eventId)` 幂等；
- 默认最多 4,096 条有界重放缓存；
- orphaned 失败关闭；
- 冲突、取消、超时、重放、PID 绑定、崩溃和恢复契约测试。

### 8.5 真实 task/PID 生命周期

PR #17 已完成：

1. Electron Main 实例化持久化、认证的 Runtime Task Supervisor。
2. DeepAgent 与 DeepCode 使用固定 Runtime 身份。
3. DeepAgent 任务绑定共享 Agent Bridge 真实 PID。
4. DeepCode 每回合在 spawn 前获取写租约，并绑定实际子进程 PID。
5. Runtime heartbeat 与 Main timeout 监督接入。
6. 正常结束、取消、进程退出、Runtime crash 和 Main shutdown 驱动权威状态。
7. Main 重启后先恢复为 orphaned，PID 指纹验证成功并显式 resume 后才重建 active。
8. POSIX 使用进程启动时间和命令证据；Windows 使用 PowerShell/CIM 进程证据。
9. 一个 Runtime 的 heartbeat 失效时，该 Runtime 活跃任务统一 orphaned 并继续持锁。
10. Supervisor Token 不传播给 Agent、npm、工具或 bridge 子进程。
11. Supervisor 状态跟随 `webUiHome()`。
12. generation 历史只保留可复用 DeepAgent task，不累计一次性 DeepCode 回合。
13. Main 重启后的 socket RPC 强制新连接，避免 stale keep-alive `EPIPE`。
14. 非 Desktop WebUI 未配置 Supervisor 时保持 no-op；Desktop 缺少 Supervisor 时失败关闭。

### 8.6 双 Runtime 同 Workspace 并发与故障 E2E

PR #19 已完成：

1. 使用生产客户端和同一 Main Supervisor 验证 reader-reader、reader-writer 双向互斥和 writer-writer。
2. acquire 被拒绝时 spawn 计数为 0，Workspace 无写副作用。
3. 正常完成、取消、heartbeat timeout、Bridge crash 和 DeepCode child crash 终态闭环。
4. PID 消失、PID 重用、Main/Runtime 重启和跨 Workspace 隔离通过。
5. 不可验证任务保持 orphaned 和 Workspace 锁，后台 PID 探测不自动释放。
6. acquire-before-bind 的无 PID orphaned 任务禁止盲目恢复，但允许原 Runtime 显式终止并释放。
7. 最终专项 E2E 6/6、Browser E2E 和完整 Electron Preview workflow 全部通过。
8. 唯一 P2 actionable review 已修复并解决，未解决 actionable thread 为 0。

完整证据：`12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`。

---

## 9. 当前唯一第一优先任务

### Owner Gate：轮换外部凭据并确认旧凭据失效

该任务必须由仓库 Owner / 外部平台管理员执行，当前环境不得代替 Owner 创建、查看或撤销真实 Secret。

完成条件：

1. 盘点所有曾进入代码、配置、日志、制品或 Git 历史的发布、对象存储和服务凭据。
2. 创建最小权限的新凭据并更新 GitHub / 外部平台 Secrets。
3. 使用新凭据完成隔离的最小读写验证，不创建公开 Release 或渠道。
4. 撤销旧凭据。
5. 使用旧凭据执行安全的最小只读验证，并确认认证失败或权限拒绝。
6. 将不含秘密值的脱敏证据提交远程。

Owner 操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

在该 Gate 关闭前，不得启动 Git 历史重写，也不得提升 Alpha、Beta、Preview 或 Stable 渠道。

---

## 10. 后继执行顺序

```text
A. ✅ 双 Runtime 同 Workspace 并发与故障 E2E
→ B. 【当前唯一 Owner Gate】轮换外部凭据并确认旧凭据失效
→ C. 清理 Git 历史并重扫全部 refs
→ D. 干净 Apple Silicon Mac 验证 CLI/WebUI/Electron 生命周期
→ E. CLI/Desktop/Hermes/OpenCode 共存验证
→ F. 正式模型任务和真实用户 Preview 测试
→ G. 清零 P0/P1
→ H. 按各阶段 Go/No-Go 提升对应发布渠道
```

每次只锁定一个可独立验收的工作单元。

---

## 11. 对外发帖与发布表述边界

可以对外说明：

- Runtime Lease 协议、真实 task/PID 生命周期和双 Runtime 同 Workspace E2E 已进入 `develop`；
- Browser E2E、WebUI、Electron Main 和无签名 DMG 自动门禁已通过；
- 项目处于发布收敛阶段。

不得对外宣称：

- Electron Preview 已公开发布；
- 已签名或已公证；
- CLI Alpha、WebUI Beta 或 Electron Preview 已达到 Go；
- 仓库全部使用 MIT；
- 已完成凭据轮换、历史清理、干净机或真实用户验收。

---

## 12. 开发流程规范

适用于以下 5 个项目：

- `deepseekagent`
- `deepcode`
- `deepseek_runtime`
- `llm-harness-agent`
- `oh-my-deepseek-harness`

Remote：`https://github.com/yuanchenglu/<项目名>.git`

### 12.1 分支策略

- 开发分支：`develop`
- 发布分支：`master`
- `develop` 已取消 PR 强制保护，可以直接推送。

### 12.2 第一优先：走 PR 流程

1. 创建功能分支 → 提 Pull Request → 等待 CI 通过 → 合入 `develop`。
2. 按项目 `docs/` 目录下的计划文档执行任务。
3. 确保 PR 标题和描述清晰说明变更内容。

PR 描述至少包含：问题根因、技术方案、修改范围、测试结果、未验证内容、技术债务。

### 12.3 第二优先：异常处理与直推

如果 PR 流程持续出问题，例如 CI 环境不可用、测试依赖无法安装、规则冲突：

1. **先分析原因**：定位根因，确认是代码问题还是环境问题。
2. **尝试修复**：如果是代码问题，例如缺少文件、配置错误，直接修复。
3. **解决不了则直推 `develop`**：如果问题无法在当前环境解决，直接推送到 `develop`，不无限阻塞流程。

### 12.4 直推 `develop` 的纪律

Commit 信息必须包含“问题原因”和“技术债务”段落：

```text
<type>(<scope>): <变更说明>

## 问题原因
[写明为什么 PR 流程无法通过，根因是什么]

## 技术债务
- [遗留问题或待办事项]
```

示例：

```text
feat(auth): add login ticket validation

## 问题原因
CI 环境的 Playwright 依赖版本与本地不一致，E2E 测试在 CI 上无法运行。已手动验证本地通过。

## 技术债务
- Playwright 版本锁定需要统一管理
- E2E 测试在 CI 上需要单独排查
```

### 12.5 技术债务记录（二选一）

**方式 A：Commit 信息，推荐**

- 在 Commit 的“技术债务”段落使用短横线列表记录。

**方式 B：项目文档**

- `deepseekagent` → `docs/TECH_DEBT.md` 或 `docs/BUG_LIST.md`
- `deepcode` → `docs/BUG_LIST.md`
- `deepseek_runtime` → `docs/TECH_DEBT.md`
- `oh-my-deepseek-harness` → `docs/TECH_DEBT.md`
- `llm-harness-agent` → 根目录 `TECH_DEBT.md`

每条格式：

```text
[日期] 描述 | 遗留原因 | 状态
```

### 12.6 核心原则

- 能走 PR 就走 PR，直推是兜底方案，不是默认方案。
- 直推必须有交代：Commit 信息要说明为什么以及遗留了什么。
- 技术债务必须留下可追踪记录。
- 会话结束前，所有关键代码、文档、补丁和诊断结论必须存在于 GitHub 远程。
- 不得依赖旧容器、旧工作区或未推送文件继续工作。

---

## 13. Go/No-Go 判断纪律

不得出现以下误判：

- 把代码已写描述为发布门禁已通过。
- 把无签名 DMG 构建成功描述为 Electron Preview 已发布。
- 把无签名 DMG 描述为已签名、公证或 Stable。
- 把 Renderer Workspace Lock 测试描述为 Runtime 生命周期闭环。
- 把 Runtime Lease 协议测试描述为真实 task/PID 生命周期已经接入。
- 把真实 task/PID 接入描述为双 Runtime E2E 已完成。
- 把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 在凭据轮换和历史清理前公开包含有效秘密的仓库或发布渠道。
- 在未重新核对 GitHub 远程状态时机械沿用旧 SHA、旧计划或旧交接。
