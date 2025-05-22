import asyncio
import logging
from typing import ClassVar
from opentelemetry import trace
from venv import logger

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
#from semantic_kernel.processes.local_runtime import KernelProcessEvent, start

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RunAnalysisStep(KernelProcessStep):
    @tracer.start_as_current_span("run_analysis_step")
    @kernel_function(description="Run analysis on alarm")
    def run_analysis(self, alarm, kernel) -> str:
        logger.debug(f"Running analysis on alarm: {alarm}")
        return f"Running analysis on alarm: {alarm}"

__all__ = [
    "RunAnalysisStep",
]