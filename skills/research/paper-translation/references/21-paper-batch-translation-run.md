# 21-Paper Batch Full-Body Translation Run (June 2026)

## Context

Task: Search Google Scholar for "LM + Harness = Agent" papers (high quality, SCI+), then translate ALL papers' full body text into Chinese.

Seminal work on: LLM + Harness = Agent theory (a theory about agent execution infrastructure being the OS around the model)

## Execution

### Phase 1: Google Scholar Verification
- Searched for latest harness engineering papers
- Found 3 new 2026 papers not in existing database:
  - F0: Agent Harness Engineering (ETCLOVG taxonomy, TMLR submission)
  - F1: Code as Agent Harness (arXiv, 44 authors)
  - F2: Harness Engineering for Language Agents (Preprints)
- Downloaded F0 (3.3MB) and F1 (9.4MB) PDFs; F2 failed (preprints.org blocks direct download)

### Phase 2: PDF Text Extraction
- Tool: `pypdf` (pip install pypdf)
- 18/21 extracted successfully on first pass
- 3 failures:
  - A3-Wang-Survey-LLM-Agents.pdf (smaller duplicate, skipped — big version succeeded)
  - E1-Coscientist-Nature.pdf (Nature encoding issue — downloaded from nature.com PDF endpoint instead)
  - E2-ChemCrow-NatMachIntell.pdf (Nature MI encoding — downloaded from arXiv:2304.05376 instead)

### Phase 3: Parallel Translation
- Batch size: 3 papers per `delegate_task` call (max concurrent = 3)
- 7 batches total to cover 21 papers
- Each subagent: read raw-txt/<ID>.txt → translate full body → write zh/<ID>.md
- Model used: deepseek-v4-flash (inherited from parent)

### Completing

**21 papers, total 2.4MB raw text extracted, ~86MB PDFs**

Completed batches:
- Batch 4 (A3, A4, A5): COMPLETED — all 3 surveys translated
- Other batches: in progress (background subagents)

## Directory Structure Created

```
papers/
├── papers.md              # English metadata database (21 entries)
├── papers-zh.md           # Chinese metadata database (21 entries, 439 lines)
├── raw-txt/               # Extracted raw text from PDFs
│   ├── A2-AIOS.txt (104KB, 34p)
│   ├── A3-Wang-Survey.txt (151KB, 42p)
│   ├── A4-Xi-Survey.txt (344KB, 86p)
│   ├── A5-MultiAgent-Survey.txt (53KB, 13p)
│   ├── B1-ReAct.txt (109KB, 33p)
│   ├── B2-Generative-Agents.txt (129KB, 22p)
│   ├── B3-Toolformer.txt (71KB, 17p)
│   ├── B4-Reflexion.txt (59KB, 19p)
│   ├── B5-Tree-of-Thoughts.txt (67KB, 14p)
│   ├── B6-HuggingGPT.txt (92KB, 27p)
│   ├── B7-AgentBench.txt (175KB, 58p)
│   ├── C1-ToolLLM.txt (83KB, 24p)
│   ├── C2-MetaGPT.txt (76KB, 29p)
│   ├── C3-OpenHands.txt (103KB, 38p)
│   ├── D1-Memory-Survey.txt (146KB, 39p)
│   ├── D2-MemAgent.txt (64KB, 20p)
│   ├── E1-Coscientist.txt (57KB, 13p)
│   ├── E2-ChemCrow.txt (89KB, 38p)
│   ├── F0-Agent-Harness-Engineering.txt (268KB, 71p)
│   └── F1-Code-as-Agent-Harness.txt (353KB, 102p)
├── zh/                    # Full Chinese translations (one per paper)
│   ├── A3-Wang-Survey.md (114KB, 511 lines) ✓
│   ├── A4-Xi-Survey.md (125KB, 535 lines) ✓
│   ├── A5-MultiAgent-Survey.md (49KB, 312 lines) ✓
│   └── (others in progress)
├── pdf/                   # Original PDFs
└── download_papers.py
```

## Key Lessons

1. **Don't confuse metadata translation with full body translation.** If the file is called `papers-zh.md`, it's metadata. The user will correct you forcefully.
2. **PDF extraction needs fallback strategies.** Nature journal PDFs fail pypdf. Always have an arXiv download as backup.
3. **Batch of 3 via delegate_task is the sweet spot.** One batch takes 2-5 minutes depending on paper length.
4. **Large papers need chunked reads in subagents.** Instruct subagents explicitly to read in 500-line increments for 80+ page papers.
