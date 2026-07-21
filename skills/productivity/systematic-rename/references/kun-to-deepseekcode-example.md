# Reference: Kun → DeepSeekCode (Electron + React + TypeScript)

**Session date:** 2026-06-27
**Project type:** Electron + React + TypeScript desktop app
**Scope:** 29 files changed, +176/−182 lines

## Rename Targets

| From | To |
|------|----|
| Product name | Kun → DeepSeekCode |
| Company | (none) → 7ColorAI |

## Files Changed

### Core config (5 files)
- `package.json`: productName, description + author field
- `electron-builder.config.cjs`: productName, artifactName, shortcutName,
  uninstallDisplayName, NSMicrophoneUsageDescription, copyright
- `src/main/app-identity.ts`: APP_PRODUCT_NAME constant

### UI/i18n (6 files)
- `locales/zh/common.json`, `locales/en/common.json`: appName, clawCoreTitle,
  runtimeStatusRestarting, runtimeStatusCrashed, runtimeStatusFailed
- `src/renderer/src/agent/kun-runtime.ts`: displayName
- `src/renderer/src/plan/plan-prompts.ts`: DRAFT_PLAN_INTRO, REFINE_PLAN_INTRO
- `src/main/gui-updater.ts`: update dialog title/message
- `src/main/index.ts`: tray tooltip, notification title fallback

### Build/packaging (4 files)
- `scripts/zip-mac-app.cjs`: appName, zipPath
- `scripts/generate-mac-latest.cjs`: artifact filename regex
- `scripts/compute-ci-release-version.cjs`: PRODUCT_NAME
- `scripts/publish-r2.mjs`: PRODUCT_NAME

### Runtime display strings (3 files)
- `src/main/claw-runtime.ts`: IM welcome fallback name
- `src/main/services/write-export-service.ts`: DOCX creator metadata
- `src/renderer/src/agent/kun-runtime.test.ts`: test assertion

### Documentation (12 files)
- `README.md`, `README.en.md`: full rewrite
- `AGENTS.md`: 6 product-name references
- `DESIGN.md`, `DESIGN.zh-CN.md`: product_name, tagline
- `kun/README.md`, `kun/README.zh-CN.md`: product title
- `CODE_OF_CONDUCT.md`, `CODE_OF_CONDUCT.zh-CN.md`: community name
- `SECURITY.md`, `SECURITY.zh-CN.md`: project name
- `CLA.md`: 4 legal-document references

## Pitfalls Encountered

### 1. patch() + Template Literals
When using `patch(old_string=...)` where the replacement text contains
backtick template literals with `${interpolation}`, the tool can produce
mangled diffs with literal `\\n` characters. Fix: use `read_file` + `write_file`
instead for any block containing template literals.

Example from `src/main/gui-updater.ts`:
```
title: isZh ? 'Kun 已更新' : 'Kun updated',
message: isZh ? `已更新到 Kun ${currentVersion}` : ...
```
The `${currentVersion}` interpolation caused the patch to produce
`\\n    message:` on one line. Needed a follow-up patch to clean up.

### 2. README duplicated image tag
First `patch()` on `README.md` left a duplicated `<img>` tag:
```
<img src="...kun.png" alt="Kun 图标">
<img src="...kun.png" alt="DeepSeekCode 图标">
```
Had to rewrite the whole file. Lesson: for large multi-line changes, skip
`patch()` and use `write_file` with a complete rewrite.

### 3. Test assertion mismatch
After changing `displayName = 'DeepSeekCode'` in the runtime provider,
the corresponding test (`kun-runtime.test.ts`) asserted `toBe('Kun')`
and needed updating. Always grep for test files after renaming a
display string.

### 4. i18n value vs key
Only the JSON *values* were changed, not the keys. The keys
(`appName`, `clawCoreTitle`, `runtimeStatusRestarting`) are code
identifiers and must stay unchanged.

## What Was NOT Changed

- Internal code types: `KunConfig`, `KunServeHandle`, `KunRuntimeProvider`,
  `KunErrorBody`, `KunCapabilitiesConfig`
- Import paths: `@shared/kun-gui-api`, `@shared/kun-endpoints`
- Directory names: `kun/`, `src/asset/img/kun.png`
- CLI command: `kun serve`
- Git repo URLs: `github.com/KunAgent/Kun`
- docs/ directory: internal runtime architecture docs
- release/ directory: historical release notes
