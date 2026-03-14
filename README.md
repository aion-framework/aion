# Aion Framework

The Durable Application Framework for Agentic AI (v1.0.0).

## Requirements

- Python 3.10+
- Docker & Docker Compose (for Hatchet)

## Setup

```bash
# Copy env and set your keys
cp .env.example .env   # then edit OPENAI_API_KEY and HATCHET_CLIENT_TOKEN

# Install the package
pip install -e .

# Start Hatchet (Postgres, RabbitMQ, Hatchet Engine)
docker-compose up -d
```

## Usage

**Terminal 1 – start the worker (runs the agent durably):**

```bash
aion worker
```

**Terminal 2 – dispatch a task:**

```bash
python examples/demo.py
# or Phase 2 Meta-Memory demo:
python examples/demo_memory.py
# or Phase 3 Enterprise (PII scrubber + planner + HITL):
python examples/demo_enterprise.py
# or Phase 4 Observability (OTEL + DurableSDR):
python examples/demo_observability.py
# or after: aion init
python demo.py
```

## Durability test (Milestone 1.2)

1. Run `docker-compose up -d`, then `aion worker` in one terminal.
2. In another terminal run `python examples/demo.py`.
3. While the worker is “thinking” or executing the tool, press **Ctrl+C** to kill the worker.
4. Run `aion worker` again. Hatchet should pick the task back up and continue.

## Meta-Memory test (Phase 2 / v0.3.0)

1. Start `aion worker`, then run `python examples/demo_memory.py`.
2. The agent is asked to "Fetch the user data for today." It may call `fetch_user_data("today")` and hit a `ValueError` (date must be YYYY-MM-DD).
3. The exception is analyzed by the LLM, stored in LanceDB, and the step fails so Hatchet retries.
4. On retry, the pre-hook injects a WARNING from MetaMemory into the prompt; the agent formats the date correctly and succeeds.

## Enterprise guardrails (Phase 3 / v0.6.x)

- **HITL:** `AionContext.suspend_for_approval(approval_key)` pauses the workflow until an external approval event.
- **Policies:** `PIIScrubberPolicy` (SSN/email → `[REDACTED_PII]`), `ToxicityValidatorPolicy` (restricted words).
- **Planner:** `AionPlannerAgent` produces a `Plan(steps)` and runs each step (plan-and-execute).

Run `python examples/demo_enterprise.py` to see PII scrubbing, planning, and HITL-capable `transfer_funds`.

## Observability (Phase 4 / v1.0.0)

- **OTEL:** `setup_telemetry(service_name, endpoint)` configures OTLP export (default `http://127.0.0.1:4317`).
- **Spans:** `@aion_trace(name)`, and tool calls as `ToolCall:<tool_name>`.
- **Patterns:** `DurableWebScraper`, `DurableSDR` in `aion.patterns`.

Run `python examples/demo_observability.py` then view traces in Arize Phoenix (`docker run -p 6006:6006 -p 4317:4317 arizeai/phoenix`).

## Tests

```bash
pytest tests/ -v
```

## CLI

- `aion init` – creates `demo.py` and `.env` in the current directory.
- `aion worker` – starts the Hatchet worker (agent + planner workflows).

## Project layout

- `src/aion/` – package
  - `agent.py` – `AionAgent`, `@aion_tool`, optional `policies`
  - `cli.py` – `aion init`, `aion worker`
  - `core/engine.py` – Hatchet singleton, `AionWorkflow`, `run_aion_workflow()`
  - `core/worker.py` – `AionWorkflowImpl`, `AionPlannerWorkflowImpl` (MetaMemory, policies, tools)
  - `core/context.py` – `AionContext`, `suspend_for_approval`, HITL
  - `core/exceptions.py` – `ExceptionAnalyzer`
  - `memory/store.py` – `MetaMemory`, `MistakeRecord`
  - `middleware/policies.py` – `BasePolicy`, `PIIScrubberPolicy`, `ToxicityValidatorPolicy`
  - `patterns/` – `AionPlannerAgent`, `DurableWebScraper`, `DurableSDR`
  - `telemetry/tracer.py` – `setup_telemetry`, `@aion_trace`
- `examples/` – `demo.py`, `demo_memory.py`, `demo_enterprise.py`, `demo_observability.py`
- `tests/` – `conftest.py`, `test_agent.py`
