"""
CLI for the Aion Framework.

Provides init (scaffold demo + .env) and worker (start Hatchet worker loop).
"""

from __future__ import annotations

import os

import typer
from dotenv import load_dotenv

from .core.engine import get_hatchet
from .core.worker import AionPlannerWorkflowImpl, AionWorkflowImpl

app = typer.Typer(help="Aion Framework CLI")


@app.command()
def init() -> None:
    """Scaffold a new Aion agent project: creates demo.py and .env in the current directory."""
    demo_content = '''"""
Aion demo: dispatches a task to the durable worker.
Run with: python demo.py (after starting the worker with `aion worker`).
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
    print(f"Dispatched! Event ID: {event_id}")
    print("Run `aion worker` in another terminal to process this task.")


if __name__ == "__main__":
    main()
'''
    env_content = """OPENAI_API_KEY=sk-your-openai-api-key
HATCHET_CLIENT_TOKEN=your-local-hatchet-token
"""

    with open("demo.py", "w") as f:
        f.write(demo_content)
    typer.echo("✅ Created demo.py")

    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        typer.echo("✅ Created .env")
    else:
        typer.echo("⏭️  .env already exists, skipping")


@app.command()
def worker() -> None:
    """Start the Hatchet worker to listen for agent tasks (durable execution)."""
    load_dotenv()  # Load .env so OPENAI_API_KEY and HATCHET_* are available
    typer.echo("👷 Starting Aion Durable Worker...")
    hatchet = get_hatchet(debug=True)
    w = hatchet.worker("aion-worker")
    w.register_workflow(AionWorkflowImpl)
    w.register_workflow(AionPlannerWorkflowImpl)
    w.start()


if __name__ == "__main__":
    app()
