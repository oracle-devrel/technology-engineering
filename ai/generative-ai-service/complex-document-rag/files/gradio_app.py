#!/usr/bin/env python3
"""Oracle Enterprise RAG System Interface."""

import gradio as gr
import logging
import os
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

from local_rag_agent import RAGSystem
from local_rag_agent import OCIModelHandler, LocalLLM
from oci_embedding_handler import EmbeddingModelManager
from vector_store import EnhancedVectorStore
from ingest_xlsx import XLSXIngester
from ingest_pdf import PDFIngester

# Import modular handlers
from handlers.xlsx_handler import process_xlsx_file
from handlers.pdf_handler import process_pdf_file
from handlers.query_handler import process_query
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
            collection="Multi-Collection",
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
        Get list of available LLM models dynamically from OCIModelHandler.
        
        Returns:
            List[str]: Names of available LLM models
        """
        try:
            # Get all available models from OCIModelHandler
            available_models = OCIModelHandler.get_available_models()
            
            # Filter out models that don't have required configuration
            configured_models = []
            for model_name in available_models:
                try:
                    # Check if model can be initialized (has required env vars or is dedicated)
                    model_config = OCIModelHandler.MODEL_CONFIGS.get(model_name, {})
                    
                    # Check if it's a dedicated cluster (always available)
                    if model_config.get("is_dedicated", False):
                        # Check if DAC compartment is configured
                        if os.getenv("COMPARTMENT_ID_DAC"):
                            configured_models.append(model_name)
                            logger.info(f"Added dedicated cluster model: {model_name}")
                    # Check if model has required environment variables
                    elif model_config.get("model_id"):
                        configured_models.append(model_name)
                    else:
                        # Check environment variables for non-dedicated models
                        model_env_mapping = {
                            "grok-3": ["OCI_GROK_3_MODEL_ID", "GROK_MODEL_ID"],
                            "grok-3-fast": ["OCI_GROK_3_FAST_MODEL_ID"],
                            "grok-4": ["OCI_GROK_4_MODEL_ID"],
                            "llama3.3": ["OCI_LLAMA_3_3_MODEL_ID"],
                            "cohere-command-a": ["OCI_COHERE_COMMAND_A_MODEL_ID"],
                        }
                        
                        if model_name in model_env_mapping:
                            envs = model_env_mapping[model_name]
                            if any(os.getenv(ev) for ev in envs):
                                configured_models.append(model_name)
                except Exception as e:
                    logger.warning(f"Could not validate model {model_name}: {e}")
            
            if not configured_models:
                logger.warning("No configured LLM models found, using defaults")
                configured_models = ["grok-3"]  # Fallback to at least one model
            
            logger.info(f"Available LLM models: {configured_models}")
            return configured_models
            
        except Exception as e:
            logger.error(f"Error getting available LLM models: {e}")
            # Return fallback list
            return ["grok-3", "grok-4", "llama3.3", "cohere-command-a"]

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
        collection: str = "Multi-Collection",
        embedding_model: Optional[str] = None
    ) -> bool:
        """
        Initialize or update the RAG agent with specified parameters.
        
        Args:
            llm_model: Name of the LLM model to use
            collection: Name of the collection to use (default: "Multi-Collection")
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
    
    with gr.Blocks(title="RAG Report Generator", css=gradio_css) as interface:

        # Global Header
        with gr.Row(elem_classes=["app-header"]):
            gr.Markdown("""
                <h1 style="margin: 0; color: #ffffff; font-size: 1.8rem; font-weight: 600; 
                text-transform: uppercase; letter-spacing: 2px; 
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace;">
                RAG Report Generator</h1>
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
                        xlsx_entity = gr.Textbox(
                            label="Entity", 
                            placeholder="e.g. ZypherCorp",
                            max_lines=1
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
                        pdf_entity = gr.Textbox(
                            label="Entity", 
                            placeholder="e.g. TechCorp Inc.",
                            max_lines=1
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

            gr.Markdown("### ⚠️ DELETE ALL CHUNKS")
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

        with gr.Tab("SEARCH COLLECTIONS", id="search"):
            gr.Markdown("### Search through your vector store collections")
            
            # Add embedding model selector for search tab
            with gr.Row():
                embedding_model_selector_search = gr.Dropdown(
                    choices=rag_system.available_embedding_models,
                    value=rag_system.current_embedding_model,
                    label="Embedding Model for Search",
                    info="Select the embedding model to use for searching"
                )
            
            with gr.Row():
                search_query = gr.Textbox(
                    label="Search Query",
                    placeholder="Enter search terms...",
                    scale=3
                )
                search_collection = gr.Dropdown(
                    choices=["PDF Documents", "XLSX Documents"],
                    value="XLSX Documents",
                    label="Collection",
                    scale=1
                )
                search_results_count = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="Results",
                    scale=1
                )
            
            search_btn = gr.Button("Search", variant="secondary", elem_classes=["secondary-button"])
            
            search_results = gr.Textbox(
                elem_id="scientific-results-box",
                label="Search Results",
                lines=25,
                max_lines=30,
                placeholder="Search results will appear here..."
            )

        with gr.Tab("INFERENCE & QUERY", id="inference"):
            with gr.Row():
                # Left Column - Input Controls
                with gr.Column(scale=1, elem_classes=["inference-left-column"]):
                    # Query Section
                    with gr.Group(elem_classes=["query-section"]):
                        query_input = gr.Textbox(
                            label="Query", 
                            lines=4,
                            max_lines=6,
                            placeholder="Enter your query here...",
                            elem_classes=["compact-query"]
                        )
                        query_btn = gr.Button(
                            "Run Query", 
                            elem_classes=["primary-button"], 
                            size="sm",
                            elem_id="run-query-btn"
                        )
                    
                    # Model Configuration
                    with gr.Group(elem_classes=["model-controls"]):
                        gr.HTML("<h4>Model Configuration</h4>")
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
                                label="Embedding Model",
                                interactive=True,
                                scale=1
                            )
                    
                    # Data Sources
                    with gr.Group(elem_classes=["collection-controls"]):
                        gr.HTML("<h4>Data Sources</h4>")
                        with gr.Row():
                            collection_pdf = gr.Checkbox(label="Include PDF Collection", value=False)
                            collection_xlsx = gr.Checkbox(label="Include XLSX Collection", value=False)
                    
                    # Processing Mode
                    with gr.Group(elem_classes=["processing-controls"]):
                        gr.HTML("<h4>Processing Mode</h4>")
                        agent_mode = gr.Checkbox(
                            label="Use Agentic Workflow", 
                            value=False,
                            info="Enable advanced reasoning and multi-step processing"
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
                    
                    # Download section for generated reports
                    download_file = gr.File(
                        label="📄 Download Generated Report",
                        visible=False,
                        interactive=False
                    )

        # === Callbacks ===

        def process_xlsx_and_clear(file, model, entity):
            # Process file and get just the summary (no processing status)
            success, summary = process_xlsx_file(file, model, rag_system, entity)
            return f"Processed successfully!\n{summary}", gr.update(value="")

        def process_pdf_and_clear(file, model, entity):
            # Process file and get just the summary (no processing status) 
            success, summary = process_pdf_file(file, model, rag_system, entity)
            return f"Processed successfully!\n{summary}", gr.update(value="")

        xlsx_process_btn.click(
            fn=process_xlsx_and_clear,
            inputs=[xlsx_file, embedding_model_selector_ingest, xlsx_entity],
            outputs=[xlsx_summary, xlsx_entity]
        )

        pdf_process_btn.click(
            fn=process_pdf_and_clear,
            inputs=[pdf_file, embedding_model_selector_ingest, pdf_entity],
            outputs=[pdf_summary, pdf_entity]
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

        search_btn.click(
            fn=lambda q, coll, emb, n: search_chunks(q, coll, emb, rag_system, n),
            inputs=[search_query, search_collection, embedding_model_selector_search, search_results_count],
            outputs=[search_results]
        )

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

        def handle_query_with_download(query, llm_model, embedding_model, include_pdf, include_xlsx, agentic, progress=gr.Progress()):
            """Handle query and manage download functionality with progress updates"""
            
            # Show initial status
            yield (
                gr.update(value="🔄 **Processing Query...**\n\nInitializing system...", visible=True),
                gr.update(value=""),
                gr.update(visible=False)
            )
            
            # Update progress
            progress(0.2, desc="Connecting to models...")
            yield (
                gr.update(value="🔄 **Processing Query...**\n\nConnecting to models and preparing collections...", visible=True),
                gr.update(value=""),
                gr.update(visible=False)
            )
            
            # Process the query
            progress(0.5, desc="Analyzing query and retrieving context...")
            yield (
                gr.update(value="🔄 **Processing Query...**\n\nAnalyzing query and retrieving relevant context from collections...", visible=True),
                gr.update(value=""),
                gr.update(visible=False)
            )
            
            # If agentic mode, show additional status
            if agentic:
                progress(0.7, desc="Running multi-agent workflow...")
                yield (
                    gr.update(value="🤖 **Multi-Agent Processing...**\n\nAgents are planning, researching, and writing report sections...\n\nThis may take a few moments for comprehensive analysis.", visible=True),
                    gr.update(value=""),
                    gr.update(visible=False)
                )
            else:
                progress(0.7, desc="Generating response...")
                yield (
                    gr.update(value="✍️ **Generating Response...**\n\nProcessing retrieved context and formulating answer...", visible=True),
                    gr.update(value=""),
                    gr.update(visible=False)
                )
            
            # Actually process the query
            response, report_path = process_query(query, llm_model, embedding_model, include_pdf, include_xlsx, agentic, rag_system)
            
            progress(1.0, desc="Complete!")
            
            # Return final results and hide status
            if report_path and Path(report_path).exists():
                # Show download components
                yield (
                    gr.update(visible=False),  # Hide status
                    response,
                    gr.update(value=report_path, visible=True)
                )
            else:
                # Hide download components
                yield (
                    gr.update(visible=False),  # Hide status
                    response,
                    gr.update(visible=False)
                )

        query_btn.click(
            fn=handle_query_with_download,
            inputs=[query_input, llm_model_selector, embedding_model_selector_query, collection_pdf, collection_xlsx, agent_mode],
            outputs=[status_box, response_box, download_file],
            show_progress="full"
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
    ui.launch(
        server_name="0.0.0.0", 
        server_port=7863, 
        share=False, 
        debug=True, 
        show_error=True,
        show_api=False  # Disable the "Use via API" button
    )
