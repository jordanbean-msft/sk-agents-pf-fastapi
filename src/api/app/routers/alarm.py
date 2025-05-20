import os
import json
import logging
import cloudevents
import cloudevents.http
from opentelemetry import trace
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from azure.core.exceptions import AzureError

import asyncio

from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum
from app.services.chat import build_chat_results, create_thread, get_thread
from app.services.dependencies import AzureAIClient, ConnectionManagerClient, EventHubClient, get_create_azure_ai_client, get_create_connection_manager, get_create_event_hub_client

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

def make_on_event(websocket_connection_manager: ConnectionManagerClient, azure_ai_client: AzureAIClient):
    async def on_event(partition_context, event):
        try:
            event = cloudevents.http.from_json(event.body_as_str(encoding="UTF-8"))

            thread_output = await create_thread(azure_ai_client)

            chat_input = ChatInput(thread_id=thread_output.thread_id, content=json.dumps(event.data))
            
            final_result = ""
            async for result in build_chat_results(chat_input, azure_ai_client):
                chat_output_dict = json.loads(result)
                chat_output = ChatOutput(
                    content_type=ContentTypeEnum(chat_output_dict["content_type"]),
                    content=chat_output_dict["content"],
                    thread_id=chat_output_dict["thread_id"],
                )
                final_result += chat_output.content
                
            await send_message(thread_output.thread_id, final_result, websocket_connection_manager)

            await partition_context.update_checkpoint(event)
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    return on_event

async def receive_events(event_hub_client: EventHubClient, websocket_connection_manager: ConnectionManagerClient, azure_ai_client: AzureAIClient):    
    try:
        async with event_hub_client:
            await event_hub_client.receive(
                on_event=make_on_event(websocket_connection_manager, azure_ai_client),
                starting_position="-1",  # from beginning
            )
    except AzureError as e:
        logger.error(f"Azure Event Hub error: {e}")
        raise
    except Exception as e:
        logger.error(f"General error: {e}")
        raise

#@router.post("/alarm")
def start_alarm_event_listener():
    """
    Triggers pulling events from Azure Event Hub and starts agent workflow.
    """
    try:
        event_hub_client = get_create_event_hub_client()
        websocket_connection_manager = get_create_connection_manager()
        azure_ai_client = get_create_azure_ai_client()

        # Start the event receiver as a background task (no timeout)
        asyncio.create_task(receive_events(event_hub_client, websocket_connection_manager, azure_ai_client))
        return {"status": "Event processing started in background."}
    except Exception as e:
        logger.error(f"Failed to process events: {e}")
        raise HTTPException(status_code=500, detail="Failed to process events from Event Hub.")

@router.websocket("/alarm/{client_id}")
async def websocket_connect(websocket: WebSocket, client_id: str, websocket_connection_manager: ConnectionManagerClient):
    """
    WebSocket endpoint for real-time communication.
    """
    await websocket.accept()
    try:
        await websocket_connection_manager.connect(websocket, client_id)
        logger.info(f"WebSocket connection established for thread_id: {client_id}")
    except WebSocketDisconnect:
        websocket_connection_manager.disconnect(client_id)
        logger.info(f"WebSocket connection closed for thread_id: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        raise HTTPException(status_code=500, detail="WebSocket error.")
    
async def send_message(thread_id: str, message: str, websocket_connection_manager: ConnectionManagerClient):
    try:
        websocket = websocket_connection_manager.active_connections.get(thread_id)

        if websocket is not None:        
            await websocket.send_text(message)
            logger.info(f"Message sent to thread_id {thread_id}: {message}")
        else:
            logger.warning(f"No active WebSocket connection for thread_id {thread_id}.")
            raise HTTPException(status_code=404, detail="WebSocket connection not found.")
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message.")

__all__ = ['start_alarm_event_listener']