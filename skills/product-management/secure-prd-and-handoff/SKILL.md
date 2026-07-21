---
name: secure-prd-and-handoff
description: "撰写 PRD 时的安全规范和 AI 研发小组交接边界——不在 PRD 中写明文凭证、不替 AI 做实施决策、正确的手续点。配合 product-rd-workflow 总纲使用。"
version: 1.0.0
metadata:
  hermes:
    tags: [prd, security, workflow, handoff, process]
    related_skills: [product-rd-workflow, writing-plans, opencode]
---

# PRD 安全规范与 AI 研发小组交接边界

> 复盘来源：2026-07-01 DeepAgent Release 安装系统 PRD 流程。
> 本 Skill 是对 product-rd-workflow 总纲的补充细则，不替代总纲。

---

## 一、PRD 中的凭证安全铁律

**永远不要在 PRD 文档中写入任何凭证明文值。**

| ❌ 禁止 | ✅ 正确做法 |
|---------|------------|
| `API Key: sk-xxx...` | `${API_KEY}` 占位符 |
| `Secret: abc123...` | `${SECRET_KEY}` 占位符 |
| Cloudflare Token 明文 | `${CF_API_TOKEN}` 占位符 |
| R2 Secret Access Key | `${R2_SECRET_ACCESS_KEY}` 占位符 |
| 数据库密码 | `${DB_PASSWORD}` 占位符 |

**凭证存放层级**：

```
~/.deepagent/.env          ← 个人开发/日常使用（已被 git 忽略）
~/.hermes/.env             ← Hermes 个人配置
<project>/.env             ← 项目级配置（已被 .gitignore 忽略）
环境变量                    ← CI/CD / 生产部署
```

如果用户意外将凭证明文放到 PRD 中：

1. 立即从 PRD 中删除明文
2. 将凭证写入安全的 `.env` 文件（如 `~/.deepagent/.env`）
3. PRD 中使用环境变量占位符引用（如 `${CF_ACCOUNT_ID}`）
4. 检查 git 状态确保没有 commit 包含凭证

---

## 二、AI 研发小组交接边界

### 关键原则

> **我是数字分身，不是技术架构师。**
> 我的强项在需求理解和过程管控，不在技术实施决策。

### 各阶段我该做什么/不该做什么

| 阶段 | 我的职责 | ❌ 不要替 AI 做的事 |
|------|---------|-------------------|
| PRD 撰写 | 写"要什么"、"为什么"、约束条件 | 写"怎么实现"的具体方案 |
| 用户确认 | 和用户确认需求正确性 | 替 AI 决定实施细节 |
| 交给 AI 审查 | 准备 PRD 和上下文 | 提前决定凭证放哪、路径用啥 |
| AI 出计划 | 审查计划是否完整 | 替 AI 写技术方案 |
| AI 执行 | 监管进度，纠正跑偏 | 中途插入技术架构决策 |

### 交接触发点（三问自检）

把 PRD 交给 AI 研发小组前，问自己三个问题：

1. **有没有替 AI 决定"怎么做"？** → 如果有，删掉，只留"做什么"
2. **PRD 里有没有明文凭证？** → 如果有，立即删除
3. **AI 小组会不会对这个需求有疑问？** → 如果有疑问是正常的，等 AI 审查时来问你

### 典型错误模式

```
❌ 错误：PRD 写完后自己决定凭证存哪、路径用哪个、装哪个工具
   └→ 这是越权替 AI 做技术决策

✅ 正确：PRD 写完后交给 AI，让 AI 阅读、审查、出方案
   └→ AI 自己会决定凭证管理方式和实施细节
   └→ AI 有疑问时会主动来确认
```

---

## 三、典型复盘案例

### 案例：Release 安装系统 PRD

**背景**：撰写 DeepAgent Release 安装系统的 PRD（2026-07-01）。

**错误**：
1. PRD 末尾被贴了 Cloudflare 全套凭证（Global API Key、R2 Token、S3 Secret Access Key）
2. 用户确认 PRD 后，我直接替 OpenCode 决定了凭证存放位置和替换方案
3. 用户纠正："你是不是搞错了？流程是什么样子的？"

**改正**：
1. 从 PRD 删除凭证明文 → 存入 `~/.deepagent/.env`
2. PRD 只保留环境变量占位符
3. 确认 PRD 后交给 OpenCode 审查，不自己替它做决定

---

## 四、关联工具

- `product-rd-workflow`：8 阶段产研流程总纲（必须先加载）
- `writing-plans`：写实施计划模板
- `opencode`：OpenCode CLI 命令速查（含 OMO 项目级配置方法）
