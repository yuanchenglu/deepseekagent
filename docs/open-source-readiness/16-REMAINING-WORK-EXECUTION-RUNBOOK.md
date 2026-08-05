# DeepAgent 剩余工作确定性执行手册

> 版本：v1.0  
> 更新日期：2026-07-29  
> 面向对象：能力有限、上下文容易丢失、容易跳步的本地执行 AI  
> 机器可读任务图：`remaining-work-plan.json`  
> 启动提示词：`15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`

## 0. 本手册解决什么问题

本手册不依赖执行 AI 自己“理解大方向”。它把剩余工作拆成固定 Work ID，并规定：

1. 当前只能做哪一项；
2. 做之前必须满足什么；
3. 必须读取哪些文件；
4. 可以运行哪些命令；
5. 什么输出才算通过；
6. 失败后如何分类和处理；
7. 必须提交哪些远程证据；
8. 何时必须停下来等待 Owner；
9. 何时自动进入下一项。

执行 AI 不得自行更改依赖顺序，不得把“看起来正常”当作通过，不得用上一轮成功结果替代最终 Head 的失败结果。

---

# 1. 不需要判断的硬规则

## 1.1 每次只做一个 Work ID

从 `remaining-work-plan.json` 选择任务：

```text
候选任务 = status 为 READY 或 LOCKED
          且 depends_on 中所有任务都为 PASSED
          且尚未有等价远程证据

下一任务 = 候选任务中 order 最小的一项
```

如果候选任务为 0：

- 检查是否有 BLOCKED 任务；
- 检查阻塞输入是否已由 Owner 提供；
- 检查依赖任务是否只是忘记更新状态；
- 仍无法推进时，更新技术债务和交接后停止。

如果候选任务大于 1：仍只执行 `order` 最小的一项。

## 1.2 状态只能按以下方式变化

```text
LOCKED → READY → IN_PROGRESS → PASSED
                         ├→ FAILED
                         └→ BLOCKED
BLOCKED → READY（只有阻塞输入已真实满足）
FAILED → IN_PROGRESS（修复后重新执行完整验收）
```

`WAIVED` 只能在 Plan 明确允许、Owner 明确批准、风险与补偿控制均记录后使用。安全、凭据失效、Git 历史有效秘密、P0 不得口头豁免。

## 1.3 禁止动作

除非对应 Work ID 已到达且有明确授权，禁止：

- 重写或 force push Git 历史；
- 删除 branch、tag、release、artifact 或历史证据；
- 创建或推送发布 Tag；
- 将 Draft Release 改为公开；
- 提升 Alpha、Beta、Preview、Stable channel；
- 上传签名证书、私钥、API Key 或模型 Token；
- 在命令行参数、PR、Issue、Commit、日志或聊天中放 Secret；
- 把无签名 DMG 称为 Stable；
- 把 CI 构建成功称为真实干净机验收；
- 把内部测试称为用户反馈闭环。

## 1.4 任何歧义都按失败关闭

出现以下任一情况，不得标记 PASSED：

- 命令退出码未知；
- 日志不完整；
- artifact 无 digest；
- 测试对象未确认删除；
- 旧凭据只验证了“已点撤销”，未证明认证失败；
- gitleaks 报告无法解析；
- 只扫描当前分支，未扫描全部 refs；
- 只在已有开发机测试，无法证明干净环境；
- Review thread 未逐项确认 resolved；
- 发布后未从公开渠道重新下载验证；
- P0/P1 列表不明确；
- Owner 授权没有写明版本、Head SHA、渠道和动作。

---

# 2. 每个 Work ID 的固定执行循环

每项都必须完整执行：

```text
A. 读取依赖证据
B. 把任务状态改为 IN_PROGRESS
C. 建立独立分支
D. 执行或开发
E. 保存原始本地证据
F. 生成脱敏远程证据
G. 自检 Secret 和不可逆动作
H. 推送分支并创建 PR
I. 等待最终 PR Head CI
J. 处理全部 actionable review
K. 合入 develop
L. 重新读取 develop 和远程 Actions
M. 把任务状态改为 PASSED
N. 更新 Plan、状态、阶段文档、技术债务、索引和交接
O. 自动选择下一 Work ID
```

### PR 描述固定字段

每个 PR 必须包含：

```text
## Work ID
## 问题根因 / Gate 目标
## 前置依赖及证据
## 技术方案或执行步骤
## 修改范围
## 最终 Head SHA
## 测试和真实环境结果
## Artifact / digest
## Review 处理结果
## 未验证内容
## 回滚方案
## Secret 脱敏检查
## 技术债务
## 下一唯一任务
```

---

# 3. 统一证据标准

每个 Work ID 的证据文件放入：

```text
docs/open-source-readiness/evidence/<WORK-ID>-<YYYY-MM-DD>.md
```

证据最少包含：

```text
Work ID:
结论: PASSED / FAILED / BLOCKED
执行时间（UTC）:
执行人/AI:
复核人:
仓库:
develop 基线 SHA:
功能分支:
最终 PR Head SHA:
合并 SHA:
操作系统/芯片:
工具版本:
输入来源:
执行命令（不得含 Secret）:
退出码:
关键断言:
原始本地证据位置:
远程 artifact ID/digest:
Review threads:
P0/P1:
回滚方案:
Secret 脱敏检查:
未验证内容:
下一 Work ID:
```

### 证据判定

- `PASSED`：所有强制断言都有可复核证据。
- `FAILED`：执行完成但至少一个强制断言失败。
- `BLOCKED`：缺少 Owner 权限、真实设备、真实用户或不可逆授权，且当前环境无法补足。
- 不允许使用 `PARTIAL PASS` 解锁后继任务。

---

# 4. BOOT：本地执行环境启动

## BOOT-001：重新审计远程真实状态

### 前置条件

无。任何新会话必须从本项开始。

### 必读

- `AGENTS.md`
- `docs/open-source-readiness/00-INDEX.md`
- `三阶段执行计划PLAN.md`
- `00-THREE-PHASE-DELIVERY-STATUS.md`
- `13-OWNER-CREDENTIAL-ROTATION-GATE.md`
- `14-REMOTE-RELEASE-STATE-AUDIT.md`
- `15-LOCAL-HIGH-PERMISSION-EXECUTION-PROMPT.md`
- 本手册
- `remaining-work-plan.json`
- `docs/TECH_DEBT.md`
- Issue #21

### 命令

```bash
set -euo pipefail
REPO=yuanchenglu/deepseekagent

gh auth status
gh repo view "$REPO" --json nameWithOwner,defaultBranchRef,url

git clone https://github.com/yuanchenglu/deepseekagent.git
cd deepseekagent
git fetch --all --tags --prune
git checkout develop
git pull --ff-only origin develop

git rev-parse develop
git rev-parse origin/master
git log origin/develop -30 --date=iso-strict --pretty='%H%x09%ad%x09%s'
gh pr list --repo "$REPO" --state open --limit 100
gh issue view 21 --repo "$REPO" --comments
gh run list --repo "$REPO" --limit 100

gh workflow run remote-release-state-audit.yml --repo "$REPO" --ref develop
```

等待手工审计运行完成，下载 artifact 并复核 JSON/Markdown。不得只看绿色图标。

### PASSED 条件

- 当前 `develop`、`master`、开放 PR、Issue #21、Actions、Tags、Releases、公开渠道全部有时间戳快照；
- 没有把历史 SHA 当作最新事实；
- 当前唯一合法任务已由依赖图计算出来；
- 没有未推送本地改动。

### 失败处理

- GitHub 无权限：BLOCKED，记录缺少的具体 scope；
- 网络问题：重试并保存错误；持续失败则 BLOCKED；
- 有开放 PR：先审计其是否属于当前唯一任务，不得并行另开重复工作；
- 当前 Head 有失败 CI：先修复失败，不得进入安全 Gate。

### 证据

`BOOT-001-YYYY-MM-DD.md`，附远程审计 run、artifact ID 和 digest。

---

## BOOT-002：建立安全本地工作区

### 命令与约束

```bash
set +x
umask 077
export HISTFILE=/dev/null
mkdir -p "$HOME/deepagent-secure-work"
chmod 700 "$HOME/deepagent-secure-work"
```

- Secret 只允许进入密码管理器、Keychain、受限临时环境变量或受控 CI Secret；
- 不写 `.env`、Markdown、shell script、命令参数或终端截图；
- 使用独立测试前缀和最小权限；
- 录屏、远程日志、AI 上下文和命令回显全部关闭；
- 完成后清除环境变量并关闭会话。

### PASSED 条件

- 工作目录权限为 700；
- Secret 文件不存在于仓库和工作树；
- `git status --ignored` 未出现包含 Secret 的文件；
- 终端未开启 `set -x`；
- Owner 明确知道不得粘贴 Secret 给 AI。

---

## BOOT-003：建立执行台账

创建：

```text
docs/open-source-readiness/evidence/EXECUTION-LEDGER-YYYY-MM-DD.md
```

台账按 `order` 列出所有 Work ID，字段：状态、开始时间、完成时间、PR、Head、merge、artifact、阻塞、下一项。

同时复制 `remaining-work-plan.json` 到本地临时状态文件。每完成一项，远程 JSON 中对应状态也必须更新。

### PASSED 条件

- 所有 Work ID 均存在且无重复；
- 只有 BOOT-001/002/003 和当前首个安全任务可能为 READY/PASSED；
- 后继任务保持 LOCKED；
- 台账已进入独立 PR。

---

# 5. SEC：外部凭据轮换 Gate

## SEC-001：凭据盘点

### 必须盘点

- Repository、Organization、Environment Actions Secrets；
- Dependabot、Codespaces Secrets；
- Cloudflare R2、Pages、DNS；
- `CF_ACCOUNT_ID`、`CF_R2_ACCESS_KEY_ID`、`CF_R2_SECRET_ACCESS_KEY`、`CLOUDFLARE_API_TOKEN`；
- GitHub Release、Pages、Packages；
- 模型 Provider；
- 遥测、错误上报、邮件、对象存储、部署平台；
- 本地 `.env`、shell history、CI 日志、历史 artifact；
- Git 全 refs 命中。

### 记录字段

Provider、用途、Secret 名称、scope、创建时间、旧 Token 脱敏 ID、是否进入 Git、Owner、轮换状态。禁止记录 Secret 值。

### PASSED 条件

- 所有已知服务均有条目；
- 每个条目明确“需轮换/不需轮换/无法确认”；
- “无法确认”视为未完成；
- 至少两人复核清单完整性。

---

## SEC-002：创建替代凭据

### Owner 动作

- 每个 Token 只授予当前发布或测试必需 scope；
- R2 Token 限制到 `deepagent-releases`；
- 测试 Token 与生产 Token 分离；
- 记录脱敏 Token ID、scope、创建时间和过期时间；
- 不覆盖旧凭据，直到新凭据验证成功。

### PASSED 条件

- 每个需轮换条目都有新凭据；
- 权限矩阵证明没有账户级无关权限；
- Secret 值只存在安全存储；
- 没有 Commit/Issue/日志泄漏。

---

## SEC-003：更新 Secret 存储

### 执行顺序

1. 更新外部平台配置；
2. 更新 GitHub Repository Secrets；
3. 更新 Organization/Environment Secrets；
4. 检查 Dependabot/Codespaces；
5. 检查本地发布机和密码管理器共享项；
6. 不撤销旧凭据。

只记录更新时间、Secret 名称和操作者，不读取或导出 Secret 值。

### PASSED 条件

所有消费方均指向新凭据，且不存在仍引用旧 ID 的自动化。

---

## SEC-004：验证新凭据

### R2 命令

在安全 shell 中设置：

```text
CF_ACCOUNT_ID
NEW_CF_R2_ACCESS_KEY_ID
NEW_CF_R2_SECRET_ACCESS_KEY
OLD_CF_R2_ACCESS_KEY_ID
OLD_CF_R2_SECRET_ACCESS_KEY
EVIDENCE_PATH
```

运行：

```bash
set +x
bash scripts/owner-gate/verify-r2-credential-rotation.sh
```

脚本必须完成：随机对象上传、读回、字节比较、删除。人工再检查 Token scope。

### PASSED 条件

- 上传成功；
- 读回成功；
- `cmp` 成功；
- 删除成功且对象不存在；
- 不存在多余 bucket/account 权限；
- 证据不含 Access Key、Secret、Authorization Header 或签名 URL。

其他 Provider 执行等价的最小权限验证。

---

## SEC-005：撤销旧凭据

只有 SEC-004 PASSED 后执行。

逐个撤销，记录 Provider、脱敏 ID、UTC 时间、操作者。不得批量撤销未确认用途的 Token。

### PASSED 条件

清单内所有旧凭据状态为 revoked/disabled，所有消费方已切换新凭据。

---

## SEC-006：证明旧凭据失效

使用旧凭据执行最小只读请求，禁止写入。

### PASSED 条件

- 每个旧凭据均返回认证失败或权限拒绝；
- 记录 HTTP/CLI 错误码和 UTC 时间；
- 未记录旧凭据值；
- “控制台显示 revoked”不能代替该测试。

如果任何旧凭据仍成功：SEC-006 FAILED，立即重新撤销并调查缓存、复制 Token、子账号或旧部署。

---

## SEC-007：证据 PR 与 Issue #21

复制模板：

```bash
cp docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-TEMPLATE.md \
  docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-$(date -u +%F).md
```

完成脱敏扫描、双人复核、PR、CI、Review、合入 `develop`。只有远程证据明确 PASSED 后关闭 Issue #21。

### 下一任务

`HIST-001`。Issue #21 未关闭不得开始历史重写。

---

# 6. HIST：Git 历史清理

## HIST-001：备份和清理前扫描

```bash
set -euo pipefail
WORK="$HOME/deepagent-secure-work/history-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$WORK" && chmod 700 "$WORK"
git clone --mirror https://github.com/yuanchenglu/deepseekagent.git "$WORK/deepseekagent.git"
cd "$WORK/deepseekagent.git"
git show-ref | sort > "$WORK/refs-before.txt"
git bundle create "$WORK/deepseekagent-before.bundle" --all
git fsck --full --no-reflogs > "$WORK/fsck-before.txt" 2>&1 || true
bash "$OLDPWD/scripts/owner-gate/audit-all-git-refs.sh" \
  https://github.com/yuanchenglu/deepseekagent.git "$WORK/scan-before"
```

将 bundle 加密并离线保存；远程只提交脱敏摘要和哈希，不上传含旧 Secret 的 bundle。

### PASSED 条件

- mirror、bundle、refs、fsck、scan 全部存在；
- bundle 可在隔离目录恢复；
- 每个 finding 映射到已失效凭据或明确误报；
- 未对远程执行写操作。

---

## HIST-002：精确重写规则

对每个真实命中记录：RuleID、文件、Commit、ref、凭据脱敏 ID、处理方式。

规则要求：

- 使用精确字符串或精确路径；
- 禁止“删除所有类似 Token 的字符串”一类宽泛规则；
- replace-text 文件只存在安全临时位置，权限 600；
- 不把旧 Secret 放在 shell 参数；
- 先在副本验证误伤范围。

### PASSED 条件

每个真实 finding 有且只有一个处理规则，每个规则有预期受影响 Commit 数和文件清单。

---

## HIST-003：隔离 dry run

在 mirror 的复制品中运行固定版本 `git filter-repo`。先记录版本：

```bash
git filter-repo --version
gitleaks version
```

执行后导出 before/after ref 对照。不得 push。

### PASSED 条件

- 重写只影响预期 refs/commits/files；
- 当前源码没有非预期变化；
- 旧 Secret 不出现在命令日志；
- 可从备份恢复原状态。

---

## HIST-004：重写后验证

必须运行：

```bash
git fsck --full --no-reflogs
git show-ref | sort
# 对重写结果执行 gitleaks 全 refs 扫描
```

并在普通 clone 中运行仓库规定的核心测试、WebUI 测试、Electron Main 测试和构建验证。

### PASSED 条件

- 0 个有效秘密 finding；
- 误报均有逐项证据；
- 所有 refs 均在对照表中；
- 测试与构建通过；
- Tag/Release/PR 影响清单完整；
- 回滚 bundle 已验证。

---

## HIST-005：force-push 授权

Owner 授权必须明确写出：

```text
AUTHORIZE HIST-006
Repository: yuanchenglu/deepseekagent
Rewritten source digest:
Affected branches:
Affected tags:
Backup bundle digest:
Collaborator re-clone notice prepared: yes
Authorized by:
UTC time:
```

缺任一字段都不执行。

---

## HIST-006：更新远程 refs

- 维护窗口内执行；
- 先保护/暂停自动发布；
- 按清单分批 push branches，再 push tags；
- 每批后重新 fetch 比较；
- 任何非预期拒绝或 SHA 偏差立即停止；
- 不删除未列出的 refs。

### PASSED 条件

远程所有目标 ref 与批准的 after SHA 完全一致。

---

## HIST-007：远程重克隆和全 refs 重扫

从空目录重新 mirror clone 远程，运行 `audit-all-git-refs.sh`。

### PASSED 条件

- 有效秘密为 0；
- `git fsck` 无破坏性错误；
- Secret scanning 无未处理有效告警；
- Tags、Releases、Channels 未被错误提升；
- 当前 Actions 没有由重写造成的未解决失败。

---

## HIST-008：协作者恢复和证据闭环

提交脱敏报告、before/after ref 摘要、工具版本、扫描 digest、测试结果和重新 clone 指令。明确禁止旧 clone force push 回污染历史。

下一任务：`CLI-001`。

---

# 7. CLI Alpha

## CLI-001：候选冻结和版本一致性

- 从最新 `develop` 建候选分支；
- 冻结非必要功能；
- 校验 `VERSION`、`pyproject.toml`、WebUI 版本及 Release Notes；
- 审计所有 workflow 的 Tag pattern。

### 强制 Tag 冲突检查

候选 Tag 推送前，列出所有匹配 `push.tags` 的 workflow。如果候选 Tag 会触发非目标发布工作流，必须先通过独立 PR 修复 trigger；禁止“推了再看”。

### PASSED 条件

版本、Head、目标 workflow、制品名、channel、回滚版本全部唯一确定。

---

## CLI-002：Core dry run

```bash
gh workflow run release.yml \
  --repo yuanchenglu/deepseekagent \
  --ref <candidate-branch> \
  -f version=<X.Y.Z-alpha.N> \
  -f dry_run=true
```

下载 artifact，验证：

- gitleaks；
- Core-only 边界；
- tarball、checksum、manifest；
- Python 许可证；
- smoke install；
- `deepagent --version`。

### PASSED 条件

最终候选 Head 对应的 dry-run 全部成功，artifact digest 已记录。

---

## CLI-003 至 CLI-008：干净 Mac 与共存

固定顺序：首次安装 → 真实模型任务 → 正常升级 → 覆盖安装 → 失败升级 → 自动回滚 → 卸载 → Hermes/OpenCode 共存。

每个步骤都记录：

- macOS 版本、芯片、用户是否新建；
- 安装来源 URL 与 checksum；
- 命令、退出码、PID、端口；
- `~/.deepagent` 前后快照；
- Hermes/OpenCode 配置与数据前后摘要；
- 未知用户文件是否保留；
- 失败注入方法和回滚版本。

任何步骤失败，修复代码并从 CLI-002 重新构建候选；不得在同一损坏环境继续凑齐后续结果。

---

## CLI-009：P0/P1 Gate

P0 示例：Secret 泄漏、数据删除、远程未授权暴露、无法启动/安装、升级破坏且无法回滚。  
P1 示例：核心真实任务失败、共存破坏、卸载误删、版本/channel 错误、可复现高频崩溃。

### PASSED 条件

范围内开放 P0=0、P1=0；任何豁免必须符合 Plan，P0 不得豁免。

---

## CLI-010：公开发布授权

Owner 必须使用固定格式：

```text
AUTHORIZE CLI-ALPHA-PUBLISH
Version:
Candidate Head SHA:
Tag:
Target GitHub Release: prerelease
Target R2 objects:
Target channel: alpha
Release Notes reviewed: yes
Rollback version/channel object:
Authorized by:
UTC time:
```

授权前只允许准备 Draft 和 dry run，不得推 Tag。

---

## CLI-011：发布

发布 Tag 前再次运行 Tag 冲突检查。`release.yml` 对 Tag push 会自动执行发布，禁止重复手工触发同一版本。

顺序：

1. 确认授权中的 Head；
2. 创建 annotated Tag；
3. 推送 Tag；
4. 监控唯一目标 workflow；
5. 验证 immutable objects readback；
6. 验证 GitHub Release；
7. 最后验证 alpha channel；
8. 若失败，按回滚方案恢复 channel，不覆盖不可变制品。

---

## CLI-012/013：公开回归与反馈

从公开 URL 重新下载，不使用本地产物缓存。完成安装、升级、失败升级、回滚和卸载。组织明确起止时间的 Alpha 测试周期，记录参与人数、环境、任务完成率、P0/P1 和退出标准。

只有反馈周期结束且 P0/P1=0，CLI-013 才 PASSED。

---

# 8. WebUI Beta

## WEB-001/002：迁移与失败回滚

准备至少三份数据：

- Alpha 正常数据；
- 边界数据；
- 故意损坏/不兼容数据。

对每份记录迁移前后 schema、行数、关键对象、备份、失败错误和回滚结果。

### PASSED 条件

正常迁移无数据丢失；失败迁移不破坏旧数据；重试可成功；回滚后 Alpha 仍可读取。

---

## WEB-003/004：生命周期与认证

在干净 Mac 执行：

```text
deepagent webui start
deepagent webui status
deepagent webui open
deepagent webui stop
```

验证 loopback、PID、端口、日志、Ticket → HttpOnly Cookie、非法/过期/重放 Ticket、URL Secret 清理、stop 后无残留进程。

---

## WEB-005：共存矩阵

至少覆盖安装顺序、并发启动、分别停止、端口冲突、配置目录、日志目录、CLI 与 WebUI 共用 Runtime、Hermes/OpenCode 不受影响。

---

## WEB-006：Beta dry run

```bash
gh workflow run release-webui-beta.yml \
  --repo yuanchenglu/deepseekagent \
  --ref <candidate-branch> \
  -f version=<X.Y.Z-beta.N> \
  -f publish=false
```

下载并验证 Core、WebUI Server、managed DeepCode 三类制品、许可证、checksum、manifest 和边界。

### Tag 风险

WebUI publish 要求 Tag 指向 Head。推 Tag 前必须确认该 Tag 不触发 `release.yml` 等非目标发布；若会触发，先修 workflow pattern。

---

## WEB-007 至 WEB-011

依次关闭 P0/P1、取得固定格式授权、发布不可变制品、最后提升 beta channel、从公开渠道验证迁移/安装/升级/回滚、完成外部 Beta 周期。

授权格式将 `CLI-ALPHA-PUBLISH` 替换为 `WEBUI-BETA-PUBLISH`，并明确 WebUI BSL-1.1 许可口径。

---

# 9. Electron Preview

## DESK-001：干净 Mac 下载与 checksum

```bash
gh workflow run release-electron-preview.yml \
  --repo yuanchenglu/deepseekagent \
  --ref <candidate-branch> \
  -f version=<X.Y.Z-preview.N> \
  -f publish=false
```

下载 DMG artifact，独立计算 SHA-256，与 `.sha256` 和 manifest 比较。

---

## DESK-002：Gatekeeper 手工路径

因为 Preview 无签名、未公证：

- 普通双击应观察真实 Gatekeeper 行为；
- 按文档右键 Open；
- 不允许要求用户关闭系统安全；
- 限制说明必须在 Release Notes、下载页和应用内一致；
- 记录 macOS 版本和完整交互结果。

---

## DESK-003 至 DESK-006

验证：

- DeepAgent/DeepCode 模式切换；
- 两种模式真实任务；
- 覆盖安装、升级、失败升级、回滚、卸载；
- Main crash、Runtime crash、PID 消失/重用、orphaned、Workspace Lease；
- CLI/WebUI/Desktop/Hermes/OpenCode 同机共存；
- 一个 Runtime 崩溃不影响另一个；
- 不同 Workspace 不误阻塞。

自动化证据不能替代这些真实 GUI/物理机证据。

---

## DESK-007 至 DESK-011

完成受控用户测试、P0/P1 清零、Owner 对“无签名 Preview”的明确公开发布授权、发布和 preview channel 最后提升、公开下载回归、反馈闭环。

授权必须写明：无签名、未公证、Gatekeeper 需要手工批准，Owner 接受该公开风险。

---

# 10. Stable

## STB-001：Apple 权限盘点

记录但不导出：Team ID、Developer ID Application identity、证书过期时间、notary profile 名称、CI Keychain 配置、最小权限责任人。

私钥、证书密码和 App Store Connect 密钥不得进入仓库或聊天。

---

## STB-002/003：签名、公证、stapling

必须验证：

```bash
codesign --verify --deep --strict --verbose=2 <DeepAgent.app>
spctl --assess --type execute --verbose=4 <DeepAgent.app>
xcrun stapler validate <DeepAgent.app-or-dmg>
```

同时审计 Hardened Runtime、Entitlements、嵌套二进制、Helper、Runtime 和 updater。

### PASSED 条件

干净 Mac 普通双击可启动，无右键绕过，无隔离属性手工清除。

---

## STB-004/005：正式更新链

建立签名 manifest/feed/channel，验证：

- 旧公开版本 → Stable 候选；
- checksum/signature；
- 下载中断；
- 损坏包；
- 失败安装；
- 自动回滚；
- channel 回滚；
- 卸载与数据保留。

---

## STB-006/007：全矩阵和 RC 冻结

执行 CLI、WebUI、Desktop、Hermes、OpenCode、真实模型、Workspace 并发、迁移、升级、回滚、卸载全回归。冻结 RC 后只允许修复阻断问题；任何代码变更都必须重新执行受影响 Gate。

---

## STB-008：最终授权

```text
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
```

缺任一字段不发布。

---

## STB-009：正式发布

顺序不可调整：

1. 最终候选 CI/Review；
2. 按 Plan 合入 `master`；
3. 确认 master SHA；
4. 创建 Tag；
5. 创建不可变制品；
6. 签名、公证、staple；
7. 上传并读回；
8. 发布 GitHub Release；
9. 最后提升 Stable channel；
10. 从公开端点复核；
11. 运行回滚演练。

任何中间失败，不得提升 Stable channel。

---

## STB-010 至 STB-012：发布后闭环

- 多台干净机公开下载；
- 旧版本升级；
- 新安装；
- 回滚；
- 错误监控；
- 用户反馈周期；
- P0/P1 处理；
- 最终 Plan、状态、测试报告、技术债务、索引、交接同步；
- `develop`、`master`、Tag、Release、Channels 一致性审计。

只有全部完成，才可宣布整个 Plan 完成。

---

# 11. 失败分类决策树

```text
测试失败？
├─ 可稳定复现
│  ├─ 代码/配置错误 → 修复、加回归测试、重新跑完整当前 Work ID
│  ├─ 测试错误 → 修测试，但必须证明生产行为正确
│  └─ 外部服务错误 → 保存证据，判断是否可重试或 BLOCKED
├─ 不可稳定复现
│  ├─ 先增加日志/探针/重试诊断
│  └─ 未定位前不得 PASSED
└─ 权限/设备/用户缺失
   ├─ 记录精确输入、Owner 步骤和验证方式
   └─ BLOCKED；继续所有不依赖该输入的合法任务
```

### 禁止的失败处理

- 仅重跑直到绿色；
- 删除失败日志；
- 降低断言；
- 将失败测试标记 skip；
- 使用旧 artifact；
- 把环境问题直接归咎于 GitHub；
- 在未定位根因时合并。

---

# 12. 上下文腐烂与交接规则

执行 AI 发现以下任一信号时，应先保存远程成果并生成新会话交接，不得继续凭记忆操作：

- 无法准确复述当前 Work ID、依赖和通过条件；
- 重复执行同一命令三次仍无新信息；
- 混淆 `develop`/`master`、候选 Head 或版本；
- 不确定某项是否已合并；
- 引用旧 SHA 与远程冲突；
- 工具进入循环；
- 上下文不足以完整检查 CI/Review。

新会话必须从 BOOT-001 重新审计，但不得重复已经有 PASSED 远程证据的 Work ID。

---

# 13. 最终完成判定

只有 `remaining-work-plan.json` 中所有任务均为 `PASSED`，且以下事实一致，才可宣布完成：

- Issue #21 已关闭并有脱敏证据；
- 全 refs 有效秘密为 0；
- Alpha、Beta、Preview、Stable 各 Gate 和反馈周期闭环；
- 签名、公证、更新链通过；
- P0/P1 为 0 或符合正式豁免；
- `develop`、`master`、Tags、Releases、Channels、Manifest、Checksum 一致；
- 最终 Head CI 成功且 Review 为 0；
- 没有关键成果只在本地；
- 发布后回归和反馈文档已合入。

在此之前只能报告“当前 Work ID 完成”，不能报告“整个 Plan 完成”。
