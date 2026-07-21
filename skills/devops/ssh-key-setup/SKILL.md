---
name: ssh-key-setup
description: Set up bidirectional SSH key-based authentication between two machines, including Tailscale-connected hosts on different LANs.
category: devops
tags:
  - ssh
  - authentication
  - keys
  - tailscale
  - remote-access
---

# SSH Key Setup

Set up passwordless SSH between two machines, including Windows-to-macOS and Tailscale setups. Covers both directions.

## Prerequisites

- SSH server running on the target machine
  - **macOS:** `sudo systemsetup -getremotelogin` → should say "On"
  - **Linux:** `systemctl status sshd` or check if port 22 is listening
  - **Windows (OpenSSH Server):** `sc query sshd` → should show STATE=4 RUNNING

## Key Directory / Path Differences by Platform

| Platform | Authorized keys path | Notes |
|---|---|---|
| Linux / macOS | `~/.ssh/authorized_keys` | Permissions: `~/.ssh`=700, `authorized_keys`=600 |
| Windows (standard user) | `%USERPROFILE%\.ssh\authorized_keys` | Same permissions requirement |
| Windows (admin user) | `%ProgramData%\ssh\administrators_authorized_keys` | **icacls**: `SYSTEM:F`, `BUILTIN\Administrators:F`, no inheritance |

> **Critical:** On Windows, if the user is in the **Administrators** group, OpenSSH reads `administrators_authorized_keys` instead of the user's `.ssh\authorized_keys`. The file must have explicit permissions set via `icacls` — SSHd silently ignores it otherwise.

## One Direction (current → remote)

### Standard (Linux/macOS target)

```bash
# If you have an existing key
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@remote-host

# Or generate one first
ssh-keygen -t ed25519 -C "your-comment"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@remote-host
```

### Windows target (admin user)

When `ssh-copy-id` is not available or the target has the admin-path quirk:

```bash
# Manually copy the key to Windows
sshpass -p 'password' ssh user@windows-host 'cmd /c "echo YOUR_PUBKEY > C:\ProgramData\ssh\administrators_authorized_keys & icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant "SYSTEM:F" /grant "BUILTIN\Administrators:F""'
```

Set the correct permissions explicitly — this is **required** for admin accounts. Without `icacls`, SSHd silently ignores the file.

## Reverse Direction (remote → current)

1. Get the remote machine's public key:
   ```bash
   # Linux/macOS remote
   ssh user@remote-host 'cat ~/.ssh/id_ed25519.pub'

   # Windows remote (non-admin user)
   ssh user@windows-host 'type %USERPROFILE%\.ssh\id_ed25519.pub'

   # Windows remote (admin user — check administrators_authorized_keys)
   ssh user@windows-host 'type %USERPROFILE%\.ssh\id_ed25519.pub'
   ```

2. Append it to the local machine's `authorized_keys`:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   echo '<remote-pubkey>' >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

> **Pitfall:** If `~/.ssh/authorized_keys` doesn't exist yet, create it with `chmod 600`. Without correct permissions, SSHd will silently ignore the file.

## Verification

```bash
# Test without password prompts
ssh -o BatchMode=yes user@remote-host 'echo OK'
```

Use `BatchMode=yes` to force non-interactive auth — if it fails, key auth isn't working yet.

## File Transfer (Post-SSH Setup)

Once SSH key auth is in place, transfer files across platforms. See `references/cross-platform-file-transfer.md`:

- **Small dirs (<100 MB):** `scp -r` is fine
- **Large dirs (100 MB – 5 GB):** `tar + SCP` (compress, transfer one file, extract) — avoids `scp -r` timeout
- **Background transfers:** Start SCP in background to work in parallel while the transfer completes

## Tailscale-Aware Setup

When machines are on different LANs but connected via Tailscale:

1. Identify Tailscale IPs (100.x.x.x range):
   ```bash
   # On each machine
   ifconfig | grep -E 'inet ' | grep 100.
   # Or
   tailscale status
   ```

2. **Both directions** must use the Tailscale IP as the target:
   - macOS → ThinkPad: `ssh user@100.108.x.x`
   - ThinkPad → macOS: `ssh user@100.73.x.x`

3. **Do not** assume LAN IPs (192.168.x.x, 10.x.x.x) work for cross-machine SSH — they may be on completely different subnets even though the Tailscale tunnel is up.

## Windows SSH Client Config & Agent Setup

When the Windows machine needs to initiate SSH connections (reverse direction of primary setup):

### Enable Windows ssh-agent (required for agent-based auth)

```cmd
sc config ssh-agent start=auto
net start ssh-agent
ssh-add %USERPROFILE%\.ssh\id_ed25519
```

Without the agent running, `ssh -v` shows:
```
debug1: get_agent_identities: ssh_get_authentication_socket: No such file or directory
```
Keys still work via direct file read (no agent needed for simple auth), but agent forwarding and keychain integration requires it.

- **Error `error :1058` on start:** The service is disabled. Run `sc config ssh-agent start=auto` first, then `net start ssh-agent`.

### Windows SSH client config (`%USERPROFILE%\.ssh\config`)

Create a config file to specify which identity file to use per host:

```cmd
echo Host 192.168.10.100>> %USERPROFILE%\.ssh\config
echo   IdentityFile %USERPROFILE%\.ssh\id_rsa_for_windows>> %USERPROFILE%\.ssh\config
echo   StrictHostKeyChecking accept-new>> %USERPROFILE%\.ssh\config
```

Without this, the Windows client iterates over all default key names (`id_rsa`, `id_ecdsa`, `id_ed25519`, etc.) and tries each one. Specifying `IdentityFile` skips the scan.

### Copy private key to Windows via SSH pipe

```bash
# From the machine that generated the key
cat ~/.ssh/id_rsa_for_windows | ssh user@windows-host \
  'powershell -Command "$input | Set-Content $env:USERPROFILE\.ssh\id_rsa_for_windows"'

# Set correct permissions
ssh user@windows-host \
  'cmd /c "icacls %USERPROFILE%\.ssh\id_rsa_for_windows /inheritance:r /grant %USERNAME%:R /grant SYSTEM:R"'
```

## macOS sudo without Terminal PTY

When running Hermes Agent (non-interactive terminal), `sudo -S` for piping passwords is typically blocked. Use `SUDO_ASKPASS` with a custom askpass script instead:

```bash
# Create askpass script
cat > ~/.hermes/scripts/sudo_askpass.sh << 'EOF'
#!/bin/bash
echo "YOUR_SUDO_PASSWORD"
EOF
chmod +x ~/.hermes/scripts/sudo_askpass.sh

# Use it
SUDO_ASKPASS=~/.hermes/scripts/sudo_askpass.sh sudo -A <command>

# Clean up
rm ~/.hermes/scripts/sudo_askpass.sh
```

This works because `sudo -A` calls the external askpass program rather than reading stdin, bypassing the `sudo -S` block.

### macOS sshd is managed by launchd

Unlike Linux where sshd runs as a persistent daemon, macOS uses launchd to start sshd on-demand when a connection arrives on port 22:

```bash
# Restart / kick the service
sudo launchctl kickstart -k system/com.openssh.sshd

# Check if enabled
launchctl print-disabled system | grep ssh

# View service logs
log show --predicate 'process == "sshd"' --last 30m --info
```

## Common Pitfalls

### Windows Admin authorized_keys
- **Symptom:** Key is in `~/.ssh/authorized_keys` but auth fails.
- **Root cause:** User is an Administrator; OpenSSH reads `administrators_authorized_keys` instead. Must set `icacls` permissions explicitly.

### macOS Sequoia (OpenSSH 10.2) ↔ Windows (OpenSSH 9.5p1) — hostbound extension hang
- **Symptom:** `ssh -v` shows TCP connect, key exchange, "Server accepts key", then `sign_and_send_pubkey: using publickey-hostbound-v00@openssh.com` — and **hangs forever** (times out).
- **Root cause:** The `publickey-hostbound-v00@openssh.com` extension in macOS 15+ OpenSSH 10.2 interacts badly with keys generated by Windows OpenSSH 9.5p1 client during the signing handshake. The key is valid and accepted; the signing handshake never completes.
- **Best workaround — generate key on Unix side, copy private key to Windows:**
  1. On the **Mac** (or any Linux machine), generate a new key pair:
     ```bash
     ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_for_windows -N ""
     ```
     (Use RSA; ed25519 may trigger the same issue depending on client build.)
  2. Add the public key to the Mac's `~/.ssh/authorized_keys`:
     ```bash
     cat ~/.ssh/id_rsa_for_windows.pub >> ~/.ssh/authorized_keys
     ```
  3. Copy the **private key** to Windows via SSH pipe:
     ```bash
     cat ~/.ssh/id_rsa_for_windows | ssh user@windows-host \
       'powershell -Command "$input | Set-Content $env:USERPROFILE\.ssh\id_rsa_for_windows"'
     ```
  4. Set proper permissions on Windows:
     ```cmd
     icacls %USERPROFILE%\.ssh\id_rsa_for_windows /inheritance:r /grant %USERNAME%:R /grant SYSTEM:R
     ```
  5. Configure Windows SSH client to use this key for the Mac host:
     ```cmd
     echo Host 192.168.10.100> %USERPROFILE%\.ssh\config
     echo   IdentityFile %USERPROFILE%\.ssh\id_rsa_for_windows>> %USERPROFILE%\.ssh\config
     ```
  This works because the key itself is generated by a compatible OpenSSH version; the Windows client only signs with it.
- **Fallback (if you have sudo on the Mac):**
  Restart the SSH daemon:
  ```bash
  sudo launchctl kickstart -k system/com.openssh.sshd
  ```
  Or toggle Remote Login off/on in System Settings → General → Sharing.
- **If no sudo on Mac at all:** Use a reverse tunnel (Mac → Windows with `-R` flag) so the Mac acts as client, or use a third machine as jump host.

### Permission denied
- **`Permission denied (publickey,password)`**: The key was not added, or permissions are wrong. Check `~/.ssh/authorized_keys` on the target and its permissions (must be `600`).
- **Connection timed out**: Wrong IP or network unreachable. Try the Tailscale IP instead of LAN IP.
- **`ssh: Could not resolve hostname`**: Typo in hostname or IP. Verify with `ping`.
- **macOS SSH not running**: `sudo systemsetup -setremotelogin on` to enable Remote Login.
- **Windows SSH server not running**: `net start sshd` from an admin Command Prompt.

### Diagnostic approach for hanging auth
1. Add `-vvv` (triple verbose) to see exactly where it hangs.
2. On the **server side**, check logs:
   - macOS: `log show --predicate 'process == "sshd"' --last 10m --info`
   - Windows: `Get-WinEvent -LogName OpenSSH/Operational | Select-Object -First 10`
3. If "Server accepts key" is seen but hangs afterward, suspect the hostbound extension compatibility issue above.
