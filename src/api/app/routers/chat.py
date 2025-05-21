import base64
import logging
from typing import Any, cast
import tempfile
import shutil

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, UploadFile
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    AzureRealtimeWebsocket,
    ListenEvents,
)
from semantic_kernel.contents import RealtimeAudioEvent, RealtimeTextEvent
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.connectors.ai.open_ai.services.azure_audio_to_text import AzureAudioToText

from websockets import ConnectionClosed

from app.models.chat_input import ChatInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.config import get_settings
from app.models.chat_get_image import ChatGetImageInput
from app.models.chat_get_image_contents import ChatGetImageContents
from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.services.chat import build_chat_results, create_thread, get_thread
from app.services.dependencies import AzureAIClient

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="create_thread")
@router.post("/create_thread")
async def create_thread_router(azure_ai_client: AzureAIClient):
    return await create_thread(azure_ai_client) 

@tracer.start_as_current_span(name="get_thread")
@router.get("/get_thread")
async def get_thread_router(thread_input: ChatGetThreadInput, azure_ai_client: AzureAIClient):
    return await get_thread(thread_input, azure_ai_client) 

@tracer.start_as_current_span(name="get_image_contents")
@router.get("/get_image_contents")
async def get_file_path_annotations(thread_input: ChatGetImageContents, azure_ai_client: AzureAIClient):
    messages = []
    async for msg in azure_ai_client.agents.messages.list(thread_id=thread_input.thread_id):
        messages.append(msg)

    return_value = []

    for message in messages:
        return_value.append(
            {
                "type": message.type,
                "file_id": message.image_file.file_id,
            }
        )

    return return_value

@tracer.start_as_current_span(name="get_image")
@router.get("/get_image", response_class=Response)
async def get_image(thread_input: ChatGetImageInput, azure_ai_client: AzureAIClient):   
    file_content_stream = await azure_ai_client.agents.files.get_content(thread_input.file_id)
    if not file_content_stream:
        raise RuntimeError(f"No content retrievable for file ID '{thread_input.file_id}'.")

    chunks = []
    async for chunk in file_content_stream:
        if isinstance(chunk, (bytes, bytearray)):
            chunks.append(chunk)
        else:
            raise TypeError(f"Expected bytes or bytearray, got {type(chunk).__name__}")

    image_data = b"".join(chunks)

    return Response(content=image_data, media_type="image/png")

@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    return StreamingResponse(build_chat_results(chat_input, azure_ai_client))

@router.post("/transcribe")
async def transcribe(file: UploadFile, azure_ai_client: AzureAIClient):
    client = await azure_ai_client.inference.get_azure_openai_client(
        api_version=get_settings().azure_openai_transcription_model_api_version
    )

    audio_to_text_service = AzureAudioToText(
         async_client=client,
         deployment_name=get_settings().azure_openai_transcription_model_deployment_name
    )

    # Save the uploaded file to a temporary file and get its path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    audio_content = AudioContent.from_audio_file(tmp_path)

    user_input = await audio_to_text_service.get_text_content(audio_content=audio_content)

    return user_input.text

@router.websocket('/realtime')
async def realtime_endpoint(websocket: WebSocket,azure_ai_client: AzureAIClient):
    await websocket.accept()
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            end = await websocket.receive_text()

            if end == "END":
                settings = AzureRealtimeExecutionSettings(
                    modalities=['audio'],
                )
                
                # client = await azure_ai_client.inference.get_azure_openai_client(
                #     api_version="2025-03-01-preview"
                # )

                # audio_to_text_service = AzureAudioToText(
                #      async_client=client,
                #      deployment_name="gpt-4o-mini-transcribe"
                # )

                # audio_content = AudioContent(
                #     data=base64.b64encode(cast(Any, audio_bytes)).decode("utf-8")
                # )

                # user_input = await audio_to_text_service.get_text_content(audio_content=audio_content)

                # await websocket.send_text(user_input.text)

                client = await azure_ai_client.inference.get_azure_openai_client(
                    api_version="2024-10-01-preview"
                )

                azure_realtime_websocket_client = AzureRealtimeWebsocket(
                    async_client=client,
                    #deployment_name='gpt-4o-mini-realtime-preview',
                    deployment_name="gpt-4o-mini-transcribe",
                    settings=settings,
                )
                
                async with azure_realtime_websocket_client():
                    await azure_realtime_websocket_client.send(
                        RealtimeAudioEvent(audio=AudioContent(data=base64.b64encode(cast(Any, audio_bytes)).decode("utf-8")))
                    )

                    async for event in azure_realtime_websocket_client.receive():
                        match event:
                            case RealtimeTextEvent():
                                await websocket.send_text(event.text.text)
                            case _:
                                if event.service_event == ListenEvents.RESPONSE_DONE:
                                    logger.info("Response done")
                                    break
                                
                await websocket.send_text("END")
    except (WebSocketDisconnect, ConnectionClosed) as e:
        logger.warning(f"WebSocket error: {e}")
    # except Exception as e:
    #     logger.error(f"Unexpected error: {e}")