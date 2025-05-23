import asyncio
from typing import ClassVar
import logging
from opentelemetry import trace
from enum import Enum

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

from app.process_framework.steps import determine_affected_systems
from app.process_framework.steps.final_recommendation import FinalRecommendationStep
from app.process_framework.steps.retrieve_alarm_documentation import RetrieveAlarmDocumentationStep
from app.process_framework.steps.run_analysis import RunAnalysisStep
from app.process_framework.steps.determine_affected_systems import DetermineAffectedSystemsStep

def build_process_alarm_process() -> KernelProcess:
      # Create the process builder
    process_builder = ProcessBuilder(
      name="AlarmProcess",
    ) # type: ignore

    # Add the steps
    determine_affected_systems_step = process_builder.add_step(DetermineAffectedSystemsStep)
    retrieve_alarm_documentation_step = process_builder.add_step(RetrieveAlarmDocumentationStep)
    run_analysis_step = process_builder.add_step(RunAnalysisStep)
    final_recommendation_step = process_builder.add_step(FinalRecommendationStep)

    # Orchestrate the events
    process_builder.on_input_event("Start").send_event_to(
        target=determine_affected_systems_step,
        parameter_name="alarm",
        )

    determine_affected_systems_step.on_event(DetermineAffectedSystemsStep.OutputEvents.CountOfAffectedSystems).send_event_to(
        target=final_recommendation_step, function_name=FinalRecommendationStep.Functions.SetCountOfAffectedSystems, parameter_name="count"
    )

    determine_affected_systems_step.on_event(
        DetermineAffectedSystemsStep.OutputEvents.AffectedSystemsDetermined
    ).send_event_to(
        target=run_analysis_step, function_name=RunAnalysisStep.Functions.RunAnalysis, parameter_name="params"
    )       

    run_analysis_step.on_event(
        RunAnalysisStep.OutputEvents.AnalysisComplete
    ).send_event_to(
        target=retrieve_alarm_documentation_step, 
        function_name=RetrieveAlarmDocumentationStep.Functions.RetrieveAlarmDocumentation, 
        parameter_name="params"
    )   

    retrieve_alarm_documentation_step.on_event(
        RetrieveAlarmDocumentationStep.OutputEvents.AlarmDocumentationRetrieved
    ).send_event_to(
        target=final_recommendation_step, function_name=FinalRecommendationStep.Functions.RetrieveFinalRecommendation, parameter_name="params"
    )   

    process = process_builder.build()

    return process

__all__ = [
    "build_process_alarm_process",
]