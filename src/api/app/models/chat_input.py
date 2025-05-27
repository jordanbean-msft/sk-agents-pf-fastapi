from pydantic import BaseModel


class ChatInput(BaseModel):
    thread_id: str
    # content: ChatHistory
    content: str


__all__ = ["ChatInput"]
