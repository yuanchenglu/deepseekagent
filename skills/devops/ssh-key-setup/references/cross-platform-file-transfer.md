# Cross-Platform File Transfer (macOS ↔ Windows via SSH)

Transfer large project directories between macOS and Windows over SSH after key-based auth is set up.

## Transfer Strategy by Size

| Size | Method | Resume | Notes |
|------|--------|--------|-------|
| < 100 MB | `scp -r` | No | Fast enough; restart is cheap |
| 100 MB – 5 GB | **tar + SCP** (below) | Partial | Compress first, transfer one file, then extract |
| > 5 GB | rsync (if available) or split tar+scp | Yes | See cross-filesystem-rsync skill |

## Preferred Method: tar + SCP + background

This avoids `scp -r`'s per-file overhead and handles mixed OS paths cleanly.

### Step 1: Compress on source (Mac/Linux)

```bash
# Creates a single compressed archive
tar czf /tmp/project.tar.gz -C /path/to/parent project-folder
```

Check size:
```bash
ls -lh /tmp/project.tar.gz
```

### Step 2: Transfer in background (free up your agent)

```bash
# Start SCP in background terminal
scp -o StrictHostKeyChecking=accept-new \
  /tmp/project.tar.gz \
  user@windows-host:"C:/Users/user/Desktop/"
```

Use `notify_on_complete=true` in the terminal tool so you're notified when done.

### Step 3: Extract on Windows

Windows 10+ includes `tar.exe`:

```cmd
cd /d C:\Users\user\Desktop\
tar -xzf project.tar.gz
```

### Step 4: Clean up

```bash
rm /tmp/project.tar.gz                     # source
ssh user@windows-host 'del project.tar.gz'  # dest
```

## Alternative: rsync (when Windows has rsync)

If `rsync` is available on both sides (e.g., Windows Git Bash, WSL, or Cygwin):

```bash
# Push from Mac → Windows
rsync -rtP --no-perms --no-owner --no-group \
  --partial --append \
  -e "ssh -o StrictHostKeyChecking=accept-new" \
  /path/to/source/ \
  user@windows-host:"C:/Users/user/Desktop/dest/"
```

Key flags:
- `-rtP`: recursive, preserve timestamps, progress + partial
- `--no-perms --no-owner --no-group`: skip Unix permissions (not supported on NTFS)
- `--partial --append`: resume support

**Pitfall:** rsync must be installed on BOTH sides. Windows native `scp` is simpler if rsync isn't available.

## Verification

```bash
# File count comparison
echo "Source: $(find /path/to/source -type f | wc -l)"
ssh user@windows-host \
  'cmd /c "dir C:\Users\user\Desktop\dest /S | findstr \"File(s)\""'

# Or use PowerShell for size
ssh user@windows-host \
  'powershell "Get-ChildItem C:\Users\user\Desktop\dest -Recurse | Measure-Object -Property Length -Sum | Select Count,@{N=\"MB\";E={[math]::Round($_.Sum/1MB,1)}}"'
```

## Pitfalls

1. **`scp -r` times out on large (>500MB) directories** — tar+scp transfers a single file, which is more reliable and easier to resume.
2. **Environment variable expansion** — `%USERPROFILE%` does NOT work in SCP paths. Use the full path with forward slashes: `C:/Users/user/Desktop/`.
3. **Windows path quoting** — SCP on Windows accepts forward slashes (`C:/Users/...`). Backslashes cause errors.
4. **GBK console encoding** — Windows Chinese locale can't print non-ASCII characters. Use simple ASCII markers in test output or set `PYTHONIOENCODING=utf-8`.
5. **Windows cmd `tail`/`grep`** — These Unix commands do NOT exist on Windows. Use `findstr` instead of `grep`, or pipe to `more` instead of `tail`.
