---
name: folder-naming-convention
title: Folder Naming Convention for Article Storage
description: Standard naming rules for organizing article folders in ~/Documents/article/
version: 1.0
triggers:
  - Creating new article folder
  - Organizing existing article folders
---

# Folder Naming Convention

## Location
`~/Documents/article/`

## Naming Rules

### 1. Use Article Title (Chinese)
- Extract the main title from the article content
- Convert to simplified Chinese if needed
- Remove punctuation marks (，。！？)
- Keep meaningful keywords

### 2. Format
- No spaces between characters
- Use descriptive Chinese title
- Length: 15-30 characters ideal
- Must clearly identify the article topic

### 3. Examples

**Good:**
- `给10万Star的Hermes装个记忆外挂AI终于能越用越聪明了/`
- `我发现大多数人配置Hermes的顺序都错了/`
- `RAG总是答非所问我发现了Karpathy的LLM_Wiki模式/`
- `OpenCode加OpenSpec加OhMyOpenCode联合SDDATDD开发指南/`

**Bad:**
- `article/` (too vague)
- `article_20250418_2/` (date-based, not descriptive)
- `article_extra1/` (numbered, not descriptive)
- `claude_code_setup/` (English, not descriptive enough)

### 4. Folder Contents
Each folder must contain ALL related files:
- `article_optimized.md` - Full optimized article
- `cover_900x500.png` - Cover image (MUST be inside folder)
- `feishu_archive.md` - Feishu format
- `wechat_format.txt` - WeChat format
- Any additional supporting files

## Pitfalls
- DO NOT use generic names like "article", "temp", "output"
- DO NOT use date-based naming unless it's a news article
- DO NOT use English abbreviations or technical terms as folder names
- DO NOT create separate directories for cover images
- ALWAYS use the actual article title in Chinese