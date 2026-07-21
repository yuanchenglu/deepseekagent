---
name: codegraph-code-analysis
description: 使用 CodeGraph 对任意代码库进行知识图谱分析。Clone → 构建 → 索引 → 生成报告，一站式代码分析工具。
---

# CodeGraph 代码分析技能

## 概述
CodeGraph 是一个本地优先的代码智能库，通过 tree-sitter 解析代码，构建 SQLite 知识图谱（FTS5），为 AI Agent 提供语义级代码智能。支持 Python、TypeScript、Rust、Go、Java、Swift 等语言。

**核心理念**：预索引代码知识图谱，Agent 直接查询图谱而非逐文件扫描，平均节省 35% 成本、70% 工具调用。

## 安装

```bash
# npm 全局安装（推荐）
npm install -g @colbymchenry/codegraph

# 或 npx 零安装
npx @colbymchenry/codegraph
```

已安装在本地: `~/Code/codegraph/`（源码仓库，已在 hermes 上完成过分析）

## 完整分析流程

### Step 1: Clone 目标仓库

```bash
cd ~/Code
git clone <repo-url> <project-name>
```

### Step 2: 初始化 CodeGraph 索引

```bash
cd ~/Code/<project-name>
codegraph init -i
```

### Step 3: 生成分析报告

```bash
# 基础状态
codegraph status

# 按关键字搜索代码节点
codegraph query "<搜索词>"

# 获取调用者和被调用者
codegraph query --callers <ClassName>
codegraph query --callees <functionName>

# 影响半径分析（一个节点影响多少其他节点）
codegraph query --radius <nodeName>

# 列出文件
codegraph files

# 代码上下文（供 Agent 消费）
codegraph context "<问题描述>"
```

### Step 4: 提取并整理报告

分析报告的核心产出包括：

1. **项目规模**：文件数、节点数、边数、DB 大小、语言分布
2. **目录结构**：各子目录文件数和职责
3. **节点类型分布**：method、function、class、import 等
4. **最大文件排行**：Top 15-20 文件（大小+节点数）
5. **核心类分析**：主要类的方法数、位置、功能
6. **子系统详解**：Gateway、Tools、Memory、Skills 等
7. **架构洞察**：测试覆盖率、单体模块、特殊定制

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `codegraph status` | 查看索引状态（文件数、节点数、边数） |
| `codegraph query <pattern>` | 搜索代码节点 |
| `codegraph query --callers <name>` | 查谁调用了这个节点 |
| `codegraph query --callees <name>` | 查这个节点调用了谁 |
| `codegraph query --radius <name>` | 影响半径分析 |
| `codegraph files` | 列出所有已索引文件 |
| `codegraph context <query>` | 语义上下文（Markdown） |
| `codegraph init -i` | 初始化项目索引 |
| `codegraph index` | 手动触发索引 |
| `codegraph sync` | 增量同步（git hook 触发） |

## 输出格式

分析完成后，将结果整理为以下格式：
1. **项目规模一览表**（文件数/节点数/边数/语言分布）
2. **目录结构分布表**
3. **节点类型分布**
4. **最大文件 Top 15-20**
5. **核心类/函数 Top 30**
6. **子系统详解**（Gateway、Tools、Skills 等）
7. **架构洞察**（3-5 条关键发现）

## 注意事项

- 大项目（如 hermes 2345 文件）索引 DB 可达 140MB+，但仍在可接受范围
- 索引过程使用 tree-sitter 解析，Python/TS/JS/TSX 覆盖最好
- YAML 文件被索引但不会产生代码节点（非编程语言）
- `.codegraph/` 目录包含 SQLite DB，不要提交到 git（已自动 .gitignore）
- 增量同步通过 `codegraph sync` 或 git hook 触发

## 已分析项目

| 项目 | 文件数 | 节点数 | 边数 | DB大小 | 分析日期 |
|------|--------|--------|------|--------|----------|
| Hermes Agent | 2,345 | 66,757 | 153,752 | 140.49 MB | 2026-05-23 |
