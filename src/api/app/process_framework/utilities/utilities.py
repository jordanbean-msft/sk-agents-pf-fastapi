import logging
from opentelemetry import trace
from semantic_kernel.contents import ChatHistory

from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent
)

from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def on_intermediate_message(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")


async def call_agent(agent_name: str,
                     chat_history: ChatHistory,
                     on_intermediate_message_param) -> str:
    agent_manager = get_create_agent_manager()

    agent = None
    for a in agent_manager:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        return f"{agent_name} not found."

    final_response = ""
    try:
        async for response in agent.invoke(
            messages=chat_history.messages,  # type: ignore
            on_intermediate_message=on_intermediate_message_param
        ):
            final_response += response.content.content
    except Exception as e:
        logger.error(f"Error invoking agent {agent_name}: {e}")
        raise

    logger.debug(f"Agent {agent_name} response: {final_response}")

    return final_response

__all__ = [
    "on_intermediate_message",
    "call_agent",
]
