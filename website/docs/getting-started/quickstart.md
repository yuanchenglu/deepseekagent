---
sidebar_position: 1
title: "CLI Alpha Quickstart"
description: "Install DeepAgent CLI Alpha on macOS Apple Silicon and complete a first task"
---

# CLI Alpha Quickstart

The first public release supports **macOS Apple Silicon only**. Linux, Intel macOS,
Windows/WSL, and Android are not release-supported yet.

## 1. Install from the official website

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
```

The installer does not use `sudo`. It verifies the release manifest, artifact size,
and SHA-256 before installing a version under `~/.deepagent/versions/`. It creates
only `~/.local/bin/deepagent` as a global command.

## 2. Verify and configure

```bash
deepagent --version
deepagent setup
deepagent doctor
```

Choose a supported model provider in the setup wizard and enter the required API
credential. Credentials and sessions remain under `~/.deepagent/`; DeepAgent does
not use the data directories of an installed Hermes or OpenCode product.

## 3. Complete a first task

```bash
deepagent
```

At the prompt, try a small task whose result you can check, such as:

```text
Create a Markdown summary of the files in the current directory. Ask before writing.
```

Use `/help` to see interactive commands and `Ctrl+C` to stop the current operation.

## 4. Update or roll back

```bash
deepagent update --check
deepagent update
deepagent update --rollback
```

Updates install side by side and switch the `current` pointer only after verification.

## 5. Uninstall safely

Keep configuration and sessions:

```bash
deepagent uninstall --keep-data
```

Remove only installer-owned code and registered DeepAgent data:

```bash
deepagent uninstall --full
```

The uninstaller does not remove unknown files and never owns `~/.hermes`,
`~/.config/opencode`, or `~/.opencode`.

See [Installation](./installation.md) for failure behavior and directory details.
