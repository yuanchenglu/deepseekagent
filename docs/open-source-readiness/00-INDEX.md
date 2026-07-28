# DeepSeekAgent 开源准备文档集

> 分支：`develop`  
> 状态：三阶段执行基线  
> 当前计划：`三阶段执行计划PLAN.md` v2.8.0  
> 目标：先交付 CLI Alpha，再交付 WebUI Beta，最终交付 DeepAgent / DeepCode 双模式 Electron Preview。

## 文档目录

1. [01-CODE-REVIEW.md](./01-CODE-REVIEW.md) — 代码审查结论、风险与证据。
2. [02-PRODUCT-ARCHITECTURE.md](./02-PRODUCT-ARCHITECTURE.md) — 产品定位、用户、能力边界与分层。
3. [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md) — Runtime、Harness、工具、桌面端、WebUI、任务与安全架构。
4. [04-PRD.md](./04-PRD.md) — 产品需求和验收标准。
5. [05-TEST-PLAN-AND-CASES.md](./05-TEST-PLAN-AND-CASES.md) — 测试策略、矩阵和用例。
6. [06-FUNCTIONAL-TEST-REPORT.md](./06-FUNCTIONAL-TEST-REPORT.md) — 功能验证与未执行项。
7. [07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md](./07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md) — CLI Alpha。
8. [08-PHASE-2-WEBUI-STABLE-BETA.md](./08-PHASE-2-WEBUI-STABLE-BETA.md) — WebUI Beta。
9. [09-PHASE-3-DUAL-MODE-ELECTRON.md](./09-PHASE-3-DUAL-MODE-ELECTRON.md) — 双模式 Electron。
10. [10-ELECTRON-PREVIEW-STATUS.md](./10-ELECTRON-PREVIEW-STATUS.md) — Electron 专项事实层和发布边界。
11. [11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md](./11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md) — Main 权威 Runtime Task / Workspace Lease 协议。
12. [12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md](./12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md) — 双 Runtime 并发、故障和恢复的最终远程证据。
13. [13-OWNER-CREDENTIAL-ROTATION-GATE.md](./13-OWNER-CREDENTIAL-ROTATION-GATE.md) — Owner 凭据轮换、旧凭据失效和脱敏证据清单。
14. [14-REMOTE-RELEASE-STATE-AUDIT.md](./14-REMOTE-RELEASE-STATE-AUDIT.md) — GitHub Tags、Releases、Actions 和公开渠道的只读远程审计。
15. [00-THREE-PHASE-DELIVERY-STATUS.md](./00-THREE-PHASE-DELIVERY-STATUS.md) — 三阶段真实进度和阻断项。
16. [三阶段执行计划PLAN.md](./三阶段执行计划PLAN.md) — 唯一执行顺序和 Go/No-Go 规则。
17. [HANDOFF_2026-07-28.md](./HANDOFF_2026-07-28.md) — 新会话交接提示词。
18. [evidence/CREDENTIAL-ROTATION-TEMPLATE.md](./evidence/CREDENTIAL-ROTATION-TEMPLATE.md) — Owner Gate 脱敏证据模板。

原 `07-OPEN-SOURCE-ITERATION-PLAN.md` 仅作历史审计记录，不再是执行依据。

## 已确认远程基线

- PR #17：真实 task/PID 生命周期。
- PR #18：PLAN v2.7.0 和交接同步。
- PR #19 Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`。
- PR #19 squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`。
- PR #20：PLAN v2.8.0、状态、E2E 报告和 Owner Gate 同步。
- PR #22：凭据轮换脱敏证据模板。
- Remote release audit run `30386865073`：Tags 0、Releases 0、当前 Active/失败 Actions 0、五个公开渠道均 404；artifact `8699299635`。
- `master` 历史快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。
- 最新 Head、开放 PR、Actions、Tag、Release 和渠道必须通过 `14-REMOTE-RELEASE-STATE-AUDIT.md` 或等价实时审计重新确认。

## 当前唯一优先级

双 Runtime E2E 和远程发布状态审计已完成。当前唯一任务：

> **Owner Gate：轮换外部凭据并确认旧凭据失效**

操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。  
证据模板：`evidence/CREDENTIAL-ROTATION-TEMPLATE.md`。

完成前不得启动 Git 历史重写或提升任何发布渠道。

## 当前发布结论

- CLI Alpha：No-Go
- WebUI Beta：No-Go
- Electron Preview：No-Go

远程审计未发现 Tag 或 GitHub Release；Alpha、Beta、Core Stable、Electron Preview 和 Electron Stable 五个公开渠道均返回 HTTP 404。无签名 DMG 是候选 artifact，不是已发布产品。

## 决策原则

- 代码实现、自动化通过、真实环境验收和公开发布必须严格区分。
- 不把模型能力当作权限、安全或一致性保证。
- 发布门禁必须失败关闭。
- 核心功能必须有状态机、错误边界、可观测性和测试证据。
- `develop` 是开发分支；`master` 只接收通过发布门禁的版本。
- GitHub 远程是唯一事实源。
