# See https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-app-insights?tabs=Powershell&pivots=programming-language-python

import logging

from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)

from opentelemetry._logs import set_logger_provider
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import DropAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import set_tracer_provider

from config import config

# Create a resource to represent the service/sample
resource = Resource.create({ResourceAttributes.SERVICE_NAME: config.APPLICATIONINSIGHTS_SERVICE_NAME})

# Suppress health probe logs from the Uvicorn access logger
# Dapr runtime calls it frequently and pollutes the logs


class HealthProbeFilter(logging.Filter):
    def filter(self, record):
        # Suppress log messages containing the health probe request
        return (
            "/health" not in record.getMessage()
            and "/healthz" not in record.getMessage()
        )


def set_up_logging():
    logging.warning(f"Connection string: {config.APPLICATIONINSIGHTS_CONNECTIONSTRING}")
    exporter = AzureMonitorLogExporter.from_connection_string(config.APPLICATIONINSIGHTS_CONNECTIONSTRING)

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    # Log processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Add filters to the handler to only process records from semantic_kernel.
    handler.addFilter(logging.Filter("semantic_kernel"))
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger()
    logger.addHandler(handler)
    # TODO check how to keep console logging less verbose without limiting remote traces
    # logger.setLevel(logging.INFO)

    # Configure logging
    logging.basicConfig(level=logging.WARN)
    logging.getLogger("sk_ext").setLevel(logging.DEBUG)

    # Add the filter to the Uvicorn access logger
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addFilter(HealthProbeFilter())


def set_up_tracing():
    exporter = AzureMonitorTraceExporter(connection_string=config.APPLICATIONINSIGHTS_CONNECTIONSTRING)

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def set_up_metrics():
    exporter = AzureMonitorMetricExporter(connection_string=config.APPLICATIONINSIGHTS_CONNECTIONSTRING)

    # Initialize a metric provider for the application. This is a factory for creating meters.
    meter_provider = MeterProvider(
        metric_readers=[
            PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
        ],
        resource=resource,
        views=[
            # Dropping all instrument names except for those starting with "semantic_kernel"
            View(instrument_name="*", aggregation=DropAggregation()),
            View(instrument_name="semantic_kernel*"),
        ],
    )
    # Sets the global default meter provider
    set_meter_provider(meter_provider)
