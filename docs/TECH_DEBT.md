# 技术债务追踪

## 1. 落地页中文化（stash 中保留）

**位置：** Git stash（原 stash@{1}，标签：`WIP on master: security: redact 3 real API keys`）

**涉及文件：** `landingpage/index.html`、`landingpage/script.js`、`landingpage/style.css`、`package.json`、`package-lock.json`

**内容摘要：**
- 落地页从英文改为中文
- 新增"应用场景"（Use Cases）板块
- 新增"一人公司"架构图
- 新增成本对比表
- 安装说明改为 5 步流程
- 终端演示 demo 改为 SaaS 项目搭建场景
- 移除了 ASCII art 和折叠规格列表
- 新增 `marked` 依赖

**状态：** WIP，不继续开发，保留在 stash 中。

**恢复方式：** `git stash apply stash@{0}`（在 2026-07-23 stash 清理后此 stash 变为 @{0}，应用前请先 `git stash list` 确认。）

---

## 2. 残留未跟踪文件（待评估）

以下文件不属于本次清理范围，当前保留在仓库中未跟踪。需要后续决定：提交到仓库、删除、或移到 Obsidian。

| 文件 | 建议 |
|------|------|
| `overview.md` | 待评估（落地页描述文档） |
| `plan-websites.md` | 待评估（产品矩阵规划文档） |
| `docs/API_REFERENCE.md` | 待评估（API 参考文档） |
| `docs/refactor/` | 待评估（重构文档目录） |
| `website/docs/reference/developer-api-reference.md` | 待评估（开发者 API 参考） |
| `website/docs/reference/python-api-reference.md` | 待评估（Python API 参考） |
