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

**Requires a valid `OPENAI_API_KEY`** in `.env` (agent, ExceptionAnalyzer, and MetaMemory embeddings all use it). If the key is missing or invalid, the worker will log an auth error and the step will complete without retrying.

1. Start `aion worker` (from project root), then run `python examples/demo_memory.py`.
2. The agent is asked to "Fetch the user data for today." It may call `fetch_user_data("today")` and hit a `ValueError` (date must be YYYY-MM-DD).
3. The exception is analyzed by the LLM, stored in LanceDB, and the step fails so Hatchet retries.
4. On retry, the pre-hook injects a WARNING from MetaMemory into the prompt; the agent formats the date correctly and succeeds.

To validate the Phase 2 flow without an API key, run: `pytest tests/test_e2e_phase2.py tests/test_memory.py -v`.

## Enterprise guardrails (Phase 3 / v0.6.x)

Phase 3 adds **approval (HITL)**, **policies**, and **planning**. Here is how an agent developer defines and uses each.

### How the developer defines **policies**

Policies are **input/output middleware**: they run on the client before the task is sent (pre_process) and in the worker after the LLM responds (post_process).

1. **Pass policies when creating the agent** (same for `AionAgent` and `AionPlannerAgent`):

   ```python
   from aion import AionAgent
   from aion.middleware.policies import PIIScrubberPolicy, ToxicityValidatorPolicy

   agent = AionAgent(
       name="MyAgent",
       model="openai:gpt-4o-mini",
       system_prompt="You are helpful.",
       policies=[PIIScrubberPolicy(), ToxicityValidatorPolicy()],
   )
   agent.start("Contact me at admin@corp.com")  # task is scrubbed to ... [REDACTED_PII] ... before send
   ```

2. **Built-in policies:**
   - **PIIScrubberPolicy** – Replaces SSNs (XXX-XX-XXXX) and emails with `[REDACTED_PII]` in both the task (pre) and the response (post).
   - **ToxicityValidatorPolicy** – Leaves input unchanged; validates output and raises `SafetyViolationError` if it contains restricted words (e.g. `confidential_leak`, `internal_only`).

3. **Custom policy:** Implement `BasePolicy` with `pre_process(prompt: str) -> str` and `post_process(response: str) -> str`. Add it to the worker’s registry in `worker.py` (`_get_policies_by_names`) and pass the **class name** in `policy_names` (the client sends policy names; the worker instantiates and runs post_process).

### How the developer defines **approval (HITL)**

Approval is implemented **inside tools** that run in the worker. The worker sets `AionContext` before running the agent so tools can call `suspend_for_approval`.

1. **In a tool** (defined in the worker, e.g. `_transfer_funds`, `_send_email`), get the context and wait for approval:

   ```python
   from aion.core.context import get_aion_context

   async def _transfer_funds(amount: int, account: str) -> str:
       ctx = get_aion_context()  # or _current_aion_context.get()
       if ctx:
           await ctx.suspend_for_approval(f"approve_transfer_{account}", timeout="72h")
       return f"Transferred {amount} to {account}."
   ```

2. **Parameters:**
   - **approval_key** – Event key the workflow waits for (e.g. `approve_transfer_XYZ`). An external system must send a Hatchet user event with this key to resume.
   - **timeout** – Max wait, e.g. `"72h"`, `"30m"`, `"60s"`. After timeout, the wait completes (behavior is implementation-dependent).

3. **Resuming:** Send a Hatchet user event with the matching `approval_key` and a payload like `{"approved": true}` (or `{"approved": false}` to raise `ApprovalDeniedError`). How you send the event depends on your Hatchet setup (REST API or SDK).

So: the **developer** adds tools that call `suspend_for_approval` in the worker; the **operator** (or another service) sends approval events to Hatchet to resume.

### How the developer defines **planning**

Use **AionPlannerAgent** when you want the agent to break a goal into steps and run each step (plan-then-execute).

1. **Create a planner agent** (same constructor as `AionAgent`, including `policies`):

   ```python
   from aion.patterns import AionPlannerAgent
   from aion.middleware.policies import PIIScrubberPolicy

   agent = AionPlannerAgent(
       name="EnterpriseAgent",
       model="openai:gpt-4o-mini",
       system_prompt="You are a compliant assistant. Break requests into clear steps.",
       policies=[PIIScrubberPolicy()],
   )
   agent.start("My email is admin@corp.com. Plan a transfer of $10,000 to XYZ and execute it.")
   ```

2. **Flow:** The planner workflow runs a **plan** step (LLM returns a `Plan(steps)`), then an **execute_plan** step runs the same agent for each step string. Policies are applied: **pre_process** to the initial task (and planner applies it before sending), **post_process** to each step’s output. HITL tools (e.g. `transfer_funds`) can be used during execute; the workflow pauses until the approval event is received.

3. **Event:** `AionPlannerAgent.start()` pushes to `aion:planner_task` (not `aion:agent_task`). The worker must register `AionPlannerWorkflowImpl` so the planner workflow runs.

**Summary:** The developer **provides/defines** approval by implementing tools that call `suspend_for_approval` in the worker; **policies** by passing `policies=[...]` to the agent and (for custom policies) registering them by name in the worker; **planning** by using `AionPlannerAgent` and the same agent config (model, system_prompt, policies). Run `python examples/demo_enterprise.py` to see PII scrubbing, planning, and HITL-capable `transfer_funds`.

### Is this the best way to define guardrails?

For **built-in policies**, **HITL**, and **planning**, the current design is a good fit:

- **Policies** – Declarative: pass `policies=[...]` to the agent; client runs pre_process, worker runs post_process by policy name. Same API for `AionAgent` and `AionPlannerAgent`.
- **Approval** – Encapsulated in tools: any tool can call `suspend_for_approval`; the operator resumes via Hatchet events. No extra “approval config” layer; approval semantics live in one place (`AionContext`).
- **Planning** – Reuse the same agent (and thus the same policies) for plan and execute; no separate guardrail config for the planner.

**Limitation:** Custom policies must be **registered by name** in the worker (`_get_policies_by_names` in `worker.py`). That keeps the worker in control (no arbitrary code from the client) but means adding a new policy type requires a worker code or config change. A **configurable policy registry** is planned for [V2.0.0 (future roadmap)](#aion-framework-v200-future-roadmap).

## Observability (Phase 4 / v1.0.0)

- **OTEL:** `setup_telemetry(service_name, endpoint)` configures OTLP export (default `http://127.0.0.1:4317`). Use `OTEL_EXPORTER_OTLP_ENDPOINT` in the environment to override the endpoint without code changes.
- **Spans:** `@aion_trace(name)` wraps a function in an OTEL span (attributes for args, kwargs, result; exceptions recorded and re-raised). In the worker, the agent step is traced as `AgentExecution` and each tool as `ToolCall:<tool_name>` when the telemetry package is available.
- **Patterns:** `DurableWebScraper` (AionAgent for URL fetch + structured extraction), `DurableSDR` (AionPlannerAgent for lead lookup, draft outreach, HITL send_email) in `aion.patterns`.

Run `python examples/demo_observability.py` then view traces in Arize Phoenix (`docker run -p 6006:6006 -p 4317:4317 arizeai/phoenix`). To see worker-side spans, run `aion worker` with the same env; the worker uses `@aion_trace` for the agent step and tool calls when `aion.telemetry` is installed.

**Verification:** `pytest tests/test_phase4_observability.py -v` runs Phase 4 tests (setup_telemetry, aion_trace, DurableWebScraper, DurableSDR dispatch).

## Building agentic apps on Aion

Can you build things like **OpenClaw**, **Moltbot**, **Clawdbot**, or other agentic apps (coding agents, CLI bots, DB assistants) **quickly** on this framework? Yes, with one important constraint.

### What you get out of the box

- **Durable execution** – Tasks run in the Hatchet worker; restarts and retries don’t lose work.
- **Agent + tools** – One event push (`agent.start(task)`) runs the LLM and tools in the worker.
- **Optional extras** – Meta-Memory (learn from failures), HITL (pause for approval), Planner (plan then execute), policies (PII/toxicity), OTEL tracing.

So you get a production-style **backend**: durable, observable, and with guardrails if you need them.

### The one constraint: tools live in the worker

Today, **tools are defined in the worker** (`src/aion/core/worker.py`), not in the client. The client sends only **task**, **model**, and **system_prompt**. So to build *your* agentic app you either:

1. **Extend the worker** – Add your domain tools (e.g. `read_file`, `run_shell`, `query_db`) in the worker’s tool list and wire them to your APIs/DBs, or  
2. **Add a custom workflow** – Register another Hatchet workflow (like the planner) that has its own tools and event, and dispatch to that from your app.

Both are straightforward: same pattern as the [report-generator](examples/use-cases/report-generator/) use case (worker has the tools; client sends the task and prompt).

### Quick-build path

1. **Prove V1.0.0** – Run [Prove V1.0.0 works](#prove-v100-works) so the stack is working.
2. **Try the minimal example** – Run the [Agentic app quickstart](examples/use-cases/agentic-app-quickstart/) use case: worker tools (`get_app_context`, `save_note`) + a script that dispatches a task. That’s the same pattern you’ll use for your app.
3. **Add your tools** – In the worker (or a new workflow), implement tools your agent needs (file system, shell, DB, APIs, RAG, etc.).
4. **Define your agent** – In your app, create an `AionAgent` with the right `system_prompt` (and optionally policies); call `agent.start(task)` to dispatch.
5. **Expose an interface** – Add a thin API (FastAPI/Flask) or CLI that calls `agent.start(...)` and, if needed, polls Hatchet or a store for the result. Optionally add a simple UI (chat or dashboard).

So: **durability, retries, and worker-side execution are already there**; you add **domain tools in the worker** and a **client/API/UI** that dispatches tasks and consumes results. That’s the fastest path to an OpenClaw/Moltbot/Clawdbot-style app today. Planned improvements are captured in the [V2.0.0 future roadmap](#aion-framework-v200-future-roadmap) below.

## Aion Framework V2.0.0 (future roadmap)

The following improvements are planned for a future major release (V2.0.0) to reduce the need to edit core worker code and to make guardrails and prompts more configurable.

### Configurable policy registry (enterprise guardrails)

Today, custom policies must be registered by name in the worker (`_get_policies_by_names` in `worker.py`). In V2.0, a **configurable policy registry** will allow adding custom policies without changing worker source: e.g. environment variables or a config file that map policy names to class paths (e.g. `my.module.MyPolicy`), so the worker can instantiate and run them at runtime. Built-in policies (e.g. `PIIScrubberPolicy`, `ToxicityValidatorPolicy`) will remain available by default.

### Extensible tool configuration

Today, **tools are defined in the worker** and adding new tools requires editing `worker.py` (or registering a custom workflow). V2.0 will introduce **extensible tool configuration** so that:

- Tools can be **registered** via config or a registry (e.g. module path + function name), or
- The worker can accept **tool declarations** from a trusted source (e.g. app-specific worker entrypoint or plugin directory),

allowing agent developers to add or override tools without forking the core worker.

### Prompt registry

Today, the client sends `system_prompt` (and optional task) in the payload; there is no built-in notion of named or versioned prompts. V2.0 will add a **prompt registry** so that:

- Prompts can be **stored and referenced by name** (e.g. `support_agent_v2`, `compliance_summarizer`),
- Optional **versioning** and **environment-specific** variants (e.g. dev vs prod) can be supported,

reducing duplication and making it easier to update prompts in one place and reference them from the agent or workflow.

### Additional V2 directions (under consideration)

To support a **wide variety of agent use cases** (generic and domain-specific), the following are under consideration for V2 or later:

- **Multi-agent composition** – First-class support for **agent-as-tool** or **agent teams**: chain or graph multiple agents (e.g. researcher → writer → reviewer), each step durable as a Hatchet workflow. Enables complex pipelines and delegation without building custom DAGs by hand.
- **Streaming and real-time UX** – **Stream tokens or partial results** to the client (e.g. SSE or WebSocket) while the workflow runs, so UIs can show progress and reduce perceived latency. Today the worker returns only when the step completes.
- **Evaluation and quality** – **Evaluation harness**: run an agent on a dataset of inputs (and optional expected outputs or criteria), record results, and compare runs or prompt versions. **Guardrail testing**: validate policies against a suite of inputs/outputs before deploy.
- **Security and compliance** – **Audit log**: immutable record of tasks, policy applications, tool calls, and approvals for compliance. **Secrets by reference**: reference API keys and secrets by name from a secure store (e.g. env or Vault) instead of passing them in payloads.
- **Cost and limits** – **Budgets and quotas** per tenant or workflow (e.g. cap LLM spend or tool calls). **Rate limiting** so one tenant or job cannot starve others. **Token/cost attribution** on spans for visibility.
- **Developer experience** – **Result client**: typed helpers to push a task and poll or subscribe for the result (or webhook), so app code stays simple. **Local/dev mode**: run the same agent logic locally without Hatchet (or with a mock) for fast iteration and unit tests. **Replay**: replay a workflow run from stored events for debugging.
- **Model flexibility** – **Multiple LLM configuration**: register and reference multiple LLM configs (model id, provider, endpoint, API key reference, params) so different agents or tenants can use different models without code changes; e.g. `production-gpt4`, `dev-gpt4-mini`, or per-tenant overrides. **Model routing**: choose model by task type, tenant, or A/B (e.g. cheaper model for simple tasks). **Multiple backends**: first-class support for more providers (Anthropic, local/OSS) alongside OpenAI, where the framework and registry stay provider-agnostic.
- **Observability** – **Standard OTEL conventions**: consistent attributes (e.g. `agent`, `workflow_id`, `policy`) so any backend (Phoenix, Langfuse, Datadog) can display agent runs. **Cost and usage** attached to spans for dashboards.

These are goals under consideration; priority and scope for V2 will depend on community and production feedback.

### V2 and later (further ideas)

Additional directions that could make the framework more useful over time:

- **Conversation and chat memory** – Multi-turn sessions: persist chat history per thread or user, inject last N turns (or summarized context) into the agent, optional TTL or compaction. Fits support bots, assistants, and any chat-style agent.
- **RAG and retrieval** – First-class **retrieval step** or **knowledge-base** attachment: index documents, query before or during the run, inject retrieved chunks into the prompt. Common for enterprise, support, and document-heavy agents.
- **Structured output and tool schemas** – Agent outputs as **Pydantic/JSON schema** for reliability and parsing. **Tool schemas** (e.g. OpenAPI-style) exposed so clients or UIs can discover and render tools, validate args, and generate forms.
- **Human feedback loop** – Beyond HITL: collect thumbs up/down or corrections, feed into **prompt tuning**, **fine-tuning**, or **Meta-Memory** (e.g. success signals) to improve agents over time.
- **Webhooks and callbacks** – Notify an external URL when a workflow completes or fails, so clients don’t have to poll. Optional payload (result summary, status, run id) for integrations.
- **Scheduling and cron** – Trigger agent workflows on a **schedule** (e.g. daily report, periodic sync). Enables recurring and background jobs without a separate scheduler.
- **Tenancy and isolation** – First-class **tenant_id** (or org_id) in context: scoped config, policies, and tools; per-tenant rate limits and quotas; fits multi-tenant SaaS.
- **Libraries of patterns** – Curated, reusable **agent patterns** for common domains (support bot, code reviewer, data analyst, content moderator) as optional packages or built-in templates, beyond DurableSDR and DurableWebScraper.
- **Workflow DSL** – Declarative **multi-step or multi-agent flows** (YAML/JSON or Python DSL) for non-developers or quick experiments, with steps mapped to durable workflows.
- **Testing and mocking** – **Test harness**: mock LLM responses and tools, assert on tool-call sequences or final output; deterministic unit and integration tests for agents.
- **Idempotency** – **Idempotency keys** for task submission so duplicate requests (e.g. retried API calls) don’t run twice. Important for production APIs.
- **Deployment and scaling** – Guidance or helpers for **worker autoscaling**, **queue priorities**, and running **multiple workers**; health checks and graceful shutdown.

---

These roadmap items are goals for V2.0.0 and beyond; the current V1.x design remains the supported way to build on Aion until then.

## Use cases

| Use case | Description | Run |
|----------|-------------|-----|
| [Agentic app quickstart](examples/use-cases/agentic-app-quickstart/) | **Minimal pattern to build an agentic app:** worker tools (`get_app_context`, `save_note`) + app that dispatches tasks. Start here to build your own app. | See `examples/use-cases/agentic-app-quickstart/README.md` |
| [Report generator](examples/use-cases/report-generator/) | Pull metrics, events, and data sources; produce a one-page briefing with summary and top 3 recommendations (multiple tools, durable). | See `examples/use-cases/report-generator/README.md` |

Run the worker from the project root (`aion worker`), then from the project root run the use case script (e.g. `python examples/use-cases/agentic-app-quickstart/run.py`). Add your own use cases in the same directory and list them here.

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
