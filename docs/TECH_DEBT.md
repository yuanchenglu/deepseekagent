# 技术债务与外部门禁追踪

> 更新日期：2026-07-29  
> 事实源：GitHub 远程代码、Plan、PR、CI 和 review。  
> 禁止记录仅存在于旧容器、stash 或未跟踪工作区的状态。

## 开放项

| 日期 | 描述 | 遗留原因 | 所需本地能力 | 状态 |
|---|---|---|---|---|
| 2026-07-29 | 轮换所有外部发布、对象存储和服务凭据，并验证旧凭据失效 | 需要仓库 Owner / 外部平台管理员权限 | GitHub Secrets、Cloudflare、其他 Provider 管理权限；安全本地 Secret 会话 | **BLOCKED / Issue #21 / 当前唯一 Owner Gate** |
| 2026-07-29 | 清理 Git 历史中的有效秘密并重扫全部 refs | 严格依赖凭据轮换和旧凭据失效；涉及不可逆 force push | 本地 mirror clone、加密备份、`git filter-repo`、gitleaks、Owner force-push 授权 | BLOCKED BY CREDENTIAL GATE |
| 2026-07-29 | 干净 Apple Silicon Mac 安装、升级、失败升级、回滚、卸载和 Gatekeeper | 当前远程环境没有可用的干净物理 Mac | 干净 Apple Silicon Mac、重置用户态、浏览器和 Electron GUI | OWNER / PHYSICAL DEVICE GATE |
| 2026-07-29 | CLI、WebUI、Desktop、Hermes 和用户 OpenCode 共存矩阵 | 依赖安全 Gate 和干净机 | 同机多产品真实安装、进程/端口/目录检查、真实 Workspace | PLANNED / LOCAL ENVIRONMENT |
| 2026-07-29 | 正式支持模型和真实用户 Alpha/Beta/Preview | 需要真实凭据、发布候选环境和外部用户 | 模型 Provider、受控测试项目、真实用户组织和反馈渠道 | OWNER / USER GATE |
| 2026-07-29 | Apple 签名、公证和 Stable 更新链 | 需要 Apple Developer 账号、证书和公证权限 | Developer ID、Keychain、notarytool、stapler、正式更新渠道 | OWNER / APPLE GATE |
| 2026-07-29 | Alpha、Beta、Preview、Stable 的不可逆公开发布和发布后反馈闭环 | 需要 Owner 对外发布授权；发布后需真实下载与用户反馈 | GitHub Release、R2/Pages、公开渠道、回滚权限和用户支持 | OWNER RELEASE AUTHORIZATION |

## 本地高权限执行包

所有当前远程环境无法代替 Owner 完成的工作，已形成可直接交给其他本地 AI 的执行包：

- 完整串行提示词：`open-source-readiness/15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`；
- R2 新旧凭据安全验证：`../scripts/owner-gate/verify-r2-credential-rotation.sh`；
- Git 全 refs 非破坏性扫描：`../scripts/owner-gate/audit-all-git-refs.sh`；
- 自动测试：`../tests/owner-gate/test-owner-gate-kit.sh`；
- CI：`.github/workflows/local-owner-gate-kit-check.yml`；
- 凭据证据模板：`open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md`。

执行入口仍为 Issue #21。Issue #21 关闭并有远程 PASSED 证据前，不得执行 Git 历史重写或任何发布渠道提升。

## 本轮已关闭项

| 日期 | 描述 | 证据 | 状态 |
|---|---|---|---|
| 2026-07-29 | 双 Runtime 同 Workspace 并发与故障 E2E | PR #19；run `30383776537`；6/6 | CLOSED |
| 2026-07-29 | Main 重启时不可验证 PID 被静默丢弃 | PR #19；orphaned fail-closed E2E | CLOSED |
| 2026-07-29 | acquire-before-bind 重启导致无 PID orphaned 永久锁 | PR #19；显式终止清理 E2E；P2 review resolved | CLOSED |
| 2026-07-29 | MCU TTS 第二次 enqueue 异步断言竞态 | 最终 Electron run `30383776723` 全量通过 | CLOSED |
| 2026-07-29 | Tag、Release、Actions 和五个公开渠道缺少可重复远程审计 | PR #23；只读审计 workflow 和 artifact | CLOSED |
| 2026-07-29 | 本地高权限环境缺少统一安全执行提示词和验证工具 | 本地高权限执行包 PR；最终 CI/review 以远程为准 | IMPLEMENTED / PENDING MERGE |

## 记录纪律

- Secret 值不得进入本文、Commit、PR、Issue、Actions 日志或聊天。
- 每项必须有远程证据和明确依赖。
- 代码完成不能替代真实环境或发布 Gate。
- 本地 AI 完成每项后必须把脱敏证据、Plan、状态和交接重新推回 GitHub。
