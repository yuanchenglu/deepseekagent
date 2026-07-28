# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1、#3、#4、#5、#6、#10 已合入 `develop`  
> 最新合并提交：`d0b06b0`  
> 本文是 `docs/HANDOFF-DEVELOPER.md` 中 Electron 未完成项的最新状态补充；冲突处以本文为准。

## 1. 已完成

### 1.1 工作区多读单写算法

`WorkspaceLockManager` 已实现标准多读单写语义：

- 多个只读任务可以并行。
- 写任务与其他写任务互斥。
- 写任务与其他只读任务互斥。
- 任务可在没有其他 reader 时将自身读锁升级为写锁。
- 释放工作区锁或释放任务全部锁后，可由后续任务重新获取。

基础算法与单元测试随 PR #1 合入。

### 1.2 Main IPC 所有权与崩溃回收

PR #10 将工作区锁从仅依赖 `taskId` 的自愿式 IPC，升级为 Main Process 强制的 Renderer 所有权模型：

- 锁持有者由 `webContents.id + taskId` 共同标识。
- 一个 Renderer 无法释放另一个 Renderer 的锁，即使双方使用相同 taskId。
- Main 对每个 Renderer 只注册一个 `destroyed` 监听。
- Renderer 崩溃或窗口销毁后，其跨多个 Workspace 的全部租约自动回收。
- 其他 Renderer 的有效 reader/writer 租约不受影响。
- 新增所有者隔离、并发竞争、读写互斥和销毁回收测试。

该子项已通过 Electron Main Vitest、WebUI Browser E2E 和完整 macOS arm64 DMG workflow。

> 边界：这完成的是 P3-06 的 Main IPC 所有权与故障回收子项，不能等同于 Runtime 真实任务协议已强制接入。

### 1.3 无签名 Apple Silicon DMG

由于当前不配置 Apple Developer 账号，Electron Preview 明确采用无签名、未公证的 Apple Silicon DMG：

- `mac.identity: null`，禁止自动发现本机证书。
- CI 不要求 `CSC_*`、`APPLE_ID` 或 Team ID。
- CI 验证产物确实未签名，并验证 Bundle ID、arm64 架构、版本和安装脚本。
- Desktop Manifest 明确记录 `signed=false`、`notarized=false` 和首次启动需 Gatekeeper 人工批准。
- Release Notes 明确说明首次启动采用 Finder 右键“打开”。

### 1.4 安装方式

DMG 保留 macOS 标准拖拽安装，同时提供可选的 `Install DeepAgent.command`：

- 将 `DeepAgent.app` 安装到 `/Applications`。
- 保留 macOS quarantine 元数据，不自动绕过 Gatekeeper。
- 在 `~/.local/bin/` 创建独立的 `deepagent-desktop` 启动命令。
- 不覆盖、替换或重定向第一阶段的 `deepagent` CLI。

交接文档原建议创建 `/usr/local/bin/deepagent` 链接会破坏 CLI/Desktop 共存，因此不执行该做法。

### 1.5 浏览器认证 E2E

WebUI Browser E2E 已建立并在 PR #5、#6、#10 真实通过：

- Chromium Headless、Playwright、loopback Vite Server 和 mock API 全部在 GitHub Actions 运行。
- 首次 Ticket、非法/失效 Ticket、Ticket 重放、Cookie Session 和 URL 清理均有浏览器级覆盖。
- Browser E2E 不依赖物理显示器环境。

### 1.6 Electron Preview 自动构建门禁

PR #6 将 Electron Preview Release workflow 从“仅手动执行”收敛为两种模式：

1. **PR 验证模式**：涉及 Desktop、版本契约或 workflow 的 PR 自动在 `macos-15` arm64 runner 构建并验证无签名 DMG，不发布。
2. **正式发布模式**：仅通过 `workflow_dispatch` 显式输入 `X.Y.Z-preview.N` 和 `publish=true`，并要求对应 Tag 指向当前 Commit。

版本契约：

- Runtime 版本由根目录 `VERSION` 与 `webui/package.json` 共同定义。
- Desktop Preview 版本在构建时写入 `package.json` 与 `package-lock.json`，不长期维护第二套手工版本号。
- Desktop Preview 与 Runtime 必须共享相同的 `X.Y.Z` 基础版本。
- PR 自动验证使用 `<runtime-base>-preview.0`；正式发布使用显式 `preview.N`。

最终门禁已真实完成：

- Git 全 refs 密钥扫描。
- WebUI 安装、全量测试、构建和许可证审计。
- Electron Main 测试与 TypeScript 构建。
- 无签名 arm64 DMG 构建与挂载验证。
- Bundle ID、版本、架构、安装脚本和未签名状态验证。
- Manifest、SHA-256 和 release artifact 生成。

### 1.7 i18n 与品牌契约

PR #6 同步修复了 Hermes → DeepAgent 品牌迁移后的测试与 i18n 契约：

- MCP server 对外名称统一为 `deepagent-webui-mcp`。
- 旧 Hermes 日志断言更新为 DeepAgent 文案。
- Coding Agent 安装失败提示移除旧 Hermes 命名。
- changelog 使用独立 `changelog.*` 命名空间，不再与 `sidebar.changelog` 字符串冲突。
- 新增静态 i18n PR 门禁；英文源必须完整，其他语言允许按产品运行规则回退英文。

## 2. 仍未完成

以下项目不能因算法、IPC 或 CI 测试通过而标记完成：

1. **Runtime 任务协议强制接入**：DeepAgent Runtime 与 DeepCode Runtime 的真实任务启动、结束、取消和崩溃事件必须由 Main 租约协调器强制管理，而不是 Renderer 自愿调用 acquire/release。
2. **进程级租约生命周期**：Main 需要把租约绑定到真实 Runtime task/PID，并处理心跳、超时、取消、进程树退出和 Runtime 崩溃。
3. **双 Runtime 真实并发 E2E**：在同一 Workspace 上验证 reader-reader 并行、reader-writer 互斥、writer-writer 互斥和崩溃回收。
4. **干净 macOS 安装验收**：下载 DMG artifact，在干净 Apple Silicon 环境完成安装、Gatekeeper 首次启动、升级和卸载。
5. **CLI Alpha 干净机门禁**：完成安装、升级、回滚、卸载和 Hermes/OpenCode 共存验证。
6. **真实用户 Preview 测试**：清零 P0/P1 后才能进入公开 Preview 发布。

## 3. 发布边界

无签名 DMG 仅定位为 **Electron Preview**，不得标记 Stable：

- 不承诺普通双击可直接通过 Gatekeeper。
- 不自动删除 quarantine 属性。
- 不声称已完成 Apple 签名或公证。
- 不将 DMG 直接提升为正式渠道。
- 完成真实 macOS 安装与双 Runtime E2E 后，才允许发布 Preview prerelease。

## 4. 下一执行顺序

```text
固化 Runtime Task / Workspace Lease 协议
→ Main 将租约绑定到真实 task/PID 生命周期
→ 双 Runtime 同 Workspace 并发与故障 E2E
→ 下载 DMG artifact 做干净机验收
→ 修复真实环境发现的问题
→ 创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布 Electron Preview
```
