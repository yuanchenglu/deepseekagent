---
name: paper-translation
description: "Translate academic papers (English→Chinese): single paper, batch full-body via subagents, or metadata-only."
version: 1.2.0
author: Hermes Agent
license: MIT
triggers:
  - User asks to translate academic papers, technical reports, or arXiv papers
  - User says "翻译成中文", "translate to Chinese", or similar
  - User says "逐篇翻译" (full body)
  - User says "论文原文的完整翻译" (full body from PDF)
  - User points to papers-zh.md and says it's insufficient (wants full body)
  - User explicitly says "use an API" / "don't use your own tokens"
---

# Paper Translation (EN → ZH)

Translate academic papers from English to Simplified Chinese. **Three approaches — choose based on scope:**

| Scenario | Method | Why |
|---|---|---|
| **Single important paper** (user is studying it, agent has already read it) | **Direct LLM translation** | Agent preserves core meaning, handles academic terminology precisely, maintains logical flow across sections. Machine translation misses nuances. |
| **Batch full-paper translation** (3-21 papers, user wants complete body text) | **Parallel subagent dispatch** (this skill's third method) | Full body translation per paper via delegate_task. Each paper = one subagent. 3 at a time parallel. Best scale/quality tradeoff. |
| **Bulk metadata ingestion** (paper database entry, not full body) | Direct LLM or metadata-only | Translate abstracts + relevance analysis for database creation. ~5 min per paper. |

## When to Use

- User asks to translate academic papers, technical reports, or arXiv papers
- User says "翻译成中文", "translate to Chinese", or similar
- User says "逐篇翻译" → FULL BODY translation, not just abstract
- User says "论文原文的完整翻译" → translated body text from PDF, not metadata summary
- User explicitly says "use an API" / "don't use your own tokens" → use API method
- User points to existing papers-zh.md or similar file and says this is insufficient → they want full body

## CRITICAL DISTINCTION: Metadata-Level vs Full-Body Translation

**NEVER confuse these two.** The user will correct you forcefully if you deliver the wrong one.

## CRITICAL WORKFLOW DISTINCTION: Batch Parallel vs Sequential Single-Paper

The user has corrected this twice. There are TWO approaches for full-body translation, and they produce different quality:

| Approach | Method | Quality | When Used |
|---|---|---|---|
| **Batch Parallel (旧方式)** | dispatch 3 papers at once via delegate_task, each subagent reads extracted text → translates | Acceptable for paragraphs; **tables/formulas may lose structure** | Used for the first 21 papers (harness agent papers batch) |
| **Sequential Single-Paper (用户首选)** | ONE paper at a time: (1) convert PDF→English Markdown with PyMuPDF (preserving tables) (2) read entire English Markdown to understand (3) translate to Chinese in one pass (4) user reviews → next paper | **Highest quality**: tables preserved, original meaning accurate, terminology consistent, not stiff/mechanical | DeepSeek official papers, or any paper the user cares deeply about |

**The user's reasoning (quoting directly):**
> "你一篇一篇的，你自己阅读原本的英文版，阅读了之后，然后呢再来把它翻译成对应的中文版。只有这样子，你才能够保证原意，而且你自己的理解才更加准确一些。翻译成的简体中文，它就不是生硬的，它不会有偏差。更重要的是，因为这里面还涉及到表格，你在做简体中文的时候，里面的表格的内容会更加精准一些。"

**Default to sequential single-paper approach unless user explicitly says to do batch.**

| Deliverable | What it contains | File pattern | Example |
|---|---|---|---|
| **Metadata-level (论文数据库)** | Title, citation info, abstract synthesis, relevance analysis per entry | `papers-zh.md` | "LLM + Harness = Agent 论文数据库" — 395 lines, metadata only |
| **Full body (论文完整翻译)** | EVERY section, paragraph, sentence from the original PDF body | `zh/<Paper-ID>.md` | Complete Chinese markdown, section-by-section, all technical content |

**Warning signal:** If you find yourself writing a file called `papers-zh.md`, you are doing metadata-level translation. If the user later says "我要的是论文原文的翻译", pivot immediately to full-body translation in `zh/*.md` files.

## Workflow A: Direct LLM Translation (Single Important Paper)

When translating a single important paper directly (not via API, not via subagent):

1. **Read the full paper first.** Understand the structure, key concepts, and logical flow before translating. Don't translate blind.
2. **Write to the project directory in one pass.** Use `write_file` to create a markdown file with:
   - Paper title and author info
   - Full translation section by section (Introduction, Method, Experiments, Discussion, Conclusion — everything)
   - Preserve all section numbering, figure/table references, citations
3. **Key translation principles:**
   - Preserve LaTeX, code blocks, citation markers as-is
   - Academic terms: choose the Chinese equivalent that conveys the concept, not word-for-word
   - Keep author/institution names in original English
   - DO NOT skip the experimental/technical sections — these are often the most important part

## Workflow D: Sequential Single-Paper Translation (User-Preferred)

**This is the user's preferred method.** Use this for papers they want to study carefully. Do NOT default to parallel subagents unless explicitly told to.

### Phase 1: Convert PDF → English Markdown (Preserve Tables)

Use **PyMuPDF (fitz)** — it's far better than pypdf at preserving text spacing and detecting tables.

```bash
pip install PyMuPDF  # or pip3 install PyMuPDF
```

Conversion script:

```python
import fitz  # PyMuPDF

doc = fitz.open("paper.pdf")
md_lines = []

for i, page in enumerate(doc):
    md_lines.append(f"\n<!-- Page {i+1} -->\n")
    
    # Try to find tables
    tables = page.find_tables()
    
    # Get text blocks with position info
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    
    table_regions = []
    if tables and tables.tables:
        for t in tables.tables:
            table_regions.append((t.bbox, t.extract()))
    
    text_parts = []
    for block in blocks:
        if block["type"] == 0:  # text block
            bbox = block["bbox"]
            in_table = False
            for t_bbox, _ in table_regions:
                if (bbox[0] >= t_bbox[0] and bbox[1] >= t_bbox[1] and 
                    bbox[2] <= t_bbox[2] and bbox[3] <= t_bbox[3]):
                    in_table = True
                    break
            if not in_table:
                for line in block["lines"]:
                    text = " ".join([span["text"] for span in line["spans"]])
                    if text.strip():
                        text_parts.append(text)
    
    if text_parts:
        md_lines.append("\n".join(text_parts))
    
    # Render tables as Markdown tables
    for t_bbox, t_data in table_regions:
        if t_data and len(t_data) > 0:
            md_lines.append("\n")
            header = t_data[0]
            md_lines.append("| " + " | ".join([str(c or "").replace("\n", " ") for c in header]) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
            for row in t_data[1:]:
                md_lines.append("| " + " | ".join([str(c or "").replace("\n", " ") for c in row]) + " |")
            md_lines.append("")
    
    md_lines.append("\n---\n")

doc.close()
output = "\n".join(md_lines)
with open("paper.md", "w") as f:
    f.write(output)
```

**Why PyMuPDF over pypdf:**
- `pypdf`: text often loses spaces between words ("Therapiddevelopment" instead of "The rapid development")
- `PyMuPDF`: preserves proper word spacing via `TEXT_PRESERVE_WHITESPACE`
- `PyMuPDF` has built-in `find_tables()` for table detection
- `marker-pdf`: designed for PDF→Markdown but model download is very slow (>120s timeout)

**Don't use pdfplumber for this** — it also has spacing issues.

### Phase 2: Read the Full English Version

Read the ENTIRE English Markdown to understand the paper's structure, key contributions, technical details, tables, and formulas before translating. Do not translate section by section blind.

Key sections to understand:
- Title, authors, abstract
- Introduction (motivation, contributions)
- Method/Architecture (core technical content)
- Experiments (benchmarks, datasets, results, ablation studies)
- Discussion and Conclusion
- Appendices (often contain critical details)

### Phase 3: Translate to Chinese Markdown (One Pass)

After reading and understanding the whole paper:

1. **Create the Chinese Markdown file** in one `write_file` call
2. **Include ALL sections** — do not skip experiments, ablation studies, or appendices
3. **Preserve table structures** as Markdown tables. If the source tables weren't automatically detected by PyMuPDF, manually reconstruct them from the text
4. **Handle formulas:** keep mathematical notation as-is
5. **Handle references:** keep citation markers `[n]` as-is, keep author names in original English
6. **Handle code:** keep code blocks as-is

### Phase 4: Deliver and Proceed

1. Report to user what was done (paper name, pages, sections covered)
2. Ask if quality is acceptable
3. Only proceed to next paper after user confirms or adjusts

**Directory structure for DeepSeek papers:**

```
papers/deepseek_papers/
├── 2401.02954v1.pdf     # Original PDFs
├── en-md/               # English Markdown (converted from PDF)
│   └── 01-DeepSeek-LLM.md
└── zh-md/               # Chinese Markdown translations (FINAL DELIVERABLE)
    └── 01-DeepSeek-LLM.md
└── 01-DeepSeek-LLM.md

---

## Workflow B: Full-Body Batch Translation (via Parallel Subagents)

### Prerequisites

- `pypdf` for PDF extraction (`pip install pypdf` in the active terminal/venv)
- OR `pdftotext` from poppler-utils (`apt install poppler-utils` / `brew install poppler`)
- For Nature journal PDFs: they use nonstandard encoding — pypdf may fail. Try downloading from arXiv instead, or download from nature.com's PDF endpoint.

### Phase 1: Extract Raw Text from PDFs

```bash
pip install pypdf
# Verify: python3 -c "import pypdf; print(pypdf.__version__)"
```

Extract each PDF with a batch script:

```python
from pypdf import PdfReader
import os

pdf_dir = "pdf/"
out_dir = "raw-txt/"
os.makedirs(out_dir, exist_ok=True)

for pdf in sorted(os.listdir(pdf_dir)):
    if not pdf.endswith('.pdf'):
        continue
    r = PdfReader(os.path.join(pdf_dir, pdf))
    pages = []
    for j, page in enumerate(r.pages):
        t = page.extract_text()
        if t and t.strip():
            pages.append(f'[Page {j+1}]\n{t.strip()}')
    content = '\n\n---PAGE BREAK---\n\n'.join(pages)
    txt_path = os.path.join(out_dir, pdf.replace('.pdf', '.txt'))
    with open(txt_path, 'w') as f:
        f.write(content)
    print(f'{pdf}: {len(r.pages)}p, {len(content)} chars')
```

### Phase 2: Create Directory Structure

```
papers/
├── papers.md          # Metadata-level English database
├── papers-zh.md       # Metadata-level Chinese translation
├── raw-txt/           # Extracted raw text from PDFs
│   └── A2-AIOS.txt
├── zh/                # Full Chinese translations (one per paper, THE deliverable)
│   └── A2-AIOS.md
├── pdf/               # Original PDFs
└── download_papers.py
```

### Phase 3: Dispatch Parallel Translation Subagents

**Key parameters:**
- Batch 3 papers at a time via `delegate_task(tasks=[...])` (max concurrent for this user)
- Each task targets ONE paper, reads from `raw-txt/<ID>.txt`, writes to `zh/<ID>.md`
- Include in each task's `context` field:
  - Paper identity (what it is, where published, why important)
  - What sections exist (from PDF page structure)
  - The explicit instruction: "Translate EVERY section, paragraph, and sentence. Do not skip anything."
  - For papers > 50 pages: "This paper is large, read it in chunks of 500 lines at a time using offset/limit."

**Example dispatch:**

```python
delegate_task(tasks=[
    {
        "goal": "Read raw-txt/A2-AIOS.txt and translate ENTIRE paper body to Chinese. Save to zh/A2-AIOS.md",
        "context": "AIOS (COLM 2025) - LLM Agent OS. Sections: Intro, Architecture, Scheduler, Context Manager, Memory Manager, Tool Manager, Experiments, Conclusion.",
        "toolsets": ["file", "terminal"]
    },
    # ... up to 3 tasks in one call
])
```

**Important:** Subagents inherit the parent model. Large papers (50+ pages, 300K+ chars raw text) may need multiple chunked reads. Include `toolsets=["file", "terminal"]` so subagents can use both `read_file` and `write_file`.

### Phase 4: Handle Problematic PDFs

Some PDFs fail pypdf extraction:

| Problem | Symptom | Fix |
|---|---|---|
| Nature journal PDFs | "Stream has ended unexpectedly" | Download from arXiv if available (e.g., ChemCrow: arxiv.org/pdf/2304.05376), or download from nature.com's PDF endpoint |
| Corrupted PDF header | "invalid pdf header: b'<!DOC'" | File is an HTML error page, not a real PDF. Re-download from correct source |
| Small PDF (< 1KB) | Not a real PDF | HTML redirect saved as .pdf. Use browser or curl with -L flag |
| Preprint PDFs (preprints.org) | Blocked direct download | Try `download?format=pdf` query param, or accept HTML text version |

### Phase 5: Verify and Report

After all subagents complete, verify:

```bash
ls -lh zh/*.md | wc -l  # count translations
du -sh zh/               # total size
```

Report to user with a completeness table showing which papers are done and any that failed.

## Workflow C: API Chunk Translation (Legacy, Bulk Metadata Only)

For bulk metadata ingestion (not full body):

1. Extract text via pdftotext or pypdf
2. Use DeepSeek API (`https://api.deepseek.com/v1`, model `deepseek-chat`)
3. Split into ~3000-char chunks at paragraph boundaries
4. Send each chunk with translation prompt
5. Clean up chunk-number prefixes that some API responses inject

**Files:** `templates/translate.py`, `templates/translate_all.py`

## Pitfalls

### Never Deliver Metadata-Level Translation When User Wants Full Body
This is the #1 mistake. The user says "翻译论文" and you reach for papers-zh.md. Papers-zh.md translates METADATA (title, citation, abstract synthesis, relevance). It does NOT translate the paper body. When the user says "逐篇翻译" or "论文原文的完整翻译", they want the FULL BODY.

**How to know:** Output filename `papers-zh.md` = metadata. `zh/<ID>.md` = full body. If the user says "你在干什么呀？我要的是论文的原文", you made this mistake — pivot immediately.

### Don't Default to Batch Parallel — User Prefers Sequential Single-Paper
This is the #2 mistake from this session. The user explicitly criticized parallel dispatch and wants one-paper-at-a-time: read full paper → understand → translate. Default to sequential unless user explicitly requests batch speed.

**Table loss is the core problem with batch parallel.** Parallel subagents using pypdf-extracted text lose table structure. Sequential single-paper with PyMuPDF preserves it.

### Never Just Report "Already Done" When Asked to Search
When the user says "你在谷歌学术上搜索一下...", they want YOU to do the search. Do not report "the work already exists in the filesystem from a previous session." The user's "？" response means: do the work yourself.

### Google Scholar Must Be Verified, Not Assumed
When the user says to search Google Scholar:
1. Actually search (web_search with relevant queries)
2. Cross-check the existing paper list against search results
3. Report what was found, what matches, and what's new
4. Download any new papers found

### pypdf Text Extraction Loses Word Spacing
`pypdf` often concatenates words without spaces. Always verify the output. If text looks like "Therapiddevelopmentofopen-source", switch to PyMuPDF instead.

### PyMuPDF Table Detection Is Not Perfect
Even PyMuPDF's `find_tables()` may miss tables in papers where tables are formatted as text with spacing/alignment rather than actual PDF table objects. In that case, tables appear as regular text paragraphs. You must identify them by context (e.g., "Table 5 presents...") and manually reconstruct them in the Chinese version.

### marker-pdf Has Slow Model Downloads
The `marker-pdf` package downloads vision models on first use, which takes >120 seconds. Use PyMuPDF instead for faster extraction.

### Don't Default to API for Single Important Papers
The API chunk-translation approach sacrifices quality for cost. When the user sends a paper they want to study (not just archive), translate directly. The user explicitly corrected this: "纯机器翻译没有你翻译的准确，很容易表达不清楚论文中的核心意思."

### Verify Python Environment for pypdf
`pypdf` may be installed in system python but not in the Hermes venv. Always run `pip install pypdf` in the active terminal session (which uses the venv). Test with `python3 -c "import pypdf; print(pypdf.__version__)"`.

### Nature Journal PDFs Are Special
Nature PDFs use nonstandard encoding that pypdf rejects. Workaround: (1) Check if arXiv version exists; (2) Download from arXiv instead; (3) For Nature-only papers, download from nature.com's PDF endpoint.

### Batch Size Limit
`delegate_task` supports max 3 concurrent children. For 21 papers: dispatch 7 batches of 3. Each batch runs independently — results auto-enter the conversation.

### Large Paper Bodies Exceed Single `read_file`
Papers like A4-Xi-Survey (86 pages, 344KB raw) or F1-Code-as-Agent-Harness (102 pages, 353KB) must be read in chunks via offset/limit. Instruct subagents explicitly: "Read in chunks of 500 lines at a time."

### Wrong API Key (Legacy API Mode Only)
The older `translate.py` used `OPENAI_API_KEY` which returns 401/403. The current version uses `DEEPSEEK_API_KEY`. Verify credentials before starting.

### Rate Limiting (HTTP 403)
Too many parallel translation processes hit DeepSeek rate limits. Run **one process at a time** in API chunk mode.

### Background Process Zombies
Old translation processes may persist with wrong API keys. Check with `ps aux | grep translate.py` and kill all before restarting.

### Output Buffering
Use `python3 -u translate_all.py` for unbuffered output in API chunk mode.

## User Preference

- **Full-body translation is the default for "翻译论文".** Not metadata. When the user says "逐篇翻译" or "翻译全部论文原文", they want every section of every paper translated.
- **Sequential single-paper approach is the PREFERRED method.** Read full English → understand → translate to Chinese → next paper. NOT parallel subagent dispatch. The user explicitly prefers this for quality (table preservation, consistent terminology, natural Chinese flow).
- **Batch parallel subagent dispatch** is the FALLBACK for very large collections (20+ papers) where the user explicitly says they want speed.
- **Single important papers → direct LLM translation.** Quality > cost.
- **Bulk/batch metadata (papers-zh.md) → direct LLM, one-off.** Only when user explicitly asks for "论文数据库" or "论文列表", not full body.
- **Google Scholar search must be real.** Do not report "work already exists in filesystem" — actually search when asked.
- API chunk translation (DeepSeek) is only for bulk metadata ingestion, never for full body.

## Files

- `templates/translate.py` — single-paper translator (API chunk mode, legacy)
- `templates/translate_all.py` — batch metadata translator (API chunk mode, legacy)
- `references/example-workflow.md` — session transcript of an earlier real run (13 papers, DeepSeek API)
- `references/21-paper-batch-translation-run.md` — 21-paper full-body parallel subagent run (June 2026, this session)
