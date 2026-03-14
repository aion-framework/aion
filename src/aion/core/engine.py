"""
Core engine for the Aion Framework.

Manages the connection to the Hatchet execution engine and provides
a base workflow abstraction for durable agent execution.
"""

from __future__ import annotations

from typing import Any

from hatchet_sdk import Hatchet

_hatchet_instance: Hatchet | None = None


def get_hatchet(debug: bool = False) -> Hatchet:
    """
    Return the singleton Hatchet client instance.

    Uses dependency-injection-friendly singleton pattern so that tests
    can override the client if needed.

    Args:
        debug: If True, enable Hatchet debug logging.

    Returns:
        The Hatchet client instance.
    """
    global _hatchet_instance
    if _hatchet_instance is None:
        _hatchet_instance = Hatchet(debug=debug)
    return _hatchet_instance


def run_aion_workflow(payload: dict[str, Any]) -> str:
    """
    Trigger the Aion workflow on the Hatchet engine (durable execution).

    Does not execute the LLM locally; pushes an event so that a running
    worker picks up the task and executes it with checkpointing/retries.

    Args:
        payload: Workflow input (e.g. task, model, system_prompt, agent_name).

    Returns:
        The event or run identifier from Hatchet.
    """
    client = get_hatchet()
    # Event triggers the workflow registered as on_events=["aion:agent_task"]
    event_id = client.event.push("aion:agent_task", payload)
    return event_id


class AionWorkflow:
    """
    Base Hatchet workflow for Aion agent execution.

    The actual workflow definition (with steps) lives in the worker module;
    this class serves as the conceptual base and naming contract ("AionWorkflow").
    Workers register the concrete workflow that listens for aion:agent_task events.
    """

    WORKFLOW_NAME: str = "AionWorkflow"
    TRIGGER_EVENT: str = "aion:agent_task"
