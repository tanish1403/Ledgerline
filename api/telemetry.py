"""OpenTelemetry setup, instrumentation, custom metrics, and JSON logging with trace/span IDs."""

import json
import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram

# Prometheus Custom Metrics
tool_calls_total = Counter("tool_calls_total", "Total tool executions", ["tool_name", "status"])
tool_errors_total = Counter("tool_errors_total", "Total tool execution errors", ["tool_name"])
agent_run_duration_seconds = Histogram("agent_run_duration_seconds", "Agent run duration in seconds", ["agent_name"])
llm_tokens_total = Counter("llm_tokens_total", "Total LLM tokens consumed", ["type"])  # input / output
validation_failures_total = Counter("validation_failures_total", "Total validation failures")
approvals_pending = Gauge("approvals_pending", "Number of pending inspection approvals")


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter including OpenTelemetry trace_id and span_id."""

    def format(self, record: logging.LogRecord) -> str:
        span = trace.get_current_span()
        span_context = span.get_span_context() if span else None
        
        trace_id = format(span_context.trace_id, "032x") if span_context and span_context.is_valid else "0" * 32
        span_id = format(span_context.span_id, "016x") if span_context and span_context.is_valid else "0" * 16

        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "trace_id": trace_id,
            "span_id": span_id,
        }
        return json.dumps(log_record)


def setup_telemetry(app: Any = None, enabled: bool = True) -> None:
    """Initialize OpenTelemetry tracer provider and instrumentations."""
    if not enabled:
        return

    provider = TracerProvider()
    try:
        exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    except Exception:
        # Collector optional: app runs even if OTLP collector is unreachable
        pass

    trace.set_tracer_provider(provider)

    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass
