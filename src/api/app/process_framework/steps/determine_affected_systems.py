import logging
import time
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import Field
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.steps.run_analysis import RunAnalysisParameters

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class DetermineAffectedSystemsState(KernelBaseModel):
    analysis_results: str = ""

@kernel_process_step_metadata("DetermineAffectedSystemsStep")
class DetermineAffectedSystemsStep(KernelProcessStep):
    state: DetermineAffectedSystemsState = Field(default_factory=DetermineAffectedSystemsState) # type: ignore

    class Functions(StrEnum):
        DetermineAffectedSystems = auto()

    class OutputEvents(StrEnum):
        CountOfAffectedSystems = auto()
        AffectedSystemsDetermined = auto()

    async def activate(self, state: KernelProcessStepState[DetermineAffectedSystemsState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.DetermineAffectedSystems)
    @kernel_function(name=Functions.DetermineAffectedSystems)
    async def determine_affected_systems(self, context: KernelProcessStepContext, alarm: str):
        logger.debug(f"Determining affected systems for alarm: {alarm}")

        time.sleep(5)

        count_of_affected_systems = 3

        await context.emit_event(
            process_event=self.OutputEvents.CountOfAffectedSystems,
            data=count_of_affected_systems
        )

        for i in range(count_of_affected_systems):
            await context.emit_event(
                process_event=self.OutputEvents.AffectedSystemsDetermined,
                data=RunAnalysisParameters(
                    alarm=alarm,
                    systems_number=i
                ))
            logger.debug(f"Affected system {i} detected.")

__all__ = [
    "DetermineAffectedSystemsStep",
]