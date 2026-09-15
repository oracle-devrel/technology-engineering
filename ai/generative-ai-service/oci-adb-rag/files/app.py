"""Gradio RAG chatbot backed by Oracle Autonomous AI Database."""

import os

import gradio as gr
import oci
import oracledb
from dotenv import load_dotenv
from langchain_oci import ChatOCIGenAI, OCIGenAIEmbeddings
from langchain_oracledb.vectorstores import DistanceStrategy, OracleVS


load_dotenv()


def get_connection():
    """Connect to Autonomous AI Database using its downloaded wallet."""
    wallet_dir = os.environ["TNS_ADMIN"]
    return oracledb.connect(
        user=os.environ["ORACLE_DB_USERNAME"],
        password=os.environ["ORACLE_DB_PASSWORD"],
        dsn=os.environ["ORACLE_DB_DSN"],
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
    )


def get_oci_settings():
    """Read region, compartment, and API-key authentication from ~/.oci/config."""
    profile = os.getenv("OCI_PROFILE", "DEFAULT")
    config = oci.config.from_file(profile_name=profile)
    return {
        "compartment_id": config["compartment_id"],
        "service_endpoint": (
            f"https://inference.generativeai.{config['region']}.oci.oraclecloud.com"
        ),
        "auth_type": "API_KEY",
        "auth_profile": profile,
    }


connection = get_connection()
oci_genai = get_oci_settings()
embeddings = OCIGenAIEmbeddings(
    model_id=os.getenv("OCI_EMBEDDING_MODEL", "cohere.embed-v4.0"),
    **oci_genai,
)
vector_store = OracleVS(
    connection,
    embeddings,
    os.getenv("VECTOR_TABLE", "KNOWLEDGE_CHUNKS"),
    DistanceStrategy.COSINE,
)
llm = ChatOCIGenAI(
    model_id=os.getenv("OCI_CHAT_MODEL", "cohere.command-a-03-2025"),
    **oci_genai,
)


def answer_question(question, _history):
    """Retrieve related chunks with OracleVS and generate a grounded answer."""
    documents = vector_store.similarity_search(question, k=6)
    context = "\n\n".join(
        f"Source: {doc.metadata.get('file_name', 'Unknown')}\n{doc.page_content}"
        for doc in documents
    )
    prompt = f"""Answer only from the enterprise context below.
If the context does not support an answer, say so.
Give a clear direct answer and list the source filenames used.

Enterprise context:
{context}

Question: {question}
"""
    answer = llm.invoke(prompt)
    sources = sorted({doc.metadata.get("file_name", "Unknown") for doc in documents})
    return f"{answer.content}\n\nSources: {', '.join(sources)}"


demo = gr.ChatInterface(
    fn=answer_question,
    title="Enterprise Knowledge Assistant",
    description="Answers are grounded in documents indexed in Oracle Autonomous AI Database.",
    examples=[
        "What are the main AI principles?",
        "What does the policy say about responsible AI?",
    ],
)


if __name__ == "__main__":
    demo.launch()
