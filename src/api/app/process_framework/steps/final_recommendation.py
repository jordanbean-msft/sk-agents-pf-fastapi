import asyncio
from typing import ClassVar
import logging
from opentelemetry import trace
from enum import StrEnum, auto

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
#from semantic_kernel.processes.local_runtime import KernelProcessEvent, start
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class FinalRecommendationParameters(BaseModel):
    alarm: str
    systems_number: int
    error_message: str
    documentation: str

class FinalRecommendationState(KernelBaseModel):
    count_of_affected_systems: int = 0
    affected_systems: list[str] = []
    final_answer: str = ""

@kernel_process_step_metadata("FinalRecommendationStep")
class FinalRecommendationStep(KernelProcessStep[FinalRecommendationState]):
    state: FinalRecommendationState = Field(default_factory=FinalRecommendationState) # type: ignore

    class Functions(StrEnum):
        SetCountOfAffectedSystems = auto()
        RetrieveFinalRecommendation = auto()

    class OutputEvents(StrEnum):
        FinalRecommendationComplete = auto()
        AffectedSystemAnalysisRecieved = auto()

    async def activate(self, state: KernelProcessStepState[FinalRecommendationState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.SetCountOfAffectedSystems)
    @kernel_function(name=Functions.SetCountOfAffectedSystems)
    def set_count_of_affected_systems(self, count: int) -> None:
        logger.debug(f"Setting count of affected systems to: {count}")
        self.state.count_of_affected_systems = count

    @tracer.start_as_current_span(Functions.RetrieveFinalRecommendation)
    @kernel_function(name=Functions.RetrieveFinalRecommendation)
    async def retrieve_final_recommendation(self, context: KernelProcessStepContext, params: FinalRecommendationParameters):
        logger.debug(f"Generating final recommendation for alarm: {params.alarm}")

        self.state.affected_systems.append(params.alarm)

        if len(self.state.affected_systems) == self.state.count_of_affected_systems:
            await asyncio.sleep(5)

            logger.debug(f"Final recommendation: {self.state.affected_systems}")

            self.state.final_answer = f"Final recommendation for alarm: {params.alarm} is to check the following systems: {', '.join(self.state.affected_systems)}"

            await context.emit_event(
                process_event=self.OutputEvents.FinalRecommendationComplete,
                data="Analysis Complete"
            )
        else:
            logger.debug(f"Waiting for more affected systems. Current count: {len(self.state.affected_systems)}")
            await context.emit_event(
                process_event=self.OutputEvents.AffectedSystemAnalysisRecieved,
                data=self.state.affected_systems
            )
    
__all__ = [
    "FinalRecommendationStep",
]