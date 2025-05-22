from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.services.connection_manager import ConnectionManager


def create_connection_manager() -> ConnectionManager:
    return ConnectionManager()

@lru_cache
def get_create_connection_manager() -> ConnectionManager:
    return create_connection_manager()


ConnectionManagerClientDependency = Annotated[ConnectionManager, Depends(get_create_connection_manager)]