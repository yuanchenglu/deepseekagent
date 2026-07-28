# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-28  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 说明：阶段范围、验收契约仍以 `07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`、`08-PHASE-2-WEBUI-STABLE-BETA.md`、`09-PHASE-3-DUAL-MODE-ELECTRON.md` 为准；本文只记录真实实施进度、当前阻断项和下一执行顺序。

---

## 1. 远程事实基线

| 项目 | 当前事实 |
|---|---|
| `develop` 基线 | `96c1d47ea03d06bcb4c342bcc7f33d506dd2499b`，PR #5 已合入 |
| 当前代码工作分支 | `chatgpt/electron-preview-release-gate` |
| 当前代码 PR | PR #6：`ci: establish automated Electron Preview DMG gate` |
| PR #6 当前 Head | `4125b418772822e6bf8d6c3ea457b74bbb3cb22d` |
| PR #6 规模 | 15 commits，9 changed files |
| 本次文档分支 | `chatgpt/update-three-phase-progress-2026-07-28` |
| 本地未推送代码 | **无**；当前工作均已存在于 GitHub 远程分支 |

PR #6 的 CI 状态会持续变化，新会话必须重新读取，不得把本文中的瞬时状态当作最终结论。

---

## 2. 总体进度结论

| 阶段 | 代码/工程实施进度 | 发布就绪状态 | 结论 |
|---|---:|---|---|
| 第一阶段：CLI Alpha | 约 90%–95% | **No-Go** | 主体代码完成，外部凭据、历史清理、干净机和真实模型门禁未完成 |
| 第二阶段：WebUI Beta | 约 90% | **No-Go** | 核心功能和 Browser E2E 已完成，仍需清理 CI、升级/共存/迁移和真实环境门禁 |
| 第三阶段：Electron Preview | 约 80% | **No-Go** | 双模式架构、工作区锁、无签名 DMG 构建链路已形成，PR #6 尚未全绿并合入 |

**整体判断：**三阶段的主体工程已经完成大半，当前工作重心已从“继续堆功能”转为“关闭发布契约、CI、真实环境与外部安全门禁”。不能把代码完成度等同于可发布程度；当前三个阶段均仍是 **No-Go**。

---

## 3. 第一阶段：CLI Alpha

### 3.1 已完成

- `DEEPAGENT_HOME` 产品目录隔离。
- 安装、更新、回滚和清单驱动卸载主体实现。
- Core-only 制品、渠道/版本 Manifest、SHA-256 契约。
- CLI 主入口、`setup`、`doctor`、更新与卸载路径。
- 开源治理、许可边界和官网安装入口的代码准备。

### 3.2 未完成阻断项

1. 轮换对象存储、发布和服务凭据，并确认旧凭据失效。
2. 在凭据轮换后清理 Git 历史中的有效秘密。
3. 对全部 Git refs 重新执行密钥扫描并达到零有效秘密。
4. 在干净 macOS 15.5 Apple Silicon 环境验证：安装、同版本覆盖、升级、故意失败升级、自动回滚、显式回滚、`--keep-data` 卸载和完全卸载。
5. 验证 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期变化。
6. 使用至少一个正式支持模型完成真实 Agent 任务。
7. 发布门禁清零 P0/P1。

### 3.3 阶段结论

代码主体接近完成，但 P1-01、P1-02 和真实 VM/模型验收尚未完成，CLI Alpha 仍不得公开提升渠道。

---

## 4. 第二阶段：WebUI Beta

### 4.1 已完成

- 一次性 Ticket 换取 HttpOnly Session Cookie 的本地认证链路。
- 非法/失效 Ticket、重放、URL 清理和浏览器持久存储边界测试。
- `deepagent webui start/open/status/stop` 生命周期主体。
- 默认 loopback、本地数据目录和端口共存逻辑。
- WebUI 与 CLI 共用 DeepAgent Runtime 的主路径。
- WebUI Browser E2E 已在 PR #5 真实通过；PR #6 当前 Head 的 Browser E2E 也已通过。
- NPM 许可证审计和 Beta 发布 workflow 已建立。

### 4.2 当前阻断项

- PR #6 的独立 i18n 门禁仍失败；报告确认只缺英文源 locale 的 3 个 changelog key：
  - `changelog.initial`
  - `changelog.auth`
  - `changelog.electron`
- 仍需验证 Alpha → Beta 数据升级、失败回滚和干净机生命周期。
- 仍需执行 CLI/WebUI/Hermes/OpenCode 共存的真实环境测试。
- LAN/公网访问继续保持非 Beta 承诺，不应为赶进度扩大范围。
- 官网和正式 Beta 渠道仍需发布级验证。

### 4.3 阶段结论

Browser E2E 的核心阻断已解除；剩余工作主要是 CI 契约、迁移、共存和真实环境门禁。WebUI Beta 代码层接近完成，但仍是 No-Go。

---

## 5. 第三阶段：Electron Preview

### 5.1 已完成

- DeepAgent / DeepCode 双模式架构和模式切换基础。
- Main Process、子进程环境白名单和 Keychain 凭据边界。
- `WorkspaceLockManager` 已修复为多读单写语义，旧交接文档中的“写+读未互斥”已过时。
- Apple Silicon Electron 构建配置。
- 当前明确采用**无签名、未公证 Preview DMG**，不伪装为 Stable。
- DMG 内保留拖拽安装和可选 `Install DeepAgent.command`。
- Desktop CLI 使用独立 `deepagent-desktop`，不覆盖第一阶段 `deepagent`。
- PR #6 已把手动 DMG workflow 改造成 PR 自动验证 + 显式正式发布两种模式。
- PR #6 已通过全 refs Gitleaks 扫描、版本契约、依赖安装和 Browser E2E 的阶段性验证。

### 5.2 PR #6 当前状态

- PR：#6，目标分支 `develop`，当前可合并但**不应在 CI 全绿前合入**。
- 当前 Head：`4125b418772822e6bf8d6c3ea457b74bbb3cb22d`。
- Browser E2E：成功。
- WebUI i18n Coverage：失败，根因为 3 个英文 changelog key 缺失。
- Electron Preview DMG：本文快照时仍在执行 WebUI tests，必须重新读取最终结论。
- 未解决 review：发布运行不应被新的运行取消；`cancel-in-progress` 应只用于 PR 验证，正式 `publish=true` 运行应串行且不可被取消。

### 5.3 合入后仍需完成

1. 下载 DMG workflow artifact，在干净 Apple Silicon Mac 安装并首次启动。
2. 验证 Bundle ID、arm64、安装脚本、Gatekeeper 行为和卸载边界。
3. 执行 Electron 多任务真实并发 E2E，验证同 Workspace 多读单写和崩溃后锁回收。
4. 验证两个 Runtime 独立崩溃恢复、模式切换和后台任务持续运行。
5. 完成真实用户 Preview 测试并清零 P0/P1。
6. 创建 `preview.N` Tag 后，才允许显式运行 `workflow_dispatch(publish=true)`。

### 5.4 阶段结论

Electron Preview 已从架构开发进入发布门禁阶段，但 PR #6 尚未全绿，干净机与真实并发测试尚未执行，因此仍是 No-Go。

---

## 6. 下一执行顺序

```text
1. 重新读取 PR #6 最新 Head、CI 和 review threads
2. 补齐 3 个英文 changelog i18n key
3. 修复正式发布运行的 concurrency/cancel-in-progress 规则
4. 等待 Browser E2E、i18n、Electron DMG 全部通过
5. 解决 review thread，squash 合入 develop
6. 更新本文、10-ELECTRON-PREVIEW-STATUS.md 和交接文档
7. 执行 CLI Alpha 外部凭据轮换与 Git 历史清理
8. 执行干净 Mac 的 CLI/WebUI/Electron 生命周期和共存验收
9. 执行 Electron 并发/故障 E2E 与真实用户 Preview
10. 满足各阶段 Go/No-Go 后再提升对应发布渠道
```

---

## 7. 禁止误判

- 不得把“已写代码”写成“已通过发布门禁”。
- 不得把 Browser E2E 通过写成整个 WebUI Beta 已发布。
- 不得把无签名 DMG 写成已签名、公证或 Stable。
- 不得把旧交接文档中的工作区锁缺陷继续当作当前缺陷。
- 不得因 PR 显示 mergeable 就绕过失败 CI 或未解决 review。
- 不得依赖当前容器、旧工作区或未推送文件；GitHub 远程仓库是唯一事实源。
