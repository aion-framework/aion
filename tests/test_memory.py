"""
Tests for Phase 2 Meta-Memory: store (save_mistake, get_warnings_for_task) and ExceptionAnalyzer.

Mocks OpenAI embeddings so tests run without API keys.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aion.memory.store import MetaMemory


@pytest.fixture
def mock_embedding() -> list[float]:
    """Fixed 1536-dim vector for deterministic similarity (LanceDB uses this for search)."""
    return [0.1] * 1536


@pytest.fixture
def meta_memory_tmp(tmp_path: Path) -> MetaMemory:
    """MetaMemory backed by a temp directory."""
    return MetaMemory(db_path=str(tmp_path / "lancedb"))


@patch("aion.memory.store._get_embedding")
def test_save_mistake_and_get_warnings(
    mock_get_embedding: object,
    meta_memory_tmp: MetaMemory,
    mock_embedding: list[float],
) -> None:
    """Save a mistake then retrieve correction_advice via similarity search."""
    mock_get_embedding.return_value = mock_embedding

    meta_memory_tmp.save_mistake(
        task_context="Fetch the user data for today.",
        error_trace="ValueError: Date must be in YYYY-MM-DD format.",
        correction_advice="Use a date in YYYY-MM-DD format, e.g. 2025-03-14.",
    )

    warnings = meta_memory_tmp.get_warnings_for_task("Fetch the user data for today.", limit=2)
    assert len(warnings) == 1
    assert "YYYY-MM-DD" in warnings[0]


@patch("aion.memory.store._get_embedding")
def test_get_warnings_empty_when_no_mistakes(
    mock_get_embedding: object,
    meta_memory_tmp: MetaMemory,
) -> None:
    """get_warnings_for_task returns [] when table is empty."""
    # Don't save anything; table may be empty or we need to avoid calling _get_embedding
    # when count_rows() is 0 - the implementation returns [] before calling _get_embedding
    warnings = meta_memory_tmp.get_warnings_for_task("Any task.", limit=2)
    assert warnings == []


@patch("aion.memory.store._get_embedding")
def test_save_mistake_called_with_embedding(
    mock_get_embedding: object,
    meta_memory_tmp: MetaMemory,
    mock_embedding: list[float],
) -> None:
    """save_mistake calls _get_embedding with task_context."""
    mock_get_embedding.return_value = mock_embedding
    meta_memory_tmp.save_mistake(
        task_context="Run the report",
        error_trace="Error trace",
        correction_advice="Fix the report.",
    )
    mock_get_embedding.assert_called_once_with("Run the report")


def test_exception_analyzer_stores_correction_without_raising() -> None:
    """ExceptionAnalyzer.analyze_and_store uses LLM response and calls save_mistake; does not raise."""
    import asyncio
    from unittest.mock import MagicMock, patch

    from aion.core.exceptions import ExceptionAnalyzer

    mock_memory = MagicMock()
    with patch("aion.core.exceptions.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Use YYYY-MM-DD format for dates."))]
        )
        MockOpenAI.return_value = mock_client

        analyzer = ExceptionAnalyzer(memory=mock_memory)
        try:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        except ValueError as e:
            asyncio.run(analyzer.analyze_and_store(task_context="Fetch user data for today.", exception=e))

    mock_memory.save_mistake.assert_called_once()
    call_kw = mock_memory.save_mistake.call_args[1]
    assert "Fetch user data for today." in call_kw["task_context"]
    assert "YYYY-MM-DD" in call_kw["correction_advice"]
    assert "Date must be" in call_kw["error_trace"]


def test_fetch_user_data_tool_phase2_contract() -> None:
    """Phase 2 demo_memory relies on _fetch_user_data: invalid date raises, YYYY-MM-DD succeeds."""
    from aion.core.worker import _fetch_user_data

    with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD"):
        _fetch_user_data("today")
    with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD"):
        _fetch_user_data("Oct 12")
    with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD"):
        _fetch_user_data("")

    out = _fetch_user_data("2025-03-14")
    assert "2025-03-14" in out
    assert "sample records" in out or "User data" in out


@patch("aion.memory.store._get_embedding")
def test_get_warnings_respects_limit(
    mock_get_embedding: object,
    meta_memory_tmp: MetaMemory,
    mock_embedding: list[float],
) -> None:
    """get_warnings_for_task returns at most `limit` items."""
    mock_get_embedding.return_value = mock_embedding
    for i in range(3):
        meta_memory_tmp.save_mistake(
            task_context=f"Task {i}",
            error_trace=f"Trace {i}",
            correction_advice=f"Advice {i}",
        )
    warnings = meta_memory_tmp.get_warnings_for_task("Task 1", limit=2)
    assert len(warnings) == 2


def test_traceback_preserved_when_called_from_except_block() -> None:
    """traceback.format_exc() used in analyze_and_store must see the exception when called from worker's except block."""
    import traceback

    def nested_called_from_except() -> str:
        return traceback.format_exc()

    try:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    except ValueError:
        tb = nested_called_from_except()
    assert "Date must be in YYYY-MM-DD" in tb
    assert "ValueError" in tb


def test_analyzer_fallback_when_llm_returns_empty() -> None:
    """When LLM returns empty content, correction_advice falls back to exception message."""
    import asyncio
    from unittest.mock import MagicMock, patch

    from aion.core.exceptions import ExceptionAnalyzer

    mock_memory = MagicMock()
    with patch("aion.core.exceptions.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="   "))]
        )
        MockOpenAI.return_value = mock_client
        analyzer = ExceptionAnalyzer(memory=mock_memory)
        try:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        except ValueError as e:
            asyncio.run(analyzer.analyze_and_store(task_context="Fetch for today.", exception=e))

    mock_memory.save_mistake.assert_called_once()
    call_kw = mock_memory.save_mistake.call_args[1]
    assert "Avoid the action that caused" in call_kw["correction_advice"] or "Date must be" in call_kw["correction_advice"]
