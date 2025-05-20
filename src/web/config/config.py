from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    event_hub_fully_qualified_namespace: str
    event_hub_name: str
    services__api__api__0: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

@lru_cache
def get_settings():
    return Settings()

__all__ = ["get_settings"]
