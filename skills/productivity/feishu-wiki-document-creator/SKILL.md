---
name: feishu-wiki-document-creator
description: Create comprehensive documents and publish them to Feishu Wiki via lark-cli. Supports long document workflow (skeleton + block_insert_after), XML/Markdown format, and wiki node management.
version: 1.1.0
trigger: When user asks to create a document/article/guide and publish to Feishu
---

# Feishu Wiki Document Creator

> **References**: [lark-cli v2 migration guide](references/lark-cli-v2-migration.md) — flag mapping, breaking changes, @file path restriction.

## Purpose
Create well-formatted documents and publish them to Feishu Wiki with automatic verification.

## Steps

### 0. Check Tooling

```bash
which lark-cli          # local installation (preferred)
# OR
npx -y @larksuite/cli   # npx fallback — slower, no auth binding
```

If `lark-cli` is available locally, use it directly (faster, supports `--as user`, `--format json`). Fall back to `npx` only when lark-cli is not installed.

> **⚠️ BREAKING CHANGE (June 2026)**: `lark-cli` v2 changed `docs +create` flags. Old v1 flags (`--title`, `--folder-token`, `--markdown`) will error. Always use `--api-version v2`.

### 1. Pre-auth: Bind & Login (first time)

If lark-cli is not yet bound to the current Hermes context:

```bash
# Bind (user must confirm)
lark-cli config bind --source hermes --identity user-default

# Auth split-flow (do NOT block in same turn — use --no-wait --json)
lark-cli auth login --recommend --no-wait --json
# → extract verification_url + device_code, show QR code to user
# → user authorizes, then:
lark-cli auth login --device-code <device_code>
```

> `--output` for QR codes must be a **relative path** from cwd, not absolute (e.g. `./qr.png`, not `/tmp/qr.png`).

### 2. Create a Wiki Node

Create a new child document under an existing wiki node, or at the root of a space:

```bash
# Under a parent wiki node (recommended)
lark-cli wiki +node-create \
  --parent-node-token "<PARENT_NODE_TOKEN>" \
  --title "文档标题"

# In a specific space
lark-cli wiki +node-create \
  --space-id "<SPACE_ID>" \
  --title "文档标题"
```

**To find the parent node token**: use `lark-cli wiki +node-get --node-token "<wiki_URL_or_token>"`.

### 3. Write Content (Two Strategies)

**Strategy A — Skeleton then Append (recommended for long documents):**

Start with a skeleton (title + headings), then populate each section with `block_insert_after`:

```bash
# 3a. Write skeleton
lark-cli docs +update --api-version v2 --doc "<doc_url>" \
  --command overwrite \
  --content '<title>文档标题</title><h1>引言</h1><p>概述...</p><h1>章节一</h1><h1>章节二</h1>'

# 3b. Fetch block IDs
lark-cli docs +fetch --api-version v2 --doc "<doc_url>" --detail with-ids --format json

# 3c. Append content after a specific block
lark-cli docs +update --api-version v2 --doc "<doc_url>" \
  --command block_insert_after \
  --block-id "doxcnXXX" \
  --content '<h2>小节</h2><ul><li>详情1</li><li>详情2</li></ul>'

# 3d. Append to end (--block-id -1)
lark-cli docs +update --api-version v2 --doc "<doc_url>" \
  --command block_insert_after \
  --block-id "-1" \
  --content '<h2>更多内容</h2><p>...</p>'
```

**Strategy B — Single Create (for short documents):**

```bash
# Markdown (preferred for simple docs)
cat content.md | lark-cli docs +create --api-version v2 \
  --parent-token "NODE_TOKEN" \
  --doc-format markdown \
  --content -

# XML (richer: callout, grid, checkbox, tables)
lark-cli docs +create --api-version v2 \
  --parent-token "NODE_TOKEN" \
  --content '<title>标题</title><p>正文</p>'
```

### 4. Verify Content

```bash
# Fetch outline
lark-cli docs +fetch --api-version v2 --doc "<doc_url>" --scope outline --format json

# Fetch full content as XML
lark-cli docs +fetch --api-version v2 --doc "<doc_url>" --format json
```

> Do NOT use `browser_navigate` or `curl` to verify private Feishu docs — they require authentication.

### 5. Link Generation

Generate BOTH formats:
- **Docx format**: `https://<domain>.feishu.cn/docx/{obj_token}`
- **Wiki format**: `https://<domain>.feishu.cn/wiki/{node_token}`

The `wiki +node-create` result includes both `node_token` and `obj_token`.

## Common Pitfalls
1. **Browser/curl won't work for private docs**: Feishu documents require authentication. Always use `lark-cli docs +fetch` for verification.
2. **Empty documents**: Always verify content was actually written (`docs +fetch`).
3. **Wrong link format**: Docx and Wiki URLs have different patterns — provide both.
4. **Access permissions**: Ensure document is accessible to intended audience.
5. **Missing verification**: Never assume document was created successfully — always fetch to confirm.
6. **XML content length**: For very long content, use Strategy A (skeleton + append) rather than sending everything in one `--content`.
7. **Absolute paths**: `--content @file.md` and `--output` only accept relative paths from cwd; use stdin (`cat file | cmd --content -`) for absolute paths.
8. **Auth split-flow**: Never block on `lark-cli auth login` without `--no-wait` in an agent turn — the user won't see the URL.

## Quality Checklist
- [ ] Content is complete and comprehensive
- [ ] Formatting is clean (tables, headers, lists, callouts)
- [ ] Both docx and wiki links generated
- [ ] Content verified via `docs +fetch`
- [ ] Document length confirmed
- [ ] User can open and view content