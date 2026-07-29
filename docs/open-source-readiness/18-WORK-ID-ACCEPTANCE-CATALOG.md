# 剩余 65 个 Work ID 逐项验收目录

> 用途：防止执行 AI 因 Runbook 使用范围描述而漏掉中间任务。  
> 详细操作步骤：`16-REMAINING-WORK-EXECUTION-RUNBOOK.md`。  
> 依赖和状态：`remaining-work-plan.json`。

| Work ID | 依赖 | 一句话 PASSED 标准 | 必须有的远程证据 |
|---|---|---|---|
| BOOT-001 | 无 | 最新远程 Head、PR、Issue #21、Actions、Tag、Release、Channels 已重新审计 | 审计 run、artifact digest、远程快照 |
| BOOT-002 | BOOT-001 | 安全本地工作区、Secret 隔离、无 shell 回显和无仓库 Secret 文件 | 环境检查清单、权限和脱敏声明 |
| BOOT-003 | BOOT-002 | 65 个 Work ID 执行台账已创建且状态与 JSON 一致 | 台账 PR、最终 Head、CI |
| SEC-001 | BOOT-003 | 所有外部凭据和暴露面均有脱敏清单且无“无法确认” | 凭据盘点表、双人复核 |
| SEC-002 | SEC-001 | 每个需轮换项都有最小权限替代凭据 | scope 清单、脱敏 Token ID、创建时间 |
| SEC-003 | SEC-002 | GitHub 和外部平台所有消费方均切换新凭据 | Secret 名称与更新时间、消费方清单 |
| SEC-004 | SEC-003 | 新凭据完成隔离上传、读回、字节比较、删除和最小权限检查 | 验证脚本证据、退出码、对象已删除 |
| SEC-005 | SEC-004 | 所有旧凭据均已撤销且无消费方仍引用 | 撤销时间、操作者、脱敏 ID |
| SEC-006 | SEC-005 | 每个旧凭据的安全只读请求均认证失败或权限拒绝 | 错误码、UTC 时间、脱敏 ID |
| SEC-007 | SEC-006 | 脱敏证据合入 develop，Issue #21 关闭 | 证据 PR、merge SHA、Issue 关闭记录 |
| HIST-001 | SEC-007 | mirror、加密备份、bundle、refs、fsck、清理前全 refs 扫描齐全 | 摘要、bundle digest、scan digest |
| HIST-002 | HIST-001 | 每个真实 finding 都有精确且不误伤的处理规则 | finding-to-rule 映射、影响清单 |
| HIST-003 | HIST-002 | 隔离副本完成 filter-repo dry run，未写远程 | before/after refs、工具版本、dry-run 报告 |
| HIST-004 | HIST-003 | 重写副本 0 有效秘密、fsck/测试/构建通过、可回滚 | scan、测试、构建、回滚验证 |
| HIST-005 | HIST-004 | Owner 按固定模板授权 force push 和协作者重克隆 | 完整授权文本、UTC 时间 |
| HIST-006 | HIST-005 | 远程目标 branches/tags 与批准 after SHA 一致 | push 日志、远程 ref 对照 |
| HIST-007 | HIST-006 | 从空目录重克隆远程后全 refs 有效秘密为 0 | 远程 scan artifact、fsck、Actions |
| HIST-008 | HIST-007 | 清理报告和协作者恢复说明合入，旧 clone 回污染被明确禁止 | 报告 PR、merge SHA、通知记录 |
| CLI-001 | HIST-008 | Alpha 候选冻结，版本/Head/Tag/workflow/channel/回滚唯一确定 | 候选清单、Tag 触发冲突审计 |
| CLI-002 | CLI-001 | Core Alpha dry run、边界、许可证、checksum、smoke 全通过 | workflow run、release artifact digest |
| CLI-003 | CLI-002 | 干净 Apple Silicon Mac 首次安装和最小启动通过 | 环境、安装命令、退出码、快照 |
| CLI-004 | CLI-003 | 正式支持模型完成预定义真实 Agent 任务 | 模型/任务脱敏记录、结果和日志 |
| CLI-005 | CLI-004 | 正常升级与覆盖安装保持版本和数据一致 | 升级前后版本、数据快照、退出码 |
| CLI-006 | CLI-005 | 故意失败升级触发自动回滚且旧版本可用 | 失败注入、回滚版本、恢复验证 |
| CLI-007 | CLI-006 | 卸载完整且未知用户文件、Hermes/OpenCode 数据不被删除 | 卸载前后文件系统差异 |
| CLI-008 | CLI-007 | CLI 与 Hermes、用户 OpenCode 命令/配置/数据/进程共存 | 共存矩阵、端口/PID/目录证据 |
| CLI-009 | CLI-008 | Alpha 范围开放 P0=0、P1=0 | Bug 列表、关闭 PR、回归结果 |
| CLI-010 | CLI-009 | Owner 按固定模板授权具体 Alpha 版本和渠道 | AUTHORIZE CLI-ALPHA-PUBLISH 文本 |
| CLI-011 | CLI-010 | 不可变制品和 Release 验证后最后提升 alpha channel | Tag、Release、R2 readback、channel |
| CLI-012 | CLI-011 | 从公开渠道重新下载后安装、升级、失败回滚、卸载通过 | 公开 URL、checksum、真实回归报告 |
| CLI-013 | CLI-012 | Alpha 测试周期结束且反馈范围 P0/P1=0 | 用户周期、问题清单、闭环报告 |
| WEB-001 | CLI-013 | Alpha 正常/边界数据迁移到 Beta 无数据丢失 | schema/行数/对象前后对照 |
| WEB-002 | WEB-001 | 故意损坏或不兼容迁移失败后旧数据完整可恢复 | 失败日志、备份和回滚验证 |
| WEB-003 | WEB-002 | 干净机 start/open/status/stop 无残留进程 | 生命周期命令、PID/端口/日志 |
| WEB-004 | WEB-003 | Ticket/Cookie、非法/过期/重放和 URL 清理全部通过 | Browser E2E 与真实浏览器证据 |
| WEB-005 | WEB-004 | CLI/WebUI/Hermes/OpenCode 安装顺序和并发共存通过 | 共存矩阵和目录/进程快照 |
| WEB-006 | WEB-005 | Beta dry run 三类制品、边界、许可证、checksum 全通过 | workflow run、artifact digest |
| WEB-007 | WEB-006 | Beta 范围开放 P0=0、P1=0 | Bug 列表和最终回归 |
| WEB-008 | WEB-007 | Owner 授权具体 Beta 版本、Head、Tag、R2 和 channel | AUTHORIZE WEBUI-BETA-PUBLISH 文本 |
| WEB-009 | WEB-008 | Release 和 R2 readback 成功后最后提升 beta channel | prerelease、objects、manifest、channel |
| WEB-010 | WEB-009 | 公开渠道安装、迁移、升级、失败回滚通过 | 公开回归和 checksum 证据 |
| WEB-011 | WEB-010 | Beta 外部测试周期结束且 P0/P1=0 | 参与者、环境、问题和闭环报告 |
| DESK-001 | WEB-011 | 干净 Mac 下载 unsigned DMG，独立 checksum 与 manifest 一致 | DMG 来源、三方 digest 对照 |
| DESK-002 | DESK-001 | Gatekeeper 右键 Open 路径可用且不要求关闭系统安全 | macOS 版本、交互记录、限制文案 |
| DESK-003 | DESK-002 | DeepAgent/DeepCode 双模式均完成真实任务 | 双模式任务、PID/Runtime 证据 |
| DESK-004 | DESK-003 | 覆盖安装、升级、失败升级、回滚、卸载全部通过 | 各阶段版本/数据/退出码 |
| DESK-005 | DESK-004 | Main/Runtime crash、恢复、orphaned 和 Lease 无双写 | 故障注入、状态快照、日志 |
| DESK-006 | DESK-005 | Desktop 与 CLI/WebUI/Hermes/OpenCode 同机共存 | 完整共存矩阵、端口/PID/目录 |
| DESK-007 | DESK-006 | 受控 Preview 用户完成预定义任务和反馈周期 | 用户数、环境、任务成功率、问题 |
| DESK-008 | DESK-007 | Preview 范围开放 P0=0、P1=0 | Bug 列表、修复和回归 |
| DESK-009 | DESK-008 | Owner 明确接受无签名/未公证风险并授权版本 | AUTHORIZE ELECTRON-PREVIEW-PUBLISH |
| DESK-010 | DESK-009 | DMG/manifest/readback 成功后最后提升 preview channel | prerelease、R2、checksum、channel |
| DESK-011 | DESK-010 | 公开 Preview 回归和反馈闭环完成 | 公开下载回归、用户问题闭环 |
| STB-001 | DESK-011 | Apple Team、签名身份、过期时间、notary 权限均确认 | 脱敏权限清单和责任人 |
| STB-002 | STB-001 | 签名配置、Hardened Runtime、Entitlements、嵌套二进制审计通过 | codesign 配置和审计报告 |
| STB-003 | STB-002 | notarization 和 stapling 成功，Gatekeeper 验证通过 | notary result、stapler、spctl |
| STB-004 | STB-003 | Stable manifest/feed/channel 和回滚链建立 | 更新链设计、签名和故障测试 |
| STB-005 | STB-004 | 干净 Mac Stable 安装、升级、失败回滚、卸载通过 | 真实生命周期报告 |
| STB-006 | STB-005 | CLI/WebUI/Desktop/Hermes/OpenCode/模型全矩阵通过 | 全矩阵报告和 artifacts |
| STB-007 | STB-006 | RC 冻结且开放 P0=0、P1=0 | RC Head、Bug 清单、最终回归 |
| STB-008 | STB-007 | Owner 按完整模板授权 Stable 版本和渠道 | AUTHORIZE STABLE-PUBLISH 文本 |
| STB-009 | STB-008 | 候选合入 master，签名制品发布，最后提升 Stable channel | master SHA、Tag、Release、channel |
| STB-010 | STB-009 | 公开下载、新装、旧版升级、失败回滚和监控通过 | 多机公开回归、监控证据 |
| STB-011 | STB-010 | Stable 用户反馈周期结束，发布回归全部处理 | 用户反馈、回归和问题闭环 |
| STB-012 | STB-011 | Plan/状态/证据/债务/交接一致，全部 65 项 PASSED | 最终审计、develop/master/channel 一致性 |

## 判定规则

- 任一行缺远程证据，状态不能是 PASSED。
- 范围性测试不能替代该行的独立验收。
- Owner 授权任务缺固定格式授权文本时必须 BLOCKED。
- `STB-012` 之前不得宣布整个 Plan 完成。
