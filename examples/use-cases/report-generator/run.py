"""
Report generator – use case example for the Aion Framework.

Dispatches a task to the durable worker: pull metrics, recent events, and
available data sources, then produce a one-page briefing with summary and
recommendations. Uses multiple tools in a single run.

Run with: aion worker in one terminal, then
  python examples/use-cases/report-generator/run.py
from the project root.
"""
from dotenv import load_dotenv

from aion import AionAgent

load_dotenv()


def main() -> None:
    agent = AionAgent(
        name="ReportGenerator",
        model="openai:gpt-4o-mini",
        system_prompt=(
            "You are a reporting assistant. Use get_metrics_snapshot, get_recent_events, "
            "and get_available_sources to gather data. Then write a short one-page briefing with: "
            "(1) an executive summary in 2–3 sentences, (2) key numbers to watch, "
            "and (3) your top 3 recommendations. Be concise and actionable."
        ),
        tools=[],  # Tools are provided by the worker
    )
    event_id = agent.start(
        "Pull the latest metrics, recent events, and list of available sources. "
        "Then produce a one-page briefing with an executive summary, key numbers, and top 3 recommendations."
    )
    print("✅ Dispatched! Event ID:", event_id)
    print("👉 Check the worker terminal for the generated briefing.")


if __name__ == "__main__":
    main()
