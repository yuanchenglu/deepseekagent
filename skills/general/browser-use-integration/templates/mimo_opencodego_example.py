"""browser-use + opencodego mimo-v2.5 — verified working test script"""
import asyncio
import os

# CRITICAL: Disable extension downloads to avoid hangs
os.environ["BROWSER_USE_DISABLE_EXTENSIONS"] = "1"

from browser_use import Agent, BrowserSession
from browser_use.llm.openai.chat import ChatOpenAI


async def main():
    llm = ChatOpenAI(
        model="mimo-v2.5",
        base_url="https://opencode.ai/zen/go/v1",
        api_key=os.environ.get("OPENCODEGO_API_KEY"),
        temperature=0.2,
        max_completion_tokens=4096,
        # Non-reasoning model — must disable structured output forcing
        dont_force_structured_output=True,
        reasoning_models=[],
    )

    browser = BrowserSession(headless=True)

    agent = Agent(
        task="Open https://example.com and report the page title.",
        llm=llm,
        browser=browser,
    )
    history = await agent.run(max_steps=10)
    print("=== Result ===")
    print(history.final_result() or "(no final result)")
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
