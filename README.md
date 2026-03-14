# Aion Framework

The Durable Application Framework for Agentic AI (v1.0.0).

## Requirements

- **Python 3.10+** (3.9 is not supported; the codebase and `hatchet-sdk` use 3.10+ syntax.)
- **Docker & Docker Compose** – used to run Hatchet (Postgres, RabbitMQ, Hatchet Engine, Dashboard).
- **OpenAI API key** – for the agent and optional Meta-Memory/ExceptionAnalyzer.

## Initial setup

Follow these steps once to get the environment running.

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/aion-framework/aion.git
cd aion
python3.10 -m venv .venv   # or python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Start Hatchet with Docker

```bash
docker-compose up -d
```

Wait until all services are healthy (Postgres, RabbitMQ, migration, setup-config, hatchet-engine, hatchet-dashboard). You can check with `docker-compose ps`.

### 3. Get the Hatchet client token

The worker needs a **HATCHET_CLIENT_TOKEN** to connect to the local engine.

1. Open **http://localhost:8080** in your browser (Hatchet Dashboard).
2. Log in with **admin@example.com** / **Admin123!!**
3. Go to **Settings → API Tokens → Create API Token**.
4. Copy the token (you will paste it into `.env`).

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key (starts with `sk-`). Required for the agent and for Meta-Memory/ExceptionAnalyzer. |
| `HATCHET_CLIENT_TOKEN` | The token from the Hatchet Dashboard (step 3). |
| `HATCHET_CLIENT_TLS_STRATEGY` | Use `none` for local development. |
| `HATCHET_CLIENT_HOST_PORT` | Use `localhost:7077` for local Docker engine. |

Example `.env`:

```env
OPENAI_API_KEY=sk-proj-...
HATCHET_CLIENT_TOKEN=your-token-from-dashboard
HATCHET_CLIENT_TLS_STRATEGY=none
HATCHET_CLIENT_HOST_PORT=localhost:7077
```

### 5. Run the worker from the project root

The worker loads `.env` from the **current working directory**. Always start it from the repo root:

```bash
cd /path/to/aion
source .venv/bin/activate
aion worker
```

## Quick start (after setup)

```bash
# Terminal 1 – start the worker (must run from project root so .env is loaded)
cd /path/to/aion && source .venv/bin/activate && aion worker

# Terminal 2 – dispatch a task
cd /path/to/aion && source .venv/bin/activate && python examples/demo.py
```

## Prove V1.0.0 works

Do these two checks before building on the framework or trying [use cases](#use-cases).

### 1. End-to-end run

With a **valid `OPENAI_API_KEY`** in `.env` and the worker running from the project root:

- **Terminal 1:** `aion worker`
- **Terminal 2:** `python examples/demo.py`

You should see:

- Terminal 2: `✅ Dispatched! Event ID: ...`
- Terminal 1: `🚀 [Aion Worker] Executing task: Fetch the latest data and summarize it.` then `✅ [Aion Worker] Task completed.`

The agent calls the tool, gets data, and returns a summary. That confirms the full path (client → Hatchet → worker → OpenAI → result) works.

### 2. Durability (resume after worker kill)

Same setup (worker + demo). Then:

1. Run `python examples/demo.py` again so a task is in the queue or running.
2. While the worker is processing (or right after you dispatch), press **Ctrl+C** in the worker terminal to kill it.
3. Start the worker again: `aion worker`.
4. Hatchet should resume the same run and complete it (you’ll see the task finish in the restarted worker).

Once both steps succeed, V1.0.0 is proven. You can then run the [demos](#usage) (Meta-Memory, Enterprise, Observability) and the [use cases](#use-cases) below.

## Usage

**Terminal 1 – start the worker (runs the agent durably):**  
Run from the **project root** so `.env` is loaded (see [Initial setup](#initial-setup)).

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

## Troubleshooting

Common issues and how to fix them.

### "OPENAI_API_KEY environment variable" / "api_key client option must be set"

**Cause:** The worker process does not see `OPENAI_API_KEY` (e.g. you didn’t set it in `.env` or the worker wasn’t started from the project root).

**Fix:**

1. Create or edit `.env` in the **project root** with a valid `OPENAI_API_KEY=sk-...`.
2. Start the worker from that directory: `cd /path/to/aion && aion worker`. The CLI loads `.env` from the current working directory.
3. If you use a different cwd, export the key in the shell before starting the worker: `export OPENAI_API_KEY=sk-...`.

### "Incorrect API key provided" / 401 authentication error

**Cause:** The key in `.env` is invalid, expired, or still the placeholder (`sk-your-openai-api-key`).

**What you’ll see:** The worker logs:  
`❌ [Aion Worker] OpenAI authentication failed. Set a valid OPENAI_API_KEY in .env or your environment.`  
The step completes without a traceback (auth failures are handled gracefully).

**Fix:**

1. Get a key from https://platform.openai.com/account/api-keys.
2. Put it in `.env`: `OPENAI_API_KEY=sk-proj-...` (no quotes, no spaces).
3. Restart the worker.

### Worker doesn’t connect to Hatchet / gRPC or connection errors

**Cause:** Wrong host/port or TLS settings for the local engine.

**Fix:**

1. Ensure Docker is running and Hatchet is up: `docker-compose ps`. You should see `hatchet-engine` and related services running.
2. In `.env` set:
   - `HATCHET_CLIENT_TLS_STRATEGY=none`
   - `HATCHET_CLIENT_HOST_PORT=localhost:7077`
3. Ensure `HATCHET_CLIENT_TOKEN` is the token from the Hatchet Dashboard (http://localhost:8080 → Settings → API Tokens), not a placeholder.

### "Event ID" printed but nothing happens in the worker

**Cause:** Worker isn’t running, or it’s not connected to the same Hatchet instance (e.g. wrong token or port).

**Fix:**

1. Start the worker first: `aion worker` (from project root).
2. Confirm you see: `'aion-worker' waiting for ['aionworkflow:execute_agent', ...]` and `acquired action listener`.
3. Then run `python examples/demo.py`. If the worker is connected, you’ll see `🚀 [Aion Worker] Executing task: ...`.

### Python 3.9 or "unsupported syntax" errors

**Cause:** This project and `hatchet-sdk` require Python 3.10+ (e.g. `X | None` type hints).

**Fix:** Use Python 3.10 or 3.11: `python3.10 -m venv .venv` (or install Python 3.10/3.11 via your OS package manager or pyenv).

### gRPC message: "Other threads are currently calling into gRPC, skipping fork() handlers"

**Cause:** Normal gRPC/runtime message when the worker process uses threading. It is harmless and can be ignored.

### Dashboard or engine not reachable after `docker-compose up -d`

**Cause:** Services may still be starting (migration, setup-config run after Postgres/RabbitMQ).

**Fix:** Wait 30–60 seconds and check again. Run `docker-compose logs hatchet-engine` or `docker-compose logs hatchet-dashboard` for errors. Ensure ports 7077 (engine) and 8080 (dashboard) are not in use by another process.

---

For more detail on the worker (task signatures, event API, auth handling), see the source: `src/aion/core/worker.py`, `src/aion/core/engine.py`, and `src/aion/cli.py`.

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

## Use cases

| Use case | Description | Run |
|----------|-------------|-----|
| [Report generator](examples/use-cases/report-generator/) | Pull metrics, events, and data sources; produce a one-page briefing with summary and top 3 recommendations (multiple tools, durable). | See `examples/use-cases/report-generator/README.md` |

Run the worker from the project root (`aion worker`), then from the project root run the use case script (e.g. `python examples/use-cases/report-generator/run.py`). Add your own use cases in the same directory and list them here.

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
