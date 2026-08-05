---
slug: /
sidebar_position: 0
title: "DeepAgent CLI Alpha"
description: "Official documentation for the macOS Apple Silicon CLI Alpha"
hide_table_of_contents: true
---

# DeepAgent CLI Alpha

The first public DeepAgent release is a command-line Agent for **macOS Apple
Silicon**. It is designed to install, update, roll back, and uninstall without
reading or modifying an existing Hermes or OpenCode product installation.

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
deepagent setup
deepagent doctor
deepagent
```

## Start here

| Document | Purpose |
|---|---|
| [Quickstart](/docs/getting-started/quickstart) | Install, configure, and complete a first task |
| [Installation contract](/docs/getting-started/installation) | Paths, verification, updates, rollback, and uninstall |
| [Platform status](/docs/getting-started/termux) | Why unsupported platforms intentionally stop |
| [CLI Alpha FAQ](/docs/reference/faq) | Troubleshooting and product boundaries |
| [Contributing](/docs/developer-guide/contributing) | Development and mixed-license contribution rules |

## Release boundary

- Phase 1 ships Core and CLI only; it does not ship WebUI, Electron, bundled
  OpenCode, or bundled Skills.
- DeepAgent Core is MIT-licensed. Existing source under `webui/` is BSL-1.1
  source-available software. The repository is not entirely MIT.
- The default product root is `~/.deepagent`; Hermes and user OpenCode paths
  remain outside DeepAgent ownership.
- Intel macOS, Linux, Windows/WSL, Android, LAN access, and public network
  access are not part of this Alpha support promise.
