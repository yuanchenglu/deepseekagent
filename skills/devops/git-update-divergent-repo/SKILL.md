---
name: git-update-divergent-repo
description: Update a git repository that has divergent/unrelated history from its remote, with local customizations to preserve. Covers shallow fetch workarounds, branch surgery, and careful re-application of patches.
---

# Git: Update Repo with Divergent History + Local Customizations

## When to Use

- `git pull` fails with "refusing to merge unrelated histories"
- Local and remote branches diverged with no common ancestor (e.g., repo was set up from tarball/zip, not cloned)
- Full `git fetch` times out (large repo in China/slow network)
- Repo has local customizations that need to survive the update

## Step 1: Fetch the Remote

If full fetch times out, use shallow fetch:

```bash
# Shallow fetch (fast, gets just the tip)
git fetch --depth 1 origin main

# Deepen to get more history for merge context
git fetch --deepen=500 origin main
```

If shallow fetch also times out:
```bash
# Test SSH connectivity first
ssh -T -o ConnectTimeout=5 git@github.com

# Try with longer timeout
timeout 300 git fetch --depth 1 origin main
```

## Step 2: Handle Unrelated Histories

If `git pull --allow-unrelated-histories` fails or is undesirable:

```bash
# Create a temp branch tracking origin/main
git checkout -b temp-new origin/main

# Delete the old main branch
# If git branch -D times out (large branch), use:
git update-ref -d refs/heads/main

# Rename temp-new to main
git branch -m temp-new main
```

> **Note**: `git update-ref -d refs/heads/main` is faster than `git branch -D main` for branches with many commits.

## Revert + Merge Pattern (Undo a Custom Feature, Keep Unrelated Patches)

When you have a single custom commit on top of upstream that you want to remove, but you also have unrelated bug-fix patches to preserve:

### Step 1: Stash unrelated changes

Before reverting, save any bug fixes that are NOT part of the custom feature:

```bash
git stash push -m "description" -- <path/to/files>
```

### Step 2: Revert the custom commit in-place

Instead of `git reset --hard` (which loses the commit from history), use `git revert --no-commit`:

```bash
git revert --no-commit HEAD
```

This produces the **inverse** patch of HEAD's changes in the working tree — it's a clean undo without losing history.

Then commit the revert:
```bash
git commit -m "revert: remove <feature-name> — reverting to upstream behavior"
```

**Why not `git reset --hard <upstream>`?** 
- `git reset --hard` is destructive and may be blocked by terminal safety guards.
- `revert --no-commit` preserves the history (useful for audit trails) and is non-destructive.
- If the terminal has safety protections, `revert` passes through while `reset --hard` gets blocked.

### Step 3: Merge upstream

```bash
git merge upstream/main --no-edit
```

This incorporates all upstream commits since the fork point. Because the revert in step 2 is a clean inverse of the custom commit, the merge should be conflict-free.

### Step 4: Restore unrelated patches

```bash
git stash pop
```

The stash was based on the original custom code, but the revert+merge produced the same file context (upstream's version), so the stash should apply cleanly.

### Step 5: Verify

```bash
git log --oneline -5
# Should show: merge commit, revert commit, upstream commits

# Check the custom feature is gone
grep -r "custom-feature-pattern" path/to/relevant/files  # should not find

# Check the bug fixes are still there
grep -n "distinctive-pattern-from-fix" path/to/file  # should find
```

### When to use this pattern vs alternatives

| Scenario | Approach |
|----------|----------|
| Single custom commit to undo, unrelated fixes to keep | **Revert + Merge (this pattern)** |
| Multiple divergent customizations, no common ancestor | See "Step 2: Handle Unrelated Histories" above |
| All local changes should be discarded | `git reset --hard upstream/main` |
| Temporary experimentation, might re-apply later | `git stash` the custom commit, merge upstream, assess 

When the old code had local patches that upstream may have partially or fully addressed:

### 3a. First, save local changes with stash
```bash
git stash push -m "description" -- <files>
```

### 3b. After updating, try to apply stash
```bash
git stash pop stash@{0}
```

### 3c. If conflicts arise, DON'T blindly take --theirs or --ours
The stash may be based on an **older version** of the files. Upstream may have:
- Already implemented the same features (differently)
- Refactored the code around the stashed changes
- Split methods into different places

**Better approach**: 
1. Restore to HEAD (upstream clean version):
   ```bash
   git restore --staged <files> && git checkout -- <files>
   ```
2. Read the stash diff to understand what the customizations did:
   ```bash
   git stash show -p stash@{0}
   ```
3. Check if upstream already has equivalent functionality (grep for key patterns)
4. Manually re-apply only the changes that upstream doesn't already have, using `patch` tool
5. Drop the obsolete stash

### 3d. Stash pop merge semantics (for reference)
During `git stash pop` conflict resolution:
- `--ours` = current branch (new upstream)
- `--theirs` = stash (your old customizations)

But this is context-dependent — always verify the result visually.

## Step 4: Verify

```bash
# Check current commit matches remote
git log --oneline -1

# Verify local customizations are present
grep -n "your-distinctive-pattern" <file>

# Check for cleanup
git stash list  # should be empty
git branch      # should only have main (no temp-* branches)
```

## Pitfalls

- **git branch -D can hang** on repos with large commit history — use `git update-ref -d refs/heads/<name>` instead
- **Don't assume stash applies cleanly** — upstream code often evolves significantly; always check if upstream already implements what your patch did
- **Line numbers shift** when upstream has new code — search by method name, not line number
- **Shallow fetches create disconnected history** — always `--deepen` after a `--depth 1` fetch before attempting merge
- **If all else fails: fresh repo workaround** — when `did not receive expected object` blocks push, the git history has a corrupted/missing object referenced by a shallow clone boundary. Don't try to fix the history. Instead: `git init` a new repo, copy all source files (excluding `.git`), single commit, `push --force`. See `openmaic-deployment` skill for the exact recipe.
- The current branch can't be force-deleted; you must be on a different branch first
