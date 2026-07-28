# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-28  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 发布分支：`master`  
> 说明：阶段范围以 `07`、`08`、`09` 计划为准；总执行顺序以 `三阶段执行计划PLAN.md` 为准；本文只记录真实完成情况、阻断项和远程基线。

---

## 1. 远程事实基线

| 项目 | 当前事实 |
|---|---|
| 更新前 develop Head | `1fc31324343c574a9e03bac8e2435f72b474d45a` |
| PR #6 | 已 squash 合入；Electron Preview 自动无签名 DMG 门禁全绿 |
| PR #10 | 已 squash 合入；Workspace Lock Renderer 所有权与销毁回收全绿 |
| PR #11 | 已 squash 合入；Electron 专项状态已同步 |
| Browser E2E | PR #5、#6、#10 真实通过 |
| Electron artifact | PR #6 生成约 118 MB 的 `electron-preview-release` artifact |
| 过期 PR #2 | 已关闭，不合并；包含 171 个被后续 PR 替代的旧文件变更 |
| 本地未推送代码 | **无**；代码和文档均存在于 GitHub 远程 |

新会话必须先读取最新 `develop` Head、最近 commits、开放 PR 和当前 Actions，不得机械沿用本文 SHA。

---

## 2. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 门禁未关闭 |
| WebUI Beta | 约 90% | **No-Go** | Browser E2E 和核心自动化已完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 87%–90% | **No-Go** | 自动 DMG、Main IPC 锁所有权已完成；发布 concurrency、Runtime 租约、真实并发和干净机未关闭 |

**整体判断**：主体工程约九成完成，项目已进入发布收敛阶段。当前重点不是增加功能，而是关闭安全、发布事务、生命周期、迁移、共存、故障恢复和真实用户验收。

---

## 3. CLI Alpha

### 已完成

- `DEEPAGENT_HOME` / `~/.deepagent` 目录隔离。
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
- PR #10：`webContents.id + taskId` 所有权隔离。
- Renderer 不能释放其他 Renderer 的锁。
- Renderer 销毁后 Main 自动回收跨 Workspace 租约。
- 无签名、未公证 Apple Silicon DMG 自动门禁。
- DMG、Bundle ID、版本、arm64、安装脚本、未签名状态、Manifest 和 SHA-256 校验。
- Browser E2E、i18n、WebUI 测试/构建/许可审计和 Electron Main 测试全绿。

### 尚未关闭的工程技术债务

1. `.github/workflows/release-electron-preview.yml` 仍使用：

```yaml
concurrency:
  group: electron-preview-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

PR 验证可以取消，但正式 `workflow_dispatch + publish=true` 必须串行、不可被后续运行取消，避免 GitHub prerelease 与 R2 Preview channel 不一致。

2. Workspace Lock 尚未强制绑定真实 Runtime task/PID 生命周期。
3. 真实任务启动、结束、取消、超时、进程树退出和 Runtime 崩溃仍需 Main Lease 协议。
4. 双 Runtime 同 Workspace 的真实并发和故障 E2E 未执行。

### 外部阻断项

- 干净 Apple Silicon Mac 安装、Gatekeeper 首次启动、升级和卸载。
- CLI/Desktop/Hermes/OpenCode 共存。
- 真实用户 Preview 测试和 P0/P1 清零。
- 满足门禁前不得创建公开 `preview.N` 渠道。

结论：**No-Go**。

---

## 6. 下一执行顺序

```text
1. 修复 Electron release workflow concurrency
2. 固化 Runtime Task / Workspace Lease 协议
3. 将租约绑定真实 task/PID 生命周期
4. 双 Runtime 同 Workspace 并发与故障 E2E
5. 轮换凭据、确认旧凭据失效
6. 清理 Git 历史并重扫全部 refs
7. 干净 Mac 验证 CLI/WebUI/Electron 生命周期与共存
8. 正式模型任务和真实用户 Preview 测试
9. 清零 P0/P1
10. 按 Go/No-Go 提升 Alpha、Beta、Preview 渠道
```

每次只启动一个可独立验收的工作单元。

---

## 7. 禁止误判

- 不得把代码实现等同于发布门禁完成。
- 不得把无签名 DMG 描述为已签名、公证或 Stable。
- 不得把 Main IPC 锁测试描述为 Runtime Lease 闭环。
- 不得把 Browser E2E 通过描述为 WebUI 迁移、共存和正式渠道完成。
- 不得忽略 Electron 正式发布 concurrency 风险。
- 不得依赖旧容器或未推送文件；GitHub 远程是唯一事实源。
