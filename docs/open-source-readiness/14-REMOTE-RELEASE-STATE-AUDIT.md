# GitHub Tag、Release、Actions 与公开渠道远程审计

> PR #23 squash merge：`09aae3829afeeb4d1750ad96a671ebde3611785a`  
> 观测时间（UTC）：`2026-07-28T18:19:18.748426+00:00`  
> 仓库：`yuanchenglu/deepseekagent`  
> 审计 workflow run：`30386865073`  
> 审计 artifact：`8699299635`  
> Artifact digest：`sha256:6c6b722661f6d25597ee53ef8057505495683df1e0ef2e5bd0fbd743b2492188`  
> 性质：**只读审计；未创建、修改或删除 Tag、Release、Channel 或 Secret。**

## 1. 当前事实摘要

审计时点：

- 默认分支：`develop@f9b39ddbb745321b43e575937c7dd3ff15cf9b4a`
- 开放 PR：1，即本审计 PR #23
- Tags：**0**
- GitHub Releases：**0**，包括 Draft 和 Prerelease
- 当前 Active Actions：**0**，已排除审计 workflow 自身
- 当前引用 Head 上的失败类 Actions：**0**
- 历史或已被新 Head 取代的失败/取消 Actions：**132**

“当前引用 Head”包括默认分支最新 Head 和所有开放 PR 的最新 Head。旧 PR Commit、旧分支 Commit、旧 `develop` Commit 或已被后续提交替代的失败运行保留为历史证据，但不构成当前 Head 阻塞。

## 2. Tags

未发现任何 Git Tag。

## 3. GitHub Releases

未发现任何 GitHub Release，包括：

- Draft Release
- Prerelease
- 正式 Release

因此当前不存在可由 Tag 或 GitHub Release 识别的 Alpha、Beta、Preview 或 Stable 发布。

## 4. 当前 Actions 状态

### 4.1 Active Actions

无 queued、in-progress、waiting、requested 或 pending 运行。

### 4.2 当前引用 Head 的失败运行

无。

### 4.3 历史失败/取消运行

GitHub Actions API 完整扫描得到 132 条历史失败类记录：

| Conclusion | 数量 |
|---|---:|
| `cancelled` | 88 |
| `failure` | 44 |

按分支聚合的主要来源：

| Branch | 数量 |
|---|---:|
| `chatgpt/runtime-task-pid-lifecycle` | 51 |
| `chatgpt/dual-runtime-workspace-e2e` | 33 |
| `chatgpt/electron-preview-release-gate` | 28 |
| `chatgpt/runtime-task-lease-protocol` | 8 |
| `chatgpt/workspace-lock-ownership` | 3 |
| `chatgpt/auth-ticket-browser-e2e` | 3 |
| `chatgpt/sync-post-runtime-lease-protocol` | 2 |
| `chatgpt/sync-dual-runtime-e2e-status` | 1 |
| `develop` | 1 |
| `chatgpt/webui-browser-e2e` | 1 |
| `master` | 1 |

其中两个需要单独说明的历史分支运行：

- `develop` 历史失败：run `30294872846`，Head `386ca6f0e2a967b8b9c74309becb2e6608e3b760`，已被当前 `develop` 多次推进取代。
- `master` 历史失败：run `28570812931`，Head `856f910f1a3abd9e06bd0abc5fe9aa166920b9a6`，发生于 2026-07-02 的手工 `Release Build & Publish`，不是当前 `master` Head。

完整 132 条逐项记录保存在 run `30386865073` 的 `remote-release-audit.json` artifact 中。不得删除历史失败来伪造成功；也不得用历史失败覆盖最终 Head 的成功证据。

## 5. 公开发布渠道

审计以下公开端点：

| Channel | 公开端点 | HTTP | JSON | 响应 SHA-256 |
|---|---|---:|---|---|
| CLI Alpha | `/releases/channels/alpha.json` | 404 | 无 | `b63300542e6c99d9f0d546a40d21373e648cec1ff205372c22bd04ff3f677ba8` |
| WebUI Beta | `/releases/channels/beta.json` | 404 | 无 | `117814d0051370ba603efbaf214568049623541997c8ba11c857fb4b08ea8a59` |
| Core Stable | `/releases/channels/stable.json` | 404 | 无 | `16fd40dfe350de6ca9f9399b41e47875b8ed3d8035b58e93e85f0641f862db97` |
| Electron Preview | `/releases/desktop/channels/preview.json` | 404 | 无 | `dfbf37e2ece0203ae2c69fbc15c696355441313c97c88f943d83387b25bbd95f` |
| Electron Stable | `/releases/desktop/channels/stable.json` | 404 | 无 | `03ea14d290f94f4ecc48910877359f6c3ab00e8dab908f008507db35156183ca` |

结论：当前公开渠道均未建立，不存在公开可消费的 Alpha、Beta、Preview 或 Stable channel manifest。

## 6. Review 与 API 契约闭环

PR #23 的两个 actionable review 已处理并解决：

1. 所有 active status 查询均显式分页，超过安全上限时失败关闭；
2. 失败类运行只使用 GitHub 文档支持的 `status=completed` 查询，再本地过滤 `conclusion`；不依赖未文档化的 `status=startup_failure`。

最终 reviewed Head 的 workflow run `30386865073` 通过，未解决 actionable thread 为 0。

## 7. 与当前 Plan 的关系

本报告关闭了开始前远程审计中的 Tag、Release、Actions 和公开渠道枚举缺口，但不改变 Plan v2.8.0 的依赖顺序。

当前唯一合法任务仍为：

> **Owner Gate：轮换外部凭据并确认旧凭据失效。**

Gate 关闭前：

- 不执行 Git 历史重写；
- 不创建 Tag 或 Release；
- 不提升 Alpha、Beta、Preview 或 Stable channel；
- 不把无签名 DMG 称为已发布产品。

## 8. 可重复审计工具

PR #23 新增：

- `.github/workflows/remote-release-state-audit.yml`
- `scripts/audit-remote-release-state.py`

Workflow 仅具备：

- `contents: read`
- `actions: read`

它在 PR 和 `develop` push 后均会运行，可在后续每个发布 Gate 前重复审计：

- Tags
- Releases
- 当前和历史 Actions
- 开放 PR 最新 Head
- 五个公开发布渠道

该工具不具备发布或仓库写权限。
