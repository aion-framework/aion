# Agentic app quickstart

A **minimal use case** that shows how to build an agentic app on the Aion framework: worker-side tools + a small app that dispatches tasks.

## What this demonstrates

1. **Tools in the worker** – The worker exposes `get_app_context()` and `save_note(content)` (mock implementations). Your own app would add real tools here (DB, APIs, files, etc.).
2. **App = agent + dispatch** – Your “app” creates an `AionAgent` with a system prompt and calls `agent.start(task)`. Execution runs durably in the worker.
3. **Optional next step** – To expose an HTTP API, add a thin FastAPI/Flask app that accepts a task and returns the event ID (and later poll Hatchet or your store for the result).

## Prerequisites

- [Prove V1.0.0 works](../../../README.md#prove-v100-works).
- Valid `OPENAI_API_KEY` in `.env` at the project root.

## How to run

**Terminal 1 (worker):**

```bash
cd /path/to/aion
source .venv/bin/activate
aion worker
```

**Terminal 2 (your “app” – dispatches a task):**

```bash
cd /path/to/aion
source .venv/bin/activate
python examples/use-cases/agentic-app-quickstart/run.py
```

The agent will use `get_app_context` and optionally `save_note` to fulfill the task; the result appears in the worker logs.

## Building your own agentic app

1. **Add your tools** in `src/aion/core/worker.py` (or a [custom workflow](../../../README.md#the-one-constraint-tools-live-in-the-worker)) and register them in the worker’s `tools` list.
2. **Keep this pattern** – In your app code, create an `AionAgent` with your `system_prompt` and call `agent.start(task)`.
3. **Add an interface** – Wrap that in a CLI, a FastAPI/Flask endpoint, or a frontend that posts the task and (optionally) fetches the result.

See [Building agentic apps on Aion](../../../README.md#building-agentic-apps-on-aion) in the main README for the full path.
