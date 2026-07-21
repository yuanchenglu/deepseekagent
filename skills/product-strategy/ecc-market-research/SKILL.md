---
name: ecc-market-research
description: Conduct market research, competitive analysis, investor due diligence, and industry intelligence with source attribution and decision-oriented summaries. Originates from ECC (Everything Claude Code) by affaan-m — 182K+ stars.
version: 2.0.0-rc.1
author: affaan-m (ECC) + Hermes Agent adaptation
origin: https://github.com/affaan-m/ECC/skills/market-research
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [market-research, business, competitive-analysis, investor-diligence, ecc]
---

# Market Research

> 源自 ECC (Everything Claude Code) — GitHub 182K+ Stars 的跨框架 Agent 技能系统  
> 该技能已克隆至 ~/Code/ECC/skills/market-research/

Produce research that supports decisions, not research theater.

## When to Activate

- researching a market, category, company, investor, or technology trend
- building TAM/SAM/SOM estimates
- comparing competitors or adjacent products
- preparing investor dossiers before outreach
- pressure-testing a thesis before building, funding, or entering a market

## Research Standards

1. Every important claim needs a source.
2. Prefer recent data and call out stale data.
3. Include contrarian evidence and downside cases.
4. Translate findings into a decision, not just a summary.
5. Separate fact, inference, and recommendation clearly.

## Common Research Modes

### Investor / Fund Diligence
Collect:
- fund size, stage, and typical check size
- relevant portfolio companies
- public thesis and recent activity
- reasons the fund is or is not a fit
- any obvious red flags or mismatches

### Competitive Analysis
Collect:
- product reality, not marketing copy
- funding and investor history if public
- traction metrics if public
- distribution and pricing clues
- strengths, weaknesses, and positioning gaps

### Market Sizing
Use:
- top-down estimates from reports or public datasets
- bottom-up sanity checks from realistic customer acquisition assumptions
- explicit assumptions for every leap in logic

### Technology / Vendor Research
Collect:
- how it works
- trade-offs and adoption signals
- integration complexity
- lock-in, security, compliance, and operational risk

## Output Format

Default structure:
1. executive summary
2. key findings
3. implications
4. risks and caveats
5. recommendation
6. sources

## Quality Gate

Before delivering:
- all numbers are sourced or labeled as estimates
- old data is flagged
- the recommendation follows from the evidence
- risks and counterarguments are included
- the output makes a decision easier

## Related ECC Skills

The following complementary skills exist in the ECC ecosystem (~/Code/ECC/skills/):

| Skill | File | Purpose |
|-------|------|---------|
| deep-research | skills/deep-research/ | Deeper research workflows |
| research-ops | skills/research-ops/ | Research operations |
| investor-materials | skills/investor-materials/ | Investor presentations |
| investor-outreach | skills/investor-outreach/ | Investor communications |
| lead-intelligence | skills/lead-intelligence/ | Lead research |
| seo | skills/seo/ | SEO and visibility |
| content-engine | skills/content-engine/ | Content strategy |
| brand-voice | skills/brand-voice/ | Brand tone standards |

> See `references/ecc-ecosystem-overview.md` for the full ECC ecosystem structure, skill categories, and local installation details.
