"""
Worker runtime for the Aion Framework.

Listens for agent and planner events. Pre-hook injects Meta-Memory warnings;
post-hook catches exceptions, analyzes them, applies output policies, and re-raises.
Supports HITL via contextvar and durable task where available.
"""

from __future__ import annotations

import asyncio
from typing import Any

from hatchet_sdk import Context
from openai import AuthenticationError as OpenAIAuthError
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError

from .context import AionContext, _current_aion_context
from .engine import AionWorkflow, get_hatchet
from .exceptions import ExceptionAnalyzer

try:
    from aion.telemetry.tracer import aion_trace
except ImportError:
    def aion_trace(name: str):  # noqa: ARG001
        def _id(f): return f
        return _id

hatchet = get_hatchet(debug=True)

# Policy registry for post_process by name (worker-side)
def _get_policies_by_names(policy_names: list[str]) -> list[Any]:
    from aion.middleware.policies import (
        PIIScrubberPolicy,
        ToxicityValidatorPolicy,
    )
    registry = {
        "PIIScrubberPolicy": PIIScrubberPolicy,
        "ToxicityValidatorPolicy": ToxicityValidatorPolicy,
    }
    return [registry[name]() for name in policy_names if name in registry]


def _fetch_data() -> str:
    """Built-in demo tool: fetch data for the agent to summarize."""
    return "Latest data: Aion Framework v0.1.0 is running with durable execution."


def _fetch_user_data(date_string: str) -> str:
    """Fetch user data for a given date. Date must be YYYY-MM-DD."""
    if not date_string.startswith("202"):
        raise ValueError("Date must be in YYYY-MM-DD format.")
    return f"User data for {date_string}: [sample records]"


async def _transfer_funds(amount: int, account: str) -> str:
    """Transfer funds; requires human approval via HITL."""
    ctx = _current_aion_context.get()
    if ctx:
        await ctx.suspend_for_approval(f"approve_transfer_{account}", timeout="72h")
    return f"Transferred {amount} to account {account}."


def _find_lead_info(company_name: str) -> str:
    """Find lead/contact info for a company (mock)."""
    return f"Lead info for {company_name}: [CTO contact placeholder]"


def _draft_outreach(topic: str, recipient: str) -> str:
    """Draft an outreach email (mock)."""
    return f"Draft email to {recipient} re: {topic}"


async def _send_email(to: str, subject: str, body: str) -> str:
    """Send email; requires HITL approval."""
    ctx = _current_aion_context.get()
    if ctx:
        await ctx.suspend_for_approval(f"approve_email_{to}", timeout="72h")
    return f"Sent to {to}: {subject}"


def get_metrics_snapshot() -> str:
    """Return a snapshot of key metrics (mock). Used by report-generator use case."""
    return """
    Metrics snapshot (last 24h):
    - API latency p99: 420ms (target <500ms)
    - Throughput: 12.4k req/min
    - Error rate: 0.02%
    - Cache hit rate: 94%
    """


def get_recent_events(limit: int = 5) -> str:
    """Return recent system events (mock). Used by report-generator use case."""
    return """
    Recent events:
    1. Deployment: service-api v2.1.0 (success, 14:00 UTC)
    2. Alert: disk usage >85% on node-3 (resolved)
    3. Config change: feature flag 'new_checkout' enabled for 10% traffic
    """


def get_available_sources() -> str:
    """Return list of available data sources (mock). Used by report-generator use case."""
    return """
    Available sources: metrics_db, events_log, audit_trail, config_store.
    """


def get_app_context() -> str:
    """Return current app context (mock). Used by agentic-app-quickstart use case."""
    return "App context: user=guest, theme=light, locale=en."


def save_note(content: str) -> str:
    """Save a note and return confirmation (mock). Used by agentic-app-quickstart use case."""
    preview = (content[:50] + "…") if len(content) > 50 else content
    return f"Note saved: {preview!r}"


def _fetch_url_content(url: str) -> str:
    """Fetch raw text from URL (mock)."""
    return f"[Mock content from {url}]"


def _extract_structured_data(raw_text: str, schema_hint: str) -> str:
    """Extract structured data from raw text (mock)."""
    return f"Extracted data for schema: {schema_hint}"


def _apply_post_process(raw: str, policy_names: list[str]) -> str:
    out = raw
    for policy_cls in _get_policies_by_names(policy_names or []):
        out = policy_cls.post_process(out)
    return out


def _workflow_input_to_dict(workflow_input: Any) -> dict[str, Any]:
    """Normalize workflow input to dict; Hatchet may pass a Pydantic EmptyModel when no input_validator is set."""
    if isinstance(workflow_input, dict):
        return workflow_input
    if hasattr(workflow_input, "model_dump"):
        return workflow_input.model_dump()
    if hasattr(workflow_input, "dict"):
        return workflow_input.dict()
    return dict(workflow_input) if workflow_input is not None else {}


# Workflow object (use .task(), not hatchet.step)
aion_workflow = hatchet.workflow(
    name=AionWorkflow.WORKFLOW_NAME,
    on_events=[AionWorkflow.TRIGGER_EVENT],
)


@aion_workflow.task(name="execute_agent", retries=3)
@aion_trace("AgentExecution")
def execute_agent(workflow_input: Any, context: Context) -> dict[str, Any]:
    """Run the agent; Meta-Memory pre-hook, exception analyzer post-hook."""
    from aion.memory.store import MetaMemory

    payload = _workflow_input_to_dict(workflow_input)
    task = payload.get("task", "")
    model = payload.get("model", "openai:gpt-4o-mini")
    system_prompt = payload.get("system_prompt", "You are a helpful AI.")
    policy_names = payload.get("policy_names") or []

    meta_memory = MetaMemory()
    warnings = meta_memory.get_warnings_for_task(task, limit=2)
    if warnings:
        block = "WARNING - PAST FAILURES TO AVOID:\n"
        block += "\n".join(f"- {w}" for w in warnings)
        system_prompt = f"{system_prompt}\n\n{block}"
        print(f"🧠 [Memory] Injected {len(warnings)} past failure warning(s) into prompt.")

    def _wrap_tool(fn: Any) -> Any:
        try:
            return aion_trace(f"ToolCall:{fn.__name__}")(fn)
        except Exception:
            return fn
    tools: list[Any] = [
        _wrap_tool(_fetch_data),
        _wrap_tool(_fetch_user_data),
        _wrap_tool(get_metrics_snapshot),
        _wrap_tool(get_recent_events),
        _wrap_tool(get_available_sources),
        _wrap_tool(get_app_context),
        _wrap_tool(save_note),
        _wrap_tool(_transfer_funds),
        _wrap_tool(_find_lead_info),
        _wrap_tool(_draft_outreach),
        _wrap_tool(_send_email),
        _wrap_tool(_fetch_url_content),
        _wrap_tool(_extract_structured_data),
    ]
    agent = Agent(
        model,
        system_prompt=system_prompt or "You are a helpful AI.",
        tools=tools,
    )

    token = _current_aion_context.set(AionContext(context))
    try:
        print(f"🚀 [Aion Worker] Executing task: {task}")
        result = agent.run_sync(task)
        output = result.output
        output = _apply_post_process(str(output), policy_names)
        print("✅ [Aion Worker] Task completed.")
        return {"result": output}
    except (OpenAIAuthError, ModelHTTPError) as e:
        is_auth = isinstance(e, OpenAIAuthError) or (
            isinstance(e, ModelHTTPError) and getattr(e, "status_code", None) == 401
        )
        if is_auth:
            msg = "OpenAI authentication failed. Set a valid OPENAI_API_KEY in .env or your environment."
            print(f"❌ [Aion Worker] {msg}")
            # Return instead of raise so Hatchet marks the step completed (no traceback, no retries)
            return {"result": None, "error": msg}
        raise
    except Exception as e:
        analyzer = ExceptionAnalyzer()
        asyncio.run(analyzer.analyze_and_store(task_context=task, exception=e))
        print("❌ [Aion Worker] Task failed; stored in MetaMemory and re-raising for retry.")
        raise e
    finally:
        _current_aion_context.reset(token)


# Alias for CLI registration (register_workflow expects a workflow object)
AionWorkflowImpl = aion_workflow


# --- Planner workflow: plan step + execute step (spawn child workflows) ---

PLANNER_EVENT = "aion:planner_task"
SUBTASK_WORKFLOW_NAME = "AionWorkflow"


def _run_planner_llm(goal: str, model: str, system_prompt: str) -> list[str]:
    """Use PydanticAI to output a Plan (steps list)."""
    from pydantic import BaseModel
    class PlanSchema(BaseModel):
        steps: list[str]
    planner_agent = Agent(
        model,
        system_prompt=(
            system_prompt
            or "You are a planner. Break the user goal into a short ordered list of concrete steps. Output only a JSON object with a single key 'steps' (array of strings)."
        ),
        result_type=PlanSchema,
    )
    result = planner_agent.run_sync(
        f"Goal: {goal}. Output a JSON object with key 'steps' (array of step strings)."
    )
    return result.output.steps


planner_workflow = hatchet.workflow(name="AionPlannerWorkflow", on_events=[PLANNER_EVENT])


@planner_workflow.task(name="plan", retries=2)
def plan_step(workflow_input: Any, context: Context) -> dict[str, Any]:
    payload = _workflow_input_to_dict(workflow_input)
    goal = payload.get("task", "")
    model = payload.get("model", "openai:gpt-4o-mini")
    system_prompt = payload.get("system_prompt", "")
    steps = _run_planner_llm(goal, model, system_prompt)
    return {"steps": steps, "model": model, "system_prompt": system_prompt, "policy_names": payload.get("policy_names") or []}


@planner_workflow.task(name="execute_plan", parents=[plan_step], retries=1)
def execute_plan(workflow_input: Any, context: Context) -> dict[str, Any]:
    plan_output = context.step_output("plan")
    steps = plan_output.get("steps") or []
    model = plan_output.get("model", "openai:gpt-4o-mini")
    system_prompt = plan_output.get("system_prompt", "")
    policy_names = plan_output.get("policy_names") or []
    all_tools: list[Any] = [
        _fetch_data, _fetch_user_data, _transfer_funds,
        _find_lead_info, _draft_outreach, _send_email,
        _fetch_url_content, _extract_structured_data,
    ]
    agent = Agent(model, system_prompt=system_prompt or "You are a helpful AI.", tools=all_tools)
    results = []
    for step in steps:
        token = _current_aion_context.set(AionContext(context))
        try:
            result = agent.run_sync(step)
            out = _apply_post_process(str(result.output), policy_names)
            results.append(out)
        finally:
            _current_aion_context.reset(token)
    return {"results": results}


AionPlannerWorkflowImpl = planner_workflow
