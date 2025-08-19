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
from vector_store import EnhancedVectorStore

load_dotenv()

try:
    from OraDBVectorStore import OraDBVectorStore
    ORACLE_DB_AVAILABLE = True
except ImportError:
    ORACLE_DB_AVAILABLE = False
    logging.warning(
        "Oracle DB support not available. "
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

class LocalLLM:
    """Wrapper for OCI LLM to match LangChain's ChatOpenAI interface"""
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __call__(self, prompt: str) -> str:
        # This gets used when you do `llm(prompt)`
        max_tokens = getattr(self.pipeline, 'model_config', {}).get('max_output_tokens', 4000)
        return self.pipeline(prompt, max_new_tokens=max_tokens)[0]["generated_text"].strip()
    
    def invoke(self, messages):
        # Convert messages to a single prompt
        prompt = "\n".join([msg.content for msg in messages])
        
        # Use model-specific max tokens from the pipeline's model config
        max_tokens = getattr(self.pipeline, 'model_config', {}).get('max_output_tokens', 4000)
        result = self.pipeline(prompt, max_new_tokens=max_tokens)[0]["generated_text"]
        
        # Create a response object with content attribute
        class Response:
            def __init__(self, content):
                self.content = content
        
        return Response(result.strip())
    
class OCIModelHandler:
    """Handler for calling multiple OCI Generative AI models"""
    
    # Model configurations
    MODEL_CONFIGS = {
        "grok-4": {
            "model_id": os.getenv("OCI_GROK_4_MODEL_ID"),
            "request_type": "generic",
            "max_output_tokens": 120000,  
            "default_params": {
                "temperature": 1,
                "top_p": 1
            }
        },
        "grok-3": {
            "model_id": os.getenv("OCI_GROK_3_MODEL_ID", 
                                 os.getenv("GROK_MODEL_ID")),
            "request_type": "generic",
            "max_output_tokens": 16000, 
            "default_params": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        "grok-3-fast": {
            "model_id": os.getenv("OCI_GROK_3_FAST_MODEL_ID", 
                                 os.getenv("GROK_MODEL_ID")),
            "request_type": "generic",
            "max_output_tokens": 16000,  
            "default_params": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        "llama3.3": {
            "model_id": os.getenv("OCI_LLAMA_3_3_MODEL_ID"),
            "request_type": "generic",
            "max_output_tokens": 4000,  
            "default_params": {
                "temperature": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "top_p": 0.75
            }
        },
        "cohere-command-a": {
            "model_id": os.getenv("OCI_COHERE_COMMAND_A_MODEL_ID"),
            "request_type": "cohere",
            "max_output_tokens": 4000,   # Cohere limited to 4K output
            "default_params": {
                "temperature": 1,
                "frequency_penalty": 0,
                "top_p": 0.75,
                "top_k": 0
            }
        },
        "dac-cluster": {
            "endpoint_id": "ocid1.generativeaiendpoint.oc1.eu-frankfurt-1.amaaaaaa2xxap7yaj6ki7iooezw6yrkj5lj6l2y43xekiekg2jxu4li2tnna",
            "request_type": "generic",
            "max_output_tokens": 600,  # Adjust based on your DAC configuration
            "is_dedicated": True,
            "region": "eu-frankfurt-1",
            "default_params": {
                "temperature": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "top_p": 0.75
            }
        }
    }
    
    def __init__(self, model_name: str = "grok-3", config_profile: str = "DEFAULT", compartment_id: str = None):
        """Initialize OCI model handler
        
        Args:
            model_name: Name of the model to use (grok-4, grok-3, grok-3-fast, llama3.3, cohere-command-a, dac-cluster, etc.)
            config_profile: OCI config profile to use
            compartment_id: OCI compartment ID (if None, will try to get from environment)
        """
        import oci
        self.oci = oci
        self.model_name = model_name
        
        # Validate model name
        if model_name not in self.MODEL_CONFIGS:
            available_models = ", ".join(self.MODEL_CONFIGS.keys())
            raise ValueError(f"Unsupported model: {model_name}. Available models: {available_models}")
        
        self.model_config = self.MODEL_CONFIGS[model_name]
        
        # Check if this is a dedicated cluster
        is_dedicated = self.model_config.get("is_dedicated", False)
        
        # Validate that model ID or endpoint ID is available
        if not is_dedicated and not self.model_config.get("model_id"):
            env_var_map = {
                "grok-4": "OCI_GROK_4_MODEL_ID",
                "grok-3": "OCI_GROK_3_MODEL_ID or GROK_MODEL_ID",
                "grok-3-fast": "OCI_GROK_3_FAST_MODEL_ID",
                "llama3.3": "OCI_LLAMA_3_3_MODEL_ID",
                "cohere-command-a": "OCI_COHERE_COMMAND_A_MODEL_ID"
            }
            required_env = env_var_map.get(model_name, "Unknown")
            raise ValueError(
                f"Model ID not found for {model_name}. "
                f"Please set {required_env} in your .env file."
            )
        
        # Set compartment ID - use DAC compartment for dedicated cluster
        if is_dedicated:
            self.compartment_id = os.getenv("COMPARTMENT_ID_DAC")
            if not self.compartment_id:
                raise ValueError(
                    "DAC Compartment ID not found. "
                    "Please set COMPARTMENT_ID_DAC in your .env file."
                )
        else:
            self.compartment_id = (compartment_id or 
                                  os.getenv("OCI_COMPARTMENT_ID") or 
                                  os.getenv("COMPARTMENT_ID"))
            
            if not self.compartment_id:
                raise ValueError(
                    "Compartment ID not found. "
                    "Please set OCI_COMPARTMENT_ID in your .env file."
                )
        
        # Set endpoint based on region
        region = self.model_config.get("region", "us-chicago-1")
        self.endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

        # Initialize OCI client
        config = oci.config.from_file("~/.oci/config", config_profile)
        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=self.endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240)
        )
        
        print(f"✅ Initialized OCI handler for {model_name}")
        if is_dedicated:
            print(f"   Using dedicated cluster in {region}")
            print(f"   DAC Compartment ID: {self.compartment_id[:20]}...")

    def _create_generic_request(self, prompt: str, max_tokens: int, **kwargs) -> Any:
        """Create a generic chat request for Grok and Llama models"""
        oci = self.oci
        params = {**self.model_config["default_params"], **kwargs}
        
        content = oci.generative_ai_inference.models.TextContent(text=prompt)
        message = oci.generative_ai_inference.models.Message(role="USER", content=[content])

        request_kwargs = {
            "api_format": oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
            "messages": [message],
            "max_tokens": max_tokens,
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
        }

        if "frequency_penalty" in params:
            request_kwargs["frequency_penalty"] = params.get("frequency_penalty", 0)
        if "presence_penalty" in params:
            request_kwargs["presence_penalty"] = params.get("presence_penalty", 0)
        
        return oci.generative_ai_inference.models.GenericChatRequest( **request_kwargs)

    def _create_cohere_request(self, prompt: str, max_tokens: int, **kwargs) -> Any:
        """Create a Cohere chat request"""
        oci = self.oci
        
        # Merge default params with provided kwargs
        params = {**self.model_config["default_params"], **kwargs}
        
        return oci.generative_ai_inference.models.CohereChatRequest(
            message=prompt,
            max_tokens=max_tokens,
            temperature=params.get("temperature", 1),
            frequency_penalty=params.get("frequency_penalty", 0),
            top_p=params.get("top_p", 0.75),
            top_k=params.get("top_k", 0)
        )

    def __call__(self, prompt: str, max_new_tokens: int = 4000, **kwargs) -> List[Dict[str, str]]:
        """Call the OCI model with the given prompt"""
        try:
            oci = self.oci
            max_tokens = max_new_tokens or 4000

            print(f"🧪 [OCI DEBUG] Using {self.model_name}")
            print(f"🧪 [OCI DEBUG] Prompt length (chars): {len(prompt)}")
            print(f"🧪 [OCI DEBUG] Prompt preview:\n{prompt[:300]}...")

            # Create appropriate request based on model type
            if self.model_config["request_type"] == "cohere":
                chat_request = self._create_cohere_request(prompt, max_tokens, **kwargs)
            else:  # generic
                chat_request = self._create_generic_request(prompt, max_tokens, **kwargs)

            # Create serving mode based on whether it's dedicated or on-demand
            is_dedicated = self.model_config.get("is_dedicated", False)
            if is_dedicated:
                # Use DedicatedServingMode for DAC
                serving_mode = oci.generative_ai_inference.models.DedicatedServingMode(
                    endpoint_id=self.model_config["endpoint_id"]
                )
            else:
                # Use OnDemandServingMode for regular models
                serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
                    model_id=self.model_config["model_id"]
                )

            # Create chat detail
            chat_detail = oci.generative_ai_inference.models.ChatDetails(
                serving_mode=serving_mode,
                chat_request=chat_request,
                compartment_id=self.compartment_id
            )

            # Make the API call
            response = self.client.chat(chat_detail)

            # Extract response text - handle different response structures
            chat_response = response.data.chat_response
            
            if self.model_config["request_type"] == "cohere":
                # Cohere has a different response structure
                if hasattr(chat_response, 'text'):
                    # Direct text attribute
                    text = chat_response.text.strip()
                elif hasattr(chat_response, 'message') and hasattr(chat_response.message, 'content'):
                    # Message with content
                    if isinstance(chat_response.message.content, list):
                        text = "".join(chunk.text for chunk in chat_response.message.content).strip()
                    else:
                        text = str(chat_response.message.content).strip()
                else:
                    print("⚠️ Unexpected Cohere response structure!")
                    print(f"Response attributes: {dir(chat_response)}")
                    return [{"generated_text": ""}]
            else:
                # Generic models (Grok, Llama) use choices structure
                choices = chat_response.choices
                if not choices or not choices[0].message.content:
                    print("⚠️ Empty response from model!")
                    return [{"generated_text": ""}]
                
                # Generic models may return multiple text chunks
                text = "".join(chunk.text for chunk in choices[0].message.content).strip()
            
            if not text:
                print("⚠️ Empty text extracted from response!")
                return [{"generated_text": ""}]

            print(f"🧪 [OCI DEBUG] Model output:\n{text[:100]}...")

            return [{"generated_text": text}]
        
        except Exception as e:
            print(f"⚠️ Error in OCIModelHandler for {self.model_name}: {str(e)}")
            raise

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available model names"""
        return list(cls.MODEL_CONFIGS.keys())

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        is_dedicated = self.model_config.get("is_dedicated", False)
        info = {
            "name": self.model_name,
            "request_type": self.model_config["request_type"],
            "default_params": self.model_config["default_params"],
            "max_output_tokens": self.model_config.get("max_output_tokens", 4000)
        }
        
        if is_dedicated:
            info["endpoint_id"] = self.model_config.get("endpoint_id")
            info["region"] = self.model_config.get("region")
            info["is_dedicated"] = True
        else:
            info["model_id"] = self.model_config.get("model_id")
            
        return info




class RAGSystem:
    def __init__(self, vector_store: EnhancedVectorStore = None, model_name: str = None, 
                 use_cot: bool = False, skip_analysis: bool = False,
                 quantization: str = None, use_oracle_db: bool = True, collection: str = "Multi-Collection",
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
        print('Model Name after assignment:', self.model_name)
        self.collection=collection
        # Support all OCI models
        available_oci_models = OCIModelHandler.get_available_models()
        if model_name in available_oci_models:
            print(f"\nLoading {model_name} model...")
            self.oci_handler = OCIModelHandler(model_name=model_name)
            self.pipeline = self.oci_handler
            # Add model config to pipeline for token limit access
            self.pipeline.model_config = self.oci_handler.model_config
            print(f"Using {model_name} from OCI")
        else:
            print(f"⚠️ Model {model_name} not supported. Available OCI models: {', '.join(available_oci_models)}")
            print("Falling back to grok-3")
            self.oci_handler = OCIModelHandler(model_name="grok-3")
            self.pipeline = self.oci_handler
            # Add model config to pipeline for token limit access
            self.pipeline.model_config = self.oci_handler.model_config
            self.model_name = "grok-3"
        
        # Create LLM wrapper
        self.llm = LocalLLM(self.pipeline)
        logger.info(f"RAGSystem: self.llm assigned = {self.llm}")

        # Initialize tiktoken tokenizer for accurate token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Always start with minimal agents; full agentic setup is handled elsewhere if needed
        self.agents = create_agents(
            self.llm,
            self.vector_store,
            model_name=self.model_name,
            tokenizer=self.tokenizer
        )
        logger.info(f"Agents initialized: {list(self.agents.keys())}")



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
                                                    collection_mode: str = "multi") -> Dict[str, Any]:
        """Process a query with pre-retrieved multi-collection context"""
        logger.info(f"Processing query with {len(multi_collection_context)} multi-collection chunks")
        
        if self.use_cot:
            return self._process_query_with_report_agent(query, multi_collection_context, is_comparison_report, collection_mode=collection_mode)
        else:
            # For non-CoT mode, use the context directly
            return self._generate_response(query, multi_collection_context)
            
    def _process_query_with_report_agent(
        self,
        query: str,
        multi_collection_context: Optional[List[Dict[str, Any]]] = None,
        is_comparison_report: bool = False,
        collection_mode: str = "multi"   
    ) -> Dict[str, Any]:
        """
        Report agent pipeline:
        - Plan sections using PlannerAgent
        - Retrieve chunks using ResearchAgent
        - Write sections using SectionWriterAgent
        - Assemble report with ReportWriterAgent
        """
        logger.info("Starting report generation pipeline")

        planner = self.agents.get("planner")
        researcher = self.agents.get("researcher")
        section_writer = self.agents.get("section_writer")
        report_writer = self.agents.get("report_agent")

        if not planner or not researcher or not section_writer or not report_writer:
            logger.warning("Missing one or more required agents")
            return self._generate_general_response(query)

        # STEP 1: Plan the report
        logger.info("Planning report sections...")
        try:
            result = planner.plan(query, is_comparison_report=is_comparison_report)
            if not isinstance(result, tuple) or len(result) != 3:
                raise ValueError(f"Planner returned unexpected format: {type(result)} → {result}")
            plan, entities, is_comparison = result

            if not isinstance(plan, list):
                logger.error("Planner output is not a list of steps. Got: %s", type(plan))
                logger.debug("Raw planner output: %s", plan)
                return self._generate_general_response(query)

        except Exception as e:
            logger.error(f"Error calling planner.plan: {e}")
            return self._generate_general_response(query)

        logger.info("Sections planned: %s", [p['topic'] for p in plan])

        # PARALLEL SECTION PROCESSING - Major speed improvement!
        def process_section(section_data):
            """Process a single section (research + write) - runs in parallel"""
            section, section_idx = section_data
            topic = section.get("topic", "Untitled Section")
            steps = section.get("steps", [])
            section_chunks = []
            
            logger.info(f"🔄 Processing section {section_idx+1}/{len(plan)}: {topic}")

            if is_comparison:
                if len(steps) != 2:
                    raise ValueError(f"Expected 2 steps per topic for comparison, got {len(steps)}")

                step_a, step_b = steps
                entity_a, entity_b = entities[:2] if len(entities) >= 2 else ("Unknown", "Unknown")

                # Parallel research for both entities
                with ThreadPoolExecutor(max_workers=2) as research_executor:
                    future_a = research_executor.submit(
                        researcher.research, query, step_a, None, True, [entity_a], collection_mode
                    )
                    future_b = research_executor.submit(
                        researcher.research, query, step_b, None, True, [entity_b], collection_mode
                    )
                    
                    chunks_a = future_a.result()
                    chunks_b = future_b.result()

                for chunk in chunks_a:
                    chunk["_search_entity"] = entity_a
                for chunk in chunks_b:
                    chunk["_search_entity"] = entity_b

                section_chunks = chunks_a + chunks_b

            else:
                entity = entities[0] if entities else "Unknown"
                # Parallel research for multiple steps if needed
                if len(steps) > 1:
                    with ThreadPoolExecutor(max_workers=min(4, len(steps))) as research_executor:
                        futures = []
                        for step in steps:
                            future = research_executor.submit(
                                researcher.research, query, step, None, False, [entity], collection_mode
                            )
                            futures.append(future)
                        
                        for future in as_completed(futures):
                            chunks = future.result()
                            for chunk in chunks:
                                chunk["_search_entity"] = entity
                            section_chunks.extend(chunks)
                else:
                    # Single step - no need for parallelization
                    chunks = researcher.research(query, steps[0], is_comparison=False, entities=[entity], collection=collection_mode)
                    for chunk in chunks:
                        chunk["_search_entity"] = entity
                    section_chunks.extend(chunks)

            logger.info(f"🧹 Collected {len(section_chunks)} chunks for topic: {topic}")

            # Write the section
            section_result = section_writer.write_section(topic, section_chunks)
            section_result["entities"] = entities
            section_result["is_comparison"] = is_comparison
            section_result.setdefault("chart_data", {})
            if not isinstance(section_result.get("table"), list):
                section_result["table"] = [section_result.get("table")]

            logger.info(f"✅ Completed section {section_idx+1}: {topic}")
            return section_result, len(section_chunks)

        # Process all sections in parallel - MAJOR SPEED BOOST!
        logger.info(f"🚀 Processing {len(plan)} sections in parallel...")
        all_sections = []
        total_chunks_used = 0
        
        # Use ThreadPoolExecutor to process sections in parallel
        max_workers = min(4, len(plan))  # Limit concurrent sections to avoid overwhelming the LLM
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all section processing tasks
            section_futures = []
            for idx, section in enumerate(plan):
                future = executor.submit(process_section, (section, idx))
                section_futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(section_futures):
                try:
                    section_result, chunk_count = future.result()
                    all_sections.append(section_result)
                    total_chunks_used += chunk_count
                except Exception as e:
                    logger.error(f"❌ Section processing failed: {e}")
                    # Continue with other sections
        
        # Sort sections to maintain original order (since parallel processing may complete out of order)
        # We'll need to track the original index to maintain order
        logger.info(f"📊 Processed {len(all_sections)} sections with {total_chunks_used} total chunks")

        logger.info("📄 Writing report with %d sections", len(all_sections))
        report_path = report_writer.write_report(all_sections, query=query)

        return {
            "answer": f"Report successfully written to {report_path}",
            "report_path": report_path,
            "sections": all_sections,
            "context": [],
            "total_chunks_used": total_chunks_used
        }

    


    def _guess_entity_from_step(self, step: str, known_entities: List[str]) -> str:
        for entity in known_entities:
            if entity.lower() in step.lower():
                return entity
        return "Unknown"

    
    def _generate_text(self, prompt: str, max_length: int = None) -> str:
        """Generate text using the OCI model with model-aware token limits"""
        # Log start time for performance monitoring
        start_time = time.time()
        print("\n🧪 [DEBUG] Prompt being sent to model:\n")
        print(prompt)  # Optional: trim to 1000 chars
        print("\n🧪 [DEBUG] Prompt length:", len(prompt))

        # Use model-specific max tokens if max_length not provided
        if max_length is None:
            max_length = getattr(self.pipeline, 'model_config', {}).get('max_output_tokens', 4000)
        
        # Ensure we don't exceed model limits
        model_max = getattr(self.pipeline, 'model_config', {}).get('max_output_tokens', 4000)
        max_length = min(max_length, model_max)
        
        print(f"🧪 [DEBUG] Using max_tokens: {max_length} (model limit: {model_max})")

        # Only OCI models are supported in this cleaned version
        result = self.pipeline(prompt, max_new_tokens=max_length)[0]["generated_text"]
        
        # Log completion time
        elapsed_time = time.time() - start_time
        logger.info(f"Text generation completed in {elapsed_time:.2f} seconds")
        
        return result.strip()
    
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
    parser.add_argument("--model", default="qwen2", help="Model to use (default: qwen2)")
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
