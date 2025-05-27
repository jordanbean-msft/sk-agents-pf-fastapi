import logging
from datetime import datetime
import os
from pydoc import cli

from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from azure.ai.agents.models import CodeInterpreterTool
from azure.ai.agents.models import FileSearchTool
from azure.ai.agents.models import ToolSet
from azure.ai.agents.models import FilePurpose
from azure.ai.agents.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)

from app.config import get_settings
from app.models.chat_output_message import ChatOutputMessage
from app.services.dependencies import AIProjectClient

logger = logging.getLogger("uvicorn.error")

async def setup_file_search_tool(client: AIProjectClient, kernel: Kernel) -> FileSearchTool:
    file_search_tool = None

    try:
        files = []
        # upload alarm documentation files to Agent storage
        for file in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/files"):
            file_path = os.path.join(f"{os.path.dirname(os.path.abspath(__file__))}/files", file)
            with open(file_path, "rb") as f:
                file = await client.agents.files.upload(
                    file_path=file_path,
                    purpose=FilePurpose.AGENTS
                )
                logger.info(f"Uploaded {file} to Agent storage.")
                files.append(file.id)

        # create vector store
        vector_store = await client.agents.vector_stores.create(
            file_ids=files,
            name="alarm-documentation"
        )
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise

    # create file search tool
    file_search_tool = FileSearchTool(
        vector_store_ids=[vector_store.id],
    )            

    return file_search_tool

async def create_alarm_agent(client: AIProjectClient, kernel: Kernel) -> AzureAIAgent:
    azure_ai_agent = None

    async for agent in client.agents.list_agents():
        if agent.name == "alarm-agent":
            logger.info(f"Found existing alarm-agent: {agent.id}")
            agent = await client.agents.get_agent(agent.id)
            azure_ai_agent = AzureAIAgent(
                client=client,
                definition=agent,
                kernel=kernel
            )
            break

    if not azure_ai_agent:
        logger.info("Creating new alarm-agent...")
        code_interpreter = CodeInterpreterTool()

        file_search_tool = await setup_file_search_tool(client, kernel)

        toolset = ToolSet()
        toolset.add(code_interpreter)
        toolset.add(file_search_tool)

        agent_definition = await client.agents.create_agent(
            model=get_settings().azure_openai_model_deployment_name,
            name="alarm-agent",
            instructions=f"""
            You are a helpful assistant that can read alarms & make recommendations.
            """,
            toolset=toolset,
        )

        azure_ai_agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            kernel=kernel
        )

    return azure_ai_agent

__all__ = ["create_alarm_agent"]
