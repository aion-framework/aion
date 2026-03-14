"""
E2E-style test for Phase 2 Meta-Memory: first run fails and stores, retry gets warning and succeeds.

Uses mocks for OpenAI and embeddings so no API key is required. Validates the full
worker path: execute_agent -> failure -> analyze_and_store -> save_mistake;
retry -> get_warnings_for_task -> inject into prompt -> success.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Fixed embedding so similarity search finds the stored record
MOCK_EMBEDDING = [0.1] * 1536


def test_phase2_meta_memory_flow_fail_then_retry_with_warning(tmp_path: Path) -> None:
    """
    Simulate Phase 2 E2E: first execute_agent fails (ValueError), analyzer stores in MetaMemory.
    Second execute_agent (retry) gets warnings from MetaMemory and succeeds; prompt contains the warning.
    """
    from aion.core.worker import execute_agent

    db_path = str(tmp_path / "lancedb")
    task = "Fetch the user data for today."
    workflow_input = {
        "task": task,
        "model": "openai:gpt-4o-mini",
        "system_prompt": "You are a helpful assistant. Use fetch_user_data with YYYY-MM-DD.",
        "policy_names": [],
    }
    mock_ctx = MagicMock()
    # execute_agent is a Hatchet Task; call the underlying function
    run_agent = getattr(execute_agent, "fn", execute_agent)

    call_count = 0

    def run_sync_side_effect(*args: object, **kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        result = MagicMock()
        result.output = "User data for 2025-03-14: [sample records]"
        return result

    from aion.memory.store import MetaMemory
    from aion.core.exceptions import ExceptionAnalyzer

    real_memory = MetaMemory(db_path=db_path)
    with (
        patch("aion.memory.store._get_embedding", return_value=MOCK_EMBEDDING),
        patch("aion.core.exceptions.OpenAI") as MockOpenAI,
        patch("aion.core.worker.Agent") as MockAgentClass,
    ):
        MockOpenAI.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Use YYYY-MM-DD format for the date."))]
        )
        real_analyzer = ExceptionAnalyzer(memory=real_memory)

        # Worker imports MetaMemory from aion.memory.store inside execute_agent
        with (
            patch("aion.memory.store.MetaMemory", MagicMock(return_value=real_memory)),
            patch("aion.core.worker.ExceptionAnalyzer", return_value=real_analyzer),
        ):
            mock_agent_instance = MagicMock()
            mock_agent_instance.run_sync.side_effect = run_sync_side_effect
            MockAgentClass.return_value = mock_agent_instance

            # First run: should raise ValueError after storing the mistake
            with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD"):
                run_agent(workflow_input, mock_ctx)

            assert call_count == 1
            # Stored one mistake (via ExceptionAnalyzer -> save_mistake)
            warnings_after_fail = real_memory.get_warnings_for_task(task, limit=2)
            assert len(warnings_after_fail) == 1
            assert "YYYY-MM-DD" in warnings_after_fail[0]

            # Second run (retry): should inject warning and succeed
            result = run_agent(workflow_input, mock_ctx)
            assert result == {"result": "User data for 2025-03-14: [sample records]"}
            assert call_count == 2

            # Agent was created with system_prompt that should include the warning block on second run
            assert MockAgentClass.called
            second_call_kw = MockAgentClass.call_args_list[1].kwargs
            system_prompt_retry = second_call_kw["system_prompt"]
            assert "WARNING - PAST FAILURES TO AVOID" in system_prompt_retry
            assert "YYYY-MM-DD" in system_prompt_retry
