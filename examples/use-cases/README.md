# Use cases

Real-world examples built on the Aion Framework. Use these **after** you have [proven V1.0.0 works](../../README.md#prove-v100-works) (end-to-end run + durability test).

## How to run

1. From the **project root**, start the worker:
   ```bash
   aion worker
   ```
2. In another terminal, from the **project root**, run the use case script, for example:
   ```bash
   python examples/use-cases/agentic-app-quickstart/run.py
   ```

Each use case folder contains:

- **README.md** – What it does, how to run it, and what to expect.
- **run.py** (or similar) – Entry point that dispatches a durable task to the worker.

## Use cases

| Use case | Description |
|----------|-------------|
| [agentic-app-quickstart](agentic-app-quickstart/) | **Build your first agentic app** – minimal pattern: worker tools + app that dispatches tasks. |
| [report-generator](report-generator/) | Pull metrics, events, and data sources; produce a one-page briefing with summary and recommendations. |

## Adding a use case

1. Create a subfolder under `examples/use-cases/`, e.g. `my-use-case/`.
2. Add a **README.md** with a short description and run instructions.
3. Add a runnable script (e.g. `run.py`) that uses `AionAgent`, `@aion_tool`, and `agent.start(...)`.
4. Update this README and the [Use cases section in the main README](../../README.md#use-cases) with a link and one-line description.

Keep each use case self-contained and runnable with only the framework and a valid `OPENAI_API_KEY` in `.env`.
