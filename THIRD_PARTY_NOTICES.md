# Third-party dependency notices

This document records the direct Python dependencies resolved for the Phase 1 CLI Alpha Core.
The authoritative complete dependency graph and hashes are in `uv.lock`; every dependency
continues to be governed by its upstream license. Release engineering must re-run license review
whenever `uv.lock` changes.

| Package | Resolved version | Declared license | Upstream |
|---|---:|---|---|
| anthropic | 0.86.0 | MIT | https://github.com/anthropics/anthropic-sdk-python |
| edge-tts | 7.2.7 | LGPL-3.0 (one file MIT) | https://github.com/rany2/edge-tts |
| exa-py | 2.10.2 | MIT | https://github.com/exa-labs/exa-py |
| fal-client | 0.13.1 | Apache-2.0 (official repository; wheel metadata omits it) | https://github.com/fal-ai/fal |
| fire | 0.7.1 | Apache-2.0 | https://github.com/google/python-fire |
| firecrawl-py | 4.17.0 | MIT | https://github.com/firecrawl/firecrawl |
| httpx | 0.28.1 | BSD-3-Clause | https://github.com/encode/httpx |
| Jinja2 | 3.1.6 | BSD-3-Clause | https://github.com/pallets/jinja |
| openai | 2.24.0 | Apache-2.0 | https://github.com/openai/openai-python |
| parallel-web | 0.4.2 | MIT | https://github.com/parallel-web/parallel-sdk-python |
| prompt-toolkit | 3.0.52 | BSD-3-Clause | https://github.com/prompt-toolkit/python-prompt-toolkit |
| pydantic | 2.12.5 | MIT | https://github.com/pydantic/pydantic |
| PyJWT | 2.12.1 | MIT | https://github.com/jpadilla/pyjwt |
| python-dotenv | 1.2.1 | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| PyYAML | 6.0.3 | MIT | https://github.com/yaml/pyyaml |
| requests | 2.33.0 | Apache-2.0 | https://github.com/psf/requests |
| rich | 14.3.3 | MIT | https://github.com/Textualize/rich |
| tenacity | 9.1.4 | Apache-2.0 | https://github.com/jd/tenacity |

This table is an engineering inventory, not legal advice and not a replacement for the license
texts shipped by upstream projects. Optional dependency groups, WebUI npm dependencies, embedded
OpenCode dependencies, development tools, and bundled Skills may add other licenses; they are
excluded from the Phase 1 Core artifact and must be reviewed in the phase that distributes them.

## DeepCode runtime (Phase 2 Experimental)

The separately downloaded DeepCode runtime includes the OpenCode executable. OpenCode is licensed
under the MIT License, copyright (c) 2025 opencode. Its complete license text is included as
`LICENSE` in every DeepCode runtime artifact. DeepAgent never replaces or invokes a user's global
OpenCode installation.

## Release-generated inventories

Every release build generates machine-readable dependency inventories with
`scripts/audit-python-licenses.py` and `webui/scripts/audit-npm-licenses.mjs`.
Publishing fails when an installed dependency has an unknown or prohibited license. Dependencies
that require notice review remain explicitly listed in the generated report.
