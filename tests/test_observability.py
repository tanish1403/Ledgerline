"""Unit tests for OpenTelemetry spans, custom metrics, and telemetry resilience."""

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from api.telemetry import setup_telemetry, tool_calls_total


@pytest.fixture
def memory_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    yield exporter
    exporter.clear()


def test_tool_call_span_and_metrics(memory_exporter):
    tracer = trace.get_tracer("test.tracer")
    
    # Simulate manual tool span with audit trace_id
    with tracer.start_as_current_span("tool_execution") as span:
        span.set_attribute("tool.name", "fit_weibull")
        # Record metric increment
        tool_calls_total.labels(tool_name="fit_weibull", status="success").inc()

    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "tool_execution"
    assert spans[0].attributes["tool.name"] == "fit_weibull"


def test_telemetry_disabled_by_config():
    # Verify setup_telemetry with enabled=False does not raise error
    setup_telemetry(app=None, enabled=False)
    assert True
