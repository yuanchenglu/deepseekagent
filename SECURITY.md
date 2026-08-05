# DeepAgent Security Policy

## Supported releases

Security fixes are provided for the most recent promoted release on each public channel.
During Phase 1, that means the current macOS Apple Silicon CLI Alpha only. Source snapshots,
unpromoted artifacts, old Alpha builds, WebUI previews, and Electron development builds are
not supported releases.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or leaked credential. Use the
repository's private [GitHub security advisory](https://github.com/yuanchenglu/deepseekagent/security/advisories/new)
and include:

- affected version and installation method;
- operating system and architecture;
- reproduction steps or a minimal proof of concept;
- expected impact and any known workarounds;
- whether credentials or user data may have been exposed.

The maintainers will acknowledge a complete report within five business days. Acknowledgement
is not a promise of a particular remediation date. Please allow a coordinated fix and release
before public disclosure.

## Release security boundary

- DeepAgent product state is rooted at `DEEPAGENT_HOME` (default `~/.deepagent`).
- The installer does not require `sudo` and must stop on a missing or invalid SHA-256 digest.
- The uninstaller removes only manifest-owned paths after boundary validation.
- Hermes and user OpenCode directories are outside DeepAgent's ownership boundary.
- The CLI Alpha artifact excludes `webui/`, Electron, and embedded OpenCode artifacts.

If a release violates one of these rules, treat it as a release-blocking security defect.
