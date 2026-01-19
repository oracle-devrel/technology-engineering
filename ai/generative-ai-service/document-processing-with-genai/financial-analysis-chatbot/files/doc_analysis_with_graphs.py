"""
Document Analysis with Graphs

This Streamlit application allows users to upload financial documents (PDFs or images), 
extracts and embeds their content, and enables interactive Q&A using Oracle Generative AI models. 
It supports semantic search, summarization, and financial analysis with references to both text 
and visual elements (charts, tables, graphs).

Author: Ali Ottoman
"""

import io
import base64
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.embeddings.oci_generative_ai import OCIGenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from PyPDF2 import PdfReader
from config import COMPARTMENT_ID

def pil_to_base64(img: Image.Image) -> str:
    """
    Convert a PIL Image to a base64-encoded PNG string.

    Args:
        img (Image.Image): The PIL Image to encode.

    Returns:
        str: Base64-encoded PNG image string.
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def extract_text_by_page(pdf_bytes):
    """
    Extract text from each page of a PDF file.

    Args:
        pdf_bytes (bytes): The PDF file content as bytes.

    Returns:
        list: List of strings, each representing the text of a page.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [page.extract_text() or "" for page in reader.pages]

def embed_extraction():
    """
    Main Streamlit app logic for document ingestion, embedding, semantic search, and Q&A.

    - Handles file uploads (PDFs/images).
    - Extracts text and images from documents.
    - Embeds documents using Oracle Generative AI embeddings.
    - Supports semantic search and summarization.
    - Provides a chat interface for financial Q&A with context-aware responses.
    """
    st.title("\U0001F4AC Financial Analytics Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None

    user_question = st.chat_input("Ask a question about the document")

    with st.sidebar:
        st.subheader("Upload Files")
        st.caption("Upload your PDF or image files containing financial reports, charts, or balance sheets.")
        uploaded_files = st.file_uploader(
            "Upload PDF or image", type=["pdf", "png", "jpg"], accept_multiple_files=True
        )
        st.subheader("Configuration")
        super_searcher = st.toggle("Super Searcher")
        st.caption("This button re-engineers your prompt using Command A to ensure the best results from your embeddings")
        st.subheader("Session Control")
        if st.button("🧹 Clear Memory & Context"):
            st.session_state.chat_history = []
            st.session_state.vectorstore = None
            st.success("Session memory and document context cleared!")

    if uploaded_files:
        docs = []
        with st.spinner("Processing files..."):
            for file in uploaded_files:
                if file.type == "application/pdf":
                    pdf_bytes = file.read()
                    pages_text = extract_text_by_page(pdf_bytes)
                    pages_image = convert_from_bytes(pdf_bytes)

                    for i, (page_img, page_text) in enumerate(zip(pages_image, pages_text)):
                        image_data_url = f"data:image/png;base64,{pil_to_base64(page_img)}"
                        combined_text = page_text.strip()
                        docs.append(Document(
                            page_content=combined_text,
                            metadata={"data_url": image_data_url, "page": i + 1, "filename": file.name}
                        ))
                else:
                    img = Image.open(file)
                    b64 = pil_to_base64(img)
                    docs.append(Document(
                        page_content="[IMAGE ONLY]",
                        metadata={"data_url": f"data:image/png;base64,{b64}", "page": 1, "filename": file.name}
                    ))
            st.success(f"✅ Your document has been ingested successfully. Processed {len(docs)} document{'s' if len(docs) > 1 else ''} successfully!")

        embeddings = OCIGenAIEmbeddings(
            model_id="cohere.embed-v4.0",
            service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
            compartment_id=COMPARTMENT_ID,
            model_kwargs={"input_type": "search_document", "embedding_types": ["float"], "output_dimension": 1024}
        )

        st.session_state.vectorstore = Qdrant.from_documents(
            documents=docs,
            embedding=embeddings,
            location=":memory:",
            collection_name="my_documents",
            distance_func="Dot"
        )

    for user_msg, ai_msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            st.markdown(ai_msg)

    if user_question:
        llm = ChatOCIGenAI(
                model_id="meta.llama-4-maverick-17b-128e-instruct-fp8",
                compartment_id=COMPARTMENT_ID,
                model_kwargs={"max_tokens": 2000, "temperature": 0}
        )
        with st.spinner("Summarizing your document..."):
            if "summary" in user_question.lower() or "summarize" in user_question.lower():
                full_content = "\n\n".join([doc.page_content for doc in docs])
                summary_prompt = [
                    SystemMessage(content="You are a financial analyst AI tasked with summarizing corporate financial reports."),
                    HumanMessage(content=f"Please summarize the following document:\n\n{full_content}")
                ]
                summary_response = llm.invoke(summary_prompt)
                st.subheader("📊 Full Report Summary")
                st.write(summary_response.content)
                return
        with st.spinner("Researching your document..."):
            with st.chat_message("user"):
                st.markdown(user_question)

            if super_searcher:
                llm_rewriter = ChatOCIGenAI(
                    model_id="cohere.command-a-03-2025",
                    compartment_id=COMPARTMENT_ID,
                    model_kwargs={"temperature": 0, "max_tokens": 200}
                )
                rewrite_prompt = [
                    SystemMessage(content="You are a query rewriting assistant for semantic search."),
                    HumanMessage(content=f"Rewrite this query to clearly describe the type of document and field involved: '{user_question}'")
                ]
                user_question = llm_rewriter.invoke(rewrite_prompt).content

            # Combine prior context for semantic grounding in retrieval
            if len(st.session_state.chat_history) >= 1:
                prev_user, prev_ai = st.session_state.chat_history[-1]
                user_question = f"{prev_user}\n{prev_ai}\n\nFollow-up question: {user_question}"

            retriever = st.session_state.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
            top_docs = retriever.invoke(user_question)

            counter = 0
            response = None
            for d in top_docs:
                image_data_url = d.metadata.get("data_url", "")
                text_snippet = d.page_content.strip()[:1500]
                context = [
                    SystemMessage(
                        content="""
                                You are a professional financial analyst assistant that specializes in understanding and interpreting corporate financial reports, charts, and balance sheet analysis. You are capable of interpreting both textual content and accompanying visual elements (e.g., charts, tables, graphs) to extract insights. 
                                Your job is to respond to user questions with concise, accurate financial interpretations using both the provided document content and chart images.

                                Your response must meet these rules:

                                1. If the requested information is NOT present in the document or image, respond with exactly: **NULL** (no explanations, no quotes, no formatting, no preamble).
                                2. Otherwise, respond as a financial analyst would:
                                - Use **clear financial terminology** (e.g., “debt-to-equity ratio dropped from 47% to 37%”, “liquidity improved to 170%”).
                                - If the answer is derived from a **chart**, identify the **axes and units** (e.g., “Chart 2a shows the short-term loans as a percentage of total loans on the Y-axis, ranging from 20% to 60%”).
                                - If applicable, indicate **time periods** and **firm size categories** (e.g., “small firms”, “all corporations”).
                                - Be clear, factual, and explanatory and ensure you are answering the question exactly — no fluff or storytelling, or steps.
                                - Be sure to format the answer using markdown for clarity, such as using bullet points or headings if needed.
                                - Ensure your response is from the perspective of a financial analyst, not a generalist AI.

                                You may assume the document is a structured financial analysis containing time-series data, ratios (e.g., ROA, gearing, EBITDA margin), and classifications of companies by size or sector.
                                If a table or chart is involved, refer to its content explicitly (e.g., “as per Chart 3a”).
                                """
                    ),
                ]
                for prev_user, prev_ai in st.session_state.chat_history[-3:]:
                    context.append(HumanMessage(content=prev_user))
                    context.append(SystemMessage(content=prev_ai))
                context.append(HumanMessage(content=[
                    {"type": "text", "text": f"Here is the content:\n{text_snippet}\n\nQuestion: {user_question}"},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]))

                response = llm.invoke(context)
                if "NULL" not in response.content:
                    break
                counter += 1

        with st.chat_message("assistant"):
            if response and "NULL" not in response.content and counter < len(top_docs):
                st.markdown(response.content)
                st.image(top_docs[counter].metadata["data_url"], caption=f"{top_docs[counter].metadata['filename']} — Page {top_docs[counter].metadata['page']}")
            else:
                st.markdown("Information not found in your documents.")

        if response:
            st.session_state.chat_history.append((user_question, response.content))

if __name__ == "__main__":
    embed_extraction()