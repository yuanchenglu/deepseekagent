---
name: vpn-globalprotect-openconnect
description: Connect to GlobalProtect VPN using OpenConnect CLI as an alternative to the proprietary GlobalProtect client. Supports automated and interactive login modes.
version: 1.0.0
metadata:
  hermes:
    tags: [vpn, globalprotect, openconnect, networking, remote-access]
---

# GlobalProtect VPN via OpenConnect

Use OpenConnect to connect to GlobalProtect VPN gateways without installing the proprietary Palo Alto Networks GlobalProtect client.

## Overview

OpenConnect is an open-source VPN client that supports multiple protocols including GlobalProtect (GP). It can be used as a drop-in replacement for the official GlobalProtect client on Linux systems.

**Use Cases:**
- Accessing corporate networks that use GlobalProtect VPN
- Automating VPN connections in scripts
- Running on systems where the official client isn't available
- CI/CD pipelines requiring VPN access

## Prerequisites

- Linux system (Ubuntu/Debian/CentOS)
- sudo privileges (required for network interface manipulation)
- VPN credentials (username/password)
- VPN gateway address (e.g., `vpn.company.com`)

## Installation

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y openconnect
```

Verify installation:
```bash
openconnect --version
# Expected: OpenConnect version v9.x or later
```

Check supported protocols:
```bash
openconnect --version
# Should show: Supported protocols: anyconnect (default), nc, gp, pulse, f5, fortinet, array
```

## Basic Usage

### Interactive Mode (Recommended for first use)

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username
```

You'll be prompted for:
1. Password (hidden input)
2. Any 2FA/OTP codes if required

### Background Mode

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username --background
```

### With Password from File (Scripting)

```bash
# Create password file (secure permissions!)
echo "your_password" > ~/.vpn_pass
chmod 600 ~/.vpn_pass

# Connect using password file
sudo openconnect --protocol=gp vpn.company.com --user=username --passwd-on-stdin < ~/.vpn_pass
```

**Security Note:** Always use `chmod 600` on password files and store them outside version control.

## Advanced Options

### Specify Interface Name

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username --interface=vpn0
```

### Disable IPv6

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username --disable-ipv6
```

### Connect with Certificate

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username --certificate=client.pem --sslkey=key.pem
```

### Custom MTU

```bash
sudo openconnect --protocol=gp vpn.company.com --user=username --mtu=1300
```

## Troubleshooting

### DNS Resolution Issues

If the VPN gateway hostname doesn't resolve:

```bash
# Check DNS
nslookup vpn.company.com

# If it only resolves inside the VPN, you may need to:
# 1. Connect from a location with VPN access, OR
# 2. Use the IP address directly (check with IT department)
```

### Authentication Failures

**Symptom:** Login fails with "Invalid username/password"

**Common Causes:**
1. **Special characters in password** - Characters like `&`, `$`, `!` may need escaping:
   ```bash
   # Wrap password in single quotes
   sudo openconnect --protocol=gp vpn.company.com --user=username --passwd-on-stdin <<<'MyP&ssw0rd!'
   ```

2. **Wrong domain** - Some VPNs require domain prefix:
   ```bash
   # Try with domain prefix
   sudo openconnect --protocol=gp vpn.company.com --user=DOMAIN\\username
   # or
   sudo openconnect --protocol=gp vpn.company.com --user=username@domain.com
   ```

3. **2FA/OTP required** - Check if your organization requires a second factor

### Connection Drops

```bash
# Enable more verbose output
sudo openconnect --protocol=gp vpn.company.com --user=username --verbose

# Reconnect automatically
sudo openconnect --protocol=gp vpn.company.com --user=username --background --pid-file=/var/run/openconnect.pid
```

### Browser Portal vs CLI

If the VPN has a web portal (like SonicWall Virtual Office):

1. **Web portal access** - Use browser automation to log in and download client configuration
2. **Direct CLI connection** - Use OpenConnect with the gateway address (often different from portal URL)

**Note:** The web portal URL (e.g., `https://vpn.company.com/cgi-bin/login`) and the VPN gateway address for OpenConnect may be different. Check with your IT department for the correct gateway address.

### Check Connection Status

```bash
# Check if VPN interface exists
ip addr show tun0

# Check routing table
ip route show

# Test connectivity to internal resources
ping 10.0.0.1  # Replace with internal IP
```

## Automation Examples

### Connect on Boot (systemd)

Create `/etc/systemd/system/openconnect-vpn.service`:

```ini
[Unit]
Description=OpenConnect VPN
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/openconnect --protocol=gp --user=username --passwd-on-stdin vpn.company.com < /etc/openconnect/passwd
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable openconnect-vpn
sudo systemctl start openconnect-vpn
```

### Wrapper Script

```bash
#!/bin/bash
# vpn-connect.sh

VPN_HOST="vpn.company.com"
VPN_USER="username"
PID_FILE="/tmp/openconnect.pid"

connect() {
    echo "Connecting to $VPN_HOST..."
    sudo openconnect --protocol=gp \
        --user="$VPN_USER" \
        --background \
        --pid-file="$PID_FILE" \
        "$VPN_HOST"
}

disconnect() {
    if [ -f "$PID_FILE" ]; then
        sudo kill $(cat "$PID_FILE")
        rm "$PID_FILE"
        echo "Disconnected"
    else
        echo "Not connected"
    fi
}

case "$1" in
    connect)
        connect
        ;;
    disconnect)
        disconnect
        ;;
    status)
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
            echo "Connected (PID: $(cat $PID_FILE))"
        else
            echo "Not connected"
        fi
        ;;
    *)
        echo "Usage: $0 {connect|disconnect|status}"
        exit 1
        ;;
esac
```

## Security Best Practices

1. **Never commit passwords** - Use environment variables or secure credential stores
2. **Use certificate authentication** when possible (more secure than passwords)
3. **Restrict password file permissions** - `chmod 600` on any files containing credentials
4. **Monitor connection logs** - Check `/var/log/syslog` or `journalctl` for connection issues
5. **Disconnect when not needed** - Don't leave VPN connections open indefinitely

## Comparison: OpenConnect vs Official Client

| Feature | OpenConnect | Official GlobalProtect |
|---------|-------------|------------------------|
| Cost | Free (open source) | Requires license |
| Platforms | Linux, BSD | Windows, macOS, Linux, mobile |
| GUI | No (CLI only) | Yes |
| HIP Checks | Limited | Full support |
| 2FA | Supported | Supported |
| Split Tunneling | Supported | Supported |

## Resources

- **OpenConnect Documentation:** https://www.infradead.org/openconnect/
- **GlobalConnect Protocol Info:** https://www.infradead.org/openconnect/globalprotect.html
- **Man Page:** `man openconnect`

## Notes

- OpenConnect uses the `tun` kernel module - ensure it's loaded: `sudo modprobe tun`
- Some corporate VPNs require specific routes or DNS settings - check with your IT department
- The `--protocol=gp` flag is essential for GlobalProtect compatibility
- Connection logs are typically sent to syslog - check with `sudo tail -f /var/log/syslog`
