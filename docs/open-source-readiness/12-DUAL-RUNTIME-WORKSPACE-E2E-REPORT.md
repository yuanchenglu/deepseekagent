# 双 Runtime 同 Workspace 并发与故障 E2E 报告

> 执行日期：2026-07-29  
> 工程 PR：#19  
> 最终 PR Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`  
> squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`  
> 结论：**该工作单元完成；不代表 Electron Preview 已发布。**

## 1. 验证对象

测试使用生产客户端 `acquireRuntimeTaskLease()` 与 Electron Main `RuntimeTaskSupervisor`，让 DeepAgent 和 DeepCode 通过同一认证 Supervisor 竞争真实规范化 Workspace。

本报告区分：

- 协议/状态机已实现；
- 自动化 E2E 已通过；
- 干净物理 Mac 与真实用户验收尚未执行；
- 公开 Preview 尚未发布。

## 2. 覆盖范围

最终专项 E2E 共 6 个场景，覆盖：

1. reader-reader 并行；
2. reader-writer 双向互斥；
3. writer-writer 互斥；
4. acquire 被拒绝时 spawn 计数保持 0，Workspace 不产生写副作用；
5. 正常完成和用户取消后的租约释放；
6. heartbeat timeout 保持 orphaned 失败关闭，不产生双写窗口；
7. DeepAgent 共享 Agent Bridge crash；
8. DeepCode 子进程 crash；
9. PID 消失与 PID 重用；
10. Main 重启后的可验证恢复；
11. Runtime 重启后的恢复；
12. PID 证据不匹配时保持 orphaned 和 Workspace 锁；
13. acquire 后、PID bind 前 Main 重启时，无 PID orphaned 任务禁止绑定任意新 PID；
14. 原 Runtime 显式 `finish('failed')` 后，无 PID orphaned 任务安全终止并释放；
15. 一个 Runtime 崩溃不破坏另一个 Runtime；
16. 不同 Workspace 不被错误阻塞；
17. 状态快照和持久化证据上传 GitHub Actions artifact。

## 3. 修复的生产缺陷

### 3.1 不可验证任务被静默丢弃

旧实现中，Main 重启后若 PID 消失或指纹不匹配，`restorePersistedTasks()` 会跳过该任务，导致 Workspace 租约被释放。

修复后：

- 不可验证任务恢复为 `orphaned`；
- Workspace 继续持锁；
- 后台 PID 探测不会自动释放 orphaned 任务；
- 有历史 PID 指纹的任务只有在指纹匹配时才能显式恢复。

### 3.2 acquire-before-bind 的永久锁

Review 发现：DeepCode 在 acquire 后、PID bind 前遇到 Main 重启时，持久化任务没有 `process`。它必须保持 fail-closed，但旧客户端也无法完成正常清理。

修复后：

- 无 PID 证据的 orphaned 任务仍禁止绑定或恢复任意新 PID；
- 原 Runtime 可以通过现有 `/finish` 显式确认该尝试已经终止；
- Main 使用 coordinator `process-exit` 终态路径释放 Workspace；
- E2E 证明释放前冲突 Runtime 被阻塞，释放后才能进入。

### 3.3 WebUI 测试竞态

首轮完整 Electron workflow 在 MCU TTS 测试中暴露异步断言竞态：第二次 TTS 请求完成后，测试未等待对应 `audio.enqueue`。

修复后等待目标 `segmentId` 的 enqueue 事件，再执行断言。最终 Head 的 WebUI 全量测试通过；没有通过简单重跑掩盖失败。

## 4. 最终远程证据

### 4.1 Runtime Task Dual Runtime E2E

- Workflow run：`30383776537`
- 结果：success
- 测试：6/6
- Artifact：`8698111868`
- Artifact digest：`sha256:fe7f347e35eb97fe252825b59bef1dc5719cbf56f1e831f49b8090d5827ab6dd`

### 4.2 WebUI Browser E2E

- Workflow run：`30383777443`
- 结果：success

### 4.3 Release Electron Preview 验证链

- Workflow run：`30383776723`
- 结果：success
- 已通过：
  - Electron Preview concurrency contract；
  - 全 Git refs 密钥扫描；
  - WebUI 全量测试和构建；
  - NPM 许可证审计；
  - Electron Main Vitest 和 TypeScript build；
  - Runtime 复用与无签名 Preview 约束；
  - 无签名 Apple Silicon DMG；
  - Bundle ID、版本、arm64 和安装器；
  - Manifest、SHA-256 和 artifact。

Artifacts：

- Release：`8698244717`  
  digest：`sha256:533fb9a30f9c628afb6c692efcd36597aea1f093018abb4a8c586bec483a8ada`
- WebUI tests：`8698204670`  
  digest：`sha256:0637a275963b86bdb06dcfab81e79af749a2899c3ca34b43e283e5ab739b9dd2`
- Secret scan：`8698118512`  
  digest：`sha256:dc9d735b8ad450bcfdb0cf61ae6001913cafec489f69ecb4432880ed3a731537`

Publish Job 在 PR 场景按预期跳过。未创建 Tag、Release 或公开渠道。

## 5. Review 闭环

- Actionable review：1 个 P2；
- 状态：已修复、已回复、已解决；
- 最终未解决 actionable thread：0。

## 6. 剩余门禁

该工作单元完成后，下一唯一合法任务是：

> **轮换所有外部发布、对象存储和服务凭据，并确认旧凭据失效。**

其后才允许执行 Git 历史秘密清理与全 refs 重扫。干净 Apple Silicon Mac、共存、真实模型、真实用户 Preview、P0/P1 和公开发布仍未关闭。
