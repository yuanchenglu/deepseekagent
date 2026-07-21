# ECC Ecosystem Overview

> Context for the ecc-market-research Hermes skill — documents the broader ECC (Everything Claude Code) ecosystem available locally at `~/Code/ECC/`.

## Project Summary

ECC is a "Harness-native Agent OS" — 232 skills, 60 agents, 75 commands, and automated hooks for AI coding assistants.

- **GitHub**: https://github.com/affaan-m/ECC (182K+ Stars, MIT license)
- **Local path**: `~/Code/ECC/`
- **Latest version**: v2.0.0-rc.1 (Apr 2026) — includes Rust control-plane prototype (`ecc2/`)
- **Cross-harness**: Works on Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, GitHub Copilot, and 5+ more

## Ecosystem Structure

| Component | Count | Directory |
|-----------|-------|-----------|
| Skills | 232 | `~/Code/ECC/skills/` |
| Agents | 60 | `~/Code/ECC/agents/` + `.agents/` |
| Commands | 75 | `~/Code/ECC/commands/` |
| Hooks | system-level | `~/Code/ECC/hooks/` |
| Install manifests | — | `~/Code/ECC/manifests/install-modules.json` |
| Language rules | 12+ | `~/Code/ECC/rules/` |
| Guides | 3 | Shorthand, Longform, Security |

### Skill Categories (from install manifest)

| Module ID | Category | Skills Included |
|-----------|----------|----------------|
| `framework-language` | Core tech | Coding patterns, testing, frameworks (Java, Python, Go, Rust, Kotlin, etc.) |
| `database` | Data | Postgres, MySQL, Prisma, ClickHouse, JPA, migrations |
| `workflow-quality` | Quality | TDD, verification, eval-harness, continuous-learning, error-handling |
| `security` | Security | Security review, Django/Spring/Laravel security, HIPAA, smart contract |
| `research-apis` | Research | Deep research, scientific databases (PubMed, USPTO), PubMed |
| `business-content` | **Commercial** | Market research, SEO, content-engine, brand-voice, investor-outreach, lead-intelligence |
| `operator-workflows` | Ops | Google Workspace ops, billing ops, Jira, github-ops, cost-tracking |
| `social-distribution` | Social | Crosspost, X API |
| `media-generation` | Media | Manim, Remotion, Blender, video editing, fal.ai |

## Business-Content Skills (Related)

These are the complementary business skills in the same module as market-research:

| Skill | Purpose | Local Path |
|-------|---------|------------|
| deep-research | Deeper research workflows with iterative depth | `skills/deep-research/` |
| research-ops | Research operations and management | `skills/research-ops/` |
| investor-materials | Investor presentation generation | `skills/investor-materials/` |
| investor-outreach | Investor communication templates | `skills/investor-outreach/` |
| lead-intelligence | Lead research and qualification | `skills/lead-intelligence/` |
| seo | SEO audit and strategy | `skills/seo/` |
| content-engine | Content strategy workflows | `skills/content-engine/` |
| brand-voice | Brand tone and voice standardization | `skills/brand-voice/` |

## Using ECC Skills with This Hermes Skill

The ecc-market-research skill can be combined with other ECC skills for a complete research-to-delivery pipeline:

```markdown
1. ecc-market-research → produce research report
2. (ECC) investor-materials → convert report into investor deck
3. (ECC) brand-voice → polish external-facing version
```

## Limitations

- All ECC skills are pure Prompt templates — no live API data source binding
- For production market research, recommend supplementing with: Crunchbase, Brave Search API, Statista, or Gartner
- Hermes Skill import only captures the SKILL.md; for full ECC features (hooks, agents, commands), use the ECC installer directly on a supported harness
