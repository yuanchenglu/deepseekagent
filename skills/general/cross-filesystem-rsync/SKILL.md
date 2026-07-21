---
name: cross-filesystem-rsync
description: Optimize rsync for cross-filesystem copies (ext4 → exFAT/NTFS/FAT32). Diagnose and fix catastrophic slowdown caused by Unix permission attempts on non-Unix destinations.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [rsync, filesystem, exFAT, NTFS, performance, migration, USB]
---

# Cross-Filesystem rsync (ext4 → exFAT / NTFS / FAT32)

## Trigger
User asks to copy/migrate a large directory tree between two different filesystem types — e.g., ext4 source → exFAT/NTFS/FAT32 destination, local USB drive copies, or when rsync on a local copy is inexplicably slow.

## P0: Check filesystem types FIRST

Before any copy command, check BOTH source and destination filesystem types:

```bash
df -T /source/path /dest/path
```

If destination is **exFAT, NTFS, or FAT32**: these do NOT support Unix permissions, ownership, or symlinks. rsync `-a` (which implies `-p -o -g`) will attempt to set these on every file, fail expensively, and slow the copy by 100–1000×.

## P1: Fast rsync recipe (non-Unix destination)

```bash
# The "-a" killer — avoid it on exFAT/NTFS/FAT32
rsync -rtP --partial \
  --no-perms --no-owner --no-group \
  --exclude='*.iso' --exclude='*.img' \
  /source/ /dest/
```

| Flag | Why |
|------|-----|
| `-r` | recursive (keep, needed) |
| `-t` | preserve timestamps (keep, exFAT supports) |
| `-P` | `--partial --progress` (resume + progress) |
| `--no-perms` | skip chmod (useless on exFAT, saves massive time) |
| `--no-owner` | skip chown (useless) |
| `--no-group` | skip chgrp (useless) |
| `--exclude` | skip large ISOs/images (handle separately with `cp`) |

## P2: Large single files → use `cp`, not rsync

rsync does block checksums even for local copies. For ISO/image files > 500 MB, `cp` uses `sendfile()` syscall (zero-copy) and is 100–1000× faster:

```bash
# Copy ISO separately — cp is ~168 MB/s vs rsync ~150 KB/s on same hardware
cp /source/ISO/ubuntu.iso /dest/ISO/
# Then verify
md5sum /source/ISO/ubuntu.iso /dest/ISO/ubuntu.iso
```

Then run rsync with `--exclude` for those files to handle the rest.

## P3: Diagnose slow rsync

If rsync is still slow after fixing flags:

```bash
# Check USB queue depth (RQ-SIZE=2 kills IOPS on many small files)
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,RM,ROTA,TRAN,RQ-SIZE

# Test raw read speed of a single large file
dd if=/source/large_file of=/dev/null bs=1M count=200 status=progress

# Check load and I/O wait
uptime && iostat -x 1 2
```

Key insight: **rsync spawns 3 processes for local copies** (sender + receiver + generator). This is normal architecture, NOT 3 independent rsyncs. Do NOT kill the children — they're part of the same operation.

## P4: Tiny-File Bottleneck (Beyond Permissions)

Even with correct flags (`--no-perms --no-owner --no-group`), rsync to exFAT can still be unusably slow when the source contains **hundreds of thousands of tiny files** (node_modules, runtime includes, app caches). This is an exFAT cluster-allocation bottleneck, not a permission-attempt bottleneck.

**Diagnosis**: If rsync is slow but you don't see permission-denied errors in the output:
```bash
# Count tiny files likely to bottleneck
find /source -type f -size -4k | wc -l
find /source -type f -size -4k -path '*/node_modules/*' | wc -l
```
If >10% of total files are under 4KB, exFAT's large cluster size (128KB-256KB) will dominate transfer time.

**Remediation**: Exclude entire categories of tiny files rather than waiting for rsync to grind through them:

| Category | Exclusion pattern | Typical count |
|----------|-------------------|---------------|
| npm dependencies | `--exclude='**/node_modules/'` | 50K-500K files |
| Python stdlib (other OS) | `--exclude='**/python-win-x64/'` | 5K-20K files |
| App caches | `--exclude='**/AppData/'` | 1K-10K files |
| Electron caches | `--exclude='**/DawnCache/' --exclude='**/GPUCache/'` | 1K-5K files |

Apply progressively: start with none, add the largest category first (node_modules), re-evaluate speed, add more if still slow.

**Why this works**: Each tiny file costs a full cluster allocation on exFAT (~128KB I/O transaction for a 500B file). Removing 100K tiny files eliminates ~12.8GB of wasted I/O, collapsing the transfer from hours to minutes.

## P5: Post-copy verification

```bash
# File count sanity check
echo "Source: $(find /source -type f | wc -l)"
echo "Dest:   $(find /dest -type f | wc -l)"

# Directory structure alignment
ls /source/ && echo "---" && ssh user@remote "ls /dest/"

# For critical large files, MD5 verify
md5sum /source/bigfile /dest/bigfile
```

## P6: Selective file transfer — exclude expanded dirs, keep archives

When you want to skip large extracted/generated directories (node_modules, build/, 3产物/) but still transfer the compressed source archives (.zip, .tar.gz) for later extraction on the destination:

### Two-pass include/exclude pattern

```bash
# PASS 1: Copy everything except the large directory(ies)
rsync -avh --progress \
  --exclude='BIG_DIR_NAME/' \
  /source/ \
  user@remote:/dest/

# PASS 2: Transfer only compressed archives from those dirs
rsync -avhm --progress \
  --include='*/' \
  --include='*.zip' \
  --include='*.tar.gz' \
  --include='*.tgz' \
  --include='*.7z' \
  --include='*.rar' \
  --exclude='*' \
  /source/ \
  user@remote:/dest/
```

| Flag / Pattern | Purpose |
|----------------|---------|
| `--exclude='DIR/'` | Exclude the entire directory tree (PASS 1) |
| `--include='*/'` | Include all directories for traversal (PASS 2) |
| `--include='*.zip'` | Include only archive files |
| `--exclude='*'` | Exclude everything else |
| `-m` (prune-empty-dirs) | Remove empty expanded directories that had no files matched (PASS 2) |

### Why two passes

- **PASS 1** handles the bulk (config, docs, scripts, rubrics — the non-generated content) with no filter overhead.
- **PASS 2** targets only archives within the excluded directory. rsync won't re-copy files that already exist from PASS 1; it just adds the new archive files.
- This avoids the massive I/O cost of traversing expanded directories looking for zip files (if done as a single complex include/exclude rule).

### Application to common patterns

| Scenario | BIG_DIR_NAME | Archive pattern |
|----------|-------------|-----------------|
| Node project | `node_modules/` | `*.tgz` (npm cache) |
| Build artifacts | `dist/`, `build/`, `target/` | `*.tar.gz`, `*.zip` |
| ML datasets | `data/raw/`, `datasets/` | `*.tar.gz`, `*.zst` |
| Extraction folders | `3产物/` (方舟众测 results) | `*.zip` |
| Container layers | `docker/`, `oci-blobs/` | `*.tar.gz` |

### Verification after selective transfer

```bash
# Compare archive counts on source vs dest
echo "Source archives: $(find /source -name '*.zip' -o -name '*.tar.gz' | wc -l)"
ssh user@remote "echo 'Dest archives:'; find /dest -name '*.zip' -o -name '*.tar.gz' | wc -l"

# Check dest is REAL files, not empty dirs
du -sh /dest/
ls /dest/

# Clean up any empty placeholder dirs (created by --include='*/' on dirs with no matched files)
ssh user@remote "find /dest -type d -empty -delete"
```

## P7: Post-transfer source cleanup

After a successful selective transfer, reclaim space on the source by deleting the large expanded directories that were intentionally skipped during copy.

### The pattern

```bash
# Delete expanded directories inside a target path, keeping archives intact
find /source/ -path '*/TARGET_DIR/*' -type d ! -name 'TARGET_DIR' -exec rm -rf {} \;
```

| Part | Purpose |
|------|---------|
| `-path '*/TARGET_DIR/*'` | Scope deletion to only files inside the excluded directory |
| `-type d ! -name 'TARGET_DIR'` | Match subdirectories only, not TARGET_DIR itself |
| `-exec rm -rf {} \;` | Recursively delete each matched directory |

### Handling timeout on large directories

Expanded directories 10s of GB cause `find -exec rm -rf` to timeout in foreground mode. Use background process with completion notification:

```python
# Wrapper form
terminal(
  command="find /source/ -path '*/TARGET_DIR/*' -type d ! -name 'TARGET_DIR' -exec rm -rf {} \\;",
  background=true,
  notify_on_complete=true
)
```

After notification, verify:

```bash
# Confirm no expanded dirs remain
find /source/ -path '*/TARGET_DIR/*' -type d ! -name 'TARGET_DIR' | wc -l
# -> 0

# Size after cleanup
du -sh /source/
# -> Should approximate destination size (fs overhead aside)
```

### Verification: source ↔ destination alignment

```bash
# Structure matches
ls /source/ && ssh user@remote "ls /dest/"

# Archive count matches (not accidentally deleted)
echo "Source: $(find /source/ -name '*.zip' | wc -l)"
ssh user@remote "echo 'Dest:'; find /dest/ -name '*.zip' | wc -l"
```

### Real-world delta

Copy `fangzhouzhongce/` from MacBook (APFS) to AIPC (NTFS), then delete expanded `3产物/`:

| Stage | Size | Expanded dirs | Archives |
|-------|------|---------------|----------|
| Before | 88G | ~210 dirs (~47G) | 334 .zip files |
| After transfer (AIPC) | 41G | 0 | 334 .zip files |
| After source cleanup (Mac) | 39G | 0 | 334 .zip files |

The ~2G difference between source (APFS) and destination (NTFS) is filesystem overhead, not missing data.

## Pitfalls

1. **DO NOT use `-a` on exFAT/NTFS/FAT32 destinations** — this is the #1 cause of 1000× slowdown. Each file: rsync opens fd → fchmod → fails (EOPNOTSUPP) → logs → next. On 180K+ files this adds hours.

2. **DO NOT `find` or `du` on exFAT during active rsync** — exFAT directory traversal is slow and competes with rsync for USB I/O. Check counts before or after, not during.

3. **Symlinks silently skipped on exFAT** — `rsync` skips symlinks with "skipping non-regular file". This is expected. If symlinks matter, consider archiving with `tar` to preserve them, then extracting on a Unix-native filesystem later.

4. **`killall rsync` vs `killall -9 rsync`** — SIGTERM gives rsync a chance to flush partial files. SIGKILL (`-9`) may leave corrupted `.partial` files that the next run can't resume from. Prefer SIGTERM first, wait 5s, then SIGKILL only if stuck.

## Diagnostics reference

See `references/session-data.md` for the real session numbers (timings, RQ-SIZE, speed before/after, device topology).
