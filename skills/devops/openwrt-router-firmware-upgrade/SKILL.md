---
name: openwrt-router-firmware-upgrade
title: OpenWrt Router Firmware Selection and Upgrade Guide
description: Systematic approach to diagnose router issues, select optimal OpenWrt-based firmware, backup configurations, and perform safe firmware upgrades
tags: [openwrt, firmware, router, upgrade, jdcloud, ax1800, ipq60xx, immortalwrt]
---

# OpenWrt Router Firmware Upgrade Guide

## Overview

This skill provides a systematic workflow for upgrading router firmware to resolve stability issues (VPN instability, WiFi disconnections) and improve performance.

## Workflow

### Phase 1: Hardware Identification

```bash
# SSH into router and gather system info
ssh root@<router-ip>

# Key commands to identify hardware
cat /proc/cpuinfo
cat /tmp/sysinfo/model
cat /etc/openwrt_release
ubus call system board

# Check current resources
free -h
df -h
ip addr show
iwinfo
```

**Document:**
- Router model
- Chipset platform (e.g., ipq60xx, mt7621, x86)
- Current firmware version
- Architecture (aarch64, mipsel, etc.)

### Phase 2: Configuration Backup

```bash
# Create backup directory on local machine
mkdir -p ~/router-backup/<model>-$(date +%Y%m%d)

# Backup all configs via SSH
ssh root@<router-ip> "for f in /etc/config/*; do echo \"===\$(basename \$f)===\"; cat \$f; echo ''; done" > all-configs.txt

# Backup system info
ssh root@<router-ip> "opkg list-installed; echo '---'; uci show; echo '---'; dmesg | head -50" > system-info.txt

# Alternative: Create tarball (if sysupgrade supports)
ssh root@<router-ip> "sysupgrade -b /tmp/backup.tar.gz" && scp root@<router-ip>:/tmp/backup.tar.gz .
```

### Phase 3: Firmware Selection Framework

**Evaluation Criteria:**

| Criteria | Weight | Notes |
|----------|--------|-------|
| Stability | High | LTS releases preferred over snapshots |
| VPN Plugin Support | High | SSR Plus, PassWall, OpenClash availability |
| Hardware Optimization | High | NSS offload, WiFi 6 driver quality |
| Maintenance Status | High | Active community, regular updates |
| Package Availability | Medium | Software repository size |

**Recommended Firmwares by Use Case:**

**For VPN-heavy use (China users):**
1. Lean LEDE - Optimized for Chinese users, frequent updates, pre-integrated plugins
2. ImmortalWrt 23.05 - Best balance of stability and features (if available for your platform)
3. Official OpenWrt - Most stable, manual plugin installation

**For WiFi stability issues:**
- ImmortalWrt (ipq60xx/mt7621 optimized) - if available
- OpenWrt Snapshot (for newer devices like ipq60xx)
- Avoid: Old community builds, unmaintained forks (like HWrt)

**For specific platforms:**
- IPQ60xx (AX1800): OpenWrt Snapshot or Lean LEDE (ImmortalWrt doesn't support ipq60xx)
- IPQ807x (AX3600/AX6000): ImmortalWrt 24.10+
- MT7621: Padavan or OpenWrt 23.05
- x86: Official OpenWrt or ImmortalWrt

**Important Note on ImmortalWrt:**
- ImmortalWrt 23.05.x: NO qualcommax/ipq60xx support
- ImmortalWrt 24.10.x: Only ipq807x, NOT ipq60xx
- For ipq60xx devices (JDCloud AX1800 Pro, etc.), use OpenWrt Snapshot or Lean LEDE instead

**Firmware Discovery Workflow for Limited-Support Platforms:**

When standard repositories don't have factory firmware:

1. **Check OpenWrt Snapshots** (for newer devices)
   ```bash
   curl -sL "https://downloads.openwrt.org/snapshots/targets/<target>/<subtarget>/"
   ```
   - May only have `initramfs` and `sysupgrade`, no `factory`
   - Device names may differ from marketing names

2. **Check ImmortalWrt** (if available for your platform)
   ```bash
   curl -sL "https://downloads.immortalwrt.org/releases/"
   ```
   - Check both 23.05.x and 24.10.x - platform support varies

3. **Check Lean LEDE** (for Chinese devices)
   - https://github.com/coolsnowwolf/lede
   - https://github.com/coolsnowwolf/openwrt-gl-ax1800 (IPQ60xx specific)
   - Often requires self-compilation or finding community builds

4. **Check Device Forums**
   - right.com.cn (恩山论坛) for Chinese routers
   - Device-specific Telegram/Discord groups

5. **Alternative: Use initramfs + sysupgrade method**
   - Boot initramfs via TFTP
   - Then flash sysupgrade from running system
   - Documented in Method 3 above

### Phase 4: Download Firmware

**Common download URLs:**

```bash
# ImmortalWrt
https://downloads.immortalwrt.org/releases/<version>/targets/<target>/<subtarget>/

# Official OpenWrt
https://downloads.openwrt.org/releases/<version>/targets/<target>/<subtarget>/

# Lean LEDE (must compile or find community builds)
https://github.com/coolsnowwolf/lede
```

**File naming:**
- Factory: `*-factory.ubi` or `*-factory.bin` (for stock→OpenWrt)
- Sysupgrade: `*-sysupgrade.bin` (for OpenWrt→OpenWrt)

**Important: Check Device Compatibility**

Marketing names often don't match firmware filenames. Always verify:

```bash
# Check actual board name on your device
ssh root@<router-ip> "cat /tmp/sysinfo/board_name"
# Example output: jdc,ax1800-pro

# Then find matching firmware in download directory
# Look for: jdcloud_re-cs-02, jdcloud_re-ss-01, etc.
```

**Common mismatches:**
| Marketing Name | Firmware Name | Platform |
|----------------|---------------|----------|
| JDCloud AX1800 Pro | `jdcloud_re-cs-02` or `re-ss-01` | ipq60xx |
| GL.iNet AX1800 | `glinet_gl-ax1800` | ipq60xx |
| Xiaomi AX3600 | `xiaomi_ax3600` | ipq807x |

**If exact model not found:**
1. Check if similar models exist (same platform/chipset)
2. Try `re-cs-02` first, then `re-ss-01` for JDCloud
3. Consult device-specific forums (right.com.cn for Chinese routers)

### Phase 5: Flashing Methods

**Method 1: Web Interface (Recommended)**
1. Login to router web UI
2. System → Backup/Flash Firmware
3. Upload firmware file
4. **Uncheck "Keep settings"** for clean install
5. Flash and wait 2-5 minutes

**Method 2: SSH Command Line**
```bash
# Upload firmware
scp <firmware-file> root@<router-ip>:/tmp/

# Flash (no settings preserved)
ssh root@<router-ip> "sysupgrade -n /tmp/<firmware-file>"

# Flash (preserve settings - not recommended for major version changes)
ssh root@<router-ip> "sysupgrade /tmp/<firmware-file>"
```

**Method 3: TFTP Recovery (Brick recovery)**
```bash
# Router: Hold reset, power on, release when LED blinks
# Computer: Set static IP 192.168.1.100
tftp 192.168.1.1
tftp> binary
tftp> put <firmware-file>
```

### Phase 6: Post-Flash Configuration

**Basic Setup:**
```bash
# Change password
passwd

# Configure WAN
uci set network.wan.proto=pppoe  # or dhcp/static
uci set network.wan.username='...'
uci set network.wan.password='...'
uci commit network
/etc/init.d/network restart
```

**Package Manager Note:**
Most OpenWrt-based systems use `opkg`, but some newer ImmortalWrt builds use `apk` (Alpine package manager). Check which one is available:
```bash
which opkg && echo "Using opkg" || which apk && echo "Using apk"
```

**Install VPN Plugins:**
```bash
# For opkg-based systems
opkg update
opkg install luci-app-passwall  # or luci-app-ssr-plus

# For apk-based systems
apk add luci-app-passwall
```

**WiFi Optimization:**
```bash
# 5GHz: Use channels 36-64 or 149-165
uci set wireless.radio0.channel=36
uci set wireless.radio0.htmode='HE80'

# 2.4GHz: Use channels 1, 6, or 11
uci set wireless.radio1.channel=6
uci set wireless.radio1.htmode='HE40'

uci commit wireless
wifi reload
```

**Enable Hardware Offload (if supported):**
```bash
# For IPQ60xx - NSS offload
echo 'options nss-firmware load_separate_firmware=1' > /etc/modules.d/99-nss-firmware

# For MT7621 - HWNAT
/etc/init.d/hwacc start
```

## Platform-Specific Notes

### JDCloud AX1800 Pro (IPQ6018)

**Target:** `qualcommax/ipq60xx`

**Important Firmware Availability Note:**
- **ImmortalWrt 23.05.x**: Does NOT have qualcommax/ipq60xx target
- **ImmortalWrt 24.10.x**: Only has ipq807x, NOT ipq60xx
- **Official OpenWrt**: Has ipq60xx support but device names differ from marketing names

**Device Name Mapping:**
| Marketing Name | OpenWrt Device Name | Board Name |
|----------------|---------------------|------------|
| JDCloud AX1800 Pro | `jdcloud_re-cs-02` or `jdcloud_re-ss-01` | `jdc,ax1800-pro` |

**Recommended Firmware Sources:**

1. **Official OpenWrt Snapshot** (Most Compatible)
   - URL: `https://downloads.openwrt.org/snapshots/targets/qualcommax/ipq60xx/`
   - Files: `openwrt-qualcommax-ipq60xx-jdcloud_re-cs-02-squashfs-sysupgrade.bin`
   - Note: Try `re-cs-02` first, if incompatible try `re-ss-01`

2. **Lean LEDE (大雕固件)** (Best for Chinese Users)
   - Project: https://github.com/coolsnowwolf/openwrt-gl-ax1800
   - Specifically maintained for JDCloud AX1800 Pro
   - Pre-integrated SSR Plus, PassWall, OpenClash
   - Best VPN stability for China users

3. **ImmortalWrt** (NOT available for ipq60xx)
   - Use OpenWrt Snapshot or Lean LEDE instead

**How to Identify Correct Firmware:**
```bash
# Check your device's actual board name
ssh root@<router-ip> "cat /tmp/sysinfo/board_name"
# Output: jdc,ax1800-pro

# Check compatible devices in firmware
# Look for files matching: jdcloud_re-* in the download directory
```

**When Factory Firmware is Unavailable:**

Some devices (like JDCloud AX1800 Pro) only have `sysupgrade` files in official repos, not `factory` files. Solutions:

1. **TFTP + initramfs method** (recommended)
   - Download `initramfs-uImage.itb` file
   - Boot via TFTP recovery mode
   - Once booted, use `sysupgrade` to install permanent firmware

2. **Community builds** (check forums)
   - right.com.cn (恩山论坛)
   - GitHub Actions artifacts from device-specific repos

3. **Self-compile** (last resort)
   - Use Lean's LEDE source
   - Build factory image with proper bootloader support

**Known Issues with HWrt:**
- VPN instability due to outdated plugins
- WiFi disconnections due to missing NSS offload patches
- Memory leaks in WiFi 6 drivers
- Personal maintenance, infrequent updates

**Why OpenWrt Snapshot/Lean LEDE is Better than HWrt:**
- Kernel 5.15/6.1 LTS (vs random SNAPSHOT)
- Proper NSS hardware acceleration (ipq60xx specific)
- Updated WiFi 6 firmware (ath11k)
- Active maintenance and security patches
- Better memory management for 512MB RAM

### Common Fixes

**VPN DNS Issues:**
```bash
# Check if proxy domains resolve to 127.0.0.1
nslookup <proxy-domain> 127.0.0.1

# Fix: Add correct IP to /etc/hosts
echo "<correct-ip> <proxy-domain>" >> /etc/hosts
```

**WiFi Instability:**
```bash
# Disable legacy rates (802.11b)
uci set wireless.radio1.legacy_rates=0

# Enable Airtime Fairness
uci set wireless.radio0.atf=1
uci set wireless.radio1.atf=1

uci commit wireless
wifi reload
```

**Memory Management:**
```bash
# Add to crontab for periodic cache clearing
echo '0 4 * * * echo 3 > /proc/sys/vm/drop_caches' >> /etc/crontabs/root
/etc/init.d/cron restart
```

## Installing Themes

**Argon Theme** (Most Popular):
The Argon theme is the most popular and modern theme for OpenWrt/ImmortalWrt with a clean, responsive design.

```bash
# For opkg-based systems
opkg update
opkg install luci-theme-argon luci-app-argon-config luci-i18n-argon-config-zh-cn

# For apk-based systems
apk add luci-theme-argon luci-app-argon-config luci-i18n-argon-config-zh-cn

# Set as default theme
uci set luci.main.mediaurlbase=/luci-static/argon
uci commit luci

# Restart web server
/etc/init.d/uhttpd restart
```

**Available Themes:**
| Theme | Package | Description |
|-------|---------|-------------|
| Argon | `luci-theme-argon` | Modern, responsive, dark/light mode support |
| Material | `luci-theme-material` | Google Material Design |
| Bootstrap | `luci-theme-bootstrap` | Default theme |
| OpenWrt 2020 | `luci-theme-openwrt-2020` | Official OpenWrt style |

**Theme Customization:**
After installing `luci-app-argon-config`, access theme settings at:
- **System → Argon 主题设置** (Chinese) or **System → Argon Config**
- Customize: dark/light mode, primary color, background image, blur effects

**Cannot find firmware for your device:**
1. Check actual board name: `cat /tmp/sysinfo/board_name`
2. Marketing name ≠ firmware name (e.g., "AX1800 Pro" → `jdcloud_re-cs-02`)
3. Check multiple sources:
   - Official OpenWrt snapshots (for newer devices)
   - Lean LEDE GitHub (for Chinese devices)
   - Device-specific forums (right.com.cn)
4. Try compatible models with same chipset

**Cannot access router after flash:**
1. Check if IP changed (default usually 192.168.1.1)
2. Try TFTP recovery mode
3. Check serial console if available

**WiFi not working:**
1. Check `logread | grep -i wifi`
2. Verify firmware includes proper wireless drivers
3. Try different channel settings

**VPN slow/unstable:**
1. Enable hardware offload if available
2. Check DNS resolution
3. Verify iptables rules: `iptables -t nat -L -n -v`

## References

- ImmortalWrt: https://immortalwrt.org/
- OpenWrt ToH: https://openwrt.org/toh/start
- Right.com.cn forum (Chinese): https://www.right.com.cn/forum/

## DHCP Static Lease Management

After flashing or when setting up a new network, lock down device IPs via static DHCP leases so critical machines (dev workstations, servers, AI hosts) always get the same address. OpenWrt uses `uci` to manage `/etc/config/dhcp` — do NOT hand-edit the file directly.

### Connecting (non-interactive SSH)

Many OpenWrt routers have password-only SSH (no keys). Use `sshpass` for scripting:

```bash
sudo apt install -y sshpass
sshpass -p '<password>' ssh -o StrictHostKeyChecking=no root@192.168.2.1 "<command>"
```

> **Pitfall**: If the password is wrong, sshpass returns "Permission denied" with no hint. Try max 2 passwords before asking the user. Save correct credentials to `~/.hermes/.env` so you never ask again.

### Viewing current DHCP leases

```bash
sshpass -p '<pass>' ssh root@<ip> "cat /tmp/dhcp.leases"
# Format: <epoch> <mac> <ip> <hostname> <client-id>
```

### Reading current DHCP config

```bash
sshpass -p '<pass>' ssh root@<ip> "cat /etc/config/dhcp"
```

### Adding static DHCP leases (batch)

Use `uci` — it validates and prevents corruption:

```bash
sshpass -p '<pass>' ssh root@<ip> "
# Remove all existing host entries
while uci get dhcp.@host[0] &>/dev/null; do
    uci delete dhcp.@host[0]
done

# Add each device
uci add dhcp host
uci set dhcp.@host[-1].name='my-workstation'
uci set dhcp.@host[-1].mac='AA:BB:CC:DD:EE:FF'
uci set dhcp.@host[-1].ip='192.168.2.100'

# Commit and reload
uci commit dhcp
/etc/init.d/dnsmasq restart
"
```

> **Note**: `uci add dhcp host` appends to the list; `uci set dhcp.@host[-1]` targets the last added entry. Use `-1` for "last" or `0`, `1`, `2` for specific indices.

### Verifying static leases were applied

```bash
sshpass -p '<pass>' ssh root@<ip> "uci show dhcp | grep host"
```

### DHCP pool awareness

Before assigning static IPs, know the pool range:
```
config dhcp 'lan'
    option start '100'    # First dynamic IP
    option limit '150'    # Number of addresses (100-249)
```
Static leases can be inside or outside the pool — both work in OpenWrt.

### Pitfalls

| Pitfall | Prevention |
|---------|-----------|
| `Permission denied` loops | After 2 failed attempts, ask user. Do not cycle through password lists |
| Wrong device name (sda vs sdb) | USB plug/unplug can swap device names. Always `lsblk` immediately before destructive commands |
| Hand-editing `/etc/config/dhcp` | Use `uci` commands instead. Direct file edits may not survive `uci commit` |
| Forgetting to restart dnsmasq | Always run `/etc/init.d/dnsmasq restart` after `uci commit dhcp` |
| Old static entries with wrong subnet | Check existing entries — they may reference `192.168.1.x` when the actual network is `192.168.2.x`. Delete and recreate with correct subnet |
| LuCI JSON-RPC `/rpc/auth` returns 404 | ImmortalWrt and some OpenWrt builds don't expose the JSON-RPC API. Fall back to `sshpass` + SSH (`ssh` + `uci`) — it works everywhere and is more scriptable anyway. Do NOT waste time trying curl/cookie-based LuCI login when SSH is available |

### Reference

- `references/dhcp-static-lease-example.md` — Full session transcript: ImmortalWrt DHCP setup with 7 devices (router, ThinkPad, Mac, phone, speaker)
