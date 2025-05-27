import asyncio
from typing import ClassVar
import logging
from enum import StrEnum, auto
from opentelemetry import trace

from pydantic import BaseModel, Field

from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    KernelProcessStepState,
    kernel_process_step_metadata
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.utilities.utilities import call_agent, on_intermediate_message

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class FinalRecommendationParameters(BaseModel):
    alarm: str
    systems_number: int
    error_message: str = ""
    documentation: str = ""


class FinalRecommendationState(KernelBaseModel):
    count_of_affected_systems: int = 0
    affected_systems: list[str] = []
    final_answer: str = ""
    chat_history: ChatHistory | None = None


@kernel_process_step_metadata("FinalRecommendationStep")
class FinalRecommendationStep(KernelProcessStep[FinalRecommendationState]):
    state: FinalRecommendationState = Field(
        default_factory=FinalRecommendationState)  # type: ignore

    class Functions(StrEnum):
        SetCountOfAffectedSystems = auto()
        RetrieveFinalRecommendation = auto()

    class OutputEvents(StrEnum):
        FinalRecommendationComplete = auto()
        AffectedSystemAnalysisRecieved = auto()
        FinalRecommendationError = auto()

    system_prompt: ClassVar[str] = """
You are a helpful assistant that summarizes the results from alarm analysis and provides a final recommendation based on the affected systems.
"""

    async def activate(self, state: KernelProcessStepState[FinalRecommendationState]):
        self.state = state.state  # type: ignore
        if self.state.chat_history is None:  # type: ignore
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)  # type: ignore

    @tracer.start_as_current_span(Functions.SetCountOfAffectedSystems)
    @kernel_function(name=Functions.SetCountOfAffectedSystems)
    def set_count_of_affected_systems(self, count: int) -> None:
        logger.debug(f"Setting count of affected systems to: {count}")
        self.state.count_of_affected_systems = count

    @tracer.start_as_current_span(Functions.RetrieveFinalRecommendation)
    @kernel_function(name=Functions.RetrieveFinalRecommendation)
    async def retrieve_final_recommendation(self,
                                            context: KernelProcessStepContext,
                                            params: FinalRecommendationParameters):
        logger.debug(f"Generating final recommendation for alarm: {params.alarm}")

        self.state.affected_systems.append(params.alarm)

        if len(self.state.affected_systems) == self.state.count_of_affected_systems:
            await asyncio.sleep(5)

            logger.debug(f"Final recommendation: {self.state.affected_systems}")

            self.state.chat_history.add_user_message(  # type: ignore
                f"""
Retrieve final recommendation for {params.alarm}.
Use the following systems: {', '.join(self.state.affected_systems)}
"""
            )

            try:
                final_response = await call_agent(
                    agent_name="alarm-agent",
                    chat_history=self.state.chat_history,  # type: ignore
                    on_intermediate_message_param=on_intermediate_message
                )
            except Exception as e:
                final_response = f"Error retrieving final recommendation: {e}"
                logger.error(f"Error retrieving final recommendation: {e}")
                await context.emit_event(
                    process_event=self.OutputEvents.FinalRecommendationError,
                    data=FinalRecommendationParameters(
                        alarm=params.alarm,
                        systems_number=params.systems_number,
                        error_message=str(e),
                    )
                )

            logger.debug(f"Final response: {final_response}")

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            self.state.final_answer = final_response.strip()

            await context.emit_event(
                process_event=self.OutputEvents.FinalRecommendationComplete,
                data="Analysis Complete"
            )
        else:
            logger.debug(
                f"""
Waiting for more affected systems. Current count: {len(self.state.affected_systems)}
"""
            )
            await context.emit_event(
                process_event=self.OutputEvents.AffectedSystemAnalysisRecieved,
                data=self.state.affected_systems
            )


__all__ = [
    "FinalRecommendationStep",
    "FinalRecommendationParameters",
    "FinalRecommendationState",
]
