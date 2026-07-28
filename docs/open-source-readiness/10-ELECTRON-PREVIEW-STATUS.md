# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1、#3、#4、#5、#6、#10、#11 已合入 `develop`  
> 更新前最新合并提交：`1fc31324343c574a9e03bac8e2435f72b474d45a`  
> 本文是 Electron Preview 专项事实层；冲突处以本文、`00-THREE-PHASE-DELIVERY-STATUS.md` 和最新远程代码为准。

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

### 1.2 Main IPC 所有权与崩溃回收

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

- Browser E2E 在 PR #5、#6、#10 真实通过。
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

---

## 2. 尚未完成

### 2.1 正式发布 concurrency

当前 `.github/workflows/release-electron-preview.yml` 仍为：

```yaml
concurrency:
  group: electron-preview-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

风险：新的 `workflow_dispatch + publish=true` 运行可能取消正在执行的正式发布。当前发布顺序包含 GitHub prerelease 和 R2 Preview channel 两个公开状态；中途取消可能造成渠道不一致。

正确契约：

- 同一 PR 的新提交可以取消旧的 PR 验证。
- 正式发布必须串行。
- 运行中的正式发布不能被后续运行取消。
- 修复后必须重新通过完整 Electron workflow。

### 2.2 Runtime Task / Workspace Lease 强制接入

必须继续完成：

1. DeepAgent Runtime 与 DeepCode Runtime 的真实任务启动、结束、取消、超时和崩溃事件由 Main 协调器强制管理。
2. 租约绑定真实 task/PID，而不是 Renderer 自愿 acquire/release。
3. 处理心跳、超时、进程树退出、Runtime 重启和异常回收。
4. 明确任务访问级别：read 或 write，并由协议而不是 UI 猜测。

### 2.3 双 Runtime 真实并发 E2E

在同一 Workspace 验证：

- reader-reader 并行。
- reader-writer 互斥。
- writer-writer 互斥。
- 取消后释放。
- Renderer 销毁后释放。
- Runtime 进程崩溃后释放。
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
- 完成 concurrency、Runtime Lease、真实并发、干净机和用户验收后，才允许创建公开 Preview prerelease。

---

## 4. 下一执行顺序

```text
修复 release workflow concurrency
→ 固化 Runtime Task / Workspace Lease 协议
→ Main 绑定真实 task/PID 生命周期
→ 双 Runtime 同 Workspace 并发与故障 E2E
→ 下载 DMG artifact 做干净机验收
→ 修复真实环境问题
→ 清零 P0/P1
→ 创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
