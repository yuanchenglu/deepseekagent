# 本地高权限环境：剩余 Plan 一次性执行提示词

> 更新日期：2026-07-29  
> 适用仓库：`yuanchenglu/deepseekagent`  
> 用途：交给具备本地 Git、GitHub、Cloudflare、模型 Provider、Apple Developer、干净 Apple Silicon Mac 和真实发布权限的 AI。  
> 安全原则：**Secret 永不进入 GitHub、日志、Issue、PR、Commit、聊天或公开 artifact。**

## 一、使用方式

将下方完整提示词复制给本地高权限 AI。该 AI 必须从 GitHub 远程重新审计，不得把本文中的 SHA 当作永久最新状态。

```text
@GitHub

你现在接管并持续负责 GitHub 仓库：

  yuanchenglu/deepseekagent

Remote：

  https://github.com/yuanchenglu/deepseekagent.git

你运行在本地高权限环境，具备或可以由 Owner 安全提供以下能力：

- GitHub 仓库、Actions Secrets、Environments 和 Release 管理权限；
- Cloudflare R2 / Pages / DNS 管理权限；
- 模型 Provider 的正式测试凭据；
- Apple Developer 证书、签名、公证和更新链权限；
- 一台可重置或全新用户态的 Apple Silicon Mac；
- CLI、浏览器、Electron、Hermes 和用户 OpenCode 的真实执行环境；
- 必要的真实用户测试组织能力。

# 1. 总目标

严格按照仓库 `docs/open-source-readiness/` 下的当前有效计划，自主、连续、串行完成全部剩余 Work ID、Milestone、Gate、发布准备、CLI Alpha、Alpha 反馈闭环、WebUI Beta、Beta 反馈闭环、Electron Preview、Preview 反馈闭环、Stable 准备、正式 Stable 发布及发布后回归。

不要只处理当前 Owner Gate。完成一个工作单元后立即读取最新远程状态并进入下一个依赖已满足的唯一合法任务，不等待用户发送“继续”。

只有以下情况可以停止：

1. 整个 Plan 全部闭环；
2. 遇到必须由 Owner 作出法律、品牌、收费或不可逆公开发布决定；
3. 缺少真实外部权限且无法由本地环境安全取得；
4. 存在安全风险，继续执行会暴露 Secret 或破坏不可恢复证据。

停止前必须推送全部可保存成果、更新 Plan/状态/证据/技术债务/交接，并给出下一唯一动作。

# 2. 远程是唯一事实源

开始时重新读取：

1. 根目录 `AGENTS.md`；
2. `docs/open-source-readiness/00-INDEX.md`；
3. `docs/open-source-readiness/三阶段执行计划PLAN.md`；
4. `docs/open-source-readiness/00-THREE-PHASE-DELIVERY-STATUS.md`；
5. `07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`；
6. `08-PHASE-2-WEBUI-STABLE-BETA.md`；
7. `09-PHASE-3-DUAL-MODE-ELECTRON.md`；
8. `10-ELECTRON-PREVIEW-STATUS.md`；
9. `11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md`；
10. `12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`；
11. `13-OWNER-CREDENTIAL-ROTATION-GATE.md`；
12. `14-REMOTE-RELEASE-STATE-AUDIT.md`；
13. `15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`；
14. `docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md`；
15. `docs/TECH_DEBT.md`、Bug、测试计划和测试报告；
16. 最近至少 30 个 `develop` Commit；
17. 所有开放 PR、review threads 和 Actions；
18. 所有领先 `develop` 的远程分支；
19. `develop`、`master`、Tags、Releases 和公开渠道；
20. Issue #21 及其最新证据。

重新运行只读发布状态审计：

  gh workflow run remote-release-state-audit.yml --ref develop

并下载、复核 artifact。历史 SHA 和百分比只能作为线索。

# 3. 分支与提交纪律

- 开发分支：`develop`；发布分支：`master`。
- 优先：功能分支 → PR → CI → review → squash merge 到 `develop`。
- 一个独立 Work ID / Gate 对应一个清晰 PR。
- 不得创建超大 PR。
- 直推 `develop` 只作为异常兜底，Commit 必须记录问题原因和技术债务。
- 每个最终 PR Head 必须重新检查 CI 和 actionable review。
- 不删除远程分支、Tag、Release、Actions artifact 或历史证据，除非当前 Work ID 明确要求且已建立备份、审计记录和 Owner 授权。

# 4. 当前唯一合法第一任务：外部凭据轮换

Issue #21 未关闭前，不得重写 Git 历史、创建发布 Tag、发布 Release 或提升 Alpha/Beta/Preview/Stable 渠道。

严格执行：

  docs/open-source-readiness/13-OWNER-CREDENTIAL-ROTATION-GATE.md

## 4.1 凭据盘点

至少审计：

- Repository / Organization Actions Secrets；
- Environment Secrets；
- Dependabot / Codespaces Secrets；
- Cloudflare R2、Pages、DNS；
- GitHub Release、Pages、Packages；
- 模型 Provider；
- 遥测、错误上报、邮件、对象存储和部署账号；
- 本地 `.env`、shell history、CI 日志和历史 artifact；
- Git 全 refs 中曾出现的凭据。

只记录 Provider、用途、权限范围、创建/撤销时间和脱敏 Token ID/末 4 位。永远不要记录 Secret 值。

## 4.2 Cloudflare R2 技术验证

在安全本地 shell 中设置环境变量，不把值写入文件或聊天：

  CF_ACCOUNT_ID
  NEW_CF_R2_ACCESS_KEY_ID
  NEW_CF_R2_SECRET_ACCESS_KEY
  OLD_CF_R2_ACCESS_KEY_ID
  OLD_CF_R2_SECRET_ACCESS_KEY
  EVIDENCE_PATH

运行：

  bash scripts/owner-gate/verify-r2-credential-rotation.sh

脚本必须完成：新凭据隔离上传 → 读回 → 字节比较 → 删除；旧凭据只读请求必须失败。随后人工检查新 Token 权限确为最小范围。

对其他 Provider 执行等价验证。

## 4.3 Gate 证据

复制模板：

  docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md

生成：

  docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md

完成双人复核，确保任何 Secret、Authorization Header、签名 URL 或可还原值都没有进入 GitHub。通过 PR 合入后关闭 Issue #21。

# 5. Git 历史有效秘密清理与全 refs 重扫

只有 Issue #21 已有远程 PASSED 证据后才开始。

## 5.1 清理前证据和备份

1. 创建隔离 mirror clone；
2. 创建离线加密备份和 Git bundle；
3. 记录所有 branches、tags、PR refs 和 commit graph；
4. 执行只读扫描：

   bash scripts/owner-gate/audit-all-git-refs.sh \
     https://github.com/yuanchenglu/deepseekagent.git \
     /安全本地路径/deepseekagent-all-refs-before

5. 确认所有命中对应的旧凭据已经失效；
6. 建立精确 replace-text/path 删除规则，不使用过宽正则。

## 5.2 历史重写

优先使用最新版 `git filter-repo`，只在隔离 mirror 中执行。要求：

- 对每个被修改 ref 记录 before/after SHA；
- 保留签名、Tag、Release、PR 和分支影响清单；
- 验证代码、文档、测试和构建仍可用；
- 重写后运行 `git fsck --full`；
- 重写后再次运行全 refs gitleaks；
- 必须达到 0 个有效秘密命中，误报需有逐项豁免证据；
- force push 前取得 Owner 明确确认；
- 分批更新 refs，保留回滚 bundle；
- 通知所有协作者旧 clone 必须重新 clone，禁止旧分支重新推回。

不得把已失效凭据重新暴露在 replace-text 文件、命令行参数、shell history 或日志中。

## 5.3 远程复核

- 远程重新扫描全部 refs；
- 检查 GitHub secret scanning / Dependabot；
- 检查 Tags、Releases、Actions 和公开渠道未被错误改变；
- 将脱敏清理报告提交到 `docs/open-source-readiness/evidence/`；
- 更新 Plan、状态、技术债务和交接。

# 6. 干净 Apple Silicon Mac：CLI Alpha 生命周期 Gate

在新用户或可证明干净的系统状态执行：

1. 首次安装；
2. `deepagent --version` 和最小启动；
3. 使用正式支持模型完成真实 Agent 任务；
4. 正常升级；
5. 故意失败升级；
6. 自动回滚；
7. 覆盖安装；
8. 卸载；
9. 验证 Manifest、SHA-256、版本和渠道一致；
10. 验证未知用户文件不被删除；
11. 验证 Hermes 和用户 OpenCode 配置、命令、插件、进程和数据不受影响。

记录 OS、芯片、Shell、Python/uv、Node、安装来源、命令退出码、关键日志、文件系统快照和失败证据。任何真实 Secret 必须脱敏。

# 7. CLI / WebUI / Desktop / Hermes / 用户 OpenCode 共存矩阵

至少覆盖：

- 安装顺序的不同排列；
- 同时启动与分别停止；
- 端口、PID、日志、配置、数据目录和全局命令；
- DeepAgent 内置 DeepCode 与用户 OpenCode；
- Workspace reader-reader、reader-writer、writer-writer；
- 一个 Runtime 崩溃时另一个 Runtime；
- 升级、回滚和卸载后共存；
- 不同 Workspace 隔离。

所有 P0/P1 必须修复或由 Plan 允许的正式豁免流程关闭。

# 8. CLI Alpha 发布与反馈闭环

只有 Alpha Gate 全部通过且 Owner 明确授权公开发布后：

1. 冻结发布候选；
2. 生成 Release Notes、Manifest、SHA-256、许可证报告和 SBOM（若 Plan 要求）；
3. dry run；
4. 创建正确 Tag；
5. 构建不可变制品；
6. 验证 GitHub Release 与 R2 读回；
7. 最后提升 Alpha channel；
8. 验证官网下载、安装、升级和回滚；
9. 执行回滚演练；
10. 组织 Alpha 用户测试；
11. 收集问题，清零 P0/P1，更新报告和 Plan。

未经明确授权，不得执行不可逆公开发布或发帖。

# 9. WebUI Beta Gate、发布和反馈闭环

按 Plan 串行完成：

- Alpha → Beta 数据迁移；
- 迁移失败回滚；
- 干净机 WebUI start/open/status/stop；
- Browser 生命周期和认证安全；
- CLI/WebUI/Hermes/OpenCode 共存；
- 正式 Beta 制品、Manifest、Checksum、官网和渠道；
- 发布前回滚演练；
- 外部 Beta 测试周期；
- P0/P1 清零；
- Beta 反馈、测试报告、状态和交接闭环。

# 10. Electron Preview Gate、发布和反馈闭环

在干净 Apple Silicon Mac 执行：

1. DMG 下载与 SHA-256；
2. Gatekeeper 手工批准路径；
3. 安装、首次启动；
4. DeepAgent / DeepCode 双模式；
5. CLI/Desktop/Hermes/OpenCode 共存；
6. 覆盖安装、升级、失败升级、回滚、卸载；
7. Main/Runtime crash、恢复和 Workspace Lease；
8. 无签名、未公证限制说明准确展示；
9. Preview 用户测试；
10. P0/P1 清零；
11. Release Notes、Manifest、渠道和回滚方案一致。

只有 Owner 明确授权时才发布公开 Preview。

# 11. Stable 签名、公证、更新链和正式发布

完成：

- Apple Developer ID Application 签名；
- Hardened Runtime 和 Entitlements 审计；
- Notarization 和 stapling；
- Gatekeeper 无手工绕过验证；
- 签名更新 Manifest / feed / channel；
- 旧版本 → Stable 候选升级；
- 失败升级与回滚；
- 安装、覆盖安装、卸载；
- CLI/WebUI/Desktop/Hermes/OpenCode 全矩阵回归；
- 真实模型任务；
- P0/P1 清零；
- Release Candidate 冻结；
- Owner 最终授权；
- Stable Tag、Release 和 Stable channel；
- 发布后下载、安装、升级、回滚、遥测/错误监控和用户反馈；
- Stable 发布后回归与文档闭环。

# 12. 每个工作单元的强制闭环

每个 Work ID / Gate 必须：

1. 创建独立分支；
2. 开发或执行验证；
3. 保存脱敏证据；
4. 推送远程；
5. 创建 PR；
6. 等待并检查最终 Head CI；
7. 处理所有 actionable review；
8. 合入 `develop`；
9. 重新读取 `develop`；
10. 更新 Plan、状态、阶段文档、测试报告、技术债务、00-INDEX 和交接；
11. 自动进入下一唯一合法任务。

发布进入 `master` 时必须使用 Plan 规定的 PR 和发布 Gate，不得把 `develop` 的工程完成误称为正式发布。

# 13. 最终完成标准

只有以下全部满足才能宣布完成：

- 所有 Work ID、Milestone 和 Gate 关闭；
- 凭据已轮换，旧凭据已验证失效；
- Git 历史有效秘密已清理，全 refs 重扫通过；
- 干净机安装、升级、失败升级、回滚和卸载通过；
- CLI/WebUI/Desktop/Hermes/OpenCode 共存通过；
- 正式支持模型真实任务通过；
- Alpha、Beta、Preview、Stable 及各自反馈周期闭环；
- Apple 签名、公证和正式更新链通过；
- P0/P1 清零或按正式流程豁免；
- 最终 Head CI 和 review 全部关闭；
- Manifest、Checksum、Release Notes、渠道和回滚方案一致；
- `develop` 与 `master` 达到 Plan 规定状态；
- 没有关键成果只存在本地；
- 发布后回归和反馈文档完成。

现在开始。从远程审计和 Issue #21 凭据轮换 Gate 执行，不只输出计划，不等待“继续”。
```

## 二、本地 AI 最小输入清单

Owner 只应通过安全本地渠道提供：

- GitHub CLI 已登录会话；
- Cloudflare 控制台或短期最小权限会话；
- 新旧凭据仅存在于临时环境变量或安全密码管理器；
- Apple Developer 本地 Keychain / CI Secret；
- 模型 Provider 的测试项目与限额；
- 干净 Apple Silicon Mac；
- 是否授权具体公开发布动作的明确指令。

不得把明文凭据复制给远程聊天 AI。

## 三、当前远程执行边界

远程 ChatGPT 环境已经完成所有不需要 Owner Secret、物理 Mac、真实用户和签名权限的前置工作。本文不是对 Gate 的豁免；它是将剩余工作安全、完整地交给具备权限的本地执行环境。
