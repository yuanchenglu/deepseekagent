# Paper Entry Format: Concrete Example

> From the LLM + Harness = Agent paper database. This shows the actual entry format used in a real deliverable.

## Overview

Each paper entry has three mandatory sections:
1. **Citation Table** — structured metadata with venue quality badge
2. **Abstract** — original understanding re-expressed, not copy-pasted
3. **Relevance Analysis** — connecting the paper back to the user's specific research thesis

## Category Header Format

```markdown
## A. Category Name

Brief paragraph explaining what this category represents and why it matters for the thesis.
```

## Entry Format

### A1. Full Paper Title
**中文标题（仅中文版使用）**

| Field | Value |
|-------|-------|
| **Authors** | Full author list with institutional affiliations |
| **Title** | Exact paper title |
| **Source** | Journal/Conference, Vol, Pages, Year |
| **DOI** | 10.xxxx/xxxxxx |
| **arXiv** | xxxx.xxxxx (if applicable) |
| **Status** | ✅ SCI / ✅ CCF-A / ✅ CCF-A (Oral) / ⏳ Preprint |

**Abstract.** (3-8 sentences. Read the original source and write your own synthesis. Capture: what problem does it solve? What approach? What results? What's the key insight?)

**Relevance to [User's Research Thesis].** (2-5 sentences. Be specific: which component of the user's framework does this paper address? Does it confirm, extend, or challenge? What specific mechanism or architecture element does it illuminate?)
```

## Real Example (from LLM+Harness=Agent Database)

### A2. AIOS: LLM Agent Operating System
**AIOS：大语言模型智能体操作系统**

| Field | Value |
|-------|-------|
| **Authors** | Kai Mei, Xi Zhu, Wujiang Xu, Mingyu Jin et al. (Rutgers University) |
| **Title** | AIOS: LLM Agent Operating System |
| **Source** | Conference on Language Modeling (COLM), 2025 |
| **arXiv** | https://arxiv.org/abs/2403.16971 |
| **Status** | ✅ COLM 2025 full paper |

**Abstract.** This paper presents AIOS, an LLM agent operating system, which embeds large language models into operating systems as the "brain" of the OS. AIOS addresses challenges in LLM-based agent deployment: context scheduling, concurrent agent management, tool orchestration, and resource allocation. It proposes a modular architecture that separates the LLM from the agent execution infrastructure, enabling multiple agents to share the same LLM backend while maintaining isolation and state. The system introduces an Agent Scheduler, Context Manager, Memory Manager, and Tool Manager as first-class OS modules.

**Relevance to LLM + Harness = Agent.** AIOS is the most explicit realization of the "OS metaphor" for the harness concept. It treats the LLM as a CPU and builds an operating system around it — exactly the CPU/OS analogy used in the DeepSeek Agent theory guide. Its modular architecture (scheduler, context manager, memory manager, tool manager) maps directly to the Harness components defined in the theory.

## Chinese Translation Example (from papers-zh.md)

```markdown
### A2. AIOS: LLM Agent Operating System
**AIOS：大语言模型智能体操作系统**

| 字段 | 内容 |
|-------|-------|
| **作者** | Kai Mei, Xi Zhu, Wujiang Xu, Mingyu Jin 等（Rutgers University） |
| **标题** | AIOS: LLM Agent Operating System |
| **出处** | Conference on Language Modeling (COLM), 2025 |
| **arXiv** | https://arxiv.org/abs/2403.16971 |
| **状态** | ✅ COLM 2025 长文 |

**摘要。** 本文提出 AIOS，一个将大语言模型嵌入操作系统作为 OS "大脑"的智能体操作系统。AIOS 解决 LLM 智能体部署中的关键挑战：上下文调度、并发智能体管理、工具编排和资源分配。它提出了一种将 LLM 与智能体执行基础设施分离的模块化架构，使多个智能体可以共享同一 LLM 后端同时保持隔离和状态。系统将 Agent 调度器、上下文管理器、记忆管理器和工具管理器作为 OS 的一等模块引入。

**与 LLM + Harness = Agent 的关联。** AIOS 是"操作系统比喻"最明确的实现。它将 LLM 类比为 CPU，并围绕它构建操作系统——与 DeepSeek Agent 理论总纲中的 CPU/OS 类比完全一致。其模块化架构（调度器、上下文管理器、记忆管理器、工具管理器）直接映射到装备层理论的各组件。
```
