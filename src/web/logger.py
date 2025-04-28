import logging
import os
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor as blp
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter as ame
from azure.monitor.opentelemetry import configure_azure_monitor
import streamlit as st

from opentelemetry._logs import (
    get_logger_provider,
    set_logger_provider,
)
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)

APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING", "")

@st.cache_resource
def setup_logging():
  configure_azure_monitor(
    connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING,
  )
    # set_logger_provider(LoggerProvider())
    # log_exporter = ame(
    #     connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING,
    # )
    # get_logger_provider().add_log_record_processor(blp(log_exporter))

    # logging_handler = LoggingHandler()
    # logger = logging.getLogger(name)
    # logger.addHandler(logging_handler)

    # return logger

__all__ = ["setup_logging"]
