# DeepSeek 产品矩阵官网方案

## 一、项目背景

5 个产品 + 1 个主站，统一放在 `/Users/bluth/Code/www/` 仓库下，通过 Cloudflare Pages 部署到 `*.starseas.org`。

产品间的关系（来自你的 GitHub profile）：

```
llm-harness-agent  ← 理论研究（18 篇深度分析 + 论文数据库）
       ↓ 验证
deepseek_runtime   ← 可复用的运行时内核（fork 了就可用）
       ↓ 封装为产品
deepseekagent     ← 面向用户的完整产品（"一人公司"操作系统）
       ↓ 派生
├── deepcode          ← DeepSeek V4 深度优化的编程助手
└── oh-my-deepseek-harness  ← Hermes 插件：注入满血 DeepSeek 能力
```

---

## 二、域名方案

| 产品 | 建议域名 | 理由 | 备注 |
|------|---------|------|------|
| **主站** | `deepseek.starseas.org` | 已有域名，入口总站 | 已有 Cloudflare 配置 |
| **llm-harness-agent** | `harness-papers.starseas.org` | 已确认 | DNS 需新增 CNAME |
| **deepseek_runtime** | `runtime.starseas.org` | "Runtime" 精准描述产品定位 | DNS 需新增 CNAME |
| **deepseekagent** | `deepseekagent.starseas.org` | 已在使用，不改变 | 已有部署 |
| **deepcode** | `deepcode.starseas.org` | 与产品名一致，用户好记 | DNS 需新增 CNAME |
| **oh-my-deepseek-harness** | `omh.starseas.org` | "oh-my" 缩写，轻松有趣、易记 | DNS 需新增 CNAME |

备选方案：
- `oh-my-deepseek-harness` 也可以考虑 `plugin.starseas.org`（更直白但少了品牌个性）

---

## 三、主站 deepseek.starseas.org 方案

### 定位

**DeepSeek Harness 产品体系的总入口。** 让访客一眼看懂：
1. 这些产品是什么关系
2. 哪个产品解决我的问题
3. 怎么快速上手

### 目标用户画像

- **独立开发者 / 创业者** → deepseekagent（一人公司）
- **Python 后端开发者** → deepseek_runtime（运行时内核）
- **用 DeepSeek V4 写代码的开发者** → deepcode（编程助手）
- **Hermes Agent 用户** → oh-my-deepseek-harness（插件）
- **产品经理 / 技术决策者** → llm-harness-agent（理论研究）

### 页面结构

```
┌─────────────────────────────────────────────┐
│                导航栏                          │
│  Harness · Runtime · Agent · DeepCode · 插件   │
├─────────────────────────────────────────────┤
│              Hero 区                           │
│  "DeepSeek 的上限，由 Harness 决定"             │
│  模型 × Harness = Agent 的真实表现              │
│  安装命令（全局一键安装入口）                    │
├─────────────────────────────────────────────┤
│           产品矩阵（产品间关系图）                  │
│  用可视化 hierarchy 展示 5 个产品的关系           │
│  理论研究 → 运行时内核 → 完整产品 → 两个派生      │
├─────────────────────────────────────────────┤
│           5 个产品卡片（价值点 + CTA）            │
│  每个卡片：图标 + 一句话定位 + 目标用户 + "了解更多"│
├─────────────────────────────────────────────┤
│           为什么需要这个体系                      │
│  模型只决定下限，Harness 决定上限                  │
│  数据对比（同一条 API，不同架构差 10 倍）          │
├─────────────────────────────────────────────┤
│              Footer                            │
│  各子站链接 + 版权信息                           │
└─────────────────────────────────────────────┘
```

---

## 四、各子站方案

### 4.1 harness.starseas.org — llm-harness-agent

**定位：** "Agent 架构的工程笔记——不是学术论文，是一线实践者的 18 篇深度分析"

**目标用户：** 产品经理（理解技术差异）、开发者（应用到项目）、研究者（学术脉络）

**核心价值点：**
- 18 篇深度分析，从理论与代码验证回答"Agent 架构怎么设计"
- 核心结论：模型能力只决定下限，Harness 设计决定上限（差 10 倍）
- 论文引用数据库，学术脉络清晰

**页面结构：**
```
Hero: "LLM + Harness = Agent — 让 AI 模型在真实场景中可靠工作"
├── 4 条用户路径（PM/开发者/研究者/直接用产品）
├── 18 篇分析文章目录（每篇一句话摘要）
├── 核心架构图
├── 现成产品入口（跳转到 runtime / agent / deepcode / plugin）
└── CTA: Star 仓库 + 阅读入口
```

**风格建议：** 知识型、专业性，深色 + 蓝色调

---

### 4.2 runtime.starseas.org — deepseek_runtime

**定位：** "DeepSeek API 上搭本地 Agent 的运行内核——fork 了就能用"

**目标用户：** 在 DeepSeek API 上做二次开发的 Python 开发者

**核心价值点：**
- 不需要自己写安全、会话、证据——仓库帮你封装好了
- 六层架构，每层 < 500 行，好读好改
- 内置 Token 统计、缓存分析、沙箱隔离、权限策略
- 一条命令体检，不需要 API Key

**页面结构：**
```
Hero: "用 DeepSeek API 做 Agent？安全、状态、成本——这个内核帮你解决了"
├── 痛点场景（调 API 和造可靠 Agent 之间的鸿沟）
├── 快速开始（clone + pip install + doctor）
├── 六层架构一览（可视化）
├── 和裸调 API 的对比（安全/多步/证据/成本/断点）
├── 研究脉络（理论→产品→内核）
└── CTA: 跳转到主站 / GitHub / 文档
```

**风格建议：** 开发者导向，代码块多，深色 + 紫色调

---

### 4.3 deepseekagent.starseas.org — deepseekagent

**定位：** "你一个人的全栈公司——说需求，它出代码、出文案、出报表"

**目标用户：** 独立开发者、创业者、不会写代码但有想法的人

**核心价值点：**
- 280+ Skill、232 AI 专家、20 个专业部门
- 10 层 Harness 定向优化，成本直降 70%
- 一行命令 30 秒装完
- WebUI + CLI + 消息网关

**页面结构：**（已在之前的改造中完成，保持现状即可，后续统一风格）

---

### 4.4 deepcode.starseas.org — deepcode

**定位：** "DeepSeek V4 编程助手的正确用法——除了它，没有替代品"

**目标用户：** 用 DeepSeek V4 写代码的开发者

**核心价值点：**
- 唯一全栈适配 DeepSeek V4 的编程助手（reasoning_effort、thinking、DSML）
- 14 个 Harness 模块让 AI 不乱来
- 飞书/微信里也能管代码
- npm install 一条命令安装

**页面结构：**
```
Hero: "把你的 DeepSeek V4 模型武装成顶级 AI 编程助手"
├── 三个痛点 → 三个解决方案
│   1. 模型能力没充分发挥 → 全栈适配 V4
│   2. 复杂项目越聊越乱 → 14 个 Harness 模块
│   3. 不想每次开终端 → 飞书/微信网关
├── 快速开始（npm install -g deepcode）
├── 和普通 OpenCode 的对比（5 个差异点）
├── 14 个 Harness 模块一览
└── CTA: 安装 / 文档 / GitHub
```

**风格建议：** 编程工具风，深色 + 橙色/绿色调

---

### 4.5 omh.starseas.org — oh-my-deepseek-harness

**定位：** "一条命令给 Hermes Agent 装上 DeepSeek 满血插件"

**目标用户：** Hermes Agent 用户

**核心价值点：**
- 唯一专门针对 DeepSeek V4 API 做全链 Agent 优化的开源插件
- 不修改一行 Hermes 核心代码（全部通过 Plugin Hook 接口）
- 认知门控 + 意图路由 + 推理强度自动匹配
- 越用越好用（Skill 学习 + 记忆累积）

**页面结构：**
```
Hero: "你的 Hermes Agent + DeepSeek = 满血版"
├── 三个安装理由（认知门控/自动路由/飞轮效应）
├── 安装命令（git clone + install.sh）
├── Before/After 对比（装前装后的区别）
├── 15 项完整能力一览（按用户收益分组）
├── 三层架构图
└── CTA: 安装 / 文档 / GitHub
```

**风格建议：** 插件风格，深色 + 粉紫色调

---

## 五、技术架构方案

### 目录结构

```
/Users/bluth/Code/www/
├── main/                        # deepseek.starseas.org
│   ├── index.html
│   ├── style.css
│   └── script.js
├── harness/                     # harness.starseas.org
│   ├── index.html
│   ├── style.css
│   └── script.js
├── runtime/                     # runtime.starseas.org
│   ├── index.html
│   ├── style.css
│   └── script.js
├── deepseekagent/               # deepseekagent.starseas.org (复制现有)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── deepcode/                    # deepcode.starseas.org
│   ├── index.html
│   ├── style.css
│   └── script.js
├── omh/                         # omh.starseas.org
│   ├── index.html
│   ├── style.css
│   └── script.js
├── assets/                      # 共享资源
│   ├── fonts/
│   └── images/
├── wrangler.toml                # Cloudflare Pages 配置
└── package.json                 # 如果统一工具链
```

### Cloudflare Pages 部署方式

**方案 A：每个子站一个 Pages 项目（推荐）**

优点：独立部署、独立 CI/CD、好管理
缺点：6 个项目需逐一配置

```
deepseek.starseas.org     → Pages project: deepseek-main
harness.starseas.org      → Pages project: deepseek-harness
runtime.starseas.org      → Pages project: deepseek-runtime
deepseekagent.starseas.org → Pages project: deepseekagent
deepcode.starseas.org     → Pages project: deepseek-deepcode
omh.starseas.org          → Pages project: deepseek-omh
```

每个 project 的 wrangler.toml:

```toml
name = "deepseek-harness"
pages_build_output_dir = "harness"
```

Cloudflare 侧绑定域名的命令示例：

```bash
npx wrangler pages project create deepseek-harness --production-branch main
npx wrangler pages domain set deepseek-harness harness.starseas.org
```

### 设计规范（建议统一）

- **颜色品牌**：DeepSeek 青蓝色系（#00D4FF / #4FC3F7）
- **深色主题**：所有子站统一深色底
- **字体**：Inter + JetBrains Mono（代码）
- **布局**：统一的响应式设计，但每个站有自己的视觉个性（色调微调）
- **导航**：底部导航条统一指向其他子站和主站

---

## 六、实施建议

### 优先级

**第一批**（先上线最关键的 2 个 + 主站）：
1. `deepseek.starseas.org` — 主站（产品矩阵总入口）
2. `deepseekagent.starseas.org` — 已改造完成，直接纳入 www 仓库
3. `deepcode.starseas.org` — 独立产品线，有明确对标价值

**第二批**：
4. `harness.starseas.org` — 理论站（内容量大，但结构清晰）
5. `runtime.starseas.org` — 开发者工具站

**第三批**：
6. `omh.starseas.org` — 插件站（用户群较窄，优先级最低）

### 实施流程

1. 确认方案（你现在看的这份）
2. 创建 `/Users/bluth/Code/www/` 仓库
3. 逐个站点起草 → 你审 → 部署
4. 主站串起所有子站
5. 配置 DNS + Cloudflare Pages

---

## 七、需要你确认的点

1. **域名分配**：以上域名方案是否合适？特别是 `omh.starseas.org` 还是 `plugin.starseas.org`？
2. **优先级**：是否同意第一批先做主站 + deepseekagent + deepcode？
3. **主站定位**："DeepSeek 的上限，由 Harness 决定"这个总定位是否准确？
4. **设计风格**：所有子站统一深色 DeepSeek 青蓝系，但每个站色调微调（如 deepcode 偏橙、omh 偏紫），这个思路合适吗？
5. **Cloudflare 方案**：选方案 A（每站独立 Pages 项目）还是方案 B（单项目 + 函数路由）？
6. **www 仓库**：这个仓库是否公开？（涉及各子站部署 token 配置）
