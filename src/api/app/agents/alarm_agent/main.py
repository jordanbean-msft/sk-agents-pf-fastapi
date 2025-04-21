import logging
from datetime import datetime

from semantic_kernel.agents import AzureAIAgent

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")

async def create_alarm_agent(client, kernel) -> AzureAIAgent:
    agent_definition = await client.agents.create_agent(
        model=get_settings().azure_openai_model_deployment_name,
        name="alarm-agent",
        instructions=f"""
          You are a helpful assistant that can read alarms & make recommendations. The current datetime is {datetime.now().isoformat()}.
        """
    )

    agent = AzureAIAgent(
        client=client,
        definition=agent_definition,
        kernel=kernel,
    )

    return agent

__all__ = ["create_alarm_agent"]
