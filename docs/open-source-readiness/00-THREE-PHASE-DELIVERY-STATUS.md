# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-28  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 发布分支：`master`  
> 说明：总执行顺序以 `三阶段执行计划PLAN.md` v2.6.0 为准；本文只记录真实完成情况、阻断项和远程证据。

---

## 1. 远程事实基线

| 项目 | 当前事实 |
|---|---|
| 更新前 develop Head | `cb2885ed1a31cf559640ec62d97caa6047a6b1ad` |
| master Head | `b3943ac43f0f0f6a1f86f5f2cb9a230527389d91` |
| PR #13 | 已合入；Electron Preview 正式发布 concurrency 风险关闭 |
| PR #15 Head | `b3c2b07e1c8508af10d217b8d0b3581657617639` |
| PR #15 merge | 已 squash 合入 `develop`，提交 `cb2885ed1a31cf559640ec62d97caa6047a6b1ad` |
| Browser E2E | PR #15 真实成功 |
| Electron workflow | concurrency、Gitleaks、WebUI、许可证、Electron Main、无签名 DMG、Manifest、SHA-256、artifact 全部成功 |
| review | 4 条建议全部实现、回复并解决 |
| 发布动作 | Publish Job 在 PR 场景跳过；未执行 `publish=true`，未创建 Tag、Release 或公开渠道 |
| 过期 PR #2 | 已关闭，不合并；分支内容已被后续 PR 替代 |
| 本地未推送工作 | **无**；本次协议代码和文档均已进入 GitHub 远程 |

新会话必须先读取最新远程 Head、开放 PR、Actions 和 review，不得机械沿用本文 SHA。

---

## 2. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90% | **No-Go** | Browser E2E 和核心自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 92% | **No-Go** | concurrency 与 Runtime Lease 协议完成；真实 task/PID、真实并发和干净机未关闭 |

**整体判断**：项目处于发布收敛阶段。当前重点是生命周期、安全、迁移、共存、故障恢复和真实用户验收，不增加非必要功能。

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

### 已完成

- DeepAgent / DeepCode 双模式架构。
- Main Process、独立 Runtime、Keychain、环境白名单和状态目录边界。
- 多读单写 Workspace Lock 算法。
- `webContents.id + taskId` Renderer 所有权隔离。
- Renderer 不能释放其他 Renderer 的锁。
- Renderer 销毁后 Main 自动回收其 Renderer 租约。
- 无签名、未公证 Apple Silicon DMG 自动门禁。
- DMG、Bundle ID、版本、arm64、安装脚本、未签名状态、Manifest 和 SHA-256 校验。
- Browser E2E、i18n、WebUI 测试/构建/许可审计和 Electron Main 测试全绿。

### 正式发布 concurrency：已关闭

PR #13 已实现并验证：

- 同一 PR 的新提交可以取消旧验证。
- PR 验证与正式发布使用不同 group。
- `publish=true` 正式运行不会被后续运行取消。
- GitHub prerelease 与 R2 Preview channel 的 Publish Job 使用固定 group 串行排队。
- 静态脚本对表达式、分组和事件真值表失败关闭。
- 未改变无签名定位、版本、Tag、Manifest、SHA-256 和 `publish=true` 边界。

### Runtime Task / Workspace Lease 协议：已完成

PR #15 已实现并验证：

- Main 权威类型化任务租约协议和状态机。
- Runtime、规范化 Workspace、taskId、显式 `read` / `write` 和可选进程身份。
- acquire 后 Main-only `bind-process`；相同绑定幂等、替换拒绝。
- Runtime Adapter 只能发送 acquire、heartbeat、release、cancel。
- timeout、process-exit、runtime-crash、recover 和 bind-process 为 Main-only。
- eventId 按 Runtime 作用域隔离。
- 重放缓存默认限制为 4,096 条。
- orphaned 失败关闭：Runtime 崩溃后继续占锁，只接受 Main 恢复证据。
- 冲突 acquire 不留下幽灵状态；快照和历史不可由外部修改。
- 契约测试覆盖并发、取消、超时、重放、进程绑定、权限、崩溃和恢复。

### 当前唯一第一优先工程任务

1. Electron Main 实例化单一 `RuntimeTaskLeaseCoordinator`。
2. DeepAgent/DeepCode 分别通过固定 Runtime Adapter 接入真实任务生命周期。
3. 任务启动前 acquire，spawn 后 Main 绑定真实 PID/进程树。
4. Runtime 发送 heartbeat，Main 负责 timeout、process-exit、runtime-crash 和 recover。
5. 正常结束、取消、超时、进程退出、Runtime 重启和异常回收不产生双写窗口。
6. Main 重启后从持久状态和存活进程失败关闭地重建或清理租约。
7. 完成真实 task/PID 生命周期接入前，不启动双 Runtime 同 Workspace E2E。

### 后继工程技术债务

- 双 Runtime 同 Workspace 的真实并发和故障 E2E 未执行。
- 干净 Apple Silicon Mac 安装、Gatekeeper、升级和卸载未执行。
- CLI/Desktop/Hermes/OpenCode 共存未验证。
- 真实用户 Preview 和 P0/P1 清零未完成。

结论：**No-Go**。

---

## 6. 下一执行顺序

```text
1. 将租约绑定真实 Runtime task/PID 生命周期
2. 双 Runtime 同 Workspace 并发与故障 E2E
3. 轮换凭据、确认旧凭据失效
4. 清理 Git 历史并重扫全部 refs
5. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
6. 正式模型任务和真实用户 Preview 测试
7. 清零 P0/P1
8. 按 Go/No-Go 提升 Alpha、Beta、Preview 渠道
```

每次只启动一个可独立验收的工作单元。

---

## 7. 禁止误判

- 不得把代码实现等同于发布门禁完成。
- 不得把无签名 DMG 描述为已签名、公证或 Stable。
- 不得把 Renderer Workspace Lock 测试描述为 Runtime 生命周期闭环。
- 不得把 Runtime Lease 协议测试描述为真实 task/PID 生命周期接入完成。
- 不得把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 不得把 concurrency 或协议阻断关闭描述为 Electron Preview 已发布。
- 不得依赖旧容器或未推送文件；GitHub 远程是唯一事实源。
