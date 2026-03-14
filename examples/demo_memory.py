"""
Phase 2 proof of concept: agent learns from its mistakes via Meta-Memory.

The agent is asked to "Fetch the user data for today." It will typically
call fetch_user_data with something like "today" or "Oct 12", which
triggers a ValueError (date must be YYYY-MM-DD). The exception is
analyzed and stored in LanceDB. On Hatchet retry, the pre-hook injects
the correction into the prompt, and the agent formats the date correctly.
"""

from dotenv import load_dotenv

from aion import AionAgent

load_dotenv()


def main() -> None:
    agent = AionAgent(
        name="MemoryDemoAgent",
        model="openai:gpt-4o-mini",
        system_prompt=(
            "You are a helpful assistant. When asked to fetch user data, "
            "use the fetch_user_data tool with a date string. Today's date "
            "should be formatted as YYYY-MM-DD."
        ),
    )
    # This task will cause the LLM to pass a non-YYYY-MM-DD value at first,
    # triggering the tool's ValueError. After Meta-Memory stores the
    # correction and Hatchet retries, the agent should use a proper date.
    event_id = agent.start("Fetch the user data for today.")
    print(f"✅ Dispatched! Event ID: {event_id}")
    print("👉 Run `aion worker` in another terminal to process this task.")
    print("   On first run the tool will fail; on retry the agent gets the warning and succeeds.")


if __name__ == "__main__":
    main()
