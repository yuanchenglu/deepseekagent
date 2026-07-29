# 弱 AI 专用：DeepAgent 剩余 Plan 确定性交接提示词

> 使用方式：把下方代码块完整复制给执行 AI，不要删减。  
> 目标：即使执行 AI 推理能力较弱，也只能按固定 Work ID、依赖、证据和发布纪律推进。  
> 本提示词不是建议，是执行协议。

```text
@GitHub

你现在接管并持续负责 GitHub 仓库：

  yuanchenglu/deepseekagent

Remote：

  https://github.com/yuanchenglu/deepseekagent.git

你的任务是：严格按照仓库当前有效 Plan、机器可读任务图和确定性执行手册，自主、连续、串行完成所有剩余 Work ID、Gate、阶段发布、反馈闭环、Stable 准备和最终 Stable 发布。

你不得自由改顺序，不得跳过 Gate，不得一次并行多个任务，不得因为完成一个 PR 就停止，也不得等待用户反复发送“继续”。

============================================================
一、你必须先接受的事实
============================================================

1. GitHub 远程仓库是唯一事实源。
2. 旧会话、旧容器、旧 SHA、百分比、未推送文件都不是事实源。
3. 代码实现、自动化通过、真实物理机验证、公开发布、用户反馈是五种不同状态，不能互相替代。
4. 当前剩余任务包含真实 Secret、不可逆 Git 历史重写、物理 Apple Silicon Mac、真实模型、真实用户、Apple 签名/公证和公开发布授权。
5. Secret 永远不得进入聊天、Commit、PR、Issue、文档、Actions 日志、命令行参数、录屏或公开 artifact。
6. 不清楚就失败关闭。没有证据就不是完成。

============================================================
二、启动后第一批动作：必须按顺序执行
============================================================

步骤 1：确认 GitHub 身份和权限。

  gh auth status
  gh repo view yuanchenglu/deepseekagent --json nameWithOwner,defaultBranchRef,url

步骤 2：从空目录获取最新仓库。

  git clone https://github.com/yuanchenglu/deepseekagent.git
  cd deepseekagent
  git fetch --all --tags --prune
  git checkout develop
  git pull --ff-only origin develop

步骤 3：完整读取以下文件，不得只读摘要：

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
  docs/open-source-readiness/remaining-work-plan.json
  docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md
  docs/TECH_DEBT.md
  docs/open-source-readiness/HANDOFF_2026-07-28.md

步骤 4：审计实时远程状态。

  git rev-parse origin/develop
  git rev-parse origin/master
  git log origin/develop -30 --date=iso-strict --pretty='%H%x09%ad%x09%s'
  gh pr list --repo yuanchenglu/deepseekagent --state open --limit 100
  gh issue view 21 --repo yuanchenglu/deepseekagent --comments
  gh run list --repo yuanchenglu/deepseekagent --limit 100

步骤 5：运行只读发布状态审计。

  gh workflow run remote-release-state-audit.yml \
    --repo yuanchenglu/deepseekagent \
    --ref develop

等待运行完成，下载 artifact，打开 JSON 和 Markdown，核对：

- develop/master Head；
- 开放 PR；
- Tags；
- Releases，包括 Draft/Prerelease；
- 当前 Active Actions；
- 当前引用 Head 最新失败；
- Alpha/Beta/Preview/Stable 公开渠道。

不得只看 workflow 显示绿色。

步骤 6：创建或更新执行台账：

  docs/open-source-readiness/evidence/EXECUTION-LEDGER-YYYY-MM-DD.md

台账必须列出 remaining-work-plan.json 中所有 Work ID、状态、PR、Head、merge、artifact、阻塞和下一任务。

============================================================
三、选择下一任务：不得自行发挥
============================================================

每次只能按以下算法选择：

候选任务 = remaining-work-plan.json 中：

- status 是 READY 或 LOCKED；
- depends_on 中每个任务都已经有远程 PASSED 证据；
- 该任务本身尚无等价 PASSED 远程证据。

下一任务 = 候选任务中 order 最小的一项。

如果没有候选任务：

1. 检查 BLOCKED 任务缺什么输入；
2. 检查 Owner 是否已在 Issue/PR 提供输入；
3. 检查依赖是否完成但忘记更新状态；
4. 仍无法推进时，更新 Plan、技术债务和交接后停止。

如果有多个候选，仍只执行 order 最小的一项。

严禁同时实施两个 Work ID。

============================================================
四、每个 Work ID 的固定动作
============================================================

对每一项，严格执行：

1. 打开 16-REMAINING-WORK-EXECUTION-RUNBOOK.md 中对应 Work ID。
2. 检查所有前置条件；有一个不满足就 BLOCKED，不能继续。
3. 把 remaining-work-plan.json 和执行台账中的状态改为 IN_PROGRESS。
4. 从最新 develop 创建独立分支：

     git checkout develop
     git pull --ff-only origin develop
     git checkout -b work/<work-id-lowercase>-<short-name>

5. 执行手册规定的命令和验证。
6. 保存原始证据到安全本地目录；原始证据可能含敏感内容时绝不上传。
7. 生成脱敏证据：

     docs/open-source-readiness/evidence/<WORK-ID>-<YYYY-MM-DD>.md

8. 证据必须填写：

   - Work ID；
   - PASSED/FAILED/BLOCKED；
   - UTC 时间；
   - 执行人和复核人；
   - develop 基线 SHA；
   - 分支和最终 Head；
   - OS/芯片/工具版本；
   - 输入来源；
   - 不含 Secret 的命令；
   - 退出码；
   - 强制断言；
   - artifact ID/digest；
   - Review；
   - P0/P1；
   - 回滚；
   - 脱敏检查；
   - 未验证内容；
   - 下一 Work ID。

9. 对所有拟提交文件运行 Secret 检查。不得上传 Secret、Authorization Header、签名 URL、证书私钥、模型 Token 或可还原值。
10. 推送分支并创建 PR。
11. PR 描述必须有：

   ## Work ID
   ## Gate 目标/问题根因
   ## 前置依赖与证据
   ## 执行步骤/技术方案
   ## 修改范围
   ## 最终 Head SHA
   ## 测试和真实环境结果
   ## Artifact/digest
   ## Review 结果
   ## 未验证内容
   ## 回滚方案
   ## Secret 脱敏检查
   ## 技术债务
   ## 下一唯一任务

12. 等待最终 PR Head 的全部目标 CI。
13. 读取所有 Review thread。每个 actionable comment 必须修复、回复、重新测试并标记 resolved。
14. 只有最终 Head CI 成功、Review 为 0、证据完整，才能 squash merge 到 develop。
15. 合并后重新读取 develop 和 Actions。
16. 把 Work ID 改为 PASSED，并解锁唯一后继任务。
17. 同步：Plan、总状态、阶段文档、测试报告、技术债务、00-INDEX、交接和执行台账。
18. 自动进入下一 Work ID，不等待“继续”。

============================================================
五、状态判定：只允许四种实际结果
============================================================

PASSED：所有强制断言均有可复核证据。
FAILED：执行结束但至少一个强制断言失败。
BLOCKED：缺少 Owner 权限、真实设备、真实用户或不可逆授权。
IN_PROGRESS：当前正在执行，不能解锁后继任务。

禁止使用“基本通过”“主体完成”“约 95%”“看起来没问题”“先算完成”。

FAILED 后必须修复根因并重新执行整个当前 Work ID。不能只重跑直到绿色。

============================================================
六、当前安全 Gate 的固定顺序
============================================================

必须依次完成：

BOOT-001 → BOOT-002 → BOOT-003
→ SEC-001 → SEC-002 → SEC-003 → SEC-004 → SEC-005 → SEC-006 → SEC-007
→ HIST-001 → HIST-002 → HIST-003 → HIST-004 → HIST-005 → HIST-006 → HIST-007 → HIST-008

Issue #21 未有远程 PASSED 证据并关闭前：

- 禁止 Git 历史重写；
- 禁止 force push；
- 禁止发布 Tag；
- 禁止公开 Release；
- 禁止提升任何 channel。

============================================================
七、Secret 处理：必须严格执行
============================================================

安全 shell：

  set +x
  umask 077
  export HISTFILE=/dev/null

Secret 只允许存在：

- 密码管理器；
- macOS Keychain；
- 受限临时环境变量；
- GitHub/Provider Secret 存储；
- 权限 600 的临时文件，并在完成后删除。

不得存在：

- 仓库文件；
- `.env`；
- shell history；
- 命令参数；
- PR/Issue/聊天；
- Actions 日志；
- 截图/录屏；
- artifact。

凭据轮换必须完成：盘点 → 新凭据 → 更新消费方 → 新凭据最小读写验证 → 撤销旧凭据 → 旧凭据只读认证失败 → 脱敏证据 PR → 关闭 Issue #21。

R2 使用：

  bash scripts/owner-gate/verify-r2-credential-rotation.sh

旧凭据只“显示 revoked”不算完成，必须真实认证失败。

============================================================
八、Git 历史重写：必须等 Owner 明确授权
============================================================

先完成：

- mirror clone；
- 加密备份；
- Git bundle；
- refs-before；
- fsck-before；
- 全 refs gitleaks；
- 每个 finding 对应的已失效凭据；
- 精确 rewrite rules；
- 隔离 dry run；
- after refs；
- 测试/构建；
- 0 有效秘密；
- 回滚 bundle 验证。

Owner 授权必须包含：

  AUTHORIZE HIST-006
  Repository:
  Rewritten source digest:
  Affected branches:
  Affected tags:
  Backup bundle digest:
  Collaborator re-clone notice prepared: yes
  Authorized by:
  UTC time:

缺任一字段不得 force push。

============================================================
九、发布前必须检查 Tag 触发冲突
============================================================

在推送任何 Tag 前：

1. 搜索所有 `.github/workflows/*.yml` 的 `push.tags`；
2. 计算候选 Tag 会匹配哪些 workflow；
3. 只允许匹配预期发布工作流；
4. 若会触发额外 workflow，先单独修复 trigger；
5. 禁止“先推 Tag 再观察”。

特别注意：Beta/Preview Tag 可能意外触发通用 `release.yml`。发现冲突必须先修复。

============================================================
十、三个阶段必须完整串行闭环
============================================================

CLI Alpha：

CLI-001 至 CLI-013 全部 PASSED，包括：dry run、干净 Mac、真实模型、升级、失败回滚、卸载、Hermes/OpenCode 共存、P0/P1=0、Owner 授权、发布、公开回归、Alpha 用户周期。

WebUI Beta：

WEB-001 至 WEB-011 全部 PASSED，包括：迁移、迁移失败回滚、干净生命周期、Browser 安全、共存、Beta dry run、P0/P1=0、Owner 授权、发布、公开回归、Beta 用户周期。

Electron Preview：

DESK-001 至 DESK-011 全部 PASSED，包括：DMG checksum、Gatekeeper 手工批准、双模式、升级/回滚/卸载、Crash/Lease、共存、受控用户测试、P0/P1=0、Owner 对无签名风险的明确授权、发布、反馈。

Stable：

STB-001 至 STB-012 全部 PASSED，包括：Apple 权限、签名、Hardened Runtime、Entitlements、公证、staple、更新链、干净 Mac、全矩阵、RC、P0/P1=0、Owner 最终授权、master/Tag/Release/Stable channel、公开回归、用户反馈、最终文档闭环。

============================================================
十一、公开发布必须使用固定授权
============================================================

没有以下明确授权，只准备 Draft、dry run、Release Notes、Manifest、Checksum 和回滚方案，不执行公开动作。

CLI Alpha：

  AUTHORIZE CLI-ALPHA-PUBLISH
  Version:
  Candidate Head SHA:
  Tag:
  Target GitHub Release:
  Target R2 objects:
  Target channel: alpha
  Release Notes reviewed: yes
  Rollback version/channel object:
  Authorized by:
  UTC time:

WebUI Beta：使用 `AUTHORIZE WEBUI-BETA-PUBLISH`，并写清 BSL-1.1 许可口径。

Electron Preview：使用 `AUTHORIZE ELECTRON-PREVIEW-PUBLISH`，并明确接受无签名、未公证和 Gatekeeper 手工批准风险。

Stable：

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

缺任一字段不得发布。

============================================================
十二、失败时不要猜，按分类处理
============================================================

代码/配置错误：修复、加回归测试、重新跑整个 Work ID。
测试错误：修测试，但必须证明生产行为正确。
外部服务错误：记录状态码、时间、Provider；可重试则重试，持续失败则 BLOCKED。
权限缺失：写清所需权限、Owner 步骤、预期结果和验证方式，BLOCKED。
物理设备缺失：BLOCKED，不用模拟器证据替代。
真实用户缺失：BLOCKED，不用内部 AI 自测替代。
不可复现：增加日志和诊断；未定位前不能 PASSED。

禁止：降低断言、skip 测试、删除失败日志、使用旧 artifact、只重跑到绿色、未定位就合并。

============================================================
十三、上下文不足时的自动交接
============================================================

出现以下任一情况：

- 无法准确说出当前 Work ID、依赖和 PASSED 条件；
- 同一命令执行三次无新信息；
- 混淆 develop/master、版本或候选 Head；
- 不确定 PR 是否合并；
- 引用 SHA 与远程冲突；
- 工具循环；
- 无法完整检查 CI/Review；

立即执行：

1. 推送全部安全成果；
2. 更新执行台账、Plan、状态、技术债务和交接；
3. 写明当前 Work ID、已完成步骤、最后一个可靠证据、阻塞和下一条命令；
4. 新会话从 BOOT-001 重新审计；
5. 不重复已有 PASSED 远程证据的任务。

============================================================
十四、每次向用户汇报的固定格式
============================================================

只汇报事实：

当前 Work ID：
状态：IN_PROGRESS / PASSED / FAILED / BLOCKED
依赖证据：
本次完成：
最终 Head：
PR：
CI：
Review：
Artifact/digest：
真实环境验证：
未验证：
技术债务：
下一唯一任务：
是否需要 Owner 输入：

不得用“基本完成”“差不多”“应该可以”。

============================================================
十五、最终完成标准
============================================================

只有 remaining-work-plan.json 中所有 Work ID 都为 PASSED，并且：

- Issue #21 关闭且有脱敏证据；
- 全 refs 有效秘密为 0；
- 干净机安装/升级/失败回滚/卸载通过；
- CLI/WebUI/Desktop/Hermes/OpenCode 共存通过；
- 真实模型任务通过；
- Alpha/Beta/Preview/Stable 和反馈周期全部闭环；
- Apple 签名、公证、staple、更新链通过；
- P0/P1 为 0 或符合正式豁免；
- 最终 Head CI 成功、Review 为 0；
- develop/master/Tags/Releases/Channels/Manifest/Checksum 一致；
- 没有关键成果只在本地；
- 发布后回归和文档闭环完成；

才可以宣布整个 Plan 完成。

现在开始执行 BOOT-001。不要先输出宏观分析或待办列表；直接审计远程并持续推进。
```
