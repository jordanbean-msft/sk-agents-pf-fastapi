from typing import List
from pydantic import BaseModel
from semantic_kernel.contents.chat_history import ChatHistory

class ChatInput(BaseModel):
    thread_id: str
    #content: ChatHistory
    content: str

__all__ = ["ChatInput"]
