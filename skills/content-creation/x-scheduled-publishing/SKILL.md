---
name: x-scheduled-publishing
description: "Set up automated, scheduled content publishing to X (Twitter) via xurl OAuth + Hermes cron jobs. Covers Developer App creation, OAuth PKCE setup, content strategy, and cron job configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [xurl]
  skills: [xurl]
metadata:
  hermes:
    tags: [x, twitter, social-media, publishing, cron, automation]
---

# X Scheduled Publishing — Automated Content Pipeline

Use this skill to set up a fully automated pipeline for publishing content to an X (Twitter) account on a schedule via Hermes cron jobs. Covers the full lifecycle: Developer App creation, OAuth PKCE authentication, content strategy, and cron job configuration.

---

## When to Use

- User wants to **periodically post articles/content to X** from their own account
- Setting up an **autonomous content pipeline** driven by Hermes cron jobs
- **First-time X API setup** for a given account — OAuth, app registration, credential bootstrapping
- User says "定期发文章到 X", "auto-post to X", "schedule tweets"

---

## Critical Pitfall: Cloud Browser WILL NOT Work for X Login

**Do NOT attempt to log into X via the browser tools.** X's anti-bot detection aggressively blocks cloud/remote browser sessions. Symptoms:
- `We've temporarily limited your login` on email submit
- Blank pages with no interactive content after navigation
- `ERR_CONNECTION_CLOSED` on repeated attempts

**The ONLY reliable path is xurl OAuth PKCE on the user's LOCAL machine.** This means:
1. User creates the Developer App on their own browser (already logged in)
2. User gives you Client ID + Client Secret
3. You configure xurl via terminal on their local machine
4. OAuth flow opens a LOCAL browser window — user clicks "Authorize"

## Critical Pitfall: Browser Automation Is for Reading, Not Writing

**Browser automation tools (Playwright, CamoFox, Selenium) are the wrong tool for X posting.** They exist for scraping/reading — where X API is expensive or rate-limited. For posting, the X API (via `xurl`) is simpler, more reliable, and the correct engineering choice.

| | API (xurl) | Browser Automation (CamoFox/Playwright) |
|---|---|---|
| **Best for** | Posting, reading (low volume) | Reading at scale, authenticated scraping |
| **Reliability** | High — official protocol | Fragile — DOM selectors break on UI changes |
| **Detection risk** | None (official) | Cat-and-mouse — X updates detection, tool updates bypass |
| **Setup complexity** | OAuth PKCE (~5 min) | Browser server + cookie management + session maintenance |
| **ToS compliance** | ✅ | ⚠️ Against ToS |

**Decision rule**: Read = CamoFox. Write = xurl. Never mix them up.

---

## Step-by-Step Setup

### Step 1: Install xurl

```bash
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash
```

Verify: `xurl --help`

### Step 2: User Creates X Developer App

The user MUST do this on their own browser (not cloud browser). Direct them to:

1. Open https://developer.x.com/en/portal/dashboard
2. Navigate to **Projects & Apps** → click existing app or **"+ Add App"**
3. For new apps: set **redirect URI** to `http://localhost:8080/callback`
4. Under **Keys and Tokens**, copy **Client ID** and **Client Secret**
5. Give both to you

**Note:** If the Developer Platform asks for an application description during signup, use the template in `references/x-dev-app-application-template.md`.

### Step 3: Register App Locally

```bash
xurl auth apps add my-app --client-id CLIENT_ID --client-secret CLIENT_SECRET
```

### Step 4: OAuth Authentication

```bash
xurl auth oauth2 --app my-app bluth111
```

This opens a LOCAL browser. The user completes the OAuth consent screen. Then:

```bash
xurl auth default my-app
xurl whoami  # verify: should show the user's X profile
```

**Common pitfall:** If the user omits `--app my-app` from `xurl auth oauth2`, the token saves to the built-in `default` app profile (no client-id/secret). Commands will fail. Fix: re-run with `--app my-app`.

### Step 5: Test a Post

```bash
xurl post "Test post from xurl — setting up automated publishing pipeline."
```

Then delete it:
```bash
xurl delete POST_ID_FROM_OUTPUT
```

### Step 6: Create the Cron Job

Use `cronjob(action='create')` with a self-contained prompt. The cron job should:

1. Load the `xurl` skill for CLI commands
2. Have access to terminal (for xurl) and optionally web tools (for content generation)
3. Post content on the desired schedule

**Minimal example** — daily post of a tech insight:
```
prompt: "Post one original technical insight to X about AI/LLM agents. Keep it under 280 characters. Use xurl to post it. Make it insightful, not generic."
schedule: "0 10 * * *"  # daily at 10:00
skills: ["xurl"]
enabled_toolsets: ["terminal"]
```

**Content-pipeline example** — weekly, pulling from Obsidian:
```
prompt: "Find the most interesting recent article draft in ~/Documents/ObsidianVault. Write a compelling 1-2 sentence summary as an X post (under 280 chars). Include 2-3 relevant hashtags. Post it using xurl. Make it hook the reader."
schedule: "0 9 * * 1"  # every Monday at 9:00
skills: ["xurl", "obsidian"]
enabled_toolsets: ["terminal", "file"]
```

---

## Content Strategy Decisions (Clarify with User Before Creating Cron Job)

Before setting up the cron job, confirm:

| Question | Options |
|----------|---------|
| **Content source** | Obsidian vault, Feishu wiki, freshly generated by LLM, or curated from user's existing drafts |
| **Frequency** | Daily, 2-3x/week, weekly |
| **Time of day** | Morning (8-10 AM), afternoon, evening |
| **Content style** | Technical deep-dives, personal insights, article links+summary, or mixed |
| **Hashtags** | Which hashtags to use consistently (e.g., #AI #LLM #Agent) |
| **Character limit** | X free tier: 280 chars; X Premium: longer |

## Critical Pitfall: 280-Character Limit Enforcement

**NEVER eyeball character counts.** Twitter free tier: 280 chars total. Every URL counts as exactly 23 chars (t.co wrapping), regardless of actual length. The text portion must be ≤257 chars.

**Enforcement workflow:**
1. Write all tweets first
2. Run a verification script that computes `len(tweet_text) + 23` for each tweet
3. Flag and fix every tweet over 280
4. **Do NOT proceed to cron setup until all pass**
5. Average compressed tweet text is ~230-250 chars after prefix overhead (`LLM+Harness=Agent #NN — ` = ~27 chars)

**Real case**: 87/90 tweets failed 280-char check on first pass. Required 3 full rewrites with progressively more aggressive compression. Lesson: write shorter from the start; depth does not require length.

## Critical Pitfall: GitHub Branch (master vs main)

**Always verify the default branch** before linking. Never assume `main`. Ask the user or check the repo. Wrong branch → all links 404. This is a hard blocker for any publishing plan with GitHub links.

**Check**: `git ls-remote --symref <repo-url> HEAD` or ask user directly.

## Critical Pitfall: UTM Parameters Damage Credibility

**Never add `?utm_source=` or any UTM tracking parameters** to GitHub links in tweets. They signal AI-generated content to readers, damaging trust. Links must be clean: `github.com/user/repo/blob/master/path.md`.

## Bilingual Delivery (CN + EN)

When the user intends to publish on both X (English) and domestic Chinese platforms (小红书, 微信, 即刻), deliver tweets as **paired messages**: Chinese first, then English. Two separate messages per time slot. User copy-pastes CN to domestic platform, EN to X.

**Formula consistency**: Use the same formula in both languages. **Preferred format**: `#Agent=LLM+Harness #NN` — the `#Agent` prefix enters Twitter's Agent topic recommendation, which has significantly larger reach than `#LLM`. The formula has evolved through testing: `LLM=Harness=Agent` → `LLM+Harness=Agent` → `#Agent=LLM+Harness`. Always verify the current preferred format with the user.

**Content depth principle**: Both CN and EN versions must carry the same source-code-level depth. Translation must preserve specific data points (e.g., "50+ scenario instructions, only 20 wired into code"), not just general insights. Generic-sounding tweets that could apply to any project signal shallow content.

## Clean Message Delivery (No Metadata)

Cron-delivered messages must contain **ONLY the tweet text + link**. No "Cronjob Response" headers, no job IDs, no "To stop or manage this job" footers. The user copy-pastes directly — any metadata pollutes the copy buffer.

### Approach A: Agent-Based (unreliable, avoid)

Setting `deliver='local'` + using `send_message` inside the cron agent often fails because:
- Cron agents may not have the `send_message` tool available
- Failed silently — no error, no delivery, `last_delivery_error: null`

**Do not use this approach unless confirmed working for the specific setup.**

### Approach B: no_agent Script (reliable, preferred)

Use TWO separate cron jobs with `no_agent=true`, each running a Python script that outputs one tweet to stdout. Stdout is delivered verbatim to the target.

**Script** (`scripts/tweet-deliver.py`):
```python
#!/usr/bin/env python3
"""Output current tweet. Args: cn|en"""
import json, re, sys
from pathlib import Path

STATE = Path("~/.hermes/profiles/<profile>/cron/twitter-publish-state.json").expanduser()
PLAN = Path("~/Documents/article/<plan-file>.md").expanduser()
lang = sys.argv[1]  # "cn" or "en"

s = json.loads(STATE.read_text())
n = s["current_tweet"]
ns = f"{n:02d}"
plan = PLAN.read_text(encoding="utf-8")

tag = "【中文】" if lang == "cn" else "【English】"
m = re.search(rf"{tag}\n(#Agent=LLM\+Harness #{ns} — .+?)\n(github\.com/[\w/\-._]+)", plan)
if not m:
    print(f"Done!" if n > 90 else f"#{ns} not found")
    exit(0)

text, link = m.group(1), m.group(2)
is_reminder = s.get("last_sent_at") is not None

if is_reminder:
    print("⏰ 上一条还未发送，请先发布这条" if lang == "cn" else "⏰ Reminder: previous tweet not yet posted")
    print()

print(text)
print(link)
```

**Two cron jobs** (CN first, EN 1 minute later):
```python
cronjob(action='create', name='Tweet-CN', schedule='0 8,16,22 * * *',
        script='tweet-deliver.py cn', no_agent=True,
        deliver='feishu:oc_HOME_CHANNEL_ID', profile='<profile>')
cronjob(action='create', name='Tweet-EN', schedule='1 8,16,22 * * *',
        script='tweet-deliver.py en', no_agent=True,
        deliver='feishu:oc_HOME_CHANNEL_ID', profile='<profile>')
```

**Why this works**: no_agent scripts run the script, capture stdout, and deliver it verbatim to the target. No agent, no metadata wrappers, no send_message dependency. EMPTY stdout → SILENT (no delivery).

## Reminder as Separate Message

When re-sending an unconfirmed tweet, the reminder notice must be a **separate message**, not prepended to the tweet text:

```
Message 1: "⏰ 上一条还未发送，请先发布这条 / Reminder: previous tweet not yet posted"
Message 2: [CN tweet text + link]
Message 3: [EN tweet text + link]
```

**Anti-pattern**: `"⏰ Reminder: previous tweet not yet posted: #Agent=LLM+Harness #01 — text..."` — this pollutes the tweet text the user needs to copy.

## Sequential Confirmation Workflow (Feishu Fallback Mode)

When using manual publishing (no xurl API), implement a **state-file-based sequential delivery** with confirmation:

### State File

`~/.hermes/profiles/<profile>/cron/twitter-publish-state.json`:
```json
{
  "current_tweet": 1,
  "last_sent_at": null,
  "total_delivered": 0
}
```

### Cron Job Design

- **One cron job** with 3 daily triggers matching the time slots
- Cron job reads state → delivers tweet #N (CN + EN) → does NOT advance state
- **The interactive session** advances state when user replies "已发"
- If `last_sent_at` is not null → this is a **re-send reminder** for the same tweet

### Confirmation Flow

```
Cron triggers (time slot)
    ↓
Reads state → current_tweet = N
    ↓
If first delivery → sends tweet #N (CN + EN)
If re-send → sends with ⏰ reminder prefix
    ↓
User posts to X, replies "已发" in Feishu
    ↓
Interactive agent updates state: current_tweet = N+1, last_sent_at = null
    ↓
Next cron trigger → reads state → sends N+1
```

**Guarantee**: Series is linear. No skipping. If unconfirmed, same tweet re-sends every time slot until confirmed.

### Cron Job Prompt Template

```
Read state file at <state_path>. Read plan at <plan_path>.
Find tweet #N (both CN and EN). Output both as separate messages.
If last_sent_at is null → normal delivery. If not null → re-send with reminder prefix.
NEVER advance current_tweet. Only the interactive session does that.
```

### Cron Job Config

```python
cronjob(
    action='create',
    schedule='0 0,8,14 * * *',  # UTC → CST 08:00, 16:00, 22:00
    prompt='<self-contained prompt as above>',
    enabled_toolsets=['file'],
    profile='<profile-name>',
    deliver='origin'
)
```

## Timezone Calculation for CST Users

When the user is in China (UTC+8 / CST):

1. **Ask for their available manual-operation window** (e.g., "07:30-23:00 CST")
2. **Convert global Twitter peak times to CST:**
   - US East morning (UTC 12:00-14:00) → CST 20:00-22:00 ✅
   - Europe afternoon (UTC 14:00-16:00) → CST 22:00-00:00 ⚠️ borderline
   - US West morning (UTC 16:00-18:00) → CST 00:00-02:00 ❌ sleeping
   - US West afternoon (UTC 20:00-22:00) → CST 04:00-06:00 ❌ sleeping
3. **Filter to the user's window**, then pick 3 evenly-spaced slots

**Recommended for CST users:**
| CST | UTC | Coverage |
|-----|-----|----------|
| 08:00 | 00:00 | US evening (previous day) |
| 16:00 | 08:00 | Europe morning |
| 22:00 | 14:00 | US East morning + Europe afternoon (peak) |

**CRITICAL: Cron expressions are interpreted in LOCAL system time, not UTC.**
Use the user's LOCAL hours in the cron expression. For CST 08:00/16:00/22:00:
```
schedule="0 8,16,22 * * *"   # CST hours — CORRECT
```
Do NOT use UTC hours (`0 0,8,14 * * *`) — that fires at midnight/8am/2pm local time, completely wrong.
**Verified bug**: `0 0,8,14 * * *` fired at CST 00:00, 08:00, 14:00 instead of the intended 08:00, 16:00, 22:00.
Always sanity-check: `next_run_at` in cron output shows the actual local time of the next fire.

## Content Depth: The #1 Principle

When the audience is AI/ML engineers and researchers, **content depth is non-negotiable**. Every tweet must contain at least one of:

- **Source-code-level claim**: "Verified in OMO's source: 50+ scenario instructions, only 20 wired into code"
- **Specific data point**: "130% cost increase for ZERO quality gain"
- **Platform-specific knowledge**: "Hermes persists _cached_system_prompt to session DB"
- **Counterintuitive finding**: "Stronger Memory makes agents WORSE for divergent tasks"
- **Named methodology**: "Compression's 'fairness violence'"

**Anti-pattern**: Generic insight tweets that could apply to any agent project (e.g., "Feedback makes upgrades possible"). These signal shallow content and damage credibility with technical audiences.

**Validation**: After writing all tweets, run a depth check — search for specific platform names (Claude Code, Hermes, CodeWhale), specific numbers (50, 128K, 130%), and source-specific claims. If generic patterns dominate, rewrite.

---

## Verification Checklist

After setup:
- [ ] `xurl auth status` shows default app with valid oauth2 token
- [ ] `xurl whoami` returns the correct user profile
- [ ] Manual test post succeeds (`xurl post "test"`)
- [ ] Cron job is scheduled (`cronjob(action='list')` shows the job)
- [ ] Cron job has `xurl` in its skills list
- [ ] First scheduled run completes successfully

---

## Decision Tree: API vs Feishu Fallback

When `xurl post` returns `CreditsDepleted`, the X Developer account has $0 balance. The user has two options:

```
CreditsDepleted?
  ├─ User pays $5 → Continue with API cron job (xurl post)
  └─ User won't pay → Switch to Feishu Fallback Mode
```

**Feishu Fallback Mode** (preferred for risk-averse accounts):

Instead of auto-posting via xurl, create a **confirmation-based manual pipeline**:
1. Hermes cron reads content from a folder, formats it, sends via **Feishu DM**
2. User manually copy-pastes and publishes to X
3. User replies `1` or `已发` in Feishu → Hermes advances to next post
4. System NEVER skips unconfirmed posts (queue integrity)

**Why this is often better than API auto-posting:**
- Zero platform risk — X sees normal human publishing, no API origin signal
- No OAuth/API maintenance, no credit balance to manage
- Lower system complexity — only content generation + Feishu delivery + state tracking
- Trade-off: manual copy-paste step (5×/day)

**Full implementation details** in `references/feishu-fallback-implementation.md` — includes state machine design, cron job prompt template, directory layout, and the `HERMES_HOME` path resolution pitfall.

**Do NOT attempt workarounds**: Bearer Token is read-only, browser automation (Playwright) is blocked by X's bot detection on cloud IPs. There is no free API posting path.

---

## Critical Pitfall: Cron Agent Auto-Deliver to Feishu (99992402)

**Symptom**: Cron job shows `last_delivery_error: "delivery error: Feishu send failed: [99992402] field validation failed"`.

**Root cause**: The cron agent's final response text contains content that doesn't pass Feishu's message field validation. This happens when the agent outputs raw formatted text (multi-line, special characters, long content) as its auto-delivered final message.

**Fix**: Do NOT rely on auto-deliver. Instead, have the cron agent use `send_message` tool inside its execution to send messages directly to the Feishu target. The agent's final response becomes irrelevant — what matters is the `send_message` calls it makes during execution.

**Cron config for send_message approach**:
```python
cronjob(
    action='create',
    schedule='0 0,8,14 * * *',
    prompt='... use send_message to feishu:oc_XXXX to send CN then EN messages ...',
    enabled_toolsets=[],  # allow all tools (needs send_message)
    deliver='feishu:oc_XXXX'  # fallback, not primary delivery
)
```

**Verification**: After a successful run, `last_delivery_error` should be `null`. If the auto-deliver error persists but tweets arrived via send_message, the job is working — the auto-deliver error is cosmetic.

## State File Script

A reusable Python script for reading the state file + plan and extracting tweet text:
`scripts/twitter-publisher.py` — reads state JSON → finds tweet #N in plan (zero-padded) → outputs CN + EN text.

## Approach Selection: LLM-Driven vs Script-Based

**For data-driven content pipelines (like tweet delivery from a plan file), prefer `no_agent=false` (LLM-driven).** The LLM reads the plan file + state file and outputs the tweet directly. No script file to create, maintain, or debug.

| | `no_agent=false` (LLM-driven) | `no_agent=true` (Script-based) |
|---|---|---|
| **Setup** | Write a prompt, attach `file` toolset | Write a Python script, place in `scripts/`, debug regex |
| **Failure mode** | Agent reads file wrong → partial output | Script missing → `last_status: "error"`, zero delivery |
| **Maintenance** | Prompt changes = cron update | Script + plan + state must stay in sync |
| **Token cost** | ~200-500 tokens per fire | Zero tokens |
| **Best for** | Content that changes format, multi-step logic | Fixed-format output, high-frequency (100+/day) |

**When to use `no_agent=true`**: The script approach is better when you need deterministic, zero-token output on a fixed template (e.g., "always output exactly this JSON shape"). For tweet delivery from a markdown plan file, the LLM approach is simpler and more resilient.

## Critical Pitfall: Script Path Doubled `scripts/`

**Path resolution**: The `script` field in cronjob is relative to `~/.hermes/profiles/<profile>/scripts/`. A value of `scripts/tweet-deliver.py cn` resolves to `~/.hermes/profiles/<profile>/scripts/scripts/tweet-deliver.py cn` (DOUBLED). Always use just the filename: `tweet-deliver.py cn`.

**Verified bug (2026-06-11)**: `script='scripts/tweet-deliver.py cn'` → `Script not found: .../scripts/scripts/tweet-deliver.py cn`. Fix: `script='tweet-deliver.py cn'`.

## Recovery: When Cron Fails and User Needs Content NOW

When a cron job fails (missing script, path error, etc.), the user still needs the content. Two recovery paths:

**Path A: Manual extraction from plan file**
1. Read the state file: `current_tweet` = N
2. Read the plan file, find tweet #N (both CN and EN)
3. Output the text directly to the user
4. Do NOT advance the state — the failed cron didn't deliver, so the tweet is still pending

**Path B: Recreate cron as LLM-driven**
1. Remove the broken `no_agent=true` cron job
2. Create a new `no_agent=false` cron with a self-contained prompt
3. The prompt reads state + plan files and outputs the tweet
4. Run once immediately to verify, then let the schedule take over

**Always do Path A first** (instant delivery), then Path B if you want to fix the cron for future fires.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|----------|-------------|-----|
| `xurl: command not found` | Not installed | Run install script |
| `No apps registered` | Developer App not created | User creates app on developer.x.com |
| `unauthorized_client` during OAuth | App type set to "Native App" | Change to "Web app, automated app or bot" in User Auth Settings |
| `UsernameNotFound` after OAuth | X not returning username | Re-run: `xurl auth oauth2 --app my-app YOUR_HANDLE` |
| 401 on every request | Token expired or wrong default app | `xurl auth status` — verify default app has oauth2 |
| `CreditsDepleted` | $0 balance | Buy credits in Developer Console → Billing (min $5) |
| Browser login blocked | Cloud browser detected | **Don't use browser tools.** Only OAuth PKCE on local machine. |
| Cron Feishu delivery 99992402 | Agent final response fails Feishu validation | Use `send_message` inside cron agent instead of auto-deliver (see pitfall above) |
| Plan script can't find tweet #N | Zero-padding mismatch (#1 vs #01) | Use `n_str = f"{n:02d}"` when searching plan file |
| Cron `last_status: "error"` but no delivery | Script file missing at resolved path | Create the script file, verify with manual run, then re-enable cron |
| `Script not found: .../scripts/scripts/...` | Doubled `scripts/` prefix in script field | Use `tweet-deliver.py cn` not `scripts/tweet-deliver.py cn` — cron resolves from `scripts/` dir automatically |

---

## References

- `references/x-dev-app-application-template.md` — 100+ word application description for X Developer signup
- `references/feishu-fallback-implementation.md` — Full Feishu Fallback Mode implementation: state machine design, directory layout, cron prompt template, confirmation flow, and HERMES_HOME path pitfall
