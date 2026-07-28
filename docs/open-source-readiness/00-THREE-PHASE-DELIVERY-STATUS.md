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
| `develop` 基线 | `e8d0d902294aab71b9f84304c5b79357e7522222`，PR #7、#8 已合入 |
| 当前代码工作分支 | `chatgpt/electron-preview-release-gate` |
| 当前代码 PR | PR #6：`ci: establish automated Electron Preview DMG gate` |
| PR #6 当前 Head | `c4bbfb17bfa2b5b8611993b67e8cf36609996a26` |
| PR #6 规模 | 23 commits，11 changed files |
| 进度/交接文档 | 已合入 `develop` |
| 本地未推送代码 | **无**；当前工作均已存在于 GitHub 远程分支 |

PR #6 的 Head、mergeability 和 review 状态仍可能变化，新会话必须重新读取远程事实。

---

## 2. 总体进度结论

| 阶段 | 代码/工程实施进度 | 发布就绪状态 | 结论 |
|---|---:|---|---|
| 第一阶段：CLI Alpha | 约 90%–95% | **No-Go** | 主体代码完成，外部凭据、历史清理、干净机和真实模型门禁未完成 |
| 第二阶段：WebUI Beta | 约 90% | **No-Go** | 核心功能、Browser E2E、静态 i18n 和当前 WebUI 测试链路已通过；真实环境门禁未完成 |
| 第三阶段：Electron Preview | 约 85% | **No-Go** | 自动无签名 DMG 门禁已真实全绿；PR #6 尚未处理 review、同步 develop 并合入 |

**整体判断：**主体开发已经完成大半，当前重点是合并发布门禁、执行外部安全操作和真实环境验收。三个阶段目前仍全部是 **No-Go**，不得把代码完成度或单次 CI 全绿等同于正式可发布。

---

## 3. 第一阶段：CLI Alpha

### 已完成

- `DEEPAGENT_HOME` 产品目录隔离。
- 安装、更新、回滚和清单驱动卸载主体实现。
- Core-only 制品、渠道/版本 Manifest、SHA-256 契约。
- CLI 主入口、`setup`、`doctor`、更新与卸载路径。
- 开源治理、许可边界和官网安装入口的代码准备。

### 未完成阻断项

1. 轮换对象存储、发布和服务凭据，并确认旧凭据失效。
2. 在凭据轮换后清理 Git 历史中的有效秘密。
3. 对全部 Git refs 重新扫描并达到零有效秘密。
4. 在干净 macOS 15.5 Apple Silicon 环境验证安装、覆盖、升级、失败回滚、显式回滚和两种卸载。
5. 验证 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期变化。
6. 使用至少一个正式支持模型完成真实 Agent 任务。
7. 发布门禁清零 P0/P1。

**阶段结论：**代码主体接近完成，但外部安全与真实环境门禁未完成，CLI Alpha 仍不得提升发布渠道。

---

## 4. 第二阶段：WebUI Beta

### 已完成

- 一次性 Ticket 换取 HttpOnly Session Cookie 的本地认证链路。
- 非法/失效 Ticket、重放、URL 清理和浏览器持久存储边界测试。
- `deepagent webui start/open/status/stop` 生命周期主体。
- 默认 loopback、本地数据目录和端口共存逻辑。
- WebUI 与 CLI 共用 DeepAgent Runtime 的主路径。
- PR #5 的 Browser E2E 已真实通过。
- PR #6 当前 Head 的 Browser E2E、静态 i18n、WebUI 单元测试、构建和许可证审计均已通过。

### 未完成阻断项

- Alpha → Beta 数据升级、失败回滚和干净机生命周期。
- CLI/WebUI/Hermes/OpenCode 共存的真实环境测试。
- 官网和正式 Beta 渠道的发布级验证。
- LAN/公网继续保持非 Beta 承诺，不扩大首版范围。

**阶段结论：**核心自动化门禁已形成，剩余工作集中在迁移、共存和真实环境验收；WebUI Beta 仍是 No-Go。

---

## 5. 第三阶段：Electron Preview

### 已完成

- DeepAgent / DeepCode 双模式架构和模式切换基础。
- Main Process、子进程环境白名单和 Keychain 凭据边界。
- `WorkspaceLockManager` 已修复为多读单写语义。
- Apple Silicon Electron 构建配置。
- 明确采用**无签名、未公证 Preview DMG**，不伪装为 Stable。
- DMG 支持拖拽安装和可选 `Install DeepAgent.command`。
- Desktop CLI 使用独立 `deepagent-desktop`，不覆盖 `deepagent`。
- PR #6 已建立 PR 自动验证与显式正式发布两种模式。

### PR #6 已通过的完整门禁

- 全 refs Gitleaks 扫描。
- Preview 版本契约。
- WebUI 依赖安装、单元测试、构建和许可证审计。
- Electron Main Process 测试与构建。
- Runtime 复用和无签名目标约束。
- 无签名 Apple Silicon DMG 构建。
- DMG、Bundle ID、版本、arm64、安装脚本和未签名状态验证。
- Manifest、SHA-256 和 workflow artifact 生成。
- Browser E2E。
- 静态 i18n Coverage。

### PR #6 当前剩余阻断

1. 未解决 review：正式发布运行不能被后续运行取消；`cancel-in-progress` 应只用于 PR 验证，`workflow_dispatch + publish=true` 必须串行且不可取消正在发布的运行。
2. PR #7、#8 已推进 `develop`，PR #6 需同步最新 `develop` 并重新确认 mergeability。
3. 修复和同步后必须重新等待全部检查通过，不能复用旧 Head 的绿色结论。
4. review thread 处理完毕后才允许 squash 合入 `develop`。

### 合入后仍需完成

- 下载 DMG artifact，在干净 Apple Silicon Mac 安装并首次启动。
- 验证 Gatekeeper、安装、卸载和 CLI/Desktop 共存。
- 执行 Electron 多任务并发、锁回收、双 Runtime 崩溃恢复和后台任务 E2E。
- 完成真实用户 Preview 测试并清零 P0/P1。
- 创建 `preview.N` Tag 后，才允许 `workflow_dispatch(publish=true)`。

**阶段结论：**自动 DMG 发布门禁已全绿，但代码尚未合入且真实环境验收未完成，Electron Preview 仍是 No-Go。

---

## 6. 下一执行顺序

```text
1. 重新读取 PR #6 最新 Head、review threads 和 mergeability
2. 修复 concurrency/cancel-in-progress 规则
3. 同步最新 develop，处理冲突
4. 重新运行并确认 i18n、Browser E2E、Electron DMG 全部通过
5. 回复并解决 review thread
6. squash 合入 develop
7. 更新 00 状态文档、10-ELECTRON-PREVIEW-STATUS.md 和交接文档
8. 执行 CLI Alpha 凭据轮换与 Git 历史清理
9. 执行干净 Mac 生命周期、共存、并发和故障验收
10. 完成真实用户 Preview 与 P0/P1 清零后再提升渠道
```

---

## 7. 禁止误判

- 不得把“已写代码”写成“已通过发布门禁”。
- 不得把 PR #6 当前 Head 全绿写成 PR 已合入或 Electron Preview 已发布。
- 不得把无签名 DMG 写成已签名、公证或 Stable。
- 不得把旧交接文档中的工作区锁缺陷继续当作当前缺陷。
- 不得绕过未解决 review、分支同步或重新运行 CI。
- 不得依赖当前容器、旧工作区或未推送文件；GitHub 远程仓库是唯一事实源。
