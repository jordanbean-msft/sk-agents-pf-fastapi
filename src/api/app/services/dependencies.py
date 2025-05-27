from typing import Annotated
from functools import lru_cache
from async_lru import alru_cache

from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)
from semantic_kernel import Kernel
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from fastapi import Depends
from app.config import get_settings


def create_azure_ai_client() -> AIProjectClient:
    creds = DefaultAzureCredential()

    client = AzureAIAgent.create_client(
        credential=creds,
        endpoint=get_settings().azure_ai_agent_endpoint
    )

    return client


async def create_async_azure_ai_client() -> AsyncAzureOpenAI:
    project_client = AIProjectClient(
        endpoint=get_settings().azure_ai_agent_endpoint,
        credential=DefaultAzureCredential()
    )

    async_azure_ai_client = await project_client.inference.get_azure_openai_client(
        api_version=get_settings().azure_ai_agent_api_version,
    )

    return async_azure_ai_client


def create_event_hub_client() -> EventHubConsumerClient:
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


async def create_kernel() -> Kernel:
    kernel = Kernel()

    kernel.add_service(AzureChatCompletion(
        async_client=await get_create_async_azure_ai_client(),
        deployment_name=get_settings().azure_openai_model_deployment_name,
    ))

    return kernel


@lru_cache
def get_create_ai_project_client() -> AIProjectClient:
    return create_azure_ai_client()


@lru_cache
def get_create_event_hub_consumer_client() -> EventHubConsumerClient:
    return create_event_hub_client()


@alru_cache
async def get_create_async_azure_ai_client() -> AsyncAzureOpenAI:
    return await create_async_azure_ai_client()


@alru_cache
async def get_create_kernel() -> Kernel:
    return await create_kernel()


AIProjectClientDependency = Annotated[AIProjectClient, Depends(get_create_ai_project_client)]
EventHubConsumerClientDependency = Annotated[EventHubConsumerClient, Depends(
    get_create_event_hub_consumer_client)]
AsyncAzureAIClientDependency = Annotated[AsyncAzureOpenAI,
                                         Depends(get_create_async_azure_ai_client)]
KernelDependency = Annotated[Kernel, Depends(get_create_kernel)]

__all__ = [
    "AIProjectClientDependency",
    "EventHubConsumerClientDependency",
    "AsyncAzureAIClientDependency",
    "KernelDependency",
    "get_create_ai_project_client",
    "get_create_event_hub_consumer_client",
    "get_create_async_azure_ai_client",
    "get_create_kernel",
]
