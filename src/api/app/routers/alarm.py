import os
import json
import logging
import time
import cloudevents
import cloudevents.http
from openai import AsyncAzureOpenAI
from opentelemetry import trace
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from azure.core.exceptions import AzureError

import asyncio
from asyncio import Queue

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.agents.alarm_agent.main import create_alarm_agent
from app.config.config import get_settings
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.processes.process_alarm import build_process_alarm_process
from app.services.chat import build_chat_results, create_thread, get_thread
from app.services.dependencies import ConnectionManagerClientDependency, EventHubConsumerClient, get_create_agent_manager, get_create_async_azure_ai_client, get_create_ai_project_client, get_create_event_hub_consumer_client, get_create_kernel

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

queue: Queue

async def on_event(partition_context, event):
    try:
        azure_ai_client = get_create_ai_project_client()

        decoded_event = cloudevents.http.from_json(event.body_as_str(encoding="UTF-8"))

        logger.debug(f"Received event: {event.body_as_str(encoding='UTF-8')}")

        # thread_output = await create_thread(azure_ai_client)

        kernel = await get_create_kernel()

        kernel_process = build_process_alarm_process()

        async with await start(
            process=kernel_process,
            kernel=kernel,
            initial_event=KernelProcessEvent(id="Start", data=decoded_event.data),
        ) as process_context:
            _ = await process_context.get_state()

        # chat_input = ChatInput(thread_id=thread_output.thread_id, content=json.dumps(decoded_event.data))
        
        # final_content = ""
        # async for result in build_chat_results(chat_input, azure_ai_client):
        #     chat_output_dict = json.loads(result)
        #     chat_output = ChatOutput(
        #         content_type=ContentTypeEnum(chat_output_dict["content_type"]),
        #         content=chat_output_dict["content"],
        #         thread_id=chat_output_dict["thread_id"],
        #     )
        #     final_content += chat_output.content
            
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
    
async def setup_agents():
    #kernel = await get_create_kernel()
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        async_client=await get_create_async_azure_ai_client(),
        deployment_name=get_settings().azure_openai_model_deployment_name,
    ))

    alarm_agent = await create_alarm_agent(
        client=get_create_ai_project_client(),
        kernel=kernel
    )

    agent_manager = get_create_agent_manager()

    agent_manager.append(alarm_agent)

async def delete_agents():
    agent_manager = get_create_agent_manager()

    for agent in agent_manager:
        if agent.name == "AlarmAgent":
            agent_manager.remove(agent)
            client = get_create_ai_project_client()
            client.agents.delete_agent(agent.id)
            break

__all__ = ['start_alarm_event_listener', 'setup_agents', 'delete_agents']