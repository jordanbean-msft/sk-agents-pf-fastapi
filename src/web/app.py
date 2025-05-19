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
import uuid  
import streamlit as st  
from streamlit_extras.bottom_container import bottom
from utils import get_user_chats, get_system_chats, push_to_event_hub  # Assuming these functions are defined in utils.py

from dotenv import load_dotenv
import os
import time
import threading
import websockets
import asyncio
import queue
from streamlit_autorefresh import st_autorefresh
import json

load_dotenv('.env', override=True)  # Load environment variables from .env file
  
st.set_page_config(layout="wide")  

st.title("GE Vernova – Virtual Operator")


# 1) Initialize session_state  
if 'my_chats' not in st.session_state:  
    st.session_state.my_chats =get_user_chats()

if 'sys_chats' not in st.session_state:  
    st.session_state.sys_chats = get_system_chats("user_id")

if 'active_chat_key' not in st.session_state:  
    # tuple of ("my" or "sys", chat_name)  
    st.session_state.active_chat_key = None 

if 'logs' not in st.session_state:  
    st.session_state.logs = []  
    
if 'msg_queue' not in st.session_state:
    st.session_state.msg_queue = queue.Queue()

def ws_reader(q):
    async def reader():
        uri = "ws://localhost:6789"
        async with websockets.connect(uri) as ws:
            while True:
                msg = await ws.recv()
                q.put(msg)
    asyncio.run(reader())

if 'ws_thread' not in st.session_state:
    t = threading.Thread(target=ws_reader, args=(st.session_state.msg_queue,), daemon=True)
    t.start()
    st.session_state.ws_thread = t

while not st.session_state.msg_queue.empty():
    st.session_state.sys_chats.insert(0,json.loads(st.session_state.msg_queue.get()))
    
st_autorefresh(interval=5000, key="ws_refresh")

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
raw_api_base_url = os.getenv("raw_api_base_url")
history = []
selected_tab = st.sidebar.radio("Navigate", ["Virtual Operator Chat", "Event Creation"])

if selected_tab == "Virtual Operator Chat":
    # — your existing sidebar chat‑list code —
    st.sidebar.markdown("#### System Chats")
    for chat in st.session_state.sys_chats:
        if st.sidebar.button(chat["chat_title"], key=f"sid_sys_{chat['chat_title']}"):
            st.session_state.active_chat_key = ("sys", chat["chat_title"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### My Chats")
    for chat in st.session_state.my_chats:
        if st.sidebar.button(chat["chat_title"], key=f"sid_my_{chat['chat_title']}"):
            st.session_state.active_chat_key = ("my", chat["chat_title"])

    # — your existing chat‐history display code —
    if st.session_state.active_chat_key:
        chat_type, chat_name = st.session_state.active_chat_key
        chats = st.session_state.my_chats if chat_type == "my" else st.session_state.sys_chats
        history = []
        if st.session_state.active_chat_key:
            history = next(c["messages"] for c in chats if c["chat_title"] == chat_name)

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    # — only here do we call bottom() —
    with bottom():
        prompt = st.chat_input("Chat with Virtual Operator")

elif selected_tab == "Event Creation":
    if st.button("Create Red Flag Event"):
        message = push_to_event_hub()
        st.json(message)
        time.sleep(2)
    
    else:
        st.info("Press the button above to create a new red flag event.")
