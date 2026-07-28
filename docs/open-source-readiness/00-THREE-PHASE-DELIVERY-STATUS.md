# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-29  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 发布分支：`master`  
> 说明：总执行顺序以 `三阶段执行计划PLAN.md` v2.7.0 为准；本文只记录稳定的工程/计划合并基线、真实完成情况和阻断项。最新 Head、PR、CI 和 review 必须实时读取。

---

## 1. 已确认远程基线

| 项目 | 已确认事实 |
|---|---|
| PR #15 | Runtime Task / Workspace Lease 协议已合入 |
| PR #17 Head | `aba94fab7b36f9bd140752c455acdd4838bd3835` |
| PR #17 squash merge | `e0f2f407daa6f273ee4c927934efc2e3b27293a0` |
| PR #18 squash merge | `9e26f290c60544fc8a99cff8c31cecfbb8c99fd9`，同步 PLAN v2.7.0、状态和交接 |
| master 快照 | `b3943ac43f0f0f6a1f86f5f2cb9a230527389d91` |
| Browser E2E | PR #17 最终 Head 真实成功 |
| Electron workflow | concurrency、全 refs 密钥扫描、WebUI、许可证、Electron Main、DMG、Manifest、SHA-256、artifact 全部成功 |
| review | PR #17 未解决 review thread 为 0 |
| 发布动作 | Publish Job 在 PR 场景跳过；未创建 Tag、Release 或公开渠道 |
| 本地未推送关键工作 | 无；关键代码和文档均存在 GitHub 远程 |

> 不在本文中把某个 SHA 描述为永久“当前 Head”。新会话必须重新读取 `develop`、`master`、开放 PR、Actions 和 review。

---

## 2. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90%–92% | **No-Go** | Browser E2E 和核心自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 94%–95% | **No-Go** | Runtime 协议和真实 task/PID 生命周期完成；双 Runtime 真实并发、干净机、共存和用户验收未关闭 |

**整体判断**：主体工程约九成以上，项目位于发布收敛后半程。当前不新增非必要功能。

---

## 3. CLI Alpha

### 已完成

- 产品目录隔离。
- Core-only 制品路径。
- Manifest、SHA-256、渠道和版本一致性契约。
- 安装、更新、回滚和清单驱动卸载主体。
- CLI 命令入口、错误边界、治理和许可文档。

### 阻断项

1. 外部凭据轮换与旧凭据失效确认。
2. Git 历史有效秘密清理和全 refs 重扫。
3. 干净 Apple Silicon Mac 生命周期验收。
4. Hermes/OpenCode 共存验证。
5. 正式支持模型的真实 Agent 任务。
6. P0/P1 清零。

结论：**No-Go**。

---

## 4. WebUI Beta

### 已完成

- 一次性 Ticket → HttpOnly Session Cookie。
- 非法、失效、重放 Ticket 和 URL 清理。
- Browser E2E 真实通过。
- WebUI 测试、构建、静态 i18n 和许可证审计。
- `deepagent webui start/open/status/stop` 主体。
- 默认 loopback、独立 PID/日志/端口/数据目录。
- 无固定默认密码和默认 LAN 暴露。

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
- Workspace Lock 多读单写算法。
- Renderer 所有权隔离和销毁自动回收。
- 正式发布 concurrency 隔离和串行事务。
- Runtime Task / Workspace Lease 类型、状态机和 Main-only 监督边界。
- 真实 Main/Runtime task 与 PID 生命周期接入。
- DeepAgent 共享 bridge PID 绑定。
- DeepCode 每回合 acquire-before-spawn 和实际子进程 PID 绑定。
- heartbeat、timeout、process-exit、runtime-crash、Main restart 恢复。
- POSIX/Windows PID 指纹验证。
- orphaned 失败关闭。
- Supervisor Token 子进程隔离。
- WebUI Home 作用域状态隔离。
- stale socket `EPIPE` 重启连接修复。
- 无签名、未公证 Apple Silicon DMG 自动门禁。
- Browser E2E、WebUI、许可证、Electron Main、DMG 和 artifact 全链路成功。

### 当前唯一第一优先任务

**双 Runtime 同 Workspace 并发与故障 E2E**：

- reader-reader；
- reader-writer；
- writer-writer；
- acquire 拒绝不得 spawn；
- 正常完成、取消和 timeout；
- DeepAgent bridge crash；
- DeepCode 子进程 crash/PID 重用；
- Main/Runtime 重启恢复；
- 一个 Runtime 崩溃不影响另一个 Runtime 或无冲突 Workspace。

### 后继阻断项

- 凭据轮换和历史清理。
- 干净 Apple Silicon Mac 安装、Gatekeeper、升级和卸载。
- CLI/Desktop/Hermes/OpenCode 共存。
- 真实用户 Preview 和 P0/P1 清零。

结论：**No-Go**。

---

## 6. 下一执行顺序

```text
1. 双 Runtime 同 Workspace 并发与故障 E2E
2. 轮换凭据并确认旧凭据失效
3. 清理 Git 历史并重扫全部 refs
4. 干净 Mac 验证 CLI/WebUI/Electron 生命周期
5. CLI/Desktop/Hermes/OpenCode 共存
6. 正式模型任务和真实用户 Preview 测试
7. 清零 P0/P1
8. 按 Go/No-Go 提升 Alpha、Beta、Preview 渠道
```

每次只启动一个可独立验收的工作单元。

---

## 7. 对外表述边界

可以说明真实 task/PID 生命周期已合入 `develop`，但不得声称：

- 双 Runtime E2E 已完成；
- Electron Preview 已发布；
- DMG 已签名或公证；
- 任一阶段已达到 Go；
- 凭据、历史、干净机、共存或用户验收已关闭。
