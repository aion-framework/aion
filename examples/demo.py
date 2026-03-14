"""
Aion Framework proof of concept.

Instantiate an AionAgent with a dummy tool fetch_data, then call
agent.start() to dispatch the task to the Hatchet worker.
"""
from dotenv import load_dotenv

from aion import AionAgent, aion_tool

load_dotenv()


@aion_tool
def fetch_data() -> str:
    """Fetch the latest data for the agent to summarize."""
    # TODO: Add random exception here to test Hatchet retries.
    return "Latest data: Aion Framework v0.1.0 is running with durable execution."


def main() -> None:
    agent = AionAgent(
        name="DemoAgent",
        model="openai:gpt-4o-mini",
        system_prompt="You are a helpful assistant. Use fetch_data when asked to get or summarize data.",
        tools=[fetch_data],
    )
    event_id = agent.start("Fetch the latest data and summarize it.")
    print(f"✅ Dispatched! Event ID: {event_id}")
    print("👉 Run `aion worker` in another terminal to process this event.")


if __name__ == "__main__":
    main()
