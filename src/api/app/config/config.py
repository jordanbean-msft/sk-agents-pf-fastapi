from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_model_deployment_name: str
    azure_ai_agent_project_connection_string: str
    application_insights_connection_string: str

@lru_cache
def get_settings():
    return Settings()

__all__ = ["get_settings"]
