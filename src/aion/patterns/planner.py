"""
Plan-and-Execute pattern for the Aion Framework.

The LLM outputs a JSON array of steps; Aion compiles this into a
parallel/sequential Hatchet DAG via child workflow spawning.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aion.agent import AionAgent
from aion.core.engine import get_hatchet


class Plan(BaseModel):
    """Structured output from the planner: a list of step descriptions."""

    steps: list[str]


def run_planner_workflow(payload: dict[str, Any]) -> str:
    """Trigger the planner workflow (aion:planner_task)."""
    client = get_hatchet()
    event_id = client.event.push("aion:planner_task", payload)
    return event_id


class AionPlannerAgent(AionAgent):
    """
    Agent that breaks a complex goal into steps and executes them via
    Hatchet child workflows (plan-and-execute DAG).

    Inherits from AionAgent; .start() triggers the planner workflow
    instead of a single agent task.
    """

    PLANNER_EVENT: str = "aion:planner_task"

    def start(self, task: str) -> str:
        """
        Trigger the planner workflow: plan step produces Plan(steps),
        then each step is executed as a child workflow.

        Args:
            task: User goal string (will be pre-processed by policies if set).

        Returns:
            Hatchet event/run identifier.
        """
        payload = {
            "agent_name": self.name,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "task": task,
            "policy_names": getattr(self, "_policy_names", []),
        }
        print("📡 [Aion Planner] Dispatching plan-and-execute to Hatchet...")
        return run_planner_workflow(payload)
