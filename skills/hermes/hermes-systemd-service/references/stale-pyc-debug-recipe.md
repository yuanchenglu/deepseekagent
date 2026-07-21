# Stale .pyc Bytecache — Debug Reference

## Symptom

Running Gateway crashes repeatedly with:

```
ERROR gateway.platforms.base: [Feishu] Error handling message: too many values to unpack (expected 3)
ValueError: too many values to unpack (expected 3)
```

Stack trace points to a slash-command handler (e.g. `_handle_model_command`). Line numbers in the traceback mismatch the current source code when checked.

## Root Cause

Hermes code was updated (`git pull`, scripted update, etc.) while a Gateway process was still running. The process keeps compiled `.pyc` bytecache in memory. When a method contains an inline import:

```python
async def _handle_model_command(self, event):
    from hermes_cli.model_switch import parse_model_flags  # loads from DISK
    model_input, explicit_provider, persist_global, force_refresh = parse_model_flags(raw_args)
```

The **import** loads the new module from disk (which may have different return types), but the **method body** was compiled from old bytecache (expecting different number of values to unpack). This mismatch crashes with `ValueError`.

## Real Example (2026-06-02)

| Component | Old (bytecache) | New (on disk) |
|-----------|-----------------|---------------|
| `parse_model_flags` return | 3-tuple: `(model_input, provider, is_global)` | 4-tuple: `(model_input, provider, is_global, force_refresh)` |
| Unpack at call site | 3 variables | 4 variables |
| Result | Crashed with `expected 3` | Should match after restart |

## Fix

```bash
# 1. Identify affected gateway(s)
systemctl --user list-units --type=service --state=running --no-legend | grep hermes-gateway

# 2. Find the profile's service
#    e.g. hermes-gateway-yunying.service

# 3. Clean bytecache
find ~/.hermes/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 4. Restart
systemctl --user restart hermes-gateway-<profile>.service

# 5. Verify
systemctl --user status hermes-gateway-<profile>.service --no-pager
journalctl --user -u hermes-gateway-<profile>.service --no-pager -n 20 | grep -i "error\|valueerror\|unpack"
```

## Prevention

After any Hermes code update, batch-restart all running gateways:

```bash
for srv in $(systemctl --user list-units --type=service --state=running --no-legend 2>/dev/null | grep hermes-gateway | awk '{print $1}'); do
    echo "Restarting $srv..."
    systemctl --user restart "$srv"
done
find ~/.hermes/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "Done — all gateways restarted, bytecache cleaned"
```
