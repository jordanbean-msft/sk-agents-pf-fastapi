import logging
from opentelemetry import trace

from semantic_kernel.contents import FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory, AuthorRole
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep

from app.agents.alarm_agent.main import ALARM_AGENT_NAME
from app.services.dependencies import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RetrieveAlarmDocumentationStep(KernelProcessStep):
    @tracer.start_as_current_span("retrieve_alarm_documentation_step")
    @kernel_function(description="Retrieve alarm documentation")
    async def retrieve_alarm_documentation(self, alarm) -> str:
        logger.debug(f"Retrieving alarm documentation for: {alarm}")
        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == ALARM_AGENT_NAME:
                agent = a
                break

        if not agent:
            return f"{ALARM_AGENT_NAME} not found."

        messages = [
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content="You are a helpful assistant that retrieves alarm documentation."
            ),
            ChatMessageContent(
                role=AuthorRole.USER,
                content=f"Retrieve alarm documentation for {alarm}."
            )
        ]

        final_response = ""
        try:
            async for response in agent.invoke(
                messages=messages, # type: ignore
                on_intermediate_message=on_intermediate_message
            ): 
                final_response += response.content.content
        except Exception as e:
            final_response = f"Error retrieving alarm documentation: {e}"

        logger.debug(f"Final response: {final_response}")

        return final_response
    
async def on_intermediate_message(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")

__all__ = [
    "RetrieveAlarmDocumentationStep",
]