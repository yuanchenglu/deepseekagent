# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-28  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 发布分支：`master`  
> 说明：总执行顺序以 `三阶段执行计划PLAN.md` v2.7.0 为准；本文只记录真实完成情况、阻断项和远程证据。

---

## 1. 远程事实基线

| 项目 | 当前事实 |
|---|---|
| PR #15 | Main 权威 Runtime Task / Workspace Lease 协议已合入 |
| PR #17 最终 Head | `aba94fab7b36f9bd140752c455acdd4838bd3835` |
| PR #17 merge | 已 squash 合入 `develop`，提交 `e0f2f407daa6f273ee4c927934efc2e3b27293a0` |
| Browser E2E | 最终 Head 真实成功 |
| Electron workflow | concurrency、全 refs Secret 扫描、WebUI、许可证、Electron Main、无签名 DMG、Manifest、SHA-256、artifact 全部成功 |
| review | 4 条建议全部实现、回复并解决；最终 unresolved 为 0 |
| 发布动作 | Publish Job 在 PR 场景跳过；未执行 `publish=true`，未创建 Tag、Release 或公开渠道 |
| 本地未推送工作 | **无**；功能代码、测试和本次状态同步均进入 GitHub 远程分支 |

PR #17 的 Electron workflow 首轮只出现一个与本次改动无关的 MCU TTS 异步断言抖动；同一最终 Head 的失败 Job 重跑后全链路成功。该抖动未通过修改业务代码规避。

新会话必须先读取最新远程 Head、开放 PR、Actions 和 review，不得机械沿用本文 SHA。

---

## 2. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90% | **No-Go** | Browser E2E 和核心自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 94% | **No-Go** | Runtime 协议及真实 task/PID 生命周期完成；双 Runtime 真实并发、干净机、共存和外测未关闭 |

**整体判断**：项目处于发布收敛阶段。当前不增加非必要功能，按顺序关闭真实并发、凭据、迁移、共存、干净机和用户验收。

---

## 3. CLI Alpha

### 已完成

- `DEEPAGENT_HOME` / `~/.deepagent` 产品目录隔离。
- Core-only 制品、Manifest、SHA-256、渠道和版本一致性契约。
- 安装、更新、回滚和清单驱动卸载主体。
- CLI 命令入口与错误边界。
- 开源治理、许可和官网安装入口代码准备。

### 阻断项

1. 轮换外部凭据并确认旧凭据失效。
2. 清理 Git 历史中的有效秘密。
3. 全 refs 重扫达到零有效秘密。
4. 干净 Apple Silicon Mac 安装、升级、失败回滚和卸载。
5. Hermes/OpenCode 命令、进程、配置和数据共存验证。
6. 正式支持模型的真实 Agent 任务。
7. 清零 P0/P1。

结论：**No-Go**。

---

## 4. WebUI Beta

### 已完成

- 一次性 Ticket → HttpOnly Session Cookie。
- 非法、失效、重放 Ticket 和 URL 清理 Browser E2E。
- `deepagent webui start/open/status/stop` 主体。
- loopback 默认监听、独立 PID/日志/端口/数据目录。
- WebUI 单元测试、构建、静态 i18n 和 NPM 许可证审计。
- WebUI 与 CLI 共用 DeepAgent Runtime 主路径。
- 无固定默认密码、无默认 LAN 监听。

### 阻断项

1. Alpha → Beta 数据迁移和失败回滚。
2. 干净机 WebUI 生命周期。
3. CLI/WebUI/Hermes/用户 OpenCode 真实共存矩阵。
4. 官网和正式 Beta 渠道验证。
5. 外部测试周期及 P0/P1 清零。

结论：**No-Go**。

---

## 5. Electron Preview

### 5.1 已完成：基础与自动门禁

- DeepAgent / DeepCode 双模式架构。
- Main Process、独立 Runtime、Keychain、环境白名单和状态目录边界。
- 多读单写 Workspace Lock 算法。
- `webContents.id + taskId` Renderer 所有权隔离。
- Renderer 不能释放其他 Renderer 的锁。
- Renderer 销毁后 Main 自动回收其 Renderer 租约。
- 无签名、未公证 Apple Silicon DMG 自动门禁。
- DMG、Bundle ID、版本、arm64、安装器、未签名状态、Manifest 和 SHA-256 校验。
- Browser E2E、WebUI 测试/构建/许可证和 Electron Main 全链路。

### 5.2 已完成：正式发布 concurrency

PR #13 已实现并验证：

- 同一 PR 的新提交可以取消旧验证。
- PR 验证与正式发布使用不同 group。
- `publish=true` 正式运行不会被后续运行取消。
- GitHub prerelease 与 R2 Preview channel 的 Publish Job 使用固定 group 串行排队。
- 静态脚本对表达式、分组和事件真值表失败关闭。

### 5.3 已完成：Runtime Task / Workspace Lease 协议

PR #15 已实现并验证：

- Main 权威类型化任务租约协议和状态机。
- Runtime、规范化 Workspace、taskId、显式 `read` / `write` 和可选进程身份。
- acquire 后 Main-only `bind-process`。
- Runtime Adapter 与 Main-only 监督事件权限隔离。
- `(runtime, eventId)` 幂等和默认 4,096 条有界重放缓存。
- orphaned 失败关闭和明确恢复证据。

### 5.4 已完成：真实 task/PID 生命周期

PR #17 已实现并验证：

- Electron Main 持久化、认证的单一 Runtime Task Supervisor。
- Unix Socket / Windows Named Pipe + Bearer Token。
- Supervisor 状态跟随 `webUiHome()`，隔离多 WebUI 实例。
- DeepAgent 稳定 session taskId 与共享 Agent Bridge PID。
- DeepCode 每回合 acquire-before-spawn 与独立子进程 PID 绑定。
- POSIX 与 Windows PID 指纹验证，防止 PID 复用误恢复。
- heartbeat、finish、cancel、process-exit、runtime-crash 和 Main restart 状态驱动。
- 同一 Runtime heartbeat 丢失时全部 active 任务进入 orphaned 并继续占锁。
- Main 重启后只恢复 PID 指纹匹配任务，并要求显式 resume。
- DeepAgent generation 持久化；DeepCode 一次性 task 不累积历史。
- Supervisor Token 从 Agent、npm、Tool、Bridge 子进程环境中删除。
- Supervisor RPC 不复用 stale socket，Main 重启后无 `EPIPE`。
- 非 Desktop WebUI 保持兼容；Desktop 缺失 Supervisor、Workspace 或 PID 证据时失败关闭。

### 5.5 当前唯一第一优先工程任务

**双 Runtime 同 Workspace 并发与故障 E2E**：

1. reader-reader 并行。
2. reader-writer 双向互斥。
3. writer-writer 互斥。
4. acquire 被拒绝时不得 spawn 写任务。
5. 正常完成与已确认取消后释放。
6. 取消不确定、heartbeat timeout 或 Runtime crash 时继续失败关闭。
7. DeepAgent Bridge 与 DeepCode 子进程真实崩溃语义。
8. Main/Runtime 重启后的 PID 验证、resume、清理或阻断。
9. 一个 Runtime 崩溃不错误释放另一个 Runtime 的租约。
10. E2E 必须使用真实 Workspace、真实任务进程和 Main 监督器，不能用纯 mock 替代。

在完成该工作单元前，不并行启动干净机、凭据清理或公开发布。

### 5.6 后继技术债务

- 外部凭据轮换、旧凭据失效和 Git 历史清理。
- 干净 Apple Silicon Mac 安装、Gatekeeper、升级和卸载。
- CLI/Desktop/Hermes/OpenCode 共存。
- 真实用户 Preview 和 P0/P1 清零。

结论：**No-Go**。

---

## 6. 下一执行顺序

```text
1. 双 Runtime 同 Workspace 并发与故障 E2E
2. 轮换凭据、确认旧凭据失效
3. 清理 Git 历史并重扫全部 refs
4. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
5. 正式模型任务和真实用户 Preview 测试
6. 清零 P0/P1
7. 按 Go/No-Go 提升 Alpha、Beta、Preview 渠道
```

每次只启动一个可独立验收的工作单元。

---

## 7. 禁止误判

- 不得把代码实现等同于发布门禁完成。
- 不得把无签名 DMG 描述为已签名、公证或 Stable。
- 不得把 Renderer Workspace Lock 测试描述为 Runtime 生命周期闭环。
- 不得把 Runtime Lease 协议测试描述为真实 task/PID 生命周期接入完成。
- 不得把真实 task/PID 生命周期描述为双 Runtime 同 Workspace E2E 已完成。
- 不得把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 不得把 concurrency、协议或 PID 生命周期完成描述为 Electron Preview 已发布。
- 不得依赖旧容器或未推送文件；GitHub 远程是唯一事实源。
