import os
import logging
import cloudevents
import cloudevents.http
from opentelemetry import trace
from fastapi import APIRouter, HTTPException
from azure.core.exceptions import AzureError

import asyncio

from app.routers.dependencies import EventHubClient

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def on_event(partition_context, event):
    try:
        event = cloudevents.http.from_json(event.body_as_str(encoding="UTF-8"))

        # TODO: Call LLM here
        


        await partition_context.update_checkpoint(event)
    except Exception as e:
        logger.error(f"Error processing event: {e}")

async def receive_events(event_hub_client: EventHubClient):    
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

@router.post("/alarm")
async def alarm_endpoint(event_hub_client: EventHubClient):
    """
    Triggers pulling events from Azure Event Hub and starts agent workflow.
    """
    try:
        # Start the event receiver as a background task (no timeout)
        asyncio.create_task(receive_events(event_hub_client))
        return {"status": "Event processing started in background."}
    except Exception as e:
        logger.error(f"Failed to process events: {e}")
        raise HTTPException(status_code=500, detail="Failed to process events from Event Hub.")
