"""
Agentic app quickstart – minimal use case for building an agentic app on Aion.

Shows the pattern: worker has tools (get_app_context, save_note); this script
is your "app" that creates an AionAgent and dispatches a task. Execution runs
durably in the worker.

Run with: aion worker in one terminal, then
  python examples/use-cases/agentic-app-quickstart/run.py
from the project root.
"""
from dotenv import load_dotenv

from aion import AionAgent

load_dotenv()


def main() -> None:
    agent = AionAgent(
        name="QuickstartApp",
        model="openai:gpt-4o-mini",
        system_prompt=(
            "You are a helpful app assistant. Use get_app_context to see current context "
            "and save_note to persist a short note when the user asks you to remember something. "
            "Reply briefly and confirm what you did."
        ),
        tools=[],  # Tools (get_app_context, save_note) are in the worker
    )
    event_id = agent.start(
        "Check the current app context, then save a note that says: 'User requested quickstart demo at today.'"
    )
    print("✅ Dispatched! Event ID:", event_id)
    print("👉 Check the worker terminal for the agent's response.")


if __name__ == "__main__":
    main()
