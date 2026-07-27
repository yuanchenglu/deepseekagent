# DeepAgent WebUI

DeepAgent WebUI is the browser interface distributed in Phase 2. This directory is licensed under BSL-1.1; it is source-available and is not part of the MIT-licensed DeepAgent Core.

## Supported release

The first public Beta supports macOS Apple Silicon. Install Core from the official site, then install and open WebUI:

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
deepagent webui install
deepagent webui open
```

Lifecycle commands:

```bash
deepagent webui start
deepagent webui open
deepagent webui status
deepagent webui stop
```

`open` creates a short-lived, one-time login ticket. DeepAgent provides no fixed default password and does not persist the browser session JWT in local storage.

## Isolation and security contract

- HTTP listens on `127.0.0.1` by default.
- LAN discovery and LAN/public access are disabled by default.
- Configuration and sessions live under `~/.deepagent/data/`.
- PID, port, lock and ticket files live under `~/.deepagent/runtime/webui/`.
- The launcher never kills or adopts a process merely because it occupies a port.
- Child processes receive an explicit environment allowlist; unrelated API keys are not inherited.
- Hermes data (`~/.hermes`) and user OpenCode data (`~/.config/opencode`, `~/.opencode`) are never read, migrated or deleted.

The old Electron shell is a separately identified `DeepAgent Legacy Preview` (`org.starseas.deepagent.legacy`). It is not the primary download and receives only security, path and startup fixes.

## Development

```bash
npm install
npm run build
npm test
```

Production releases must be generated from a matching Git tag and release manifest. `deepagent webui install` refuses missing checksums, size/hash mismatches, unsafe archives and unmanaged existing directories.

## License

See [LICENSE](./LICENSE). DeepAgent Core in the repository root is MIT-licensed; this WebUI/Desktop directory is BSL-1.1.
