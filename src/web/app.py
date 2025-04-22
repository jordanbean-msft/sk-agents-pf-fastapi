import json
import time
import asyncio

import orjson
import streamlit as st

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

from models.chat_output import ChatOutput, deserialize_chat_output
from models.content_type_enum import ContentTypeEnum
from services.chat import chat, get_thread, get_image, get_image_contents, create_thread
from utilities import output_formatter

def _handle_user_interaction():
    st.session_state["waiting_for_response"] = True

if "waiting_for_response" not in st.session_state:
    st.session_state["waiting_for_response"] = False

st.set_page_config(
    page_title="AI Assistant",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="expanded",
)

with open('assets/css/style.css', encoding='utf-8') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

#st.image("assets/images/aks.svg", width=192)
st.title("AI Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = ChatHistory()

if "thread_id" not in st.session_state:
    with st.spinner("Creating thread..."):
        thread_id = create_thread()
        st.session_state.thread_id = thread_id        

if "thread_id" in st.session_state:
    with st.sidebar:
        st.subheader(body="Thread ID", divider=True)
        st.write(st.session_state.thread_id)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            #st.write("".join(list(output_formatter(message.content))))
            st.write(message.content)

    # Accept user input
    if question := st.chat_input(
        placeholder="Ask me...",
        on_submit=_handle_user_interaction,
        disabled=st.session_state["waiting_for_response"]
    ):
        # Add user message to chat history
        st.session_state.messages.add_user_message(question)
        # Display user message in chat message container
        with st.chat_message(AuthorRole.USER):
            st.markdown(question)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Reticulating splines..."):
                response = chat(thread_id=st.session_state.thread_id,
                                content=st.session_state.messages)

                with st.empty():
                    full_delta_content = ""
                    for chunk in response:
                        #delta = ChatOutput.model_validate_json(chunk)
                        delta = deserialize_chat_output(json.loads(chunk))

                        if delta and delta.content_type == ContentTypeEnum.MARKDOWN and delta.content:
                            full_delta_content += delta.content

                            # Display the content incrementally
                            if delta.content.startswith("```python"):
                                st.code(full_delta_content, language="python")
                            elif delta.content.startswith("```"):
                                st.code(full_delta_content)
                            else:
                                st.markdown(full_delta_content)

                            # Uncomment the following line to display the entire response at once
                            #st.write(full_response)
                    #full_response = st.write_stream(response)

                    #full_response = st.write_stream(output_formatter(response))
                    #st.write(output_formatter(full_response))

        st.session_state.messages.add_assistant_message(full_delta_content)

        # image_contents = get_image_contents(thread_id=st.session_state.thread_id)

        # for image_content in image_contents:
        #     if image_content["type"] == "image_file":
        #         image = get_image(file_id=image_content["file_id"])

        #         st.image(image=image, use_container_width=True)

if st.session_state["waiting_for_response"]:
    st.session_state["waiting_for_response"] = False
    st.rerun()
