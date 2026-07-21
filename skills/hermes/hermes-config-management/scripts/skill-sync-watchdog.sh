#!/bin/bash
# skill-sync-watchdog.sh — Sync new skills from shared dir to agent-specific dirs
#
# When one agent creates a new skill in ~/.agents/skills/, this script
# creates symlinks in each agent's local skills/ dir so both agents see it.
#
# Usage:
#   ./skill-sync-watchdog.sh                    # normal run
#   ./skill-sync-watchdog.sh --dry-run          # preview only
#   ./skill-sync-watchdog.sh --agents "hermes deepagent"  # custom agent dirs
#
# Install as cron job (every 5 min via Hermes cronjob tool):
#   cronjob action=create schedule="every 5m" \
#     prompt="Run ~/.hermes/scripts/skill-sync-watchdog.sh to sync shared skills" \
#     script=~/.hermes/scripts/skill-sync-watchdog.sh
#   or via launchd / systemd timer.

set -euo pipefail

SHARED_DIR="${HOME}/.agents/skills"
DRY_RUN=false

# Default agent skills dirs
declare -a AGENT_DIRS=(
  "${HOME}/.hermes/skills"
  "${HOME}/.deepagent/skills"
)

# Parse flags
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --agents=*)
      IFS=' ' read -ra CUSTOM_AGENTS <<< "${arg#--agents=}"
      AGENT_DIRS=()
      for agent in "${CUSTOM_AGENTS[@]}"; do
        AGENT_DIRS+=("${HOME}/.${agent}/skills")
      done
      ;;
  esac
done

if [ ! -d "$SHARED_DIR" ]; then
  echo "ERROR: Shared dir $SHARED_DIR does not exist"
  exit 1
fi

COUNT_CREATED=0
COUNT_EXISTING=0
COUNT_SKIPPED=0

for skill_dir in "$SHARED_DIR"/*/; do
  name=$(basename "$skill_dir")
  
  # Skip if not a valid skill directory (no SKILL.md)
  if [ ! -f "${skill_dir}/SKILL.md" ]; then
    continue
  fi
  
  # Skip superpowers (it's already symlinked from npm)
  if [ "$name" = "superpowers" ]; then
    continue
  fi
  
  for agent_dir in "${AGENT_DIRS[@]}"; do
    target="${agent_dir}/${name}"
    
    if [ -L "$target" ]; then
      # Symlink already exists — verify it points to the right place
      current_target=$(readlink "$target")
      if [ "$current_target" != "$skill_dir" ]; then
        echo "FIX: $target points to $current_target, should be $skill_dir"
        if [ "$DRY_RUN" = false ]; then
          rm "$target"
          ln -s "$skill_dir" "$target"
          ((COUNT_CREATED++))
        fi
      else
        ((COUNT_EXISTING++))
      fi
    elif [ -d "$target" ]; then
      # Real directory exists (probably pre-migration skill) — skip
      # User should manually migrate it to shared dir
      ((COUNT_SKIPPED++))
    else
      echo "CREATE: $target -> $skill_dir"
      if [ "$DRY_RUN" = false ]; then
        mkdir -p "$(dirname "$target")"
        ln -s "$skill_dir" "$target"
        ((COUNT_CREATED++))
      fi
    fi
  done
done

echo "---"
echo "Created: $COUNT_CREATED | Already synced: $COUNT_EXISTING | Skipped (real dir): $COUNT_SKIPPED"
if [ "$DRY_RUN" = true ]; then
  echo "(dry run — no changes made)"
fi
