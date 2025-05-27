import logging
import time
from typing import Awaitable, Callable
from venv import logger
from enum import StrEnum, auto
from opentelemetry import trace

from pydantic import Field
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    KernelProcessStepState,
    kernel_process_step_metadata
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.steps.run_analysis import RunAnalysisParameters

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class DetermineAffectedSystemsState(KernelBaseModel):
    analysis_results: str = ""


class DetermineAffectedSystemsParameters(KernelBaseModel):
    alarm: str = ""
    send_message: Callable[[str], Awaitable[None]] | None = None


@kernel_process_step_metadata("DetermineAffectedSystemsStep")
class DetermineAffectedSystemsStep(KernelProcessStep):
    state: DetermineAffectedSystemsState = Field(
        default_factory=DetermineAffectedSystemsState)  # type: ignore

    class Functions(StrEnum):
        DetermineAffectedSystems = auto()

    class OutputEvents(StrEnum):
        CountOfAffectedSystems = auto()
        AffectedSystemsDetermined = auto()

    async def activate(self, state: KernelProcessStepState[DetermineAffectedSystemsState]):
        self.state = state.state  # type: ignore

    @tracer.start_as_current_span(Functions.DetermineAffectedSystems)
    @kernel_function(name=Functions.DetermineAffectedSystems)
    async def determine_affected_systems(self,
                                         context: KernelProcessStepContext,
                                         params: DetermineAffectedSystemsParameters):
        logger.debug(f"Determining affected systems for alarm: {params.alarm}")

        time.sleep(5)

        count_of_affected_systems = 3

        await context.emit_event(
            process_event=self.OutputEvents.CountOfAffectedSystems,
            data=count_of_affected_systems
        )

        await params.send_message("""
# Determining affected systems.
""")  # type: ignore

        for i in range(count_of_affected_systems):
            await params.send_message(f"""
Affected system {i} detected.
"""  # type: ignore
            )

            await context.emit_event(
                process_event=self.OutputEvents.AffectedSystemsDetermined,
                data=RunAnalysisParameters(
                    alarm=params.alarm,
                    systems_number=i,
                    send_message=params.send_message
                ))


__all__ = [
    "DetermineAffectedSystemsStep",
    "DetermineAffectedSystemsState",
    "DetermineAffectedSystemsParameters",
]
