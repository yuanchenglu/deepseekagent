---
name: hermes-source-install
description: Manage Hermes Agent installed from Git source — update safely without losing local patches.
version: 1.0.0
tags: [hermes, source-install, git-update, patches, maintenance]
---

# Hermes Source Install Management

Workflow for managing a Hermes Agent installation that lives under Git source control (`~/.hermes/hermes-agent/`), as opposed to npm/pip package installs. This covers safe update, local-patch preservation, and post-update verification.

## When to Use

- User asks to update Hermes and it's installed from git (detected via `hermes --version` showing a git hash or `Project: /home/.../hermes-agent`)
- User has local modifications to Hermes source code (`feishu.py`, `run.py`, or other patches)
- After updating, a feature that worked before breaks (especially Feishu group messages, model routing)
- User's Hermes shows `git diff` output (active local changes)

## Detection

Check if Hermes is source-installed:

```bash
# Python venv-based (pip -e install):
hermes --version | grep "Project:"   # shows source path
ls ~/.hermes/hermes-agent/.git/      # git repo present

# Or check via:
cd ~/.hermes/hermes-agent && git log --oneline -1
```

## CRITICAL: Before Any Update

**ALWAYS check for local modifications first:**

```bash
cd ~/.hermes/hermes-agent

# Check for uncommitted changes
git diff --stat

# Check for stashed changes
git stash list

# See what's modified
git status
```

If there are local changes, you MUST preserve them. The most reliable approach:

```bash
# OPTION A: Create a branch (RECOMMENDED)
git checkout -b my-patches

# OPTION B: Read the diff output to know what you'll restore later
git diff > ~/hermes-local-patches.diff
```

## Safe Update Workflow

### Step 1: Survey Current State

```bash
cd ~/.hermes/hermes-agent

# Current version
git log --oneline -1

# Remote info
git remote -v

# Local changes
git diff --stat
git stash list
```

### Step 2: Capture Local Patches

```bash
# Create a backup branch of current state (with patches)
git stash push -m "auto-update-backup-$(date +%Y%m%d_%H%M%S)"
# Or create a branch:
git checkout -b pre-update-patches
git checkout main  # go back to main after branching
```

### Step 3: Fetch and Checkout New Version

```bash
git fetch upstream --tags  # or git fetch origin --tags
git tag -l "v*" --sort=-v:refname | head -5  # see latest tags

# Checkout the new tag (this creates detached HEAD)
git checkout <newest-tag>
```

### Step 4: Restore Local Patches

```bash
# If you used stash (DANGER: git stash pop may conflict)
git stash pop

# If you made a branch
git cherry-pick <patch-commit-hash>

# If you saved a diff
git apply ~/hermes-local-patches.diff

# Verify
git diff --stat  # should show your patches on top of new version
hermes --version  # should show new version
```

### Step 5: Restart Gateways

**Linux (systemd)**:
```bash
# Restart all profile-specific gateways
systemctl --user restart hermes-gateway.service
systemctl --user restart hermes-gateway-cto.service   # if exists
systemctl --user restart hermes-gateway-yunying.service
systemctl --user restart hermes-gateway-course-designer.service
systemctl --user restart hermes-web-ui.service

# Verify
systemctl --user status hermes-gateway-cto.service | head -5
```

**macOS (no systemd — gateway runs directly)**:
```bash
# Kill the existing gateway process
pkill -f "hermes_cli.main gateway run"

# Restart (the TUI or launch agent auto-restarts; if not, run manually:)
hermes gateway
```

**Verify process picked up new code** — check the gateway start time vs commit time:
```bash
# Gateway start time
ps aux | grep "hermes_cli.main gateway run" | grep -v grep

# Latest commit time for the changed file
cd ~/.hermes/hermes-agent && git log -1 --format="%ai" -- <changed-file>
```

If gateway start time is BEFORE the commit time, the fix is NOT loaded — restart again.

### Step 6: Verify Connection

Check logs for Feishu WebSocket reconnection:

```bash
journalctl --user -u hermes-gateway-cto.service --since "1 minute ago" | grep -i feishu
# Expected: "[Lark] ... [INFO] connected to wss://msg-frontier.feishu.cn/..."
```

## Common Pitfalls

### ⚠️ Lost Local Patches After `git checkout`

**Symptom**: Feature that worked before update (Feishu group messages, group model defaults, thread reply handling) stops working. DM still works.

**Root cause**: `git checkout` of a new tag puts the repo in detached HEAD. If there were local uncommitted modifications on the original branch, `git stash` is needed before checkout — but `git stash pop` must be done AFTER checkout. If you forget, the patches are lost in the stash.

**Fix**: `git stash pop` to restore. If multiple stashes: `git stash list` then `git stash pop stash@{N}`.

### ⚠️ Git Stash Swallows Patches

**Symptom**: `git stash` runs silently, user doesn't know changes were removed.

**Prevention**: Always run `git diff --stat` BEFORE any stash/checkout operation. Show the user what's about to be saved. If there are modifications, announce them explicitly.

### ⚠️ Detached HEAD After Update

After `git checkout <tag>`, you're in detached HEAD. This is fine for running Hermes but confusing for further updates. To return to a branch:

```bash
git checkout -b my-patches  # create a branch from current position
```

### ⚠️ Restart ≠ Reload (Code cache pitfall)

The Python process caches code at startup. `git checkout` alone does NOT reload the gateway — you MUST restart the service.

**Linux**: `systemctl --user restart hermes-gateway-cto.service`
**macOS**: `pkill -f "hermes_cli.main gateway run"` then restart manually or via launch agent

The gateway can run for hours on old code. A patched source tree does NOT mean the running gateway is patched. Always restart, and verify via `journalctl` (Linux) or log files that the gateway reconnects after restart.

**Verification trick**: Compare gateway process start time vs your fix commit time:
```bash
ps aux | grep "gateway run" | grep -v grep    # gateway start time
git log -1 --format="%ai" HEAD                 # latest commit time
```
If gateway start < commit time, the fix is NOT loaded. Restart.

### ⚠️ Gateway Start→Stop→Start Loop

If a gateway starts and immediately stops (exit code 1), check:
1. The old process was mid-API-call and the new code can't reconnect
2. The new code has import errors or missing dependencies
3. Systemd auto-restarts — wait a few seconds for the next cycle

### ⚠️ Version Check Shows New Version but Code Didn't Change

If pip installed the package in editable mode (`pip install -e .`), `hermes --version` reads from the source tree. The version string changes immediately when you `git checkout` a new tag even without re-installing. Dependencies, however, only match the new version if you also run the install command.

### ⚠️ `pip install -e .` or `uv pip install -e .` May Fail

The venv may not have `pip` or `uv` installed (Hermes installer strips them). After a version bump with new dependencies:

```bash
# If uv is available at system level
cd ~/.hermes/hermes-agent && uv pip install -e .

# If neither pip nor uv is in venv, check if the existing installation
# is sufficient — often it is (Hermes is conservative with deps)
```

### ⚠️ Fix Committed Locally But Never Merged Upstream

**Symptom**: A bug was fixed and committed, user says "this was fixed before" — but the error is back after an update.

**Root cause**: The fix commit exists on a local/fork branch but was never merged into upstream `main`. After `git checkout <upstream-tag>` or `git pull upstream main`, the fix commit is no longer reachable from HEAD.

**Detection**:
```bash
# Check if a specific commit is on the current branch
git merge-base --is-ancestor <commit-hash> HEAD && echo "on branch" || echo "NOT on branch"

# Check which branches contain the commit
git branch -a --contains <commit-hash>

# If the commit is only on remotes/fork/* but not on origin/main or upstream/main,
# the fix was never merged and was lost on update.
```

**Prevention**:
1. After committing a fix locally, verify it's on the correct upstream branch BEFORE updating
2. If you have a fork with important fixes, push them as PRs or keep a patch branch
3. Before `git checkout <tag>`, run `git diff --stat main..<fix-branch>` to see what would be lost

## Related References

- `references/feishu-group-admission-patch.md` — Concrete example of a local patch that was lost during a source update. Documents the exact diff, how to verify it's active, and how to reapply it. This is a reference-level artifact; the general workflow lives in this SKILL.md.
- `references/xiaomi-opencodego-vision-fix.md` — Case study: fix for Xiaomi MiMo "text is not set" 400 error committed to fork but never merged upstream, causing regression after source update. Documents the exact fix, the diagnostic, and the verification commands.

## Verification Checklist

After update + restart:

- [ ] `hermes --version` shows the new version
- [ ] `git diff --stat` shows your local patches still present
- [ ] `systemctl --user is-active hermes-gateway-cto.service` → `active`
- [ ] Feishu WebSocket connected (`journalctl | grep "connected to wss"`)
- [ ] DM works (send a private message to the bot)
- [ ] Group messages work (at-mention or DM-to-group, whichever was patched)
- [ ] Group model overrides work (if you have `group_model_defaults`)
