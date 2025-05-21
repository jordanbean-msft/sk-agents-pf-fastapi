import logging
import urllib
import json
import csv
from typing import Annotated
import requests
from opentelemetry import trace
from msal import ConfidentialClientApplication

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from azure.ai.agents.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class AlarmPlugin:
       def __init__(self, ):
            self.thread_id = ''  
    # @tracer.start_as_current_span(name="lookup_alarm_docs")
    # @kernel_function(description="Executes a HTTP REST API call to the Azure Monitor API, using the Prometheus query language (PromQL) for querying and aggregating metrics & time series data.")
    # async def call_azure_monitor(self,
    #                             method: Annotated[str, "The HTTP REST API method (GET, POST) to make"],
    #                             url: Annotated[str, "The HTTP REST API URL to call. This should only be the Prometheus HTTP API path (using the v1 API specification)"],
    #                             params: Annotated[str, "The HTTP REST API query parameters to append to the URL. Start and End parameters must be in RFC3339 format."],
    #                             body: Annotated[str,
    #                                             "The HTTP REST API body to pass in. This should be a valid PromQL query if the method is POST."]
    #                             ) -> Annotated[str, "The result of the HTTP REST API call"]:

__all__ = ["AlarmPlugin",]