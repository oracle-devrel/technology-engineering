import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OCIGenAIEmbeddings
#from langchain.vectorstores import Qdrant
from langchain_community.vectorstores import Qdrant
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
import oracledb
import files.utils.config as config
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from files.utils.htmlTemplates import bot_template, user_template, css
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.docstore.document import Document
import pandas as pd
import io
# from pages.utils.style import set_page_config
# set_page_config()
# Configuration settings
endpoint = config.ENDPOINT
embeddingModel = config.EMBEDDING_MODEL
generateModel = config.GENERATE_MODEL
compartment_id = config.COMPARTMENT_ID
CONNECT_ARGS = config.CONNECT_ARGS




# Function to extract text from PDF files
def get_pdf_text(pdf_files):
    text = ""
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def format_row(row):
    # row is a pandas.Series or a dictionary
    formatted = []
    for col, val in row.items():
        formatted.append(f"{col}: {val}")
    return "- " + ", ".join(formatted)


def build_prompt(criteria_df, additional_instruction=None, include_ranking_marker =None):
    prompt = "You are document evaluation tool. You received these documents to evaluate. Evaluate each document based on these criteria:\n\n"
    for idx, row in criteria_df.iterrows():
        prompt += format_row(row) + "\n"
    prompt += "\n\n"
    if additional_instruction is not None:
        prompt += f"Additionally, {additional_instruction}"
    if include_ranking_marker is True:
        print('its true babes')
        prompt += f"""At the end of the evaluation, rank all documents from best to worst according to how well they satisfy the given criteria.
                        - Clearly identify the best option overall, providing a detailed explanation of why it ranks highest.
                        - List and discuss the remaining documents in order, explaining their ranking by highlighting both their strengths and weaknesses relative to the criteria.
                    """
    prompt += "\n\n"
    prompt += ( """ Your evaluation should follow these steps:
                1. For each document, assess whether the required information is present and evaluate its quality according to the criteria.
                2. Explaining by going through each criteria.
                3. For each document, assign a category based on your evaluation and the context (e.g., Eligible, Conditionally approved, Rejected, Requires review). 
                Clearly state the assigned category for each document and provide a supporting justification. Not for each criteria!
                4. Do not mention or reveal individual criterion scores or weighting in the narrative. 

                **General Instructions:**
                - Always write in professional English using third-person perspective.
                - Begin each major section with a clear markdown heading (e.g., `## Best Document`).
                - Format all content using proper markdown elements, such as headings, bullet points, tables, and code blocks where appropriate.
                - Use standard markdown table syntax with consistent column counts across all rows.
                - For any visualizations, use only markdown-compatible ASCII tables or representations.
                - Apply consistent formatting and style throughout all sections.
                - If any required information is missing, proceed with the evaluation and include the phrase: 'Info not available' in the appropriate place.

                **Output Format:**
                - Start with a brief introduction of the evaluation.
                - Provide your findings and rationale under clear markdown headings.
                - Always refer to the document by the applicant's or claimant's name (or, if unavailable, by the document type).
                - Only whent here are multiple documents, conclude with a markdown table showing numeric scores for each document on the top 4 most important criteria.
               """
       
    )
    return prompt

# Function to split text into chunks
def get_chunk_text(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create a vector store
def get_vector_store(text_chunks):
    embeddings = OCIGenAIEmbeddings(
        model_id=embeddingModel,
        service_endpoint=endpoint,
        compartment_id=compartment_id
    )

    documents = [Document(page_content=chunk) for chunk in text_chunks]

    if config.DB_TYPE == "oracle":
        try:
            connection = oracledb.connect(**CONNECT_ARGS) #oracledb.connect(oracledb.connect(**CONNECT_ARGS))
            print("Connection to OracleDB successful!")
        except Exception as e:
            print("Connection to OracleDB failed!")
            connection = None

        vectorstore = OracleVS.from_documents(
            documents=documents,
            embedding=embeddings,
            client=connection,
            table_name=config.ORACLE_TABLE_NAME,
            distance_strategy=DistanceStrategy.DOT_PRODUCT,
        )
    else:
        vectorstore = Qdrant.from_documents(
            documents=documents,
            embedding=embeddings,  # Changed from 'embedding' to 'embeddings'
            location=config.QDRANT_LOCATION,
            collection_name=config.QDRANT_COLLECTION_NAME,
            distance_func=config.QDRANT_DISTANCE_FUNC
        )
    
    return vectorstore

# Function to create a conversation chain
def get_conversation_chain(vector_store):
    llm = ChatOCIGenAI(
        model_id=generateModel,
        service_endpoint=endpoint,
        compartment_id=compartment_id,
        model_kwargs={"temperature": 0, "max_tokens": 800}
    )

    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory
    )

    return conversation_chain

def load_documents(pdf_files):
    raw_text = get_pdf_text(pdf_files)

    # Get Text Chunks
    text_chunks = get_chunk_text(raw_text)

    # Create Vector Store
    vector_store = get_vector_store(text_chunks)

    # Create conversation chain
    conversation = get_conversation_chain(vector_store)
    
    return conversation

def evaluate(criteria, conversation, additional_instruction=None, include_ranking_marker=None):
    prompt_criteria = build_prompt(criteria, additional_instruction, include_ranking_marker)
    return conversation({'question': prompt_criteria})
