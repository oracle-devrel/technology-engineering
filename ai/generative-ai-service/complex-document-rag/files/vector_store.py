#!/usr/bin/env python3
"""
Enhanced Vector Store with Multi-Embedding Model Support
Extends the existing VectorStore to support OCI Cohere embeddings alongside ChromaDB defaults
"""
from oci_embedding_handler import OCIEmbeddingHandler, EmbeddingModelManager
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.api.types import Metadata

import time
# Moved from store.py - entity detection functionality

import logging
logger = logging.getLogger(__name__)


class VectorStore:
    """Base vector store class with ChromaDB backend"""
    
    def __init__(self, *args, **kwargs):
        if type(self) is VectorStore:
            raise RuntimeError(
                "VectorStore is an abstract base class. Use EnhancedVectorStore instead."
            )
       


class EnhancedVectorStore(VectorStore):
    """Enhanced vector store with multi-embedding model support (SAFER VERSION)"""

    def __init__(self, persist_directory: str = "embeddings", embedding_model: str = "cohere-embed-multilingual-v3.0", embedder=None):
        self.embedding_manager = EmbeddingModelManager()
        self.embedding_model_name = embedding_model  # string (name)
        self.embedder = embedder                     # object (has .embed_query/.embed_documents)
        self.embedding_dimensions = getattr(embedder, "model_config", {}).get("dimensions", None) if embedder else None
        
        # If embedder is provided, use it; otherwise fall back to embedding manager
        if embedder:
            self.embedding_model = embedder
        else:
            self.embedding_model = self.embedding_manager.get_model(embedding_model)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(allow_reset=True)
        )

        # Always get dimensions from the embedding manager or embedder
        embedding_dim = None
        if embedder:
            # Use the provided embedder's dimensions
            info = embedder.get_model_info()
            if info and "dimensions" in info:
                embedding_dim = info["dimensions"]
            else:
                raise ValueError(
                    f"Cannot determine embedding dimensions from provided embedder."
                )
        elif isinstance(self.embedding_model, str):
            # Try to get from embedding_manager
            embedding_info = self.embedding_manager.get_model_info(self.embedding_model_name)
            if embedding_info and "dimensions" in embedding_info:
                embedding_dim = embedding_info["dimensions"]
            else:
                raise ValueError(
                    f"Unknown embedding dimension for model '{self.embedding_model_name}'."
                    " Please update your EmbeddingModelManager to include this info."
                )
        else:
            # Should have a get_model_info() method
            info = self.embedding_model.get_model_info()
            if info and "dimensions" in info:
                embedding_dim = info["dimensions"]
            else:
                raise ValueError(
                    f"Cannot determine embedding dimensions for non-string embedding model {self.embedding_model}."
                )

        metadata = {
            "hnsw:space": "cosine",
            "embedding_model": self.embedding_model_name,
            "embedding_dimensions": embedding_dim
        }

        base_collection_names = [
            "pdf_documents", "xlsx_documents"
        ]

        self.collections = {}

        for base_name in base_collection_names:
            full_name = f"{base_name}_{self.embedding_model_name}_{embedding_dim}"

            try:
                # Check for exact match first
                existing_collections = self.client.list_collections()
                by_name = {c.name: c for c in existing_collections}
                if full_name in by_name:
                    coll = by_name[full_name]
                    actual_dim = coll.metadata.get("embedding_dimensions", None)
                    if actual_dim != embedding_dim:
                        # This should never happen unless DB is corrupt
                        logger.error(
                            f"❌ Dimension mismatch for collection '{full_name}'. Expected {embedding_dim}, found {actual_dim}."
                        )
                        raise ValueError(
                            f"Collection '{full_name}' has dim {actual_dim}, but expected {embedding_dim}."
                        )
                    collection = coll
                    logger.info(f"🎯 Using existing collection '{full_name}' ({embedding_dim}D, {coll.count()} chunks)")
                else:
                    # Safe: only ever create the *fully qualified* name
                    collection = self.client.get_or_create_collection(
                        name=full_name,
                        metadata=metadata
                    )
                    logger.info(f"🗂️  Created new collection '{full_name}' with dimension {embedding_dim}")

                self.collections[full_name] = collection

                # For direct access: always the selected model/dim
                if base_name == "pdf_documents":
                    self.pdf_collection = collection
                elif base_name == "xlsx_documents":
                    self.xlsx_collection = collection

            except Exception as e:
                logger.error(f"❌ Failed to create or get collection '{full_name}': {e}")
                raise

        # Only include full names in the map; never ambiguous short names
        self.collection_map = self.collections

        logger.info(f"✅ Enhanced vector store initialized with {embedding_model} ({embedding_dim}D)")


    def get_collection_key(self, base_name: str) -> str:
        # Build the correct key for a base collection name
        embedding_dim = (
            self.get_embedding_info()["dimensions"]
            if hasattr(self, "get_embedding_info")
            else 1024
    )
        return f"{base_name}_{self.embedding_model_name}_{embedding_dim}"


    def _find_collection_variants(self, base_name: str):
        """
        Yield (name, collection) for all collections in the DB that start with base_name + "_",
        across ANY embedding model/dimension (not just the ones cached at init).
        """
        for c in self.client.list_collections():
            try:
                name = c.name
            except Exception:
                # Some clients return plain dicts
                name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
            if not name:
                continue
            if name.startswith(base_name + "_"):
                # get_or_create is fine; if it exists it just returns it
                yield name, self.client.get_or_create_collection(name=name)

    def list_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        List unique documents with chunk counts.
        If a base prefix (e.g., 'xlsx_documents' or 'pdf_documents') is provided, aggregate across
        ALL matching collections (any embedding model/dimension) discovered from the client.
        If a fully-qualified name is provided, operate on that single collection.
        """

        def _collect_from_collection(coll) -> List[Dict[str, Any]]:
            # IMPORTANT: do not include "ids" in include
            results = coll.get(ids=None, where=None, include=["metadatas"])
            ids = results.get("ids") or []           # ids come back regardless of include
            metadatas = results.get("metadatas") or []

            # Fallback if some client variant omits ids unless include is None
            if not ids and metadatas:
                results = coll.get(ids=None, where=None)  # default return usually includes ids+metadatas
                ids = results.get("ids") or []
                metadatas = results.get("metadatas") or []

            by_id: Dict[str, Dict[str, Any]] = {}
            for meta, chunk_id in zip(metadatas, ids):
                meta = meta or {}
                doc_id = (
                    meta.get("document_id")
                    or meta.get("source_id")
                    or "_".join((chunk_id or "").split("_")[:-1])
                )
                if not doc_id:
                    continue
                entry = by_id.setdefault(doc_id, {"document_id": doc_id, "chunk_count": 0})
                entry["chunk_count"] += 1
                for k, v in meta.items():
                    entry.setdefault(k, v)
            return list(by_id.values())

        # If it's an exact, fully-qualified collection we already know, use it
        if collection_name in self.collection_map:
            docs = _collect_from_collection(self.collection_map[collection_name])
            return sorted(docs, key=lambda d: d.get("filename") or d["document_id"])

        # Otherwise treat it as a base prefix and discover all variants in the DB
        aggregated: Dict[str, Dict[str, Any]] = {}
        any_found = False
        for name, coll in self._find_collection_variants(collection_name):
            any_found = True
            docs = _collect_from_collection(coll)
            for d in docs:
                did = d["document_id"]
                if did not in aggregated:
                    aggregated[did] = d
                else:
                    aggregated[did]["chunk_count"] += d.get("chunk_count", 0)
                    for k, v in d.items():
                        if k not in ("document_id", "chunk_count"):
                            aggregated[did].setdefault(k, v)

        if not any_found:
            # As a last resort, try the current model/dimension fully-qualified key
            fq = self.get_collection_key(collection_name)
            coll = self.collection_map.get(fq)
            if not coll:
                raise ValueError(f"Unknown collection name: {collection_name}")
            for d in _collect_from_collection(coll):
                aggregated[d["document_id"]] = d

        docs_sorted = sorted(aggregated.values(), key=lambda d: d.get("filename") or d["document_id"])
        return docs_sorted


    def list_document_ids(self, collection_name: str) -> List[str]:
        """
        List unique document IDs.
        Base names ("xlsx_documents"/"pdf_documents") aggregate across all variants.
        Fully-qualified names operate on a single collection.
        """
        def _ids_from_collection(coll) -> List[str]:
            results = coll.get(ids=None, where={}, where_document={}, include=['metadatas'])
            out = set()
            for meta in results.get("metadatas") or []:
                if not meta:
                    continue
                if "document_id" in meta:
                    out.add(meta["document_id"])
                elif "source_id" in meta:
                    out.add(meta["source_id"])
            return list(out)

        base_names = {"xlsx_documents", "pdf_documents"}
        ids: set[str] = set()

        if collection_name in base_names:
            any_found = False
            for _, coll in self._find_collection_variants(collection_name):
                any_found = True
                ids.update(_ids_from_collection(coll))
            if not any_found:
                fq = self.get_collection_key(collection_name)
                coll = self.collection_map.get(fq)
                if not coll:
                    raise ValueError(f"Unknown collection name: {collection_name}")
                ids.update(_ids_from_collection(coll))
            return sorted(ids)

        if collection_name not in self.collection_map:
            raise ValueError(f"Unknown collection name: {collection_name}")

        return sorted(_ids_from_collection(self.collection_map[collection_name]))



    def _embed_query(self, query: str) -> Optional[List[float]]:
        """Embed a query using the selected embedding model"""
        if isinstance(self.embedding_model, str):
            # ChromaDB default - let ChromaDB handle it
            return None
        else:
            # Use OCI embedding
            try:
                return self.embedding_model.embed_query(query)
            except Exception as e:
                logger.error(f"❌ OCI embedding failed: {e}")
                return None
    
    def _embed_documents(self, documents: List[str]) -> Optional[List[List[float]]]:
        """Embed documents using the selected embedding model"""
        if isinstance(self.embedding_model, str):
            # ChromaDB default - let ChromaDB handle it
            return None
        else:
            # Use OCI embedding
            try:
                return self.embedding_model.embed_documents(documents)
            except Exception as e:
                logger.error(f"❌ OCI embedding failed: {e}")
                return None
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model"""
        if isinstance(self.embedding_model, str):
            return {
                "name": "chromadb-default",
                "description": "ChromaDB default embedding (BAAI/bge-small-en-v1.5)",
                "dimensions": 384,
                "type": "local"
            }
        else:
            info = self.embedding_model.get_model_info()
            info["type"] = "oci"
            return info
    
    def query_with_details(self, collection_name: str, query: str, n_results: int = 3, 
                          entity: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Query collection and return results with detailed retrieval information
        
        Args:
            collection_name: Name of collection to query
            query: Query text
            n_results: Number of results to return
            entity: entity filter (optional)
            
        Returns:
            Tuple of (results, retrieval_details)
        """
        start_time = time.time()
        
        # Map collection names
        collection_mapping = {
            "PDF Collection": "pdf_documents",
            "XLSX Collection": "xlsx_documents", 
        }
        
        actual_collection = collection_mapping.get(collection_name, collection_name)
        
        # Build filter
        filter_kw = None
        if entity:
            filter_kw = {"entity": entity.lower()}
        
        # Perform query based on collection type
        if actual_collection == "pdf_documents":
            results = self.query_pdf_collection(query, n_results, entity)
        elif actual_collection == "xlsx_documents":
            results = self.query_xlsx_collection(query, n_results, entity)
        else:
            results = []
        
        # Calculate retrieval details
        elapsed_time = time.time() - start_time
        retrieval_details = {
            "collection": actual_collection,
            "query": query,
            "embedding_model": self.embedding_model_name,
            "num_results": len(results),
            "retrieval_time": elapsed_time,
            "entity_filter": entity,
            "embedding_info": self.get_embedding_info()
        }
        
        return results, retrieval_details
    
    def compare_embeddings(self, query: str, collection_name: str = "xlsx_documents", 
                          n_results: int = 3) -> Dict[str, Any]:
        """Compare results from different embedding models
        
        Args:
            query: Query text
            collection_name: Collection to query
            n_results: Number of results per model
            
        Returns:
            Comparison results from different embedding models
        """
        comparison_results = {}
        available_models = self.embedding_manager.list_available_models()
        
        for model_info in available_models:
            model_name = model_info["name"]
            try:
                # Create temporary enhanced store with different embedding model
                # Use default persist directory since _settings may not be available
                temp_store = EnhancedVectorStore(
                    persist_directory="embeddings",
                    embedding_model=model_name
                )
                
                # Query with this model
                results, details = temp_store.query_with_details(
                    collection_name, query, n_results
                )
                
                comparison_results[model_name] = {
                    "results": results,
                    "details": details,
                    "model_info": model_info
                }
                
            except Exception as e:
                logger.warning(f"Failed to query with {model_name}: {e}")
                comparison_results[model_name] = {
                    "error": str(e),
                    "model_info": model_info
                }
        
        return comparison_results
    
    def get_chunk_details(self, chunk_id: str, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific chunk
        
        Args:
            chunk_id: ID of the chunk
            collection_name: Collection containing the chunk
            
        Returns:
            Detailed chunk information
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return {"error": f"Collection {collection_name} not found"}
            
            # Get chunk data
            result = collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not result["ids"]:
                return {"error": f"Chunk {chunk_id} not found"}
            
            chunk_details = {
                "id": chunk_id,
                "content": result["documents"][0] if result["documents"] else "",
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
                "embedding_dimensions": len(result["embeddings"][0]) if result["embeddings"] and result["embeddings"][0] else 0,
                "collection": collection_name,
                "embedding_model": self.embedding_model_name
            }
            
            return chunk_details
            
        except Exception as e:
            logger.error(f"Error getting chunk details: {e}")
            return {"error": str(e)}
    
    def list_available_embedding_models(self) -> List[Dict[str, Any]]:
        """List all available embedding models"""
        return self.embedding_manager.list_available_models()
    
    def debug_collections(self):
        """Print all Chroma collections with their stored embedding dims & model."""
        try:
            print("——— VECTOR STORE AUDIT ———")
            for c in self.client.list_collections():
                try:
                    name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
                    if not name:
                        continue
                    coll = self.client.get_or_create_collection(name=name)
                    md = coll.metadata or {}
                    dims = md.get("embedding_dimensions")
                    model = md.get("embedding_model")
                    cnt = 0
                    try:
                        cnt = coll.count()
                    except Exception:
                        pass
                    print(f"• {name} | dim={dims} | model={model} | count={cnt}")
                except Exception as e:
                    print(f"  (skip) {c}: {e}")
            print("———————————————")
        except Exception as e:
            print(f"debug_collections error: {e}")



    
    def _add_cite(self, meta: Union[Dict[str, Any], "Metadata"]) -> Dict[str, Any]:
        """
        Add a [source:location] citation string to metadata.
        For PDFs: [filename:page], for Excel: [filename:sheet].
        """
        meta = dict(meta) if meta else {}

        if "cite" in meta:
            return meta

        # Identify source file, fallback to "unknown"
        src = (
            meta.get("filename")
            or meta.get("source")
            or meta.get("document_id")
            or meta.get("source_id")
            or "unknown"
        )
        try:
            src = Path(str(src)).stem
        except Exception:
            src = str(src)

        # Default location to '0' (page) or 'unknown' (sheet)
        location = "0"

        # Prefer Excel sheet name if present, otherwise PDF page
        if "sheet" in meta and meta["sheet"]:
            location = str(meta["sheet"])
        elif "sheet_name" in meta and meta["sheet_name"]:
            location = str(meta["sheet_name"])
        elif "page" in meta and meta["page"] is not None:
            location = str(meta["page"])
        elif meta.get("page_numbers"):
            page_numbers = meta["page_numbers"]
            if isinstance(page_numbers, list) and page_numbers:
                location = str(page_numbers[0])

        meta["cite"] = f"[{src}:{location}]"
        return meta

    
    def add_xlsx_chunks(self, chunks: List[Dict[str, Any]], document_id: str):
        """Add XLSX chunks to the vector store with proper embedding handling"""
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [chunk["id"] for chunk in chunks]
        
        # Check collection metadata to see what dimensions are expected
        collection_metadata = self.xlsx_collection.metadata or {}
        expected_dimensions = collection_metadata.get('embedding_dimensions')
        expected_model = collection_metadata.get('embedding_model')
        
        # Handle embeddings based on model type
        if isinstance(self.embedding_model, str):
            # ChromaDB default - let ChromaDB handle embeddings
            if expected_dimensions and expected_dimensions != 384:
                logger.error(f"❌ Collection expects {expected_dimensions}D but using ChromaDB default (384D)")
                raise ValueError(f"Dimension mismatch: collection expects {expected_dimensions}D, ChromaDB default is 384D")
            
            self.xlsx_collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        else:
            # Use OCI embeddings
            try:
                embeddings = self.embedding_model.embed_documents(texts)
                actual_dimensions = len(embeddings[0]) if embeddings and embeddings[0] else 0
                
                if expected_dimensions and actual_dimensions != expected_dimensions:
                    # Try to find or create the correct collection
                    correct_collection_name = f"xlsx_documents_{self.embedding_model_name}_{actual_dimensions}"
                    logger.warning(f"⚠️ Dimension mismatch: collection '{self.xlsx_collection.name}' expects {expected_dimensions}D, embedder produces {actual_dimensions}D")
                    logger.info(f"🔍 Looking for correct collection: {correct_collection_name}")
                    
                    try:
                        # Try to get the correct collection
                        correct_collection = self.client.get_collection(correct_collection_name)
                        logger.info(f"✅ Found correct collection: {correct_collection_name}")
                    except:
                        # Create new collection with correct dimensions
                        metadata = {
                            "hnsw:space": "cosine",
                            "embedding_model": self.embedding_model_name,
                            "embedding_dimensions": actual_dimensions
                        }
                        correct_collection = self.client.create_collection(
                            name=correct_collection_name,
                            metadata=metadata
                        )
                        logger.info(f"✅ Created new collection: {correct_collection_name}")
                    
                    # Add to the correct collection
                    correct_collection.add(
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids,
                        embeddings=embeddings
                    )
                    
                    # Update the reference for future use
                    self.xlsx_collection = correct_collection
                    self.collections[correct_collection_name] = correct_collection
                    
                    logger.info(f"✅ Added {len(chunks)} XLSX chunks to {correct_collection_name}")
                else:
                    # Dimensions match, proceed normally
                    self.xlsx_collection.add(
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids,
                        embeddings=embeddings
                    )
                    logger.info(f"✅ Added {len(chunks)} XLSX chunks to {self.embedding_model_name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to add chunks with OCI embeddings: {e}")
                raise  # Don't silently fall back - this causes dimension mismatches

    def add_pdf_chunks(self, chunks: List[Dict[str, Any]], document_id: str):
        """Add PDF chunks to the vector store with proper embedding handling"""
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [chunk["id"] for chunk in chunks]
        
        # Check collection metadata to see what dimensions are expected
        collection_metadata = self.pdf_collection.metadata or {}
        expected_dimensions = collection_metadata.get('embedding_dimensions')
        expected_model = collection_metadata.get('embedding_model')
        
        # Handle embeddings based on model type and expected dimensions
        if isinstance(self.embedding_model, str):
            # String identifier - check if it matches expected model
            if expected_model and self.embedding_model_name != expected_model:
                logger.warning(f"⚠️ Model mismatch: collection expects '{expected_model}', got '{self.embedding_model_name}'")
            
            if expected_dimensions == 384 or self.embedding_model_name == "chromadb-default":
                # ChromaDB default - let ChromaDB handle embeddings
                logger.info(f"📝 Using ChromaDB default embeddings ({expected_dimensions or 384}D)")
                self.pdf_collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # Expected OCI model but got string - this is a configuration error
                logger.error(f"❌ Configuration error: Expected {expected_model} ({expected_dimensions}D) but OCI embedding handler failed to initialize")
                logger.error(f"💡 Falling back to ChromaDB default, but this will cause dimension mismatch!")
                raise ValueError(f"Cannot add {expected_dimensions}D embeddings using ChromaDB default (384D). Please fix OCI configuration or recreate collection with chromadb-default.")
        else:
            # Use OCI embeddings
            try:
                embeddings = self.embedding_model.embed_documents(texts)
                actual_dimensions = len(embeddings[0]) if embeddings and embeddings[0] else 0
                
                if expected_dimensions and actual_dimensions != expected_dimensions:
                    logger.error(f"❌ Dimension mismatch: collection expects {expected_dimensions}D, embedder produces {actual_dimensions}D")
                    raise ValueError(f"Dimension mismatch: collection expects {expected_dimensions}D, got {actual_dimensions}D")
                
                logger.info(f"📝 Using OCI embeddings ({actual_dimensions}D)")
                self.pdf_collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            except Exception as e:
                logger.error(f"❌ Failed to add PDF chunks with OCI embeddings: {e}")
                raise  # Don't fall back silently - this causes dimension mismatches
        
        logger.info(f"✅ Added {len(chunks)} PDF chunks to {self.embedding_model_name}")
    


    def query_xlsx_collection(self, query: str, n_results: int = 3, entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query XLSX chunks. Uses the current XLSX collection if it has data,
        otherwise auto-selects the largest populated XLSX collection across ANY
        embedding model, and embeds the query with that collection's model.
        """
        try:
            ent = entity.strip().lower() if isinstance(entity, str) and entity.strip() else None

            # 1) Choose target XLSX collection (current → largest populated fallback)
            target = getattr(self, "xlsx_collection", None)
            if not target or target.count() == 0:
                best = None
                for cinfo in self.client.list_collections():
                    name = getattr(cinfo, "name", "")
                    if not name.startswith("xlsx_documents_"):
                        continue
                    try:
                        c = self.client.get_collection(name)
                        cnt = c.count()
                        if cnt > 0 and (best is None or cnt > best[1]):
                            best = (c, cnt)
                    except Exception:
                        continue
                if best:
                    target = best[0]
                    # cache so future calls don’t rescan
                    self.xlsx_collection = target
                else:
                    # nothing to search
                    return []

            # 2) Get the embedding model actually used by this collection
            meta = target.metadata or {}
            stored_model = meta.get("embedding_model", self.embedding_model_name)

            # 3) Build filter (server-side)
            where_filter = {"entity": ent} if ent else None

            # 4) Get a handler that matches the collection’s model
            if isinstance(self.embedding_model, str):
                # current is 'chromadb-default' (no external handler)
                use_handler = self.embedding_manager.get_model(stored_model)
            else:
                # current is an OCI handler; reuse if model matches, else fetch a new one
                use_handler = self.embedding_model if self.embedding_model_name == stored_model else self.embedding_manager.get_model(stored_model)

            # 5) Query (prefer vector query with matching model; fallback to text query)
            overfetch = max(n_results * 4, n_results)
            try:
                if isinstance(use_handler, str) and use_handler == "chromadb-default":
                    # text query (only works if Chroma has an embedder bound; still useful as a fallback)
                    raw = target.query(
                        query_texts=[query],
                        n_results=overfetch,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"]
                    )
                else:
                    q_emb = use_handler.embed_query(query)
                    raw = target.query(
                        query_embeddings=[q_emb],
                        n_results=overfetch,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"]
                    )
            except Exception as e:
                # last-ditch fallback to text query
                logger.warning(f"XLSX vector query failed (model='{stored_model}'), falling back to text: {e}")
                raw = target.query(
                    query_texts=[query],
                    n_results=overfetch,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )

            # 6) Normalize and defensive filter by entity
            docs = (raw.get("documents") or [[]])[0]
            metas = (raw.get("metadatas") or [[]])[0]
            dists = (raw.get("distances") or [[]])[0]

            out: List[Dict[str, Any]] = []
            for doc, m, dist in zip(docs, metas, dists):
                m = m or {}
                if ent:
                    meta_ent = str(m.get("entity", "")).lower()
                    meta_bank = str(m.get("bank", "")).lower()
                    meta_org = str(m.get("org", "")).lower()
                    if ent not in meta_ent and ent not in meta_bank and ent not in meta_org:
                        continue
                out.append({
                    "content": (doc or "").strip(),
                    "metadata": m,
                    "distance": float(dist) if dist is not None else 0.0
                })

            return out[:n_results]

        except Exception as e:
            logger.error(f"❌ Error in query_xlsx_collection: {e}")
            return []

   
    def _detect_actual_collection_dimensions(self, collection) -> Optional[int]:
        """Detect the actual dimensions of a ChromaDB collection by testing with a sample vector"""
        try:
            # Try to get existing embeddings to detect dimensions
            sample_result = collection.get(limit=1, include=["embeddings"])
            if sample_result and sample_result.get("embeddings") and sample_result["embeddings"][0]:
                actual_dim = len(sample_result["embeddings"][0])
                logger.info(f"🔍 Detected actual collection dimensions from existing data: {actual_dim}D")
                return actual_dim
        except Exception as e:
            logger.debug(f"Could not detect dimensions from existing data: {e}")
        
        # If no existing data, we can't detect dimensions reliably
        return None

    def query_pdf_collection(
        self,
        query: str,
        n_results: int = 3,
        entity: Optional[str] = None,
        add_cite: bool = False
    ) -> List[Dict[str, Any]]:
        """Query PDF collection with robust dimension mismatch handling."""
        # Build filter
        where_filter = {"entity": entity.lower()} if entity else None

        # Hard guard: require an embedder object
        if not hasattr(self, "embedder") or self.embedder is None:
            logger.error("No embedder configured for PDF collection query")
            return []
            
        if not hasattr(self.embedder, "embed_query"):
            logger.error("Embedder does not have embed_query method")
            return []

        try:
            # Get the embedder's actual dimensions
            embedder_info = self.embedder.get_model_info()
            handler_dim = embedder_info.get("dimensions")
            
            # Get collection metadata dimensions
            metadata_dim = (self.pdf_collection.metadata or {}).get("embedding_dimensions")
            
            # Detect actual ChromaDB collection dimensions
            actual_dim = self._detect_actual_collection_dimensions(self.pdf_collection)
            
            logger.info(f"PDF collection dimension check: metadata={metadata_dim}D, actual={actual_dim}D, embedder={handler_dim}D")
            
            # Check if we have a dimension mismatch
            dimension_mismatch = False
            if actual_dim and handler_dim and actual_dim != handler_dim:
                dimension_mismatch = True
                logger.warning(f"❌ ACTUAL dimension mismatch: collection has {actual_dim}D vectors, embedder produces {handler_dim}D")
            elif metadata_dim and handler_dim and metadata_dim != handler_dim and not actual_dim:
                dimension_mismatch = True
                logger.warning(f"⚠️ METADATA dimension mismatch: collection metadata says {metadata_dim}D, embedder produces {handler_dim}D")
            
            if dimension_mismatch:
                # Try to find the correct PDF collection for this embedding model
                correct_collection_name = f"pdf_documents_{self.embedding_model_name}_{handler_dim}"
                logger.info(f"🔍 Looking for correct PDF collection: {correct_collection_name}")
                
                try:
                    candidate_collection = self.client.get_collection(correct_collection_name)
                    # Verify this collection actually has the right dimensions
                    candidate_actual_dim = self._detect_actual_collection_dimensions(candidate_collection)
                    
                    if candidate_actual_dim == handler_dim or candidate_collection.count() == 0:
                        self.pdf_collection = candidate_collection
                        logger.info(f"✅ Switched to correct PDF collection: {correct_collection_name}")
                        actual_dim = handler_dim  # Update for consistency
                    else:
                        logger.warning(f"⚠️ Found collection {correct_collection_name} but it has {candidate_actual_dim}D, not {handler_dim}D")
                        raise Exception("Dimension mismatch in candidate collection")
                        
                except Exception as e:
                    logger.error(f"Could not use collection {correct_collection_name}: {e}")
                    
                    # Try to find any PDF collection with the right dimensions
                    found_alternative = False
                    for collection_info in self.client.list_collections():
                        coll_name = getattr(collection_info, 'name', str(collection_info))
                        if coll_name.startswith("pdf_documents_") and str(handler_dim) in coll_name:
                            try:
                                candidate = self.client.get_collection(coll_name)
                                candidate_dim = self._detect_actual_collection_dimensions(candidate)
                                
                                if candidate_dim == handler_dim or candidate.count() == 0:
                                    self.pdf_collection = candidate
                                    logger.info(f"✅ Found alternative PDF collection: {coll_name}")
                                    actual_dim = handler_dim
                                    found_alternative = True
                                    break
                            except Exception:
                                continue
                    
                    if not found_alternative:
                        # Create a new collection with the correct dimensions
                        logger.info(f"🆕 Creating new PDF collection for {handler_dim}D embeddings: {correct_collection_name}")
                        metadata = {
                            "hnsw:space": "cosine",
                            "embedding_model": self.embedding_model_name,
                            "embedding_dimensions": handler_dim
                        }
                        self.pdf_collection = self.client.get_or_create_collection(
                            name=correct_collection_name,
                            metadata=metadata
                        )
                        logger.info(f"✅ Created new PDF collection: {correct_collection_name}")
                        actual_dim = handler_dim

            # Generate query embedding
            qvec = self.embedder.embed_query(query)
            if handler_dim and len(qvec) != handler_dim:
                logger.error(f"Embedder returned {len(qvec)}D, expected {handler_dim}D")
                return []

            # Perform the query
            results = self.pdf_collection.query(
                query_embeddings=[qvec],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results with optional citation
            formatted_results = []
            docs = results.get("documents", [[]])[0] if results.get("documents") else []
            metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            dists = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(docs)

            for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
                out = {
                    "content": doc or "",
                    "metadata": meta if meta else {},
                    "distance": float(dist) if dist is not None else 0.0
                }
                if add_cite and hasattr(self, "_add_cite"):
                    meta_with_cite = self._add_cite(meta)
                    out["metadata"] = meta_with_cite
                    out["content"] = f"{doc} {meta_with_cite['cite']}"
                formatted_results.append(out)

            logger.info(f"✅ PDF query successful: {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error in PDF collection query: {e}")
            # If it's a dimension error, provide helpful guidance
            if "dimension" in str(e).lower():
                logger.error("💡 Suggestion: Try recreating the PDF collection with the correct embedding model")
            return []


    def OLD_query_pdf_collection(self, query: str, n_results: int = 3, entity: Optional[str] = None, add_cite: bool = False) -> List[Dict[str, Any]]:
        """Query PDF collection with embedding support and optional citation markup."""
        try:
            # Build filter
            where_filter = {"entity": entity.lower()} if entity else None

            # ✅ Minimal guard – blow up early if dims mismatch
            if (self.pdf_collection.metadata or {}).get("embedding_dimensions") != (self.get_embedding_info() or {}).get("dimensions"):
                raise ValueError(
                    f"EMBEDDING_DIMENSION_MISMATCH: collection expects "
                    f"{(self.pdf_collection.metadata or {}).get('embedding_dimensions')}D, "
                    f"current handler has {(self.get_embedding_info() or {}).get('dimensions')}D"
    )

            # Query by embedding or text, depending on backend
            if isinstance(self.embedding_model, str):
                # ChromaDB default
                results = self.pdf_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                try:
                    query_embedding = self.embedding_model.embed_query(query)
                    results = self.pdf_collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"]
                    )
                except Exception as e:
                    logger.error(f"❌ OCI query embedding failed: {e}")
                    # Fallback to text query
                    results = self.pdf_collection.query(
                        query_texts=[query],
                        n_results=n_results,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"]
                    )

            # Format results with optional citation
            formatted_results = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)

            for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
                out = {
                    "content": doc,
                    "metadata": meta if meta else {},
                    "distance": dist
                }
                if add_cite and hasattr(self, "_add_cite"):
                    meta_with_cite = self._add_cite(meta)
                    out["metadata"] = meta_with_cite
                    out["content"] = f"{doc} {meta_with_cite['cite']}"
                formatted_results.append(out)

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Error querying PDF collection: {e}")
            return []

    


    def inspect_xlsx_chunk_metadata(self, limit: int = 10):
        """
        Print stored metadata from the XLSX vector store for debugging.
        Assumes self.xlsx_collection is a valid Chroma collection.
        """
        try:
            print(f"📦 Inspecting XLSX vector store metadata (limit: {limit})...")
            
            # Fetch all metadata
            results = self.xlsx_collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            total = len(metadatas)
            print(f"✅ Retrieved {total} metadata entries")

            if not metadatas:
                print("⚠️ No metadata found. Check if data was ingested correctly.")
                return

            for i, meta in enumerate(metadatas[:limit]):
                print(f"🔹 Chunk {i}: {meta}")

            if total > limit:
                print(f"... ({total - limit} more not shown)")

        except Exception as e:
            print(f"❌ Error inspecting metadata: {e}")

    def bind_collections_for_model(self, embedding_model: str) -> None:
        """
        Bind PDF/XLSX collections to the *same* fully-qualified names used at init:
        '{base}_{embedding_model_name}_{embedding_dim}'.
        This guarantees we re-open the exact populated collections for the current model+dim.
        """
        # Update the active embedding model handler/name on the store
        self.embedding_model_name = embedding_model
        self.embedding_model = self.embedding_manager.get_model(embedding_model)
        
        # CRITICAL: Update the embedder object if it was passed during init
        # This ensures add_xlsx_chunks and add_pdf_chunks use the correct embedder
        if hasattr(self, 'embedder') and self.embedder is not None:
            # If we have an embedder, ensure it matches the current model
            if not isinstance(self.embedding_model, str):
                self.embedder = self.embedding_model
                logger.info(f"✅ Updated embedder to match {embedding_model}")
        elif not isinstance(self.embedding_model, str):
            # No embedder was set but we have a non-string model, set it now
            self.embedder = self.embedding_model
            logger.info(f"✅ Set embedder for {embedding_model}")
        else:
            # For chromadb-default, we don't have an embedder object
            self.embedder = None

        # Get expected dimensions the same way __init__ does
        if isinstance(self.embedding_model, str):
            info = self.embedding_manager.get_model_info(self.embedding_model_name)
            if not info or "dimensions" not in info:
                raise ValueError(
                    f"Unknown embedding dimension for model '{self.embedding_model_name}'. "
                    "Update EmbeddingModelManager.get_model_info()."
                )
            embedding_dim = info["dimensions"]
        else:
            info = self.embedding_model.get_model_info()
            embedding_dim = info.get("dimensions")
            if not embedding_dim:
                raise ValueError("Cannot determine embedding dimensions for current embedding handler.")

        # Build the exact same names used in __init__
        pdf_name  = f"pdf_documents_{self.embedding_model_name}_{embedding_dim}"
        xlsx_name = f"xlsx_documents_{self.embedding_model_name}_{embedding_dim}"

        # Get or create those specific collections with proper metadata
        metadata = {
            "hnsw:space": "cosine",
            "embedding_model": self.embedding_model_name,
            "embedding_dimensions": embedding_dim
        }
        
        self.pdf_collection  = self.client.get_or_create_collection(
            name=pdf_name,
            metadata=metadata
        )
        self.xlsx_collection = self.client.get_or_create_collection(
            name=xlsx_name,
            metadata=metadata
        )

        # Cache for debugging
        self.current_pdf_collection_name = pdf_name
        self.current_xlsx_collection_name = xlsx_name

        logger.info(f"🔗 Bound collections to: PDF='{pdf_name}' ({embedding_dim}D), XLSX='{xlsx_name}' ({embedding_dim}D)")


def main():
    """Test the enhanced vector store"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test enhanced vector store")
    parser.add_argument("--embedding-model", default="chromadb-default",
                       help="Embedding model to use")
    parser.add_argument("--query", default="ESG sustainability metrics",
                       help="Test query")
    parser.add_argument("--collection", default="xlsx_documents",
                       help="Collection to query")
    parser.add_argument("--compare", action="store_true",
                       help="Compare different embedding models")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize enhanced vector store
        print(f"Initializing enhanced vector store with {args.embedding_model}...")
        store = EnhancedVectorStore(embedding_model=args.embedding_model)
        
        # Show embedding info
        embedding_info = store.get_embedding_info()
        print(f"✅ Using embedding model: {embedding_info['name']}")
        print(f"   Description: {embedding_info['description']}")
        print(f"   Dimensions: {embedding_info['dimensions']}")
        print(f"   Type: {embedding_info['type']}")
        
        if args.compare:
            # Compare embedding models
            print(f"\n🔍 Comparing embedding models for query: '{args.query}'")
            comparison = store.compare_embeddings(args.query, args.collection)
            
            for model_name, result in comparison.items():
                print(f"\n--- {model_name} ---")
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    details = result["details"]
                    print(f"✅ Retrieved {details['num_results']} results in {details['retrieval_time']:.3f}s")
                    
                    # Show first result preview
                    if result["results"]:
                        first_result = result["results"][0]
                        content_preview = first_result["content"][:100] + "..."
                        print(f"   First result: {content_preview}")
        else:
            # Single query
            print(f"\n🔍 Querying {args.collection} with: '{args.query}'")
            results, details = store.query_with_details(args.collection, args.query)
            
            print(f"✅ Retrieved {details['num_results']} results in {details['retrieval_time']:.3f}s")
            print(f"   Embedding model: {details['embedding_model']}")
            
            # Show results
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                content_preview = result["content"][:200] + "..."
                print(f"Content: {content_preview}")
                
                metadata = result.get("metadata", {})
                if isinstance(metadata, dict):
                    source = metadata.get("source", "Unknown")
                    print(f"Source: {source}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
