# import json
# import logging
# from opentelemetry import trace

# from semantic_kernel import Kernel
# from semantic_kernel.contents import StreamingFileReferenceContent, StreamingTextContent
# from semantic_kernel.agents import AzureAIAgentThread
# from azure.ai.agents.models import ThreadMessageOptions
# from app.agents.alarm_agent.main import create_alarm_agent
# from app.models.chat_create_thread_output import ChatCreateThreadOutput
# from app.models.chat_get_thread import ChatGetThreadInput
# from app.models.chat_input import ChatInput
# from app.models.chat_output import ChatOutput, serialize_chat_output
# from app.models.content_type_enum import ContentTypeEnum
# from app.plugins.alarm_plugin import AlarmPlugin
# from app.services.dependencies import AIProjectClient

# logger = logging.getLogger("uvicorn.error")
# tracer = trace.get_tracer(__name__)

# async def create_thread(azure_ai_client: AIProjectClient):
#         thread = await azure_ai_client.agents.threads.create()

#         return ChatCreateThreadOutput(thread_id=thread.id)

# async def build_chat_results(chat_input: ChatInput, azure_ai_client: AIProjectClient):
#     with tracer.start_as_current_span(name="build_chat_results"):
#         alarm_agent = None
#         try:        
#             kernel = Kernel()

#             alarm_agent = await create_alarm_agent(
#                 client=azure_ai_client,
#                 kernel=kernel
#             )

#             kernel.add_plugin(
#                 plugin=AlarmPlugin(
#                 ),
#                 plugin_name="alarm_plugin"
#             )           
#             thread = await get_agent_thread(chat_input, azure_ai_client, alarm_agent)
                 
#             async for response in alarm_agent.invoke_stream(
#                     thread=thread,
#                     messages=chat_input.content
#             ):
#                 for item in response.items:
#                     if isinstance(item, StreamingTextContent):
#                         yield json.dumps(
#                             obj=ChatOutput(
#                                 content_type=ContentTypeEnum.MARKDOWN,
#                                 content=response.content.content,
#                                 thread_id=str(response.thread.id),
#                             ),
#                             default=serialize_chat_output,                    
#                         )
#                     elif isinstance(item, StreamingFileReferenceContent):
#                         yield json.dumps(
#                             obj=ChatOutput(
#                                 content_type=ContentTypeEnum.FILE,
#                                 content=item.file_id if item.file_id else "",
#                                 thread_id=str(response.thread.id),
#                             ),
#                             default=serialize_chat_output,                    
#                         )
#                     else:
#                         logger.warning(f"Unknown content type: {type(item)}")
            
#             await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)
#         except Exception as e:
#             logger.error(f"Error processing chat: {e}")

#             if alarm_agent is not None:
#                 await azure_ai_client.agents.delete_agent(agent_id=alarm_agent.id)

# async def get_agent_thread(chat_input, azure_ai_client, alarm_agent):
#     thread_messages = await get_thread(ChatGetThreadInput(thread_id=chat_input.thread_id), azure_ai_client)

#     messages = []

#     for message in thread_messages:
#         msg = ThreadMessageOptions(
#                     content=message['content'],
#                     role=message['role']
#                 )
#         messages.append(msg)

#     thread = AzureAIAgentThread(
#                 client=alarm_agent.client,
#                 thread_id=chat_input.thread_id,
#                 messages=messages
#             )
    
#     return thread

# async def get_thread(thread_input: ChatGetThreadInput, azure_ai_client: AIProjectClient):
#         messages = []
#         async for msg in azure_ai_client.agents.messages.list(thread_id=thread_input.thread_id):
#             messages.append(msg)

#         return_value = []

#         for message in messages:
#             return_value.append({"role": message.role, "content": message.content})

#         return return_value

# __all__ = [
#     "build_chat_results",
#     "get_agent_thread",
#     "get_thread",
#     "create_thread",
# ]
