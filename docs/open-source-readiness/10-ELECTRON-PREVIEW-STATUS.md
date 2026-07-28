# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1、#3、#4、#5、#6、#10、#11、#12、#13、#15 已合入 `develop`  
> Runtime Lease 协议合并提交：`cb2885ed1a31cf559640ec62d97caa6047a6b1ad`  
> 本文是 Electron Preview 专项事实层；冲突处以最新远程代码、`三阶段执行计划PLAN.md` v2.6.0 和 `00-THREE-PHASE-DELIVERY-STATUS.md` 为准。

---

## 1. 已完成

### 1.1 工作区多读单写算法

`WorkspaceLockManager` 已实现标准语义：

- reader-reader 可并行。
- reader-writer 双向互斥。
- writer-writer 互斥。
- 同一任务在无其他 reader 时可升级为 writer。
- 释放后后续任务可重新获取。

### 1.2 Renderer 所有权与销毁回收

PR #10 将 Renderer IPC 锁升级为 Main Process 所有权模型：

- 持有者由 `webContents.id + taskId` 共同标识。
- Renderer 无法释放其他 Renderer 的锁。
- 每个 Renderer 只注册一次 `destroyed` 监听。
- Renderer 崩溃或窗口销毁后，其跨多个 Workspace 的租约自动回收。
- 其他 Renderer 的有效 reader/writer 不受影响。

该子项已通过 Electron Main Vitest、TypeScript 构建、Browser E2E 和 macOS arm64 DMG workflow。

> 该边界只处理 Renderer 所有权，不能替代真实 Runtime task/PID 生命周期。

### 1.3 无签名 Apple Silicon DMG

当前未配置 Apple Developer 账号，Electron Preview 明确采用无签名、未公证 DMG：

- `mac.identity: null`，不自动发现本机证书。
- CI 不依赖 `CSC_*`、`APPLE_ID` 或 Team ID。
- CI 验证 Bundle ID、arm64、版本、安装脚本和确实未签名。
- Manifest 标记 `signed=false`、`notarized=false`。
- 首次启动需通过 Finder 右键“打开”。

不得把该制品描述为已签名、公证或 Stable。

### 1.4 安装与 CLI 共存

- DMG 支持标准拖拽安装到 `/Applications`。
- 可选 `Install DeepAgent.command`。
- 保留 quarantine，不自动绕过 Gatekeeper。
- 创建独立 `~/.local/bin/deepagent-desktop`。
- 不覆盖 CLI 的 `deepagent`。

### 1.5 Browser E2E、i18n 与品牌契约

- Browser E2E 在 PR #5、#6、#10、#13、#15 真实通过。
- 覆盖首次 Ticket、非法/失效 Ticket、重放、Cookie Session 和 URL 清理。
- MCP 对外名称统一为 `deepagent-webui-mcp`。
- 旧 Hermes 日志和 Coding Agent 提示已收敛为 DeepAgent。
- changelog 使用独立 `changelog.*` 命名空间。
- 静态 i18n 门禁要求英文源完整，其他语言可按运行时规则回退英文。

### 1.6 Electron Preview 自动构建门禁

PR 修改 Desktop、版本或 workflow 时，在 `macos-15` arm64 runner 自动执行：

- 全 refs Gitleaks。
- Preview 版本和 Tag 边界检查。
- WebUI 安装、全量测试、构建和许可证审计。
- Electron Main 测试和 TypeScript 构建。
- Runtime 复用和无签名目标约束。
- DMG 构建、挂载、Bundle ID、版本、arm64 和安装脚本验证。
- Manifest、SHA-256 和 artifact 生成。

正式发布仍只允许：

```text
workflow_dispatch
+ 显式 X.Y.Z-preview.N
+ publish=true
+ 对应 Tag 指向当前 Commit
```

### 1.7 正式发布 concurrency

PR #13 关闭了正式发布被后续运行取消的风险：

- PR 验证使用稳定的 `validation-<PR number>` group。
- 同一 PR 的新提交可以取消旧验证。
- `workflow_dispatch + publish=true` 使用独立正式运行 group，运行中不可被后续运行取消。
- 修改 GitHub prerelease 和 R2 Preview channel 的 Publish Job 使用固定 `electron-preview-publish` group。
- 多个正式发布事务串行排队。
- 发布 Job 未设置 `cancel-in-progress: true`。
- `scripts/check-electron-preview-concurrency.py` 对表达式、分组和事件真值表失败关闭。

PR #13 已真实通过 i18n、Browser E2E 和完整 Electron Main/DMG workflow，但未执行 `publish=true`。

### 1.8 Runtime Task / Workspace Lease 协议

PR #15 固化 Main 权威协议：

#### 身份与访问级别

- Runtime 只能是 `deepagent` 或 `deepcode`。
- Workspace 进入协调器后规范化为绝对路径。
- 唯一任务键为 `(runtime, taskId)`。
- 任务必须显式声明 `read` 或 `write`。
- 进程身份可包含 PID 和进程树标识。

#### 状态机

```text
pending
active
releasing
released
expired
orphaned
recovered
```

核心转换：

```text
acquire:          ∅ → pending → active
bind-process:     active → active(process bound)
release/cancel:   active → releasing → released
timeout:          active → expired
runtime-crash:    active|pending|releasing → orphaned
recover/exit:     orphaned → recovered
```

#### 权限边界

- Runtime Adapter 只允许 acquire、heartbeat、release、cancel。
- bind-process、timeout、process-exit、runtime-crash、recover 只能由可信 Main 监督路径发送。
- 即使通过动态对象向 Adapter 注入监督事件，也返回 `invalid-request`。
- Renderer 和 Runtime 不能绕过 Main 改变权威状态。

#### 幂等与内存边界

- 幂等键为 `(runtime, eventId)`。
- DeepAgent 与 DeepCode 可独立使用相同 eventId。
- 相同事件与载荷返回第一次结果。
- 同一事件携带不同载荷返回 `replay-conflict`。
- 重放缓存默认最多 4,096 条，超限淘汰最旧记录。

#### 故障语义

- 迟到 heartbeat 不复活过期租约。
- Runtime 崩溃后租约进入 orphaned 并继续持锁。
- 其他 Runtime 的冲突任务继续被拒绝。
- 只有 Main 明确 recover 或确认对应 process-exit 才释放 orphaned 锁。
- 冲突 acquire 不留下幽灵 pending 状态。

#### 验证证据

PR #15 最终 Head `b3c2b07e1c8508af10d217b8d0b3581657617639` 已通过：

- Browser E2E。
- Electron Main Vitest，包括 Runtime Lease 契约测试。
- WebUI 全量测试、构建和许可证审计。
- 全 refs Gitleaks、Runtime 约束、无签名 DMG、Bundle ID、arm64 和安装器。
- Manifest、SHA-256 和 artifact。

4 条 Codex review 建议均已实现、回复并解决。

> **边界**：协议与契约测试完成，不等于真实 Runtime task/PID、心跳监督、进程退出或 Main 重启恢复已接入。

---

## 2. 尚未完成

### 2.1 当前唯一第一优先：真实 task/PID 生命周期接入

必须把已固化协议接入真实 Runtime，不得并行启动双 Runtime E2E。

必须完成：

1. Main 实例化单一 `RuntimeTaskLeaseCoordinator`。
2. DeepAgent/DeepCode 分别使用固定 Runtime Adapter。
3. 真实任务启动前 acquire；被拒绝时不得 spawn 任务进程。
4. spawn 成功后由 Main-only `bind-process` 绑定真实 PID/进程树。
5. Runtime 周期性 heartbeat；Main 触发 timeout。
6. Main 根据真实 process-exit、runtime-crash 和 recover 驱动状态机。
7. 正常完成、取消、超时、进程树退出、Runtime 重启和异常回收不产生双写窗口。
8. Main 重启后从持久状态与存活进程重建；无法证明安全时保持 orphaned。
9. Renderer 与 Runtime 无法调用 Main-only 监督事件。
10. 新增真实监督器集成测试。

完成证据：

- Main 真实监督器和两个 Runtime Adapter 接入代码。
- task/PID/进程树、heartbeat、timeout、exit、crash 的集成测试。
- Main 重启持久化与恢复测试。
- Browser E2E 与完整 Electron Main/DMG workflow 真实通过。
- 计划、状态和交接文档更新。

### 2.2 双 Runtime 真实并发 E2E

真实 task/PID 接入后，在同一 Workspace 验证：

- reader-reader 并行。
- reader-writer 互斥。
- writer-writer 互斥。
- 取消后释放。
- timeout 后释放。
- Runtime 进程崩溃后失败关闭与恢复。
- Main/Runtime 重启后的租约重建或回收。
- 一个 Runtime 崩溃不影响另一个 Runtime 或 Electron 窗口。

### 2.3 干净机与外部验收

- 下载 DMG artifact，在干净 Apple Silicon Mac 安装。
- Gatekeeper 首次启动、升级和卸载。
- CLI/Desktop/Hermes/OpenCode 共存。
- 真实用户 Preview 测试和 P0/P1 清零。

---

## 3. 发布边界

无签名 DMG 仅定位为 **Electron Preview**：

- 不承诺普通双击直接通过 Gatekeeper。
- 不删除 quarantine。
- 不声称已签名、公证。
- 不直接提升 Stable。
- concurrency 完成不等于发布门禁完成。
- Runtime Lease 协议完成不等于真实 task/PID 生命周期闭环。
- 完成 Runtime 生命周期、真实并发、干净机、共存和用户验收后，才允许创建公开 Preview prerelease。

---

## 4. 下一执行顺序

```text
Main 绑定真实 Runtime task/PID 生命周期
→ 双 Runtime 同 Workspace 并发与故障 E2E
→ 下载 DMG artifact 做干净机验收
→ 验证 CLI/Desktop/Hermes/OpenCode 共存
→ 修复真实环境问题
→ 清零 P0/P1
→ 创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
