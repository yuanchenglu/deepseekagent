# 技术债务与外部门禁追踪

> 更新日期：2026-07-29  
> 事实源：GitHub 远程代码、Plan、PR、CI 和 review。  
> 禁止记录仅存在于旧容器、stash 或未跟踪工作区的状态。

## 开放项

| 日期 | Work ID 范围 | 描述 | 遗留原因 | 所需本地能力 | 状态 |
|---|---|---|---|---|---|
| 2026-07-29 | SEC-001..007 | 轮换所有外部发布、对象存储和服务凭据，并验证旧凭据失效 | 需要仓库 Owner / 外部平台管理员权限 | GitHub Secrets、Cloudflare、其他 Provider 管理权限；安全本地 Secret 会话 | **BLOCKED / Issue #21 / 当前唯一 Owner Gate** |
| 2026-07-29 | HIST-001..008 | 清理 Git 历史中的有效秘密并重扫全部 refs | 严格依赖凭据轮换和旧凭据失效；涉及不可逆 force push | mirror clone、加密备份、`git filter-repo`、gitleaks、Owner force-push 授权 | BLOCKED BY SEC-007 |
| 2026-07-29 | CLI-001..013 | CLI Alpha 干净机、真实模型、共存、发布和反馈闭环 | 依赖安全 Gate、干净物理 Mac、模型和公开发布授权 | Apple Silicon Mac、模型 Provider、R2/GitHub Release、测试用户 | LOCKED BY HIST-008 |
| 2026-07-29 | WEB-001..011 | WebUI Beta 迁移、生命周期、共存、发布和反馈闭环 | 依赖 Alpha 反馈完成和真实浏览器环境 | 干净 Mac、Browser、真实数据、Beta 用户、发布权限 | LOCKED BY CLI-013 |
| 2026-07-29 | DESK-001..011 | Electron Preview Gatekeeper、双模式、升级回滚、用户测试和发布 | 需要物理 Mac、真实 GUI、用户和无签名 Preview 风险授权 | Apple Silicon Mac、Electron GUI、真实用户、R2/GitHub Release | LOCKED BY WEB-011 |
| 2026-07-29 | STB-001..012 | Apple 签名、公证、Stable 更新链、正式发布和发布后反馈 | 需要 Apple Developer 账号、证书、公证和最终公开授权 | Developer ID、Keychain、notarytool、stapler、正式渠道和用户支持 | LOCKED BY DESK-011 |

## 确定性本地执行包

所有远程环境无法代替 Owner 完成的工作均已映射到固定 Work ID：

- 弱 AI 默认复制提示词：`open-source-readiness/17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md`；
- 逐项执行手册：`open-source-readiness/16-REMAINING-WORK-EXECUTION-RUNBOOK.md`；
- 65 项逐项验收目录：`open-source-readiness/18-WORK-ID-ACCEPTANCE-CATALOG.md`；
- 机器可读依赖图：`open-source-readiness/remaining-work-plan.json`；
- 高权限背景提示词：`open-source-readiness/15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`；
- R2 分阶段验证：`../scripts/owner-gate/verify-r2-credential-rotation.sh --new-only|--old-denial-only`；
- Git 全 refs 非破坏性扫描：`../scripts/owner-gate/audit-all-git-refs.sh`；
- 任务图 validator：`../scripts/validate_remaining_work_plan.py`；
- 自动测试：`../tests/owner-gate/test-owner-gate-kit.sh` 和 `../tests/owner-gate/test_remaining_work_plan.py`；
- CI：`.github/workflows/local-owner-gate-kit-check.yml`；
- 凭据证据模板：`open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md`。

执行入口仍为 Issue #21。SEC-007 PASSED 前不得启动 HIST-001 或任何发布渠道提升。

## 本轮已关闭项

| 日期 | 描述 | 证据 | 状态 |
|---|---|---|---|
| 2026-07-29 | 双 Runtime 同 Workspace 并发与故障 E2E | PR #19；run `30383776537`；6/6 | CLOSED |
| 2026-07-29 | Main 重启时不可验证 PID 被静默丢弃 | PR #19；orphaned fail-closed E2E | CLOSED |
| 2026-07-29 | acquire-before-bind 重启导致无 PID orphaned 永久锁 | PR #19；显式终止清理 E2E；P2 review resolved | CLOSED |
| 2026-07-29 | MCU TTS 第二次 enqueue 异步断言竞态 | 最终 Electron run `30383776723` 全量通过 | CLOSED |
| 2026-07-29 | Tag、Release、Actions 和五个公开渠道缺少可重复远程审计 | PR #23；只读审计 workflow 和 artifact | CLOSED |
| 2026-07-29 | 本地高权限环境缺少统一安全执行提示词和验证工具 | PR #25 merge `f05077ec72b421a299617754120ad94833f5f363` | CLOSED |
| 2026-07-29 | 远程发布审计与并发 Check 自锁、旧失败永久阻断 | PR #26 merge `fd75b2864cdd0cafb406ea5e7d137f8691c78849`；8/8 单测 | CLOSED |
| 2026-07-29 | 剩余计划过度依赖执行 AI 自己判断，容易跳步、状态卡死或误发布 | PR #28 merge `9c8ff198e547bc11b849cd7a7415a8b2138b3ee9`；65 Work IDs；17/17 单测；runs `30420533971` / `30420534026`；3 个 P1 resolved | CLOSED |

## 记录纪律

- Secret 值不得进入本文、Commit、PR、Issue、Actions 日志或聊天。
- 每项必须有远程证据和明确依赖。
- 代码完成不能替代真实环境或发布 Gate。
- 一个 Work ID 未 PASSED，后继任务必须保持 LOCKED。
- 当前状态只能形成一个执行前沿；不得同时解锁多个任务。
- 本地 AI 完成每项后必须把脱敏证据、JSON 状态、Plan、状态和交接重新推回 GitHub。
