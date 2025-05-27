import logging
from typing import Awaitable, Callable, ClassVar
from enum import StrEnum, auto
from opentelemetry import trace

from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    kernel_process_step_metadata
)
from semantic_kernel.processes.kernel_process.kernel_process_step_state import (
    KernelProcessStepState
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from pydantic import BaseModel, Field

from app.process_framework.steps.final_recommendation import FinalRecommendationParameters
from app.process_framework.utilities.utilities import call_agent, on_intermediate_message

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class RetrieveAlarmDocumentationParameters(BaseModel):
    alarm: str
    systems_number: int
    analysis: str
    error_message: str
    send_message: Callable[[str], Awaitable[None]] | None = None


class RetrieveAlarmDocumentationState(KernelBaseModel):
    chat_history: ChatHistory | None = None


@kernel_process_step_metadata("RetrieveAlarmDocumentationStep")
class RetrieveAlarmDocumentationStep(KernelProcessStep[RetrieveAlarmDocumentationState]):
    state: RetrieveAlarmDocumentationState = Field(default_factory=RetrieveAlarmDocumentationState)

    class Functions(StrEnum):
        RetrieveAlarmDocumentation = auto()

    class OutputEvents(StrEnum):
        AlarmDocumentationRetrieved = auto()
        AlarmDocumentationError = auto()

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves alarm documentation. Look in your documentation and find relevant documents related to the alarm message that you have received. Your job is not to interpret the results, just to find relevant documents.
"""

    async def activate(self, state: KernelProcessStepState[RetrieveAlarmDocumentationState]):
        self.state = state.state  # type: ignore
        if self.state.chat_history is None:  # type: ignore
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)  # type: ignore

    @tracer.start_as_current_span(Functions.RetrieveAlarmDocumentation)
    @kernel_function(name=Functions.RetrieveAlarmDocumentation)
    async def retrieve_alarm_documentation(self,
                                           context: KernelProcessStepContext,
                                           params: RetrieveAlarmDocumentationParameters):
        logger.debug(
            f"""
Retrieving alarm documentation for: {params.alarm} with systems number: {params.systems_number}
"""
        )

        self.state.chat_history.add_user_message(  # type: ignore
            f"Retrieve alarm documentation for {params.alarm}.")

        try:
            final_response = await call_agent(
                agent_name="alarm-agent",
                chat_history=self.state.chat_history,  # type: ignore
                on_intermediate_message_param=on_intermediate_message
            )
        except Exception as e:
            final_response = f"Error retrieving alarm documentation: {e}"
            logger.error(f"Error retrieving alarm documentation: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.AlarmDocumentationError,
                data=FinalRecommendationParameters(
                    alarm=params.alarm,
                    systems_number=params.systems_number,
                    error_message=str(e),
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response)  # type: ignore

        await params.send_message(
            f"""***
# Retrieve Alarm Documentation
Retrieved documentation for alarm ```{params.alarm}```.
## Response
{final_response}
"""
        )  # type: ignore

        await context.emit_event(
            process_event=self.OutputEvents.AlarmDocumentationRetrieved,
            data=FinalRecommendationParameters(
                alarm=params.alarm,
                systems_number=params.systems_number,
                documentation=final_response,
                send_message=params.send_message,
            )
        )


__all__ = [
    "RetrieveAlarmDocumentationStep",
    "RetrieveAlarmDocumentationParameters",
    "RetrieveAlarmDocumentationState",
]
