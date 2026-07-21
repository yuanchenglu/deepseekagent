# Docsify Dynamic Sidebar Switching Plugin

When using top-level tab navigation (文章/课程/开源项目), each tab needs its own sidebar. This plugin detects the current section from the URL path, fetches the appropriate `_sidebar.md`, and replaces the sidebar DOM content.

## How it works

1. `_navbar.md` contains tab links: `<a href="/#/文章/README" data-section="文章">`
2. The plugin's `afterEach` hook fires on every route change
3. It extracts the section name from the URL path
4. If the section changed, it fetches `{section}/_sidebar.md` via AJAX
5. Parses the markdown with `marked.parse()` and replaces `.sidebar-nav` innerHTML
6. Highlights the active tab visually

## Key implementation notes

- Docsify already loads `marked` — no extra dependency for parsing sidebar markdown
- Cache sidebar content in a JS object to avoid re-fetching on every navigation
- The global `_sidebar.md` is pre-cached in `hook.init()` as a fallback
- Tab highlight uses `data-section` attribute matching

## Router path matching

```javascript
function getSection(path) {
  var SECTIONS = ['文章', '课程', '开源项目'];
  for (var i = 0; i < SECTIONS.length; i++) {
    // Docsify routes encode non-ASCII paths
    if (path.indexOf('/' + encodeURIComponent(SECTIONS[i]) + '/') === 0) {
      return SECTIONS[i];
    }
  }
  return null;  // homepage or other — use global sidebar
}
```

## Sidebar cache

```javascript
var sidebarCache = {};

function fetchSidebar(section, cb) {
  if (sidebarCache[section]) return cb(sidebarCache[section]);
  var xhr = new XMLHttpRequest();
  xhr.open('GET', vm.config.basePath + encodeURIComponent(section) + '/_sidebar.md');
  xhr.onload = function() {
    if (xhr.status === 200) {
      sidebarCache[section] = xhr.responseText;
      cb(xhr.responseText);
    }
  };
  xhr.send();
}
```

## DOM update

```javascript
function updateSidebar(content) {
  var sidebarEl = document.querySelector('.sidebar-nav');
  if (!sidebarEl || !content) return;
  var parsed = marked.parse(content);
  sidebarEl.innerHTML = parsed;
}
```

## Per-section sidebar generation

The sidebar generator script must produce `_sidebar.md` inside each section folder (文章/, 课程/, 开源项目/). Each contains only the files within that section's subdirectory.
