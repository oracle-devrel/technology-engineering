#!/usr/bin/env python3
"""Oracle Enterprise RAG System Interface."""

# Disable telemetry first to prevent startup errors
import disable_telemetry
# Patch gradio_client bool-schema crash before gradio builds any API info
import gradio_compat  # noqa: F401

import gradio as gr
import logging
import os
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

from local_rag_agent import RAGSystem
from llm_factory import get_available_models, MODEL_REGISTRY
from oci_embedding_handler import EmbeddingModelManager
from vector_store import EnhancedVectorStore
from ingest_xlsx import XLSXIngester
from ingest_pdf import PDFIngester

# Import modular handlers
from handlers.xlsx_handler import process_xlsx_file
from handlers.pdf_handler import process_pdf_file
from handlers.query_handler import process_query
from progress_bus import progress_bus
from utils.entity_utils import suggest_entities_from_filename
from handlers.vector_handler import (
    get_collection_stats,
    view_collection_documents,
    search_chunks,
    list_all_chunks,
    delete_all_chunks_in_collection
)
import chromadb
# We'll initialize the chroma_client dynamically based on the current embedding model
chroma_client = None

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class NoErrorsFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
file_handler = logging.FileHandler("logs/app.log", mode="a")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger = logging.getLogger(__name__)


class RAGAppController:
    """Main controller class for the RAG application."""
    
    def __init__(self) -> None:
        """Initialize the RAG application controller with default models and processors."""
        self.embedding_manager: EmbeddingModelManager = EmbeddingModelManager()
        self.vector_store: Optional[EnhancedVectorStore] = None
        self.rag_agent: Optional[RAGSystem] = None
        self.llm: Optional[Callable[[str], str]] = None

        self.xlsx_processor: Optional[XLSXIngester] = None
        self.pdf_processor: Optional[PDFIngester] = None

        # Initialize with environment settings or defaults
        self.current_embedding_model = os.getenv(
            "DEFAULT_EMBEDDING_MODEL",
            "cohere-embed-multilingual-v3.0"
        )
        self.current_llm_model = os.getenv("DEFAULT_LLM_MODEL", "grok-3")

        # Initialize available models for UI
        self.available_llm_models = self._get_available_llm_models()
        self.available_embedding_models = self._get_available_embedding_models()

        # Initialize core components
        self._initialize_vector_store(self.current_embedding_model)
        self._initialize_rag_agent(
            self.current_llm_model,
            collection="multi",
            embedding_model=self.current_embedding_model
        )

        # Initialize LLM wrapper if available
        if self.rag_agent and hasattr(self.rag_agent, "llm"):
            self.llm = self.rag_agent.llm
        else:
            self.llm = None
            logger.warning("No LLM wrapper found on RAG agent during init")

    def _get_available_embedding_models(self) -> List[str]:
        """
        Get list of available embedding models.
        
        Returns:
            List[str]: Names of available embedding models, including ChromaDB default
        """
        try:
            models = self.embedding_manager.list_available_models()
            model_names = [m["name"] for m in models]
            if "chromadb-default" not in model_names:
                model_names.insert(0, "chromadb-default")
            return model_names
        except Exception as e:
            logger.warning(f"Could not load embedding models: {e}")
            return ["chromadb-default"]

    def _get_available_llm_models(self) -> List[str]:
        """
        Get list of available LLM models from llm_factory.

        Returns:
            List[str]: Names of available LLM models
        """
        try:
            configured_models = get_available_models()
            logger.info(f"Available LLM models: {configured_models}")
            return configured_models
        except Exception as e:
            logger.error(f"Error getting available LLM models: {e}")
            return ["grok-3"]

    def _initialize_vector_store(self, embedding_model: str) -> str:
        """
        Initialize the vector store with specified embedding model.
        
        Args:
            embedding_model: Name of the embedding model to use
            
        Returns:
            str: Status message indicating success or failure
        """
        try:
            logger.info(f"Initializing vector store with embedding model: {embedding_model}")
            
            # Create embedder object for non-default models
            embedder = None
            if embedding_model != "chromadb-default":
                from oci_embedding_handler import OCIEmbeddingHandler
                try:
                    embedder = OCIEmbeddingHandler(model_name=embedding_model)
                    logger.info(f"Created OCI embedder for {embedding_model}")
                except Exception as e:
                    logger.error(f"Failed to create OCI embedder: {e}")
                    # Fall back to chromadb-default if OCI fails
                    embedding_model = "chromadb-default"
                    embedder = None
            
            persist_dir = f"embed-{embedding_model}"
            self.vector_store = EnhancedVectorStore(
                persist_directory=persist_dir,
                embedding_model=embedding_model,
                embedder=embedder  # Pass the embedder object!
            )
            
            # Bind collections to ensure correct dimensions
            self.vector_store.bind_collections_for_model(embedding_model)
            self.current_embedding_model = embedding_model

            logger.info("Vector store initialized successfully")
        
            if hasattr(self.vector_store, "debug_collections"):
                self.vector_store.debug_collections()
                
            return f"Vector store initialized with {embedding_model}"
        except Exception as e:
            msg = f"Failed to initialize vector store: {e}"
            logger.error(msg)
            return msg

    def _initialize_processors(self) -> Tuple[Optional[XLSXIngester], Optional[PDFIngester]]:
        """
        Initialize document processors for XLSX and PDF files.
        
        Returns:
            Tuple containing initialized processors (xlsx_processor, pdf_processor)
        """
        xlsx_proc = None
        pdf_proc = None

        try:
            chunk_rewriter = self.rag_agent.agents.get("chunk_rewriter") if self.rag_agent else None
            if self.xlsx_processor is None:
                self.xlsx_processor = XLSXIngester(
                    tokenizer="BAAI/bge-small-en-v1.5",
                    chunk_rewriter=chunk_rewriter
                )
            elif chunk_rewriter and self.xlsx_processor is not None:
                self.xlsx_processor.chunk_rewriter = chunk_rewriter
                logger.info("Chunk rewriter injected into XLSX processor")
                
            xlsx_proc = self.xlsx_processor
            logger.info("XLSX processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize XLSX processor: {e}")
            logger.error(traceback.format_exc())
            self.xlsx_processor = None

        try:
            self.pdf_processor = PDFIngester()
            pdf_proc = self.pdf_processor
            logger.info("PDF processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PDF processor: {e}")
            logger.error(traceback.format_exc())
            self.pdf_processor = None

        logger.info("Document processors initialization completed")
        return xlsx_proc, pdf_proc

    def _initialize_rag_agent(
        self,
        llm_model: str,
        collection: str = "multi",
        embedding_model: Optional[str] = None
    ) -> bool:
        """
        Initialize or update the RAG agent with specified parameters.
        
        Args:
            llm_model: Name of the LLM model to use
            collection: Name of the collection to use (default: "multi")
            embedding_model: Optional embedding model to switch to
            
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        try:
            # Handle embedding model switch if needed
            if embedding_model and embedding_model != self.current_embedding_model:
                logger.info(f"Switching embedding model to: {embedding_model}")
                result = self._initialize_vector_store(embedding_model)
                if "Failed" in result:
                    return False

            # Verify vector store initialization
            if self.vector_store is None:
                logger.error("Vector store not initialized")
                return False

            # Create new agent if needed
            if self.rag_agent is None or self.current_llm_model != llm_model:
                logger.info(f"Initializing RAG agent: {llm_model} with embedding {self.current_embedding_model}")
                self.rag_agent = RAGSystem(
                    vector_store=self.vector_store,
                    model_name=llm_model,
                    use_cot=True,
                    collection=collection,
                )
                self.current_llm_model = llm_model
                logger.info("RAG agent initialized successfully")

            # Set up LLM access
            if hasattr(self.rag_agent, "llm") and callable(self.rag_agent.llm):
                self.llm = self.rag_agent.llm
                logger.info("LLM callable exposed on RAGSystem")
            else:
                self.llm = None
                logger.warning("RAG agent does not expose a callable llm() method")

            # Configure chunk rewriter if available
            chunk_rewriter = self.rag_agent.agents.get("chunk_rewriter")
            if chunk_rewriter and self.xlsx_processor is not None:
                self.xlsx_processor.chunk_rewriter = chunk_rewriter
                logger.info("Chunk rewriter injected into XLSX processor")
            else:
                logger.warning("Could not inject chunk rewriter")

            # Finalize initialization
            self._initialize_processors()
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG agent: {e}")
            return False




rag_system = RAGAppController()




def _discover_sample_prompts(root: str = "sample_queries") -> Dict[str, Path]:
    """
    Map a readable label to each saved prompt file under sample_queries/.

    Files there have mixed conventions — some carry a .txt extension, some do not —
    so select on "is a readable file" rather than on suffix, and skip OS cruft.
    """
    prompts: Dict[str, Path] = {}
    root_path = Path(root)
    if not root_path.is_dir():
        logger.warning(f"Sample prompt directory not found: {root_path}")
        return prompts

    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        label = f"{path.parent.name} / {path.stem}" if path.parent != root_path else path.stem
        prompts[label] = path

    logger.info(f"Discovered {len(prompts)} saved prompts")
    return prompts


SAMPLE_PROMPTS: Dict[str, Path] = _discover_sample_prompts()


def create_oracle_interface():
    
    # Load external CSS
    # THEME SWITCHER: 
    # - For Cline dark theme: use "gradio.css"
    # - For original theme: use "gradio_backup.css"
    # Force CSS reload with timestamp
    import time
    css_timestamp = int(time.time())
    with open("gradio.css", "r") as f:
        gradio_css = f.read()
    
    # Add timestamp comment to force reload
    gradio_css = f"/* CSS Reload: {css_timestamp} */\n" + gradio_css
    
    # Add CSS to hide the footer (which contains the "Use via API" button)
    gradio_css += "\nfooter{display:none !important}"
    
    with gr.Blocks(title="Multi-Agent Report Generator", css=gradio_css) as interface:

        # Global Header. Colour and size come from .app-header in gradio.css — the
        # inline values here previously contradicted it (white text on a white
        # background) and only worked because the stylesheet's !important won.
        with gr.Row(elem_classes=["app-header"]):
            gr.Markdown("""
                <h1 style="margin: 0; font-weight: 600;
                text-transform: uppercase; letter-spacing: 2px;
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace;">
                Multi-Agent Report Generator</h1>
            """)

        with gr.Tab("DOCUMENT PROCESSING", id="processing"):
            gr.Markdown("### Configure Embedding Model and Process Documents")
            
            # Embedding model selection - ONLY in this tab
            with gr.Row():
                with gr.Column(scale=1):
                    embedding_model_selector_ingest = gr.Dropdown(
                        choices=rag_system.available_embedding_models,
                        value=rag_system.current_embedding_model,
                        label="Embedding Model for Ingestion",
                        info="Select the embedding model to use for document processing."
                    )
                with gr.Column(scale=2):
                    pass  # Empty column to make dropdown narrower
            
            gr.Markdown("---")
            gr.Markdown("### Upload and process documents")
            
            # Side-by-side XLSX and PDF Processing
            with gr.Row():
                # XLSX Upload Section
                with gr.Column(scale=1):
                    with gr.Group(elem_classes=["upload-section", "compact-upload"]):
                        gr.Markdown("#### XLSX Document Processing")
                        xlsx_file = gr.File(
                            label="Upload XLSX File", 
                            file_types=[".xlsx", ".xls"], 
                            type="filepath"
                        )
                        xlsx_entity = gr.Dropdown(
                            label="Entity",
                            choices=[],
                            value=None,
                            allow_custom_value=True,
                            info="Suggested from the filename on upload — pick one or type your own.",
                        )
                        xlsx_process_btn = gr.Button("Process XLSX", variant="secondary", elem_classes=["secondary-button"])
                        xlsx_summary = gr.Textbox(label="XLSX Summary", lines=2, max_lines=3, elem_classes=["compact-field"])

                # PDF Upload Section  
                with gr.Column(scale=1):
                    with gr.Group(elem_classes=["upload-section", "compact-upload"]):
                        gr.Markdown("#### PDF Document Processing")
                        pdf_file = gr.File(
                            label="Upload PDF File", 
                            file_types=[".pdf"], 
                            type="filepath"
                        )
                        pdf_entity = gr.Dropdown(
                            label="Entity",
                            choices=[],
                            value=None,
                            allow_custom_value=True,
                            info="Suggested from the filename on upload — pick one or type your own.",
                        )
                        pdf_process_btn = gr.Button("Process PDF", variant="secondary", elem_classes=["secondary-button"])
                        pdf_summary = gr.Textbox(label="PDF Summary", lines=2, max_lines=3, elem_classes=["compact-field"])

        with gr.Tab("VECTOR STORE VIEWER", id="viewer"):
            gr.Markdown("### Explore and analyze your vector store collections")
            
            # Add embedding model selector for this tab
            with gr.Row():
                embedding_model_selector_viewer = gr.Dropdown(
                    choices=rag_system.available_embedding_models,
                    value=rag_system.current_embedding_model,
                    label="Embedding Model",
                    info="Select the embedding model to view collections for"
                )

            with gr.Row():
                with gr.Column(scale=1):
                    stats_refresh_btn = gr.Button("REFRESH STATS", variant="secondary", elem_classes=["secondary-button"])
                    collection_stats = gr.Textbox(
                        elem_id="scientific-stats-box",
                        label="Collection Statistics",
                        lines=20,
                        max_lines=25
                    )
                with gr.Column(scale=1):
                    collection_selector = gr.Dropdown(
                        choices=["PDF Documents", "XLSX Documents", "Web Documents", 
                                 "Repository Documents", "General Knowledge"],
                        value="XLSX Documents",
                        label="Select Collection"
                    )
                    view_docs_btn = gr.Button("VIEW DOCUMENTS", variant="secondary", elem_classes=["secondary-button"])
                    collection_documents = gr.Textbox(
                        label="Collection Documents",
                        lines=15,
                        max_lines=20
                    )

            gr.Markdown("### LIST ALL CHUNKS")
            with gr.Row():
                chunks_collection = gr.Dropdown(
                    choices=["PDF Documents", "XLSX Documents"],
                    value="XLSX Documents",
                    label="Collection to List",
                    scale=2
                )
                list_chunks_btn = gr.Button("LIST ALL CHUNKS", variant="secondary", elem_classes=["secondary-button"], scale=1)
            
            all_chunks_display = gr.Textbox(
                elem_id="all-chunks-display",
                label="All Chunks",
                lines=20,
                max_lines=25,
                placeholder="All chunks will be displayed here..."
            )

            # Collapsed by default: an irreversible one-click wipe should not sit
            # open on screen while this tab is being shown to an audience.
            with gr.Accordion("⚠️ Danger zone — delete all chunks", open=False):
                with gr.Row():
                    delete_collection = gr.Dropdown(
                        choices=["PDF Documents", "XLSX Documents"],
                        value="XLSX Documents",
                        label="Collection to Delete",
                        scale=2
                    )
                    with gr.Column(scale=1):
                        delete_chunks_btn = gr.Button("🗑️ DELETE ALL CHUNKS", variant="stop", size="sm")
                        gr.Markdown("*⚠️ This action cannot be undone*", elem_classes=["warning-text"])

                delete_result = gr.Textbox(
                    label="Deletion Result",
                    lines=5,
                    max_lines=8,
                    placeholder="Deletion results will appear here..."
                )

        with gr.Tab("INFERENCE & QUERY", id="inference"):
            with gr.Row():
                # Left Column - Query Input
                with gr.Column(scale=1, elem_classes=["inference-left-column"]):
                    # Large Query Section
                    with gr.Group(elem_classes=["query-section"]):
                        # Saved prompts, so a 3,000-character task prompt does not
                        # have to be pasted in live.
                        sample_prompt_selector = gr.Dropdown(
                            choices=[""] + list(SAMPLE_PROMPTS.keys()),
                            value="",
                            label="Load a saved prompt",
                            info="Populates the query box below. Edit freely after loading.",
                        )

                        query_input = gr.Textbox(
                            label="Query",
                            lines=15,  # Much larger query area
                            max_lines=20,
                            placeholder="Enter your query here...",
                            elem_classes=["compact-query"]
                        )

                        query_btn = gr.Button(
                            "Run Query", 
                            elem_classes=["primary-button"], 
                            size="lg",
                            elem_id="run-query-btn"
                        )
                    
                    # Compact Configuration Section - All in one group
                    with gr.Group(elem_classes=["compact-settings"]):
                        # Model Configuration in one row
                        with gr.Row():
                            llm_model_selector = gr.Dropdown(
                                choices=rag_system.available_llm_models,
                                value=rag_system.current_llm_model,
                                label="LLM Model",
                                scale=1
                            )
                            embedding_model_selector_query = gr.Dropdown(
                                choices=rag_system.available_embedding_models,
                                value=rag_system.current_embedding_model,
                                label="Embeddings",
                                interactive=True,
                                scale=1
                            )
                        
                        # Data Sources and Processing Mode in one compact row.
                        # XLSX + Agentic default ON: the multi-agent report pipeline
                        # lives behind agent_mode, and starting with everything off
                        # meant a fresh launch silently produced nothing useful.
                        with gr.Row():
                            collection_pdf = gr.Checkbox(label="Include PDF", value=True, scale=1)
                            collection_xlsx = gr.Checkbox(label="Include XLSX", value=True, scale=1)
                            agent_mode = gr.Checkbox(label="Agentic Mode", value=True, scale=1)

                        # Deterministic, model-independent entity selection. Populated
                        # from the tags actually in the store (see vector_store.list_entities),
                        # so a pick always matches retrieval's exact-match filter. Leave
                        # empty to fall back to LLM extraction from the prompt.
                        with gr.Row():
                            def _initial_entities():
                                try:
                                    return rag_system.vector_store.list_entities()
                                except Exception:
                                    return []
                            query_entities = gr.Dropdown(
                                label="Entities to compare",
                                info="From ingested documents. Leave empty to auto-detect from the prompt.",
                                choices=_initial_entities(),
                                value=[],
                                multiselect=True,
                                allow_custom_value=True,
                                scale=5,
                            )
                            refresh_entities_btn = gr.Button("↻ Refresh", scale=1, elem_classes=["secondary-button"])

                        # Chunks retrieved per entity per section. Lower = tighter,
                        # fewer citations; higher = more context. Overrides RESEARCH_TOP_K.
                        with gr.Row():
                            top_k_slider = gr.Slider(
                                minimum=1, maximum=12, value=4, step=1,
                                label="Chunks per entity (TOP_K)",
                                info="Lower = tighter & fewer citations; higher = more context per section.",
                            )
                
                # Right Column - Results
                with gr.Column(scale=1, elem_classes=["inference-right-column"]):
                    gr.Markdown("#### Query Results")
                    
                    # Add status indicator
                    status_box = gr.Markdown(
                        value="",
                        visible=False,
                        elem_classes=["status-indicator"]
                    )
                    
                    response_box = gr.Markdown()

                    # Charts appear here as each section renders one. They were
                    # previously only visible inside the downloaded .docx.
                    charts_gallery = gr.Gallery(
                        label="📊 Charts",
                        visible=False,
                        columns=2,
                        height="auto",
                        object_fit="contain",
                        show_label=True,
                    )

                    # Download section for generated reports
                    download_file = gr.File(
                        label="📄 Download Generated Report",
                        visible=False,
                        interactive=False
                    )

        # === Callbacks ===

        def load_sample_prompt(label: str):
            """Populate the query box from a saved prompt file."""
            if not label:
                return gr.update()
            path = SAMPLE_PROMPTS.get(label)
            if not path:
                return gr.update()
            try:
                return gr.update(value=path.read_text(encoding="utf-8").strip())
            except Exception as e:
                logger.error(f"Could not read sample prompt {path}: {e}")
                return gr.update(value=f"Could not read {path}: {e}")

        def _default_entity(file, entity: str) -> str:
            """
            Fall back to the filename stem when no entity is typed.

            Both ingest handlers hard-require an entity and return an error string if
            it is blank — which the UI then displayed as success. The entity is also
            the retrieval filter key, so it has to match the name used in the query
            prompt: Supremo1.xlsx -> "supremo1", which is exactly what the planner
            extracts from "compare Supremo1 and Supremo2".
            """
            if entity and entity.strip():
                return entity.strip()
            if file is None:
                return ""
            return Path(file.name).stem.strip().lower()

        # These handlers return (summary, detailed_log) — NOT (success, summary).
        # The summary already carries its own ✅/❌, so display it directly. The old
        # code unpacked it as a success flag and printed "Processed successfully!"
        # unconditionally, hiding "❌ ERROR: Entity name is required" behind a tick.
        def process_xlsx_and_clear(file, model, entity, progress=gr.Progress()):
            resolved = _default_entity(file, entity)
            progress(0, desc=f"Ingesting {Path(file.name).name if file else 'file'} as '{resolved}'…")
            summary, detailed_log = process_xlsx_file(file, model, rag_system, resolved)
            if not (entity and entity.strip()) and resolved:
                summary = f"ℹ️ No entity given — used **{resolved}** (from filename).\n\n{summary}"
            return summary, gr.update(value="")

        def process_pdf_and_clear(file, model, entity, progress=gr.Progress()):
            resolved = _default_entity(file, entity)
            progress(0, desc=f"Ingesting {Path(file.name).name if file else 'file'} as '{resolved}'…")
            summary, detailed_log = process_pdf_file(file, model, rag_system, resolved)
            if not (entity and entity.strip()) and resolved:
                summary = f"ℹ️ No entity given — used **{resolved}** (from filename).\n\n{summary}"
            return summary, gr.update(value="")

        # On upload, suggest up to 3 entity-name variants from the filename and
        # preselect the first. Deterministic; the user can still pick another or type.
        def _suggest_entity_from_file(file):
            if file is None:
                return gr.update(choices=[], value=None)
            variants = suggest_entities_from_filename(Path(file.name).name)
            return gr.update(choices=variants, value=(variants[0] if variants else None))

        pdf_file.change(fn=_suggest_entity_from_file, inputs=[pdf_file], outputs=[pdf_entity])
        xlsx_file.change(fn=_suggest_entity_from_file, inputs=[xlsx_file], outputs=[xlsx_entity])

        # Refresh the query-time entity picker from what is actually in the store.
        def _refresh_query_entities():
            try:
                return gr.update(choices=rag_system.vector_store.list_entities())
            except Exception:
                return gr.update()

        refresh_entities_btn.click(fn=_refresh_query_entities, outputs=[query_entities])

        # After ingesting, tick the matching collection (so a query defaults to the
        # collection just populated) and refresh the entity picker.
        xlsx_process_btn.click(
            fn=process_xlsx_and_clear,
            inputs=[xlsx_file, embedding_model_selector_ingest, xlsx_entity],
            outputs=[xlsx_summary, xlsx_entity]
        ).then(
            fn=lambda: (gr.update(value=True), _refresh_query_entities()),
            outputs=[collection_xlsx, query_entities],
        )

        pdf_process_btn.click(
            fn=process_pdf_and_clear,
            inputs=[pdf_file, embedding_model_selector_ingest, pdf_entity],
            outputs=[pdf_summary, pdf_entity]
        ).then(
            fn=lambda: (gr.update(value=True), _refresh_query_entities()),
            outputs=[collection_pdf, query_entities],
        )

        stats_refresh_btn.click(
            fn=lambda emb: get_collection_stats(emb, rag_system),
            inputs=[embedding_model_selector_viewer],
            outputs=[collection_stats]
        )

        view_docs_btn.click(
            fn=lambda coll, emb: view_collection_documents(coll, emb, rag_system),
            inputs=[collection_selector, embedding_model_selector_viewer],
            outputs=[collection_documents]
        )

        # search_btn.click(
        #     fn=lambda q, coll, emb, n: search_chunks(q, coll, emb, rag_system, n),
        #     inputs=[search_query, search_collection, embedding_model_selector_search, search_results_count],
        #     outputs=[search_results]
        # )

        list_chunks_btn.click(
            fn=lambda coll, emb: list_all_chunks(coll, emb, rag_system),
            inputs=[chunks_collection, embedding_model_selector_viewer],
            outputs=[all_chunks_display]
        )


        delete_chunks_btn.click(
            fn=lambda coll, emb: delete_all_chunks_in_collection(coll, emb, rag_system),
            inputs=[delete_collection, embedding_model_selector_viewer],
            outputs=[delete_result]
        )

        def _format_status(snap, agentic: bool) -> str:
            """Render the progress bus snapshot as the status panel's markdown."""
            mins, secs = divmod(int(snap.elapsed), 60)
            clock = f"{mins}:{secs:02d}"

            if not agentic:
                return f"✍️ **Generating response…**  ·  elapsed {clock}"

            if snap.total_steps:
                filled = int(snap.fraction * 20)
                bar = "█" * filled + "░" * (20 - filled)
                headline = (
                    f"🤖 **Multi-agent processing**  ·  step {snap.step}/{snap.total_steps}"
                    f"  ·  elapsed {clock}\n\n`{bar}`  {int(snap.fraction * 100)}%"
                )
            else:
                headline = f"🤖 **Multi-agent processing**  ·  elapsed {clock}"

            current = f"\n\n**{snap.message}**" if snap.message else ""

            # Most recent activity first — the tail is what is actually happening.
            recent = snap.events[-6:]
            trail = "\n".join(f"- {e}" for e in reversed(recent)) if recent else ""
            trail = f"\n\n{trail}" if trail else ""

            return headline + current + trail

        def handle_query_with_download(query, llm_model, embedding_model, include_pdf, include_xlsx, agentic, selected_entities, top_k, progress=gr.Progress()):
            """
            Run the query on a worker thread and stream real progress.

            Previously every yield here fired within milliseconds and then
            process_query() blocked for minutes, so the bar jumped to 70% and froze.
            The pipeline now publishes milestones to progress_bus and this generator
            polls them while the work actually runs.
            """
            # Deterministic entity selection from the picker; empty => LLM auto-detect.
            selected_entities = [e for e in (selected_entities or []) if e and e.strip()]

            progress_bus.start(message="Initialising…")
            yield (
                gr.update(value="🔄 **Starting…**", visible=True),
                gr.update(value=""),
                gr.update(visible=False),
                gr.update(value=[], visible=False),
            )

            result: dict = {}

            def _run():
                try:
                    result["value"] = process_query(
                        query, llm_model, embedding_model,
                        include_pdf, include_xlsx, agentic,
                        rag_system, provided_entities=selected_entities,
                        top_k=int(top_k) if top_k else None,
                    )
                except Exception as e:
                    logger.exception("Query processing failed")
                    result["error"] = e
                finally:
                    progress_bus.finish()

            worker = threading.Thread(target=_run, daemon=True, name="rag-query")
            worker.start()

            last_render = ""
            last_chart_count = 0
            while worker.is_alive():
                worker.join(timeout=0.5)
                snap = progress_bus.snapshot()
                progress(snap.fraction, desc=snap.message or "Working…")
                rendered = _format_status(snap, agentic)
                if rendered == last_render:
                    continue
                last_render = rendered

                # The status text changes every second (it carries the clock), but
                # the gallery must only be rebuilt when a new chart actually lands —
                # otherwise it reloads and flickers once a second for minutes.
                if len(snap.charts) != last_chart_count:
                    last_chart_count = len(snap.charts)
                    gallery_update = gr.update(value=snap.charts, visible=True)
                else:
                    gallery_update = gr.update()

                yield (
                    gr.update(value=rendered, visible=True),
                    gr.update(),
                    gr.update(),
                    gallery_update,
                )

            snap = progress_bus.snapshot()
            progress(1.0, desc="Complete!")

            if "error" in result:
                yield (
                    gr.update(
                        value=f"❌ **Query failed**\n\n```\n{result['error']}\n```",
                        visible=True,
                    ),
                    gr.update(value=""),
                    gr.update(visible=False),
                    gr.update(value=snap.charts, visible=bool(snap.charts)),
                )
                return

            response, report_path = result.get("value", ("No response produced.", None))
            elapsed = int(snap.elapsed)
            done = f"✅ **Complete** in {elapsed // 60}:{elapsed % 60:02d}"

            yield (
                gr.update(value=done, visible=True),
                response,
                gr.update(value=report_path, visible=True)
                if report_path and Path(report_path).exists()
                else gr.update(visible=False),
                gr.update(value=snap.charts, visible=bool(snap.charts)),
            )

        sample_prompt_selector.change(
            fn=load_sample_prompt,
            inputs=[sample_prompt_selector],
            outputs=[query_input],
        )

        query_btn.click(
            fn=handle_query_with_download,
            inputs=[query_input, llm_model_selector, embedding_model_selector_query, collection_pdf, collection_xlsx, agent_mode, query_entities, top_k_slider],
            outputs=[status_box, response_box, download_file, charts_gallery],
            show_progress="minimal"
        )

    return interface


def show_embedding_info(model_name):
    try:
        if model_name == "chromadb-default":
            return gr.update(
                value="ChromaDB Default (BAAI/bge-small-en-v1.5)\n"
                    "Dimensions: 384\n"
                    "Type: Local",
                visible=True
            )
        else:
            models = rag_system.embedding_manager.list_available_models()
            for model in models:
                if model["name"] == model_name:
                    info = (
                        f"{model['name']}\n"
                        f"Description: {model.get('description', 'N/A')}\n"
                        f"Dimensions: {model.get('dimensions', 'N/A')}\n"
                        f"Type: OCI"
                    )
                    return gr.update(value=info, visible=True)
            return gr.update(value="Model information not available", visible=True)
    except Exception as e:
        return gr.update(value=f"Error: {str(e)}", visible=True)

        
if __name__ == "__main__":
    logger.info("Launching Oracle Enterprise RAG Interface")
    ui = create_oracle_interface()
    # Streaming generators need the queue; without it the progress updates above
    # are collapsed into a single response at the end.
    ui.queue()
    ui.launch(
        server_name="0.0.0.0", 
        server_port=7863, 
        share=False, 
        debug=True, 
        show_error=True,
        show_api=False  # Disable the "Use via API" button
    )
