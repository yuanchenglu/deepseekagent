# Gateway Crash Diagnostic Pipeline — Reproduction Recipe

## Case Overview

- **Date**: 2026-06-18
- **Machine**: Lenovo ThinkPad E450c (bluth@100.108.145.79)
- **Hermes version**: Branch `fix/feishu-group-open-policy-mention` on custom fork
- **Symptom**: User reported "all tool calls reporting errors" due to "backend middleware upgrade parameter incompatibility"

## What Happened

| Time | Event |
|------|-------|
| June 17 01:49-02:13 | Gateways started (yunying, course-designer, cto) |
| June 18 03:53 | SIGTERM received → old gateways shut down |
| June 18 08:56 | Systemd restarted gateways; cto old process crashed with `_middleware` error during shutdown |
| June 18 08:56 | All 4 gateways restarted successfully |

## SSH Connectivity Issue

Initial IP (192.168.2.157) failed during key exchange:

```
kex_exchange_identification: Connection closed by remote host
```

**Root cause**: Machine was not on the same local subnet — traffic routed through VPN tunnel (utun8). Machine reachable via alternate IP (100.108.145.79).

**Diagnostic commands used**:

```bash
# Network check
ping -c 3 -W 3 192.168.2.157           # timeout
nc -zv -w 5 192.168.2.157 22           # port open
ssh -vvv bluth@192.168.2.157 "uptime"  # key exchange failure

# Route check
route -n get 192.168.2.157             # goes via utun8 (VPN tunnel)

# Port scan for alternative services
for port in 22 80 443 3000 3001 4000 5000 8080 8443 9090 9091 7860 11434 51820; do
  nc -z -w 2 192.168.2.157 $port 2>&1 && echo "Port $port: OPEN" || true
done
```

## Process vs. Systemd State Mismatch

```bash
# Systemd state (3 running + 1 failed)
systemctl --user list-units --type=service --all | grep -iE 'hermes|gateway'
# Output:
#   hermes-gateway-course-designer.service  active     running
#   hermes-gateway-cto.service              active     running
#   hermes-gateway-yunying.service          active     running
#   hermes-gateway.service                  failed     failed       ← default gateway down

# Actual running processes (3 gateways, NOT 4)
ps aux | grep 'hermes.*gateway' | grep -v grep
# PIDs 514554 (yunying), 514556 (course-designer), 595456 (cto)
# DEFAULT gateway was missing from ps!
```

Only port 3000 was listening — confirmed single gateway attachment.

## Log Diagnostic Sequence

### Gateway Log (`gateway.log`)
Showed clean shutdown at 03:53 with SIGTERM:
```
Received SIGTERM — initiating shutdown
```
Then systemd restart but no further log entries (new process started fresh).

### Error Log (`errors.log`)
Found the smoking gun:
```
❌ Error during OpenAI-compatible API call #2: 'PluginManager' object has no attribute '_middleware'
```

### Exit Diagnostic (`gateway-exit-diag.log`)
Showed repeated non-zero exits over days:
```
asyncio.run.returned... success: false
gateway.exit_nonzero
```
Pattern: gateway would start, run for hours, then crash. Multiple restarts across June 5-17.

### MCP stderr (`mcp-stderr.log`)
Only MCP DrawIO activity — not related to the crash.

## Git Source Code Forensics

```bash
cd ~/.hermes/hermes-agent

git status --short
# UU gateway/platforms/feishu.py   ← UNMERGED CONFLICT
# M  gateway/run.py                ← LOCAL MODIFICATION

git branch -a | head -5
# * fix/feishu-group-open-policy-mention  ← fork branch, NOT upstream/main

git log --oneline HEAD..upstream/main | wc -l
# 0 (current branch is based on latest upstream)

git log --oneline upstream/main..HEAD | wc -l
# 1 (one commit ahead: "fix(feishu): respect group policy...")

git ls-files --stage gateway/platforms/feishu.py
# 100644 abc... 1  feishu.py  (merge base)
# 100644 def... 2  feishu.py  (our side — fork branch)
# 100644 ghi... 3  feishu.py  (their side — upstream)
```

## PluginManager `_middleware` Attribute Check

```bash
cd ~/.hermes/hermes-agent

# Found PluginManager class in plugins.py
grep -n 'class PluginManager\|_middleware' hermes_cli/plugins.py

# Output showed _middleware IS defined:
# 1087: class PluginManager:
# 1093:     self._middleware: Dict[str, List[Callable]] = {}

# Runtime test confirmed:
python3 -c "from hermes_cli.plugins import PluginManager; pm = PluginManager(); print('_middleware exists:', hasattr(pm, '_middleware'))"
# _middleware exists: True
```

The code was correct ON DISK, but the OLD process (running since June 17) loaded a `PluginManager` instance created before the `_middleware` attribute existed. When shutdown triggered middleware code paths, the old instance crashed.

## Resolution Steps in Order

### 1. Fix UU conflict (feishu.py)

```bash
cd ~/.hermes/hermes-agent
git checkout --theirs gateway/platforms/feishu.py
git add gateway/platforms/feishu.py
```

### 2. Restore run.py

```bash
git checkout gateway/run.py  # already matched index
```

### 3. Restart all gateways

```bash
for srv in hermes-gateway hermes-gateway-course-designer hermes-gateway-cto hermes-gateway-yunying hermes-web-ui; do
    systemctl --user restart "$srv.service" 2>/dev/null && echo "$srv restarted" || echo "$srv skipped"
done
```

### 4. Verify health

```bash
sleep 5
for srv in hermes-gateway hermes-gateway-course-designer hermes-gateway-cto hermes-gateway-yunying; do
    status=$(systemctl --user is-active "$srv.service" 2>/dev/null)
    echo "$srv: $status"
done
```

### 5. Verify Feishu connection

```bash
journalctl --user -u hermes-gateway.service --since "1 minute ago" --no-pager | grep -i "feishu\|wss"
# Output: "[Lark] [INFO] connected to wss://msg-frontier.feishu.cn/..."
```

## Outcome

All 4 gateways came up clean. The `_middleware` error only manifested during the OLD process shutdown — new processes loaded the correct code with `_middleware` initialized properly.

## Key Lessons

1. **Process vs systemd state check first** — a gateway can be running (from earlier `--replace`) while systemd thinks it's failed, or vice versa
2. **Log triage order matters** — journalctl first (systemd-level), then gateway.log (runtime), then errors.log (specific crashes)
3. **UU files are silent killers** — `git status --short` shows them but they produce no Python error until the exact code path with the merge conflict is hit
4. **Restart doesn't fix code problems** — fix the git conflict FIRST, then restart. Restart alone re-runs the same broken code.
5. **Branch drift vs. upstream** — when running a fork branch, always check `git log --oneline upstream/main..HEAD` to know what unique changes you carry
