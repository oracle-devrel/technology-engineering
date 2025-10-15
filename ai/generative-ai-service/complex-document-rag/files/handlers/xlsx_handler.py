# =============================================================================
# DOCUMENT PROCESSING FUNCTIONS
# =============================================================================
import gradio as gr
import time
import traceback
import logging
from typing import Any, Tuple
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# processing from Gradio APP

def process_xlsx_file(
    file: Any,
    embedding_model: str,
    rag_system: Any,
    entity: str,  
    progress: Any = None
) -> Tuple[str, str]:
    """Process uploaded XLSX file and return summary + log."""
    import time, traceback

    if file is None:
        return "❌ ERROR: No file uploaded", ""

    if not entity:
        return "❌ ERROR: Entity name is required", ""
    if progress is None:
        def progress(*args, **kwargs):
            pass

    try:
        progress(0.1, desc="Initializing...")

        # Switch embedding model if needed
        if embedding_model != rag_system.current_embedding_model:
            progress(0.2, desc="Switching embedding model...")
            result = rag_system._initialize_vector_store(embedding_model)
            if "Failed" in result:
                return result, ""

        progress(0.3, desc="Processing XLSX file...")

        if rag_system.xlsx_processor is None:
            try:
                rag_system._initialize_processors()
                if rag_system.xlsx_processor is None:
                    return "❌ ERROR: XLSX ingester failed to initialize", ""
            except Exception as reinit_error:
                return f"❌ ERROR: Could not initialize XLSX ingester: {str(reinit_error)}", ""

        if rag_system.vector_store is None:
            return "❌ ERROR: Vector store not initialized", ""

        file_path = Path(file.name)
        chunks, doc_id = rag_system.xlsx_processor.ingest_xlsx(file_path, entity=entity)

        progress(0.7, desc="Adding to vector store...")

        converted_chunks = [
            {
                'id': chunk['id'],
                'content': chunk['content'],
                'metadata': chunk['metadata']
            }
            for chunk in chunks
        ]

        rag_system.vector_store.add_xlsx_chunks(converted_chunks, doc_id)

        progress(1.0, desc="Complete!")

        # Pull stats from ingester if available
        stats = rag_system.xlsx_processor.stats if hasattr(rag_system.xlsx_processor, "stats") else {}

        actual_collection_name = rag_system.vector_store.xlsx_collection.name
        collection_name = f"{actual_collection_name} ({embedding_model})"

        summary = f"""
✅ **XLSX PROCESSING COMPLETE**

**File:** {file_path.name}  
**Document ID:** {doc_id}  
**Entity:** {entity}  
**Chunks created:** {len(chunks)}  
**Embedding model:** {embedding_model}  
**Collection:** {collection_name}  

**Processing Stats:**
- Total Chunks: {stats.get("total_chunks", "N/A")}
- Rewritten Chunks: {stats.get("rewritten_chunks", "N/A")}
- Processing Time: {stats.get("processing_time", "N/A"):.2f}s
- Rewriting Time: {stats.get("rewriting_time", "N/A"):.2f}s

**Next Steps:**
- Explore chunks in the 'Vector Store Viewer' tab
- Use 'Inference & Query' tab to ask questions
""".strip()

        detailed_log = f"""
=== XLSX PROCESSING LOG ===
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
            text_content = chunk.get('content', str(chunk))
            detailed_log += f"\n--- Chunk {i+1} ---\n{text_content[:500].strip()}...\n"

        return summary, detailed_log

    except Exception as e:
        error_msg = f"❌ ERROR: Processing XLSX file failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg, traceback.format_exc()

