from dotenv import load_dotenv
from aion import AionAgent

load_dotenv()


def main():
    print("🤖 Initializing Demo Agent...")

    agent = AionAgent(
        name="ResearchAgent",
        model="openai:gpt-4o-mini",
        system_prompt="You are a durable research agent. You never give up.",
    )

    # Normally we'd bind a tool here that randomly throws an exception.
    # For now, the worker executing this task is completely durable!

    event_id = agent.start(
        "Tell me a 3 sentence story about a resilient robot."
    )
    print(f"✅ Dispatched! Event ID: {event_id}")
    print("👉 Now, run `aion run` in another terminal to process this event.")


if __name__ == "__main__":
    main()
