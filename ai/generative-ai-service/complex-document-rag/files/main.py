import os
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid

from pdf_processor import PDFProcessor
from ingest_xlsx import XLSXProcessor
from vector_store import EnhancedVectorStore as VectorStore
from local_rag_agent import RAGSystem
#from rag_agent import RAGAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Agentic RAG API",
    description="API for processing PDFs and answering queries using an agentic RAG system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pdf_processor = PDFProcessor()
vector_store = VectorStore()


# Initialize RAG agent 

try:
    print("\nTrying to use OCI model...")
    rag_agent = RAGSystem(vector_store=vector_store)
    print("Successfully initialized OCI model.")
    try: 
        xlsx_processor = XLSXProcessor(
        tokenizer="BAAI/bge-small-en-v1.5",
        chunk_rewriter=rag_agent.agents.get("chunk_rewriter") if hasattr(rag_agent, "agents") else None
    )
    except Exception as e:
        print(f"\nFailed to initialize XLSX processor: {str(e)}")
        xlsx_processor = XLSXProcessor(tokenizer="BAAI/bge-small-en-v1.5")
        print("⚠️ Fallback XLSX processor initialized without chunk rewriting.")
except Exception as e:
    print(f"\nFailed to initialize OCI model: {str(e)}")
    


class QueryRequest(BaseModel):
    query: str
    use_cot: bool = False
    model: Optional[str] = None  # Allow specifying model in the request

class QueryResponse(BaseModel):
    answer: str
    reasoning: Optional[str] = None
    context: List[dict]

@app.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Save the uploaded file temporarily
        temp_path = f"temp_{uuid.uuid4()}.pdf"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the PDF
        chunks, document_id = pdf_processor.process_pdf(temp_path)
        
        # Add chunks to vector store
        vector_store.add_pdf_chunks(chunks, document_id=document_id)
        
        # Clean up
        os.remove(temp_path)
        
        return {
            "message": "PDF processed successfully",
            "document_id": document_id,
            "chunks_processed": len(chunks)
        }
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/upload/xlsx")
async def upload_xlsx(file: UploadFile = File(...)):
    """Upload and process an XLSX file"""
    if not file.filename.lower().endswith(('.xlsx', '.xlsm')):
        raise HTTPException(status_code=400, detail="File must be an Excel (.xlsx or .xlsm) file")

    try:
        # Save the uploaded file temporarily
        temp_path = f"temp_{uuid.uuid4()}.xlsx"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process the XLSX
        chunks = xlsx_processor.process_workbook(Path(temp_path))

        # Use filename as document ID
        document_id = file.filename

        # Add chunks to vector store
        vector_store.add_xlsx_chunks(chunks, document_id=document_id)

        # Clean up
        os.remove(temp_path)

        return {
            "message": "XLSX processed successfully",
            "document_id": document_id,
            "chunks_processed": len(chunks)
        }

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a query using the RAG agent"""
    try:
        # Determine which model to use
        if request.model:
            if request.model.startswith("ollama:") and ollama_available:
                # Use specified Ollama model
                rag_agent = RAGSystem(vector_store=vector_store, model_name=request.model, use_cot=request.use_cot)
            elif request.model == "openai" and openai_api_key:
                # Use OpenAI
                rag_agent = RAGAgent(vector_store=vector_store, openai_api_key=openai_api_key, use_cot=request.use_cot)
            else:
                # Use default local model
                rag_agent = RAGSystem(vector_store=vector_store, use_cot=request.use_cot)
                
        else:
            # Reinitialize agent with CoT setting using default model
            if openai_api_key:
                rag_agent = RAGAgent(vector_store=vector_store, openai_api_key=openai_api_key, use_cot=request.use_cot)
            else:
                # Try local Mistral first
                try:
                    rag_agent = RAGSystem(vector_store=vector_store, use_cot=request.use_cot)
                except Exception as e:
                    print(f"Failed to initialize local Mistral model: {str(e)}")
                    # Fall back to Ollama if available
                    if ollama_available:
                        try:
                            rag_agent = RAGSystem(vector_store=vector_store, model_name="ollama:llama3", use_cot=request.use_cot)
                        except Exception as e2:
                            raise Exception(f"Failed to initialize any model: {str(e2)}")
                    else:
                        raise e
        print(f"📢 [DEBUG] Using RAG agent type: {type(rag_agent).__name__}")    
        response = rag_agent.process_query(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
