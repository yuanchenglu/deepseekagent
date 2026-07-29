# DeepSeekAgent 开源准备文档集

> 分支：`develop`  
> 状态：三阶段执行基线  
> 当前计划：`三阶段执行计划PLAN.md` v2.8.0  
> 剩余工作执行规范：65 项机器可读任务图 + 确定性 Runbook + 逐项验收目录  
> 目标：先交付 CLI Alpha，再交付 WebUI Beta，再交付 Electron Preview，最终完成签名、公证和 Stable 闭环。

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
15. [15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md](./15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md) — 本地高权限 AI 的完整背景和安全边界。
16. [16-REMAINING-WORK-EXECUTION-RUNBOOK.md](./16-REMAINING-WORK-EXECUTION-RUNBOOK.md) — 每个阶段的输入、命令、通过条件、失败分支、证据和下一任务。
17. [17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md](./17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md) — 默认交给较弱执行 AI 的复制即执行提示词，禁止自由跳步。
18. [18-WORK-ID-ACCEPTANCE-CATALOG.md](./18-WORK-ID-ACCEPTANCE-CATALOG.md) — 全部 65 个 Work ID 的逐项依赖、PASSED 标准和强制远程证据。
19. [remaining-work-plan.json](./remaining-work-plan.json) — 机器可读 Work ID、order、depends_on、executor、不可逆授权和持久状态图。
20. [00-THREE-PHASE-DELIVERY-STATUS.md](./00-THREE-PHASE-DELIVERY-STATUS.md) — 三阶段真实进度和阻断项。
21. [三阶段执行计划PLAN.md](./三阶段执行计划PLAN.md) — 总体依赖和 Go/No-Go 规则。
22. [HANDOFF_2026-07-28.md](./HANDOFF_2026-07-28.md) — 新会话交接和远程保存状态。
23. [evidence/CREDENTIAL-ROTATION-TEMPLATE.md](./evidence/CREDENTIAL-ROTATION-TEMPLATE.md) — Owner Gate 脱敏证据模板。

## 给不同能力 AI 的入口

### 默认入口：能力较弱或上下文易丢失的 AI

完整复制：

`17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md`

该 AI 必须同时使用：

- `16-REMAINING-WORK-EXECUTION-RUNBOOK.md`；
- `18-WORK-ID-ACCEPTANCE-CATALOG.md`；
- `remaining-work-plan.json`；
- CI validator。

### 能力较强、具备完整本地权限的 AI

可先读 `15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`，但实际任务选择、状态推进和验收仍必须服从 `16`、`18` 和 JSON 任务图。

## 本地工具与自动验证

- `scripts/owner-gate/verify-r2-credential-rotation.sh --new-only` — SEC-004 新凭据隔离上传、读回、比较和删除；
- `scripts/owner-gate/verify-r2-credential-rotation.sh --old-denial-only` — SEC-005 撤销后执行 SEC-006 旧凭据只读拒绝验证；
- `scripts/owner-gate/audit-all-git-refs.sh` — mirror clone + 全 refs 非破坏性 gitleaks 扫描；
- `scripts/validate_remaining_work_plan.py` — 检查 65 项数量、ID/order、依赖、无循环、唯一状态前沿、状态证据、不可逆授权、验收目录和提示词护栏；
- `tests/owner-gate/test-owner-gate-kit.sh` — 分阶段凭据验证、Secret 不泄漏和辅助脚本烟测；
- `tests/owner-gate/test_remaining_work_plan.py` — 17 项任务图、持久状态和防跳步规则测试；
- `.github/workflows/local-owner-gate-kit-check.yml` — PR/develop 自动执行全部校验。

原 `07-OPEN-SOURCE-ITERATION-PLAN.md` 仅作历史审计记录，不再是执行依据。

## 已确认远程基线

- PR #17：真实 task/PID 生命周期。
- PR #18：PLAN v2.7.0 和交接同步。
- PR #19 Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`。
- PR #19 squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`。
- PR #20：PLAN v2.8.0、状态、E2E 报告和 Owner Gate 同步。
- PR #22：凭据轮换脱敏证据模板。
- PR #23/#24：只读远程发布状态审计和合并后复核。
- PR #25 squash merge：`f05077ec72b421a299617754120ad94833f5f363`，本地高权限提示词、安全脚本、测试和 CI。
- PR #26 squash merge：`fd75b2864cdd0cafb406ea5e7d137f8691c78849`，修复审计并发自锁和旧失败永久阻断。
- PR #27 squash merge：`16baa7ab7917e8624f4952fcd05db13a4acc37df`，Owner Gate 和总状态正式公开本地执行入口。
- PR #28 squash merge：`9c8ff198e547bc11b849cd7a7415a8b2138b3ee9`，65 项确定性任务图、弱 AI 提示词、逐项验收目录、可推进状态机和分阶段 R2 验证；runs `30420533971` / `30420534026` success；3 个 P1 resolved。
- `master` 历史快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。
- 最新 Head、开放 PR、Actions、Tag、Release 和渠道必须通过实时远程审计重新确认。

## 当前唯一优先级

双 Runtime E2E、远程发布状态审计、本地高权限执行准备和弱 AI 防错体系均已完成。新执行会话先完成 BOOT-001/002/003，然后唯一业务 Gate 是：

> **Owner Gate：轮换外部凭据并确认旧凭据失效**

操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。  
证据模板：`evidence/CREDENTIAL-ROTATION-TEMPLATE.md`。  
弱 AI 默认入口：`17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md`。  
逐项执行手册：`16-REMAINING-WORK-EXECUTION-RUNBOOK.md`。  
逐项验收目录：`18-WORK-ID-ACCEPTANCE-CATALOG.md`。

凭据 Gate 完成前不得启动 Git 历史重写或提升任何发布渠道。

## 当前发布结论

- CLI Alpha：No-Go
- WebUI Beta：No-Go
- Electron Preview：No-Go
- Stable：No-Go

远程审计未发现 Tag 或 GitHub Release；Alpha、Beta、Core Stable、Electron Preview 和 Electron Stable 五个公开渠道均返回 HTTP 404。无签名 DMG 是候选 artifact，不是已发布产品。

## 决策原则

- 一次只执行一个 Work ID；
- 依赖没有 PASSED 远程证据就保持 LOCKED；
- 持久状态只允许一个 READY/IN_PROGRESS/BLOCKED/FAILED 前沿；
- PASSED 必须包含 evidence 文件、PR、最终 Head 和 merge SHA；
- 代码实现、自动化通过、真实环境验收、公开发布和反馈闭环严格区分；
- 不把模型能力当作权限、安全或一致性保证；
- 发布门禁必须失败关闭；
- 不可逆动作必须有固定格式 Owner 授权；
- 任何 Tag 推送前必须检查跨 Workflow 触发冲突；
- `develop` 是开发分支；`master` 只接收通过发布门禁的版本；
- GitHub 远程是唯一事实源。
