# Example: DeepSeek AI 13-Paper Translation (2026-05-23)

## Task
User: "把deepseek和梁文锋发的所有论文列举出来，先列成清单，然后每一项都下载下来，下载后将所有论文翻译成简体中文。"

## Workflow

### Phase 1: Discovery
```bash
# arXiv author search for "Wenfeng Liang" (梁文锋)
python3 -c "
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, ssl
query = 'au:Liang_Wenfeng'
url = f'https://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&max_results=20&sortBy=submittedDate&sortOrder=descending'
...
"
```
Result: 13 papers found, all with Wenfeng Liang as co-author.

### Phase 2: Download
```bash
mkdir -p ~/Code/DeepSeekNews/papers
for id in 2601.07372v1 2512.24880v2 ...; do
  python3 -c "
import urllib.request, ssl
ctx = ssl.create_default_context()
req = urllib.request.Request('https://arxiv.org/pdf/$id', headers={'User-Agent': 'HermesAgent/1.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    with open('\${id}.pdf', 'wb') as f: f.write(resp.read())
"
done
```
All 13 PDFs downloaded (~28MB total).

### Phase 3: Extraction
```bash
cd papers/ && for f in *.pdf; do pdftotext -layout "$f" "${f%.pdf}.txt"; done
```
All English (CN=0), ~1.8M total characters.

### Phase 4: Translation (the hard part)

**Attempt 1 (failed):** Subagents via `delegate_task`
- 3 subagents, 10-min timeout each → all timed out
- Lesson: 300K-char papers can't be translated in one agent session

**Attempt 2 (failed):** Background processes with wrong API key
- Used `OPENAI_API_KEY` (OpenCode) instead of `DEEPSEEK_API_KEY`
- Hit 401/403 errors, created garbage output files with 53 FAILED markers
- Lesson: Verify API keys before launching background processes

**Attempt 3 (failed):** Too many parallel processes
- 19 duplicate translate.py processes from multiple restart attempts
- DeepSeek API rate limiting → HTTP 403 on all
- Lesson: Kill zombies first, run one process at a time

**Attempt 4 (success):** Single batch script
- `translate_all.py` importing `translate.py`
- Reads API key from env file directly (not `source`)
- Sequential processing with 2s pause between papers
- 13 papers, ~30 minutes total

### Phase 5: Cleanup
```python
import re
# Strip chunk-number prefixes some API responses add
cleaned = re.sub(
    r'^这是学术论文的第\d+/\d+(?:部分|块)[。：]\s*翻译成中文[：:]\s*',
    '', text, flags=re.MULTILINE
)
```

## Results
| Paper | Original (EN) | Translation (ZH) |
|-------|---------------|-------------------|
| DeepSeek-R1 | 319K | 390K |
| V3 Technical Report | 197K | 188K |
| Insights into V3 | 160K | 119K |
| DeepSeek-V2 | 152K | 55K |
| Fire-Flyer AI-HPC | 149K | 113K |
| DeepSeekMoE | 139K | 95K |
| DeepSeek LLM | 136K | 122K |
| Conditional Memory | 127K | 116K |
| V3.2 | 91K | 76K |
| DeepSeek-Coder | 89K | 73K |
| mHC | 88K | 74K |
| Native Sparse Attention | 87K | 77K |
| Coder-V2 | 75K | 101K |
| **Total** | **~1,800K** | **~1,600K** |

## Key Learnings
1. **One process at a time** for bulk API translation — parallelism triggers rate limits
2. **Read API key from env file directly** — don't rely on `source` in background shells
3. **Kill zombie processes before restarting** — `pkill -f translate.py` then verify with `ps aux`
4. **Chunk size 3000 chars** with paragraph-boundary splitting works well for academic text
5. **pdftotext -layout** is sufficient for English academic papers — no need for pymupdf/marker
6. **DeepSeek API deepseek-chat** model is cheap and good quality for EN→ZH academic translation
