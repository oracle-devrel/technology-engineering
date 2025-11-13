import gradio as gr
import time
import traceback
import logging
from typing import Any, Tuple
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_collection_stats(embedding_model: str, rag_system) -> str:
    """Get statistics for all collections"""
    try:
        # Switch embedding model if needed
        if embedding_model != rag_system.current_embedding_model:
            result = rag_system._initialize_vector_store(embedding_model)
            if "Failed" in result:
                return result
        
        if rag_system.vector_store is None:
            return "ERROR: Vector store not initialized"
        
        stats = []
        stats.append(f"VECTOR STORE STATISTICS")
        stats.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        stats.append("")
        
        # Get collection statistics and documents first
        collections = ["pdf_documents", "xlsx_documents"]
        
        for collection_name in collections:
            try:
                documents = rag_system.vector_store.list_documents(collection_name)
                total_chunks = sum(doc.get('chunk_count', 0) for doc in documents)
                
                stats.append(f"{collection_name.replace('_', ' ').title().upper()}:")
                stats.append(f"- Documents: {len(documents)}")
                stats.append(f"- Total chunks: {total_chunks}")
                
                if documents:
                    # Show ALL documents, not just recent ones
                    stats.append(f"- All documents:")
                    for doc in documents:
                        doc_name = doc.get('filename', doc.get('document_id', 'Unknown'))
                        chunk_count = doc.get('chunk_count', 0)
                        entity = doc.get('entity', 'Unknown')
                        stats.append(f"  • {doc_name} ({chunk_count} chunks) - {entity}")
                
                stats.append("")
                
            except Exception as e:
                stats.append(f"{collection_name.upper()}: Error - {str(e)}")
                stats.append("")
        
        # Add embedding model info at the bottom
        embedding_info = rag_system.vector_store.get_embedding_info()
        stats.append(f"EMBEDDING MODEL DETAILS:")
        stats.append(f"- Name: {embedding_info['name']}")
        stats.append(f"- Description: {embedding_info['description']}")
        stats.append(f"- Dimensions: {embedding_info['dimensions']}")
        stats.append(f"- Type: {embedding_info['type']}")
        stats.append(f"- Current Model: {embedding_model}")
        
        return "\n".join(stats)
        
    except Exception as e:
        error_msg = f"ERROR: Getting collection stats failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

def view_collection_documents(collection_name: str, embedding_model: str, rag_system) -> str:
    """View documents in a specific collection"""
    try:
        # Switch embedding model if needed
        if embedding_model != rag_system.current_embedding_model:
            result = rag_system._initialize_vector_store(embedding_model)
            if "Failed" in result:
                return result
        
        if rag_system.vector_store is None:
            return "ERROR: Vector store not initialized"
        
        # Map display names to internal names
        collection_mapping = {
            "PDF Documents": "pdf_documents",
            "XLSX Documents": "xlsx_documents"
        }
        
        actual_collection = collection_mapping.get(collection_name, collection_name.lower().replace(" ", "_"))
        
        documents = rag_system.vector_store.list_documents(actual_collection)
        
        if not documents:
            return f"No documents found in {collection_name} collection"
        
        result = []
        result.append(f"{collection_name.upper()} COLLECTION")
        result.append(f"Embedding Model: {embedding_model}")
        result.append(f"Total Documents: {len(documents)}")
        result.append("")
        
        for i, doc in enumerate(documents, 1):
            doc_name = doc.get("filename") or f"{doc.get('document_id', f'Document {i}')}"
            chunk_count = doc.get('chunk_count', 0)
            entity = doc.get('entity', 'Unknown')
            
            result.append(f"**{i}. {doc_name}**")
            result.append(f"   - Chunks: {chunk_count}")
            result.append(f"   - Entity: {entity}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        error_msg = f"ERROR: Viewing collection documents failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

def search_chunks(query: str, collection_name: str, embedding_model: str, rag_system, n_results: int = 5) -> str:
    """Search for chunks in a specific collection"""
    try:
        # Switch embedding model if needed
        if embedding_model != rag_system.current_embedding_model:
            result = rag_system._initialize_vector_store(embedding_model)
            if "Failed" in result:
                return result
        
        if rag_system.vector_store is None:
            return "ERROR: Vector store not initialized"
        
        if not query.strip():
            return "ERROR: Please enter a search query"
        
        # Map display names to internal names
        collection_mapping = {
            "PDF Documents": "pdf_documents",
            "XLSX Documents": "xlsx_documents"
        }
        
        actual_collection = collection_mapping.get(collection_name, collection_name.lower().replace(" ", "_"))
        
        # Perform search based on collection type
        dispatch = {
            "pdf_documents": rag_system.vector_store.query_pdf_collection,
            "xlsx_documents": rag_system.vector_store.query_xlsx_collection
        }
        
        if actual_collection not in dispatch:
            return f"ERROR: Unknown collection: {collection_name}"
        results = dispatch[actual_collection](query, n_results)
        if not results:
            return f"No results found for query '{query}' in {collection_name} collection"  
        # Format results
        output = []
        output.append(f"SEARCH RESULTS FOR '{query}'")
        output.append(f"Collection: {collection_name}")
        output.append(f"Embedding Model: {embedding_model}")
        output.append(f"Results: {len(results)}")
        output.append("")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            distance = result.get('distance', 0.0)
            
            # Truncate content for display
            content_preview = content[:300] + "..." if len(content) > 300 else content
            
            output.append(f"**Result {i}:**")
            output.append(f"Distance: {distance:.4f}")
            output.append(f"Source: {metadata.get('source', 'Unknown')}")
            output.append(f"Company: {metadata.get('company', 'Unknown')}")
            output.append(f"Content: {content_preview}")
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"ERROR: Searching chunks failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

def list_all_chunks(collection_name: str, embedding_model: str, rag_system, batch_size: int = 1000) -> str:
    """List all chunks in a collection (base name or fully-qualified), across all model/dimension variants."""
    try:
        # Switch embedding model if needed (so rag_system.vector_store is available)
        if embedding_model != rag_system.current_embedding_model:
            result = rag_system._initialize_vector_store(embedding_model)
            if isinstance(result, str) and "Failed" in result:
                return result

        vs = rag_system.vector_store
        if vs is None:
            return "ERROR: Vector store not initialized"

        # Map display names to base prefixes
        display_to_base = {
            "PDF Documents": "pdf_documents",
            "XLSX Documents": "xlsx_documents",
        }
        base = display_to_base.get(collection_name, collection_name.lower().replace(" ", "_"))

        # Find collections to read:
        #  - if the provided name matches a fully-qualified name we know, use just that
        #  - else, discover all variants from the client that start with base + "_"
        to_read = []

        # 1) exact match in current map?
        if base in getattr(vs, "collection_map", {}):
            to_read.append((base, vs.collection_map[base]))
        elif base in getattr(vs, "collections", {}):
            to_read.append((base, vs.collections[base]))
        else:
            # 2) treat as base prefix; discover all variants in the DB
            client = vs.client  # chromadb.PersistentClient
            found = False
            for c in client.list_collections():
                name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
                if not name:
                    continue
                if name == base or name.startswith(base + "_"):
                    # Re-acquire as a collection object
                    coll = client.get_or_create_collection(name=name)
                    to_read.append((name, coll))
                    found = True

            if not found:
                # 3) last resort: try the fully-qualified key for the current model/dim
                if hasattr(vs, "get_collection_key"):
                    fq = vs.get_collection_key(base)
                    coll = vs.collection_map.get(fq)
                    if coll:
                        to_read.append((fq, coll))

            if not to_read:
                return f"Collection '{collection_name}' not found"

        # Helper to stream all rows from a collection with batching
        def iter_chunks(coll):
            total = coll.count()
            offset = 0
            while offset < total:
                res = coll.get(where=None, include=["documents", "metadatas"], limit=batch_size, offset=offset)
                docs = res.get("documents") or []
                metas = res.get("metadatas") or []
                ids = res.get("ids") or []

                # Fallback in case some client variant omits ids unless include=None
                if not ids and docs:
                    res = coll.get(where=None, limit=batch_size, offset=offset)
                    docs = res.get("documents") or docs
                    metas = res.get("metadatas") or metas
                    ids = res.get("ids") or ids

                # Pad metas/ids to docs length (defensive)
                if len(metas) < len(docs):
                    metas += [{}] * (len(docs) - len(metas))
                if len(ids) < len(docs):
                    ids += [f"{offset+i}" for i in range(len(ids), len(docs))]

                for doc, meta, _id in zip(docs, metas, ids):
                    yield _id, (doc or "").strip(), (meta or {})
                offset += len(docs)
                if len(docs) == 0:
                    break  # safety to avoid infinite loop on odd clients

        # Build output
        out = []
        out.append(f"ALL CHUNKS")
        out.append(f"Requested: {collection_name}  |  Embedding Model Context: {embedding_model}")
        out.append("=" * 80)
        grand_total = 0

        for name, coll in to_read:
            count = coll.count()
            out.append(f"\nCOLLECTION: {name}  (chunks: {count})")
            out.append("-" * 80)
            i = 0
            for cid, content, meta in iter_chunks(coll):
                i += 1
                grand_total += 1
                out.append(f"CHUNK {i} | ID: {cid}")
                out.append(f"Content: {content}")
                if meta:
                    out.append("Metadata:")
                    for k, v in meta.items():
                        out.append(f"  {k}: {v}")
                out.append("-" * 80)

        if grand_total == 0:
            return f"No chunks found for '{collection_name}'."

        out.insert(2, f"Total Chunks Listed (across matched collections): {grand_total}")
        return "\n".join(out)

    except Exception as e:
        logger.exception("Listing chunks failed")
        return f"ERROR: Listing chunks failed: {e}"



def delete_all_chunks_in_collection(collection_name: str, embedding_model: str, rag_system) -> str:
    """Delete ALL chunks for a logical collection (e.g., all XLSX collections across models)."""
    try:
        # Ensure vector store exists (don't switch models for delete-all)
        if rag_system.vector_store is None:
            init_msg = rag_system._initialize_vector_store(rag_system.current_embedding_model)
            if "Failed" in init_msg:
                return init_msg

        # Map UI label -> base prefix used in Chroma collection names
        base_prefix_map = {
            "PDF Documents": "pdf_documents",
            "XLSX Documents": "xlsx_documents",
        }
        base_prefix = base_prefix_map.get(collection_name, collection_name.lower().replace(" ", "_"))

        client = rag_system.vector_store.client
        all_colls = client.list_collections()

        # Find all physical collections for this logical group (e.g., xlsx_documents_* or pdf_documents_*)
        targets = []
        for c in all_colls:
            # Handle both collection objects and dict representations
            coll_name = getattr(c, 'name', None) or (c.get('name') if isinstance(c, dict) else str(c))
            if coll_name and coll_name.startswith(f"{base_prefix}_"):
                targets.append((coll_name, c))

        if not targets:
            return f"Collection group '{collection_name}' has no collections to delete."

        # Delete them all
        total_deleted_chunks = 0
        deleted_names = []
        for coll_name, coll_obj in targets:
            try:
                count = 0
                try:
                    # Get the actual collection object if we only have the name
                    if isinstance(coll_obj, str):
                        actual_coll = client.get_collection(coll_name)
                    else:
                        actual_coll = coll_obj
                    count = actual_coll.count()
                except Exception:
                    pass
                    
                total_deleted_chunks += count
                client.delete_collection(coll_name)
                deleted_names.append(coll_name)
                
                # Clean up all in-memory references
                if hasattr(rag_system.vector_store, "collections"):
                    rag_system.vector_store.collections.pop(coll_name, None)
                if hasattr(rag_system.vector_store, "collection_map"):
                    rag_system.vector_store.collection_map.pop(coll_name, None)
                    
            except Exception as e:
                logging.error(f"Failed to delete collection '{coll_name}': {e}")

        # Recreate the CURRENT model's empty collection so the app keeps a live handle
        # Build full name like: {base_prefix}_{model_name}_{dimensions}
        emb_info = rag_system.vector_store.get_embedding_info()
        model_name = rag_system.vector_store.embedding_model_name
        dims = int(emb_info.get("dimensions", 384))
        metadata = {
            "hnsw:space": "cosine",
            "embedding_model": model_name,
            "embedding_dimensions": dims,
        }
        new_full_name = f"{base_prefix}_{model_name}_{dims}"
        new_collection = client.get_or_create_collection(name=new_full_name, metadata=metadata)

        # Refresh ALL vector_store references comprehensively
        if hasattr(rag_system.vector_store, "collections"):
            rag_system.vector_store.collections[new_full_name] = new_collection
            
        if hasattr(rag_system.vector_store, "collection_map"):
            rag_system.vector_store.collection_map[new_full_name] = new_collection
            # Also ensure the collection_map is properly updated
            rag_system.vector_store.collection_map = {
                k: v for k, v in rag_system.vector_store.collection_map.items()
                if not k.startswith(f"{base_prefix}_") or k == new_full_name
            }
            rag_system.vector_store.collection_map[new_full_name] = new_collection

        # Update the specific collection references
        if base_prefix == "xlsx_documents":
            rag_system.vector_store.xlsx_collection = new_collection
            if hasattr(rag_system.vector_store, "current_xlsx_collection_name"):
                rag_system.vector_store.current_xlsx_collection_name = new_full_name
        elif base_prefix == "pdf_documents":
            rag_system.vector_store.pdf_collection = new_collection
            if hasattr(rag_system.vector_store, "current_pdf_collection_name"):
                rag_system.vector_store.current_pdf_collection_name = new_full_name

        # Nice summary
        deleted_list = "\n".join(f"  • {name}" for name in deleted_names) if deleted_names else "  • (none)"
        return (
            "✅ DELETION COMPLETED\n\n"
            f"Logical collection: {collection_name}\n"
            f"Collections removed: {len(deleted_names)}\n"
            f"Total chunks deleted: {total_deleted_chunks}\n"
            f"Deleted collections:\n{deleted_list}\n\n"
            "Recreated empty collection for current model:\n"
            f"  • {new_full_name}\n"
            f"Embedding model: {model_name} ({dims}D)"
        )

    except Exception as e:
        logging.exception("Delete-all failed")
        return f"ERROR: Deleting chunks failed: {e}"
