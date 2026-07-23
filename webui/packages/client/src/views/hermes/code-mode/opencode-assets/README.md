# OpenCode Embedded Assets (ported from `embedded/`)

This directory contains the **text/configuration assets** of the embedded OpenCode
runtime, ported one file at a time from the repository root `embedded/` directory
(Stage 9 of the dual-mode unification task).

> The actual `opencode` native binaries (macos-arm64 / macos-x64) are **not**
> copied here. They remain under `embedded/opencode/<platform>/opencode` and are
> resolved at runtime by the desktop main process (`mode-manager.ts`).

## Files

| Source (repo root)                       | Ported here                                | Purpose                              |
|------------------------------------------|--------------------------------------------|--------------------------------------|
| `embedded/README.md`                     | `README.md` (this file)                    | Overview of the embedded R&D team    |
| `embedded/start.sh`                      | `start.sh`                                 | Launcher shell script                |
| `embedded/run_task.sh`                   | `run_task.sh`                              | Task execution shell script          |
| `embedded/config/opencode.json`          | `config/opencode.json`                     | OpenCode plugin config               |
| `embedded/config/opencode-config.yaml`   | `config/opencode-config.yaml`              | Model / workspace / isolation config |
| `embedded/config/oh-my-openagent.jsonc`  | `config/oh-my-openagent.jsonc`             | Agent persona/model assignments      |

## How these are used

- `CodeModeView.vue` (renderer) does **not** read these directly.
- The desktop main process (`packages/desktop/src/main/mode-manager.ts`) spawns
  `opencode serve` with env vars derived from the shared config
  (`OPENCODE_API_KEY`, `OPENCODE_MODEL`, `OPENCODE_PROVIDER`, ...).
- These files are kept as reference / human-readable documentation of the
  OpenCode runtime's expected configuration shape, and are available for a
  future "edit OpenCode config" UI in the Code mode header.
