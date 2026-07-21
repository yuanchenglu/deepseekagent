---
name: static-content-site
category: creative
description: Build production-quality static HTML/CSS/JS content analysis websites with multi-document navigation, sidebar layout, theme toggle, and Markdown-based content tabs.
tags: [html, css, javascript, static-site, content-analysis, documentation-site]
trigger: user asks to build a website for presenting document/paper analysis, content catalog, or multi-article study guides
---

# Static Content Analysis Site

Build a production-quality static HTML/CSS/JS website for presenting multi-document content analysis (paper reviews, article collections, research companions).

## User Preferences (this user — 小路)

- **Theme**: Light theme as default, with a toggle to switch to dark theme. Save preference to `localStorage`.
- **Layout**: Left collapsible sidebar for navigation (paper/document list). NOT a top dropdown — sidebar saves more room for content.
  - Sidebar has a collapse/expand button (◀/▶)
  - Collapse state persisted in `localStorage`
- **Paper/Document selector**: Show **both English and Chinese titles** so the user can identify papers at a glance.
- **Content tabs**: Only the overview tab uses custom HTML formatting. All other tabs read content from **standalone Markdown files** loaded via `fetch()`. No inline HTML rendering for thinking/Q&A or translation tabs.
- **Thinking/Q&A section**: "苏格拉底启发式" Socratic Q&A, each paper has its own `.md` file. Pure Markdown, no foldable/collapsible UI, no custom styling.

## Structure Pattern

```
html/
├── index.html              ← Single-page app (all CSS + JS in one file)
├── zh-md/                  ← Symlink to zh translations
├── en-md/                  ← Symlink to English originals
└── thinking-md/            ← Socratic Q&A files (one .md per document)
```

### File Access via Symlinks

When serving from `html/` directory, create symbolic links so `fetch()` can load Markdown files:

```bash
ln -sf /absolute/path/to/zh-md html/zh-md
ln -sf /absolute/path/to/en-md html/en-md
```

If symlinks are not possible, start the HTTP server from the parent directory:

```bash
cd parent_dir && python3 -m http.server 8080
```

Then the index.html lives at `/html/index.html` and Markdown paths use relative navigation like `../zh-md/filename.md`.

### Markdown Loading Pattern

```javascript
async function loadMDTab(containerId, filePath) {
  const container = document.getElementById(containerId);
  container.innerHTML = `<div class="md-loading"><div class="spinner"></div><p>加载中...</p></div>`;
  try {
    const resp = await fetch(filePath);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const md = await resp.text();
    container.innerHTML = `<div class="md-content">${mdToHtml(md)}</div>`;
  } catch(e) {
    container.innerHTML = `<div class="md-error">
      <p>⚠️ 加载失败</p>
      <p>请直接查看 <a href="${filePath}" style="text-decoration:underline;">源文件</a></p>
    </div>`;
  }
}
```

### Simple Client-Side Markdown → HTML Renderer

Keep a minimal standalone renderer inline in the HTML. Only handles: headers (h1-h4), bold, italic, inline code, blockquotes, HR, unordered/ordered lists, paragraphs. Do NOT add a dependency on marked.js or libraries.

```javascript
function mdToHtml(text) {
  let html = text;
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/m, '<h1>$1</h1>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
  html = html.replace(/^\d+\. (.*)$/gm, '<li>$1</li>');
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';
  // Fix nesting
  html = html.replace(/<p><h([1-4])>/g, '<h$1>');
  html = html.replace(/<\/h([1-4])><\/p>/g, '</h$1>');
  html = html.replace(/<p><(li|blockquote|hr)>/g, '<$1>');
  html = html.replace(/<(li|blockquote|hr)><\/p>/g, '<$1>');
  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>.*?<\/li>(\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
  return html;
}
```

## Theme System

Use `data-theme` attribute on `<html>`:

```css
:root { /* light theme variables */ }
[data-theme="dark"] { /* dark theme overrides */ }
```

Toggle function:

```javascript
function toggleTheme() {
  isDark = !isDark;
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = isDark ? '🌙' : '☀️';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}
```

## Collapsible Sidebar Pattern

```css
.sidebar {
  position: fixed; top: 0; left: 0;
  width: 280px; height: 100vh;
  transition: transform 0.3s ease;
}
.sidebar.collapsed {
  transform: translateX(calc(-280px + 36px)); /* show only the expand button area */
}
.sidebar.collapsed ~ .main { margin-left: 36px; }
```

## Data Architecture

Embed paper/document data as a JavaScript array of objects. Each object contains:

```javascript
{
  id: 1,
  zhTitle: '中文标题',
  enTitle: 'English Title',
  date: '2026年6月',
  authors: '作者名',
  venue: '出处',
  zhFile: 'zh-md/01-file.md',
  enFile: 'en-md/01-file.md',
  thinkFile: 'thinking-md/01-file.md',
  metrics: [{value: '...', label: '...'}],
  problems: [{title: '...', desc: '...'}],
  solutions: [{title: '...', desc: '...'}],
  insights: [{emoji: '⚡', title: '...', desc: '...'}],
  resultsTables: [{title: '...', headers: [...], rows: [...]}],
  highlights: [{title: '...', text: '...'}],
  harScore: 4  // 1-5 relevance score
}
```

## Pitfalls

1. **Don't embed all content in HTML** — Only the overview/analysis is custom HTML. Q&A, translations, and original text should be standalone Markdown files. This makes content editable without touching the page structure.
2. **Symlinks before server root changes** — If the HTTP server root is at `html/`, symlink the content directories inside it. Otherwise server blocks `../` access (403/404).
3. **No library dependencies** — Keep the Markdown renderer simple and self-contained. Don't import `marked`, `showdown`, or other libraries. The minimal renderer handles 90% of paper content.
4. **localStorage for persistence** — Always persist theme and sidebar state. Users expect the layout to survive page refreshes.
5. **Show both languages** — The paper selector must display both EN and CN titles. This user reads both and uses the English title for precise identification.
6. **Only overview is HTML** — This user explicitly wants only the first tab (概述) to be hand-crafted HTML. Everything else (思考/译文/原文) must be loaded from Markdown files.
