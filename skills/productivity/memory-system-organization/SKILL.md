---
name: memory-system-organization
description: "Organize and maintain Hermes Agent's memory system: classify content across SOUL/MEMORY/USER/Skills/Nested MD/.env layers to keep the model performing well."
version: 1.0.0
tags: [memory, organization, system-design, performance, hermes]
---

# Memory System Organization

> This skill captures the methodology for keeping Hermes Agent's persistent memory effective and lean. The core insight: **memory length has a direct, measurable impact on model performance** — a bloated memory (approaching 10K chars) causes context decay, hallucinations, and failure to follow loaded skills. Keeping memory under 2K chars restores original capability.

---

## Root Cause

Hermes' built-in `memory` tool injects **all** stored content into every turn's system prompt. When memory grows toward its 10K char limit:

- The model's attention is diluted across irrelevant entries
- Key operational rules get buried by stale procedural notes
- Skill instructions (loaded via `skill_view`) compete with conflicting memory entries
- The model becomes less responsive to in-session corrections

**Evidence pattern**: User reports "you were smarter 2 weeks ago with the same model" — the difference is memory length, not model capability.

---

## The 5-Layer Architecture

```
Layer 0: SOUL.md          ~2-3KB    Core identity, never changes
Layer 1: USER.md           ~2KB      User profile, rarely changes
Layer 2: MEMORY (memory)   ~2KB      Active operational rules
Layer 3: Skills                     Workflow procedures
Layer 4: Nested MD files            Reference data (no plaintext secrets)
Layer 5: .env                       Plaintext credentials
```

### Layer 0: SOUL.md (`~/.hermes/SOUL.md`)

**What goes here**: Everything that defines who the agent IS — core identity, cognitive framework, methodological principles. Content that should never change.

**Typical content**:
- Role definition ("I am the user's digital twin CEO")
- Cognitive framework (3-layer value system)
- Methodological rules (first principles, step-by-step, evidence-backed)
- Communication methodology
- Core insights about the user's domain
- Token discipline and execution flow

**Sizing**: 2-3KB. If SOUL.md exceeds 5KB, some content belongs in USER.md or a skill.

**Loading mechanism**: If Hermes supports `system_prompt.additions`, copy the SOUL.md essence there. Otherwise, load manually at session start. SOUL.md content should be treated as non-compressible — the cognitive framework section must survive context compression.

### Layer 1: USER.md (`memory target=user`)

**What goes here**: Who the user is — preferences, identity, style, communication patterns.

**Typical content**:
- Name preference ("Xiao Lu", not formal titles)
- Communication style preference
- Technical background (non-technical, product manager persona)
- Decision-making authority ("you decide when you can")
- Work style (action-oriented, prefers directness)

**Sizing**: Under 2KB. User preferences are compact.

**Principle**: User feedback about style/format/approach goes here OR in the relevant skill's SKILL.md, but not in the operational memory layer.

### Layer 2: MEMORY (`memory target=memory` or `memories/MEMORY.md`)

**What goes here**: Active operational rules that change week-to-week. The highest-signal, most-frequently-needed content.

**Navigation format (用户验证过的结构)**:
MEMORY 不是平铺清单，而是**分类导航索引**。每一条都是指向 skill 或 memories/*.md 的指针，详情按需加载：

```
# MEMORY 导航索引

## 生产管线
- **产研流程** → PRD→审计→OpenCode→OMO→截图→交付
- **三步走** → skill:wechat-three-step-publishing

## 文档规范
- **文档语言** → 代码注释/Spec优先简体中文
- **Commit** → 英文标题在前，简体中文正文在后
- **验证** → 截图留证，真实浏览器验收 ✅/❌/⚠️

## 参考
- **机器配置** → memories/machine-configs.md
- **Cloudflare** → memories/cloudflare-ref.md
```

**格式规则**：\n- `## 类别名` — 二级标题分 4 个域（生产管线/文档规范/运维规范/参考）\n- `- **条目名** → 指针` — 每个条目明确写 `→ skill:xxx` 或 `→ memories/xxx.md`\n- 指针让 Agent 知道**去哪找**详情，不在 MEMORY 本身装内容\n- **总字符 ≤2000**（不是每条 ≤200）

**Typical content**:
- Active project constraints and conventions
- Frequently used command/service ports/configs
- Workflow rules (process iron laws)  
- Verification standards
- Cross-reference pointers to nested MD or skills

**Sizing**: Hard cap at **2000 characters**. This is the most critical constraint — exceeding 2K causes measurable performance degradation in models like DeepSeek V4 Flash.

**Maintenance rule**: When memory approaches 1800 chars, initiate a consolidation pass:
1. Identify entries that are stale (rules from 2+ weeks ago, completed project configs)
2. Move reference data to nested MD files
3. Check if any rule is already covered by a skill — if so, remove from memory
4. Confirm the final count is under 2K

### Layer 3: Skills (`~/.hermes/skills/`)

**What goes here**: Reusable workflow procedures — step-by-step processes, template formats, decision trees. Anything that has a repeatable sequence of steps belongs here, not in memory.

**Key distinction from Nested MD**:
```
Skill (.md with YAML frontmatter) = "how to do X" with steps, templates, pitfalls
Nested MD (.md without frontmatter) = "what is X" — reference data, static facts
```

**When memory-adjacent info fits better in a skill**:
- Scoring format rules → belongs in `fangzhou-evaluation`, not memory
- Task list generation rules → belongs in `fangzhou-testing-guide`, not memory
- Fangzhou platform constraints → belongs in `fangzhou-benchmark-prep`, not memory

**Health check signal**: If memory contains a lengthy procedural rule ("do X then Y then Z"), it should probably be in a skill instead.

### Layer 4: Nested MD (`~/.hermes/memories/*.md`)

**What goes here**: Reference data that is consulted occasionally — machine configs, domain mappings, historical lesson records.

**Critical rule**: References to sensitive credentials use `$ENV_VAR_NAME` placeholders, never plaintext.

**File structure**:
```
~/.hermes/memories/
  cloudflare-ref.md        Zone IDs, tunnel mappings, env var references
  machine-configs.md       IPs, ports, services per machine
  feedback-lessons.md      Historical user corrections (patterns, not single events)
```

**When to use**: Any memory entry that:
- Is longer than 500 chars of reference material
- Contains static configuration data
- Is only needed 1-2 times per week
- Documents a lesson from a past session

### Layer 5: `.env` (`~/.hermes/.env` or `~/.hermes/env/*.env`)

**What goes here**: Plaintext credentials, API keys, tokens. Never store these in any Markdown file — even with restrictive file permissions.

**Pattern**: The nested MD files reference `$ENV_VAR_NAME` that the `.env` file defines.

---

## Cross-Machine Sync

When running Hermes on multiple machines (e.g., AIPC + MacBook Air as identical twins with daily sync):

**Approach**: LLM-driven cron sync (see `digital-twin-architecture` skill for full design) — not blind rsync. The agent reads both sides, compares, decides merge strategy, writes back.

**What to sync** | **Direction** | **Merge Strategy**
---|---|---
SOUL.md | AIPC → MacBook | AIPC version (master priority)
MEMORY.md | Bidirectional merge | Combine unique category entries from both sides
USER.md | Bidirectional merge | Combine unique §-separated entries
memories/*.md | Bidirectional merge | Richer version wins (more lines = more content)
Skills/ | AIPC → MacBook | AIPC version priority, fill missing on other side
.env | **DO NOT SYNC** | Each machine has its own credentials
config.yaml | **DO NOT SYNC** | Different providers/ports per machine

---

## Relationship with Memory Plugins

Hermes supports pluggable memory providers via `memory.provider` config:

| Provider | Behavior |
|----------|----------|
| `builtin` (default) | Directly reads/writes MEMORY.md + USER.md. This skill's methodology applies directly. |
| `memtensor` (MemOS) | Uses a Node.js bridge with L1/L2/L3 layered memory. The file-based MEMORY.md still exists as a fallback representation. The 5-layer taxonomy remains valid; MemOS adds sub-layers within what this skill calls Layer 2. |
| `honcho`, `mem0`, etc. | External memory stores. The 5-layer mental model still applies for what goes where in the Hermes ecosystem. |

**Key insight**: Advanced memory plugins (MemOS L3 world model, etc.) are strategic additions that coexist with the 5-layer architecture, not replacements for it. The SOUL/USER/MEMORY distinction remains relevant regardless of backend.

---

## Common Pitfalls

1. **Memory as default dumping ground**: Every new rule, preference, config, or lesson goes into `memory()` → 9700 chars → performance death. **Rule of thumb**: if it's not needed EVERY turn, it doesn't belong in memory.

2. **Duplicating skill content in memory**: A rule like "TST format for fangzhou scoring" that exists in `fangzhou-evaluation` skill does NOT also need to be in memory. Loading the skill injects the rule. Memory duplication makes both sources less reliable.

3. **Mixing user profile into operational memory**: "User prefers X" belongs in USER.md, not memory. If the preference changes, update USER.md — don't add a contradictory entry to memory.

4. **Over-relying on memory corrections**: When the user corrects your style/format, the fix belongs in the RELEVANT SKILL (or USER.md for general style), not in memory. Memory should contain the pointer ("see skill X for formatting rules"), not the full rule.

5. **Conflicting signal sources**: If a fangzhou scoring rule exists in both memory AND `fangzhou-evaluation` skill, they will eventually diverge. Memory should have a lightweight pointer: "Scoring format → see fangzhou-evaluation skill."

7. **Losing value during memory reduction**: When a 15KB memory is reduced to 1.4KB, routing aliases ("三步走"→skill:xxx), platform constraints, and user-style details may be lost. Always check old MEMORY.md.bak files first. Extraction methodology: see `digital-twin-architecture` skill → "1b1. 备份提取方法论".

8. **User preference vs environment fact confusion**: A user saying "don't use Chinese" in a specific project context is a per-task instruction, not a durable memory entry. Distinguish: style/format/workflow preference → SKILL.md; who the user is → USER.md; environment facts → memories/*.md; active rules → MEMORY.md.

---

## Consolidation Pass Checklist

When initiating a memory consolidation (triggered by memory approaching 2K or user reporting quality degradation):

```\n☐ Read current memory (system prompt or memory() tool)\n☐ Before deleting, check backups: `ls MEMORY.md.bak.*` — extract routing aliases not yet in current memory\n☐ Classify each entry:\n  → SOUL material? → Move to SOUL.md\n  → User preference/identity? → Move to USER.md\n  → Static reference data? → Move to nested MD, use $VAR_NAME for secrets\n  → Workflow procedure? → Check if skill covers it; update skill if needed\n  → Legitimate active rule? → Keep in memory (trim to <200 chars per entry)\n  → Stale or completed? → Delete\n☐ Calculate new total: target < 2000 chars\n☐ Verify skills that reference the removed entries still work\n☐ If multiple machines: sync after consolidation\n```

---

## References

- **Cognitive loop framework**: See `the-agency` skill → `references/cognitive-workflow.md` for the meta-level task approach that complements memory hygiene
- **Hermes memory docs**: `hermes memory status` / `hermes config env-path` for memory provider configuration
- **SOUL.md convention**: `~/.hermes/SOUL.md` — core identity file
- **Fangzhou memory-to-skill migration pattern**: See `fangzhou-testing-guide`, `fangzhou-evaluation`, `fangzhou-benchmark-prep` skills
