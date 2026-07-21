---
name: course-resource-scraper
title: Course Resource Scraping and Organization
description: Extract course links from articles, scrape course websites, and organize into categorized bilingual directories (English + Simplified Chinese)
version: 1.0
triggers:
  - User asks to scrape courses from an article
  - User wants to extract course content from URLs
  - User requests organizing course materials into folders
  - User mentions scraping courses (扒课程/爬课程/提取课程)
---

# Course Resource Scraping and Organization

## Overview

This skill handles the complete workflow of:
1. Extracting course links from articles or user-provided URLs
2. Scraping course website content using curl with proper headers
3. Organizing courses into categorized directories
4. Creating bilingual versions (English + Simplified Chinese)

## Trigger Conditions
- User asks to scrape/extract courses from an article
- User provides article URL containing course links
- User wants to organize course materials into structured folders

## Workflow

### Phase 1: Extract Course Information
1. Parse the article to identify course links and descriptions
2. Extract: course name, URL, category, description
3. Handle common course platforms: Skilljar, Coursera, Kaggle, GitHub, Udacity, etc.

### Phase 2: Create Directory Structure
```
~/Documents/AI course/
├── {category_1}/
│   ├── 英文版/
│   └── 简体中文版/
├── {category_2}/
│   ├── 英文版/
│   └── 简体中文版/
└── README.md
```

**Category Examples**:
- 提示工程与智能体开发 (Prompt Engineering & Agent Development)
- AI基础 (AI Fundamentals)
- 智能体开发 (Agent Development)
- Copilot办公应用 (Copilot Office Applications)
- AI与机器学习 (AI & Machine Learning)
- 深度学习 (Deep Learning)
- 开源模型 (Open Source Models)
- ChatGPT与AI应用 (ChatGPT & AI Applications)

### Phase 3: Scrape Course Websites

**Use curl with proper headers**:
```bash
curl -s -L \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept: text/html,application/xhtml+xml" \
  -H "Accept-Language: en-US,en;q=0.5" \
  --connect-timeout 10 \
  --max-time 30 \
  {url} \
  -o /tmp/course_{name}.html
```

**Extract text from HTML**:
```python
import re

def extract_text_from_html(html_content):
    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '\n', text)
    # Clean whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    return text.strip()

def clean_content(content):
    """Remove boilerplate text"""
    lines = content.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
        if any(x in line.lower() for x in ['cookie', 'privacy policy', 'terms of service', 'sign in', 'log in']):
            continue
        cleaned.append(line)
    return '\n\n'.join(cleaned[:200])  # Limit length
```

### Phase 4: Generate Bilingual Content

**English Version Structure**:
```markdown
# {Course Name}

**URL**: {url}

## Course Overview

{extracted_content}

## Key Information
- Duration: {duration}
- Platform: {platform}
- Target Audience: {audience}

## What You'll Learn
{learning_outcomes}
```

**Simplified Chinese Version Structure**:
```markdown
# {Course Name_CN}

**网址**: {url}

## 课程概览

{translated_content}

## 关键信息
- 时长: {duration}
- 平台: {platform}
- 目标受众: {audience}

## 学习内容
{learning_outcomes}
```

### Phase 5: Save Files

**Naming Convention**:
- Use Simplified Chinese for filenames
- Format: `{Course Name}.md`
- Examples:
  - `Anthropic Academy.md`
  - `Google AI基础课程.md`
  - `Kaggle五日AI智能体课程.md`

**File Locations**:
```
{category}/
├── 英文版/{Course Name}.md
└── 简体中文版/{Course Name}.md
```

### Phase 6: Generate Summary Report

Create `README.md` with:
- Statistics (total courses, categories, files)
- Directory tree
- Course list by category
- File description

## Key Learnings

### HTML Extraction Best Practices
1. **Always use curl with headers** - Many sites block requests without proper User-Agent
2. **Handle encoding** - Decode HTML entities (&amp;, &lt;, etc.)
3. **Clean boilerplate** - Remove cookie notices, privacy policies, login prompts
4. **Limit content length** - First 200 lines usually contain main content

### Bilingual Content Strategy
1. **Extract English first** - Original content from website
2. **Translate key sections** - Overview, key information, learning outcomes
3. **Keep technical terms** - Some terms (API, CLI, SDK) may remain in English
4. **Maintain structure** - Both versions should have identical section headers

### Directory Organization
1. **Categorize by topic** - Group related courses
2. **Bilingual subdirectories** - Always create "英文版" and "简体中文版"
3. **Chinese filenames** - Use Simplified Chinese for better readability
4. **JSON manifest** - Save course list as JSON for programmatic access

## Example Usage

**User Request**: 
"https://mp.weixin.qq.com/s/xxxxx 把这篇文章按三步走处理，然后把文章中涉及的课程扒下来，放到Documents目录下，分好类，中英文两个版本"

**Implementation**:
1. Extract article using article-workflow-v2 skill
2. Parse course links from extracted content
3. Create directory structure in ~/Documents/AI course/
4. Scrape each course website with curl
5. Generate bilingual Markdown files
6. Create README.md with summary

## Pitfalls
- **Rate limiting**: Add 2-second delay between requests
- **Dynamic content**: Some sites require JavaScript (use browser tool as fallback)
- **Encoding issues**: Always specify UTF-8 encoding
- **File permissions**: Ensure directory creation succeeds
- **Content length**: Limit extracted content to avoid noise

## Related Skills
- article-workflow-v2: For article extraction and optimization
- wechat-wiki-archiver: For WeChat article extraction
- browser-tool: For JavaScript-heavy sites that curl can't handle
