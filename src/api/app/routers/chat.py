import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

import orjson
from semantic_kernel import Kernel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import StreamingFileReferenceContent
from semantic_kernel.contents import StreamingTextContent
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    AzureRealtimeWebsocket,
    ListenEvents,
)
from semantic_kernel.contents import RealtimeAudioEvent, RealtimeTextEvent
from semantic_kernel.contents.audio_content import AudioContent
from azure.ai.projects.models import ThreadMessageOptions

from azure.identity.aio import DefaultAzureCredential
from websockets import ConnectionClosed

from app.models.chat_input import ChatInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.plugins.alarm_plugin import AlarmPlugin
from app.agents.alarm_agent import create_alarm_agent
from app.config import get_settings
from app.models.content_type_enum import ContentTypeEnum
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.chat_get_image import ChatGetImageInput
from app.models.chat_get_image_contents import ChatGetImageContents
from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.routers.dependencies import AzureAIClient

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="create_thread")
@router.post("/create_thread")
async def create_thread(azure_ai_client: AzureAIClient):
        thread = await azure_ai_client.agents.create_thread()

        return ChatCreateThreadOutput(thread_id=thread.id)

@tracer.start_as_current_span(name="get_thread")
@router.get("/get_thread")
async def get_thread(thread_input: ChatGetThreadInput, azure_ai_client: AzureAIClient):
        messages = await azure_ai_client.agents.list_messages(thread_id=thread_input.thread_id)

        return_value = []

        for message in messages.data:
            return_value.append({"role": message.role, "content": message.content})

        return return_value

@tracer.start_as_current_span(name="get_image_contents")
@router.get("/get_image_contents")
async def get_file_path_annotations(thread_input: ChatGetImageContents, azure_ai_client: AzureAIClient):
        messages = await azure_ai_client.agents.list_messages(thread_id=thread_input.thread_id)

        return_value = []

        for message in messages.image_contents:
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
        file_content_stream = await azure_ai_client.agents.get_file_content(thread_input.file_id)
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

async def build_chat_results(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    with tracer.start_as_current_span(name="build_chat_results"):
        alarm_agent = None
        try:        
            kernel = Kernel()

            alarm_agent = await create_alarm_agent(
                client=azure_ai_client,
                kernel=kernel
            )

            # kernel.add_plugin(
            #     plugin=AlarmPlugin(
            #         thread_id=chat_input.thread_id
            #     ),
            #     plugin_name="alarm_plugin"
            # )           
            thread = await get_agent_thread(chat_input, azure_ai_client, alarm_agent)
                 
            async for response in alarm_agent.invoke_stream(
                    thread=thread,
                    messages=chat_input.content
            ):
                for item in response.items:
                    if isinstance(item, StreamingTextContent):
                        yield json.dumps(
                            obj=ChatOutput(
                                content_type=ContentTypeEnum.MARKDOWN,
                                content=response.content.content,
                                thread_id=str(response.thread.id),
                            ),
                            default=serialize_chat_output,                    
                        )
                    elif isinstance(item, StreamingFileReferenceContent):
                        yield json.dumps(
                            obj=ChatOutput(
                                content_type=ContentTypeEnum.FILE,
                                content=item.file_id if item.file_id else "",
                                thread_id=str(response.thread.id),
                            ),
                            default=serialize_chat_output,                    
                        )
                    else:
                        logger.warning(f"Unknown content type: {type(item)}")
            
            await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            if alarm_agent is not None:
                await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)

async def get_agent_thread(chat_input, azure_ai_client, alarm_agent):
    thread_messages = await get_thread(ChatGetThreadInput(thread_id=chat_input.thread_id), azure_ai_client)

    messages = []

    for message in thread_messages:
        msg = ThreadMessageOptions(
                    content=message['content'],
                    role=message['role']
                )
        messages.append(msg)

    thread = AzureAIAgentThread(
                client=alarm_agent.client,
                thread_id=chat_input.thread_id,
                messages=messages
            )
    
    return thread

@router.websocket('/realtime')
async def realtime_endpoint(websocket: WebSocket,azure_ai_client: AzureAIClient):
    await websocket.accept()
    try:
         while True:
              chat_realtime_input = await websocket.receive_json()
              audio_bytes = await websocket.receive_bytes()

              settings = AzureRealtimeExecutionSettings(
                   modalities=['audio'],
              )
              
              client = await azure_ai_client.inference.get_azure_openai_client(
                   api_version="2024-10-01-preview"
              )

              azure_realtime_websocket_client = AzureRealtimeWebsocket(
                   async_client=client,
                   deployment_name='gpt-4o-mini-realtime-preview',
                   settings=settings,
              )
              
              async with azure_realtime_websocket_client():
                await azure_realtime_websocket_client.send(
                    RealtimeAudioEvent(
                        audio=AudioContent(
                             data=audio_bytes,
                             data_format="base64",
                             mime_type="audio/wav",)
                    )
                )

                async for event in azure_realtime_websocket_client.receive():
                    if isinstance(event, RealtimeTextEvent):
                        await websocket.send_text(event.text.text)
                    else:
                        logger.warning(f"Unknown event type: {type(event)}")
              
              await websocket.send_text("END")
    except (WebSocketDisconnect, ConnectionClosed) as e:
        logger.warning(f"WebSocket error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")