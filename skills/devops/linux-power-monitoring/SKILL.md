---
name: linux-power-monitoring
description: Measure and estimate power consumption on Linux machines using RAPL, NVML, sensors, and external meters. Covers CPU/DRAM/GPU power monitoring, total system estimation methodology, and smart plug integration with Mi Home.
---

# Linux Power Monitoring

Complete methodology for measuring and estimating real-time and cumulative power consumption on Linux hardware — from on-die sensors (RAPL) to GPU monitoring (NVML) to system-level estimation and external meters.

## 1. CPU + DRAM: Intel RAPL

Intel Running Average Power Limit (RAPL) provides hardware-level energy counters with ~95%+ accuracy.

### Sysfs paths

```
/sys/class/powercap/intel-rapl:0/        # package (CPU cores + uncore/ring)
/sys/class/powercap/intel-rapl:0:0/      # core-only (PP0, not always present)
/sys/class/powercap/intel-rapl:0:1/      # DRAM (DIMM power, not memory controller)
```

### Reading cumulative energy (microjoules)

```bash
cat /sys/class/powercap/intel-rapl:0/energy_uj
```

⚠️ **Permission pitfall**: `energy_uj` is typically root-only (`-r-------- 1 root root`). Either run the monitoring daemon as root (systemd service) or add a udev rule to relax permissions. Reading other attributes (name, max_energy_range_uj, constraint_*) does NOT require root.

### Reading power limits (microwatts)

```bash
cat /sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw  # PL1 (sustained)
cat /sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw  # PL2 (burst)
cat /sys/class/powercap/intel-rapl:0/constraint_0_max_power_uw    # hardware maximum
```

**Note**: Motherboard firmware can override PL1 above Intel's default TDP. Example: i5-10400F with Intel default 65W had PL1 set to 125W on an ASUS H510M board.

### Computing instantaneous power

```python
def read_uj(path):
    with open(path) as f:
        return int(f.read())

e1 = read_uj("/sys/class/powercap/intel-rapl:0/energy_uj")
time.sleep(1)
e2 = read_uj("/sys/class/powercap/intel-rapl:0/energy_uj")
power_watts = (e2 - e1) / 1_000_000  # μJ → W
```

Handle counter overflow: RAPL counters wrap at `max_energy_range_uj`. If delta is negative, add `max_energy_range_uj`.

### Supported domains by CPU generation

- **Sandy Bridge through Haswell**: package, PP0 (core), PP1 (graphics/uncore)
- **Broadwell through Comet Lake**: package, core, DRAM (sometimes uncore)
- **Alder Lake and newer**: package, core, DRAM, platform (PSYS)

Always enumerate available domains: `ls /sys/class/powercap/intel-rapl:*/name`

## 2. GPU: NVIDIA NVML / nvidia-smi

### Check if GPU has power sensors

```bash
nvidia-smi --query-gpu=name,power.draw,power.limit --format=csv
```

If `power.draw` returns `[N/A]`, the GPU has **no power monitoring hardware**. This is common on:

- GT 1030, GTX 1050 (no power sensors)
- Some GTX 1050 Ti variants
- Older Quadro entry-level cards

**Most GTX 1060 and above have sensors.** When in doubt, query first — never assume.

### Get power limit and utilization (always available)

```bash
nvidia-smi --query-gpu=power.limit,utilization.gpu,utilization.memory,pstate --format=csv
```

### Estimate GPU power when sensors are absent

When `power.draw` is N/A, use a linear model based on utilization and power limit:

```python
# GT 1030 example: power_limit = 19.6W, P8 idle approx 40% of limit
idle_mw = power_limit_mw * 40 // 100
gpu_mw = idle_mw + (power_limit_mw - idle_mw) * utilization_pct // 100
```

This is a **first-order approximation**. Actual power vs utilization curve is non-linear (leakage current floor, voltage scaling). Expect ±15-20% error.

### Check which processes hold the GPU open

```bash
nvidia-smi pmon -c 1
```

Processes holding the GPU prevent it from entering deep sleep (D3cold). Even without a display connected, Xorg + compositor keep the DRM device open.

### Runtime D3 (PCIe power management)

```bash
cat /sys/bus/pci/devices/0000:01:00.0/power/control       # "on" or "auto"
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status # "active" or "suspended"
```

Desktop NVIDIA GPUs rarely enter D3cold — the driver keeps them active.

## 3. Storage Power (Estimation Required)

No consumer hardware has inline storage power monitoring. Use fixed estimates:

| Drive Type | Idle (W) | Active (W) |
|---|---|---|
| 3.5" HDD (7200 RPM) | 5-6 | 7-9 |
| 2.5" HDD (5400 RPM) | 1.5-2 | 3-4 |
| SATA SSD | 0.5-1 | 2-3 |
| NVMe SSD (Gen3) | 1-2 | 4-6 |
| NVMe SSD (Gen4) | 2-3 | 6-8 |

Check HDD spin state: `smartctl -n standby /dev/sda`

## 4. Motherboard + Chipset + Fans (Fixed Offset)

| System Class | Estimated DC Draw |
|---|---|
| Desktop (budget board, 2-3 fans) | 15-20 W |
| Desktop (high-end, 5+ fans, RGB) | 20-35 W |
| Laptop | 5-10 W |
| Mini PC / NUC | 5-12 W |

## 5. PSU Efficiency

PSU efficiency is load-dependent (not a flat percentage). Budget PSUs are least efficient at low load.

| PSU Rating | Efficiency at 20% load | Efficiency at 50% load | Efficiency at 100% load |
|---|---|---|---|
| 80+ White | ~80% | ~82% | ~80% |
| 80+ Bronze | ~82% | ~85% | ~82% |
| 80+ Gold | ~87% | ~90% | ~87% |
| 80+ Platinum | ~90% | ~92% | ~89% |

Formula: `AC_Watts = DC_Watts / efficiency_at_load_pct`

When PSU model is unknown, assume 80+ White as worst case.

## 6. Total System Power Estimation Methodology

### Tier 1: Hardware measured (accurate)
- CPU package (RAPL) ✓
- DRAM (RAPL) ✓
- GPU (NVML power.draw, if sensor present) ✓

### Tier 2: Estimated from utilization (approximate)
- GPU without power sensor (NVML utilization × power limit)
- HDD activity (smartctl + known wattage)

### Tier 3: Fixed offset (rough)
- Storage (idle wattage per drive count)
- Motherboard + chipset + fans
- PSU efficiency conversion

### Formula

```
DC_Total = RAPL_package + RAPL_dram + GPU_estimated + Storage_estimated + Mobo_offset
AC_Total = DC_Total / PSU_efficiency
```

A RAPL-only measurement typically captures only 55-65% of total AC power on a desktop system with discrete GPU. Multiply by 1.7-1.8× for a rough AC estimate.

## 7. Smart Plug / External Meter (Gold Standard)

The ONLY method to get true total AC power with ±1-2% accuracy.

### Xiaomi/Mijia Smart Plug Model Reference

| Model | Power Monitoring | Protocol | Notes |
|---|---|---|---|
| ZNCZ01CM | ❌ | WiFi | Basic on/off only |
| ZNCZ02CM | ✅ | WiFi | |
| ZNCZ03CM | ✅ | WiFi | |
| ZNCZ04CM | ✅ | WiFi | |
| ZNCZ05CM | ✅ | WiFi | |
| CX series (Chuangmi) | Varies | WiFi | Check spec |
| QBKG series (Aqara) | Some models | ZigBee | Requires gateway |

### Finding power data in Mi Home app

1. Tap the device tile (not the on/off switch)
2. Scroll down past the main controls
3. Look for "用电量" (energy) or "当前功率" (instant power)
4. If not visible, check `···` menu → More features
5. Check device info for model number — ZNCZ01CM has no power monitoring hardware

### ZigBee socket notes

ZigBee sockets (e.g., Aqara) will NOT appear on WiFi network scans or respond to mDNS. They connect through a Xiaomi Gateway Hub. Discovery requires the gateway's IP.

### Alternative: Python API access

Some Xiaomi WiFi sockets expose a local HTTP API on port 54321 (MiIO protocol). Use `python-miio` library for programmatic access:

```bash
pip install python-miio
miio discover  # broadcast discovery
```

Note: newer firmware versions may disable the local API port. If discovery returns nothing, the socket may be cloud-only.

## 8. Common Pitfalls

- **BIOS does NOT show real-time power**: BIOS only displays static configuration values (power limits, voltages). It cannot measure dynamic power draw while the OS is running.
- **RAPL energy_uj requires root**: Wrap in a systemd service. See `references/powerlog-daemon-example.py`.
- **GT 1030 and entry-level NVIDIA cards have no power sensors**: Must estimate. Check with `nvidia-smi --query-gpu=power.draw` first.
- **`sensors` returning empty**: On budget motherboards (H510, A520, etc.), the Super I/O chip driver may not be loaded. Check with `sensors-detect` (from `lm-sensors` package). Missing drivers = no fan/voltage/temperature readings beyond CPU coretemp.
- **Smart plug WiFi ≠ always discoverable**: Newer firmware may disable mDNS and the MiIO port. Check the Mi Home app for the device model first.
- **Subnet isolation**: Smart home devices and computers may be on different subnets. Scan from the correct network.
- **GPU won't go to zero watts without a display**: The GPU core has leakage current, VRAM needs refresh, and PCIe link stays active. Only physical removal or D3cold (rare on desktops) brings it to zero.

## 9. Reference Files

- `references/powerlog-daemon-example.py` — Complete RAPL + NVML power logging daemon (systemd service, cumulative kWh tracking with crash recovery)
- `references/aipc-hardware-profile.md` — Specific hardware configuration of bluth-aipc (ASUS H510M, i5-10400F, GT 1030, power characteristics)
