---
name: browser-use-integration
description: Install, configure, and run browser-use (v0.13.0+) with custom OpenAI-compatible LLM providers. Covers Python agent setup, Rust beta agent quirks, extension management, and non-reasoning model compatibility. Use when the user wants to use browser-use for AI-driven browser automation with models like DeepSeek, GLM, Kimi, MiMo, or any OpenAI-compatible API.
tags: [browser, automation, ai-agent, python, playwright]
---

# browser-use Integration Guide

## Overview

[browser-use](https://github.com/browser-use/browser-use) is an AI browser automation library that takes natural language tasks and executes them in Chromium via Playwright. Version 0.13.0+ introduces a Rust-powered beta agent alongside the Python agent.

## Installation

```bash
# Clone and install from source (recommended for custom provider work)
cd ~/Code && git clone --depth 1 https://github.com/browser-use/browser-use.git
cd browser-use
uv pip install -e ".[core]"
```

The `[core]` extra installs the native Rust runtime (`browser-use-core`).

### Verify

```bash
browser-use --help        # CLI works
browser-use doctor        # Check dependencies
python3 -c "from browser_use import Agent, BrowserSession; print('OK')"
```

## Architecture: Two Agents

| Agent | Import | Backend | Custom Provider Support |
|-------|--------|---------|------------------------|
| Python Agent | `from browser_use import Agent` | Python + Playwright | ✅ Full (ChatOpenAI with base_url) |
| Beta Agent | `from browser_use.beta import Agent` | Rust core + browser harness | ⚠️ May 404 with non-OpenAI base URLs |

**Recommendation:** Use the Python Agent for custom providers. The Beta Agent's Rust SDK constructs API URLs differently and may not work with all OpenAI-compatible endpoints.

## Connecting to Custom LLM Providers

browser-use's `ChatOpenAI` wraps `AsyncOpenAI` and accepts `base_url` for any OpenAI-compatible API.

### Template

```python
import os
os.environ["BROWSER_USE_DISABLE_EXTENSIONS"] = "1"  # Skip uBlock download

from browser_use import Agent, BrowserSession
from browser_use.llm.openai.chat import ChatOpenAI

llm = ChatOpenAI(
    model="mimo-v2.5",                    # Model name as recognized by provider
    base_url="https://opencode.ai/zen/go/v1",  # OpenAI-compatible endpoint
    api_key=os.environ["OPENCODEGO_API_KEY"],
    temperature=0.2,
    max_completion_tokens=4096,
    # CRITICAL for non-reasoning models:
    dont_force_structured_output=True,    # Don't enforce JSON schema response_format
    reasoning_models=[],                  # Clear the list — model is not a reasoning model
)

agent = Agent(
    task="Your task here",
    llm=llm,
    browser=BrowserSession(headless=True),
)
history = await agent.run(max_steps=20)
print(history.final_result())
```

### Provider Config Reference (from hermes config)

| Provider | base_url | key_env | Example Models |
|----------|----------|---------|----------------|
| opencodego | `https://opencode.ai/zen/go/v1` | `OPENCODEGO_API_KEY` | deepseek-v4-flash, mimo-v2.5, glm-5.1, kimi-k2.6 |
| 7colorai-liantong | `https://aigw-gzgy2.cucloud.cn:8443/v1` | `COLORAI_LIANTONG_API_KEY` | glm-5.1, DeepSeek-V4-Pro |

## Pitfalls

### 1. uBlock Origin Download Hangs

By default, browser-use downloads uBlock Origin Lite, "I still don't care about cookies", and ClearURLs extensions. On slow connections or in China, this can hang indefinitely.

**Fix:** Set env var before import:
```python
import os
os.environ["BROWSER_USE_DISABLE_EXTENSIONS"] = "1"
```

Or `export BROWSER_USE_DISABLE_EXTENSIONS=1` in shell.

### 2. Structured Output Validation Errors

Non-reasoning models (DeepSeek, GLM, MiMo, etc.) may return malformed JSON when browser-use forces `response_format=json_schema`. Error looks like:
```
45 validation errors for AgentOutput
action.0.DoneActionModel.done - Field required [type=missing]
```

**Fix:** Two settings on ChatOpenAI:
```python
dont_force_structured_output=True,  # Don't use response_format
reasoning_models=[],                # Don't apply reasoning_effort params
```

The agent will still work — it just falls back to text parsing instead of guaranteed JSON.

### 3. Beta Agent (Rust SDK) API 404

The Rust SDK may construct API URLs that don't match your provider's routing. Symptom:
```
provider error: InvalidRequest: HTTP 404
```

**Fix:** Use the Python Agent (`from browser_use import Agent`) instead of the Beta Agent.

### 4. Browser API Change in v0.13.0

`Browser` is now an alias for `BrowserSession`. Both work:
```python
from browser_use import BrowserSession  # preferred
from browser_use import Browser         # alias, same thing
```

### 5. Playwright Chromium Download

First run may download Chromium via Playwright. If blocked in China:
```bash
# Set mirror
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

## CLI Usage

```bash
# Check installation health
browser-use doctor

# Install Chromium + deps
browser-use install

# Direct browser commands (useful for scripting)
browser-use open https://example.com
browser-use screenshot
browser-use extract "page title"
browser-use click 1    # Click element by index
browser-use type "search text"
```

## Typical Workflow

1. Set `BROWSER_USE_DISABLE_EXTENSIONS=1`
2. Configure `ChatOpenAI` with provider's base_url and api_key
3. Set `dont_force_structured_output=True` and `reasoning_models=[]`
4. Create `BrowserSession(headless=True)` (or `headless=False` for debugging)
5. Create `Agent(task=..., llm=..., browser=...)`
6. `await agent.run(max_steps=20)`
7. `print(history.final_result())`

## When Beta Agent Works

The Beta Agent (Rust core) works well with:
- Official OpenAI API (GPT-4/5)
- Google Gemini
- Anthropic Claude
- Browser Use Cloud (`ChatBrowserUse()`)

It may fail with custom OpenAI-compatible proxies that have non-standard routing.
