# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1、#3、#4、#5、#6、#10、#11、#12、#13 已合入 `develop`  
> concurrency 合并提交：`888696c8fcf86c76003b49d97f48997fccbf4628`  
> 本文是 Electron Preview 专项事实层；冲突处以本文、`00-THREE-PHASE-DELIVERY-STATUS.md`、最新 PLAN 和远程代码为准。

---

## 1. 已完成

### 1.1 工作区多读单写算法

`WorkspaceLockManager` 已实现标准多读单写语义：

- reader-reader 可并行。
- writer-writer 互斥。
- reader-writer 双向互斥。
- 同一任务在无其他 reader 时可升级为 writer。
- 释放后可由后续任务重新获取。

基础算法与测试随 PR #1 合入。

### 1.2 Main IPC 所有权与 Renderer 故障回收

PR #10 将锁从仅依赖 `taskId` 的自愿式 IPC 升级为 Main Process 所有权模型：

- 持有者由 `webContents.id + taskId` 共同标识。
- Renderer 无法释放其他 Renderer 的锁，即使 taskId 相同。
- 每个 Renderer 只注册一次 `destroyed` 监听。
- Renderer 崩溃或窗口销毁后，其跨多个 Workspace 的租约全部自动回收。
- 其他 Renderer 的有效 reader/writer 不受影响。
- 所有者隔离、并发竞争、读写互斥、升级和销毁回收测试已通过。

该子项已通过 Electron Main Vitest、TypeScript 构建、Browser E2E 和 macOS arm64 DMG workflow。

> **边界**：这只完成 P3-06 的 Main IPC 所有权和 Renderer 故障回收，不能等同于真实 Runtime Task / PID 租约协议已经完成。

### 1.3 无签名 Apple Silicon DMG

当前未配置 Apple Developer 账号，Electron Preview 明确采用无签名、未公证 DMG：

- `mac.identity: null`，不自动发现本机证书。
- CI 不依赖 `CSC_*`、`APPLE_ID` 或 Team ID。
- CI 验证 Bundle ID、arm64、版本、安装脚本和确实未签名。
- Manifest 标记 `signed=false`、`notarized=false`。
- 首次启动需按发布说明通过 Finder 右键“打开”。

不得把该制品描述为已签名、公证或 Stable。

### 1.4 安装方式

- DMG 支持标准拖拽安装到 `/Applications`。
- 可选 `Install DeepAgent.command`。
- 保留 quarantine，不自动绕过 Gatekeeper。
- 创建独立 `~/.local/bin/deepagent-desktop`。
- 不覆盖 CLI 的 `deepagent`。

### 1.5 Browser E2E、i18n 与品牌契约

- Browser E2E 在 PR #5、#6、#10、#13 真实通过。
- 覆盖首次 Ticket、非法/失效 Ticket、重放、Cookie Session 和 URL 清理。
- MCP 对外名称统一为 `deepagent-webui-mcp`。
- 旧 Hermes 日志和 Coding Agent 提示已收敛为 DeepAgent。
- changelog 使用独立 `changelog.*` 命名空间。
- 静态 i18n PR 门禁已建立：英文源必须完整，其他语言可按产品规则回退英文。

### 1.6 Electron Preview 自动构建门禁

PR #6 建立两种模式：

1. **PR 验证**：Desktop、版本或 workflow 变更自动在 `macos-15` arm64 runner 构建和验证无签名 DMG，不发布。
2. **正式发布**：仅 `workflow_dispatch`，要求显式 `X.Y.Z-preview.N`、`publish=true` 和对应 Tag 指向当前 Commit。

已通过：

- 全 refs Gitleaks。
- Preview 版本契约。
- WebUI 安装、全量测试、构建和许可证审计。
- Electron Main 测试和 TypeScript 构建。
- Runtime 复用和无签名目标约束。
- DMG 构建、挂载、Bundle ID、版本、arm64 和安装脚本验证。
- Manifest、SHA-256 和 artifact 生成。

### 1.7 正式发布 concurrency 已完成

PR #13 关闭了原顶层统一 `cancel-in-progress: true` 的发布事务风险。

当前契约：

- PR 验证使用稳定的 `validation-<PR number>` group。
- 同一 PR 的新提交可以取消旧验证。
- `workflow_dispatch + publish=true` 使用独立 `publish-run-<run_id>` group，运行中的正式发布不可被后续运行取消。
- 真正修改 GitHub prerelease 和 R2 Preview channel 的 `publish` job 使用固定 `electron-preview-publish` group。
- `queue: max` 使多个正式发布事务串行排队，不互相替换 pending 运行。
- 发布 Job 未设置 `cancel-in-progress: true`。
- concurrency 表达式、固定发布队列、旧 group 消除和事件真值表由 `scripts/check-electron-preview-concurrency.py` 失败关闭。

PR #13 真实 CI：

- WebUI i18n Coverage：成功。
- WebUI Browser E2E：成功。
- Electron concurrency contract：成功。
- WebUI 测试、构建、许可证审计：成功。
- Electron Main、Runtime 约束、无签名 DMG、Bundle ID、arm64、安装器：成功。
- Manifest、SHA-256、artifact：成功。

本次仅验证 PR 路径，没有执行 `publish=true`，没有创建 Tag、Release 或公开 Preview channel。

---

## 2. 尚未完成

### 2.1 当前唯一第一优先：Runtime Task / Workspace Lease 协议

必须先固化协议，不得并行启动 PID 接入或双 Runtime E2E。

协议至少必须定义：

1. **身份**：runtime、workspace、taskId、访问级别、可选 PID/进程树标识。
2. **访问级别**：任务显式声明 `read` 或 `write`，不得由 Renderer/UI 猜测。
3. **事件**：acquire、acquired、denied、heartbeat、release、cancel、timeout、process-exit、runtime-crash、recovered。
4. **状态**：pending、active、releasing、released、expired、orphaned、recovered。
5. **所有权**：Main 是唯一租约协调器，Renderer 与 Runtime 不能绕过 Main 直接改变权威状态。
6. **幂等性**：重复 acquire/release/cancel、事件重放和重连后恢复必须有明确结果。
7. **故障语义**：心跳丢失、超时、进程树退出、Runtime 重启和 Main 重启后的回收规则。
8. **错误语义**：冲突、非法访问级别、未知任务、过期租约、所有者不匹配和恢复失败。
9. **契约测试**：先覆盖状态转换和失败关闭，再进入真实进程接入。

完成证据：

- 类型化协议文件。
- 权威状态机与不变量说明。
- DeepAgent/DeepCode Runtime 适配边界。
- 契约测试覆盖正常、取消、超时、重放、断线和崩溃场景。
- 计划、状态和交接文档更新。

### 2.2 真实 task/PID 生命周期接入

协议完成后继续：

1. DeepAgent Runtime 与 DeepCode Runtime 的真实任务启动、结束、取消、超时和崩溃事件由 Main 协调器强制管理。
2. 租约绑定真实 task/PID，而不是 Renderer 自愿 acquire/release。
3. 处理心跳、超时、进程树退出、Runtime 重启和异常回收。
4. Main 重启后从持久状态和存活进程重建或清理租约。

### 2.3 双 Runtime 真实并发 E2E

在同一 Workspace 验证：

- reader-reader 并行。
- reader-writer 互斥。
- writer-writer 互斥。
- 取消后释放。
- Renderer 销毁后释放。
- Runtime 进程崩溃后释放。
- Main/Runtime 重启后的过期租约回收。
- 一个 Runtime 崩溃不影响另一个 Runtime 或 Electron 窗口。

### 2.4 干净机与外部验收

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
- concurrency 关闭不等于发布门禁完成。
- 完成 Runtime Lease、真实并发、干净机、共存和用户验收后，才允许创建公开 Preview prerelease。

---

## 4. 下一执行顺序

```text
固化 Runtime Task / Workspace Lease 协议
→ Main 绑定真实 task/PID 生命周期
→ 双 Runtime 同 Workspace 并发与故障 E2E
→ 下载 DMG artifact 做干净机验收
→ 验证 CLI/Desktop/Hermes/OpenCode 共存
→ 修复真实环境问题
→ 清零 P0/P1
→ 创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
