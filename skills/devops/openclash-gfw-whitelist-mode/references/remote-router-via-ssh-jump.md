# Remote OpenWRT Router via SSH Jump Host

## Problem

The OpenClash router is NOT directly reachable from your machine. It's behind another host on a different subnet. You can reach the intermediate host via Tailscale/SSH, but the router's LAN IP is only accessible from that intermediate host.

## Solution: SSH Jump Host (`-J`)

```bash
# Syntax
ssh -J <jump-user@jump-host> <router-user@router-ip>

# Real example: reach 192.168.10.1 through 100.89.88.88 (bluth@AIPC)
sshpass -p 'root' ssh -J bluth@100.89.88.88 root@192.168.10.1
```

## Requirements

- Jump host SSH must use key-based auth (passwordless)
- `sshpass` installed on the originating machine for the router's password
- Router must accept SSH on port 22 from the jump host's subnet

## When to Use

- Router on different physical subnet (e.g. 192.168.10.x vs your 192.168.2.x)
- Router accessible only through a machine on its LAN
- Router management machine is offline/remote but a Tailscale-connected host is available

## Common Commands via Jump Host

```bash
# Single command
sshpass -p 'root' ssh -J bluth@100.89.88.88 root@192.168.10.1 "uci get openclash.config.proxy_mode"

# Interactive shell
sshpass -p 'root' ssh -J bluth@100.89.88.88 root@192.168.10.1

# With StrictHostKeyChecking for first connection
sshpass -p 'root' ssh -o StrictHostKeyChecking=accept-new \
  -J bluth@100.89.88.88 root@192.168.10.1 "hostname"
```
