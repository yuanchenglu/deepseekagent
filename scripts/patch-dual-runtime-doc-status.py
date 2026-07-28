#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('docs/open-source-readiness')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f'{label} contract changed: expected one match, got {text.count(old)}')
    return text.replace(old, new)


plan_path = ROOT / '三阶段执行计划PLAN.md'
plan = plan_path.read_text(encoding='utf-8')
plan = replace_once(plan, '> **版本**：v2.7.0  ', '> **版本**：v2.8.0  ', 'PLAN version')
plan = replace_once(
    plan,
    '> **当前结论**：CLI Alpha、WebUI Beta、Electron Preview 均为 **No-Go**。主体工程已进入发布收敛后半程，当前只关闭真实并发、安全、干净机、共存和用户验收门禁，不扩张非必要功能。',
    '> **当前结论**：CLI Alpha、WebUI Beta、Electron Preview 均为 **No-Go**。双 Runtime 同 Workspace 并发与故障 E2E 已完成，当前唯一任务是 Owner 外部凭据轮换与旧凭据失效确认；不得并行跳过安全依赖。',
    'PLAN conclusion',
)
plan = replace_once(
    plan,
    '- PR #18 squash merge：`9e26f290c60544fc8a99cff8c31cecfbb8c99fd9`，同步 PLAN v2.7.0、状态和交接。\n- `master` 快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。',
    '- PR #18 squash merge：`9e26f290c60544fc8a99cff8c31cecfbb8c99fd9`，同步 PLAN v2.7.0、状态和交接。\n- PR #19 最终 Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`。\n- PR #19 squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`，完成双 Runtime E2E 和失败关闭修复。\n- `master` 快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。',
    'PLAN baseline',
)
plan = replace_once(
    plan,
    '| Electron Preview | 约 94%–95% | **No-Go** | 协议和真实 task/PID 生命周期完成；双 Runtime 真实并发、干净机、共存和用户验收未关闭 |',
    '| Electron Preview | 约 95%–96% | **No-Go** | 双 Runtime 真实并发与故障 E2E 已完成；凭据、历史、干净机、共存和用户验收未关闭 |',
    'PLAN progress row',
)
old_current = '''> PR #17 完成真实生命周期接入和监督器集成测试，但不等于两个真实 Runtime 在同一 Workspace 的端到端竞争已验证。

---

## 9. 当前唯一第一优先工程任务

### 双 Runtime 同 Workspace 并发与故障 E2E

必须在真实 DeepAgent / DeepCode Runtime 路径验证：

1. reader-reader 可以并行。
2. reader-writer 双向互斥。
3. writer-writer 互斥。
4. acquire 被拒绝时不得启动写任务或产生副作用。
5. 正常完成后释放租约。
6. 用户取消后释放或进入明确失败关闭状态。
7. heartbeat timeout 后，冲突 Runtime 仍不能进入双写窗口。
8. DeepAgent bridge 崩溃后，其任务统一 orphaned；确认退出或恢复后才释放/重建。
9. DeepCode 子进程崩溃或 PID 重用时，Main 正确识别和清理。
10. Main 重启后，存活 PID 可验证恢复；证据不足时保持 orphaned。
11. 一个 Runtime 崩溃不能破坏另一个 Runtime、窗口或无冲突 Workspace。
12. 测试保留远程可审计日志、状态快照和失败证据。

完成条件：

- 新增真实双 Runtime E2E harness 和用例；
- Browser E2E 与完整 Electron Preview workflow 在最终 PR Head 真实通过；
- 所有 actionable review 处理完成；
- 合入 `develop` 后更新 PLAN、状态、Electron 专项和交接。

完成本任务前，不并行启动后继工程任务。
'''
new_current = '''### 8.6 双 Runtime 同 Workspace 并发与故障 E2E

PR #19 已完成：

1. 使用生产客户端和同一 Main Supervisor 验证 reader-reader、reader-writer 双向互斥和 writer-writer。
2. acquire 被拒绝时 spawn 计数为 0，Workspace 无写副作用。
3. 正常完成、取消、heartbeat timeout、Bridge crash 和 DeepCode child crash 终态闭环。
4. PID 消失、PID 重用、Main/Runtime 重启和跨 Workspace 隔离通过。
5. 不可验证任务保持 orphaned 和 Workspace 锁，后台 PID 探测不自动释放。
6. acquire-before-bind 的无 PID orphaned 任务禁止盲目恢复，但允许原 Runtime 显式终止并释放。
7. 最终专项 E2E 6/6、Browser E2E 和完整 Electron Preview workflow 全部通过。
8. 唯一 P2 actionable review 已修复并解决，未解决 actionable thread 为 0。

完整证据：`12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`。

---

## 9. 当前唯一第一优先任务

### Owner Gate：轮换外部凭据并确认旧凭据失效

该任务必须由仓库 Owner / 外部平台管理员执行，当前环境不得代替 Owner 创建、查看或撤销真实 Secret。

完成条件：

1. 盘点所有曾进入代码、配置、日志、制品或 Git 历史的发布、对象存储和服务凭据。
2. 创建最小权限的新凭据并更新 GitHub / 外部平台 Secrets。
3. 使用新凭据完成隔离的最小读写验证，不创建公开 Release 或渠道。
4. 撤销旧凭据。
5. 使用旧凭据执行安全的最小只读验证，并确认认证失败或权限拒绝。
6. 将不含秘密值的脱敏证据提交远程。

Owner 操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

在该 Gate 关闭前，不得启动 Git 历史重写，也不得提升 Alpha、Beta、Preview 或 Stable 渠道。
'''
plan = replace_once(plan, old_current, new_current, 'PLAN current task')
plan = replace_once(
    plan,
    '''A. 双 Runtime 同 Workspace 并发与故障 E2E
→ B. 轮换外部凭据并确认旧凭据失效
→ C. 清理 Git 历史并重扫全部 refs''',
    '''A. ✅ 双 Runtime 同 Workspace 并发与故障 E2E
→ B. 【当前唯一 Owner Gate】轮换外部凭据并确认旧凭据失效
→ C. 清理 Git 历史并重扫全部 refs''',
    'PLAN sequence',
)
plan = replace_once(
    plan,
    '- Runtime Lease 协议和真实 task/PID 生命周期已进入 `develop`；\n- Browser E2E、WebUI、Electron Main 和无签名 DMG 自动门禁已通过；',
    '- Runtime Lease 协议、真实 task/PID 生命周期和双 Runtime 同 Workspace E2E 已进入 `develop`；\n- Browser E2E、WebUI、Electron Main 和无签名 DMG 自动门禁已通过；',
    'PLAN public allowed',
)
plan = replace_once(plan, '- 双 Runtime 真实并发已经验证；\n', '', 'PLAN public forbidden')
plan_path.write_text(plan, encoding='utf-8')

status = '''# DeepAgent 三阶段交付计划：真实进展状态

> 更新日期：2026-07-29  
> 状态：**当前进展事实层**  
> 远程仓库：`https://github.com/yuanchenglu/deepseekagent.git`  
> 开发分支：`develop`  
> 发布分支：`master`  
> 说明：总执行顺序以 `三阶段执行计划PLAN.md` v2.8.0 为准。最新 Head、PR、CI、Release 和 review 必须实时读取。

---

## 1. 已确认远程基线

| 项目 | 已确认事实 |
|---|---|
| PR #15 | Runtime Task / Workspace Lease 协议已合入 |
| PR #17 | 真实 Main/Runtime task 与 PID 生命周期已合入 |
| PR #18 | PLAN v2.7.0、状态和交接已同步 |
| PR #19 Head | `26295dda9644df016353bd7fa9c5bac6b0f13c04` |
| PR #19 squash merge | `f1f9457e0443db74e9aab9ceb0ea28405917db3a` |
| Runtime 双路径 E2E | 6/6，通过 run `30383776537` |
| Browser E2E | 最终 Head 通过 run `30383777443` |
| Electron workflow | 最终 Head 通过 run `30383776723` |
| review | 唯一 P2 actionable thread 已修复并解决；未解决 actionable thread 为 0 |
| master 快照 | `b3943ac43f0f0f6a1f86f5f2cb9a230527389d91` |
| 发布动作 | 未创建 Tag、Release 或公开渠道 |
| 本地未推送关键工作 | 无；关键成果均存在 GitHub 远程 |

完整 E2E 证据：`12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`。

---

## 2. 总体进度

| 阶段 | 工程实施进度 | 发布状态 | 当前结论 |
|---|---:|---|---|
| CLI Alpha | 约 90%–95% | **No-Go** | 主体代码接近完成；凭据、历史、干净机、真实模型和 P0/P1 未关闭 |
| WebUI Beta | 约 90%–92% | **No-Go** | Browser E2E 和核心自动化完成；迁移、共存、正式渠道和外测未关闭 |
| Electron Preview | 约 95%–96% | **No-Go** | 双 Runtime E2E 完成；凭据、历史、干净机、共存和用户验收未关闭 |

**整体判断**：主体工程处于发布收敛后半程。当前不新增非必要功能。

---

## 3. CLI Alpha

### 已完成

- 产品目录隔离；
- Core-only 制品路径；
- Manifest、SHA-256、渠道和版本一致性契约；
- 安装、更新、回滚和清单驱动卸载主体；
- CLI 入口、错误边界、治理和许可文档。

### 阻断项

1. 外部凭据轮换与旧凭据失效确认；
2. Git 历史有效秘密清理和全 refs 重扫；
3. 干净 Apple Silicon Mac 生命周期验收；
4. Hermes/OpenCode 共存验证；
5. 正式支持模型的真实 Agent 任务；
6. P0/P1 清零。

结论：**No-Go**。

---

## 4. WebUI Beta

### 已完成

- 一次性 Ticket → HttpOnly Session Cookie；
- 非法、失效、重放 Ticket 和 URL 清理；
- Browser E2E；
- WebUI 测试、构建、静态 i18n 和许可证审计；
- `deepagent webui start/open/status/stop` 主体；
- 默认 loopback、独立 PID/日志/端口/数据目录；
- 无固定默认密码和默认 LAN 暴露。

### 阻断项

1. Alpha → Beta 数据迁移和失败回滚；
2. 干净机 WebUI 生命周期；
3. CLI/WebUI/Hermes/用户 OpenCode 共存矩阵；
4. 官网和正式 Beta 渠道验证；
5. 外部测试周期及 P0/P1 清零。

结论：**No-Go**。

---

## 5. Electron Preview

### 已完成

- DeepAgent / DeepCode 双模式架构；
- Renderer Workspace Lock 和所有权隔离；
- 正式发布 concurrency 隔离；
- Main 权威 Runtime Task / Workspace Lease 协议；
- 真实 task/PID 生命周期；
- DeepAgent Bridge PID 和 DeepCode acquire-before-spawn / child PID；
- heartbeat、timeout、process-exit、runtime-crash 和 Main restart；
- POSIX/Windows PID 指纹；
- orphaned 失败关闭和 Supervisor Token 隔离；
- 双 Runtime 同 Workspace 并发与故障 E2E；
- acquire 拒绝后零 spawn / 零 Workspace 写副作用；
- 不可验证 PID 与 acquire-before-bind 重启边界；
- Browser、WebUI、许可证、Electron Main、DMG 和 artifact 全链路。

### 当前唯一任务

**Owner Gate：外部凭据轮换与旧凭据失效确认**。

操作规范：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

### 后继阻断项

- Git 历史清理和全 refs 重扫；
- 干净 Apple Silicon Mac 安装、Gatekeeper、升级、回滚和卸载；
- CLI/Desktop/Hermes/OpenCode 共存；
- 真实模型和真实用户 Preview；
- P0/P1 清零。

结论：**No-Go**。

---

## 6. 下一执行顺序

```text
1. 【当前 Owner Gate】轮换凭据并确认旧凭据失效
2. 清理 Git 历史并重扫全部 refs
3. 干净 Mac 验证 CLI/WebUI/Electron 生命周期
4. CLI/Desktop/Hermes/OpenCode 共存
5. 正式模型任务和真实用户 Preview 测试
6. 清零 P0/P1
7. 按 Go/No-Go 提升 Alpha、Beta、Preview 渠道
```

每次只启动一个依赖已经满足的工作单元。

---

## 7. 对外表述边界

可以说明双 Runtime 同 Workspace 并发与故障 E2E 已完成并合入 `develop`。

不得声称：

- Electron Preview 已发布；
- DMG 已签名或公证；
- 任一阶段已达到 Go；
- 凭据、历史、干净机、共存或用户验收已关闭。
'''
(ROOT / '00-THREE-PHASE-DELIVERY-STATUS.md').write_text(status, encoding='utf-8')

electron = '''# Electron Preview 继续开发状态

> 更新日期：2026-07-29  
> 当前代码基线：`develop@f1f9457e0443db74e9aab9ceb0ea28405917db3a`  
> 双 Runtime E2E 合并：PR #19  
> 本文是 Electron Preview 专项事实层；冲突处以最新远程代码、`三阶段执行计划PLAN.md` v2.8.0 和总状态文档为准。

---

## 1. 当前结论

Electron Preview 工程实施约 **95%–96%**，发布结论仍为 **No-Go**。

已完成自动化工程主链路：

- DeepAgent / DeepCode 双模式；
- Renderer Workspace Lock；
- Runtime Task / Workspace Lease 协议；
- 真实 task/PID 生命周期；
- 双 Runtime 同 Workspace 并发与故障 E2E；
- heartbeat、崩溃、PID 复用和 Main/Runtime 重启恢复；
- Browser E2E；
- WebUI、Electron Main、许可证和无签名 DMG 全链路。

尚未完成凭据与历史安全门禁、干净物理 Mac、共存、真实模型和真实用户验收。

---

## 2. 已完成能力

### 2.1 Workspace Lock 与 Renderer 所有权

- reader-reader 并行；
- reader-writer 双向互斥；
- writer-writer 互斥；
- `webContents.id + taskId` 所有权隔离；
- Renderer 无法释放其他 Renderer 的锁；
- Renderer 销毁后 Main 自动回收 Renderer 租约。

### 2.2 无签名 Apple Silicon DMG

- `mac.identity: null`；
- CI 不依赖签名凭据；
- 验证 Bundle ID、版本、arm64、安装器和未签名状态；
- Manifest 明确 `signed=false`、`notarized=false`；
- 首次启动需要 Gatekeeper 人工批准。

不得将制品描述为已签名、公证或 Stable。

### 2.3 正式发布 concurrency

PR #13 已验证 PR 验证与正式发布隔离，`publish=true` 正式运行不被后续运行取消，GitHub prerelease 与 R2 channel 发布事务串行排队。

### 2.4 Runtime Lease 协议

PR #15 已完成 Main 唯一权威协调器、Runtime Adapter/Main-only 监督事件、幂等、有界重放、orphaned 失败关闭和状态机契约。

### 2.5 真实 task/PID 生命周期

PR #17 已完成：

- Electron Main 持久化、认证的 Runtime Task Supervisor；
- DeepAgent session task 绑定共享 Bridge PID；
- DeepCode acquire-before-spawn 并绑定真实 child PID；
- heartbeat、timeout、完成、取消、process-exit、runtime-crash 和 Main shutdown；
- Main 重启后的 PID 指纹验证和显式 resume；
- POSIX 与 Windows 进程证据；
- Runtime 级 orphaned；
- Supervisor Token 子进程隔离；
- `webUiHome()` 状态作用域；
- stale socket `EPIPE` 修复。

### 2.6 双 Runtime 同 Workspace E2E

PR #19 已完成：

- 生产客户端真实竞争同一 Main Supervisor；
- reader-reader、reader-writer、writer-writer；
- acquire 拒绝后零 spawn 和零写副作用；
- 完成、取消、timeout、Bridge/child crash；
- PID 消失、PID 复用、Main/Runtime 重启；
- 不可验证任务持续 orphaned 和持锁；
- acquire-before-bind 无 PID orphaned 的显式终止清理；
- 跨 Runtime / Workspace 故障隔离。

最终证据：

- Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`；
- merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`；
- Runtime E2E：run `30383776537`，6/6；
- Browser：run `30383777443`；
- Electron：run `30383776723`；
- Review：未解决 actionable thread 为 0。

详见 `12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`。

---

## 3. 当前唯一任务

### Owner Gate：外部凭据轮换与旧凭据失效确认

必须由 Owner / 外部平台管理员执行：

1. 盘点所有发布、对象存储和服务凭据；
2. 创建并安装最小权限新凭据；
3. 完成隔离读写验证；
4. 撤销旧凭据；
5. 验证旧凭据认证失败；
6. 提交不含秘密值的证据。

操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

---

## 4. 后继阻断项

- 清理 Git 历史并重扫全部 refs；
- 在干净 Apple Silicon Mac 下载、安装和启动 DMG；
- Gatekeeper、覆盖安装、升级、失败升级、回滚和卸载；
- CLI/Desktop/Hermes/OpenCode 共存；
- 真实模型和真实用户 Preview；
- P0/P1 清零。

---

## 5. 发布边界

无签名 DMG 只能称为 **Electron Preview candidate artifact**，不能称为已发布 Preview。

公开 prerelease 的剩余必要条件：

```text
凭据与历史安全门禁
+ 干净机
+ 共存验证
+ 真实模型与用户验收
+ P0/P1 清零
```

随后才可在 Owner 明确授权后执行：

```text
创建 preview.N Tag
→ workflow_dispatch(publish=true)
→ 发布无签名 Electron Preview
```
'''
(ROOT / '10-ELECTRON-PREVIEW-STATUS.md').write_text(electron, encoding='utf-8')

handoff = '''# DeepAgent 三阶段计划交接（更新于 2026-07-29）

> 用途：新会话仅依赖 GitHub 远程继续执行计划或制作对外内容。  
> 唯一事实源：GitHub 远程仓库。  
> 禁止依赖：旧容器、旧工作区、未推送文件和上一会话临时日志。  
> 完整计划：`三阶段执行计划PLAN.md` v2.8.0。

---

## 一、新会话直接复制的交接提示词

```text
@GitHub yuanchenglu/deepseekagent

你现在接手 GitHub 仓库 `yuanchenglu/deepseekagent` 的三阶段产品与开源发布计划。GitHub 远程仓库是唯一事实源；不要依赖旧容器、旧工作区、上一会话日志或未推送文件。

开始前重新读取：

1. 根目录 `AGENTS.md`
2. `docs/open-source-readiness/00-INDEX.md`
3. `docs/open-source-readiness/三阶段执行计划PLAN.md`（v2.8.0 或更新）
4. `docs/open-source-readiness/00-THREE-PHASE-DELIVERY-STATUS.md`
5. `docs/open-source-readiness/07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md`
6. `docs/open-source-readiness/08-PHASE-2-WEBUI-STABLE-BETA.md`
7. `docs/open-source-readiness/09-PHASE-3-DUAL-MODE-ELECTRON.md`
8. `docs/open-source-readiness/10-ELECTRON-PREVIEW-STATUS.md`
9. `docs/open-source-readiness/11-RUNTIME-TASK-WORKSPACE-LEASE-PROTOCOL.md`
10. `docs/open-source-readiness/12-DUAL-RUNTIME-WORKSPACE-E2E-REPORT.md`
11. `docs/open-source-readiness/13-OWNER-CREDENTIAL-ROTATION-GATE.md`
12. 所有测试、Bug 和技术债务文档
13. 最近至少 30 个 develop commits
14. 开放 PR、review threads、失败/排队/执行中的 Actions
15. 领先 develop 但未合入的远程分支
16. develop/master Head、Tag、Release 和渠道状态

历史稳定基线：

- PR #15：Runtime Task / Workspace Lease 协议
- PR #17：真实 task/PID 生命周期
- PR #18：PLAN v2.7.0 和交接同步
- PR #19 最终 Head：26295dda9644df016353bd7fa9c5bac6b0f13c04
- PR #19 squash merge：f1f9457e0443db74e9aab9ceb0ea28405917db3a
- master 历史快照：b3943ac43f0f0f6a1f86f5f2cb9a230527389d91

PR #19 已完成双 Runtime 同 Workspace 并发与故障 E2E：

- production-client 真实竞争同一 Main Supervisor
- reader-reader、reader-writer 双向互斥、writer-writer
- acquire 拒绝后不得 spawn 或写 Workspace
- 完成、取消、timeout、Bridge crash、DeepCode child crash
- PID 消失、PID 重用、Main/Runtime 重启
- 不可验证任务保持 orphaned 和持锁
- acquire-before-bind 无 PID orphaned 任务只能显式终止，禁止盲目绑定新 PID
- 跨 Runtime 和跨 Workspace 隔离

最终 CI：

- Runtime E2E run 30383776537：6/6 success
- Browser run 30383777443：success
- Electron run 30383776723：success
- 唯一 P2 review 已修复并解决；未解决 actionable thread 为 0

当前三阶段仍全部 No-Go。未创建 Tag、Release 或公开渠道。

当前唯一合法任务是 Owner Gate：轮换所有外部发布、对象存储和服务凭据，并确认旧凭据失效。严格按 `13-OWNER-CREDENTIAL-ROTATION-GATE.md` 执行。

该 Gate 需要 Owner / 外部平台管理员权限。不得要求 AI 查看或接收明文 Secret。Owner 需要：

1. 盘点凭据；
2. 创建最小权限新凭据；
3. 更新 GitHub / 外部平台 Secret；
4. 验证新凭据的隔离读写；
5. 撤销旧凭据；
6. 验证旧凭据认证失败；
7. 提交脱敏证据。

在凭据 Gate 关闭前，不得启动 Git 历史重写，也不得发布 Alpha、Beta、Preview 或 Stable。

Gate 关闭后的唯一下一任务：清理 Git 历史中的有效秘密，并重扫全部 Git refs。

开发流程：优先功能分支 → PR → CI → review → develop；直推 develop 仅作为异常兜底，并必须记录问题原因和技术债务。每个工作单元完成后同步 Plan、状态、测试证据和交接，不等待用户反复发送“继续”。

对外可以表述双 Runtime E2E 已完成并合入 develop；不得声称 Electron Preview 已发布、DMG 已签名/公证、任一阶段已 Go，或凭据/历史/干净机/共存/用户验收已关闭。
```

---

## 二、远程保存状态

- PR #19 工程代码已进入 `develop@f1f9457e0443db74e9aab9ceb0ea28405917db3a`。
- E2E 报告和 Owner Gate 操作清单已进入远程文档分支/PR。
- 当前没有只存在于旧容器的关键成果。

---

## 三、发布纪律

当前 CLI Alpha、WebUI Beta、Electron Preview 均为 **No-Go**。未经明确授权不得创建 Tag、Release、公开 Preview channel、Stable channel 或不可逆公开帖子。
'''
(ROOT / 'HANDOFF_2026-07-28.md').write_text(handoff, encoding='utf-8')

index = '''# DeepSeekAgent 开源准备文档集

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
14. [00-THREE-PHASE-DELIVERY-STATUS.md](./00-THREE-PHASE-DELIVERY-STATUS.md) — 三阶段真实进度和阻断项。
15. [三阶段执行计划PLAN.md](./三阶段执行计划PLAN.md) — 唯一执行顺序和 Go/No-Go 规则。
16. [HANDOFF_2026-07-28.md](./HANDOFF_2026-07-28.md) — 新会话交接提示词。

原 `07-OPEN-SOURCE-ITERATION-PLAN.md` 仅作历史审计记录，不再是执行依据。

## 已确认远程基线

- PR #17：真实 task/PID 生命周期。
- PR #18：PLAN v2.7.0 和交接同步。
- PR #19 Head：`26295dda9644df016353bd7fa9c5bac6b0f13c04`。
- PR #19 squash merge：`f1f9457e0443db74e9aab9ceb0ea28405917db3a`。
- `master` 历史快照：`b3943ac43f0f0f6a1f86f5f2cb9a230527389d91`。
- 最新 Head、开放 PR、Actions、Tag 和 Release 必须实时读取。

## 当前唯一优先级

双 Runtime E2E 已完成。当前唯一任务：

> **Owner Gate：轮换外部凭据并确认旧凭据失效**

操作清单：`13-OWNER-CREDENTIAL-ROTATION-GATE.md`。

完成前不得启动 Git 历史重写或提升任何发布渠道。

## 当前发布结论

- CLI Alpha：No-Go
- WebUI Beta：No-Go
- Electron Preview：No-Go

未创建 Tag、Release 或公开 Preview channel。无签名 DMG 是候选 artifact，不是已发布产品。

## 决策原则

- 代码实现、自动化通过、真实环境验收和公开发布必须严格区分。
- 不把模型能力当作权限、安全或一致性保证。
- 发布门禁必须失败关闭。
- 核心功能必须有状态机、错误边界、可观测性和测试证据。
- `develop` 是开发分支；`master` 只接收通过发布门禁的版本。
- GitHub 远程是唯一事实源。
'''
(ROOT / '00-INDEX.md').write_text(index, encoding='utf-8')

tech_debt = '''# 技术债务与外部门禁追踪

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
'''
Path('docs/TECH_DEBT.md').write_text(tech_debt, encoding='utf-8')

print('synchronized Plan v2.8.0, status, Electron, handoff, index, and technical debt')
