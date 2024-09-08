# app.py
import sys
import django
import os
file_dir = "/Users/mirbilal/Desktop/minsir/"
if file_dir not in sys.path:
    sys.path.insert(0, file_dir)

os.environ["DJANGO_SETTINGS_MODULE"] = "minsirx.settings"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true" 
django.setup()
import streamlit as st

from apps.email_manager.service_layer.insurance_chatbot import InsuranceChatbot

import streamlit as st 
from langchain_community.callbacks.streamlit.streamlit_callback_handler import StreamlitCallbackHandler
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from streamlit_chat import message

# Streamlit app logic
st.set_page_config(page_title="Insurance Email Reader", page_icon="📄")
st.header('Welcome to Insurance Email Reader, your insurance email assistant.')

# Initialize chatbot instance
ins_chatbot = InsuranceChatbot()

# Define the tool for querying emails
tool = Tool.from_function(
    func=ins_chatbot.query_from_data_source,
    name="search_emails",
    description="Use this tool to search for data inside emails."
)

# Initialize memory for conversational history
if 'memory' not in st.session_state:
    st.session_state['memory'] = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True
    )

# Create agent with memory and tool (remove `memory` argument from the function call)
agent_executor = create_conversational_retrieval_agent(
    llm=ins_chatbot.openai_llm,
    tools=[tool],
    # The memory argument is already handled internally by the agent creation function.
    verbose=True
)
agent_executor.memory.chat_memory.messages = st.session_state['memory'].chat_memory.messages

# Display previous messages from chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state['messages']:
    message(msg["content"], is_user=msg["role"] == "user")

# Handle user input
user_query = st.text_input("Ask me anything about your emails!")
existing_mem_len_session = 0
existing_mem_len_agent = 0
if user_query:
    # Display user's message
    st.session_state['messages'].append({"role": "user", "content": user_query})
    message(user_query, is_user=True)
    
    # Process response with memory
    # Switch from `run` to `agent_executor()` to support multiple output keys.
    response = agent_executor({"input": user_query})
    st.session_state['messages'].append({"role": "assistant", "content": response['output']})
    existing_mem_len_session = len(st.session_state['memory'].chat_memory.messages)
    existing_mem_len_agent = len(agent_executor.memory.chat_memory.messages)
    # st.session_state['memory'].chat_memory.messages = st.session_state['memory'].chat_memory.messages + agent_executor.memory.chat_memory.messages
    message(response['output'])

# Add a sidebar option to reset chat history
if st.sidebar.button("Reset chat history"):
    st.session_state['messages'] = []
    st.session_state['memory'].clear()  # Clear memory as well