"""
Developer abstraction for the Aion Framework.

Developers use AionAgent and @aion_tool without writing Hatchet step decorators.
Execution is dispatched to the Hatchet worker for durability.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from .core.engine import run_aion_workflow

if TYPE_CHECKING:
    from .middleware.policies import BasePolicy

logger = logging.getLogger("aion")

F = TypeVar("F", bound=Callable[..., Any])


def aion_tool(func: F) -> F:
    """
    Decorator for Aion tools. Adds logging when the tool is executed.
    The worker wraps tool execution in OTEL span ToolCall:<name> when telemetry is enabled.
    """
    logger.info("[Aion Tool] Registered tool: %s", func.__name__)

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info("[Aion Tool] Executing tool: %s", func.__name__)
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper  # type: ignore[return-value]


class AionAgent:
    """
    Durable agent interface. Execution is pushed to Hatchet; the LLM
    runs inside the worker, not locally.
    """

    def __init__(
        self,
        name: str,
        model: str = "openai:gpt-4o",
        system_prompt: str = "",
        tools: list[Callable[..., Any]] | None = None,
        policies: list[BasePolicy] | None = None,
    ) -> None:
        """
        Initialize an Aion agent.

        Args:
            name: Agent name (for logging and payload).
            model: Model identifier (e.g. 'openai:gpt-4o').
            system_prompt: System prompt for the LLM.
            tools: Optional list of callables (e.g. decorated with @aion_tool).
            policies: Optional list of input/output policies (PII scrubber, toxicity validator).
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools: list[Callable[..., Any]] = list(tools) if tools else []
        self.policies: list[BasePolicy] = list(policies) if policies else []
        self._policy_names = [type(p).__name__ for p in self.policies]

    def start(self, task: str) -> str:
        """
        Trigger durable execution. Applies policy pre_process to task,
        then pushes to Hatchet. Worker applies post_process to result.

        Args:
            task: User task string for the agent.

        Returns:
            Hatchet event/run identifier.
        """
        scrubbed = task
        for policy in self.policies:
            scrubbed = policy.pre_process(scrubbed)
        payload = {
            "agent_name": self.name,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "task": scrubbed,
            "policy_names": self._policy_names,
        }
        print("📡 [Aion Client] Dispatching durable task to Hatchet queue...")
        event_id = run_aion_workflow(payload)
        return event_id
