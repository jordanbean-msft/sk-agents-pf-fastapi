from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_model_deployment_name: str
    azure_ai_agent_endpoint: str
    application_insights_connection_string: str
    azure_openai_transcription_model_deployment_name: str
    azure_openai_transcription_model_api_version: str

    # Azure Event Hub configuration
    event_hub_fully_qualified_namespace: str
    event_hub_name: str
    event_hub_consumer_group: str
    blob_storage_account_url: str
    blob_container_name: str

@lru_cache
def get_settings():
    return Settings() # type: ignore

__all__ = ["get_settings"]
