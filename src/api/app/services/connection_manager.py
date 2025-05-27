from asyncio import Queue
from fastapi import WebSocket


class Connection:
    def __init__(self, websocket: WebSocket, queue: Queue):
        self.websocket = websocket
        self.queue = queue


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, Connection] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = Connection(websocket, Queue())

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str):
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            await connection.websocket.send_text(message)

    async def queue_message(self, client_id: str, message: str):
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            await connection.queue.put(message)

    def get_queue(self, client_id: str) -> Queue | None:
        if client_id in self.active_connections:
            return self.active_connections[client_id].queue
        return None


__all__ = ["ConnectionManager"]
