"""Simple PDF and DOCX ingestion flow used by the RAG notebook."""

import os
from pathlib import Path

import oci
import oracledb
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_oci import OCIGenAIEmbeddings
from langchain_oracledb.vectorstores import DistanceStrategy, OracleVS
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Change these two paths to your own files.
PROJECT_FILES = Path(__file__).parent
PDF_PATH = PROJECT_FILES / "sample_documents/your-document.pdf"
DOCX_PATH = PROJECT_FILES / "sample_documents/your-document.docx"

load_dotenv()


def get_connection():
    wallet = os.environ["TNS_ADMIN"]
    return oracledb.connect(
        user=os.environ["ORACLE_DB_USERNAME"],
        password=os.environ["ORACLE_DB_PASSWORD"],
        dsn=os.environ["ORACLE_DB_DSN"],
        config_dir=wallet,
        wallet_location=wallet,
        wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
    )


conn = get_connection()
profile = os.getenv("OCI_PROFILE", "DEFAULT")
config = oci.config.from_file(profile_name=profile)
oci_genai = {
    "compartment_id": config["compartment_id"],
    "service_endpoint": f"https://inference.generativeai.{config['region']}.oci.oraclecloud.com",
    "auth_type": "API_KEY",
    "auth_profile": profile,
}


def upload_document(file):
    """Store a local PDF or DOCX as a BLOB in the existing DOCUMENTS table."""
    mime_type = (
        "application/pdf"
        if file.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    with conn.cursor() as cursor:
        document_id = cursor.var(int)
        cursor.execute(
            """
            INSERT INTO documents (file_name, mime_type, content)
            VALUES (:file_name, :mime_type, :content)
            RETURNING document_id INTO :document_id
            """,
            {
                "file_name": file.name,
                "mime_type": mime_type,
                "content": file.read_bytes(),
                "document_id": document_id,
            },
        )
        conn.commit()
        return int(document_id.getvalue())


def load_document(document_id):
    """Read a BLOB from Autonomous AI Database, then use the correct loader."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT file_name, mime_type, content FROM documents WHERE document_id = :id",
            [document_id],
        )
        file_name, mime_type, blob = cursor.fetchone()

    file = PROJECT_FILES / "temp" / file_name
    file.parent.mkdir(exist_ok=True)
    file.write_bytes(blob.read())

    loader = PyPDFLoader(str(file)) if mime_type == "application/pdf" else Docx2txtLoader(str(file))
    pages = loader.load()
    for page in pages:
        page.metadata.update({"document_id": document_id, "file_name": file_name})
    return pages


# 1. Upload the original files to Autonomous AI Database.
pdf_id = upload_document(PDF_PATH)
docx_id = upload_document(DOCX_PATH)

# 2. Read the BLOBs back from Autonomous AI Database and extract text.
pages = load_document(pdf_id) + load_document(docx_id)

# 3. Split text into chunks.
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(pages)

# 4. Embed chunks with OCI Generative AI and store them in OracleVS.
embeddings = OCIGenAIEmbeddings(
    model_id=os.getenv("OCI_EMBEDDING_MODEL", "cohere.embed-v4.0"),
    **oci_genai,
)
vector_store = OracleVS(
    conn,
    embeddings,
    os.getenv("VECTOR_TABLE", "KNOWLEDGE_CHUNKS"),
    DistanceStrategy.COSINE,
)
vector_store.add_documents(chunks)

print(f"Uploaded 2 documents and indexed {len(chunks)} chunks.")
