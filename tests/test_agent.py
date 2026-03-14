"""
Unit tests for AionAgent.

Asserts initialization, tool registration, and that .start() pushes an event to the queue.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aion import AionAgent, aion_tool


def test_agent_initializes_correctly() -> None:
    """AionAgent initializes with name, model, system_prompt, and optional tools/policies."""
    agent = AionAgent(
        name="TestAgent",
        model="openai:gpt-4o-mini",
        system_prompt="You are helpful.",
    )
    assert agent.name == "TestAgent"
    assert agent.model == "openai:gpt-4o-mini"
    assert agent.system_prompt == "You are helpful."
    assert agent.tools == []
    assert agent.policies == []


def test_tools_are_registered() -> None:
    """Tools passed to __init__ are stored on the agent."""
    @aion_tool
    def my_tool() -> str:
        return "ok"

    agent = AionAgent(
        name="ToolAgent",
        tools=[my_tool],
    )
    assert len(agent.tools) == 1
    assert agent.tools[0].__name__ == "my_tool"


@patch("aion.agent.run_aion_workflow")
def test_start_pushes_event_to_queue(mock_run: MagicMock) -> None:
    """start(task) calls run_aion_workflow with the correct payload and returns event id."""
    mock_run.return_value = "event-456"
    agent = AionAgent(name="StartAgent", model="openai:gpt-4o-mini")
    event_id = agent.start("Hello world")
    assert event_id == "event-456"
    mock_run.assert_called_once()
    payload = mock_run.call_args[0][0]
    assert payload["task"] == "Hello world"
    assert payload["agent_name"] == "StartAgent"
    assert payload["model"] == "openai:gpt-4o-mini"


@patch("aion.agent.run_aion_workflow")
def test_start_applies_policy_pre_process(mock_run: MagicMock) -> None:
    """When policies are set, start() applies pre_process to task before pushing."""
    from aion.middleware.policies import PIIScrubberPolicy
    mock_run.return_value = "event-789"
    agent = AionAgent(
        name="PolicyAgent",
        policies=[PIIScrubberPolicy()],
    )
    agent.start("Contact me at admin@corp.com for details.")
    payload = mock_run.call_args[0][0]
    assert "[REDACTED_PII]" in payload["task"]
    assert "admin@corp.com" not in payload["task"]
