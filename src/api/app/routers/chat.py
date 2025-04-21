import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

from azure.identity.aio import DefaultAzureCredential

from app.models.chat_input import ChatInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.plugins.alarm_plugin import AlarmPlugin
from app.agents.alarm_agent import create_alarm_agent
from app.config import get_settings
from app.models.content_type_enum import ContentTypeEnum
from app.models.chat_output import ChatOutput
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

async def thread_generator(thread):
    async for message in thread:
        yield {"role": message.role, "content": message.content}

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

            async for content in alarm_agent.invoke_stream(
                    thread_id=chat_input.thread_id,
                    messages=[ChatMessageContent(role=msg.role, content=msg.content) for msg in chat_input.content.messages]):
                yield content.content.content
            
            await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            if alarm_agent is not None:
                await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)
