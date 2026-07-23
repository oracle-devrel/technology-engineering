"""Local RAG Agent with OCI model support."""

import argparse
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import tiktoken
from dotenv import load_dotenv

from agents.agent_factory import create_agents, create_ingestion_only_agents
from contracts import Chunk, Plan, PlanSection, SectionDraft, ReportResult
from llm_concurrency import llm_semaphore
from llm_factory import create_llm, get_available_models, MODEL_REGISTRY
from progress_bus import progress_bus
from vector_store import EnhancedVectorStore

load_dotenv()

try:
    from OraDBVectorStore import OraDBVectorStore
    ORACLE_DB_AVAILABLE = True
except ImportError:
    ORACLE_DB_AVAILABLE = False
    # debug, not warning: the Chroma path is the intended default here, so this is
    # a statement of configuration, not a problem. It read as a failure on screen.
    logging.debug(
        "Oracle DB backend not installed; using Chroma. "
        "Install with: pip install oracledb sentence-transformers"
    )

# Configure logging - use demo logger if available
try:
    from utils.demo_logger import demo_logger, setup_demo_logging
    logger = setup_demo_logging()
    DEMO_MODE = True
except ImportError:
    # Fallback to standard logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    DEMO_MODE = False





class RAGSystem:
    def __init__(self, vector_store: EnhancedVectorStore = None, model_name: str = None, 
                 use_cot: bool = False, skip_analysis: bool = False,
                 quantization: str = None, use_oracle_db: bool = True, collection: str = "multi",
                 embedding_model: str = "cohere-embed-multilingual-v3.0"):
        """Initialize local RAG agent with vector store and local LLM
        
        Args:
            vector_store: Vector store for retrieving context (if None, will create one)
            model_name: OCI model name to use (e.g., "grok-3", "llama3.3")
            use_cot: Whether to use Chain of Thought reasoning
            collection: Collection to search in (XLSX, PDF, Repository, Web, General Knowledge)
            skip_analysis: Whether to skip query analysis (kept for backward compatibility)
            quantization: Quantization method to use (None, '4bit', '8bit')
            use_oracle_db: Whether to use Oracle DB for vector storage (if False, uses ChromaDB)
            embedding_model: Embedding model to use
        """
        logger.info(f"RAGSystem init - model_name: {model_name}")
        
        # Set default model if none provided
        if model_name is None:
            model_name = "grok-3"
            logger.info(f"Using default model: {model_name}")
        
        # Pick your OCI model name once - ensure it's a supported model
        embedding_model_name = embedding_model or "cohere-embed-multilingual-v3.0"
        
        # Validate embedding model is supported
        from oci_embedding_handler import EmbeddingModelManager
        embedding_manager = EmbeddingModelManager()
        available_models = [m["name"] for m in embedding_manager.list_available_models()]
        
        if embedding_model_name not in available_models:
            logger.error(f"Unsupported embedding model: {embedding_model_name}. Available: {', '.join(available_models)}")
            raise ValueError(f"Unsupported embedding model: {embedding_model_name}. Available: {', '.join(available_models)}")
        
        # Create the OCI embedder object
        from oci_embedding_handler import OCIEmbeddingHandler
        self.embedder = OCIEmbeddingHandler(model_name=embedding_model_name)
        
        # Also record dimensions for guards/logs
        self.embedding_info = self.embedder.get_model_info()
        
        # Initialize vector store if not provided
        self.use_oracle_db = use_oracle_db and ORACLE_DB_AVAILABLE
        
        if vector_store is None:
            if self.use_oracle_db:
                try:
                    self.vector_store = OraDBVectorStore()
                    print("Using Oracle DB for vector storage")
                except ValueError as ve:
                    if "credentials not found" in str(ve):
                        print(f"Oracle DB credentials not found in config.yaml: {str(ve)}")
                        print("Falling back to ChromaDB")
                    else:
                        print(f"Oracle DB initialization error: {str(ve)}")
                        print("Falling back to ChromaDB")
                    # Use model-specific persist directory to avoid dimension conflicts
                    persist_dir = f"embed-{embedding_model_name}"
                    self.vector_store = EnhancedVectorStore(
                        persist_directory=persist_dir,
                        embedding_model=embedding_model_name,   # string, for naming/metadata
                        embedder=self.embedder                  # object, for actual embedding
                    )
                    self.use_oracle_db = False
                except Exception as e:
                    print(f"Error initializing Oracle DB: {str(e)}")
                    print("Falling back to ChromaDB")
                    # Use model-specific persist directory to avoid dimension conflicts
                    persist_dir = f"embed-{embedding_model_name}"
                    self.vector_store = EnhancedVectorStore(
                        persist_directory=persist_dir,
                        embedding_model=embedding_model_name,   # string, for naming/metadata
                        embedder=self.embedder                  # object, for actual embedding
                    )
                    self.use_oracle_db = False
            else:
                persist_dir = f"embed_{embedding_model_name}"
                self.vector_store = EnhancedVectorStore(
                    persist_directory=persist_dir,
                    embedding_model=embedding_model_name,   # string, for naming/metadata
                    embedder=self.embedder                  # object, for actual embedding
                )
                print("Using ChromaDB for vector storage")
        else:
            self.vector_store = vector_store
            # Determine type of vector store
            self.use_oracle_db = hasattr(vector_store, 'connection') and hasattr(vector_store, 'cursor')
        
        self.use_cot = use_cot
        self.quantization = quantization
        self.model_name = model_name
        self.collection = collection

        # Initialize LLM via factory
        available_models = list(MODEL_REGISTRY.keys())
        if model_name not in available_models:
            logger.warning("Model %s not in registry. Falling back to grok-3", model_name)
            model_name = "grok-3"
            self.model_name = model_name

        logger.info("Loading %s model...", model_name)
        self.llm = create_llm(model_name)
        logger.info("RAGSystem: self.llm assigned = %s", self.llm)

        # Initialize tiktoken tokenizer for accurate token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Always start with minimal agents; full agentic setup is handled elsewhere if needed
        self.agents = create_agents(
            self.llm,
            self.vector_store,
            model_name=self.model_name,
            tokenizer=self.tokenizer,
            known_tags=getattr(self, "known_tags", None),
        )
        logger.info(f"Agents initialized: {list(self.agents.keys())}")
        # --- known tag cache loaded from vector store - helps identify entities in the query ---
        self.known_tags: set[str] = set()
        try:
            self.refresh_known_tags()
        except Exception as e:
            logger.warning(f"[RAG] Could not load known tags on init: {e}")

    def _vector_store_all_ids(self) -> list[str]:
        """
        Return ALL canonical document/entity IDs (tags) from the vector store.
        Tries a few common method names to avoid tight coupling.
        """
        vs = self.vector_store
        # Try common APIs
        for attr in ("list_ids", "get_all_ids", "get_all_document_ids", "all_ids"):
            if hasattr(vs, attr) and callable(getattr(vs, attr)):
                try:
                    ids = getattr(vs, attr)()
                    return [str(x) for x in ids]
                except Exception as e:
                    logger.debug(f"[RAG] {_safe_name(vs)}.{attr} failed: {e}")
        # Fallback: try listing collections and aggregating
        try:
            if hasattr(vs, "list_collections"):
                coll_names = vs.list_collections()
                ids = []
                for c in coll_names:
                    try:
                        ids.extend(vs.list_ids(collection=c))
                    except Exception:
                        pass
                return [str(x) for x in ids]
        except Exception as e:
            logger.debug(f"[RAG] Could not enumerate collections: {e}")
        return []

    def refresh_known_tags(self) -> None:
        """
        Populate self.known_tags (lowercased) from the vector store.
        Call this after any ingest/update that changes IDs.
        """
        ids = self._vector_store_all_ids()
        self.known_tags = {s.lower() for s in ids if isinstance(s, str)}
        logger.info(f"[RAG] known_tags loaded: {len(self.known_tags)}")

    def _safe_name(obj) -> str:
        return getattr(obj, "__class__", type(obj)).__name__
    
    def _initialize_sub_agents(self, llm_model: str) -> bool:
        """
        Initializes agents for agentic workflows (planner, researcher, etc.)
        """
        try:
            if self.vector_store is None:
                logger.error("Vector store not initialized")
                return False

            if not hasattr(self, "agents") or self.current_llm_model != llm_model:
                logger.info(f"Creating agents for LLM model: {llm_model}")
                self.agents = create_agents(
                    self.llm,
                    self.vector_store,
                    model_name=llm_model
                )
                self.current_llm_model = llm_model
                logger.info("Agents initialized successfully")

            # ✅ Attach chunk rewriter to XLSX processor if available
            chunk_rewriter = self.agents.get("chunk_rewriter")
            if not chunk_rewriter:
                logger.warning("Chunk rewriter agent not found")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG agents: {e}")
            return False


    def process_query_with_multi_collection_context(self, query: str, 
                                                    multi_collection_context: List[Dict[str, Any]], 
                                                    is_comparison_report: bool = False,
                                                    collection_mode: str = "multi",
                                                    provided_entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process a query with pre-retrieved multi-collection context and optional provided entities"""
        logger.info(f"Processing query with {len(multi_collection_context)} multi-collection chunks")
        if provided_entities:
            logger.info(f"Using provided entities: {provided_entities}")
        
        if self.use_cot:
            return self._process_query_with_report_agent(query, multi_collection_context, is_comparison_report, 
                                                        collection_mode=collection_mode, provided_entities=provided_entities)
        else:
            # For non-CoT mode, use the context directly
            return self._generate_response(query, multi_collection_context)
        
            
    def _process_query_with_report_agent(
        self,
        query: str,
        multi_collection_context: Optional[List[Dict[str, Any]]] = None,
        is_comparison_report: bool = False,
        collection_mode: str = "multi",
        provided_entities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Report agent pipeline using typed contracts:
        - Plan sections using PlannerAgent -> Plan
        - Retrieve chunks using ResearchAgent -> List[Chunk]
        - Write sections using SectionWriterAgent -> SectionDraft
        - Assemble report with ReportWriterAgent -> ReportResult
        """
        logger.info("Starting report generation pipeline")

        planner = self.agents.get("planner")
        researcher = self.agents.get("researcher")
        section_writer = self.agents.get("section_writer")
        report_writer = self.agents.get("report_agent")

        if not planner or not researcher or not section_writer or not report_writer:
            logger.warning("Missing one or more required agents")
            return self._generate_general_response(query)

        # STEP 1: Plan the report -> typed Plan
        logger.info("Planning report sections...")
        progress_bus.publish("Planning report sections…", step=1)
        if provided_entities:
            logger.info(f"Using provided entities for planning: {provided_entities}")
        try:
            plan = planner.plan_typed(
                query,
                is_comparison_report=is_comparison_report,
                provided_entities=provided_entities,
            )
        except Exception as e:
            logger.error(f"Error calling planner.plan_typed: {e}")
            return self._generate_general_response(query)

        if not plan.sections:
            logger.error("Planner returned no sections")
            return self._generate_general_response(query)

        # Render the decomposition — the visible evidence that the task was broken
        # down rather than answered in one shot. Guarded so plain logging still works.
        if hasattr(logger, "plan"):
            logger.plan(
                [
                    {
                        "topic": s.topic,
                        "role": s.role,
                        # Criteria are carried inside the per-entity retrieval steps,
                        # not as a field. Show one — they are mirrored across entities.
                        "criteria": next(iter(s.entity_steps.values()), ""),
                    }
                    for s in plan.sections
                ],
                entities=plan.entities,
            )
        else:
            logger.info("Sections planned: %s", [s.topic for s in plan.sections])

        # Now the denominator is known: plan + every section + assembly.
        progress_bus.set_total(len(plan.sections) + 3)
        progress_bus.publish(f"Planned {len(plan.sections)} sections", step=2)

        # PARALLEL SECTION PROCESSING
        def process_section(section_data: tuple[PlanSection, int]) -> tuple[SectionDraft, int]:
            """Process a single section (research + write) - runs in parallel."""
            plan_section, section_idx = section_data
            topic = plan_section.topic
            entity_steps = plan_section.entity_steps
            all_chunks: List[Chunk] = []

            section_started = time.time()
            logger.info(f"Processing section {section_idx+1}/{len(plan.sections)}: {topic}")
            progress_bus.publish(f"Researching: {topic}")

            if plan.is_comparison and len(entity_steps) >= 2:
                # Parallel research per entity (vector store calls only)
                with ThreadPoolExecutor(max_workers=min(len(entity_steps), 10)) as research_executor:
                    futures = {}
                    for entity, step in entity_steps.items():
                        future = research_executor.submit(
                            researcher.research, query, step, None, True, [entity], collection_mode
                        )
                        futures[future] = entity

                    for future in futures:
                        entity = futures[future]
                        try:
                            raw_chunks = future.result()
                            for chunk_dict in raw_chunks:
                                chunk_dict["_search_entity"] = entity
                            all_chunks.extend([Chunk.from_legacy_dict(c) for c in raw_chunks])
                        except Exception as err:
                            logger.warning(f"Research failed for entity '{entity}': {err}")
            else:
                # Single-entity mode
                for entity, step in entity_steps.items():
                    raw_chunks = researcher.research(
                        query, step, is_comparison=False,
                        entities=[entity], collection=collection_mode,
                    )
                    for chunk_dict in raw_chunks:
                        chunk_dict["_search_entity"] = entity
                    all_chunks.extend([Chunk.from_legacy_dict(c) for c in raw_chunks])

            logger.info(f"Collected {len(all_chunks)} chunks for topic: {topic}")
            progress_bus.publish(f"Writing ({len(all_chunks)} chunks): {topic}")

            # Write the section (LLM call — goes through semaphore internally)
            with llm_semaphore:
                section_draft = section_writer.write_section_typed(
                    topic, all_chunks,
                    entities=plan.entities,
                    is_comparison=plan.is_comparison,
                )

            if hasattr(logger, "section_done"):
                logger.section_done(
                    topic, len(all_chunks), len(section_draft.findings),
                    time.time() - section_started,
                )
            else:
                logger.info(f"Completed section {section_idx+1}: {topic}")
            progress_bus.publish(f"Wrote: {topic}", advance=True)
            return section_draft, len(all_chunks)

        # Two waves: retrieval-backed sections first, then the sections that reason
        # over them. A synthesize/recommend section cannot run in parallel with the
        # compare sections because its input is their output.
        retrieval_sections = [(s, i) for i, s in enumerate(plan.sections) if s.role == "compare"]
        derived_sections = [(s, i) for i, s in enumerate(plan.sections) if s.role != "compare"]

        logger.info(
            f"Processing {len(retrieval_sections)} retrieval sections in parallel, "
            f"then {len(derived_sections)} derived: "
            f"{[f'{s.topic}({s.role})' for s, _ in derived_sections]}"
        )

        all_drafts: List[SectionDraft] = []
        total_chunks_used = 0
        results_by_idx: Dict[int, tuple[SectionDraft, int]] = {}

        # --- Wave 1: compare sections (retrieve + write), in parallel -------------
        if retrieval_sections:
            max_workers = min(4, len(retrieval_sections))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                section_futures = [
                    (executor.submit(process_section, (section, idx)), idx)
                    for section, idx in retrieval_sections
                ]
                for future, idx in section_futures:
                    try:
                        draft, chunk_count = future.result()
                        results_by_idx[idx] = (draft, chunk_count)
                    except Exception as e:
                        logger.error(f"Section processing failed: {e}")

        # --- Wave 2: synthesize / recommend, reading wave 1's output --------------
        if derived_sections:
            prior = [results_by_idx[i][0] for i in sorted(results_by_idx.keys())]
            if not prior:
                logger.warning(
                    "No compare sections succeeded; derived sections have nothing to "
                    "reason over and will be skipped"
                )
            else:
                # Derived sections all read the same frozen `prior` list, so they are
                # independent of each other and can run concurrently within the wave.
                def write_derived(section_data: tuple[PlanSection, int]) -> tuple[SectionDraft, int]:
                    section, _idx = section_data
                    progress_bus.publish(f"Synthesising: {section.topic}")
                    with llm_semaphore:
                        return section_writer.write_derived_section_typed(
                            section.topic,
                            section.role,
                            prior,
                            entities=plan.entities,
                            query=query,
                        ), 0

                with ThreadPoolExecutor(max_workers=min(4, len(derived_sections))) as executor:
                    derived_futures = [
                        (executor.submit(write_derived, (section, idx)), idx, section.topic)
                        for section, idx in derived_sections
                    ]
                    for future, idx, topic in derived_futures:
                        try:
                            results_by_idx[idx] = future.result()
                            progress_bus.publish(f"Wrote: {topic}", advance=True)
                        except Exception as e:
                            logger.error(f"Derived section '{topic}' failed: {e}")

        # Maintain original order
        for idx in sorted(results_by_idx.keys()):
            draft, chunk_count = results_by_idx[idx]
            all_drafts.append(draft)
            total_chunks_used += chunk_count

        logger.info(f"Processed {len(all_drafts)} sections with {total_chunks_used} total chunks")

        # Write report -> typed ReportResult
        logger.info("Writing report with %d sections", len(all_drafts))
        progress_bus.publish("Writing summary, conclusion and charts…", advance=True)
        report_result = report_writer.write_report_typed(
            all_drafts, query=query,
        )

        # Return backward-compatible dict
        return {
            "answer": f"Report successfully written to {report_result.report_path}",
            "report_path": report_result.report_path,
            "sections": [s.to_legacy_dict() for s in all_drafts],
            "context": [],
            "total_chunks_used": report_result.total_chunks_used,
        }

    


    def _guess_entity_from_step(self, step: str, known_entities: List[str]) -> str:
        for entity in known_entities:
            if entity.lower() in step.lower():
                return entity
        return "Unknown"

    
    def _generate_text(self, prompt: str, max_length: int = None) -> str:
        """Generate text using the LLM."""
        start_time = time.time()
        logger.info("Generating text (prompt_len=%d)", len(prompt))

        result = self.llm(prompt)

        elapsed_time = time.time() - start_time
        logger.info("Text generation completed in %.2f seconds", elapsed_time)

        return result
    
    def _generate_response(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response using the retrieved context"""
        context_str = "\n\n".join([f"Context {i+1}:\n{item['content']}" 
                                  for i, item in enumerate(context)])
        
        template = """Answer the following query using the provided context. 
Respond as if you are knowledgeable about the topic and incorporate the context naturally.
Do not mention limitations in the context or that you couldn't find specific information.

Context:
{context}

Query: {query}

Answer:"""
        
        prompt = template.format(context=context_str, query=query)
        response_text = self._generate_text(prompt)
        
        # Add sources to response if available
        sources = {}
        if context:
            # Group sources by document
            for item in context:
                # Handle metadata which could be a string (from Oracle DB) or a dict (from ChromaDB)
                metadata = item['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata = {"source": "Unknown"}
                
                source = metadata.get('source', 'Unknown')
                if source not in sources:
                    sources[source] = set()
                
                # Add page number if available
                if 'page' in metadata:
                    sources[source].add(str(metadata['page']))
                # Add file path if available for code
                if 'file_path' in metadata:
                    sources[source] = metadata['file_path']
            
            # Print concise source information
            print("\nSources detected:")
            # Print a single line for each source without additional details
            for source in sources:
                print(f"- {source}")
        
        return {
            "answer": response_text,
            "context": context,
            "sources": sources
        }

    def _generate_general_response(self, query: str) -> Dict[str, Any]:
        """Generate a response using general knowledge when no context is available"""
        template = """You are a helpful AI assistant. Answer the following query using your general knowledge.

Query: {query}

Answer:"""
        
        prompt = template.format(query=query)
        response = self._generate_text(prompt)
        
        return {
            "answer": response,
            "context": []
        }

def main():
    parser = argparse.ArgumentParser(description="Query documents using local LLM")
    parser.add_argument("--query", required=True, help="Query to search for")
    parser.add_argument("--embed", default="oracle", choices=["oracle", "chromadb"], help="embed backend to use")
    parser.add_argument("--model", default="grok3", help="Model to use (default: qwen2)")
    parser.add_argument("--collection", help="Collection to search (PDF, Repository, General Knowledge)")
    parser.add_argument("--use-cot", action="store_true", help="Use Chain of Thought reasoning")
    parser.add_argument("--store-path", default="embed", help="Path to ChromaDB store")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip query analysis (not recommended)")
    parser.add_argument("--verbose", action="store_true", help="Show full content of sources")
    parser.add_argument("--quiet", action="store_true", help="Disable verbose logging")
    parser.add_argument("--quantization", choices=["4bit", "8bit"], help="Quantization method (4bit or 8bit)")
        
    args = parser.parse_args()
    
    # Set logging level based on quiet flag
    if args.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
    
    print("\nInitializing RAG agent...")
    print("=" * 50)
    print(f"Using model: {args.model}")
    
    try:
        # Determine which vector store to use based on args.embed
        if args.embed == "oracle" and ORACLE_DB_AVAILABLE:
            try:
                logger.info("Initializing Oracle DB vector store")
                store = OraDBVectorStore()
                print("✓ Using Oracle DB for vector storage")
            except Exception as e:
                logger.warning(f"Failed to initialize Oracle DB: {str(e)}")
                logger.info(f"Falling back to ChromaDB from: {args.store_path}")
                store = EnhancedVectorStore(persist_directory=args.store_path)
                print("⚠ Oracle DB initialization failed, using ChromaDB instead")
        else:
            if args.embed == "oracle" and not ORACLE_DB_AVAILABLE:
                logger.warning("Oracle DB support not available")
                print("⚠ Oracle DB support not available (missing dependencies)")
                
            logger.info(f"Initializing ChromaDB vector store from: {args.store_path}")
            store = EnhancedVectorStore(persist_directory=args.store_path)
            print("✓ Using ChromaDB for vector storage")
        
        logger.info("Initializing local RAG agent...")
        # Set use_oracle_db based on the actual store type
        use_oracle_db = args.embed == "oracle" and isinstance(store, OraDBVectorStore)
        
        print(f"Creating RAG System with model: {args.model}")
        agent = RAGSystem(
            store, 
            model_name=args.model, 
            use_cot=args.use_cot, 
            collection=args.collection,
            skip_analysis=args.skip_analysis,
            use_oracle_db=use_oracle_db
        )
        
        print(f"\nProcessing query: {args.query}")
        print("=" * 50)
        
        response = agent.process_query(args.query)
        
        print("\nResponse:")
        print("-" * 50)
        print(response["answer"])
        
        if response.get("reasoning_steps"):
            print("\nReasoning Steps:")
            print("-" * 50)
            for i, step in enumerate(response["reasoning_steps"]):
                print(f"\nStep {i+1}:")
                print(step)
        
        if response.get("context"):
            print("\nSources used:")
            print("-" * 50)
            
            # Print concise list of sources
            for i, ctx in enumerate(response["context"]):
                source = ctx["metadata"].get("source", "Unknown")
                if "page_numbers" in ctx["metadata"]:
                    pages = ctx["metadata"].get("page_numbers", [])
                    print(f"[{i+1}] {source} (pages: {pages})")
                else:
                    file_path = ctx["metadata"].get("file_path", "Unknown")
                    print(f"[{i+1}] {source} (file: {file_path})")
                
                # Only print content if verbose flag is set
                if args.verbose:
                    content_preview = ctx["content"][:300] + "..." if len(ctx["content"]) > 300 else ctx["content"]
                    print(f"    Content: {content_preview}\n")
    
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
