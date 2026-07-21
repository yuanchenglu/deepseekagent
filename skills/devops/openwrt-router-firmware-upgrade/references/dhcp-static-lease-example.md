# Session Example: ImmortalWrt DHCP Static Lease Setup

> Real session: 2026-06-02. Router: ImmortalWrt SNAPSHOT on 192.168.2.1, LuCI + Argon theme

## Network Environment

- Router: ImmortalWrt @ 192.168.2.1 (MAC: dc:d8:7c:4c:b9:8c)
- DHCP pool: 192.168.2.100-249 (start=100, limit=150)
- User: bluth, workstation ThinkPad E450c (Ubuntu 24.04)

## Authentication

- SSH: `root@192.168.2.1`, password `password`
- LuCI Web: http://192.168.2.1, same credentials
- Non-interactive access via `sshpass -p 'password' ssh root@192.168.2.1`

> **Pitfall encountered**: Two wrong passwords tried before finding "password". `sshpass` and LuCI both returned unhelpful errors. Always confirm credentials with user.

## Devices Discovered (from /tmp/dhcp.leases)

| IP | MAC | Hostname | Device |
|----|-----|----------|--------|
| 192.168.2.157 | 68:f7:28:d0:4b:2f | bluth-ThinkPad-E450c | User's workstation |
| 192.168.2.130 | 9a:6a:de:ed:d8:93 | REDMI-K80 | Phone |
| 192.168.2.228 | e6:86:43:61:0e:32 | vivo-X200-Pro-mini | Phone |
| 192.168.2.164 | a6:f0:2f:e7:0a:3e | Mac | Apple computer |
| 192.168.2.166 | e0:9d:31:d5:3e:0f | bluth-PC | Desktop PC |
| 192.168.2.140 | 88:2d:53:e0:aa:c4 | Xiaodu-AudioSpeaker | Smart speaker |
| 192.168.2.115 | e4:b3:18:e8:b2:14 | * (no hostname) | Unknown |

## Problem Found: Stale Static Entries

Existing `/etc/config/dhcp` had 3 `config host` entries pointing to **192.168.1.x** subnet — completely wrong for the actual 192.168.2.x network. These were remnants from a previous configuration.

```bash
# Deleting stale entries (the while-loop pattern)
while uci get dhcp.@host[0] &>/dev/null; do
    uci delete dhcp.@host[0]
done
```

## Final Configuration Applied

All 7 known devices bound with static leases matching their current DHCP addresses:

```bash
# Pattern for each device:
uci add dhcp host
uci set dhcp.@host[-1].name='bluth-ThinkPad-E450c'
uci set dhcp.@host[-1].mac='68:f7:28:d0:4b:2f'
uci set dhcp.@host[-1].ip='192.168.2.157'
# ... repeat for all devices ...
uci commit dhcp
/etc/init.d/dnsmasq restart
```

## Verification

```bash
uci show dhcp | grep host
# Output confirmed all 7 host entries with correct MACs and IPs
```

## Lessons

- Always check existing DHCP config before adding entries — there may be wrong-subnet remnants
- Use `while uci delete dhcp.@host[0]` to cleanly remove all hosts (the list re-indexes after each delete, so `@host[0]` always targets the first remaining entry)
- DHCP lease file (`/tmp/dhcp.leases`) gives ground truth for current assignments — base static entries on these, not assumptions
- Unknown devices (no hostname) can be left dynamic — only bind known/important devices
