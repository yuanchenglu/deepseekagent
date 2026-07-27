# Electron Preview 继续开发状态

> 更新日期：2026-07-28  
> 基线：PR #1 已合入 `develop`  
> 当前工作分支：`chatgpt/finish-electron-preview`  
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

### 1.2 无签名 Apple Silicon DMG

由于当前不配置 Apple Developer 账号，Electron Preview 明确改为无签名、未公证的 Apple Silicon DMG：

- `mac.identity: null`，禁止自动发现本机证书。
- CI 不再要求 `CSC_*`、`APPLE_ID` 或 Team ID。
- CI 必须验证产物确实未签名，并验证 Bundle ID、arm64 架构和安装脚本。
- Desktop Manifest 明确记录 `signed=false`、`notarized=false` 和首次启动需 Gatekeeper 人工批准。
- Release Notes 明确说明首次启动采用 Finder 右键“打开”。

### 1.3 安装方式

DMG 保留 macOS 标准拖拽安装，同时提供可选的 `Install DeepAgent.command`：

- 将 `DeepAgent.app` 安装到 `/Applications`。
- 保留 macOS quarantine 元数据，不自动绕过 Gatekeeper。
- 在 `~/.local/bin/` 创建独立的 `deepagent-desktop` 启动命令。
- 不覆盖、替换或重定向第一阶段的 `deepagent` CLI。

交接文档原建议创建 `/usr/local/bin/deepagent` 链接会破坏 CLI/Desktop 共存，因此不执行该做法。

## 2. 仍需真实环境执行

以下项目不是当前代码沙箱内可完成的验证：

1. 在 GitHub Actions 手动执行 `Release Electron Preview`，`publish=false`，验证无签名 DMG 构建。
2. 下载 workflow artifact，在干净的 macOS Apple Silicon 环境安装并首次启动。
3. 执行 Electron 多任务真实并发 E2E，确认同一 Workspace 的 reader/writer 行为。
4. 执行浏览器认证 E2E：首次 Ticket、过期、重放、Cookie、服务重启。
5. 完成 CLI Alpha 的干净机安装、升级、回滚、卸载门禁。

## 3. 发布边界

无签名 DMG 仅定位为 **Electron Preview**，不得标记 Stable：

- 不承诺普通双击可直接通过 Gatekeeper。
- 不自动删除 quarantine 属性。
- 不声称已完成 Apple 签名或公证。
- 不将 DMG 直接提升为正式渠道。
- 完成真实 macOS 安装与 E2E 后，才允许发布 Preview prerelease。

## 4. 下一执行顺序

```text
合并本分支
→ 触发 unsigned DMG 构建（publish=false）
→ 下载并做干净机验收
→ 运行 Electron / Browser E2E
→ 修复真实环境发现的问题
→ 使用版本 Tag 重新运行（publish=true）
→ 发布 Electron Preview
```
