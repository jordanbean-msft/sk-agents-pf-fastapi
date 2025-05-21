import asyncio
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
#from semantic_kernel.processes.local_runtime import KernelProcessEvent, start

class RunAnalysisStep(KernelProcessStep):
    @kernel_function(description="Run analysis on alarm")
    def run_analysis(self, alarm, kernel) -> str:
        return f"Running analysis on alarm: {alarm}"
    
__all__ = [
    "RunAnalysisStep",
]