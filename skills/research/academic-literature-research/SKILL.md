---
name: academic-literature-research
title: Academic Literature Research & Paper Database Curation
description: Systematic academic literature search, paper metadata extraction, and structured bilingual paper database creation. Covers Google Scholar search strategy, paper entry formatting with relevance analysis, and bilingual (EN+ZH) output conventions.
version: 1.0.0
triggers:
  - User asks to search for academic papers on a specific topic
  - User wants a structured bibliography or paper database
  - User requests high-quality (SCI, CCF-A) paper recommendations
  - User has research notes and needs to find supporting academic literature
  - User needs bilingual paper entries (original + Chinese translation)
---

# Academic Literature Research & Paper Database Curation

## Trigger Conditions

- User asks to "search for papers about X", "find related research on Y"
- User needs a structured bibliography or paper database for a research topic
- User requests "high quality / SCI-level / top-conference papers"
- User provides their own research notes/theory and needs supporting literature
- User needs bilingual (English + Chinese) paper entries

## Core Output Structure

The deliverable is a**paper database** (not a synthesized summary). Each entry standardizes:

```markdown
### [ID]. [Paper Title]
**[中文标题]**（如果做中文版）

| Field | Value |
|-------|-------|
| **Authors** | Full author list |
| **Title** | Full paper title |
| **Source** | Journal/Conference, Year |
| **DOI** | DOI link |
| **arXiv** | arXiv link (if available) |
| **Status** | ✅ SCI / ✅ CCF-A / ⏳ Preprint |

**Abstract.** (Synthesized from original, 3-8 sentences capturing the core contribution)

**Relevance to [Research Thesis].** (Analysis connecting the paper back to the user's specific research question — NOT a generic summary)
```

## Workflow

### Phase 1: Topic Alignment
1. **Understand the user's exact research question** — they may use non-standard terminology that needs clarification (e.g. "Haness" → "Harness")
2. **Read user's existing research material** — if they point to a directory, read their theory docs, methodology notes, and paper drafts to align with their framework
3. **Identify the core thesis** — extract the user's unique angle so you can evaluate paper relevance

### Phase 2: Multi-Source Paper Discovery

Run complementary search strategies in parallel:

| Strategy | Target | Query Pattern |
|----------|--------|---------------|
| Google Scholar | All papers | `site:scholar.google.com [topic] survey 2024 2025` |
| Direct web search | SCI journals | `"LLM" "agent" "Nature" OR "Science" survey 2024` |
| arXiv | Preprints | `arxiv [topic] survey 2024` |
| Springer/ACM/Elsevier | Published papers | `link.springer.com OR dl.acm.org [topic]` |
| Semantic Scholar | Citation counts | `semanticscholar.org [specific-paper-title]` |

**Key tactics:**
- Batch independent queries in a single turn (web_search is stateless)
- Search by specific paper title to verify venue/status
- Use `web_extract` to read paper pages for full metadata (authors, DOI, abstract)
- For Google Scholar specifically, try browser_navigate + browser_vision if web_search gives shallow results

### Phase 3: Metadata Extraction

For each candidate paper, collect:
- **Citation**: Full author list, title, journal/conference, year, DOI, arXiv ID
- **Venue quality**: Is it SCI-indexed? CCF-A/B/C conference? Preprint?
- **Abstract**: Extract from the official page — NOT from search results snippets
- **Key contribution**: 1-3 sentences on what the paper actually achieved
- **Relevance signal**: What components of the harness/agent model does this paper address?

**Verification steps:**
- Verify venue: check if paper was published at ICLR, NeurIPS, ICML, ACL, Nature, etc.
- Check DOI resolution for SCI status
- For arXiv papers: check the latest version and any publication info in the comments

### Phase 4: Structured Database Writing

Organize papers into categories based on their relationship to the core thesis:

| Category | Contents | Example |
|----------|----------|---------|
| **A: Core Theory** | Papers directly addressing the thesis | Harness surveys, Agent OS papers |
| **B: Foundational** | Papers that established the paradigm | ReAct, Generative Agents, Toolformer |
| **C: Frameworks** | Systems implementing key architecture | ToolLLM, MetaGPT, OpenHands |
| **D: Key Components** | Deep dives on sub-topics | Memory, context management |
| **E: Applications** | Real-world proof | Coscientist (Nature), ChemCrow |

For each category, create a sub-heading with a table of contents.

### Phase 5: Bilingual Output (if requested)

When user wants Chinese translation:
1. Write the **English original** first (papers.md) — includes original citations, abstracts synthesized from source, relevance analysis
2. Write the **Chinese translation** (papers-zh.md) — your own translation, NOT machine-translated. You are the model — read the original English paper understanding and express it naturally in Chinese
3. Naming convention: `papers.md` (EN) + `papers-zh.md` (ZH) — per document-storage-rules convention
4. Optionally add a `README.md` as a table-of-contents index

**Important**: Translate the full content including:
- Paper titles (give a descriptive Chinese title)
- Abstract section (re-expressed in natural Chinese, not literal word-for-word)
- Relevance analysis section (same depth as English)
- Keep DOIs, arXiv IDs, and source URLs in original form — these are identifiers

**⚠️ CROSS-REFERENCE: This phase is METADATA-LEVEL TRANSLATION only** (titles, abstracts, relevance). If the user asks for "逐篇翻译" or "论文原文的完整翻译", they want FULL PAPER BODY TRANSLATION (Introduction, Method, Experiments, Discussion, etc. — every section). That is NOT this skill — use the `single-paper-translation` skill for full body work. The two deliverables are:

| File | Content | Skill | 
|------|---------|-------|
| `papers-zh.md` | Metadata: titles, citation info, abstract synopsis, relevance analysis | **academic-literature-research** (this skill) |
| `zh/<ID>.md` | Full body: every section, paragraph, sentence from the paper | **single-paper-translation** |

**Never confuse these.** Delivering papers-zh.md when the user wants full body translation will result in a correction.

### Phase 6: Handling Large Files

The `write_file` tool will time out if content exceeds approximately 31-32 KB or ~8K tokens in the arguments. **Do NOT retry the same call.** Instead:

1. Write the first segment normally with `write_file` (keeps it under 5-8K tokens)
2. Append subsequent segments using `patch` to replace the last characters with the extended content
3. Or: break the content into logical sections and write each as a separate `write_file` + multiple `patch` calls

**Tip**: The paper database for 15-20 papers is typically 30-35 KB. Write it in 2-3 segments.

## Paper Entry Template

```markdown
### [ID]. Full Paper Title
**[中文标题]**

| Field | Value |
|-------|-------|
| **Authors** | Author1, Author2, ... |
| **Title** | Exact paper title |
| **Source** | Journal/Conference, Year |
| **DOI** | 10.xxxx/xxxxxx |
| **arXiv** | xxxx.xxxxx |
| **Status** | ✅ SCI / ✅ CCF-A / ⏳ Preprint |

**Abstract.** (3-8 sentence synthesis — DO NOT copy-paste. Read the original and write your own concise version.)

**Key Contributions:**
1. First point about what the paper achieved
2. Second point
3. Third point

**Relevance to [Research Thesis].** (Analysis: which components of the target framework does this paper address? What does it prove, enable, or challenge? How does it relate to the user's specific theory?)
```

## Quality Standards

### Paper Selection Criteria
- **Prefer**: SCI-indexed journals, CCF-A/B conferences, Nature/Springer/ACM/IEEE published
- **Accept**: arXiv preprints with high citation counts or clear publication trajectory
- **Exclude**: Blog posts, non-peer-reviewed technical reports, obviously low-quality venues

### Entry Completeness
- Every entry MUST have: citation, venue quality indicator, abstract, relevance analysis
- Relevance analysis is NOT optional — it's what makes the database useful for the user's specific research
- DOIs and arXiv IDs should be verified and functional

### Translation Quality
- Chinese translation should be natural academic Chinese, not translation-engine output
- Keep technical terms that are commonly used in English (e.g., "Harness", "Agent") in English when that's how the user uses them
- The translation should read as if it was originally written in Chinese

## Pitfalls

- **DO NOT** copy-paste abstracts from paper pages verbatim — synthesize in your own words
- **DO NOT** stop at surface-level relevance ("this paper is about agents") — dig into WHAT component of the model/harness/architecture it advances
- **DO NOT** write relevance analysis that's identical for every paper — each must be specific
- **DO NOT** use machine translation tools — you ARE the translation engine
- **DO NOT** retry `write_file` with the same large content if it times out — split into chunks
- **DO NOT** include papers the user can't access (arXiv-only is OK; behind-paywall-only is borderline)
- **ALWAYS** verify venue quality — just because a paper is on arXiv doesn't mean it's been published
- **ALWAYS** read the user's existing research context before starting
- **ALWAYS** clarify ambiguous terminology — the user may use domain-specific shorthands or nonstandard terms
- **NEVER** confuse metadata-level translation (papers-zh.md) with full paper body translation (zh/*.md). The two serve different purposes. If the user says "逐篇翻译" or asks "你在干什么呀" after receiving papers-zh.md, they wanted full body — redirect to the `single-paper-translation` skill immediately.
- **Google Scholar search must be actively executed.** When the user says "你在谷歌学术上搜索一下", they expect YOU to search. Do not report that work "already exists in the filesystem" — that frustrates the user. Actually run the web_search queries.

## Verification Checklist

- [ ] User's research context read and understood
- [ ] Terminology clarified and aligned
- [ ] Multiple search strategies run (not just one query)
- [ ] All paper entries have DOIs or stable identifiers
- [ ] Venue quality verified for each entry
- [ ] Relevance analysis is specific and differentiated per paper
- [ ] Files stored in user-specified directory
- [ ] Bilingual naming convention followed (papers.md + papers-zh.md)
- [ ] File size limits respected (chunk large content)
