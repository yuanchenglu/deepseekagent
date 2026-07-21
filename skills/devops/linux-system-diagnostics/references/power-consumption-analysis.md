# Power Consumption Analysis on Linux

## Measurement Stack Overview

```
┌─────────────────────────────────────────────────┐
│  Wall (AC) — what your electricity meter reads  │
│  ═══════════════════════════════════════════════ │
│  PSU efficiency loss (15-20%)                    │
│  ─────────────────────────────────────────────── │
│  DC side — what the motherboard actually draws  │
│  ┌──────────┬──────────┬──────────┬───────────┐ │
│  │ RAPL     │ NVML     │ Storage  │ Mobo+Fan  │ │
│  │ pkg+dram │ GPU est. │ HDD/SSD  │ ~15-20W   │ │
│  └──────────┴──────────┴──────────┴───────────┘ │
└─────────────────────────────────────────────────┘
```

## Intel RAPL (Running Average Power Limit)

RAPL provides hardware-level energy counters in microjoules (uJ). These are measured by the CPU's power control unit (PCU) and are accurate to within ~1-5%.

### Reading energy (requires root)

```bash
# Read cumulative energy in microjoules
cat /sys/class/powercap/intel-rapl:0/energy_uj

# Calculate instantaneous power (W):
# (energy2 - energy1) / (time2 - time1) / 1,000,000
```

### Power limits (constraints)

```bash
# PL1 — long-duration power limit (uW)
cat /sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw
# PL2 — short-duration burst limit (uW)  
cat /sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw
# Default hardware max
cat /sys/class/powercap/intel-rapl:0/constraint_0_max_power_uw
```

### Domain coverage

| Domain | File | i5-10400F actual | Notes |
|--------|------|-----------------|-------|
| package-0 | `intel-rapl:0` | ~4W idle | CPU cores + ring bus + uncore + iGPU (disabled on F) |
| core | `intel-rapl:0:0` | ~2W idle | CPU cores only |
| dram | `intel-rapl:0:1` | ~2W idle | DDR4 DIMM power |

**What RAPL does NOT cover:**
- Storage (HDD, SSD, NVMe)
- GPU (even iGPU power is separate from package in newer chips)
- Motherboard chipset, VRM losses, fans
- Network cards, USB devices
- PSU efficiency losses

## NVIDIA GPU Power

### Cards WITH power sensors

```bash
nvidia-smi --query-gpu=power.draw,power.limit --format=csv
```

Returns actual instantaneous power draw in Watts.

### Cards WITHOUT power sensors (GT 1030, GTX 1050/Ti, some 16-series)

`power.draw` returns `N/A`. Must estimate from power limit and utilization:

```python
# Powerlog script's estimation:
idle_mw = power_limit_mw * 0.40        # 40% of limit as idle baseline
gpu_mw = idle_mw + (power_limit_mw - idle_mw) * utilization_pct / 100
```

This is approximate — real power curves are nonlinear. The 40% idle fraction is a reasonable heuristic but can vary significantly.

### GPU power states (P-states)

- **P0**: Maximum performance (3D clocks)
- **P2/P5**: Intermediate 
- **P8**: Minimum idle — still draws 5-10W depending on card

GT 1030 at P8: core ~135 MHz, memory ~405 MHz, estimated 6-8W DC.

### Why GPU won't reach zero power with HDMI unplugged

1. **P8 ≠ off.** Core powered, VRAM refreshed, PCIe link active.
2. **Xorg/processes hold device open.** Check with `nvidia-smi pmon`.
3. **Desktop cards don't support D3cold.** Laptop Optimus can power off dGPU completely, but desktop NVIDIA cards stay in P8 minimum.
4. **Runtime D3** (`/sys/bus/pci/devices/*/power/control`) set to "on" means the PCIe power management won't suspend.

## Estimating Total System AC Power

### Methodology

```
AC wall power = (RAPL_total + GPU_est + storage_est + mobo_overhead) / PSU_efficiency
```

### Component estimates for typical desktop

| Component | Idle | Moderate | Load |
|-----------|------|----------|------|
| CPU package (RAPL) | 5-10W | 35-55W | 65-90W |
| DRAM (RAPL) | 2-4W | 5-10W | 10-15W |
| GT 1030 | 6-8W | 12-16W | 19-20W |
| 3.5" HDD (each) | 4-6W | 6-8W | 8-10W |
| SATA SSD | 0.5-1W | 1-2W | 2-3W |
| NVMe SSD | 1-2W | 2-4W | 4-6W |
| Mobo + fans + VRM loss | 10-15W | 15-20W | 20-25W |
| PSU efficiency | 80-87% | 82-85% | 85-90% |

### Worked example: bluth-AIPC (i5-10400F + GT 1030)

**Scenario: 70% CPU, 25GB RAM used, GPU at 2GB VRAM**

DC-side breakdown:
```
CPU package (RAPL):       60W   (70% of 65W TDP CPU, all-core mixed load)
DRAM (RAPL):              10W   (3 DIMMs, moderate-high activity)
GPU GT 1030 (estimated):  20W   (close to 19.6W power limit)
Storage (2 HDD + 2 SSD):  16W   
Motherboard + fans:       18W
─────────────────────────────────
DC total:               ~124W
```

AC estimate (80+ White PSU, ~82% at moderate load):
```
124W / 0.82 ≈ 151W  (wall power)
～0.15 kWh per hour
～¥0.08 per hour (@ ¥0.5/kWh)
```

**Note:** The user's powerlog script would only report ~85W (RAPL ~70W + GPU est. ~15W). The gap (~39W DC + ~27W PSU loss) is all unmonitored — storage, motherboard, fans, PSU inefficiency. Multiply powerlog's numbers by **~1.7-1.8×** for approximate AC power.

## Common Pitfalls

1. **GT 1030 has no power sensor.** `nvidia-smi` shows N/A — this is hardware limitation, not a bug.
2. **RAPL is DC-side.** Doesn't include PSU losses (15-20% overhead).
3. **Unplugging HDMI ≠ GPU off.** Desktop NVIDIA cards stay at P8 minimum, drawing 5-10W.
4. **Utilization ≠ power linearly.** A GPU at 50% utilization might draw ~75% of max power, not 50%.
5. **Package power INCLUDES DRAM on some platforms but not others.** Always check which RAPL domains are present.
