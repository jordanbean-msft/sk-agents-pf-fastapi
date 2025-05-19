"""
Alarm Event Router for Azure Event Hub integration.
- Exposes /v1/alarm endpoint to trigger Semantic Kernel agent workflow.
- Pulls events from Azure Event Hub using Azure SDK (with Managed Identity if available).
- Kicks off agent reasoning workflow on event receipt.

Security: Uses Managed Identity (if available) for authentication. No credentials are hardcoded.
Error handling, logging, and configuration are included per Azure best practices.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from azure.eventhub.aio import EventHubConsumerClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import AzureError

import asyncio

from app.routers.dependencies import EventHubClient

router = APIRouter()

logger = logging.getLogger("alarm_event_router")

async def process_event(event):
    # TODO: here
    x = 1

async def on_event(partition_context, event):
    try:
        #await process_event(event)
        logging.info(
            'Received the event: "{}" from the partition with ID: "{}"'.format(
                event.body_as_str(encoding="UTF-8"), partition_context.partition_id
            )
        )
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
        # Run the event receiver for a short period (demo: 10 seconds)
        await asyncio.wait_for(receive_events(event_hub_client), timeout=10)
        return {"status": "Event processing triggered."}
    except asyncio.TimeoutError:
        return {"status": "Event processing started (timeout reached)."}
    except Exception as e:
        logger.error(f"Failed to process events: {e}")
        raise HTTPException(status_code=500, detail="Failed to process events from Event Hub.")
