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

class RetrieveAlarmDocumentationStep(KernelProcessStep):
    @kernel_function(description="Retrieve alarm documentation")
    def retrieve_alarm_documentation(self, alarm) -> str:
        return f"Documentation for alarm: {alarm}"
    
__all__ = [
    "RetrieveAlarmDocumentationStep",
]