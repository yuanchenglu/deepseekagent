# NPM Package Security Audit Checklist

A specialized application of source-code-verification principles for evaluating third-party npm packages before installation or recommendation.

## Trigger

User asks "evaluate the security of `<package>`", "is `<package>` safe to install", or similar security-audit questions about an npm package.

## Phase 1: Registry Metadata (no source clone needed)

```bash
npm view <package> --json
```

Key fields to inspect:
- `scripts.postinstall` / `scripts.preuninstall` / `scripts.prepare` — these run arbitrary code on install/uninstall. Read them.
- `scripts.preuninstall` that makes HTTP requests — check if it's `127.0.0.1` only (local daemon shutdown) vs external.
- `dependencies` — scan for suspicious or unknown packages. Well-known deps (`commander`, `ws`, `js-yaml`, `turndown`) are low-risk.
- `dist.attestations` — look for `provenance.predicateType: "https://slsa.dev/provenance/v1"` (SLSA build attestation).
- `dist.signatures` — npm publish signatures verify the publisher identity.
- `version` history — rapid version churn (90+ versions in 3 months) may indicate active development OR could be suspicious. Cross-reference with GitHub commit activity.
- `repository.url` — verify it points to a real GitHub repo.
- `publishConfig.access: "public"` — expected for scoped packages.

## Phase 2: Source Clone

```bash
git clone --depth 1 <repo-url> /tmp/<name>
```

## Phase 3: Critical Scripts Audit

Read these files FIRST (they run automatically):

| File | Why |
|------|-----|
| `scripts/postinstall.js` | Runs on `npm install -g`. Check for network calls, file writes outside expected paths, data exfiltration. |
| `scripts/preuninstall.js` | Runs on `npm uninstall -g`. Same checks. |
| `scripts/prepare.js` | Runs on `npm install` (including as dependency). Same checks. |

Red flags:
- `fetch()` / `http.request()` to non-localhost, non-registry URLs
- Writing to `~/.ssh/`, `/etc/`, `~/.bashrc`, `~/.zshrc`
- `child_process.exec()` with dynamic strings
- Reading `~/.aws/`, `~/.config/gh/`, `~/.npmrc`, `~/.gitconfig`

## Phase 4: Main Entry Point Audit

Read the file referenced by `main` in package.json. Key checks:
- Does it call out to external servers on startup?
- Does it have an update-check mechanism? (acceptable if: npm registry or GitHub API only, non-blocking, cache-respecting)
- Does it load any binary blobs?

## Phase 5: Network Call Pattern Search

```bash
# Search for all network calls
rg "fetch\(|http://|https://" src/ -g "*.ts" -g "*.js"

# Search for telemetry/analytics patterns
rg "telemetry|analytics|track|sentry|datadog|posthog|gtag|collect\b|metrics" src/ -g "*.ts" -g "*.js"
```

Analysis:
- If telemetry patterns are found, check whether the code is SENDING telemetry or FILTERING it (e.g., regex filtering analytics URLs from scraped data is benign).
- Update checks to npm registry + GitHub API are standard and acceptable.
- Any requests to unknown domains or IPs are red flags.

## Phase 6: Daemon/Server Audit (if applicable)

If the package runs a local server/daemon:
- Verify it binds to `127.0.0.1` only, not `0.0.0.0`.
- Check for authentication/authorization on endpoints.
- Check body size limits (prevents OOM attacks).

## Phase 7: Supply Chain

- `npm view <package> downloads` — check monthly download count. Very low (<100) may indicate an untrusted package.
- GitHub stars, forks, open issues — community trust signals.
- License — Apache-2.0, MIT, BSD are standard.
- Check if the package has been on npm for a while (created date) or is brand new.

## Phase 8: Overall Verdict

Synthesize into a clear table:

| Dimension | Assessment |
|-----------|-----------|
| Backdoor / malicious code | Yes/No |
| Telemetry / data collection | Yes/No |
| External network requests | List + purpose |
| Supply chain security | SLSA provenance, signatures, downloads |
| Dependency risk | All known vs unknown deps |
| Code quality | Organization, comments, tests |
| Local privilege use | Daemon, file writes, shell completions |

## Pitfalls

1. **Don't confuse filtering with sending**: A regex that matches `analytics` in scraped URLs is likely filtering noise from API discovery, NOT sending telemetry. Read the context.
2. **Don't conflate local daemon with remote server**: `127.0.0.1` daemon is architecture-necessary for browser-automation tools. Check what it does, not just that it exists.
3. **Update checks are not spyware**: npm registry + GitHub API version checks with caching and timeouts are standard practice (npm, gh, yarn all do this).
4. **Rapid versioning is not inherently malicious**: Some projects iterate fast. Cross-reference with GitHub — real commits backing each version = legitimate development.
