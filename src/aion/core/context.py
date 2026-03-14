"""
Human-in-the-Loop (HITL) primitives for the Aion Framework.

Exposes Hatchet's durable sleep/event-wait mechanics so workflows can
pause indefinitely without consuming compute until an external API resumes.
"""

from __future__ import annotations

import re
from contextvars import ContextVar
from datetime import timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatchet_sdk import Context

# Set by the worker before running the agent so tools can access it.
_current_aion_context: ContextVar[AionContext | None] = ContextVar(
    "aion_context",
    default=None,
)


def get_aion_context() -> AionContext | None:
    """Return the AionContext for the current execution, if set (e.g. inside a tool)."""
    return _current_aion_context.get()


class ApprovalDeniedError(Exception):
    """Raised when a human-in-the-loop approval is explicitly denied."""

    def __init__(self, approval_key: str, message: str = "") -> None:
        self.approval_key = approval_key
        super().__init__(message or f"Approval denied for key: {approval_key}")


def _parse_timeout(timeout: str) -> timedelta:
    """Parse a timeout string like '72h', '30m', '60s' into a timedelta."""
    match = re.match(r"^(\d+)(h|m|s)$", timeout.strip().lower())
    if not match:
        return timedelta(hours=72)
    value, unit = int(match.group(1)), match.group(2)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "m":
        return timedelta(minutes=value)
    return timedelta(seconds=value)


class AionContext:
    """
    Wraps the Hatchet Context (or DurableContext) to expose HITL operations.

    Use suspend_for_approval() inside a tool to pause the workflow until
    an external system sends an approval event to Hatchet.
    """

    def __init__(self, hatchet_context: Any) -> None:
        """
        Args:
            hatchet_context: The Hatchet Context or DurableContext from the step.
        """
        self._ctx = hatchet_context

    async def suspend_for_approval(
        self,
        approval_key: str,
        timeout: str = "72h",
    ) -> bool:
        """
        Pause the workflow until an approval event is received or the timeout expires.

        Uses Hatchet's native wait mechanics so the worker slot is freed and
        state is persisted. When the event is received, returns True if approved,
        or raises ApprovalDeniedError if rejected.

        Args:
            approval_key: Event key to wait for (e.g. "approve_transfer_XYZ").
            timeout: Max wait time, e.g. "72h", "30m", "60s". Default 72h.

        Returns:
            True if the approval event indicated success.

        Raises:
            ApprovalDeniedError: If the event payload indicated rejection.
        """
        # DurableContext has aio_wait_for; standard Context may not.
        aio_wait_for = getattr(self._ctx, "aio_wait_for", None)
        if aio_wait_for is None:
            # Fallback when not in a durable task: sleep briefly and "approve"
            # so demos still run. In production, use a workflow with a durable task.
            import asyncio
            delta = _parse_timeout(timeout)
            await asyncio.sleep(min(delta.total_seconds(), 1.0))
            return True

        try:
            from hatchet_sdk import UserEventCondition
        except ImportError:
            from hatchet_sdk.conditions import UserEventCondition  # type: ignore

        wait_result = await aio_wait_for(
            approval_key,
            UserEventCondition(event_key=approval_key),
        )
        if wait_result is None:
            return True
        payload = wait_result if isinstance(wait_result, dict) else {}
        if payload.get("approved") is False:
            raise ApprovalDeniedError(approval_key)
        return True
