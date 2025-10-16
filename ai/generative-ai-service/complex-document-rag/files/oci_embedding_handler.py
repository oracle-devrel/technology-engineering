#!/usr/bin/env python3
"""
OCI Native Embedding Handler
Supports Cohere and other OCI embedding models with proper error handling and fallbacks
"""

import os
import oci
import numpy as np
from typing import List, Dict, Any, Optional, Union
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class OCIEmbeddingHandler:
    """Handler for OCI native embedding models with multi-model support"""
    LOCAL_MODELS = {
        "chromadb-default": {
            "name": "chromadb-default",
            "description": "ChromaDB default embedding (BAAI/bge-small-en-v1.5)",
            "dimensions": 384,
            "type": "local"
        }
       }
    # Available OCI embedding models
    EMBEDDING_MODELS = {        
        "cohere-embed-v4.0": {
            "model_id": "cohere.embed-v4.0",
            "endpoint": "us-chicago-1",  # 
            "input_type": None,  # Not needed for Cohere
            "max_tokens": 512,
            "dimensions": 1024,
            "description": "Cohere English embedding v4.0 - Frankfurt region, optimized for semantic search"
        },
        "cohere-embed-english-v3.0": {
            "model_id": "cohere.embed-english-v3.0",
            "endpoint": "eu-frankfurt-1",  # Cohere v3.0 is in Frankfurt
            "input_type": None,  # Not needed for Cohere
            "max_tokens": 512,
            "dimensions": 1024,
            "description": "Cohere English embedding v3.0 - Frankfurt region, optimized for semantic search"
        },
        "cohere-embed-english-light-v2.0": {
            "model_id": "cohere.embed-english-light-v2.0",
            "endpoint": "us-chicago-1",  # Light v2.0 is in Chicago
            "input_type": None,  # Not needed for Cohere
            "max_tokens": 512,
            "dimensions": 1024,
            "description": "Cohere English light v2.0 - Chicago region, optimized for semantic search"
        },
        "cohere-embed-multilingual-v3.0": {
            "model_id": "cohere.embed-multilingual-v3.0",
            "endpoint": "us-chicago-1",  # Multilingual v3.0 in Chicago
            "input_type": None,  # Not needed for Cohere
            "max_tokens": 512,
            "dimensions": 1024,
            "description": "Cohere multilingual embedding model v3.0 - Chicago region, supports 100+ languages"
        },
        "openai-text-embedding-3-large": {
            "model_id": "openai.text-embedding-3-large",
            "endpoint": "us-chicago-1",
            "input_type": None,
            "max_tokens": 8192,
            "dimensions": 3072,
            "description": "OpenAI text-embedding-3-large - Chicago region (coming soon)"
        },
        "openai-text-embedding-3-small": {
            "model_id": "openai.text-embedding-3-small",
            "endpoint": "us-chicago-1", 
            "input_type": None,
            "max_tokens": 8192,
            "dimensions": 1536,
            "description": "OpenAI text-embedding-3-small - Chicago region (coming soon)"
        }
    }
    
    def __init__(self, 
                 model_name: str = "cohere-embed-english-v3.0",
                 config_profile: str = "DEFAULT",
                 compartment_id: Optional[str] = None):
        """Initialize OCI embedding handler
        
        Args:
            model_name: Name of the embedding model to use
            config_profile: OCI config profile to use
            compartment_id: OCI compartment ID
        """
        self.model_name = model_name
        
        # Validate model name
        if model_name not in self.EMBEDDING_MODELS:
            available_models = ", ".join(self.EMBEDDING_MODELS.keys())
            raise ValueError(f"Unsupported embedding model: {model_name}. Available: {available_models}")
        
        self.model_config = self.EMBEDDING_MODELS[model_name]
        
        # Set compartment ID - check both OCI_COMPARTMENT_ID and COMPARTMENT_ID for compatibility
        self.compartment_id = compartment_id or os.getenv("OCI_COMPARTMENT_ID") or os.getenv("COMPARTMENT_ID")
        
       # Set endpoint region based on model configuration (supports multiple OCI regions)
        endpoint_region = self.model_config.get("endpoint", "us-chicago-1")
        self.endpoint = f"https://inference.generativeai.{endpoint_region}.oci.oraclecloud.com"
        
        # Initialize OCI client
        try:
            config = oci.config.from_file("~/.oci/config", config_profile)
            self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=config,
                service_endpoint=self.endpoint,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240)
            )
            logger.info(f"✅ Initialized OCI embedding handler for {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCI client: {e}")
            raise


  
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            List of embedding vectors
        """
        return self._embed_texts(texts, input_type="search_document")
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self._embed_texts([text], input_type="search_query")
        return embeddings[0] if embeddings else []
    
    def _embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Internal method to embed texts using OCI API
        
        Args:
            texts: List of texts to embed
            input_type: Type of input ("search_document" or "search_query")
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Batch processing for efficiency
            batch_size = 96  # OCI limit for Cohere embeddings
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self._process_batch(batch, input_type)
                all_embeddings.extend(batch_embeddings)
                
                # Add small delay between batches to avoid rate limiting
                if i + batch_size < len(texts):
                    time.sleep(0.1)
            
            logger.info(f"✅ Successfully embedded {len(texts)} texts using {self.model_name}")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"❌ Error embedding texts: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "model_id": self.model_config["model_id"],
            "dimensions": self.model_config["dimensions"],
            "max_tokens": self.model_config["max_tokens"],
            "description": self.model_config["description"]
        }
    
    def _process_batch(self, texts: List[str], input_type: str) -> List[List[float]]:
        """Process a batch of texts for embedding
        
        Args:
            texts: Batch of texts to embed
            input_type: Type of input
            
        Returns:
            List of embedding vectors for the batch
        """
        try:
            # Truncate texts if they exceed max tokens
            max_chars = self.model_config["max_tokens"] * 4  # Rough estimate: 4 chars per token
            truncated_texts = [text[:max_chars] if len(text) > max_chars else text for text in texts]
            
            # Create embedding request using the working pattern from your example
            embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
            embed_text_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=self.model_config["model_id"]
            )
            embed_text_detail.inputs = truncated_texts
            embed_text_detail.truncate = "NONE"
            embed_text_detail.compartment_id = self.compartment_id
            
            # Don't add input_type - it was causing the validation errors
            
            # Make API call
            start_time = time.time()
            response = self.client.embed_text(embed_text_detail)
            elapsed_time = time.time() - start_time
            
            logger.debug(f"🔄 Embedded batch of {len(texts)} texts in {elapsed_time:.2f}s")
            
            # Extract embeddings from response
            embeddings = []
            try:
                if response and hasattr(response, 'data') and response.data:
                    if hasattr(response.data, 'embeddings') and response.data.embeddings:
                        for embedding_data in response.data.embeddings:
                            # The embedding_data is actually the embedding vector itself (a list of floats)
                            if isinstance(embedding_data, list) and len(embedding_data) > 0:
                                embeddings.append(embedding_data)
                            else:
                                logger.warning(f"⚠️ Unexpected embedding data format: {type(embedding_data)}")
                    else:
                        logger.warning(f"⚠️ No embeddings found in response data")
                else:
                    logger.warning(f"⚠️ No valid response data")
            except AttributeError as e:
                logger.error(f"❌ Error extracting embeddings from response: {e}")
                raise
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error processing batch: {e}")
            raise
    def test_input_types(self, text: str = "Example input text"):
        """Test embedding with different input types"""
        input_types = ["SEARCH_QUERY", "SEARCH_DOCUMENT", "CLUSTERING", "CLASSIFICATION"]
        
        results = {}
        
        for input_type in input_types:
            try:
                print(f"\n🔎 Testing input_type: {input_type}")
                embeddings = self._embed_texts([text], input_type=input_type)
                print(f"✅ {input_type}: Returned {len(embeddings[0])} dimensions")
                results[input_type] = embeddings[0][:5]  # Show just first 5 values
            except Exception as e:
                print(f"❌ {input_type} failed: {e}")
                results[input_type] = None
        return results

    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available embedding model names"""
        return list(cls.EMBEDDING_MODELS.keys())
    
    def test_connection(self) -> bool:
        """Test the connection to OCI embedding service
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple embedding
            test_embedding = self.embed_query("test connection")
            logger.info(f"🔍 Test embedding result: {type(test_embedding)}, length: {len(test_embedding) if test_embedding else 0}")
            
            if test_embedding and len(test_embedding) > 0:
                # Update dimensions if they're different from expected
                actual_dims = len(test_embedding)
                expected_dims = self.model_config["dimensions"]
                if actual_dims != expected_dims:
                    logger.info(f"📏 Updating dimensions for {self.model_name}: {expected_dims} → {actual_dims}")
                    self.model_config["dimensions"] = actual_dims
                return True
            else:
                logger.warning(f"⚠️ Test embedding returned empty or None result")
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

class EmbeddingModelManager:
    """Manager for multiple embedding models with fallback support"""
    
    def __init__(self):
        self.models = {}
        self.default_model = None
        
        # Try to initialize OCI models, but skip OpenAI models gracefully
        for model_name in OCIEmbeddingHandler.get_available_models():
            try:
                # Skip OpenAI models for now (coming soon)
                if "openai" in model_name.lower():
                    logger.info(f"⏳ Skipping {model_name} - coming soon to Chicago region")
                    continue
                    
                handler = OCIEmbeddingHandler(model_name)
                if handler.test_connection():
                    self.models[model_name] = handler
                    if self.default_model is None:
                        self.default_model = model_name
                    logger.info(f"✅ Registered embedding model: {model_name}")
                else:
                    logger.warning(f"⚠️ Connection test failed for: {model_name}")
            except Exception as e:
                # Check if it's a 404 error (model not found)
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.info(f"⏳ Model {model_name} not available yet in region")
                else:
                    logger.warning(f"⚠️ Failed to initialize {model_name}: {e}")
        
        # Add ChromaDB default as fallback
        self.models["chromadb-default"] = "chromadb-default"  # Placeholder
        if self.default_model is None:
            self.default_model = "chromadb-default"
    
    def get_model(self, model_name: Optional[str] = None) -> Union[OCIEmbeddingHandler, str]:
        """Get an embedding model handler
        
        Args:
            model_name: Name of the model to get (if None, returns default)
            
        Returns:
            Embedding model handler or "chromadb-default" for ChromaDB
        """
        if model_name is None:
            model_name = self.default_model or "chromadb-default"
        
        return self.models.get(model_name, self.models.get(self.default_model or "chromadb-default", "chromadb-default"))
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available embedding models with their info
        
        Returns:
            List of model information dictionaries
        """
        models_info = []
        
        for model_name, handler in self.models.items():
            if model_name == "chromadb-default":
                models_info.append({
                    "name": "chromadb-default",
                    "description": "ChromaDB default embedding (BAAI/bge-small-en-v1.5)",
                    "dimensions": 384,
                    "type": "local"
                })
            else:
                info = handler.get_model_info()
                info["type"] = "oci"
                models_info.append(info)
        
        return models_info
    
    def get_default_model(self) -> str:
        """Get the name of the default embedding model"""
        return self.default_model or "chromadb-default"
    
    def is_oci_model(self, model_name: str) -> bool:
        """Check if a model is an OCI model"""
        return model_name in self.models and model_name != "chromadb-default"
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific embedding model"""
        if model_name == "chromadb-default":
            return {
                "name": "chromadb-default",
                "description": "ChromaDB default embedding (BAAI/bge-small-en-v1.5)",
                "dimensions": 384,
                "type": "local"
            }
        elif model_name in self.models and isinstance(self.models[model_name], OCIEmbeddingHandler):
            info = self.models[model_name].get_model_info()
            info["type"] = "oci"
            return info
        else:
            return {
                "name": model_name,
                "description": "Unknown model",
                "dimensions": 0,
                "type": "unknown"
            }

def main():
    """Test the OCI embedding handler"""
    load_dotenv()
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OCI embedding models")
    parser.add_argument("--model", default="cohere-embed-english-v3.0", 
                       help="Embedding model to test")
    parser.add_argument("--text", default="This is a test document for embedding",
                       help="Text to embed")
    parser.add_argument("--list-models", action="store_true",
                       help="List available models")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    if args.list_models:
        print("Available OCI embedding models:")
        for model_name, config in OCIEmbeddingHandler.EMBEDDING_MODELS.items():
            print(f"  {model_name}: {config['description']}")
        return
    
    try:
        # Initialize handler
        print(f"Initializing {args.model}...")
        handler = OCIEmbeddingHandler(args.model)
        
        # Test connection
        print("Testing connection...")
        if handler.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
        
        # Test embedding
        print(f"Embedding text: '{args.text}'")
        embedding = handler.embed_query(args.text)
        
        print(f"✅ Embedding generated!")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
        # Test batch embedding
        test_docs = [
            "This is the first document",
            "This is the second document",
            "This is the third document"
        ]
        # Test different input types
        print("\n🧪 Testing different input types for embedding:")
        results = handler.test_input_types(args.text)

        print("\n📊 Summary of input type results:")
        for input_type, preview in results.items():
            if preview:
                print(f"  ✅ {input_type}: {preview}")
            else:
                print(f"  ❌ {input_type}: Failed")
        print(f"\nTesting batch embedding with {len(test_docs)} documents...")
        doc_embeddings = handler.embed_documents(test_docs)
        
        print(f"✅ Batch embedding successful!")
        print(f"   Generated {len(doc_embeddings)} embeddings")
        print(f"   Each with {len(doc_embeddings[0])} dimensions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
