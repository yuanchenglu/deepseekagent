# Hermes Environment Variable Audit

**Date**: 2026-06-20
**Hermes Version**: v0.17.0 (commit 2ab09a6c5083)
**Source**: `~/.hermes/hermes-agent/`

## Official Hermes Environment Variables

The only Hermes-related env var that affects the HERMES_HOME data directory:

| Variable | Exists? | Used For |
|----------|---------|----------|
| `HERMES_HOME` | YES | Root data directory (default `~/.hermes`) |

Reference: `hermes_constants.py::get_hermes_home()`:
```python
def get_hermes_home() -> Path:
    return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
```

## Invented Variables — Zero Source Matches

The following variables were used in previous portable deployments but do NOT exist anywhere in the Hermes Agent source code:

| Variable | grep across entire repo |
|----------|------------------------|
| `HERMES_STATE_DIR` | 0 results |
| `HERMES_CONFIG_PATH` | 0 results |
| `HERMES_WEBUI_PORTABLE` | 0 results |

Search command used:
```bash
rg "HERMES_STATE_DIR|HERMES_CONFIG_PATH|HERMES_WEBUI_PORTABLE" --type py
```

## Conclusion

Setting `HERMES_HOME` to the `.hermes/` directory is sufficient. All other env vars
that the startup scripts or tests set beyond `HERMES_HOME` have no effect on Hermes
behavior and were fabricated by a previous AI session.

When building a portable Hermes deployment, the only env var you need to export is:
```bash
export HERMES_HOME="$PROJECT_DIR/data/.hermes"
```

## Gateway/Platform Env Vars (separate concern)

These are platform-specific env vars used by the Gateway, not by Hermes core:
- `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, etc. — stored in `data/.hermes/.env`
- `GATEWAY_ALLOW_ALL_USERS` — gateway DM policy override
- `HERMES_GATEWAY_PORT`, `HERMES_WEB_PORT` — port configuration (read from config.yaml, not env)
