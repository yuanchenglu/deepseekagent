---
name: software-copyright
description: >
  从真实项目生成中国软件著作权申请资料（Word/TXT）。
  当用户说 软件著作权、软著申请、软著材料、操作手册、申请表信息、
  代码材料、软著登记 等关键词时触发。
  自动分析项目源码，生成申请表信息.txt、操作手册.docx、代码材料.docx。
category: productivity
---

# 软件著作权申请资料生成 Skill

基于 [Fokkyp/SoftwareCopyright-Skill](https://github.com/Fokkyp/SoftwareCopyright-Skill)（GitHub 3,349 Stars，MIT 协议），帮助开发者从真实项目中一键生成中国软件著作权登记所需的全部材料。

## 项目安装位置

```
~/Code/SoftwareCopyright-Skill/
├── software-copyright-materials/   ← Skill 核心
│   ├── SKILL.md                    ← 原始 Codex SKILL
│   ├── scripts/                    ← Python 脚本
│   ├── references/                 ← 参考规则
│   ├── agents/                     ← 子 Agent 配置
│   └── vendor/docx-toolkit/        ← DOCX 生成工具
├── 生成demo/                       ← 完整演示
├── 市场商业化分析报告.md
└── 使用指南.md
```

## 核心原则

- **固定输出目录**：当前工作目录下的 `软件著作权申请资料/`
- **先生成草稿，用户确认后再输出**：Markdown → 确认 → DOCX/TXT
- **代码必须来自真实源码**：禁止 AI 编造代码
- **操作手册面向审核员**：去 AI 味、去技术化、写清"做什么+怎么操作+什么反馈"
- **关键节点必停**：7 个强制人工门禁，不自动跳过

## 使用方式

用户对 Hermes 说：
```
帮我生成当前项目的软著申请资料
```
或指定项目：
```
对 ~/Code/my-project 生成软著申请资料
```

## 工作流（10 阶段）

### 阶段 1：环境检查

```bash
SCRIPTS=~/Code/SoftwareCopyright-Skill/software-copyright-materials/scripts
python3 $SCRIPTS/check_environment.py --out-dir 软件著作权申请资料
```

检查：Python 环境、python-docx、pandoc、.NET SDK、DOCX OpenXML 完整环境。

如果完整 DOCX 环境缺失 → **停止**，让用户选择：安装 or 使用兜底方案。

### 阶段 2：定位项目

扫描当前目录，排除 node_modules/.git 等，找到项目根目录。多候选时让用户选择。

### 阶段 3：分析项目

```bash
python3 $SCRIPTS/analyze_project.py \
  --project <项目目录> \
  --out 软件著作权申请资料/analysis/project.json
```

自动检测：框架（Vue/React/Next.js）、语言、入口文件、路由、组件结构、源程序行数。

### 阶段 4：业务理解

```bash
# 先收集证据
python3 $SCRIPTS/generate_business_context.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --software-name "<软件全称>" \
  --out-dir 软件著作权申请资料/草稿
```

Agent 必须阅读项目 README、文档、页面文案等，**自行判断**行业、目标用户、核心功能和操作流程，不得依赖脚本关键字表。

生成 `草稿/业务理解.md` 后 → **停止**，用户确认。

### 阶段 5：确认申请表字段

根据项目分析和业务理解，引导用户确认 20 个字段（软件全称、版本号、著作权人、硬件环境、操作系统等）。

硬件/系统环境必须让用户确认或填写 → **停止**，用户补全。

### 阶段 6：代码文件选择

```bash
python3 $SCRIPTS/propose_code_selection.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --out-dir 软件著作权申请资料/草稿
```

Agent 阅读候选清单，优先选择前端入口、页面、核心组件。生成 `代码文件选择.json` → **停止**，用户确认。

### 阶段 7：生成 Markdown 草稿

```bash
# 代码材料
python3 $SCRIPTS/extract_code_material.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --selection 软件著作权申请资料/草稿/代码文件选择.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿

# 申请表信息
python3 $SCRIPTS/generate_application_info.py \
  --analysis 软件著作权申请资料/analysis/project.json \
  --code-manifest 软件著作权申请资料/草稿/代码提取清单.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿

# 操作手册
python3 $SCRIPTS/generate_manual_draft.py \
  --analysis 软件著作权申请资料/analysis/project.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

### 阶段 8：截图确认

让用户从三种方式中选择：Chrome DevTools MCP、用户自行截图、跳过截图。

### 阶段 9：确认 Markdown 草稿

**停止**，让用户全面检查所有草稿后再进入 DOCX 生成。

### 阶段 10：生成正式 DOCX/TXT

```bash
python3 $SCRIPTS/build_docx_from_md.py \
  --workdir 软件著作权申请资料 \
  --software-name "<软件全称>" \
  --version "<版本号>"
```

输出：
```
正式资料/申请表信息.txt
正式资料/<软件全称>_操作手册.docx
正式资料/<软件全称>-代码(前30页).docx
正式资料/<软件全称>-代码(后30页).docx
正式资料/生成报告.md
```

## 7 个强制门禁（必须停止等待用户）

1. `environment`：DOCX 环境缺失时的选择
2. `project`：多项目候选时选哪个
3. `business`：业务理解确认
4. `application-fields`：申请表字段补全确认
5. `code-selection`：代码文件选择确认
6. `screenshot-method`：截图方式选择
7. `markdown`：最终草稿确认

每个门禁通过后运行：
```bash
python3 $SCRIPTS/confirm_stage.py \
  --workdir 软件著作权申请资料 \
  --stage <阶段名> \
  --note "<用户确认内容>"
```

## 官方参考

- 中国版权保护中心：https://www.ccopyright.com.cn/
- 著作权登记系统：https://register.ccopyright.com.cn/login.html
- 法规：《计算机软件著作权登记办法》

## 项目信息

- 来源：GitHub Fokkyp/SoftwareCopyright-Skill（3,349 Stars，MIT License）
- 已部署到：`~/Code/SoftwareCopyright-Skill/`
- 详细使用指南：`~/Code/SoftwareCopyright-Skill/使用指南.md`
- 商业分析报告：`~/Code/SoftwareCopyright-Skill/市场商业化分析报告.md`
