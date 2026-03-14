"""
OpenTelemetry configuration and decorators for the Aion Framework.

Instruments internal actions (tool latency, agent execution) as OTEL spans
for export to Arize Phoenix, Langfuse, or any OTLP endpoint.
"""

from __future__ import annotations

import functools
import os
from typing import Any, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore[attr-defined]
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Default: local OTLP ingest (Arize Phoenix uses 4317)
DEFAULT_OTLP_ENDPOINT = "http://127.0.0.1:4317"

_tracer: trace.Tracer | None = None


def setup_telemetry(
    service_name: str = "aion",
    endpoint: str | None = None,
) -> None:
    """
    Configure the global OTEL TracerProvider and OTLP Span Exporter.

    If no endpoint is provided, uses OTEL_EXPORTER_OTLP_ENDPOINT from env,
    or defaults to http://127.0.0.1:4317 (local Phoenix/OTLP).

    Args:
        service_name: Service name for the resource.
        endpoint: OTLP gRPC endpoint (e.g. http://127.0.0.1:4317).
    """
    global _tracer
    url = endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTLP_ENDPOINT)
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=url, insecure=True)))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("aion-framework", "1.0.0")


def _get_tracer() -> trace.Tracer:
    if _tracer is None:
        setup_telemetry()
    return trace.get_tracer("aion-framework", "1.0.0")


F = TypeVar("F", bound=Callable[..., Any])


def aion_trace(name: str) -> Callable[[F], F]:
    """
    Decorator that wraps a function in an OTEL span, records inputs,
    duration, and logs exceptions as span events before re-raising.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function", func.__name__)
                try:
                    for i, a in enumerate(args):
                        try:
                            span.set_attribute(f"arg.{i}", str(a)[:500])
                        except Exception:
                            pass
                    for k, v in kwargs.items():
                        try:
                            span.set_attribute(f"kwarg.{k}", str(v)[:500])
                        except Exception:
                            pass
                    result = func(*args, **kwargs)
                    if result is not None:
                        try:
                            span.set_attribute("result_preview", str(result)[:500])
                        except Exception:
                            pass
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper  # type: ignore[return-value]
    return decorator
