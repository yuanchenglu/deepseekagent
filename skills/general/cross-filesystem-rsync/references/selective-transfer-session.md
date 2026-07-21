# Session: Selective transfer — 方舟众测 to AIPC over Tailscale

## Context

Transfer the `fangzhouzhongce/` directory from macOS (MacBook) to AIPC (Deepin Linux, Tailscale 100.89.88.88). Destination: 1.2T NTFS partition at `/media/bluth/Doc/Code/`.

## Requirements from user

1. **Don't copy extracted (产物) folders** — `3产物/` contains both compressed `.zip` files AND extracted directories of the same name. The extracted dirs are huge (~60G); skip them.
2. **Only copy compressed archives** — the `.zip` files inside `3产物/` should be transferred so AIPC can extract them later when needed.
3. **Everything else** (0官方任务书, 1项目, 2任务清单, 4打分, root-level files) — copy normally.

## Source structure

```
~/Code/fangzhouzhongce/
├── rules.md, 打分提示词.txt, etc.
├── other/
├── 第24期/ ... 第33期_yanzi/  (19 period dirs)
│   ├── 0官方任务书/   # task briefs (small, .md)
│   ├── 1项目/         # project code
│   ├── 2任务清单/      # task checklists
│   ├── 3产物/          # artifacts — BOTH .zip files AND extracted dirs (~88G total for all periods)
│   ├── 4打分/          # scoring
│   └── 5复核打分/      # re-scoring (some periods)
```

## Two-pass rsync commands

### Pass 1: Everything except 3产物/

```bash
rsync -avh --progress \
  --exclude='3产物/' \
  ~/Code/fangzhouzhongce/ \
  bluth@100.89.88.88:/media/bluth/Doc/Code/fangzhouzhongce/
```

This copied ~15.9G at ~53MB/s.

### Pass 2: Only .zip archives from 3产物/

```bash
rsync -avhm --progress \
  --include='*/' \
  --include='*.zip' \
  --include='*.tar.gz' \
  --include='*.tgz' \
  --include='*.7z' \
  --include='*.rar' \
  --exclude='*' \
  ~/Code/fangzhouzhongce/ \
  bluth@100.89.88.88:/media/bluth/Doc/Code/fangzhouzhongce/
```

This transferred ~26.9G of zip files at ~63MB/s. The `-m` flag pruned empty expanded directories (which had no files matched).

### Final verification

```bash
# Check size on destination
ssh user@host "du -sh /dest"
# -> 41G (vs 88G source — saved 47G)

# Check archive count
ssh user@host "find /dest -name '*.zip' | wc -l"
# -> 334 zip files

# Align directory structure
ls /source && ssh user@host "ls /dest"

# Clean empty placeholder dirs
ssh user@host "find /dest -type d -empty -delete"
```

### Outcome

| Metric | Value |
|--------|-------|
| Source total | 88G |
| Destination total | 41G (saved 47G by skipping expanded dirs) |
| Archives transferred | 334 zip files |
| Speed (Pass 1) | ~53 MB/s |
| Speed (Pass 2) | ~63 MB/s |
| Connection | Tailscale (100.x.x.x, ~300-1400ms ping) |

## Phase 2: Source-side cleanup (removing expanded dirs)

After confirming the transfer was complete and correct, the user asked to delete all expanded directories within `3产物/` on the Mac source, keeping only the .zip files.

### Delete command

```bash
find ~/Code/fangzhouzhongce/ -path '*/3产物/*' -type d ! -name '3产物' -exec rm -rf {} \;
```

### Timeout handling

The initial `find -exec rm -rf` timed out in foreground mode (60s+). Expanded directories averaged ~200-500MB each, and the total was ~47G. Used background process with notification:

```python
terminal(
  command="find ~/Code/fangzhouzhongce/ -path '*/3产物/*' -type d ! -name '3产物' -exec rm -rf {} \\;",
  background=true,
  notify_on_complete=true
)
```

Some directories were already partially deleted by the initial run (exit 1 with "No such file or directory" warnings on directories that had already been processed). A second run cleaned the rest.

### Verification

```bash
# Confirm zero expanded dirs remain
left=$(find /source -path '*/3产物/*' -type d ! -name '3产物' | wc -l)
# -> 0

# Size dropped from 88G to 39G (49G saved)
du -sh /source/
# -> 39G
```

### Post-cleanup structure

All 334 .zip files intact. Non-3产物 content (任务书/项目/清单/打分) preserved. Only expanded directories removed.

| Stage | Size | Changes |
|-------|------|---------|
| Before any transfer | 88G | Full source tree with expanded dirs |
| After copy to AIPC | 41G (dest) | 47G saved by skipping expanded content |
| After source cleanup | 39G (source) | 49G saved total |

## Key rsync include/exclude insight

The `--include='*/'` before `--exclude='*'` is critical: rsync first includes ALL directories (so it traverses into them), then includes only archive-type files, then excludes everything else. Without `--include='*/'`, rsync wouldn't descend into subdirectories at all and would miss the zip files nested inside them.
