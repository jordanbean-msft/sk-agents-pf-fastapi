import logging
from datetime import datetime

from semantic_kernel.agents import AzureAIAgent
from azure.ai.projects.models import CodeInterpreterTool
from azure.ai.projects.models import FileSearchTool
from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)

from app.config import get_settings
from app.models.chat_output_message import ChatOutputMessage

logger = logging.getLogger("uvicorn.error")

async def create_alarm_agent(client, kernel) -> AzureAIAgent:
    code_interpreter = CodeInterpreterTool()
    file_search_tool = FileSearchTool()

    agent_definition = await client.agents.create_agent(
        model=get_settings().azure_openai_model_deployment_name,
        name="alarm-agent",
        instructions=f"""
          You are a helpful assistant that can read alarms & make recommendations.
        """,
        tools=code_interpreter.definitions + file_search_tool.definitions,
        # response_format=ResponseFormatJsonSchemaType(
        #     json_schema=ResponseFormatJsonSchema(
        #         name="chat-output-message",
        #         description="",
        #         schema=ChatOutputMessage.model_json_schema()
        #     )
        # )
    )

    agent = AzureAIAgent(
        client=client,
        definition=agent_definition,
        kernel=kernel
    )

    return agent

__all__ = ["create_alarm_agent"]
