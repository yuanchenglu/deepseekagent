---
title: "Contributing to DeepAgent"
description: "Development, testing, security reporting, and mixed-license boundaries"
---

# Contributing to DeepAgent

Read the repository's `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, and the
license file governing the directory you intend to change before editing.

## Development setup

```bash
git clone --recurse-submodules https://github.com/yuanchenglu/deepseekagent.git
cd deepseekagent
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
```

Keep development state separate from an installed product:

```bash
export DEEPAGENT_HOME="$HOME/.deepagent-test"
```

DeepAgent product code must not infer its root from a user's existing
`HERMES_HOME` value.

## Verification

Run the full Python suite before proposing a change:

```bash
source venv/bin/activate
venv/bin/python -m pytest tests/ -q
```

Release and installer changes also require:

```bash
bash scripts/test-install.sh
bash scripts/build-release.sh --core-only --version 0.9.0-alpha.test
```

The CLI Alpha support target is macOS Apple Silicon. Code for another platform
does not make that platform supported; a platform-specific install, update,
rollback, uninstall, and coexistence matrix is required first.

## Security reports

Do not publish suspected vulnerabilities or credentials in an issue. Use the
private GitHub security advisory process described in `SECURITY.md`.

## License boundary

This repository is not entirely MIT:

| Target directory | Contribution license |
|---|---|
| DeepAgent Core outside separately licensed components | Root MIT license |
| `webui/` including existing Desktop source | `webui/LICENSE` (BSL-1.1) |
| Embedded or third-party components | License in the component directory |

Submitting a contribution means agreeing to the license governing the files
changed. A contribution that crosses license boundaries should be split into
separate commits and reviewed for both scopes.

## Evidence expected in a change

- the problem and falsifiable assumption;
- source or test evidence;
- the smallest scoped implementation;
- exact verification commands and results;
- any unsupported or unverified scenario;
- confidence: certain, probable with a percentage, or uncertain.
