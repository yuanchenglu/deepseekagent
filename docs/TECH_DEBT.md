# 技术债务与外部门禁追踪

> 更新日期：2026-07-29  
> 事实源：GitHub 远程代码、Plan、PR、CI 和 review。  
> 禁止记录仅存在于旧容器、stash 或未跟踪工作区的状态。

## 开放项

| 日期 | 描述 | 遗留原因 | 状态 |
|---|---|---|---|
| 2026-07-29 | 轮换所有外部发布、对象存储和服务凭据，并验证旧凭据失效 | 需要仓库 Owner / 外部平台管理员权限 | **BLOCKED / 当前唯一 Owner Gate** |
| 2026-07-29 | 清理 Git 历史中的有效秘密并重扫全部 refs | 严格依赖凭据轮换和旧凭据失效 | BLOCKED BY CREDENTIAL GATE |
| 2026-07-29 | 干净 Apple Silicon Mac 安装、升级、失败升级、回滚、卸载和 Gatekeeper | 当前环境没有可用的干净物理 Mac | OWNER / PHYSICAL DEVICE GATE |
| 2026-07-29 | CLI、WebUI、Desktop、Hermes 和用户 OpenCode 共存矩阵 | 依赖安全 Gate 和干净机 | PLANNED |
| 2026-07-29 | 真实支持模型和真实用户 Preview | 需要真实凭据、用户和发布候选环境 | OWNER / USER GATE |
| 2026-07-29 | Apple 签名、公证和 Stable 更新链 | 需要 Apple Developer 账号、证书和公证权限 | OWNER GATE |

详细凭据操作清单：`open-source-readiness/13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

## 本轮已关闭项

| 日期 | 描述 | 证据 | 状态 |
|---|---|---|---|
| 2026-07-29 | 双 Runtime 同 Workspace 并发与故障 E2E | PR #19；run `30383776537`；6/6 | CLOSED |
| 2026-07-29 | Main 重启时不可验证 PID 被静默丢弃 | PR #19；orphaned fail-closed E2E | CLOSED |
| 2026-07-29 | acquire-before-bind 重启导致无 PID orphaned 永久锁 | PR #19；显式终止清理 E2E；P2 review resolved | CLOSED |
| 2026-07-29 | MCU TTS 第二次 enqueue 异步断言竞态 | 最终 Electron run `30383776723` 全量通过 | CLOSED |

## 记录纪律

- Secret 值不得进入本文、Commit、PR、Issue、Actions 日志或聊天。
- 每项必须有远程证据和明确依赖。
- 代码完成不能替代真实环境或发布 Gate。
