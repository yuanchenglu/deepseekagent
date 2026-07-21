# Feishu Fallback Mode — Complete Implementation

> Last updated: 2026-06-09 from llm-harness-agent 30-day publishing plan session

## State File

Path: `~/.hermes/profiles/<profile>/cron/twitter-publish-state.json`

```json
{
  "current_tweet": 1,
  "last_sent_at": null,
  "total_delivered": 0,
  "schedule": ["08:00", "16:00", "22:00"],
  "timezone": "Asia/Shanghai"
}
```

**Fields**:
- `current_tweet`: The tweet number to send next (1-indexed from the plan)
- `last_sent_at`: ISO timestamp of last delivery. `null` = first delivery of this tweet. Not null = this is a re-send
- `total_delivered`: Running count of successfully confirmed+delivered tweets

**State advancement**: Only the interactive session (NOT the cron job) advances `current_tweet`. When user replies "已发", the interactive agent:
1. Reads current state
2. Sets `current_tweet = current_tweet + 1`
3. Sets `last_sent_at = null`
4. Increments `total_delivered`

## Plan File

Path: `~/Documents/article/LLM-Harness-Agent-30day-twitter-plan-bilingual.md` (or equivalent)

**Format**:
```
## Day NN — Topic

**HH:00 UTC** / **HH:00 CST**

【中文】
LLM+Harness=Agent #NN — [CN insight text]
github.com/...

【English】
LLM+Harness=Agent #NN — [EN insight text]
github.com/...
```

**Key conventions**:
- Branch must be verified (master vs main), not assumed
- No UTM params in URLs
- English tweets ≤280 chars (text + 23 for URL)
- CN tweets first, EN second in each pair

## Cron Job Configuration

### Schedule

```
0 0,8,14 * * *  # UTC → CST 08:00, 16:00, 22:00
```

### Times (for CST users in China)

| CST (Beijing) | UTC | Coverage |
|---------------|-----|----------|
| 08:00 | 00:00 | US West 5PM, US East 8PM (previous day) |
| 16:00 | 08:00 | Europe morning, UK early morning |
| 22:00 | 14:00 | US East 10AM, Europe 3PM (peak) |

All three fall within a typical Chinese user's waking hours (07:30-23:00).

### Cron Job Prompt (Self-Contained)

```
You are a Twitter publishing scheduler for the LLM+Harness=Agent series.

## Your task
1. Read the state file at <STATE_PATH>
2. Read the bilingual plan at <PLAN_PATH>
3. Find the tweet pair (CN + EN) for current_tweet number N
4. Output them as two messages: Chinese first, then English

## State file format
{"current_tweet": N, "last_sent_at": "ISO time or null", "total_delivered": M}

## Important rules
- If last_sent_at is null → this is the first delivery of tweet #N. Send normally.
- If last_sent_at is NOT null → this is a RE-SEND reminder for tweet #N.
  Add prefix: "⏰ 提醒：上一条还未发送，请先发布这条：" before CN tweet.
  Add prefix: "⏰ Reminder: previous tweet not yet posted. Please publish this first:" before EN tweet.
- NEVER advance current_tweet. Only the main interactive session does that when user says "已发".
- Always output BOTH CN and EN versions as two separate messages.
- If plan has fewer entries than current_tweet, output "🎉 30天计划已全部完成！"
- Use exact text from plan. Do not modify, summarize, or truncate.
- Include the github link at the end of each tweet.
```

### Cron Job Creation (Hermes)

```python
cronjob(
    action='create',
    name='Twitter-Series-Publisher',
    schedule='0 0,8,14 * * *',
    prompt='<self-contained prompt from above>',
    enabled_toolsets=['file'],
    profile='<profile-name>',
    deliver='origin'
)
```

## Confirmation Flow

```
┌─────────────────────────────────────────────────────┐
│ Cron triggers at CST 08:00 / 16:00 / 22:00          │
│                                                      │
│ Reads state → current_tweet = N                      │
│    │                                                  │
│    ├─ last_sent_at = null → FIRST DELIVERY           │
│    │   Sends tweet #N (CN + EN) as two messages       │
│    │   Sets last_sent_at = now()                       │
│    │                                                  │
│    └─ last_sent_at != null → RE-SEND REMINDER        │
│        Sends tweet #N with ⏰ reminder prefix          │
│        Does NOT change state                          │
│                                                      │
│ User receives tweet text in Feishu                   │
│    │                                                  │
│    ├─ Posts to X, replies "已发" →                   │
│    │   Interactive agent advances current_tweet to N+1│
│    │   Sets last_sent_at = null                       │
│    │                                                  │
│    └─ Does nothing →                                  │
│        Next cron slot re-sends same tweet #N          │
└─────────────────────────────────────────────────────┘
```

## Guarantees

- **Linear**: Tweet #1 must be confirmed before #2 is delivered
- **No skip**: Unconfirmed tweets re-send every time slot
- **No loss**: State file persists across sessions
- **Human-in-loop**: User always controls when publishing happens

## Pitfalls

1. **Cron job must NOT advance state**: If the cron increments `current_tweet`, unconfirmed tweets will be skipped. The cron reads only.
2. **State file path must be absolute**: Cron jobs run in fresh sessions with no context. Use `/home/bluth/.hermes/profiles/<profile>/cron/twitter-publish-state.json`, not `~/...`.
3. **Plan file must be self-contained**: The cron job has no access to the conversation or memory. All content must be in the plan file.
4. **Model selection**: Cron jobs use the default model unless overridden. For simple state-reading tasks, the cheap model is fine.
5. **Profile isolation**: State file lives in the profile directory. Different profiles have independent publishing schedules.
