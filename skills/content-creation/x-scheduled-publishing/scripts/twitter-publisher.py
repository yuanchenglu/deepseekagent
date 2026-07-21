#!/usr/bin/env python3
"""Read state + plan, output current tweet for delivery.
Usage: python3 twitter-publisher.py cn|en
Output: single tweet text + link to stdout (for no_agent cron delivery).
"""
import json, re, sys
from pathlib import Path

# Paths — adjust PROFILE if needed
PROFILE = "course-designer"
STATE_FILE = Path(f"~/.hermes/profiles/{PROFILE}/cron/twitter-publish-state.json").expanduser()
PLAN_FILE = Path("~/Documents/article/LLM-Harness-Agent-30day-twitter-plan-bilingual.md").expanduser()

lang = sys.argv[1] if len(sys.argv) > 1 else "cn"
if lang not in ("cn", "en"):
    print(f"Usage: {sys.argv[0]} cn|en")
    sys.exit(1)

# Read state
state = json.loads(STATE_FILE.read_text())
n = state["current_tweet"]
last_sent = state.get("last_sent_at")

# Read plan
plan = PLAN_FILE.read_text(encoding="utf-8")

# Find tweet #N — plan uses #Agent=LLM+Harness prefix, numbers are zero-padded #01-#90
n_str = f"{n:02d}"
tag = "【中文】" if lang == "cn" else "【English】"

# Match: 【中文】 or 【English】 → tweet line → github link line
pattern = rf"{re.escape(tag)}\n((?:#\w+=LLM\+Harness|LLM\+Harness=#\w+|#Agent=LLM\+Harness) #{n_str} — .+?)\n(github\.com/[\w/\-._]+)"
match = re.search(pattern, plan)

if not match:
    if n > 90:
        print("🎉 30天计划已全部完成！")
    else:
        print(f"❌ 未找到第 {n} 条推文（lang={lang}），请检查计划文件")
    sys.exit(0)

text = match.group(1)
link = match.group(2)

# Re-send reminder prefix
is_reminder = last_sent is not None
if is_reminder:
    prefix = "⏰ 上一条还未发送，请先发布这条" if lang == "cn" else "⏰ Reminder: previous tweet not yet posted"
    print(prefix)
    print()

print(text)
print(link)
