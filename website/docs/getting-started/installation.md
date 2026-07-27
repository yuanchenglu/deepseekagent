---
sidebar_position: 2
title: "Installation"
description: "Install the DeepAgent CLI Alpha on macOS Apple Silicon"
---

# Install DeepAgent CLI Alpha

The first public Alpha supports **macOS Apple Silicon only**. Intel macOS,
Linux, Windows, WSL, Android, the browser WebUI, and Electron are not part of
this release contract.

## Quick install

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
```

The installer:

- downloads the promoted, versioned Core artifact;
- requires a valid release manifest and SHA-256 digest;
- installs without `sudo` under `~/.deepagent`;
- creates only `~/.local/bin/deepagent`;
- runs a CLI smoke test before reporting success.

It does **not** read, migrate, modify, or delete:

- `~/.hermes`;
- `~/.config/opencode`;
- `~/.opencode`;
- the global `hermes` or `opencode` commands.

## First run

Make sure `~/.local/bin` is in your `PATH`, then run:

```bash
deepagent --version
deepagent setup
deepagent doctor
deepagent
```

## Update and rollback

```bash
deepagent update --check
deepagent update
deepagent update --rollback
```

Each version is installed separately under `~/.deepagent/versions/`. An update
is promoted only after dependency installation and the installer smoke test
complete. Rollback switches to a previously verified local version.

## Uninstall

Keep configuration, sessions, and logs:

```bash
deepagent uninstall --keep-data
```

Remove all paths registered by the DeepAgent installer:

```bash
deepagent uninstall --full
```

The uninstaller refuses to run without a valid `install-manifest.json` and
never infers ownership from `HERMES_HOME` or the current source directory.

## Custom product directory

Advanced users may select an absolute directory:

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | \
  bash -s -- --dir /absolute/path/to/deepagent
```

Protected Hermes and OpenCode directories are always rejected.

## Source development

Source development is separate from the managed Alpha installation:

```bash
git clone https://github.com/yuanchenglu/deepseekagent.git
cd deepseekagent
source venv/bin/activate
```

Do not run `deepagent uninstall --full` as a source cleanup command. It only
operates on paths recorded by the managed installer.
