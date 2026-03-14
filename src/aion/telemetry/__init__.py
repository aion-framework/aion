"""OpenTelemetry instrumentation for the Aion Framework."""

from .tracer import aion_trace, setup_telemetry

__all__ = ["aion_trace", "setup_telemetry"]
