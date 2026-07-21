#!/usr/bin/env python3
"""
Diagnose API 400 errors caused by oversized max_tokens.

Usage:
  python3 scripts/diagnose-max-tokens.py <base_url> <api_key> <model>

Example:
  python3 scripts/diagnose-max-tokens.py \
    https://opencode.ai/zen/go/v1 \
    sk-xxx... \
    deepseek-v4-flash

Binary-searches the upstream API's max_tokens limit and reports
the highest accepted value.
"""

import httpx, sys, json

if len(sys.argv) < 4:
    print(f"Usage: {sys.argv[0]} <base_url> <api_key> <model>")
    print(f"  base_url: e.g. https://opencode.ai/zen/go/v1")
    print(f"  api_key: the API key or token")
    print(f"  model: e.g. deepseek-v4-flash")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
api_key = sys.argv[2]
model = sys.argv[3]

# Ensure /v1/chat/completions path
if not base_url.endswith("/v1/chat/completions"):
    chat_url = f"{base_url}/v1/chat/completions"
else:
    chat_url = base_url

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
}

# Test known values
candidates = [1024, 8192, 32768, 65536, 131072, 262144, 393216, 524288, 1048576]

print(f"🔍 Testing max_tokens limits for {model} at {chat_url}")
print()

last_ok = None
first_fail = None

for mt in candidates:
    resp = httpx.post(
        chat_url,
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": mt,
            "stream": False,
        },
        timeout=10,
    )
    ok = resp.status_code == 200
    badge = "✅" if ok else "❌"
    print(f"  {badge} max_tokens={mt:>7}: HTTP {resp.status_code}")
    if ok:
        last_ok = mt
    elif first_fail is None:
        first_fail = mt

print()
if first_fail is None:
    print(f"✅ All tested values up to {candidates[-1]} accepted — no limit found.")
elif last_ok is not None:
    print(f"✅ Max safe value: {last_ok} (upstream rejects at {first_fail})")
    safe = min(last_ok, 384000)
    print(f"💡 Recommended config value: {safe} (max output for DeepSeek V4 models)")
else:
    print(f"❌ Even max_tokens=1024 was rejected — the issue is not max_tokens.")