---
name: wechat-to-lark
description: Extract WeChat Official Account (微信公众号) articles and convert them to Lark/Feishu documents. Handles WeChat's anti-scraping protection using Playwright browser automation.
version: 1.0.0
metadata:
  hermes:
    tags: [wechat, 微信公众号, lark, feishu, article, extraction, conversion, productivity]
---

# WeChat to Lark Document Converter

Extract content from WeChat Official Account articles and automatically create formatted Lark/Feishu documents.

## Problem Solved

WeChat articles (mp.weixin.qq.com) have strong anti-scraping protection:
- Direct HTTP requests get redirected to verification pages
- Standard scraping tools fail with "脚本解析失败" errors
- Desktop User-Agent is more likely to be blocked

## Solutions (try in order):

1. **curl + desktop User-Agent + js_content parsing** (Recommended - most reliable, no dependencies)
2. **curl + mobile User-Agent + meta tags** (Fastest - try first, but check content length)
3. **Playwright browser automation** (Fallback - when curl methods fail)

## Quick Extraction (Try First)

The simplest method uses `curl` with mobile User-Agent to fetch the article HTML, then extracts content from Open Graph meta tags:

```bash
# Fetch article with mobile User-Agent
curl -sL "https://mp.weixin.qq.com/s/xxxxx" \
  -A "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15" \
  --max-time 15 > article.html
```

```python
import re

def extract_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract from Open Graph meta tags
    title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
    title = title_match.group(1) if title_match else "Unknown"
    
    # Full article content is in og:description
    desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
    content = desc_match.group(1) if desc_match else ""
    
    # Clean up escape sequences
    content = content.replace('\\x0a', '\n').replace('\\n', '\n')
    content = content.replace('\\x26lt;', '<').replace('\\x26gt;', '>')
    content = content.replace('\\x26quot;', '"').replace('\\x26amp;', '&')
    
    return {
        'title': title,
        'content': content,
        'url': url
    }

# Usage
article = extract_from_html('article.html')

# IMPORTANT: Check if extraction succeeded
if len(article['content']) < 100:
    print("⚠️ Meta tag extraction returned truncated content, use Robust Extraction method")
```

**Why this works**: WeChat stores the complete article text in `og:description` meta tag for mobile clients. This bypasses most anti-scraping measures.

**⚠️ Limitation**: This method increasingly returns truncated content (10-50 chars) for newer WeChat articles. Always check `len(content)` and fall back to Robust Extraction if < 500 characters.

## Robust Extraction (Recommended)

When the simple meta tag method returns empty or truncated content (common with newer WeChat articles), use **desktop User-Agent with full HTML parsing**:

```python
import re
import subprocess

def extract_wechat_article(url):
    """Extract WeChat article using desktop UA and full HTML parsing - MOST RELIABLE METHOD"""
    
    # Use desktop User-Agent (more likely to get full content)
    result = subprocess.run(
        ['curl', '-sL', url, 
         '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
         '--max-time', '15'],
        capture_output=True,
        text=True
    )
    
    html = result.stdout
    
    # Check if we got a valid HTML response
    if len(html) < 10000:
        print(f"⚠️ HTML response too small ({len(html)} chars), may have failed")
    
    # Extract title from h1 or meta
    title_match = re.search(r'<h1[^>]*class="rich_media_title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    else:
        title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
        title = title_match.group(1) if title_match else "Unknown"
    
    # Extract account name
    account_match = re.search(r'var nickname = [^"]*"([^"]+)"', html)
    if not account_match:
        account_match = re.search(r'profile_nickname[^>]*>([^<]+)', html)
    account = account_match.group(1) if account_match else ""
    
    # Extract publish time
    time_match = re.search(r'var publish_time = [^"]*"([^"]+)"', html)
    if not time_match:
        time_match = re.search(r'id="publish_time"[^>]*>([^<]+)', html)
    publish_time = time_match.group(1) if time_match else ""
    
    # Extract content from js_content div
    content_match = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*<script', html, re.DOTALL)
    if content_match:
        content_html = content_match.group(1)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content_html)
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        # Clean trailing JS code
        text = re.sub(r'var first_sceen__time.*', '', text, flags=re.DOTALL)
        text = re.sub(r'微信扫一扫关注该公众号.*', '', text, flags=re.DOTALL)
        text = re.sub(r'继续滑动看下一个.*', '', text, flags=re.DOTALL)
        text = text.strip()
    else:
        text = ""
    
    return {
        'title': title,
        'account': account,
        'publish_time': publish_time,
        'content': text,
        'url': url
    }

# Usage
article = extract_wechat_article('https://mp.weixin.qq.com/s/xxxxx')
print(f"Title: {article['title']}")
print(f"Account: {article['account']}")
print(f"Content length: {len(article['content'])} chars")
```

**Why this is the most reliable method**:
- Desktop User-Agent gets full HTML page (often 1-3MB)
- `js_content` div contains the complete article text
- Works even when meta tags are truncated
- No browser automation needed (fast and lightweight)

## Playwright Method (Fallback)

## Prerequisites

- Python 3 with Playwright installed: `pip install playwright`
- Playwright browsers: `playwright install chromium`
- Lark CLI configured and authenticated (see lark-cli-setup skill)

## Workflow

### Step 1: Extract WeChat Article

```python
import asyncio
from playwright.async_api import async_playwright

async def extract_wechat_article(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()
        
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Check for verification wall
            if "wappoc_appmsgcaptcha" in page.url:
                print("⚠️ Verification required - article may need manual access")
                return None
            
            # Extract metadata
            title = await page.evaluate("""
                () => {
                    const h1 = document.querySelector('h1.rich_media_title');
                    if (h1) return h1.innerText.trim();
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const match = script.innerText.match(/var msg_title[^=]*=\\s*["\']([^"\']+)["\']/);
                        if (match) return match[1];
                    }
                    return null;
                }
            """)
            
            account = await page.evaluate("""
                () => {
                    const nickname = document.querySelector('.profile_nickname');
                    if (nickname) return nickname.innerText.trim();
                    return null;
                }
            """)
            
            publish_time = await page.evaluate("""
                () => {
                    const time = document.querySelector('#publish_time');
                    if (time) return time.innerText.trim();
                    return null;
                }
            """)
            
            # Extract content
            content_html = await page.evaluate("""
                () => {
                    const content = document.querySelector('#js_content');
                    if (content) return content.innerHTML;
                    return null;
                }
            """)
            
            text = await page.evaluate("""
                () => {
                    const content = document.querySelector('#js_content');
                    if (content) return content.innerText;
                    return null;
                }
            """)
            
            return {
                'title': title,
                'account': account,
                'publish_time': publish_time,
                'content': text,
                'content_html': content_html,
                'url': url
            }
            
        finally:
            await browser.close()
```

### Step 2: Convert to Markdown

```python
def convert_to_markdown(article):
    md = f"""# {article['title']}

> 来源：{article['account'] or '微信公众号'}  
> 发布时间：{article['publish_time'] or '未知'}  
> 原文链接：{article['url']}

---

{article['content']}

---

*本文档由 AI 自动从微信公众号文章转换生成*
"""
    return md
```

**Step 3: Create Lark Document**

```bash
# Save markdown to file (must use relative path)
echo "$MARKDOWN_CONTENT" > article.md

# Create Lark document (lark-cli v2 syntax)
cd /tmp
lark-cli docs +create \
  --parent-token "NODE_TOKEN" \
  --doc-format markdown \
  --content @article.md
```

**Important**: lark-cli v2 requires:
- `--parent-token` instead of `--folder-token`
- `--doc-format markdown --content @file.md` instead of `--markdown @file.md`
- Title must be in content (first `# heading`), not a separate `--title` flag
- `@file.md` must be a relative path from cwd (not absolute)

## Complete Example

```python
import asyncio
import json
from playwright.async_api import async_playwright

async def wechat_to_lark(wechat_url):
    # Step 1: Extract
    article = await extract_wechat_article(wechat_url)
    if not article:
        return None
    
    # Step 2: Convert to markdown
    markdown = convert_to_markdown(article)
    
    # Step 3: Save and create Lark doc
    import subprocess
    with open('article.md', 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    result = subprocess.run(
        ['lark-cli', 'docs', '+create',
         '--parent-token', 'NODE_TOKEN',
         '--doc-format', 'markdown',
         '--content', '@article.md'],
        cwd='/tmp',
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)

# Usage
result = asyncio.run(wechat_to_lark('https://mp.weixin.qq.com/s/xxxxx'))
print(f"Document created: {result['data']['doc_url']}")
```

## Important: Preserve Full Content

**Always extract and preserve the complete original article content.** Do not:
- Summarize or paraphrase
- Remove sections or examples
- Skip code blocks or command examples
- Omit the article conclusion or call-to-action

The extracted `content` from Playwright contains the full text - use it entirely without editing.

## Troubleshooting

### "Verification required" error
- Some articles require logged-in WeChat access
- Try accessing the article manually in WeChat first
- Some corporate/verified accounts have stricter protection

### Empty or truncated content from meta tags
- **Problem**: `og:description` only returns 10-20 characters like "算力、时间和培训，都省了"
- **Solution**: Switch to desktop User-Agent with full HTML parsing (see "Robust Extraction" method above)
- **Cause**: WeChat has changed how they populate meta tags for some articles
- **Quick check**: If `len(content) < 100`, extraction failed - use robust method immediately

### Playwright not found
```bash
pip install playwright
playwright install chromium
```

### Lark CLI path issues
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
```

### Empty content extraction
- Check if article requires subscription
- Verify the article URL is valid and not expired
- Some articles may have different HTML structure
- Try the desktop User-Agent method if mobile UA fails

### Content was shortened/summarized
If the Lark document is missing content:
1. Re-extract using the Playwright script above
2. Verify the `content` field has full text (check character count)
3. Pass the content directly to markdown without modification
4. The full article should include all sections, examples, code blocks, and endings

## Extraction Method Decision Tree

```
Start
  │
  ├─→ Try curl + mobile UA + og:description
  │     │
  │     ├─→ Content > 1000 chars? → ✅ Use this
  │     │
  │     └─→ Content empty/short? 
  │           │
  │           └─→ Try curl + desktop UA + js_content parsing
  │                 │
  │                 ├─→ Content > 1000 chars? → ✅ Use this
  │                 │
  │                 └─→ Still failing?
  │                       │
  │                       └─→ Try Playwright browser automation
  │                             │
  │                             └─→ Success? → ✅ Use this
  │                                   │
  │                                   └─→ Verification wall? → ❌ Manual extraction needed
  │
```

**Recommendation**: Always check content length. If < 500 chars, the extraction likely failed.

## Alternative: Using wechat-article-extractor npm skill

If Playwright approach fails, try the npm skill (less reliable):

```bash
npx skills add freestylefly/wechat-article-extractor-skill@wechat-article-extractor -g -y
cd ~/.agents/skills/wechat-article-extractor
npm install
```

Then use in Node.js:
```javascript
const { extract } = require('./scripts/extract.js');
const result = await extract('https://mp.weixin.qq.com/s/xxxxx');
```

**Note**: This skill often fails with WeChat's current anti-scraping measures. Playwright approach is more reliable.

## Security Notes

- Playwright runs a real browser - more detectable but bypasses simple bot detection
- Mobile User-Agent is crucial - desktop agents are more likely to be blocked
- Headless mode works but could be detected; use headed mode if issues persist
- Respect rate limits - don't scrape too many articles in rapid succession

## Related Skills

- `lark-cli-setup` - Install and configure Lark CLI
- `baoyu-article-illustrator` - Add AI-generated illustrations to articles
