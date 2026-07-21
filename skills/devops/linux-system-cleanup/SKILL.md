---
name: linux-system-cleanup
description: >
  Linux disk space diagnostics and safe cleanup. When user says "disk full",
  "space不足", "clean up", "清理空间", or reports low disk space. Covers
  diagnostic workflow, safe cleanup targets, and what to avoid.
tags: [linux, disk, cleanup, maintenance, devops]
---

# Linux System Cleanup

Safe, methodical disk space recovery for Linux systems.

## Diagnostic Workflow

1. **Check overall usage**: `df -h /` — get total, used, free, percentage
2. **Identify top consumers**: `sudo du -sh /var /home /tmp /root /opt 2>/dev/null | sort -hr`
3. **Drill into largest directories**: `sudo du -sh /var/log /var/lib /var/cache 2>/dev/null | sort -hr`
4. **Check user home**: `du -sh ~/.* ~/.local ~/.cache ~/Documents ~/Code 2>/dev/null | sort -hr | head -15`
5. **Check /tmp**: `du -sh /tmp/* 2>/dev/null | sort -hr | head -10`

## Safe Cleanup Targets (Harmless)

### 1. Journal Logs (often largest)
```bash
# Keep last 3 days (typical savings: 2-5G)
sudo journalctl --vacuum-time=3d

# Or limit by size
sudo journalctl --vacuum-size=500M
```

### 2. /tmp Files
```bash
# Remove old archives, caches, temp files
rm -f /tmp/*.tar.gz /tmp/*.html /tmp/node-compile-cache
```

### 3. Package Manager Caches
```bash
# apt (Debian/Ubuntu)
sudo apt clean
sudo apt autoremove -y

# npm
npm cache clean --force

# pip
pip cache purge

# bun
rm -rf ~/.bun/install/cache
```

### 4. Old Log Files
```bash
# Remove rotated syslog files (keep current)
sudo rm -f /var/log/syslog.*.gz /var/log/syslog.[0-9]

# Clean application logs (todesk, etc.)
sudo rm -f /var/log/todesk/*.log

# Clean sysstat history
sudo rm -f /var/log/sysstat/sa*
```

### 5. Snap Old Revisions
```bash
# List disabled snaps
sudo snap list --all | grep disabled

# Remove old revisions (replace REV with actual version)
sudo snap remove --purge snap-name
```

### 6. Docker (if running)
```bash
# Remove unused images, containers, networks
docker system prune -f

# More aggressive (including unused volumes)
docker system prune -a -f
```

## What NOT to Clean

- **/home**: User data, code repos, documents — require manual review
- **/var/lib/snapd**: System applications — don't remove unless you know what you're doing
- **Active configs**: .bashrc, .profile, application configs
- **Git repos**: Use `git gc` instead of deleting
- **Running services**: Check with `systemctl status` before stopping

## Verification

After cleanup, verify results:
```bash
df -h /
sudo du -sh /var/log /var/lib /tmp
```

## Pitfalls

- `journalctl --vacuum-time` may show "freed 0B" if logs are already within timeframe
- `apt autoremove` may not free space if no orphaned packages
- Docker requires sudo if user not in docker group
- Some snap commands fail silently if snapd is not running

## When to Escalate

If cleanup doesn't free enough space:
1. Check for large files: `sudo find / -type f -size +100M 2>/dev/null`
2. Check for deleted but open files: `sudo lsof +L1`
3. Consider moving ~/Code or ~/Documents to external storage
4. Review Docker images: `docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}"`
