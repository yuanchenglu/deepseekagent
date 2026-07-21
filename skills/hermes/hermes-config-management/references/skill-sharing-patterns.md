# Skill Sharing Across Hermes-Based Agents

## Session Context

Discovered during a migration from ~/.hermes to ~/.deepagent (a Hermes fork). The goal was to share skills across both agents without duplicating files or modifying fork source code.

## Key Findings

### 1. Industry Standard: `~/.agents/skills/`

GitHub CLI v2.93+ (`gh skill install`) uses this as the default location for `--scope project`. Multiple agents (Copilot, Cursor, Codex, Gemini CLI, OpenCode) share this directory. This is the ecosystem's converged standard.

### 2. Hermes Source Code: external_dirs Mechanism

**File**: `agent/skill_utils.py` (in `~/.hermes/hermes-agent/`)

- `get_external_skills_dirs()` reads `skills.external_dirs` from `config.yaml`
- Each entry is expanded (tilde, env vars), resolved to absolute path
- Duplicates and paths matching the local `skills/` dir are skipped
- Results are cached in-process, keyed on `config.yaml` mtime
- `get_all_skills_dirs()` returns `[local_skills_dir, ...external_dirs]` — local always first

**File**: `agent/skill_utils.py` — `iter_skill_index_files()`

- Uses `os.walk(skills_dir, followlinks=True)` to find all `SKILL.md` files recursively
- Excludes: VCS dirs, virtualenvs, support dirs (references/templates/assets/scripts) when SKILL.md is present at the parent level
- Returns sorted paths relative to the skills directory

**File**: `hermes_cli/config.py`

- Comment on the external_dirs default: **"Read-only — skill creation always goes to ~/.hermes/skills/."**

**File**: `tools/skill_manager_tool.py` — `_resolve_skill_dir()`

- Always returns `SKILLS_DIR / name` or `SKILLS_DIR / category / name`
- `SKILLS_DIR = HERMES_HOME / "skills"`
- New skill creation cannot be redirected to external dirs via config

### 3. Skill Discovery

- `_find_skill(name)` searches ALL dirs (local + external) via `rglob("SKILL.md")`
- Returns the first match; local skills dir is always searched first
- `skill_manage(action='create')` refuses to create if name already exists in any dir

### 4. System-Bundled vs User-Developed

**Hermes source bundled skills** (72 skills):
`~/.hermes/hermes-agent/skills/` — categorized subdirectories (apple/, creative/, etc.)
These come with the Hermes installation.

**DeepAgent bundled skills** (79 skills):
`~/.deepagent/skills/` — categorized subdirectories with `.bundled_manifest` checksums
52 overlap with Hermes source; 27 are DeepAgent-specific.

**User skills**:
`~/.hermes/skills/` — flat directory structure, mixed sources (hub-installed, agent-created, manually added)

### 5. CC Switch Skill Management

**Settings** (from `~/.cc-switch/settings.json`):
- `"skillSyncMethod": "auto"` 
- `"skillStorageLocation": "cc_switch"`

**Database tables**:
- `skills` — per-skill metadata with per-agent enablement columns (`enabled_claude`, `enabled_codex`, `enabled_gemini`, `enabled_opencode`, `enabled_hermes`)
- `skill_repos` — GitHub repos as skill sources (`owner`, `name`, `branch`, `enabled`)

**Configured repos**:
- `anthropics/skills`
- `ComposioHQ/awesome-claude-skills`
- `cexll/myclaude`
- `JimLiu/baoyu-skills`

## Approach Comparison

| Approach | Read access | Write access | Auto-sync | Source code changes needed |
|----------|-------------|-------------|-----------|---------------------------|
| Pure external_dirs | Both agents | Only local dirs | No | No |
| external_dirs + symlinks | Both agents (via external_dirs) | Both agents (writes go through symlinks) | Manual for new skills | No |
| Above + watchdog cron | Both agents | Both agents + auto for new skills | Yes (every 5 min) | No |
| Symlink whole skills/ dir | Both agents | Both agents to shared dir | Yes (all writes go to shared dir) | No (but needs merging all skills flat) |
| Modify source code | Both agents | Configurable | N/A | Yes (not recommended) |

## Recommended Setup

```yaml
# ~/.hermes/config.yaml (and ~/.deepagent/config.yaml)
skills:
  external_dirs:
  - ~/.agents/skills
  - ~/.agents/skills/superpowers
```

Plus: symlink each user skill in each agent's local `skills/` dir → `~/.agents/skills/<name>/`.

Plus: watchdog cron job for auto-sync of newly created skills.

## Pitfalls

1. **Duplicates in external_dirs**: If a skill exists in both local and external dirs, the local copy takes precedence (searched first). Remove local copies after migrating to shared dir.
2. **Re-installing bundled skills**: When updating an agent, don't overwrite user symlinks in the skills/ dir. The `external_dirs` config persists across updates.
3. **Case sensitivity**: Agent names in symlinks and config are case-sensitive on macOS (APFS is case-insensitive by default but Hermes resolves paths).
4. **`skill_manage(action='create')` writes locally** — always check if you intended to create in shared dir instead, then move and symlink.
6. **.bundled_manifest in DeepAgent**: Contains MD5 hashes of each bundled skill. Used for integrity checking, not discovery. Don't modify.

## Migration Workflow (Real Session)

Actual steps executed on 2026-06-30 to migrate 323 skills from `~/.hermes/skills/` to `~/.agents/skills/`:

### Step 1: Identify what to migrate

```bash
# Count all skills
find ~/.hermes/skills -name "SKILL.md" | wc -l

# Find which are system-bundled duplicates
find ~/.hermes/hermes-agent/skills -name "SKILL.md" | while read f; do
  basename "$(dirname "$f")"
done | sort -u > /tmp/system_skills.txt

find ~/.hermes/skills -name "SKILL.md" | while read f; do
  basename "$(dirname "$f")"
done | sort -u > /tmp/user_skills.txt

# Overlap count
comm -12 /tmp/system_skills.txt /tmp/user_skills.txt | wc -l
# True user skills (not in system source)
comm -13 /tmp/system_skills.txt /tmp/user_skills.txt | wc -l
```

### Step 2: Clean shared dir duplicates

```bash
# Remove stale copies in shared dir before migration
for d in ~/.agents/skills/lark-*/; do
  name=$(basename "$d")
  [ -d ~/.hermes/skills/"$name" ] && rm -rf "$d"
done
```

### Step 3: Move to shared + symlink back

```bash
cd ~/.hermes/skills
find . -name "SKILL.md" | while read f; do
  skill_dir=$(dirname "$f")
  name=$(basename "$skill_dir")
  mv "$skill_dir" "$HOME/.agents/skills/$name"
  ln -s "$HOME/.agents/skills/$name" "$skill_dir"
done
```

### Step 4: Symlink in secondary agent

```bash
SHARED="$HOME/.agents/skills"
DA_DIR="$HOME/.deepagent/skills"
for d in "$SHARED"/*/; do
  name=$(basename "$d"); [ -f "$d/SKILL.md" ] || continue
  if [ -e "$DA_DIR/$name" ] && [ ! -L "$DA_DIR/$name" ]; then
    # System-bundled — skip
    find "$DA_DIR" -name "SKILL.md" -exec grep -l "^name: $name" {} \; 2>/dev/null | head -1 && continue
  fi
  ln -sf "$d" "$DA_DIR/$name"
done
```

### Step 5: Verify

```bash
find -L ~/.hermes/skills -name "SKILL.md" | wc -l
find -L ~/.deepagent/skills -name "SKILL.md" ! -path "*/index-cache/*" | wc -l
grep -A2 'external_dirs:' ~/.hermes/config.yaml
grep -A2 'external_dirs:' ~/.deepagent/config.yaml
```

### Step 6: Clean empty category dirs

```bash
cd ~/.hermes/skills
find . -maxdepth 3 -type l -xtype l -delete
for d in */; do
  [ -L "$d" ] && continue
  [ "$(find "$d" -type f ! -name '.*' 2>/dev/null | wc -l)" -eq 0 ] && rm -rf "$d"
done
```

### Real results

| Metric | Value |
|--------|-------|
| Skills moved to shared | 321 |
| Hermes system-bundled (untouched) | 72 |
| DeepAgent system-bundled (untouched) | 79 |
| Symlinks in hermes skills/ | 354 |
| Symlinks in deepagent skills/ | 324 |
| Empty category dirs removed | 9 |

## `gh skill install` Reference (GitHub CLI v2.93+)

- `gh skill install <repo> <skill> --scope project` → `.agents/skills/` (shared by Copilot, Cursor, Codex, Gemini CLI, Claude Code, Antigravity, Amp, Cline, OpenCode, Warp)
- `gh skill install <repo> <skill> --scope user` → `~/.config/gh/skills/`
- `--dir <path>` for custom override
- Auto-discovery: `skills/*/SKILL.md` convention
- Version pinning: `skill@v1.2.0` or `--pin <sha>`
- Source tracking metadata injected into SKILL.md frontmatter
- `--from-local` for local directory install (copies, not symlinks)

## CC Switch Details (from real DB at `~/.cc-switch/cc-switch.db`)

| Table | Columns |
|-------|---------|
| `skills` | Per-skill metadata + per-agent toggles: `enabled_claude`, `enabled_codex`, `enabled_gemini`, `enabled_opencode`, `enabled_hermes` |
| `skill_repos` | `owner`, `name`, `branch`, `enabled` (repos: anthropics/skills, ComposioHQ/awesome-claude-skills, cexll/myclaude, JimLiu/baoyu-skills) |

CC Switch approach: repo-based central catalog, per-agent toggles, DB-backed metadata. Converges on same principle as Hermes external_dirs: single source of truth, per-agent visibility control.

## Source File Locations

| File | What it shows |
|------|--------------|
| `agent/skill_utils.py` | `get_external_skills_dirs()`, `get_all_skills_dirs()`, `iter_skill_index_files()`, `_find_skill()` |
| `tools/skill_manager_tool.py` | `_resolve_skill_dir()`, `_create_skill()`, `_find_skill()`, `SKILLS_DIR` |
| `hermes_cli/config.py` | `DEFAULT_CONFIG` — `"external_dirs": []` with "Read-only" comment |
| `tests/agent/test_external_skills.py` | Tests confirming external dirs behavior |
