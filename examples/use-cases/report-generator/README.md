# Report generator

An agent that pulls from multiple mock data sources (metrics, events, available sources), then produces a short one-page briefing with an executive summary and recommendations.

## What it does

- Uses **three tools** in one run: `get_metrics_snapshot`, `get_recent_events`, `get_available_sources`.
- Asks the agent to synthesize a **briefing**: executive summary, key numbers, and top 3 recommendations.
- Runs **durably** via the Aion worker (Hatchet): you dispatch from this script; execution and LLM calls happen in the worker.

This use case is generic (no domain-specific wording) and slightly more complex than the basic demo (multiple tool calls, structured output).

## Prerequisites

- [Prove V1.0.0 works](../../../README.md#prove-v100-works) (end-to-end + durability).
- Valid `OPENAI_API_KEY` in `.env` at the project root.

## How to run

**Terminal 1 (worker):**

```bash
cd /path/to/aion
source .venv/bin/activate
aion worker
```

**Terminal 2 (dispatch):**

```bash
cd /path/to/aion
source .venv/bin/activate
python examples/use-cases/report-generator/run.py
```

You should see an event ID in terminal 2; the worker will call the three tools and print the generated briefing.

## Customization

- Change the task in `run.py` (e.g. different focus: reliability, cost, security).
- Replace the mock tools in the worker with real APIs or DB calls (same tool names: `get_metrics_snapshot`, `get_recent_events`, `get_available_sources`).
