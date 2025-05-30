# import json
# import time
# import asyncio
# import threading
# import time
# from services.chat import realtime, transcribe


# import streamlit as st
# from streamlit_extras.bottom_container import bottom

# from semantic_kernel.contents.chat_history import ChatHistory
# from semantic_kernel.contents.utils.author_role import AuthorRole
# from semantic_kernel.contents import ImageContent, TextContent, ChatMessageContent

# from models.chat_output import ChatOutput, deserialize_chat_output
# from models.content_type_enum import ContentTypeEnum
# from services.chat import chat, get_thread, get_image, get_image_contents, create_thread, realtime
# from utilities import output_formatter

# def _handle_user_interaction():
#     st.session_state["waiting_for_response"] = True

# if "waiting_for_response" not in st.session_state:
#     st.session_state["waiting_for_response"] = False

# st.set_page_config(
#     page_title="AI Assistant",
#     page_icon=":robot_face:",
#     layout="centered",
#     initial_sidebar_state="collapsed",
# )

# with open('assets/css/style.css', encoding='utf-8') as f:
#     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

# #st.image("assets/images/aks.svg", width=192)
# st.title("AI Assistant")

# # Initialize session state
# if "messages" not in st.session_state:
#     st.session_state.messages = ChatHistory()

# if "thread_id" not in st.session_state:
#     with st.spinner("Creating thread..."):
#         thread_id = create_thread()
#         st.session_state.thread_id = thread_id

# def render_response(response):
#     full_delta_content = ""
#     images = []
#     for chunk in response:
#         delta = deserialize_chat_output(json.loads(chunk))

#         if delta and delta.content:
#             if delta.content_type == ContentTypeEnum.MARKDOWN:
#                 full_delta_content += delta.content

#                 # Display the content incrementally
#                 # if delta.content.startswith("```python"):
#                 #     st.code(full_delta_content, language="python")
#                 # elif delta.content.startswith("```"):
#                 #     st.code(full_delta_content)
#                 # else:
#                 st.markdown(full_delta_content)
#             elif delta.content_type == ContentTypeEnum.FILE:
#                 image = get_image(file_id=delta.content)
#                 st.image(image=image, use_container_width=True)
#                 images.append(image)

#     st.session_state.messages.add_assistant_message(full_delta_content)

#     for image in images:
#         content = ChatMessageContent(
#                                     role=AuthorRole.ASSISTANT,
#                                     items=[
#                                         ImageContent(data=image)
#                                     ]
#                                 )
#         st.session_state.messages.add_message(content)

# @st.fragment
# def response(question):
#     # Display assistant response in chat message container
#     with st.chat_message(AuthorRole.ASSISTANT):
#         with st.spinner("Reticulating splines..."):
#             response = chat(thread_id=st.session_state.thread_id,
#                             content=question)

#             with st.empty():
#                 render_response(response)

# @st.fragment
# def display_chat_history():
#     # Display chat messages from history on app rerun
#     for message in st.session_state.messages:
#         with st.chat_message(message.role):
#             for item in message.items:
#                 if isinstance(item, TextContent):
#                     st.write(item.text)
#                 elif isinstance(item, ImageContent):
#                     st.image(item.data, use_container_width=True)
#                 else:
#                     raise TypeError(f"Unknown content type: {type(item)}")

# @st.fragment
# def audio_chat():
#     if audio := st.audio_input("Record audio"):
#         question_text = ""
#         with st.chat_message(AuthorRole.USER):
#             with st.spinner("Transcribing..."):
#                 audio_transcription = transcribe(content=audio)

#                 with st.empty():
#                     question_text = str(audio_transcription)

#                     st.markdown(question_text)

#                 st.session_state.messages.add_user_message(question_text)

#         response(question_text)

# if "thread_id" in st.session_state:
#     with st.sidebar:
#         st.subheader(body="Thread ID", divider=True)
#         st.write(st.session_state.thread_id)

#     display_chat_history()

#     if question := st.chat_input(
#         placeholder="Ask me...",
#         on_submit=_handle_user_interaction,
#         disabled=st.session_state["waiting_for_response"],
#     ):
#         # Add user message to chat history
#         st.session_state.messages.add_user_message(question)
#         # Display user message in chat message container
#         with st.chat_message(AuthorRole.USER):
#             st.markdown(question)

#         response(question)
#     # with bottom():
#     #     audio_chat()

# if st.session_state["waiting_for_response"]:
#     st.session_state["waiting_for_response"] = False
#     st.rerun()


import time
import requests # Added import
import threading
import queue
import json
import uuid
import websocket
from streamlit_autorefresh import st_autorefresh

import streamlit as st
from streamlit_extras.bottom_container import bottom

from config import get_settings
from utils import get_user_chats, get_thread, push_to_event_hub, get_chat_title, update_cosmos_record, add_thread_entry_to_cosmos

st.set_page_config(layout="wide")

st.title("Alarm Agent")

websocket.enableTrace(True)

user_id = st.session_state.get("user_id", "default_user")

# 1) Initialize session_state
if 'my_chats' not in st.session_state:
    all_chats = get_user_chats(user_id)
    user_chats = [chat for chat in all_chats if chat["chat_type"] == "USER"]
    sys_chats = [chat for chat in all_chats if chat["chat_type"] == "SYSTEM"]
    st.session_state.my_chats = user_chats
    st.session_state.sys_chats = sys_chats
    print(f"User Chats: {len(st.session_state.my_chats)}")


if 'active_chat_key' not in st.session_state:
    # tuple of ("my" or "sys", chat_name)
    st.session_state.active_chat_key = None

if 'logs' not in st.session_state:
    st.session_state.logs = []

if 'msg_queue' not in st.session_state:
    st.session_state.msg_queue = queue.Queue()

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
    
if 'active_chat_title' not in st.session_state:
    st.session_state.active_chat_title = None

if 'current_chat_display_messages' not in st.session_state: # Added for main chat display
    st.session_state.current_chat_display_messages = []


# def ws_reader(q):
#     async def reader():
#         base_uri = get_settings().services__api__api__0
#         #remove the protocol from the environment variable
#         raw_uri = base_uri.replace("https://", "").replace("http://", "")
#         uri = f"ws://{raw_uri}/v1/alarm/1"
#         async with websockets.connect(uri) as ws:
#             while True:
#                 msg = await ws.recv()
#                 q.put(msg)
#     asyncio.run(reader())

# if 'ws_thread' not in st.session_state:
#     t = threading.Thread(target=ws_reader, args=(st.session_state.msg_queue,), daemon=True)
#     t.start()
#     st.session_state.ws_thread = t

# def on_message(ws, message):
#    st.session_state.msg_queue.put(message)

from dotenv import load_dotenv
import os

# Use a closure to pass msg_queue to on_message
def make_on_message(msg_queue):
    def on_message(ws, message):
        msg_queue.put(message)
    return on_message


def on_error(ws, error):
    print(f"WebSocket Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")


def run_websocket(msg_queue, client_id):
    base_uri = get_settings().services__api__api__0
    # remove the protocol from the environment variable
    raw_uri = base_uri.replace("https://", "").replace("http://", "")
    uri = f"ws://{raw_uri}/v1/alarm/{client_id}"
    ws = websocket.WebSocketApp(
        uri,
        on_message=make_on_message(msg_queue),
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
    print("WebSocket thread started")


if 'client_id' not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())
    print(f"Client ID: {st.session_state.client_id}")

if 'ws_thread' not in st.session_state:
    t = threading.Thread(
        target=run_websocket,
        args=(st.session_state.msg_queue, st.session_state.client_id),
        daemon=True
    )
    t.start()
    st.session_state.ws_thread = t


    # The rest of the code remains unchanged
while not st.session_state.msg_queue.empty():
    st.session_state.sys_chats.insert(0, json.loads(st.session_state.msg_queue.get()))

# st_autorefresh(interval=5000)

st.markdown("""
<style>
  /* 1a) Full‑width buttons in the sidebar */
  [data-testid="stSidebar"] div[data-testid="stButton"] > button {
    width: 100% !important;
    text-align: left;
    padding: 0.5rem 1rem;
    margin-bottom: 0.25rem;
  }
  /* 1b) Highlight specific chats */
  [data-testid="stSidebar"] div[data-testid="stButton"] > button[aria-label="Chat A"] {
    background-color: #e0f7fa !important;  /* pale cyan */
    border: 1px solid #26c6da;
  }
  [data-testid="stSidebar"] div[data-testid="stButton"] > button[aria-label="Chat B"] {
    background-color: #ffebee !important;  /* pale red */
    border: 1px solid #ef5350;
  }
</style>
""", unsafe_allow_html=True)

try:
    raw_api_base_url = get_settings().services__api__api__0
except Exception as e:
    raw_api_base_url = ""
    load_dotenv(override=True)
    raw_api_base_url = os.environ['API_ENDPOINT']    
    raw_api_key = os.environ['API_KEY']
    agent_id = os.environ['AGENT_ID']
    foundry_endpoint = os.environ['FOUNDRY_ENDPOINT']



history = []
selected_tab = st.sidebar.radio("Navigate", ["Chat", "Event Creation"])


if selected_tab == "Chat":
    # — your existing sidebar chat‑list code —
    st.sidebar.markdown("#### System Chats")
    for chat in st.session_state.sys_chats:
        if st.sidebar.button(chat["chat_title"], key=f"sid_sys_{chat['chat_title']}"):
            messages = get_thread(chat["thread_id"], chat['foundry_endpoint'])
            st.session_state.active_chat_key = ("sys", chat["chat_title"])
            st.session_state.current_chat_display_messages = messages
            st.session_state.thread_id = chat["thread_id"]
            st.session_state.active_chat_title = chat["chat_title"]

    st.sidebar.markdown("#### User Chats")
    for chat in st.session_state.my_chats:
        if st.sidebar.button(chat["chat_title"], key=f"sid_sys_{chat['chat_title']}"):
            
            messages = get_thread(chat["thread_id"], chat['foundry_endpoint'])
            st.session_state.active_chat_key = ("user", chat["chat_title"])
            st.session_state.current_chat_display_messages = messages
            st.session_state.thread_id = chat["thread_id"]
            st.session_state.active_chat_title = chat["chat_title"]


    # Display current interactive chat messages
    for msg in st.session_state.current_chat_display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    # Chat Input + Streaming Response
    if prompt := st.chat_input("Chat with the Virtual Operator"):

     
        st.session_state.current_chat_display_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            partial_response = ""

            
            # Ensure raw_api_base_url is available
            if not raw_api_base_url:
                placeholder.markdown("Error: API base URL is not configured.")
            
            if st.session_state.thread_id is None:
                response = requests.post(
                    f"{raw_api_base_url}/api/create_thread?code={raw_api_key}",

                )
                if response.status_code == 200:
                    st.session_state.thread_id = response.json()
                else:
                    placeholder.markdown("Error: Unable to create thread.")

                add_thread_entry_to_cosmos(
                    agent_id=agent_id,
                    thread_id=st.session_state.thread_id,
                    foundry_endpoint=foundry_endpoint,
                    user_id=user_id,
                    chat_type="USER"
                )

            payload = {
                "thread_id": st.session_state.thread_id,
                "message": prompt
            }
            # Note: Adjust '/v1/chat/invoke' if your API endpoint is different
            api_endpoint = f"{raw_api_base_url}/api/run_agent?code={raw_api_key}" 

            try:
                response = requests.post(
                    api_endpoint,
                    json=payload,
                    stream=True
                )
                if response.status_code==200:
                    for chunk in response.iter_content( decode_unicode=True):
                        if chunk:
                            partial_response += chunk
                            placeholder.markdown(partial_response, unsafe_allow_html=True)

                        else:
                            continue

            
            except requests.exceptions.HTTPError as e:
                error_message = f"Error from API: {e.response.status_code}"
                try:
                    error_detail = e.response.json() # Try to get JSON error detail
                    if isinstance(error_detail, dict) and "detail" in error_detail:
                            error_message += f" - {error_detail['detail']}"
                    else:
                        error_message += f" - {e.response.text[:200]}" # Fallback to raw text
                except ValueError: # If response is not JSON
                    error_message += f" - {e.response.text[:200]}"
                partial_response = error_message
                placeholder.markdown(partial_response)
            except requests.exceptions.RequestException as e:
                partial_response = f"Request failed: {e}"
                placeholder.markdown(partial_response)
            except Exception as e:
                partial_response = f"An unexpected error occurred: {e}"
                placeholder.markdown(partial_response)

            # Ensure final response is displayed
            placeholder.markdown(partial_response) 

            if st.session_state.active_chat_title is None:
                convo_string = f"User: {prompt}\nAssistant: {partial_response}"
                chat_title = get_chat_title(convo_string)
                st.session_state.active_chat_title = chat_title

                update_obj = {'chat_title': chat_title}
                update_cosmos_record(st.session_state.thread_id, user_id, **update_obj)
        
            # Indicate that the response is complete
            st.session_state.is_streaming = False


            
        st.session_state.current_chat_display_messages.append({"role": "assistant", "content": partial_response})

elif selected_tab == "Event Creation":
    if st.button("Create Event"):
        message = push_to_event_hub(st.session_state.client_id)
        st.json(message)
        time.sleep(2)

    else:
        st.info("Press the button above to create a new event.")
