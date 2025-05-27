from pydantic import BaseModel


class ChatRealtimeInput(BaseModel):
    thread_id: str


__all__ = ["ChatRealtimeInput"]
