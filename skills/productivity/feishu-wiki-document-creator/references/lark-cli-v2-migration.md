# lark-cli v2 Migration Guide

## Breaking Changes (June 2026)

`lark-cli` v2 changed the `docs +create` and `docs +update` commands. Old v1 flags will error with:

```
docs +create is v2-only; the old v1 interface has been shut down;
legacy v1 flag(s) --title, --markdown, --folder-token are no longer supported
```

## v1 → v2 Flag Mapping

| v1 Flag | v2 Equivalent | Notes |
|---------|---------------|-------|
| `--title "Title"` | Part of `--content` | Put `<title>Title</title>` or first `# heading` in content |
| `--folder-token "TOKEN"` | `--parent-token "TOKEN"` | Same token, different flag name |
| `--markdown -` | `--doc-format markdown --content -` | Two flags instead of one |
| `--markdown @file.md` | `--doc-format markdown --content @file.md` | @file only accepts relative paths |
| `--mode overwrite` | `--command overwrite` | Also: `append`, `str_replace`, `block_*` |

## v2 Create Command

```bash
# Markdown content from stdin
cat content.md | npx -y @larksuite/cli docs +create \
  --parent-token "NODE_TOKEN" \
  --doc-format markdown \
  --content -

# Markdown content from file (relative path only!)
npx -y @larksuite/cli docs +create \
  --parent-token "NODE_TOKEN" \
  --doc-format markdown \
  --content @content.md

# XML content (richer formatting)
cat content.xml | npx -y @larksuite/cli docs +create \
  --parent-token "NODE_TOKEN" \
  --content -
```

## v2 Update Command

```bash
# Update with markdown (overwrite mode)
cat updated.md | npx -y @larksuite/cli docs +update \
  --doc "https://7colortech.feishu.cn/docx/XXX" \
  --command overwrite \
  --doc-format markdown \
  --content -

# Update with markdown from file (relative path)
npx -y @larksuite/cli docs +update \
  --doc "OBJ_TOKEN" \
  --command overwrite \
  --doc-format markdown \
  --content @updated.md
```

**Key v2 change**: `--mode overwrite` → `--command overwrite`. Other commands: `append`, `str_replace`, `block_delete`, `block_insert_after`, `block_replace`, `block_copy_insert_after`, `block_move_after`.

## @file Path Restriction

`--content @file.md` only works with **relative paths from the current working directory**. Absolute paths like `@/tmp/file.md` will error with `unsafe file path`.

**Workaround**: Use stdin piping for absolute paths:
```bash
cat /tmp/absolute/path/file.md | lark-cli docs +create ... --content -
```

## Reference: lark-doc-md.md

Full Markdown format reference (read via `lark-cli skills read lark-doc references/lark-doc-md.md`):
- Unconditional escaping: `\`, `` ` ``, `*`, `_`, `[`, `]`, `$`, `~`, `<`
- Position-sensitive escaping: `#`, `+`, `-`, `>` at line start
- Table cell escaping: `\|` inside GFM table cells
- Images: `![alt](https://url)` syntax supported
- XML tags (`<b>`, `<u>`, `<img>`) work in markdown mode too
