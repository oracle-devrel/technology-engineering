import time
import traceback
import logging
from typing import Any, Tuple
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_pdf_file(
    file: Any,
    embedding_model: str,
    rag_system: Any,
    entity: str,
    progress: Any = None
) -> Tuple[str, str]:
    """Process uploaded PDF file and return summary + log."""

    if file is None:
        return "❌ ERROR: No file uploaded", ""

    if not entity:
        return "❌ ERROR: Entity name is required", ""
    
    if progress is None:
        def progress(*args, **kwargs):
            pass

    try:
        progress(0.1, desc="Initializing...")

        # ✅ Ensure RAG agent & vector store are aligned with the embedding model
        progress(0.2, desc="Ensuring embedding model and RAG agent match...")
        success = rag_system._initialize_rag_agent(
            llm_model=rag_system.current_llm_model,
            embedding_model=embedding_model
        )
        if not success:
            return "❌ ERROR: Failed to initialize RAG agent with embedding model", ""
        # Ensure the collections are bound to this embedding model
        rag_system.vector_store.bind_collections_for_model(embedding_model)

        progress(0.3, desc="Processing PDF file...")

        # ✅ Make sure PDF processor exists
        if not getattr(rag_system, "pdf_processor", None):
            rag_system._initialize_processors()
            if not rag_system.pdf_processor:
                return "❌ ERROR: PDF ingester failed to initialize", ""

        # ✅ Vector store check
        if rag_system.vector_store is None:
            return "❌ ERROR: Vector store not initialized", ""

        file_path = Path(file.name)
        chunks, doc_id, _ = rag_system.pdf_processor.ingest_pdf(file_path, entity=entity)
        print("PDF processor type:", type(rag_system.pdf_processor))
        progress(0.7, desc="Adding to vector store...")

        converted_chunks = [
            {
                'id': chunk.get('id', f"{doc_id}_chunk_{i}"),
                'content': chunk.get('text', chunk.get('content', str(chunk))),
                'metadata': chunk.get('metadata', {})
            }
            for i, chunk in enumerate(chunks)
        ]

        # ✅ Add chunks
        if hasattr(rag_system.vector_store, "add_pdf_chunks"):
            rag_system.vector_store.add_pdf_chunks(converted_chunks, doc_id)
            actual_collection_name = getattr(rag_system.vector_store, "pdf_collection", type('', (), {})()).name
        else:
            rag_system.vector_store.pdf_collection.add(
                documents=[c["content"] for c in converted_chunks],
                metadatas=[c["metadata"] for c in converted_chunks],
                ids=[c["id"] for c in converted_chunks]
            )
            actual_collection_name = getattr(rag_system.vector_store.pdf_collection, "name", "Unknown Collection")

        progress(1.0, desc="Complete!")

        stats = getattr(rag_system.pdf_processor, "stats", {})

        collection_name = f"{actual_collection_name} ({embedding_model})"

        summary = f"""
✅ **PDF PROCESSING COMPLETE**

**File:** {file_path.name}  
**Document ID:** {doc_id}  
**Entity:** {entity}  
**Chunks created:** {len(chunks)}  
**Embedding model:** {embedding_model}  
**Collection:** {collection_name}  

**Processing Stats:**
- Total Chunks: {stats.get("total_chunks", len(chunks))}
- Rewritten Chunks: {stats.get("rewritten_chunks", "N/A")}
- Processing Time: {stats.get("processing_time", "N/A") if stats.get("processing_time") is None else f'{stats.get("processing_time", 0):.2f}s'}
- Rewriting Time: {stats.get("rewriting_time", "N/A") if stats.get("rewriting_time") is None else f'{stats.get("rewriting_time", 0):.2f}s'}
""".strip()

        detailed_log = f"""
=== PDF PROCESSING LOG ===
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
File: {file_path.name}
Size: {file_path.stat().st_size if file_path.exists() else 'Unknown'} bytes
Document ID: {doc_id}
Chunks: {len(chunks)}
Embedding Model: {embedding_model}
Collection: {collection_name}

Sample Chunks:
"""

        for i, chunk in enumerate(chunks[:3]):
            text_content = chunk.get('text', chunk.get('content', str(chunk)))
            detailed_log += f"\n--- Chunk {i+1} ---\n{text_content[:500].strip()}...\n"

        return summary, detailed_log

    except Exception as e:
        error_msg = f"❌ ERROR: Processing PDF file failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg, traceback.format_exc()
