import json
import logging
import cloudevents
import cloudevents.http
from opentelemetry import trace
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from azure.core.exceptions import AzureError

import asyncio

from semantic_kernel.processes.kernel_process import KernelProcessEvent, KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.processes.process_alarm import build_process_alarm_process
from app.process_framework.steps.final_recommendation import FinalRecommendationState, FinalRecommendationStep
from app.services.connections import ConnectionManagerClientDependency, get_create_connection_manager
from app.services.dependencies import get_create_event_hub_consumer_client, get_create_kernel

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def on_event(partition_context, event):
    try:
        decoded_event = cloudevents.http.from_json(event.body_as_str(encoding="UTF-8"))

        logger.debug(f"Received event: {event.body_as_str(encoding='UTF-8')}")

        #emit_event, _, queue = chat_context_var.get()

        queue = get_create_connection_manager().get_queue("1")

        if not queue:
            logger.error("Queue not found for client_id '1'.")
            return

        # thread_output = await create_thread(azure_ai_client)

        task = asyncio.create_task(run_alarm_process(decoded_event))
        
        await queue.put(None)

        await partition_context.update_checkpoint(event)
    except Exception as e:
        logger.error(f"Error processing event: {e}")

async def run_alarm_process(decoded_event):
    kernel = await get_create_kernel()        

    process = build_process_alarm_process()

    async with await start(
            process=process,
            kernel=kernel,
            initial_event=KernelProcessEvent(id="Start", data=str(decoded_event.data)),
        ) as process_context:
        process_state = await process_context.get_state()

        final_recommendation_state: KernelProcessStepState[FinalRecommendationState] = next(
                (s.state for s in process_state.steps if s.state.name == FinalRecommendationStep.__name__), None
            ) # type: ignore

        if final_recommendation_state:
            logger.debug(f"Final recommendation state: {final_recommendation_state}")

            final_result = ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content=final_recommendation_state.state.final_answer.strip(), # type: ignore
                    thread_id="asdf",
                )

            final_result_str = json.dumps(
                    obj=final_result,
                    default=serialize_chat_output,
                )

            await send_message("asdf", final_result_str)

        else:
            logger.error("Final recommendation step not found in process state.")

async def receive_events():
    event_hub_client = get_create_event_hub_consumer_client()
    try:
        async with event_hub_client:
            await event_hub_client.receive(
                on_event=on_event,
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
        # Start the event receiver as a background task (no timeout)
        asyncio.create_task(receive_events())
        logger.debug("Event processing started in background.")
    except Exception as e:
        logger.error(f"Failed to process events: {e}")
        raise HTTPException(status_code=500, detail="Failed to process events from Event Hub.")

@router.websocket("/alarm/{client_id}")
async def websocket_connect(websocket: WebSocket, client_id: str, websocket_connection_manager: ConnectionManagerClientDependency):
    """
    WebSocket endpoint for real-time communication.
    """
    try:
        await websocket_connection_manager.connect(websocket, client_id)
        logger.info(f"WebSocket connection established for thread_id: {client_id}")
    except WebSocketDisconnect:
        websocket_connection_manager.disconnect(client_id)
        logger.info(f"WebSocket connection closed for thread_id: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        raise HTTPException(status_code=500, detail="WebSocket error.")

    while True:
        queue = websocket_connection_manager.get_queue(client_id)

        if not queue:
            logger.error(f"Queue not found for client_id: {client_id}")
            break

        msg = await queue.get()

        if msg is not None:
            await websocket_connection_manager.send_message(client_id, msg)
            logger.debug(f"Sent message to client {client_id}: {msg}")

async def send_message(thread_id: str, message: str):
    queue = get_create_connection_manager().get_queue("1")

    if not queue:
        logger.error(f"Queue not found for thread_id: {thread_id}")
        raise HTTPException(status_code=404, detail="Queue not found for thread_id.")
    
    try:
        await queue.put(message)
        logger.info(f"Message put on queue to thread_id {thread_id}: {message}")

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message.")

__all__ = ['start_alarm_event_listener']