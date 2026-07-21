---
name: github-profile-optimization
description: Optimize a GitHub personal profile for job-seeking visibility — profile README, pinned repos, descriptions, topics, bio, and cleanup of old repos.
category: github
metadata:
  hermes:
    tags: [github, profile, job-seeking, portfolio, optimization]
---

# GitHub Profile Optimization

优化 GitHub 个人主页，使其对技术招聘方（尤其是 AI/Agent/ML 方向）更具吸引力。

## When to Use

- 用户想让 GitHub 主页对特定公司（如 DeepSeek、OpenAI）更有吸引力
- 主页显示的是老项目，而非当前重点方向
- 用户想创建或改进 Profile README
- 用户有私有仓库需要选择性公开
- 需要清理大量老旧 fork

## Workflow

### Phase 1: Audit（审计）

1. 浏览用户 GitHub Profile 和 Repos 页面
2. 识别：「Popular repositories」显示了什么、哪些是旧的、哪些是私有的
3. 对照用户目标岗位的 JD，判断哪些仓库是信号、哪些是噪音
4. 用 `gh api` 拉取私有仓库列表供用户确认

### Phase 2: Profile README

1. 创建与 GitHub 用户名**完全同名**的公开仓库
   ```bash
   gh repo create <username> --public --description "..." 
   ```
2. 通过 API 直接推送 `README.md`（无需 clone）
   ```bash
   gh api repos/<owner>/<repo>/contents/README.md --method PUT --input - <<< '{"message":"...","content":"<base64>","branch":"main"}'
   ```
3. README 自动渲染在个人主页左侧

### Phase 3: 仓库元数据

设置 Description 和 Topics（影响 GitHub 搜索排名）：

```bash
# 设置描述
gh api repos/<owner>/<repo> --method PATCH -f description="..."

# 设置 topics（最多 20 个）
gh api repos/<owner>/<repo>/topics --method PUT -f names[]="topic1" -f names[]="topic2"
```

Topics 应包含目标岗位的关键词（如 `agent`、`harness`、`deepseek`、`llm` 等）。

### Phase 4: 清理老旧仓库

1. 列出所有 fork：
   ```bash
   gh api users/<user>/repos?per_page=100 --jq '.[] | select(.fork == true) | {name, pushed_at, language, stargazers_count}'
   ```
2. 按类别分组呈现给用户（如：Miracast 系列、Vim 配置类、其他零散 fork）
3. 用户确认后执行删除

### Phase 5: 置顶仓库（⚠️ 必须手动操作）

**GitHub 不提供任何 API 来置顶用户主页仓库。**

- GraphQL API：无 `pinRepository` mutation
- REST API：无 `/user/pinned_items` 端点
- `gh` 扩展（如 `emberlamp/gh-pin-repo`）：仅支持组织，不支持个人用户

**手动操作步骤（30 秒）：**
1. 打开 `https://github.com/<username>`
2. 找到「Popular repositories」区域，点击右侧「Customize your pins」
3. 勾选 6 个仓库 → Save

置顶后会替换「Popular repositories」自动列表。

### Phase 6: 更新 Bio（需要 `user` scope）

```bash
gh api user --method PATCH -f bio="..."
```

⚠️ Token 必须有 `user` scope。默认 `gh auth login` 的 scope（`repo`、`read:org`）不含 `user`，会返回 404。需重新生成 token。

## 关键陷阱

1. **置顶无 API — 不要浪费时间尝试。** GraphQL/REST 都调不通，直接告诉用户手动操作。
2. **Profile README 渲染有延迟。** 推送后 GitHub 缓存 2-5 分钟，不要立即判断失败。
3. **Bio 需要 `user` scope。** 现有 token 若无此 scope，更新会 404。
4. **删除仓库前必须用户确认。** 即使是 2015 年的 Miracast fork 也要先问。
5. **私有仓库公开前需要去隐私。** 检查 README 中的账号密码、密钥等。

## Profile README 模板

见 `references/profile-readme-template.md`
