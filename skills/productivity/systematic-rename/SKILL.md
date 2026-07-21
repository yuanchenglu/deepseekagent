---
name: systematic-rename
description: "Systematically rename a product, library, or identifier across an entire codebase — search, categorize, replace, and verify. Covers user-facing strings vs. code-internal identifiers, config/build artifacts, i18n, and documentation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [rename, refactor, find-replace, codebase, rebranding]
    related_skills: [simplify-code, codebase-inspection]
---

# Systematic Rename

Methodically rename a string across a full codebase, separating user-facing
changes from internal identifiers so you don't break the build.

## When to Use

Use this skill when the user asks you to rename something that appears
throughout the project:

- Product/brand rename: "rename product X to Y everywhere"
- Library or API rename: "change all references from foo-lib to bar-lib"
- Feature/codename rename: "this feature was called X, now call it Y"
- Company/author rename: "change the copyright holder"

Do NOT use for one-off find-replace in a single file — that's a simple
`patch()` call.

## The Methodology

### Phase 1 — Comprehensive Search

Search every relevant file type for both exact-quoted and unquoted variants:

```bash
# Quoted strings (display names, API keys, config values)
grep -rn '"OldName"' --include='*.ts' --include='*.tsx' --include='*.json' --include='*.md' \
  --include='*.js' --include='*.cjs' --include='*.mjs' --exclude-dir=node_modules \
  --exclude-dir=.git --exclude-dir=dist --exclude-dir=release

# Single-quoted strings
grep -rn "'OldName'" ...

# Unquoted (type names, function names, identifiers) — be careful with these
grep -rn 'OldName' ...
```

For large codebases, pipe through `wc -l` first to gauge scope, then paginate
with `head -50` to inspect the patterns.

### Phase 2 — Categorize

Sort every hit into one of **three categories**:

| Category | What it is | Rename? |
|----------|-----------|---------|
| **A — User-facing strings** | Product name in UI, tooltips, notifications, i18n locales, tray, window title, update dialogs | ✅ YES |
| **B — Build/packaging artifacts** | `productName`, `artifactName`, `appId` comment, shortcuts, uninstall display name, zip/app file names, installer metadata | ✅ YES |
| **C — Internal code identifiers** | Type names (`KunConfig`, `KunServeHandle`), function names (`startKunServe`), file paths (`kun/` dir), import paths (`@shared/kun-gui-api`), Git repo URLs | ❌ NO (unless user explicitly asks) |

**Critical rule:** Only rename Category A and B unless the user says "change
ALL references everywhere." Renaming Category C identifiers (type names,
import paths, file names) will break the build and require cascading changes.

### Phase 3 — Replace by File Type

Apply changes grouped by file type — each type has its own pitfall:

**Package/build config files:**
- `package.json`: `productName`, `name`, `description`, `author`
- `electron-builder.config.cjs`: `productName`, `artifactName`, `shortcutName`,
  `uninstallDisplayName`, `NSMicrophoneUsageDescription`, `copyright`
- `scripts/zip-mac-app.cjs`: `appName` (e.g. `'Kun.app'`), `zipPath` pattern
- `scripts/generate-mac-latest.cjs`: artifact filename regex
- Other scripts referencing `PRODUCT_NAME`

**App identity (Electron/Desktop):**
- `src/main/app-identity.ts`: `APP_PRODUCT_NAME` constant
- `src/main/index.ts`: `tray.setToolTip()`, notification title fallback
- `src/main/gui-updater.ts`: update notification title/message
- `src/main/claw-runtime.ts`: fallback welcome name
- `src/main/services/write-export-service.ts`: DOCX creator metadata

**UI/i18n strings:**
- `src/renderer/src/locales/*/common.json`: `appName`, `clawCoreTitle`,
  `runtimeStatus*` strings
- `src/renderer/src/agent/kun-runtime.ts`: `displayName`
- `src/renderer/src/plan/plan-prompts.ts`: user-facing plan prompts

**Documentation:**
- `README.md` / `README.en.md`: title, tagline, product descriptions
- `AGENTS.md`: product name references (keep internal `kun serve`, `kun/` dir)
- `DESIGN.md` / `DESIGN.zh-CN.md`: `product_name`, `tagline`
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CLA.md`: community/project name
- `kun/README.md`: product title (keep CLI/docs references)

**Other code with display strings:**
- Custom window title, desktop file name, `.desktop` entry
- Notification body text
- About dialog

### Phase 4 — Verify

Run a final search for the **old name** to confirm no stragglers:

```bash
grep -rn '"OldName"' --include='*.ts' --include='*.tsx' --include='*.json' \
  --include='*.md' --include='*.js' --include='*.cjs' --include='*.mjs' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist \
  --exclude-dir=release | grep -v 'node_modules\|\.git'
```

Then for single-quoted:
```bash
grep -rn "'OldName'" ...
```

Check git diff for a file-count summary:
```bash
git diff --stat
```

**Verification checklist:**
- [ ] All user-facing strings updated (UI, tray, notifications, dialogs)
- [ ] i18n locale files match (both locales updated together)
- [ ] Build/artifact names updated (no file named `OldName-*.zip|dmg`)
- [ ] Installer shortcuts and display names updated
- [ ] Documentation references updated
- [ ] Tests that assert on the old display name are updated
- [ ] `productName` in package.json matches `productName` in electron-builder
- [ ] Internal code identifiers NOT touched

## Pitfalls

- **`patch()` + template literals with `${}` — USE WRITE_FILE INSTEAD.** The
  `patch` tool can mangle old_string matching when the replacement contains
  backtick template literals with interpolation (`\`...${var}...\``). The
  diff output may insert literal `\\n` characters instead of real line breaks.
  For any replacement involving template literals or multi-line blocks,
  prefer `read_file` + `write_file` (read the whole file, make the changes in
  Python/your head, write it back cleanly) instead of using `patch()`.

- **Don't rename internal identifiers.** Type names, function names, file
  names, import paths, and directory names are code contracts. Renaming them
  cascades into dozens of broken imports and type errors. Only change them
  when the user explicitly says "change ALL references" (and warn them first).

- **i18n keys are NOT display strings.** Only change the *values*, not the
  JSON keys. The key names are code identifiers used by the i18n library.

- **Tests assert on display names.** After changing a `displayName` or
  `title`, search for test files that assert on the old value and update them.

- **GitHub URLs and package names.** GitHub repo slugs
  (`github.com/OldOrg/OldName`) and npm package names
  (`@scope/old-name`) are outward-facing URLs. Only change them if the user
  specifically asks — they affect git remotes, npm publish targets, and
  downstream CI.

- **Build script `PRODUCT_NAME` constants.** Don't miss these — they control
  artifact naming in CI release pipelines. Check `scripts/` and CI config
  files (.github/workflows/*.yml, .gitlab-ci.yml).

- **`release/` directory.** Historical release notes contain the old name.
  Update only if the user asks. They're historical artifacts, not active code.

**macOS app bundle name.** After changing `productName` in
electron-builder, the macOS `.app` bundle name changes too. The
`zip-mac-app.cjs` script's `appName` and `zipPath` must match exactly or
auto-update will break.

### Agent/CLI Framework (Hermes-style) File Types

When rebranding an agent framework (Hermes, Claude Code-style CLI), the
file categories differ from Electron/desktop apps:

| File Type | What to Change | Example |
|-----------|---------------|---------|
| **Runtime persona** | Agent's self-introduction | `~/.<home>/SOUL.md` |
| **Personality config** | Personality strings referencing old brand | `config.yaml` noir/pirate roles |
| **CLI banner** | Startup title, status bar, agent name | `*_cli/banner.py` |
| **CLI module docstrings** | File-level `"""Hermes Agent ..."""` | `*_cli/*.py` module headers |
| **CLI entry points** | `argparse` description/help strings | `main.py`, `commands.py` |
| **CLI status/version** | `print("Hermes Agent vX.X")` strings | `status.py`, `banner.py` |
| **Server titles** | FastAPI/Gateway service name | `web_server.py`, `gateway.py` |
| **Worker tools** | Email Subject, OAuth client_name | `tools/send_message_tool.py`, `tools/mcp_oauth.py` |
| **Web UI** | i18n locale files, CSS header, HTML `<title>` | `web/src/i18n/en.ts`, `web/src/index.css`, `web_dist/index.html` |
| **Skin engine defaults** | Built-in skin templates with old brand | `skin_engine.py` (5 default skins) |
| **Shell completion** | Completion script header comment | `completion.py` bash/zsh/fish |
| **Installer/Uninstaller** | Wizard header, prompt text | `setup.py`, `uninstall.py` |

**Strategy for agent frameworks:**

1. **Runtime first** — Change `~/.<home>/SOUL.md` and `config.yaml` first.
   These take effect immediately and don't need a rebuild.
2. **Source code** — Then change Python, TypeScript, HTML, CSS source files.
   These are git-tracked and need a rebuild/redeploy.
3. **Built-in API key** (optional) — If the fork ships with a free API key,
   add a new `custom_providers` entry with the key and set it as the default
   `model.provider`. This makes the agent usable immediately after install.
4. **Leave functional URLs alone** — GitHub repo slugs, docs sites, API
   endpoints (`nousresearch.com`, `portal.nousresearch.com`) are functional
   URLs. Only rename them when you have 7ColorAI-equivalent replacements.

**When `patch()` fails on escape-drift in Python:**

Python source files often contain strings with escaped quotes inside double-quoted
strings (e.g. `\"│ Hermes Agent ... │\"`). The `patch()` tool's fuzzy matching
may reject these with "Escape-drift detected". Fall back to `sed` for such cases:

```bash
sed -i '' 's/Hermes Agent Setup/DeepSeek Agent Setup/' hermes_cli/setup.py
```

Multi-match patterns work well with `sed -i` and per-file verification:

```bash
# Apply and verify
grep -n 'DeepSeek Agent' hermes_cli/setup.py
```

## Verification Commands

```bash
# Count remaining references
cd /path/to/project
grep -rn '"OldName"' --include='*.ts' --include='*.tsx' --include='*.json' \
  --include='*.md' --include='*.js' --include='*.cjs' --include='*.mjs' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist \
  --exclude-dir=release | wc -l

# Check git diff summary
git diff --stat

# Spot-check a user-facing string
grep -rn 'NewName' src/renderer/src/locales/ --include='*.json'
```
