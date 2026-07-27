---
sidebar_position: 3
title: "CLI Alpha FAQ"
description: "Supported platforms, installation, isolation, updates, and troubleshooting"
---

# CLI Alpha FAQ

## What platform is supported?

The first public release supports macOS Apple Silicon only. The installer verifies
both `Darwin` and `arm64` and exits on Intel macOS, Linux, Windows/WSL, and Android.
Those platforms may be added after platform-specific testing exists.

## Where is the official installer?

Use only:

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
```

`/install.sh` is a Shell script, not a redirect to an archive. The script downloads
the promoted Alpha channel manifest, an immutable version manifest, and the matching
Core archive. Missing fields, invalid size, or a SHA-256 mismatch stop installation.

## Does installation require sudo?

No. Product files are placed under `~/.deepagent/`, and the only global command is
`~/.local/bin/deepagent`. If `~/.local/bin` is not on `PATH`, add it to your shell
configuration; do not reinstall with `sudo`.

## Does DeepAgent use Hermes or OpenCode data?

No. The product root is `DEEPAGENT_HOME`, defaulting to `~/.deepagent`. A user-level
`HERMES_HOME` value does not become the DeepAgent product root. DeepAgent installation
and uninstall do not own these paths:

```text
~/.hermes/
~/.config/opencode/
~/.opencode/
```

DeepCode/OpenCode runtime artifacts are not included in Phase 1.

## What licenses apply?

This is a mixed-license repository, not an entirely MIT repository. DeepAgent Core
uses MIT. Existing source under `webui/`, including the old Desktop code, uses
BSL-1.1 and is source-available. The CLI Alpha artifact contains Core only.

## How do I configure a model provider?

Run:

```bash
deepagent setup
deepagent doctor
```

The setup wizard lists providers supported by the installed Core. API usage and data
handling are also governed by the provider you choose.

## `deepagent` is not found after installation

Start a new terminal and check:

```bash
ls -l ~/.local/bin/deepagent
echo "$PATH"
```

If needed, add this to `~/.zshrc`, then open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Do not create a `hermes` or `opencode` alias.

## How do I check for and install updates?

```bash
deepagent update --check
deepagent update
```

The update command uses the same verified installer as a first installation. A new
version is installed beside the current version. A failed download, verification,
dependency install, or smoke test does not promote it.

## How do I roll back?

```bash
deepagent update --rollback
```

To select a specific version already present under `~/.deepagent/versions/`:

```bash
deepagent update --rollback --to 0.9.0-alpha.1
```

Rollback smoke-tests the selected CLI and restores the previous pointer if the test
fails.

## How do I uninstall?

Keep configuration and sessions:

```bash
deepagent uninstall --keep-data
```

Request removal of registered DeepAgent data:

```bash
deepagent uninstall --full
```

Uninstall requires a valid `install-manifest.json`, checks path boundaries, and does
not delete files it cannot prove the installer owns.

## Is WebUI or Electron included?

No. Browser WebUI is planned for Phase 2. The redesigned DeepAgent/DeepCode Electron
client is Phase 3. Existing UI source in the repository is not part of the CLI Alpha
release artifact or support promise.

## Is LAN or public network access supported?

No. LAN and public access are not Phase 1 commitments. Phase 2 WebUI will default to
`127.0.0.1`; any broader access requires a separate security evaluation.

## What should I include in a bug report?

Include `deepagent --version`, `uname -s`, `uname -m`, the failing command, exit code,
and redacted logs from `~/.deepagent/logs/`. Never publish API keys, access tokens,
cookies, or the contents of `~/.deepagent/config/.env`.

Report suspected vulnerabilities through the private process in the repository
`SECURITY.md`, not a public issue.
