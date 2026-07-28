# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-28  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 说明：阶段范围与验收契约仍以 `07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`、`08-PHASE-2-WEBUI-STABLE-BETA.md`、`09-PHASE-3-DUAL-MODE-ELECTRON.md` 为准；本文记录真实实施进度、当前阻断项和下一执行顺序。

---

## 1. 远程事实基线

| 项目 | 当前事实 |
|---|---|
| Electron 门禁基线 | PR #6 已 squash 合入 `develop`，提交 `0013ba280f705ec786a200c688e9fa867aa502e9` |
| PR #6 验证 Head | `c4bbfb17bfa2b5b8611993b67e8cf36609996a26` |
| PR #6 规模 | 23 commits，11 changed files |
| 自动化结论 | i18n、Browser E2E、完整无签名 Apple Silicon DMG 门禁全部成功 |
| 进度与交接文档 | 已保存到 GitHub 远程；最终状态通过 docs-only PR 更新 |
| 本地未推送代码 | **无**；当前工作均已存在于 GitHub 远程仓库 |

`develop` 在本文之后可能继续产生提交。新会话必须重新读取远程最新 Head，不得将任何 SHA 快照视为永久值。

---

## 2. 总体进度结论

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| 第一阶段：CLI Alpha | 约 90%–95% | **No-Go** | 主体代码完成；外部凭据、历史清理、干净机和真实模型门禁未完成 |
| 第二阶段：WebUI Beta | 约 90% | **No-Go** | 核心功能与主要自动化门禁完成；迁移、共存和真实环境验收未完成 |
| 第三阶段：Electron Preview | 约 85% | **No-Go** | 自动无签名 DMG 门禁已合入并全绿；发布并发缺陷与真实环境验收未完成 |

**整体判断：**项目已从主体功能开发进入发布收敛阶段。下一阶段不应继续扩张功能，而应关闭外部安全、发布事务、干净机、共存、迁移、故障恢复和真实用户验收门禁。三个阶段当前仍均为 **No-Go**。

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
4. 在干净 macOS 15.5 Apple Silicon 环境验证安装、覆盖、升级、故意失败升级、自动/显式回滚和两种卸载。
5. 验证 Hermes 与用户 OpenCode 的命令、进程、配置和数据无非预期变化。
6. 使用至少一个正式支持模型完成真实 Agent 任务。
7. 发布门禁清零 P0/P1。

**阶段结论：**代码主体接近完成，但外部安全与真实环境门禁未完成，CLI Alpha 不得提升发布渠道。

---

## 4. 第二阶段：WebUI Beta

### 已完成

- 一次性 Ticket 换取 HttpOnly Session Cookie 的本地认证链路。
- 非法/失效 Ticket、重放、URL 清理和浏览器持久存储边界测试。
- `deepagent webui start/open/status/stop` 生命周期主体。
- 默认 loopback、本地数据目录和端口共存逻辑。
- WebUI 与 CLI 共用 DeepAgent Runtime 的主路径。
- Browser E2E 已真实通过。
- 静态 i18n、WebUI 单元测试、构建和 NPM 许可证审计已通过。

### 未完成阻断项

- Alpha → Beta 数据升级、失败回滚和干净机生命周期。
- CLI、WebUI、Hermes 和用户 OpenCode 的真实共存测试。
- 官网及正式 Beta 渠道的发布级验证。
- LAN/公网继续保持非 Beta 承诺，不扩大首版范围。

**阶段结论：**核心自动化门禁已形成，剩余工作集中在迁移、共存与真实环境验收；WebUI Beta 仍是 No-Go。

---

## 5. 第三阶段：Electron Preview

### 已完成

- DeepAgent / DeepCode 双模式架构和模式切换基础。
- Main Process、子进程环境白名单和 Keychain 凭据边界。
- `WorkspaceLockManager` 已修复为多读单写语义；旧交接中的“写+读未互斥”已过时。
- Apple Silicon Electron 构建配置。
- 明确采用**无签名、未公证 Preview DMG**，不伪装为 Stable。
- DMG 支持拖拽安装和可选 `Install DeepAgent.command`。
- Desktop CLI 使用独立 `deepagent-desktop`，不覆盖 `deepagent`。
- PR #6 已合入 `develop`，建立 PR 自动验证与显式正式发布两种 workflow 模式。

### 已通过的自动门禁

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

### 已合入但尚未关闭的发布技术债务

`develop` 中 `.github/workflows/release-electron-preview.yml` 当前仍为：

```yaml
concurrency:
  group: electron-preview-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

这会使新的正式发布运行有机会取消正在执行的 `workflow_dispatch + publish=true`。由于发布流程先公开 GitHub prerelease、再提升 R2 Preview channel，被中途取消可能造成两个公开渠道不一致。

正确约束：

- PR 验证可由同一 PR 的新提交取消；
- 正式发布必须串行；
- 正在执行的正式发布不可被后续运行取消；
- 修复必须通过独立功能分支和 PR，并重新运行 Electron workflow。

### 真实环境与发布阻断项

- 下载 DMG artifact，在干净 Apple Silicon Mac 安装并首次启动。
- 验证 Gatekeeper、安装、卸载和 CLI/Desktop 共存。
- 执行 Electron 多任务并发、锁回收、双 Runtime 崩溃恢复和后台任务 E2E。
- 完成真实用户 Preview 测试并清零 P0/P1。
- 创建 `preview.N` Tag 后，才允许 `workflow_dispatch(publish=true)`。

**阶段结论：**自动 DMG 门禁已合入并全绿，但发布事务技术债务和真实环境验收未完成，Electron Preview 仍是 No-Go。

---

## 6. 下一执行顺序

```text
1. 从最新 develop 创建功能分支，修复 Electron workflow 的 concurrency/cancel-in-progress
2. 提 PR，重新确认 i18n、Browser E2E 和 Electron DMG 门禁全绿
3. 解决 review 后合入 develop，并更新 10-ELECTRON-PREVIEW-STATUS.md
4. 执行 CLI Alpha 凭据轮换和 Git 历史清理
5. 对全部 refs 重新进行有效秘密扫描
6. 执行干净 Mac 的 CLI/WebUI/Electron 生命周期与共存验收
7. 执行 Electron 并发、锁回收、双 Runtime 故障恢复 E2E
8. 完成真实模型任务与真实用户 Preview 测试
9. 清零 P0/P1
10. 满足各阶段 Go/No-Go 后再提升对应发布渠道
```

---

## 7. 禁止误判

- 不得把“已写代码”写成“已通过发布门禁”。
- 不得把 PR #6 自动门禁全绿写成 Electron Preview 已发布。
- 不得把无签名 DMG 写成已签名、公证或 Stable。
- 不得忽略已合入的发布并发技术债务。
- 不得把旧交接文档中的工作区锁缺陷继续当作当前缺陷。
- 不得依赖当前容器、旧工作区或未推送文件；GitHub 远程仓库是唯一事实源。
