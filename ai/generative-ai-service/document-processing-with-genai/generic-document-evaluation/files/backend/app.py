# import oci
import streamlit as st
import langchain
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from typing import Optional, List, Mapping, Any
from io import StringIO
import datetime
import functools
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
import files.utils.config as config
from files.utils.style import set_page_config
set_page_config()
endpoint = config.ENDPOINT
embeddingModel = config.EMBEDDING_MODEL
generateModel = config.GENERATE_MODEL
compartment_id = config.COMPARTMENT_ID
# oci_signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner() #preferred way but policies needs to be in place to enable instance principal or resource principal https://docs.oracle.com/en-us/iaas/data-flow/using/resource-principal-policies.htm


#-------------------------------------------------------------------
langchain.verbose = False
#-------------------------------------------------------------------
def timeit(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start_time = datetime.datetime.now()
        result = func(*args, **kwargs)
        elapsed_time = datetime.datetime.now() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, str(elapsed_time)))
        return result
    return new_func

#-------------------------------------------------------------------
# Main page setup
# st.set_page_config(page_title="Oracle Gen AI Chat", layout="wide")
st.header("How can I help you today? ")
st.info('Select a page on the side menu or use the chat below.', icon="📄")
with st.sidebar.success("Choose a page above"):
    st.sidebar.markdown(
    f"""
    <style>
    [data-testid='stSidebarNav'] > ul {{
        min-height: 40vh;
    }} 
    </style>
    """,
    unsafe_allow_html=True,)

#-------------------------------------------------------------------
# Instantiate chat LLM and the search agent
llm = ChatOCIGenAI(
    model_id= generateModel,
    service_endpoint= endpoint,
    compartment_id=compartment_id,
    model_kwargs={"temperature": 0.0, "max_tokens": 500}
)

chain = ConversationChain(llm=llm, memory=ConversationSummaryMemory(llm=llm, max_token_limit=500), verbose=False)

#-------------------------------------------------------------------
@timeit
def prompting_llm(prompt, _chain):
    with st.spinner(text="Prompting LLM..."):
        print('\n# '+datetime.datetime.now().astimezone().isoformat()+' =====================================================')
        print("Prompt: "+prompt+"\n")
        response = _chain.invoke(prompt).get("response")
        print("-------------------\nResponse: "+response+"\n")
        return response

#-------------------------------------------------------------------
@timeit
def commands(prompt, last_prompt, last_response):
    command = prompt.split(" ")[0]
    
    if command == "/continue":
        prompt = "Given this question: " + last_prompt + ", continue the following text you already started: " + last_response.rsplit("\n\n", 3)[0]
        response = prompting_llm(prompt, chain)
        return response
        
    elif command == "/history":
        try:
            history = chain.memory.load_memory_variables({"history"}).get("history")
            if history == "":
                return "No history to display"
            else:
                return "Current History Summary:  \n" + history
        except:
            return "The history was cleared"
            
    elif command == "/repeat":
        return last_response
        
    elif command == "/help":
        return "Command list available: /continue, /history, /repeat, /help"

#-------------------------------------------------------------------
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
else:
    chain.memory = st.session_state.history
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
    last_response = ""
else:
    last_response = st.session_state.last_response
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""
    last_prompt = ""
else:
    last_prompt = st.session_state.last_prompt
    
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.divider()

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if prompt.startswith("/"):
        response = commands(prompt, last_prompt, last_response)
        # Display assistant response in chat message container
        with st.chat_message("assistant", avatar="🔮"):
            st.markdown(response)
    else:
        response = prompting_llm(prompt, chain)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
       
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Save chat history buffer to the session
try:
    st.session_state.history = chain.memory
    st.session_state.last_prompt = prompt
    st.session_state.last_response = response
except:
    pass
