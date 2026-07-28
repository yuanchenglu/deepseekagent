# Electron Preview 继续开发状态

> 更新日期：2026-07-29  
> 当前代码基线：`develop@e0f2f407daa6f273ee4c927934efc2e3b27293a0`  
> Runtime 生命周期合并：PR #17  
> 本文是 Electron Preview 专项事实层；冲突处以最新远程代码、`三阶段执行计划PLAN.md` v2.7.0 和 `00-THREE-PHASE-DELIVERY-STATUS.md` 为准。

---

## 1. 当前结论

Electron Preview 工程实施约 **94%–95%**，发布结论仍为 **No-Go**。

已完成自动化工程主链路：

- DeepAgent / DeepCode 双模式；
- Renderer Workspace Lock；
- Runtime Task / Workspace Lease 协议；
- 真实 task/PID 生命周期；
- heartbeat、崩溃、退出和 Main 重启恢复；
- Browser E2E；
- WebUI、Electron Main、许可证和无签名 DMG 全链路。

尚未完成真实双 Runtime 同 Workspace E2E、干净机、共存和真实用户验收。

---

## 2. 已完成能力

### 2.1 Workspace Lock 与 Renderer 所有权

- reader-reader 并行；
- reader-writer 双向互斥；
- writer-writer 互斥；
- `webContents.id + taskId` 所有权隔离；
- Renderer 无法释放其他 Renderer 的锁；
- Renderer 销毁后 Main 自动回收其 Renderer 租约。

### 2.2 无签名 Apple Silicon DMG

当前没有 Apple Developer 签名与公证：

- `mac.identity: null`；
- CI 不依赖签名凭据；
- 验证 Bundle ID、版本、arm64、安装器和确实未签名；
- Manifest 明确 `signed=false`、`notarized=false`；
- 首次启动需要 Gatekeeper 人工批准。

不得将制品描述为已签名、公证或 Stable。

### 2.3 正式发布 concurrency

PR #13 已验证：

- 同一 PR 新提交可取消旧验证；
- PR 验证与正式发布分离；
- `publish=true` 正式运行不被后续运行取消；
- GitHub prerelease 与 R2 channel 发布事务串行排队；
- 静态契约脚本失败关闭。

### 2.4 Runtime Lease 协议

PR #15 已完成：

- Main 唯一权威协调器；
- Runtime、Workspace、taskId、`read` / `write` 和进程身份；
- Runtime Adapter 与 Main-only 监督事件隔离；
- `(runtime, eventId)` 幂等；
- 4,096 条有界重放缓存；
- orphaned 失败关闭；
- 冲突、取消、超时、重放、进程绑定、崩溃和恢复契约测试。

### 2.5 真实 task/PID 生命周期

PR #17 已完成：

- Electron Main 持久化、认证的 Runtime Task Supervisor；
- DeepAgent 稳定 session task 绑定共享 Agent Bridge PID；
- DeepCode 每回合 acquire-before-spawn，并绑定真实子进程 PID；
- Runtime heartbeat 和 Main timeout；
- 正常完成、取消、process-exit、runtime-crash、Main shutdown；
- Main 重启先恢复为 orphaned，PID 指纹验证后显式 resume；
- POSIX `ps` 证据和 Windows PowerShell/CIM 证据；
- 同一 Runtime heartbeat 失效时全部活跃任务统一 orphaned；
- Supervisor Token 不进入 Agent、npm、工具和 bridge 后代进程；
- 状态跟随 `webUiHome()`；
- DeepCode 一次性 task 不累计 generation 历史；
- Main 重启后 RPC 强制新连接，避免 stale socket `EPIPE`；
- 非 Desktop 无 Supervisor 时保持 no-op 兼容；Desktop 缺失 Supervisor 时失败关闭。

### 2.6 PR #17 验证证据

最终 Head：`aba94fab7b36f9bd140752c455acdd4838bd3835`

Squash merge：`e0f2f407daa6f273ee4c927934efc2e3b27293a0`

通过：

- Browser E2E；
- Electron concurrency contract；
- 全 Git refs 密钥扫描；
- WebUI 全量测试和构建；
- NPM 许可证审计；
- Electron Main Vitest 和 TypeScript build；
- Runtime 复用与无签名目标；
- DMG、Bundle ID、版本、arm64 和安装器；
- Manifest、SHA-256 和 artifact；
- 未解决 review thread 为 0。

Publish Job 在 PR 场景按预期跳过。

---

## 3. 当前唯一工程任务

### 双 Runtime 同 Workspace 并发与故障 E2E

必须验证：

1. reader-reader 并行。
2. reader-writer 双向互斥。
3. writer-writer 互斥。
4. acquire 拒绝时不得 spawn 或产生写副作用。
5. 正常完成和用户取消后的租约终态。
6. heartbeat timeout 保持失败关闭。
7. DeepAgent bridge crash 后 Runtime 级 orphaned。
8. DeepCode 子进程 crash、PID 消失和 PID 重用。
9. Main 重启后的可验证恢复和不可验证 orphaned。
10. 一个 Runtime 崩溃不影响另一个 Runtime、窗口或无冲突 Workspace。
11. 远程保留可审计日志、状态快照和故障证据。

完成前不得把模拟测试或协议测试描述为双 Runtime E2E。

---

## 4. 后继阻断项

- 轮换发布、对象存储和服务凭据并确认旧凭据失效。
- 清理 Git 历史并重扫全部 refs。
- 在干净 Apple Silicon Mac 下载并安装 DMG artifact。
- 验证 Gatekeeper、升级和卸载。
- 验证 CLI/Desktop/Hermes/OpenCode 共存。
- 真实用户 Preview 测试。
- 清零 P0/P1。

---

## 5. 发布边界

无签名 DMG 只能称为 **Electron Preview candidate artifact**，不能称为已发布 Preview。

只有完成以下事项后，才允许创建公开 prerelease：

```text
双 Runtime 真实 E2E
+ 凭据与历史安全门禁
+ 干净机
+ 共存验证
+ 真实用户验收
+ P0/P1 清零
```

随后才可执行：

```text
创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
