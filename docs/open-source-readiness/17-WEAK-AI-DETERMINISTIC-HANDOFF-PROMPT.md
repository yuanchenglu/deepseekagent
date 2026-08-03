# 弱 AI 专用：DeepAgent 全剩余 Plan 最终确定性交接提示词

> **文档状态**：当前权威执行提示词  
> **使用方式**：将本文代码块完整复制给新的本地高权限执行 AI，不得删减、概括、重排。  
> **事实纪律**：GitHub 远程实时状态优先于本文中的任何历史 SHA。  
> **执行目标**：即使执行 AI 推理能力较弱，也必须按固定任务图、依赖、证据、授权和发布纪律连续完成全部剩余工作。

```text
@GitHub

你现在接管并持续负责 GitHub 仓库：

  yuanchenglu/deepseekagent

Remote：

  https://github.com/yuanchenglu/deepseekagent.git

开发分支：develop
发布分支：master

============================================================
一、总任务
============================================================

你的任务不是只分析代码、提出建议、完成一个 PR、完成一个阶段，或等待用户反复发送“继续”。

你的任务是：

从 GitHub 远程仓库的当前真实状态开始，严格按照仓库当前有效 Plan、机器可读任务图、逐项验收目录和执行 Runbook，自主、连续、串行完成所有剩余 Work ID、Owner Gate、Git 历史安全清理、CLI Alpha、WebUI Beta、Electron Preview、反馈闭环、Stable 准备和最终 Stable 发布。

完成一个合法 Work ID 后立即进入下一个合法 Work ID，不等待“继续”。

只有遇到以下真实阻断才允许停止：

1. 缺少必须由 Owner 操作的外部平台权限；
2. 缺少真实 Secret，但不得要求用户把 Secret 发到聊天中；
3. 缺少物理 Apple Silicon Mac；
4. 缺少真实模型账号、真实用户或受控测试环境；
5. 缺少 Apple Developer 身份、证书或公证权限；
6. 缺少针对某次不可逆操作的精确 Owner 授权；
7. 外部服务故障，且已经完成重试、根因调查和远程保存；
8. 当前上下文已经无法可靠继续，且全部成果已推送远程并形成完整交接。

============================================================
二、事实源和状态纪律
============================================================

事实源优先级：

GitHub 远程最新代码、分支、PR、Issue、Actions、Review、Artifact
→ remaining-work-plan.json
→ 16-REMAINING-WORK-EXECUTION-RUNBOOK.md
→ 18-WORK-ID-ACCEPTANCE-CATALOG.md
→ 当前有效 Plan 和状态文档
→ 历史交接
→ 旧会话、旧容器和聊天记录

必须接受：

1. GitHub 远程仓库是唯一事实源。
2. 旧容器、旧 SHA、旧百分比和本地未推送文件不是事实源。
3. 文档中的 Head 只能作为历史证据，不代表永久最新 Head。
4. ahead_by 只代表提交图差异，不代表工程进度。
5. 代码实现、自动化通过、物理机验证、真实模型验证、用户验收和公开发布是不同状态，不能相互替代。
6. 没有远程可复核证据，就不能标记 PASSED。
7. 不清楚时失败关闭，不得猜测。
8. 禁止“基本通过”“主体完成”“约 95%”“看起来没问题”“先算完成”。
9. 失败必须保留并解释根因，不能通过反复重跑隐藏。

============================================================
三、权限边界
============================================================

你可以自主执行：

- 读取仓库、分支、PR、Issue、Actions、Artifact 和 Review；
- 创建安全本地工作区；
- 创建普通功能分支；
- 修改代码、测试、Workflow 和文档；
- Commit、Push 普通工作分支；
- 创建和更新 PR；
- 回复并解决 Review；
- Gate 全部满足后 squash merge 到 develop；
- 删除已经确认无唯一提交、无唯一证据的陈旧功能分支；
- 关闭已经被后续工作完全取代的陈旧 PR；
- 执行无公开副作用的测试、构建、审计和 dry run。

本提示词不构成以下不可逆操作的授权：

- 撤销真实生产凭据；
- Force Push 或远程历史重写；
- 创建或移动 Tag；
- 创建 GitHub Release；
- 提升 Alpha/Beta/Preview/Stable Channel；
- 使用 Apple Developer 身份签名或公证；
- 覆盖已有公开制品；
- 合并 develop 到 master；
- 对外发帖或发布公告。

上述操作必须满足对应 Work ID 的全部条件，并取得包含精确参数的 Owner 授权。

============================================================
四、开发和远程保存规范
============================================================

开发优先流程：

功能分支 → PR → 最终 Head CI → Review 清零 → squash merge develop → 删除分支

严禁：

- 在本地 develop 上直接开发；
- 用普通 git pull 制造 merge commit；
- git merge origin/develop；
- 把多个 Work ID 混入同一个 PR；
- 未经授权修改 master、Tag、Release 或公开 Channel；
- 跳过、删除或弱化测试；
- 合并没有有效最终 Head CI 的 PR。

同步 develop 只能使用：

  git fetch origin --prune --tags
  git checkout develop
  git reset --hard origin/develop

或：

  git pull --ff-only origin develop

远程保存是强制要求：

1. 临时沙箱可能随时销毁，任何有价值成果不得只留在本地。
2. 每完成一个可独立保存的原子工作，立即 Commit 并 Push。
3. 会话结束前必须执行 git status、git log、分支和 upstream 核对。
4. 不得留下未跟踪文件、未提交修改或未推送 Commit。
5. PR 是首选交付方式，但不是保存成果的唯一方式。
6. 如果 PR 因 GitHub 工具、CI 触发、权限或平台异常无法有效创建或合入，而改动安全、可逆、已验证且目标明确，则允许直接 Push 到 develop。
7. 直接 Push 前必须重新基于最新 origin/develop，确认无冲突、无 Secret、测试通过。
8. 直接 Push 的 Commit 信息必须写明 PR 失败原因、验证结果和技术债务。
9. 直接 Push 后必须读取远程 develop Head，确认 Commit 已真实存在。
10. 如果不能安全直推 develop，至少将全部 Commit Push 到明确命名的远程保存分支，并在交接中给出分支和 Head；不得让成果随沙箱丢失。

============================================================
五、Secret 安全
============================================================

执行任何凭据或外部平台命令前：

  set +x
  umask 077
  export HISTFILE=/dev/null

Secret 只允许存在于：

- 密码管理器；
- macOS Keychain；
- GitHub/Provider Secret Store；
- 当前进程的受限环境变量；
- 权限 0600 的临时文件，使用后立即删除。

Secret 不得进入：

- 聊天、Issue、PR、Commit；
- 仓库文件或 .env；
- Shell History 或命令行参数；
- 进程列表；
- Actions 日志；
- Screenshot、录屏或 Artifact；
- URL Query、Authorization Header 的公开输出。

不得要求用户在聊天中提供 Secret。

============================================================
六、PREBOOT-000：远程分支和 PR 卫生审计
============================================================

在 BOOT-001 前必须先执行 PREBOOT-000。

步骤 1：确认身份和仓库。

  gh auth status
  gh repo view yuanchenglu/deepseekagent --json nameWithOwner,defaultBranchRef,url,isPrivate

步骤 2：从空目录克隆，不复用旧容器工作区。

  git clone https://github.com/yuanchenglu/deepseekagent.git
  cd deepseekagent
  git fetch --all --tags --prune
  git checkout develop
  git reset --hard origin/develop
  git status --short

工作区必须为空。

步骤 3：使用分页接口全量枚举远程分支。

  gh api --paginate repos/yuanchenglu/deepseekagent/branches --jq '.[].name'

对每个非 develop/master/gh-pages 分支执行：

  git fetch origin "<branch>:refs/remotes/origin/<branch>"
  git rev-list --left-right --count origin/develop...origin/<branch>
  git log --oneline origin/develop..origin/<branch>
  git diff --stat origin/develop...origin/<branch>

每个分支只能分类为：

- ACTIVE_WORK
- OPEN_PR
- FULLY_MERGED
- SUPERSEDED
- DEPLOYMENT_BRANCH
- UNKNOWN

UNKNOWN 分支不得删除。

gh-pages 是独立部署分支，不得与 develop/master 合并，不得因无共同祖先而删除。

步骤 4：全量枚举开放 PR。

  gh pr list --repo yuanchenglu/deepseekagent --state open --limit 100 \
    --json number,title,url,isDraft,baseRefName,headRefName,headRefOid,mergeStateStatus,createdAt,updatedAt

每个 PR 必须检查：

- Base、Head 和实时落后情况；
- 是否降低 Plan 版本；
- 是否重新打开已有 PASSED 证据的任务；
- 是否有最终 Head CI；
- 是否有未解决 Review；
- 是否含独立有效提交；
- 是否只是过期文档或重复分支。

固定规则：

- 零 Workflow Run = NO-GO，不等于无需测试。
- PR 显示 0 conflicts 不等于可合并。
- 旧 Plan PR 不得合入。
- 被后续工作完全取代的 PR 应说明原因后关闭。

已知检查线索，不得机械假定仍然存在：

1. 若 PR #31 仍将 Plan 恢复到 v2.7.0、把已完成的双 Runtime E2E重新写为下一任务，且没有独立新工作，则关闭而不合并，并在确认无唯一提交后删除来源分支。
2. 若 setup/auto-merge-workflow 仍只包含“所有 PR 自动启用 auto-merge”，则确认无唯一证据后删除，不得合入 develop。
3. 若 chatgpt/sync-post-runtime-lease-protocol 相对 develop 领先为 0，则记录 FULLY_MERGED 后删除。

步骤 5：检查提交图卫生。

  git log origin/develop --merges -30 --oneline

如果发现没有最终 Tree 净变化的同步 Merge Commit：

- 记录 Git History Hygiene Finding；
- 不得误算工程进展；
- SEC Gate 完成前不得历史重写；
- 交给 HIST 阶段统一处理。

============================================================
七、完整读取权威文件
============================================================

必须完整读取：

  AGENTS.md
  docs/open-source-readiness/00-INDEX.md
  docs/open-source-readiness/三阶段执行计划PLAN.md
  docs/open-source-readiness/00-THREE-PHASE-DELIVERY-STATUS.md
  docs/open-source-readiness/07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md
  docs/open-source-readiness/08-PHASE-2-WEBUI-STABLE-BETA.md
  docs/open-source-readiness/09-PHASE-3-DUAL-MODE-ELECTRON.md
  docs/open-source-readiness/10-ELECTRON-PREVIEW-STATUS.md
  docs/open-source-readiness/11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md
  docs/open-source-readiness/12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md
  docs/open-source-readiness/13-OWNER-CREDENTIAL-ROTATION-GATE.md
  docs/open-source-readiness/14-REMOTE-RELEASE-STATE-AUDIT.md
  docs/open-source-readiness/15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md
  docs/open-source-readiness/16-REMAINING-WORK-EXECUTION-RUNBOOK.md
  docs/open-source-readiness/17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md
  docs/open-source-readiness/18-WORK-ID-ACCEPTANCE-CATALOG.md
  docs/open-source-readiness/remaining-work-plan.json
  docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md
  docs/open-source-readiness/HANDOFF_2026-07-28.md
  docs/TECH_DEBT.md

还必须读取：

  .github/workflows/local-owner-gate-kit-check.yml
  .github/workflows/remote-release-state-audit.yml
  scripts/validate_remaining_work_plan.py
  scripts/audit-remote-release-state.py
  scripts/owner-gate/verify-r2-credential-rotation.sh
  scripts/owner-gate/audit-all-git-refs.sh
  tests/owner-gate/test_remaining_work_plan.py
  tests/owner-gate/test_remote_release_audit.py
  tests/owner-gate/test-owner-gate-kit.sh

============================================================
八、交接体系防回退自检
============================================================

执行：

  python3 -m unittest tests/owner-gate/test_remaining_work_plan.py -v
  python3 -m unittest tests/owner-gate/test_remote_release_audit.py -v
  bash tests/owner-gate/test-owner-gate-kit.sh
  python3 scripts/validate_remaining_work_plan.py

必须确认：

- Work ID、Order 唯一；
- 依赖无环；
- 只有一个状态前沿；
- PASSED 任务连续位于前部；
- 后继任务保持 LOCKED；
- Plan 版本不得低于当前有效最低版本；
- Plan、总状态、技术债务和 JSON 前沿一致；
- 已完成的双 Runtime E2E 不得重新描述为未完成；
- Issue #21 未关闭前，HIST 和发布任务不得解锁。

检查 local-owner-gate-kit-check.yml 是否覆盖权威 Plan、总状态、Electron 状态、Owner Gate、远程审计、15/16/17/18、JSON 和 TECH_DEBT。

若缺少 Plan 防降级、状态一致性或触发路径：

1. 不得直接进入 SEC；
2. 创建独立防错加固分支；
3. 扩展 Workflow、Validator 和测试；
4. 完成最终 Head CI 和 Review；
5. 合入 develop 后再开始 BOOT-001。

============================================================
九、实时远程状态审计
============================================================

  git rev-parse origin/develop
  git rev-parse origin/master
  git log origin/develop -30 --date=iso-strict --pretty='%H%x09%ad%x09%s'
  gh issue view 21 --repo yuanchenglu/deepseekagent --comments
  gh run list --repo yuanchenglu/deepseekagent --limit 100

触发只读审计：

  gh workflow run remote-release-state-audit.yml \
    --repo yuanchenglu/deepseekagent \
    --ref develop

等待完成，下载并打开 JSON/Markdown Artifact，核对：

- develop/master Head；
- 开放 PR；
- Tags；
- Releases，包括 Draft/Prerelease；
- Active Actions；
- 当前引用 Head 最新失败；
- 历史失败；
- Alpha/Beta/Preview/Stable 公开 Channel。

不得只看绿色图标。

快照必须注明 UTC 时间，并声明执行后续任务前需要重新核对。

============================================================
十、执行台账
============================================================

创建或更新：

  docs/open-source-readiness/evidence/EXECUTION-LEDGER-YYYY-MM-DD.md

台账必须列出全部 Work ID 的：

- Order、状态、依赖、Executor；
- 是否不可逆、是否需要 Owner 授权；
- Evidence、PR、最终 Head、Merge SHA；
- Workflow Run、Artifact ID/Digest；
- Review、Blocker、下一任务。

原始敏感证据只保存在安全本地目录，远程只提交脱敏内容。

============================================================
十一、下一任务选择算法
============================================================

候选任务 = remaining-work-plan.json 中：

- status 为 READY 或 LOCKED；
- 全部 depends_on 已有远程 PASSED 证据；
- 当前任务尚无等价 PASSED 证据。

下一任务 = 候选中 order 最小的一项。

规则：

1. 一次只能执行一个 Work ID。
2. 多个候选仍只选 order 最小者。
3. 不得并行两个 Work ID。严禁同时实施两个 Work ID。
4. 不得跳过 Owner Gate。
5. 不得提前执行“容易”的后续任务。
6. 不得把后续任务顺手混入当前 PR。
7. 不得重复已有 PASSED 远程证据的任务。

没有候选时，检查 BLOCKED 输入、Owner 授权、状态遗漏和陈旧 PR；仍不能推进时，更新技术债务、台账和交接后停止。

============================================================
十二、每个 Work ID 的固定流程
============================================================

1. 打开 Runbook 对应章节。
2. 打开 Acceptance Catalog 对应条目。
3. 检查全部依赖。
4. 重新读取最新 origin/develop。
5. 检查是否已有等价远程证据。
6. 不满足前置条件则 BLOCKED。
7. 将 JSON 和 Ledger 改为 IN_PROGRESS。
8. 从最新 develop 创建一个独立分支：

     git fetch origin --prune --tags
     git checkout develop
     git reset --hard origin/develop
     git status --short
     git checkout -b work/<work-id-lowercase>-<short-name>

9. 严格执行 Runbook 的命令、测试、断言、失败处理和回滚。
10. 保存原始证据到安全本地目录。
11. 生成远程脱敏证据：

      docs/open-source-readiness/evidence/<WORK-ID>-<YYYY-MM-DD>.md

12. 证据必须包含：Work ID、状态、UTC、执行/复核人、基线、分支、最终 Head、OS/芯片/工具、输入、不含 Secret 的命令、退出码、断言、Workflow、Artifact、Review、P0/P1、回滚、脱敏、未验证内容、下一 Work ID。
13. 对 Diff、新文件、日志、Artifact 和历史执行 Secret 检查。
14. Commit 并立即 Push 远程。
15. 创建 PR；若 PR 工具或平台异常无法有效保存，按第四节的安全直推/远程保存分支规则处理。
16. 等待最终 PR Head 的全部目标 CI。
17. 零 Check 必须 NO-GO，调查 Path Filter 或手动触发；Run Head 必须等于最终 PR Head。
18. 读取全部 Review；Actionable Comment 必须修复、测试、回复和 Resolve。
19. 最终 Head CI 成功、Review 为 0、Evidence 完整后才可 squash merge develop。
20. 合并后读取最新 develop 和 Push Actions。
21. 将 Work ID 改为 PASSED，只解锁唯一后继任务。
22. 同步 Plan、状态、阶段文档、Evidence、TECH_DEBT、Index、Handoff 和 Ledger。
23. 自动进入下一 Work ID。

============================================================
十三、PR、Commit 和 CI 固定要求
============================================================

Commit 信息必须说明：

- Problem / Root cause
- Implementation
- Validation
- Unverified
- Technical debt

PR 必须包含：

- Work ID
- Gate 目标/根因
- 前置依赖与证据
- 技术方案
- 修改范围
- 最终 Head SHA
- 测试和真实环境结果
- Workflow Run
- Artifact ID/Digest
- Review 结果
- 失败历史和根因
- 未验证内容
- 回滚
- Secret 脱敏
- 技术债务
- 下一唯一任务

只有最终 PR Head 的结果有效。旧 Head、旧 Artifact、其他分支结果和没有 SHA 对应关系的截图无效。

============================================================
十四、状态规则
============================================================

允许状态：READY、LOCKED、IN_PROGRESS、BLOCKED、FAILED、PASSED、WAIVED。

PASSED：全部强制断言有远程可复核证据。
FAILED：至少一个强制断言失败。
BLOCKED：缺 Owner 权限、设备、用户、凭据或不可逆授权。
IN_PROGRESS：当前正在执行，后继不得解锁。

SEC、HIST、签名、公证、发布和数据安全任务不得 WAIVED。

FAILED 后必须修复根因并重新验证整个 Work ID，不能只重跑直到绿色。

============================================================
十五、安全 Gate 固定顺序
============================================================

除非机器任务图已通过 Reviewed PR 合法推进，否则：

BOOT-001 → BOOT-002 → BOOT-003
→ SEC-001 → SEC-002 → SEC-003 → SEC-004 → SEC-005 → SEC-006 → SEC-007
→ HIST-001 → HIST-002 → HIST-003 → HIST-004 → HIST-005 → HIST-006 → HIST-007 → HIST-008

Issue #21 未有远程 PASSED 证据并关闭前，禁止：

- Git 历史重写；
- Force Push；
- Tag；
- Release；
- 提升任何公开 Channel；
- develop 合并 master。

============================================================
十六、凭据轮换固定顺序
============================================================

盘点暴露面
→ 创建最小权限新凭据
→ 更新 Secret Store
→ 新凭据隔离最小读写验证
→ 撤销旧凭据
→ 使用旧凭据执行安全只读认证并确认失败
→ 提交脱敏证据
→ 关闭 Issue #21

R2 分阶段执行：

  bash scripts/owner-gate/verify-r2-credential-rotation.sh --new-only

只有旧凭据撤销后：

  bash scripts/owner-gate/verify-r2-credential-rotation.sh --old-denial-only

不得把平台显示 revoked 当作旧凭据失效证据，必须真实认证失败。

============================================================
十七、历史重写授权
============================================================

只有 SEC-007 PASSED 后才能进入 HIST。

Force Push 前必须完成 mirror、加密备份、bundle、refs/fsck before、全 refs 扫描、Finding 对应凭据失效、精确规则、隔离 dry run、refs/fsck after、测试、全 refs 零有效 Secret、回滚验证和协作者重克隆说明。

Owner 授权必须包含：

OWNER-AUTHORIZATION
action: HIST-006
repository: yuanchenglu/deepseekagent
current_remote_head: <SHA>
rewrite_result_digest: <DIGEST>
backup_bundle_digest: <DIGEST>
branches_to_update: <EXACT LIST>
tags_to_update: <EXACT LIST>
rollback_location: <LOCATION>
expires_at_utc: <TIME>

字段不完整不得 Force Push。

============================================================
十八、发布授权
============================================================

任何公开发布授权必须包含：

OWNER-AUTHORIZATION
action: <WORK-ID>
repository: yuanchenglu/deepseekagent
version: <VERSION>
head: <EXACT SHA>
tag: <EXACT TAG>
channel: <EXACT CHANNEL>
artifact_digest: <DIGEST>
rollback_target: <TARGET>
authorization_expires_at_utc: <TIME>

发布前必须再次核对 Tag、Release、Channel、Workflow Trigger、并发运行、Artifact Digest、Rollback、Active Actions、当前 Head 失败和授权有效期。Tag 触发冲突检查必须在推送任何 Tag 前完成：列出所有匹配 push.tags 的 workflow，确认候选 Tag 只触发目标发布工作流。

Channel 必须最后提升。

无签名 Electron Preview 不得描述为 Signed、Notarized 或 Stable。

授权必须包含精确的 Owner 授权格式：

  AUTHORIZE HIST-006
  Repository:
  Rewritten source digest:
  Affected branches:
  Affected tags:
  Backup bundle digest:
  Collaborator re-clone notice prepared: yes
  Authorized by:
  UTC time:

  AUTHORIZE STABLE-PUBLISH
  Version:
  Candidate Head SHA:
  master PR:
  Tag:
  Signing identity fingerprint:
  Notarization request/result:
  Stapling verified: yes
  Public channels:
  Rollback release/channel:
  P0 count: 0
  P1 count: 0
  Release Notes reviewed: yes
  Legal/license wording reviewed: yes
  Authorized by:
  UTC time:

============================================================
十九、master 纪律
============================================================

master 是发布分支，不是日常同步分支。

不得为了“保持最新”把 develop 直接合入 master。

只有发布 Gate PASSED 且 Owner 精确授权后，才能通过 PR 将已验证发布 Commit 提升到 master。

============================================================
二十、上下文腐烂和工具死循环
============================================================

出现以下任一情况视为上下文风险：

- 无法准确说出当前 Work ID、分支、Head 或依赖；
- 把已完成任务重新当作未完成；
- 连续三次相同工具操作没有新增信息；
- 在同一错误上反复重试却没有根因假设；
- 忘记修改文件；
- Plan、JSON、Ledger 和 PR 互相矛盾；
- 不能保证继续操作不会误发布或误写远程。

立即执行：

  git status --short
  git diff
  git log -5 --oneline
  git branch --show-current
  git rev-parse HEAD
  git rev-parse origin/develop

然后：

1. 停止开始新修改；
2. 完成可安全完成的最小原子 Commit；
3. Push 当前分支；
4. 确认无本地未推送工作；
5. 更新 Ledger、TECH_DEBT 和 Handoff；
6. 记录 Work ID、状态、分支、Head、PR、CI、Review、根因和下一命令；
7. 生成可直接复制的新会话提示词；
8. 停止当前会话。

如果平台不能自行创建新会话，则由用户复制交接提示词。不得声称后台继续。

============================================================
二十一、停止前远程持久化检查
============================================================

任何停止、交接或会话结束前，必须执行并记录：

  git status --porcelain=v1
  git branch --show-current
  git rev-parse HEAD
  git log --oneline --decorate -10
  git rev-list --left-right --count @{upstream}...HEAD
  git ls-remote --heads origin

通过条件：

- git status 输出为空；
- 当前有价值 Commit 已 Push；
- 远程存在当前 Head；
- 若目标是 develop，远程 develop 已包含该 Commit；
- 若暂不能安全进入 develop，远程保存分支包含全部 Commit，且交接明确分支和 Head；
- 没有仅在本地的未跟踪文件、未提交修改、stash 或 Commit。

如发现未保存工作，必须先 Commit 和 Push，再停止。

============================================================
二十二、最终完成条件
============================================================

只有全部满足才能声明整个 Plan 完成：

- 全部 Work ID PASSED；
- 所有 SEC Gate 完成；
- 历史清理和全 refs 扫描完成；
- CLI Alpha、WebUI Beta、Electron Preview 发布并完成反馈闭环；
- Apple 签名、公证和 Stable Release 完成；
- 公开渠道安装、升级、失败回滚和卸载回归通过；
- P0/P1 清零；
- Review Thread 为 0；
- Tags、Releases、Channels、master 与证据一致；
- Plan、Status、TECH_DEBT、Index、Evidence、Ledger 和 Handoff 同步；
- 没有本地未推送工作；
- 没有陈旧开放 PR；
- 没有未分类远程分支；
- 最终远程发布状态审计通过。

最终报告必须区分：

- 已完成并验证；
- 已发布；
- 未验证；
- 技术债务；
- 历史失败；
- Owner 操作；
- 最终远程 Head、Tag、Release、Channel；
- Artifact 和 Digest；
- 回滚路径。

满足以上条件前，不得声称整个计划完成。
```
