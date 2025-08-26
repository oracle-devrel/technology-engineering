import streamlit as st
from pages.utils.pdf_parser import PDFParser
from langchain.chains import RetrievalQA
import os
from langchain_community.embeddings import OCIGenAIEmbeddings
import oracledb
import pages.utils.config as config  # Import the configuration
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.vectorstores import Qdrant


def get_text_from_pdf(pdf_path):
    parser = PDFParser(config.COMPARTMENT_ID)
    docs = parser.parse_pdf(pdf_path)
    print("I am here")
    print(docs)
    return docs

def get_text_splitter(pdf_file):
    # Save the uploaded file temporarily
    with open("temp_pdf.pdf", "wb") as f:
        f.write(pdf_file.getbuffer())
    
    # Extract text from the temporary file
    text = get_text_from_pdf("temp_pdf.pdf")
    
    # Remove the temporary file
    os.remove("temp_pdf.pdf")
    print("Ansh text is ")
    print(text)
    print(type(text))
    return text

def create_qa_retrievals(pdf_file_list: list):
    qa_retrievals = []
    for pdf in pdf_file_list:
        texts = get_text_splitter(pdf)
        text_strings = [doc.page_content for doc in texts]
        metadatas = [{"source": f"{i}-{pdf.name}", "topics": doc.metadata['topics'], "page": doc.metadata['page']} for i, doc in enumerate(texts)]

        # Embedding model
        embeddings = OCIGenAIEmbeddings(
            model_id=config.EMBEDDING_MODEL,
            service_endpoint=config.ENDPOINT,
            compartment_id=config.COMPARTMENT_ID
        )
        print("Ansh 2")

        # Vector database
        if config.DB_TYPE == "oracle":
            try:
                connection = oracledb.connect(user=config.ORACLE_USERNAME, password=config.ORACLE_PASSWORD, dsn=config.ORACLE_DSN)
                db = OracleVS.from_documents(
                    documents=text_strings,
                    embedding=embeddings,
                    client=connection,
                    table_name=config.ORACLE_TABLE_NAME,
                    distance_strategy=DistanceStrategy.DOT_PRODUCT,
                )
                print("Connection to OracleDB successful!")
            except Exception as e:
                print("Connection to OracleDB failed!")
                return
        else:
            print("Ansh 3")
            print(text_strings)
            print(type(text_strings))
            db = Qdrant.from_texts(
                texts=text_strings,
                embedding=embeddings,
                location=config.QDRANT_LOCATION,
                metadatas = metadatas,
                collection_name=pdf.name
            )
            print("ansh 4")

        st.info(f"Saving {pdf.name} to vector DB")

        # LLM model
        llm = ChatOCIGenAI(
            model_id=config.GENERATE_MODEL,
            service_endpoint=config.ENDPOINT,
            compartment_id=config.COMPARTMENT_ID,
            model_kwargs={"temperature": 0, "max_tokens": 400}
        )

        qa_tmp = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(
                search_type="similarity", search_kwargs={"k": 2}
            ),
            return_source_documents=True,
        )
        
        qa_retrievals.append(qa_tmp)
    
    return qa_retrievals

def ask_to_all_pdfs_sources(query: str, qa_retrievals):
    responses = []
    progress_text = f"Asking '{query}' to all PDF's"
    total_retrievals = len(qa_retrievals)
    my_bar = st.progress(0, text=progress_text)
    
    for count, qa in enumerate(qa_retrievals):
        result = qa({"query": query})
        if result["source_documents"]:
            tmp_obj = {
                "query": query,
                "response": result["result"],
                "source_document": result["source_documents"][0].metadata["source"].split("-")[1],
            }
            responses.append(tmp_obj)
        else:
            tmp_obj = {
                "query": query,
                "response": result["result"],
                "source_document": "No source document found",
            }
            responses.append(tmp_obj)

        percent_complete = (count + 1) * 100 / total_retrievals
        my_bar.progress(int(percent_complete), text=progress_text)

    return responses
