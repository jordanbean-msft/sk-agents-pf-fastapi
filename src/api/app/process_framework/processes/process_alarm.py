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
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

from app.process_framework.steps.final_recommendation import FinalRecommendationStep
from app.process_framework.steps.retrieve_alarm_documentation import RetrieveAlarmDocumentationStep
from app.process_framework.steps.run_analysis import RunAnalysisStep

def build_process_alarm_process() -> KernelProcess:
      # Create the process builder
    process_builder = ProcessBuilder(
      name="AlarmProcess",
    ) # type: ignore

    # Add the steps
    retrieve_alarm_documentation_step = process_builder.add_step(RetrieveAlarmDocumentationStep)
    run_analysis_step = process_builder.add_step(RunAnalysisStep)
    final_recommendation_step = process_builder.add_step(FinalRecommendationStep)

    # Orchestrate the events
    process_builder.on_input_event("Start").send_event_to(target=retrieve_alarm_documentation_step)

    retrieve_alarm_documentation_step.on_function_result(
        function_name=RetrieveAlarmDocumentationStep.retrieve_alarm_documentation.__name__
    ).send_event_to(
        target=run_analysis_step, function_name=RunAnalysisStep.run_analysis.__name__, parameter_name="alarm"
    )

    #run_analysis_step.on_event("analysis_completed").send_event_to(target=final_recommendation_step)
    run_analysis_step.on_function_result(
        function_name=RunAnalysisStep.run_analysis.__name__
    ).send_event_to(
        target=final_recommendation_step, function_name=FinalRecommendationStep.retrieve_final_recommendation.__name__, parameter_name="alarm"
    )

    process = process_builder.build()

    return process

__all__ = [
    "build_process_alarm_process",
]