"""
Tests for Phase 4 Observability: setup_telemetry, @aion_trace, and patterns.

Verifies OTEL configuration, span decorator behavior, and that DurableWebScraper
and DurableSDR are available and dispatch correctly.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aion.patterns import DurableSDR, DurableWebScraper
from aion.telemetry import aion_trace, setup_telemetry


# --- setup_telemetry ---


def test_setup_telemetry_accepts_service_name_and_endpoint() -> None:
    """setup_telemetry(service_name, endpoint) runs without error and uses endpoint/env."""
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        setup_telemetry(service_name="TestService", endpoint="http://127.0.0.1:4317")
        mock_exporter.assert_called_once()
        call_kw = mock_exporter.call_args[1]
        assert call_kw.get("endpoint") == "http://127.0.0.1:4317"
        assert call_kw.get("insecure") is True


def test_setup_telemetry_uses_default_endpoint_when_endpoint_none() -> None:
    """When endpoint is None, uses OTEL_EXPORTER_OTLP_ENDPOINT or DEFAULT_OTLP_ENDPOINT."""
    from aion.telemetry.tracer import DEFAULT_OTLP_ENDPOINT
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        with patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://custom:4317"}, clear=False):
            setup_telemetry(service_name="Aion")  # no endpoint arg
            mock_exporter.assert_called_once()
            assert mock_exporter.call_args[1]["endpoint"] == "http://custom:4317"
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        with patch.dict("os.environ", {}, clear=False):
            try:
                del __import__("os").environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
            except KeyError:
                pass
            setup_telemetry(service_name="Aion")
            assert mock_exporter.call_args[1]["endpoint"] == DEFAULT_OTLP_ENDPOINT


# --- aion_trace decorator ---


def test_aion_trace_returns_value() -> None:
    """aion_trace(name) decorator runs the function and returns its result."""
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        mock_exporter.return_value.export = MagicMock(return_value=None)
        mock_exporter.return_value.force_flush = MagicMock(return_value=True)
        mock_exporter.return_value.shutdown = MagicMock()
        setup_telemetry(service_name="Test", endpoint="http://localhost:4317")

    @aion_trace("TestSpan")
    def fn() -> int:
        return 42

    assert fn() == 42


def test_aion_trace_reraises_exception() -> None:
    """aion_trace records the exception and re-raises it."""
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        mock_exporter.return_value.export = MagicMock(return_value=None)
        mock_exporter.return_value.force_flush = MagicMock(return_value=True)
        mock_exporter.return_value.shutdown = MagicMock()
        setup_telemetry(service_name="Test", endpoint="http://localhost:4317")

    @aion_trace("FailSpan")
    def fn() -> None:
        raise ValueError("expected")

    with pytest.raises(ValueError, match="expected"):
        fn()


def test_aion_trace_preserves_function_name() -> None:
    """Wrapped function keeps __name__ for tool spans."""
    with patch("aion.telemetry.tracer.OTLPSpanExporter") as mock_exporter:
        mock_exporter.return_value.export = MagicMock(return_value=None)
        mock_exporter.return_value.force_flush = MagicMock(return_value=True)
        mock_exporter.return_value.shutdown = MagicMock()
        setup_telemetry(service_name="Test", endpoint="http://localhost:4317")

    @aion_trace("ToolCall:my_tool")
    def my_tool() -> str:
        return "ok"

    assert my_tool.__name__ == "my_tool"
    assert my_tool() == "ok"


# --- Patterns: DurableWebScraper, DurableSDR ---


def test_durable_web_scraper_is_aion_agent() -> None:
    """DurableWebScraper subclasses AionAgent and has default name/model."""
    agent = DurableWebScraper(name="Scraper", model="openai:gpt-4o-mini")
    assert agent.name == "Scraper"
    assert agent.model == "openai:gpt-4o-mini"
    assert "fetch_url_content" in agent.system_prompt or "web" in agent.system_prompt.lower()
    assert len(agent.tools) == 2  # fetch_url_content, extract_structured_data


def test_durable_sdr_is_planner_agent() -> None:
    """DurableSDR subclasses AionPlannerAgent and has SDR system prompt."""
    agent = DurableSDR(name="SDR", model="openai:gpt-4o-mini")
    assert agent.name == "SDR"
    assert "SDR" in agent.system_prompt or "lead" in agent.system_prompt.lower()
    assert len(agent.tools) >= 2  # find_lead_info, draft_outreach


def test_demo_observability_dispatch() -> None:
    """DurableSDR.start(task) dispatches to planner queue (event ID returned)."""
    with patch("aion.patterns.planner.run_planner_workflow") as mock_run:
        mock_run.return_value = "event-123"
        agent = DurableSDR(name="Obs", model="openai:gpt-4o-mini")
        event_id = agent.start("Find CTO of Acme and draft email.")
        assert event_id == "event-123"
        assert mock_run.called
        payload = mock_run.call_args[0][0]
        assert "task" in payload
        assert "model" in payload
        assert payload.get("agent_name") == "Obs"
