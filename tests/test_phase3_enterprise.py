"""
Tests for Phase 3 Enterprise guardrails: policies, planner, and HITL contract.

Verifies that developers can define policies, use AionPlannerAgent with policy pre_process,
and that policy/post_process and HITL contracts behave as documented.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aion.agent import AionAgent
from aion.middleware.policies import (
    PIIScrubberPolicy,
    ToxicityValidatorPolicy,
    SafetyViolationError,
)
from aion.patterns import AionPlannerAgent


# --- Policies ---


def test_pii_scrubber_pre_process() -> None:
    """PIIScrubberPolicy replaces SSN and email in prompt."""
    policy = PIIScrubberPolicy()
    out = policy.pre_process("Contact 123-45-6789 or admin@corp.com for details.")
    assert "123-45-6789" not in out
    assert "admin@corp.com" not in out
    assert "[REDACTED_PII]" in out


def test_pii_scrubber_post_process() -> None:
    """PIIScrubberPolicy replaces PII in response."""
    policy = PIIScrubberPolicy()
    out = policy.post_process("Reply to user@example.com for SSN 111-22-3333.")
    assert "user@example.com" not in out
    assert "111-22-3333" not in out
    assert "[REDACTED_PII]" in out


def test_toxicity_validator_raises_on_restricted() -> None:
    """ToxicityValidatorPolicy raises SafetyViolationError when output contains restricted word."""
    policy = ToxicityValidatorPolicy()
    policy.post_process("Normal output.")
    with pytest.raises(SafetyViolationError, match="confidential_leak"):
        policy.post_process("Do not share confidential_leak data.")


def test_agent_start_applies_policy_pre_process() -> None:
    """AionAgent.start() applies policy pre_process to task before pushing payload."""
    with patch("aion.agent.run_aion_workflow") as mock_run:
        mock_run.return_value = "evt-1"
        agent = AionAgent(
            name="P",
            model="openai:gpt-4o-mini",
            policies=[PIIScrubberPolicy()],
        )
        agent.start("Email me at admin@corp.com")
    payload = mock_run.call_args[0][0]
    assert "[REDACTED_PII]" in payload["task"]
    assert "admin@corp.com" not in payload["task"]
    assert payload["policy_names"] == ["PIIScrubberPolicy"]


def test_planner_start_applies_policy_pre_process() -> None:
    """AionPlannerAgent.start() applies policy pre_process to task and sends policy_names."""
    with patch("aion.patterns.planner.run_planner_workflow") as mock_run:
        mock_run.return_value = "evt-2"
        agent = AionPlannerAgent(
            name="Planner",
            model="openai:gpt-4o-mini",
            policies=[PIIScrubberPolicy()],
        )
        agent.start("My email is admin@corp.com. Plan and execute.")
    payload = mock_run.call_args[0][0]
    assert "[REDACTED_PII]" in payload["task"]
    assert "admin@corp.com" not in payload["task"]
    assert payload["policy_names"] == ["PIIScrubberPolicy"]


def test_planner_inherits_policies_from_base() -> None:
    """AionPlannerAgent has .policies and ._policy_names like AionAgent."""
    agent = AionPlannerAgent(
        name="P",
        policies=[PIIScrubberPolicy(), ToxicityValidatorPolicy()],
    )
    assert len(agent.policies) == 2
    assert agent._policy_names == ["PIIScrubberPolicy", "ToxicityValidatorPolicy"]


def test_worker_apply_post_process_applies_policies_by_name() -> None:
    """Worker _apply_post_process uses policy_names to apply post_process (PII scrub)."""
    from aion.core.worker import _apply_post_process

    out = _apply_post_process("Send reply to admin@corp.com.", ["PIIScrubberPolicy"])
    assert "admin@corp.com" not in out
    assert "[REDACTED_PII]" in out


def test_worker_apply_post_process_unknown_policy_name_ignored() -> None:
    """Unknown policy names in policy_names are skipped (no error)."""
    from aion.core.worker import _apply_post_process

    out = _apply_post_process("Hello world.", ["UnknownPolicy", "PIIScrubberPolicy"])
    assert out == "Hello world."  # PII scrub leaves it; UnknownPolicy skipped


# --- HITL: AionContext contract ---


def test_suspend_for_approval_fallback_when_no_aio_wait_for() -> None:
    """When Hatchet context has no aio_wait_for, suspend_for_approval sleeps briefly and returns True."""
    import asyncio
    from aion.core.context import AionContext

    mock_ctx = MagicMock(spec=[])
    mock_ctx.aio_wait_for = None  # no durable wait
    aion_ctx = AionContext(mock_ctx)

    async def run() -> bool:
        return await aion_ctx.suspend_for_approval("approve_me", timeout="72h")

    result = asyncio.run(run())
    assert result is True
