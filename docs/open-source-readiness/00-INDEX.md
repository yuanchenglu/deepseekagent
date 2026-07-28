# DeepSeekAgent 开源准备文档集

> 分支：`develop`  
> 状态：三阶段执行基线  
> 当前计划：`三阶段执行计划PLAN.md` v2.7.0  
> 目标：先交付 CLI Alpha，再交付 WebUI Beta，最终交付 DeepAgent / DeepCode 双模式 Electron Preview。

## 文档目录

1. [01-CODE-REVIEW.md](./01-CODE-REVIEW.md) — 当前代码审查结论、风险等级与证据。
2. [02-PRODUCT-ARCHITECTURE.md](./02-PRODUCT-ARCHITECTURE.md) — 产品定位、用户、能力边界与产品分层。
3. [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md) — Runtime、Harness、工具、桌面端、WebUI、任务系统与安全架构。
4. [04-PRD.md](./04-PRD.md) — 完整产品需求文档与开源版本验收标准。
5. [05-TEST-PLAN-AND-CASES.md](./05-TEST-PLAN-AND-CASES.md) — 测试策略、测试矩阵和核心测试用例。
6. [06-FUNCTIONAL-TEST-REPORT.md](./06-FUNCTIONAL-TEST-REPORT.md) — 当前功能验证报告、已验证结论和未执行项。
7. [07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md](./07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md) — 第一阶段：CLI Alpha。
8. [08-PHASE-2-WEBUI-STABLE-BETA.md](./08-PHASE-2-WEBUI-STABLE-BETA.md) — 第二阶段：WebUI Beta。
9. [09-PHASE-3-DUAL-MODE-ELECTRON.md](./09-PHASE-3-DUAL-MODE-ELECTRON.md) — 第三阶段：DeepAgent / DeepCode 双模式 Electron。
10. [10-ELECTRON-PREVIEW-STATUS.md](./10-ELECTRON-PREVIEW-STATUS.md) — Electron Preview 已完成项、当前唯一任务和发布边界。
11. [11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md](./11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md) — Main 权威 Runtime Task / Workspace Lease 协议。
12. [00-THREE-PHASE-DELIVERY-STATUS.md](./00-THREE-PHASE-DELIVERY-STATUS.md) — 三阶段真实进度、远程证据和阻断项。
13. [三阶段执行计划PLAN.md](./三阶段执行计划PLAN.md) — 当前唯一执行顺序、开发规范和 Go/No-Go 规则。
14. [HANDOFF_2026-07-28.md](./HANDOFF_2026-07-28.md) — 可直接复制的新会话交接提示词，覆盖工程继续与对外发帖边界。

原 [07-OPEN-SOURCE-ITERATION-PLAN.md](./07-OPEN-SOURCE-ITERATION-PLAN.md) 仅作历史审计记录，不再是执行依据。

## 当前远程基线

- `develop`：`e0f2f407daa6f273ee4c927934efc2e3b27293a0`
- `master`：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`
- PR #17 已将真实 Runtime task/PID 生命周期合入 `develop`。
- 文档同步分支：`chatgpt/sync-plan-handoff-v2-7`。

## 当前唯一优先级

Runtime Lease 协议和真实 Main/Runtime task/PID 生命周期已经完成。下一工作单元是：

> **双 Runtime 同 Workspace 并发与故障 E2E**

必须验证 reader-reader、reader-writer、writer-writer、取消、timeout、DeepAgent bridge crash、DeepCode 子进程 crash/PID 重用，以及 Main/Runtime 重启恢复。

完成前不得把协议测试、监督器测试或单 Runtime 测试描述为双 Runtime E2E。

## 当前发布结论

- CLI Alpha：No-Go
- WebUI Beta：No-Go
- Electron Preview：No-Go

未创建 Tag、Release 或公开 Preview channel。无签名 DMG 只是候选 artifact，不是已发布产品。

## 决策原则

- 不以功能数量衡量版本完成度，以默认安全、安装成功率、核心闭环和可维护性衡量。
- 不把模型能力当成权限控制、安全控制或一致性保证。
- 不接受“失败后打印 warning 但流程继续”的发布门禁。
- 不接受固定默认密码、弱认证、隐式超级管理员或无签名远程执行。
- 所有核心功能必须具备明确状态机、错误边界、可观测性和可测试性。
- `develop` 是开发分支；`master` 只接收通过发布门禁的版本。
- GitHub 远程是唯一事实源；不得依赖旧容器或未推送文件。
