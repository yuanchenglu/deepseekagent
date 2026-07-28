# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1、#3、#4、#5 已合入 `develop`  
> 当前工作分支：`chatgpt/electron-preview-release-gate`  
> 本文是 `docs/HANDOFF-DEVELOPER.md` 中 Electron 未完成项的最新状态补充；冲突处以本文为准。

## 1. 已完成

### 1.1 工作区多读单写锁

`WorkspaceLockManager` 已修复为标准多读单写语义：

- 多个只读任务可以并行。
- 写任务与其他写任务互斥。
- 写任务与其他只读任务互斥。
- 任务可在没有其他 reader 时将自身读锁升级为写锁。
- 释放工作区锁或释放任务全部锁后，可由后续任务重新获取。

修复及单元测试已随 PR #1 合入 `develop`。

### 1.2 无签名 Apple Silicon DMG 配置

由于当前不配置 Apple Developer 账号，Electron Preview 明确采用无签名、未公证的 Apple Silicon DMG：

- `mac.identity: null`，禁止自动发现本机证书。
- CI 不要求 `CSC_*`、`APPLE_ID` 或 Team ID。
- CI 验证产物确实未签名，并验证 Bundle ID、arm64 架构和安装脚本。
- Desktop Manifest 明确记录 `signed=false`、`notarized=false` 和首次启动需 Gatekeeper 人工批准。
- Release Notes 明确说明首次启动采用 Finder 右键“打开”。

### 1.3 安装方式

DMG 保留 macOS 标准拖拽安装，同时提供可选的 `Install DeepAgent.command`：

- 将 `DeepAgent.app` 安装到 `/Applications`。
- 保留 macOS quarantine 元数据，不自动绕过 Gatekeeper。
- 在 `~/.local/bin/` 创建独立的 `deepagent-desktop` 启动命令。
- 不覆盖、替换或重定向第一阶段的 `deepagent` CLI。

交接文档原建议创建 `/usr/local/bin/deepagent` 链接会破坏 CLI/Desktop 共存，因此不执行该做法。

### 1.4 浏览器认证 E2E

WebUI Browser E2E 已建立并在 PR #5 真实通过：

- Chromium Headless、Playwright、loopback Vite Server 和 mock API 全部在 GitHub Actions 运行。
- 首次 Ticket、非法/失效 Ticket、Ticket 重放、Cookie Session 和 URL 清理均有浏览器级覆盖。
- Browser E2E 不再依赖物理显示器环境。

### 1.5 Electron Preview 自动构建门禁

Electron Preview Release workflow 已从“仅手动执行”收敛为两种模式：

1. **PR 验证模式**：涉及 Desktop、版本契约或 workflow 的 PR 自动在 `macos-15` arm64 runner 构建并验证无签名 DMG，不发布。
2. **正式发布模式**：仅通过 `workflow_dispatch` 显式输入 `X.Y.Z-preview.N` 和 `publish=true`，并要求对应 Tag 指向当前 Commit。

版本契约调整为：

- Runtime 版本继续由根目录 `VERSION` 与 `webui/package.json` 共同定义。
- Desktop Preview 版本在构建时写入 `package.json` 与 `package-lock.json`，无需长期维护第二套手工版本号。
- Desktop Preview 与 Runtime 必须共享相同的 `X.Y.Z` 基础版本。
- PR 自动验证使用 `<runtime-base>-preview.0`；正式发布使用显式 `preview.N`。

## 2. 仍需真实环境执行

以下项目仍不能仅靠代码审查判定完成：

1. Electron Preview 自动 DMG workflow 必须在本分支 PR 中真实通过。
2. 下载 DMG workflow artifact，在干净的 macOS Apple Silicon 环境安装并首次启动。
3. 执行 Electron 多任务真实并发 E2E，确认同一 Workspace 的 reader/writer 行为。
4. 完成 CLI Alpha 的干净机安装、升级、回滚、卸载门禁。
5. 完成真实用户 Preview 测试并清零 P0/P1。

## 3. 发布边界

无签名 DMG 仅定位为 **Electron Preview**，不得标记 Stable：

- 不承诺普通双击可直接通过 Gatekeeper。
- 不自动删除 quarantine 属性。
- 不声称已完成 Apple 签名或公证。
- 不将 DMG 直接提升为正式渠道。
- 完成真实 macOS 安装与 E2E 后，才允许发布 Preview prerelease。

## 4. 下一执行顺序

```text
Electron Preview PR 自动构建通过
→ 下载 artifact 做干净机验收
→ 运行 Electron 多任务并发 E2E
→ 修复真实环境发现的问题
→ 创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布 Electron Preview
```
