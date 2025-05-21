from functools import lru_cache

from openai import AsyncAzureOpenAI
from app.config import get_settings
from app.services.connection_manager import ConnectionManager
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from azure.ai.projects.aio import AIProjectClient
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)
from fastapi import Depends
from typing import Annotated

def create_azure_ai_client():
    creds = DefaultAzureCredential()

    client = AzureAIAgent.create_client(
        credential=creds,
        endpoint=get_settings().azure_ai_agent_endpoint
    )

    return client

async def create_async_azure_ai_client():
    project_client = AIProjectClient(
        endpoint=get_settings().azure_ai_agent_endpoint,
        credential=DefaultAzureCredential()
    )

    async_azure_ai_client = await project_client.inference.get_azure_openai_client(
        api_version=get_settings().azure_ai_agent_api_version,
    )

    return async_azure_ai_client

def create_event_hub_client():
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)

    checkpoint_store = BlobCheckpointStore(
            blob_account_url=get_settings().blob_storage_account_url,
            container_name=get_settings().blob_container_name,
            credential=credential,
        )

    client = EventHubConsumerClient(
        fully_qualified_namespace=get_settings().event_hub_fully_qualified_namespace,
        eventhub_name=get_settings().event_hub_name,
        consumer_group=get_settings().event_hub_consumer_group,
        checkpoint_store=checkpoint_store,
        credential=credential,
    )
    return client

def create_connection_manager():
    return ConnectionManager()

@lru_cache
def get_create_azure_ai_client():
    return create_azure_ai_client()

@lru_cache
def get_create_event_hub_client():
    return create_event_hub_client()

@lru_cache
def get_create_connection_manager():
    return create_connection_manager()

@lru_cache
async def get_create_async_azure_ai_client():
    return await create_async_azure_ai_client()

AzureAIClient = Annotated[AIProjectClient, Depends(get_create_azure_ai_client)]
EventHubClient = Annotated[EventHubConsumerClient, Depends(get_create_event_hub_client)]
ConnectionManagerClient = Annotated[ConnectionManager, Depends(get_create_connection_manager)]
AsyncAzureAIClient = Annotated[AsyncAzureOpenAI, Depends(get_create_async_azure_ai_client)]

__all__ = ["AzureAIClient", "EventHubClient", "ConnectionManagerClient", "AsyncAzureAIClient", "get_create_azure_ai_client", "get_create_event_hub_client", "get_create_connection_manager", "get_create_async_azure_ai_client"]
