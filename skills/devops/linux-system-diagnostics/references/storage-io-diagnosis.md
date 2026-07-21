# Storage I/O Diagnosis — USB Flash Drive Case Study

## The Problem

User complained rsync was copying at **~300 KB/s** on a local USB-to-SATA copy. Machine became unresponsive to SSH on its local IP. The copy was 19 GB, 184K+ files (code repos with venv/node_modules).

## Diagnostic Trace

### 1. USB bus speed check — NOT the bottleneck

```bash
$ lsusb -v | grep bcdUSB
Bus 002 Device 003: ID 3543:4022 COLORFUL RVA01 128GB
  bcdUSB               3.20          # USB 3.2 device on USB 3.1 bus

$ dd if=/media/usb/large.iso of=/dev/null bs=1M count=300 status=progress
314572800 bytes (315 MB, 300 MiB) copied, 1.87 s, 168 MB/s
```

**Sequential read = 168 MB/s** — the USB bus is fast. The problem is elsewhere.

### 2. Queue depth — THIS is the bottleneck

```bash
$ lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,RM,ROTA,TRAN,RQ-SIZE
NAME   SIZE  TYPE MOUNTPOINT           RM ROTA TRAN  RQ-SIZE
sdc    117G  disk                       1    1 usb         2   ← USB flash!
sdb    3.6T  disk                       0    1 sata       64   ← SATA SSD
```

**RQ-SIZE=2** on the USB flash drive means only 2 I/O requests can be queued at once.

Impact:
- Large sequential files: 168 MB/s (no queuing needed)
- 184K small files: each requires seek + read + write to target disk
- With only 2 queue slots, the drive sits idle waiting for each op to complete
- Combined with rsync's checksum computation per file → 300-500 KB/s effective throughput

### 3. rsync process count — normal, not competing

```bash
$ pgrep -c rsync
3

$ ps aux | grep rsync
288283  rsync -avP --partial /source/ /dest/     # PPID=1 (main)
288284  rsync -avP --partial /source/ /dest/     # PPID=288283 (child)
288285  rsync -avP --partial /source/ /dest/     # PPID=288284 (grandchild, state D)
```

rsync's normal **sender → receiver → generator** architecture. NOT 3 independent rsyncs competing for I/O.

### 4. Machine unresponsive on local IP but reachable via Tailscale

When the local IP (192.168.10.186) stopped responding to SSH, the Tailscale IP (100.89.88.88) still worked. The local NIC or its driver was swamped by I/O interrupts. Tailscale uses userspace networking (WireGuard in userspace), so it remained functional.

### 5. Warning: `find` while rsync is running

```bash
$ find /media/usb/ -type f | wc -l   # DO NOT DO THIS
Command timed out after 120s
```

Running `find` on the USB drive while rsync is actively reading it can:
- Double the random I/O pressure (find does stat() on every file)
- Hang the machine (SSH timeout)
- Give misleading results (find races with rsync's file creation)

**Better**: check rsync's own progress log (`tail -f /tmp/rsync.log`) or the destination file count only.

## Key Takeaways

| Symptom | Check | Likely Cause |
|---------|-------|-------------|
| Slow local copy | `lsblk RQ-SIZE` | USB flash = RQ-SIZE=2, kills IOPS |
| Sequential read fast, copy slow | `dd` large file | Many small files = random I/O bottleneck |
| 3 rsync processes | Check PPID chain | Normal sender/receiver/generator |
| SSH to local IP fails | Try Tailscale IP | Local NIC saturated, WG userspace still works |
| `find` hangs machine | Don't run during copy | Doubles random I/O, use rsync log instead |

## When to use cp instead of rsync

For local USB→disk copies:
- **Use `cp -a`** for one-shot copies — no checksum overhead, just raw read+write
- **Use `tar cf - src | tar xf - -C dest`** for pipeline speed (single I/O stream)
- **Use rsync** only when you need `--partial` (interrupt-resume) or `--delete` (sync)

rsync's checksum computation per file is wasted on local copies where data integrity is handled by the filesystem.
