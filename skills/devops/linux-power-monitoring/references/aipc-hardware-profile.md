# bluth-aipc Hardware Profile

Captured: 2026-06-11  
Hostname: bluth-AIPC  
OS: Deepin Linux, kernel 6.18.34-amd64  
Tailscale IP: 100.89.88.88  
Local IP: 192.168.10.186/24 (WiFi, wlxe0e1a932b785)

## Components

| Component | Detail |
|---|---|
| **CPU** | Intel Core i5-10400F @ 2.90GHz, 6C/12T, Comet Lake |
| **Motherboard** | ASUS H510M-D3H/M.2 (Rev 1.xx) |
| **Chipset** | Intel H510 (Tiger Lake-H SMBus) |
| **GPU** | NVIDIA GeForce GT 1030, 4GB GDDR5, Pascal GP108 |
| **RAM** | 39GB DDR4 (exact DIMM config unknown, no EDAC/dmidecode without root) |
| **VRAM** | 4096 MiB |
| **Storage** | 1× NVMe 223GB, 1× SATA SSD 117GB, 2× HDD (1TB + 3.6TB) |
| **NVIDIA Driver** | 580.119.02 |
| **PSU** | Unknown ATX (assumed 80+ White) |

## RAPL Power Limits

| Domain | PL1 | PL2 | Hardware Max |
|---|---|---|---|
| package-0 | 125W | 250W | 65W (Intel default, overridden by BIOS) |
| core | 0 (unlimited) | — | N/A |
| dram | 0 (unlimited) | — | N/A |

Note: The motherboard overrode PL1 from Intel's 65W default to 125W.

## GPU Power Characteristics

- **Power limit**: 19.6W
- **Power sensors**: NONE (`nvidia-smi power.draw` returns `[N/A]`)
- **P-state at idle**: P8
- **Runtime D3**: Supported but status is "active" (Xorg + compositor keep GPU awake)
- **Power connectors**: None (bus-powered, draws from PCIe slot only)
- **TDP**: 30W
- **Idle estimate**: ~5-8W (P8, no display load)
- **Full load estimate**: ~20W (near power limit)

## Processes holding GPU open

```
Xorg (1186), kwin_x11 (4079), kglobalacceld (4166), dde-shell (4227), 
uos-ai-assistant (4800), chrome (42694)
```

## Sensors Available

- **coretemp**: CPU core temperature only
- **Super I/O sensors**: NONE (ASUS H510M budget board, driver not loaded)
- **EDAC**: Not available
- **Fan RPM**: Not available

## Power Monitoring Setup

- **Software**: Custom `powerlog` daemon (`/usr/local/bin/powerlog`)
  - Service: `powerlog.service` (systemd, auto-start)
  - Log: `/var/log/powerlog.txt` (cumulative kWh, 10-min intervals)
  - Service log: `/var/log/powerlog-service.log`
  - Method: RAPL pkg+dram + NVML GPU estimation
  - Measured: CPU package + DRAM (accurate via RAPL)
  - Estimated: GPU (NVML utilization × power limit, ±15-20%)
  - Missing: Storage (~16W), motherboard (~18W), PSU losses (~15-18%)
  - RAPL-only captures ~55-65% of total AC power

- **External**: Smart plug via Mi Home (model unknown, no power data visible)

## Idle Power Profile (from powerlog, ~28h data)

- Average CPU+DRAM (RAPL): ~4.2W
- Average GPU (NVML estimated): ~8.2W
- Total DC logged: ~12.4W
- Actual estimated AC total: ~28-35W (DC logged + unmeasured components + PSU loss)

## Network Topology

```
[Router 192.168.2.1]
    ├── ThinkPad 192.168.2.157 (wired, enp0s25)
    │   └── Tailscale 100.108.145.79
    └── [WiFi subnet 192.168.10.0/24]
        └── AIPC 192.168.10.186 (WiFi)
            └── Tailscale 100.89.88.88
```

Subnets are isolated — no direct routing between 192.168.2.x and 192.168.10.x. Tailscale bridges them via DERP relay.
