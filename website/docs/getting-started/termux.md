---
sidebar_position: 3
title: "Android / Termux status"
description: "Why Android is not included in the first DeepAgent public release"
---

# Android / Termux status

Android and Termux are **not supported by the CLI Alpha release**. The official
installer intentionally stops on this platform; it must not be bypassed by piping
an older Hermes or repository installer into a shell.

The repository contains upstream Android-related code and development notes, but
their presence is not evidence of a tested DeepAgent product release. Android can
be added only after it has its own installation isolation, dependency, upgrade,
rollback, uninstall, and coexistence test matrix.

For the currently supported path, use an Apple Silicon Mac and follow the
[CLI Alpha installation guide](./installation.md).
