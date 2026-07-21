---
name: linux-system-diagnostics
description: >
  Linux system hardware diagnostics and power monitoring. Trigger when user
  asks about power consumption, hardware health, system services, or wants
  to understand a running daemon. Covers RAPL power measurement, GPU power
  estimation, PSU efficiency math, and service discovery.
tags: [linux, power, diagnostics, hardware, monitoring, devops]
---

# Linux System Diagnostics

Hardware inventory, power measurement, and service discovery on Linux systems.

## 1. Remote Access

- Tailscale quick check: `tailscale status | grep <hostname>`
- SSH via MagicDNS: `ssh <tailscale-hostname> 'command'`

## 2. Service Discovery — ALWAYS check existing first

Before installing any tool, search for running services:
```bash
systemctl list-units --type=service --state=running | grep -i <keyword>
systemctl cat <service-name>
```

## 3. Hardware Inventory

```bash
grep 'model name' /proc/cpuinfo | head -1 && nproc
free -h
nvidia-smi --query-gpu=name,memory.total,power.limit,power.draw --format=csv
lsblk -d -o name,size,type,rota
```

## 4. Power Measurement

See `references/power-consumption-analysis.md` for full methodology.

Quick summary:
- **Intel RAPL**: `/sys/class/powercap/intel-rapl:*/energy_uj` — root-only (mode 400)
- **NVIDIA**: `nvidia-smi` — low-end cards (GT 1030) lack power sensors → returns N/A
- **GPU estimate**: `power_limit × 0.4` idle baseline + utilization-scaled delta
- **DC→AC**: RAPL/NVML reads DC-side. Multiply by ~1.2 (80+ Bronze) to ~1.25 (80+ White) for wall power
- **Unmonitored components**: storage (HDD ~6W each, SSD ~2W), motherboard+fans ~15-20W, PSU losses

Common Intel RAPL domains:
| Domain | Path | What it covers |
|--------|------|----------------|
| package-0 | `intel-rapl:0` | CPU cores + ring/uncore + iGPU(if any) |
| core | `intel-rapl:0:0` | CPU cores only |
| dram | `intel-rapl:0:1` | DRAM DIMMs on the package |

## 5. Storage I/O Performance Diagnosis

When a local disk copy (rsync/cp/tar) seems abnormally slow, use this 3-step diagnostic:

### Step 1: Check queue depth (the #1 bottleneck for USB flash)

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,RM,ROTA,TRAN,RQ-SIZE
```

Key column: **RQ-SIZE** — the I/O request queue depth.
- **RQ-SIZE=2**: typical USB flash drives. Kills small-file random I/O (IOPS throttled).
- **RQ-SIZE=64**: SATA SSD/HDD. Much better for mixed workloads.
- **RQ-SIZE=1023**: NVMe. No contention.

### Step 2: Isolate sequential vs random speed

```bash
# Sequential read (bypasses filesystem overhead)
dd if=/path/to/large_file of=/dev/null bs=1M count=300 status=progress

# If dd is fast (100+ MB/s) but rsync is slow (100s of KB/s),
# the bottleneck is random I/O / small files, not bus bandwidth.
```

### Step 3: Verify rsync isn't self-competing

```bash
pgrep -c rsync           # count
ps aux | grep rsync     # check if 3 procs = normal sender+receiver+generator
```

rsync's normal architecture spawns 3 processes (sender, receiver, generator) for local copies — NOT 3 independent competing copies. Check PPID chain to confirm.

### When to avoid rsync entirely

For **local USB → disk** copies with many small files:
- rsync's checksum + delta overhead is wasted on local copies
- Prefer `cp -a` or `tar cf - source | tar xf - -C dest` for pure local speed
- Only use rsync if you need `--partial` for interrupt-resume

See `references/storage-io-diagnosis.md` for the full worked example.

## 6. GPU Power Reality

When user asks if GPU draws power without display connected:
- **P8 idle ≠ zero power.** Core still powered, VRAM needs refresh, PCIe link active.
- Desktop NVIDIA cards do NOT enter D3cold while Xorg/processes hold file handles.
- Check with: `nvidia-smi pmon` (process list), `/sys/bus/pci/devices/*/power/runtime_status`
- GT 1030 and similar low-end cards: no `power.draw` sensor. Only `power.limit`.
- Only way to zero GPU power: physical removal or full D3cold (laptop Optimus only).

## Pitfalls

- **Do NOT install `powertop` / `powerstat` without checking existing services first.** The user may already have a custom daemon.
- RAPL `energy_uj` is root-only. If you can't sudo, look for an existing logger service.
- Desktop PSU efficiency is NOT measured by any onboard sensor. All sensor readings are DC-side.
- `dmidecode` requires root. Fall back to `/proc/meminfo` and `lshw` for memory config.
- GT 1030 `power.draw` returns N/A — this is not a driver bug, the hardware has no sensor.
