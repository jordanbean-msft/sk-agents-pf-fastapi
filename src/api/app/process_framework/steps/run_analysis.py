import asyncio
import logging
from venv import logger
from enum import StrEnum, auto
from opentelemetry import trace

from pydantic import BaseModel

from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    kernel_process_step_metadata
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.steps.retrieve_alarm_documentation import (
    RetrieveAlarmDocumentationParameters
)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class RetrieveAlarmDocumentationState(KernelBaseModel):
    analysis_results: str


class RunAnalysisParameters(BaseModel):
    alarm: str
    systems_number: int


@kernel_process_step_metadata("RunAnalysisStep")
class RunAnalysisStep(KernelProcessStep):
    class Functions(StrEnum):
        RunAnalysis = auto()

    class OutputEvents(StrEnum):
        AnalysisComplete = auto()
        AnalysisError = auto()

    @tracer.start_as_current_span(Functions.RunAnalysis)
    @kernel_function(name=Functions.RunAnalysis)
    async def run_analysis(self, context: KernelProcessStepContext, params: RunAnalysisParameters):
        logger.debug(
            f"""
Running analysis on alarm: {params.alarm} with systems number: {params.systems_number}
"""
        )
        await asyncio.sleep(5)

        logger.debug(
            f"""
            Analysis complete for alarm: {params.alarm} with systems number: {params.systems_number}
            """
        )
        await context.emit_event(
            process_event=self.OutputEvents.AnalysisComplete,
            data=RetrieveAlarmDocumentationParameters(
                alarm=params.alarm,
                systems_number=params.systems_number,
                error_message="",
                analysis=f"""
Analysis results for alarm: {params.alarm} with systems number: {params.systems_number}
                """
            )
        )

        # TODO: Handle the case where the analysis fails
        if params.systems_number == -1:
            logger.debug(
                f"""
Analysis error for alarm: {params.alarm} with systems number: {params.systems_number}
""")
            await context.emit_event(
                process_event=self.OutputEvents.AnalysisError,
                data=RetrieveAlarmDocumentationParameters(
                    alarm=params.alarm,
                    systems_number=params.systems_number,
                    error_message="Analysis failed",
                    analysis=""
                )
            )


__all__ = [
    "RunAnalysisStep",
    "RunAnalysisParameters",
]
