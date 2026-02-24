# query_handler.py
# This module handles queries to the RAG system, processing user input and returning results.

import gradio as gr
import time
import traceback
import logging
from typing import Any, Tuple, Dict, Union, Optional
from pathlib import Path
from local_rag_agent import RAGSystem  

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_query(
    query: str,
    llm_model: str,
    embedding_model: str,
    include_pdf: bool,
    include_xlsx: bool,
    agentic: bool,
    rag_system,
    entity1: str = "",
    entity2: str = "",
    progress=gr.Progress()
) -> Tuple[str, Optional[str]]:
    """Process a query using the RAG system with optional entity specification"""

    if not query.strip():
        return "ERROR: Please enter a query", None

    try:
        progress(0.1, desc="Initializing...")

        # Switch embedding model if needed
        if embedding_model != rag_system.current_embedding_model:
            progress(0.2, desc="Switching embedding model...")
            init_result = rag_system._initialize_vector_store(embedding_model)
            if "Failed" in init_result:
                return init_result, None
       

        progress(0.3, desc="Initializing RAG agent...")
        # Decide the active collection from the checkboxes
        if include_pdf and include_xlsx:
            active_collection = "multi"
        elif include_pdf:
            active_collection = "pdf"
        elif include_xlsx:
            active_collection = "xlsx"
        else:
            return "ERROR: Please select at least one collection (PDF or XLSX).", None
        rag_system.vector_store.bind_collections_for_model(embedding_model)
        success = rag_system._initialize_rag_agent(llm_model, collection=active_collection, embedding_model=embedding_model)
        if not success:
            return "ERROR: Failed to initialize RAG agent", None

        # Generic safe query function
        def _safe_query(collection_label: str, text: str, n: int = 5):
            vs = rag_system.vector_store
            if hasattr(vs, "query_collection_by_name"):
                return vs.query_collection_by_name(
                    collection_name=collection_label,
                    query_text=text,
                    n_results=n
                )
            if collection_label == "pdf":
                return vs.query_pdf_collection(text, n_results=n)
            if collection_label == "xlsx":
                return vs.query_xlsx_collection(text, n_results=n)
            return []

        progress(0.5, desc="Processing query...")
        start_time = time.time()

        result: Dict[str, Any] = {}
        collections_queried: list[str] = []

        # --- AGENTIC MODE ---
        if agentic and rag_system.rag_agent and hasattr(rag_system.rag_agent, 'process_query_with_multi_collection_context'):
            progress(0.6, desc=f"Querying collections with {embedding_model}...")

            all_results = []

            if include_pdf:
                try:
                    # Agentic workflow: 8 chunks per collection (more targeted retrieval per subtask)
                    pdf_results = _safe_query("pdf", query, n=8)
                    if pdf_results:
                        all_results.extend(pdf_results)
                        collections_queried.append(f"PDF ({embedding_model})")
                        logger.info(f"✅ PDF: Found {len(pdf_results)} chunks")
                    else:
                        logger.info("📭 PDF: No results found")
                except Exception as e:
                    logger.warning(f"❌ PDF collection query failed: {e}")

            if include_xlsx:
                try:
                    # Agentic workflow: 8 chunks per collection (more targeted retrieval per subtask)
                    xlsx_results = _safe_query("xlsx", query, n=8)
                    if xlsx_results:
                        all_results.extend(xlsx_results)
                        collections_queried.append(f"XLSX ({embedding_model})")
                        logger.info(f"✅ XLSX: Found {len(xlsx_results)} chunks")
                    else:
                        logger.info("📭 XLSX: No results found")
                except Exception as e:
                    logger.warning(f"❌ XLSX collection query failed: {e}")

            progress(0.8, desc="Generating response...")

            # Prepare provided entities if any
            provided_entities = []
            if entity1 and entity1.strip():
                provided_entities.append(entity1.strip().lower())
            if entity2 and entity2.strip():
                provided_entities.append(entity2.strip().lower())
            
            # Log entities being used
            if provided_entities:
                logger.info(f"Using provided entities: {provided_entities}")

            if all_results:
                # Pass provided entities to the RAG system
                result = rag_system.rag_agent.process_query_with_multi_collection_context(
                    query,
                    all_results,
                    collection_mode=active_collection,
                    provided_entities=provided_entities if provided_entities else None
                )
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    result = {"answer": str(result)}
            else:
                result = {
                    "answer": f"No relevant information found in selected collections using {embedding_model} embedding model."
                }

            # Add metadata to result dictionary
            if isinstance(result, dict):
                result["collections_queried"] = collections_queried
                result["total_chunks"] = len(all_results)

        # --- NON-AGENTIC MODE (OPTIMIZED) ---
        else:
            progress(0.6, desc="Retrieving context (non-agentic, optimized)...")

            # Use concurrent.futures for parallel collection queries
            import concurrent.futures
            
            retrieved_chunks = []
            
            def query_collection(collection_type):
                """Query a single collection in parallel"""
                try:
                    if collection_type == "pdf":
                        # Optimized to 10 chunks for faster processing
                        results = _safe_query("pdf", query, n=10)
                        return ("PDF", results if results else [])
                    elif collection_type == "xlsx":
                        # Optimized to 10 chunks for faster processing
                        results = _safe_query("xlsx", query, n=10)
                        return ("XLSX", results if results else [])
                    else:
                        return (collection_type.upper(), [])
                except Exception as e:
                    logger.warning(f"❌ {collection_type.upper()} collection query failed: {e}")
                    return (collection_type.upper(), [])
            
            # Prepare collection queries to run in parallel
            collection_queries = []
            if include_pdf:
                collection_queries.append("pdf")
            if include_xlsx:
                collection_queries.append("xlsx")
            
            # Execute queries in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_to_collection = {
                    executor.submit(query_collection, col): col 
                    for col in collection_queries
                }
                
                for future in concurrent.futures.as_completed(future_to_collection):
                    collection_name, results = future.result()
                    if results:
                        retrieved_chunks.extend(results)
                        collections_queried.append(collection_name)
                        logger.info(f"✅ {collection_name}: Found {len(results)} chunks")

            if not retrieved_chunks:
                return "No relevant information found in selected collections.", None

            # Use more chunks for better context in non-agentic mode
            # Optimize chunk usage based on model
            if llm_model == "grok-4":
                chunks_to_use = retrieved_chunks[:15]  # Can handle more context
            else:
                chunks_to_use = retrieved_chunks[:10]  # Optimized for speed
            context_str = "\n\n".join(chunk["content"] for chunk in chunks_to_use)
            prompt = f"""You are an expert assistant.

Use the following context to answer the question.

Context:
{context_str}

Question:
{query}
"""

            progress(0.8, desc="Calling LLM...")

            try:
                llm = getattr(rag_system.rag_agent, "llm", None)
                if callable(llm):
                    answer = llm(prompt)
                else:
                    answer = "LLM call failed: No callable `llm()` found on RAG agent."
            except Exception as e:
                logger.error(f"LLM invocation failed: {e}")
                answer = f"ERROR: LLM call failed: {e}"

            result = {
                "answer": answer,
                "context": retrieved_chunks,
                "collections_queried": collections_queried,
                "total_chunks": len(retrieved_chunks)
            }

        processing_time = time.time() - start_time
        progress(1.0, desc="Complete!")

        # MAIN RESPONSE
        main_response = []
        if result.get('report_path'):
            main_response.append("MULTI-AGENT REPORT GENERATED SUCCESSFULLY")
            main_response.append(f"\nWORD DOCUMENT CREATED: {result['report_path']}")
        else:
            main_response.append("AI RESPONSE:")
            main_response.append(f"\n{result.get('answer', 'No response generated.')}")

        if result.get('collections_queried'):
            collections = result['collections_queried']
            if isinstance(collections, list):
                main_response.append(f"\n\nCOLLECTIONS QUERIED: {', '.join(collections)}")
            else:
                main_response.append(f"\n\nCOLLECTIONS QUERIED: {str(collections)}")

        if result.get('total_chunks') is not None:
            main_response.append(f"\nCONTEXT CHUNKS USED: {result['total_chunks']}")

        main_response.append(f"\nPROCESSING TIME: {processing_time:.2f}s")
        main_response.append(f"\nLLM MODEL: {llm_model}")
        main_response.append(f"\nEMBEDDING MODEL: {embedding_model}")

        # RETRIEVAL DETAILS
        retrieval_details = [
            "RETRIEVAL DETAILS",
            f"Query: {query}",
            f"Agentic Workflow: {'Yes' if agentic else 'No'}",
            f"Included Collections: {'PDF' if include_pdf else ''} {'XLSX' if include_xlsx else ''}".strip(),
            f"Embedding model: {embedding_model}",
            f"LLM model: {llm_model}"
        ]
        if result.get('context'):
            retrieval_details.append(f"Context chunks retrieved: {len(result['context'])}")

        # CONTEXT CHUNKS DISPLAY
        context_display = []
        if result.get('context'):
            context_display.append("RETRIEVED CONTEXT CHUNKS\n")
            for i, chunk in enumerate(result['context'][:5], 1):
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                preview = content[:200] + "..." if len(content) > 200 else content
                context_display += [
                    f"Chunk {i}:",
                    f"Source: {metadata.get('source', 'Unknown')}",
                    f"Company: {metadata.get('company', 'Unknown')}",
                    f"Content: {preview}",
                    ""
                ]
        else:
            context_display.append("No context chunks available")

        # Format everything into a single, well-formatted response
        formatted_response = []
        
        # Main result section
        if result.get('report_path'):
            formatted_response.extend([
                "🎉 **MULTI-AGENT REPORT GENERATED SUCCESSFULLY**",
                "",
                f" **Word Document Created:** `{result['report_path']}`",
                ""
            ])
        else:
            formatted_response.extend([
                " **AI RESPONSE:**",
                "",
                result.get('answer', 'No response generated.'),
                ""
            ])
        
        # Processing details section
        formatted_response.extend([
            "**PROCESSING DETAILS:**",
            f"• Collections Queried: {', '.join(result.get('collections_queried', []))}" if result.get('collections_queried') else "• Collections Queried: None",
            f"• Context Chunks Used: {result.get('total_chunks', 0)}",
            f"• Processing Time: {processing_time:.2f}s",
            f"• LLM Model: {llm_model}",
            f"• Embedding Model: {embedding_model}",
            ""
        ])
        
        # Query details section
        formatted_response.extend([

            f"• Query: {query}",
            f"• Agentic Workflow: {'Yes' if agentic else 'No'}",
            f"• Collections: {'PDF ' if include_pdf else ''}{'XLSX' if include_xlsx else ''}".strip(),
            ""
        ])
        
        # Context chunks section (only if available and meaningful)
        if result.get('context') and len(result['context']) > 0:
            formatted_response.extend([
                "**RETRIEVED CONTEXT CHUNKS:**",
                ""
            ])
            for i, chunk in enumerate(result['context'][:3], 1):  # Show only top 3 chunks
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                preview = content[:150] + "..." if len(content) > 150 else content
                formatted_response.extend([
                    f"**Chunk {i}:**",
                    f"• Source: {metadata.get('source', 'Unknown')}",
                    f"• Entity: {metadata.get('entity', metadata.get('company', 'Unknown'))}",
                    f"• Content: {preview}",
                    ""
                ])
        
        # Extract report path if available
        report_path = result.get('report_path') if isinstance(result, dict) else None
        
        return "\n".join(formatted_response), report_path

    except Exception as e:
        error_msg = f"ERROR: Processing query failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"{error_msg}\n\nTraceback:\n{traceback.format_exc()}", None
