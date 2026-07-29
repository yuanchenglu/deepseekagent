# Electron Preview 继续开发状态

> 更新日期：2026-07-29  
> 当前代码基线：`develop@f1f9457e0443db74e9aab9ceb0ea28405917db3a`  
> 双 Runtime E2E 合并：PR #19  
> 本文是 Electron Preview 专项事实层；冲突处以最新远程代码、`三阶段执行计划PLAN.md` v2.8.0 和总状态文档为准。

---

## 1. 当前结论

Electron Preview 工程实施约 **95%–96%**，发布结论仍为 **No-Go**。

已完成自动化工程主链路：

- DeepAgent / DeepCode 双模式；
- Renderer Workspace Lock；
- Runtime Task / Workspace Lease 协议；
- 真实 task/PID 生命周期；
- 双 Runtime 同 Workspace 并发与故障 E2E；
- heartbeat、崩溃、PID 复用和 Main/Runtime 重启恢复；
- Browser E2E；
- WebUI、Electron Main、许可证和无签名 DMG 全链路。

尚未完成凭据与历史安全门禁、干净物理 Mac、共存、真实模型和真实用户验收。

---

## 2. 已完成能力

### 2.1 Workspace Lock 与 Renderer 所有权

- reader-reader 并行；
- reader-writer 双向互斥；
- writer-writer 互斥；
- `webContents.id + taskId` 所有权隔离；
- Renderer 无法释放其他 Renderer 的锁；
- Renderer 销毁后 Main 自动回收 Renderer 租约。

### 2.2 无签名 Apple Silicon DMG

- `mac.identity: null`；
- CI 不依赖签名凭据；
- 验证 Bundle ID、版本、arm64、安装器和未签名状态；
- Manifest 明确 `signed=false`、`notarized=false`；
- 首次启动需要 Gatekeeper 人工批准。

不得将制品描述为已签名、公证或 Stable。

### 2.3 正式发布 concurrency

PR #13 已验证 PR 验证与正式发布隔离，`publish=true` 正式运行不被后续运行取消，GitHub prerelease 与 R2 channel 发布事务串行排队。

### 2.4 Runtime Lease 协议

PR #15 已完成 Main 唯一权威协调器、Runtime Adapter/Main-only 监督事件、幂等、有界重放、orphaned 失败关闭和状态机契约。

### 2.5 真实 task/PID 生命周期

PR #17 已完成：

- Electron Main 持久化、认证的 Runtime Task Supervisor；
- DeepAgent session task 绑定共享 Bridge PID；
- DeepCode acquire-before-spawn 并绑定真实 child PID；
- heartbeat、timeout、完成、取消、process-exit、runtime-crash 和 Main shutdown；
- Main 重启后的 PID 指纹验证和显式 resume；
- POSIX 与 Windows 进程证据；
- Runtime 级 orphaned；
- Supervisor Token 子进程隔离；
- `webUiHome()` 状态作用域；
- stale socket `EPIPE` 修复。

### 2.6 双 Runtime 同 Workspace E2E

PR #19 已完成：

- 生产客户端真实竞争同一 Main Supervisor；
- reader-reader、reader-writer、writer-writer；
- acquire 拒绝后零 spawn 和零写副作用；
- 完成、取消、timeout、Bridge/child crash；
- PID 消失、PID 复用、Main/Runtime 重启；
- 不可验证任务持续 orphaned 和持锁；
- acquire-before-bind 无 PID orphaned 的显式终止清理；
- 跨 Runtime / Workspace 故障隔离。

最终证据：

- Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`；
- merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`；
- Runtime E2E：run `30383776537`，6/6；
- Browser：run `30383777443`；
- Electron：run `30383776723`；
- Review：未解决 actionable thread 为 0。

详见 `12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`。

---

## 3. 当前唯一任务

### Owner Gate：外部凭据轮换与旧凭据失效确认

必须由 Owner / 外部平台管理员执行：

1. 盘点所有发布、对象存储和服务凭据；
2. 创建并安装最小权限新凭据；
3. 完成隔离读写验证；
4. 撤销旧凭据；
5. 验证旧凭据认证失败；
6. 提交不含秘密值的证据。

操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

---

## 4. 后继阻断项

- 清理 Git 历史并重扫全部 refs；
- 在干净 Apple Silicon Mac 下载、安装和启动 DMG；
- Gatekeeper、覆盖安装、升级、失败升级、回滚和卸载；
- CLI/Desktop/Hermes/OpenCode 共存；
- 真实模型和真实用户 Preview；
- P0/P1 清零。

---

## 5. 发布边界

无签名 DMG 只能称为 **Electron Preview candidate artifact**，不能称为已发布 Preview。

公开 prerelease 的剩余必要条件：

```text
凭据与历史安全门禁
+ 干净机
+ 共存验证
+ 真实模型与用户验收
+ P0/P1 清零
```

随后才可在 Owner 明确授权后执行：

```text
创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
