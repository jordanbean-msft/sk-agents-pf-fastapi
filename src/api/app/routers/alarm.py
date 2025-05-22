import logging
import cloudevents
import cloudevents.http
from opentelemetry import trace
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from azure.core.exceptions import AzureError

import asyncio
from asyncio import Queue

from semantic_kernel.processes.kernel_process import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.process_framework.processes.process_alarm import build_process_alarm_process
from app.services.connections import ConnectionManagerClientDependency
from app.services.dependencies import get_create_event_hub_consumer_client, get_create_kernel
#from app.services.processes import get_create_process_alarm_process

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

queue: Queue

async def on_event(partition_context, event):
    try:
        decoded_event = cloudevents.http.from_json(event.body_as_str(encoding="UTF-8"))

        logger.debug(f"Received event: {event.body_as_str(encoding='UTF-8')}")

        # thread_output = await create_thread(azure_ai_client)

        kernel = await get_create_kernel()        

        #queue = Queue()
        #alarm_event_client = AlarmEventClient(queue)
        process = build_process_alarm_process()

        async with await start(
            #process=get_create_process_alarm_process(),
            process=process,
            kernel=kernel,
            initial_event=KernelProcessEvent(id="Start", data=str(decoded_event.data)),
            # TODO: pass in the alarm_event_client here when support is added for this parameter
        ) as process_context:
            _ = await process_context.get_state()
            metadata = _.to_process_state_metadata()
            
        # final_result = ChatOutput(
        #     content_type=ContentTypeEnum.MARKDOWN,
        #     content=final_content,
        #     thread_id=thread_output.thread_id,
        # )

        # final_result_str = json.dumps(
        #     obj=final_result,
        #     default=serialize_chat_output,
        # )

        # await send_message(thread_output.thread_id, "")

        await partition_context.update_checkpoint(event)
    except Exception as e:
        logger.error(f"Error processing event: {e}")

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
        return {"status": "Event processing started in background."}
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
        
    global queue
    queue = Queue()

    while True:
        msg = await queue.get()
        await websocket_connection_manager.send_message(client_id, msg)
    
async def send_message(thread_id: str, message: str):
    try:
        if queue:
            await queue.put(message)
            logger.info(f"Message sent to thread_id {thread_id}: {message}")
                
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message.")

__all__ = ['start_alarm_event_listener']