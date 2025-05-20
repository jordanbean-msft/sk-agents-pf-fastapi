from functools import lru_cache
from app.config import get_settings
from app.services.connection_manager import ConnectionManager
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from azure.ai.projects.aio import AIProjectClient
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)
from fastapi import Depends, WebSocket
from typing import Annotated
from pydantic import SecretStr

def create_azure_ai_client():
    ai_agent_settings = AzureAIAgentSettings(
        model_deployment_name=get_settings().azure_openai_model_deployment_name,
        project_connection_string=SecretStr(get_settings().azure_ai_agent_project_connection_string or "")
    )

    creds = DefaultAzureCredential()

    client = AzureAIAgent.create_client(
        credential=creds,
        conn_str=ai_agent_settings.project_connection_string.get_secret_value() if ai_agent_settings.project_connection_string else ""
    )

    return client

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

AzureAIClient = Annotated[AIProjectClient, Depends(get_create_azure_ai_client)]
EventHubClient = Annotated[EventHubConsumerClient, Depends(get_create_event_hub_client)]
ConnectionManagerClient = Annotated[ConnectionManager, Depends(get_create_connection_manager)]

__all__ = ["AzureAIClient", "EventHubClient", "ConnectionManagerClient", "get_create_azure_ai_client", "get_create_event_hub_client", "get_create_connection_manager"]
