#!/usr/bin/env python3
"""
Enhanced Vector Store with Multi-Embedding Model Support
Extends the existing VectorStore to support OCI Cohere embeddings alongside ChromaDB defaults
"""
from oci_embedding_handler import OCIEmbeddingHandler, EmbeddingModelManager
import logging, numbers
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

    def __init__(self, persist_directory: str = "embeddings",
                 embedding_model: str = "cohere-embed-multilingual-v3.0",
                 embedder=None):
        self.embedding_manager = EmbeddingModelManager()
        self.embedding_model_name = embedding_model
        self.embedder = embedder
        self.embedding_dimensions = getattr(embedder, "model_config", {}).get("dimensions", None) if embedder else None

        # Resolve embedding handler
        self.embedding_model = embedder or self.embedding_manager.get_model(embedding_model)

        # Chroma client (ensure Settings import: from chromadb.config import Settings)
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

        # Resolve dimensions once
        self._embedding_dim = self._resolve_dimensions()

        # Internal maps/handles
        self.collections: dict[str, Any] = {}
        self.collection_map = self.collections  # alias

        # Create/bind base collections (pdf/xlsx) for current model+dim
        self._ensure_base_collections(self._embedding_dim)

        logger.info(f"✅ Enhanced vector store initialized with {self.embedding_model_name} ({self._embedding_dim}D)")

    # --- Utility: sanitize metadata before sending to Chroma ---
    def _safe_metadata(self, metadata: dict) -> dict:
        """Ensure Chroma-compatible metadata (convert everything non-str → str)."""
        safe = {}
        for k, v in (metadata or {}).items():
            key = str(k)
            if isinstance(v, str):
                safe[key] = v
            elif isinstance(v, numbers.Number):  # catches numpy.int64, Decimal, etc.
                safe[key] = str(v)
            elif v is None:
                continue
            else:
                safe[key] = str(v)
        return safe

    def _as_int(self, x):
        try:
            return int(x)
        except Exception:
            return None

    def _resolve_dimensions(self) -> int:
        if self.embedder:
            info = self.embedder.get_model_info()
            if info and "dimensions" in info:
                return int(info["dimensions"])
            raise ValueError("Cannot determine embedding dimensions from provided embedder.")
        if isinstance(self.embedding_model, str):
            info = self.embedding_manager.get_model_info(self.embedding_model_name)
            if info and "dimensions" in info:
                return int(info["dimensions"])
            raise ValueError(f"Unknown embedding dimension for model '{self.embedding_model_name}'.")
        # non-string handler
        info = self.embedding_model.get_model_info()
        if info and "dimensions" in info:
            return int(info["dimensions"])
        raise ValueError("Cannot determine embedding dimensions for non-string embedding model.")

    def _ensure_base_collections(self, embedding_dim: int):
        base_collection_names = ["pdf_documents", "xlsx_documents"]
        metadata = {
            "hnsw:space": "cosine",
            "embedding_model": self.embedding_model_name,  # keep int in memory
            "embedding_dimensions": embedding_dim         # keep int in memory
        }

        for base_name in base_collection_names:
            full_name = f"{base_name}_{self.embedding_model_name}_{embedding_dim}"
            try:
                # Prefer fast path: get_or_create with safe metadata
                coll = self.client.get_or_create_collection(
                    name=full_name,
                    metadata=self._safe_metadata(metadata)  # ← sanitize only here
                )

                # Defensive dim check (cast back to int if Chroma stored as str)
                actual_dim = self._as_int((coll.metadata or {}).get("embedding_dimensions"))
                if actual_dim and actual_dim != embedding_dim:
                    logger.error(f"❌ Dimension mismatch for '{full_name}'. Expected {embedding_dim}, found {actual_dim}.")
                    raise ValueError(f"Collection '{full_name}' has dim {actual_dim}, expected {embedding_dim}.")

                self.collections[full_name] = coll
                if base_name == "pdf_documents":
                    self.pdf_collection = coll
                    self.current_pdf_collection_name = full_name
                else:
                    self.xlsx_collection = coll
                    self.current_xlsx_collection_name = full_name

                logger.info(f"🗂️  Ready collection '{full_name}' ({embedding_dim}D, {coll.count()} chunks)")
            except Exception as e:
                logger.error(f"❌ Failed to create or get collection '{full_name}': {e}")
                raise

    def get_collection_key(self, base_name: str) -> str:
        return f"{base_name}_{self.embedding_model_name}_{self._embedding_dim}"


    def _find_collection_variants(self, base_name: str):
        """
        Yield (name, collection) for all collections that start with base_name+"_".
        Never create here—only fetch existing collections.
        """
        for c in self.client.list_collections():
            try:
                name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
            except Exception:
                name = None
            if not name:
                continue
            if not name.startswith(base_name + "_"):
                continue
            try:
                coll = self.client.get_collection(name=name)  # ← get (NOT get_or_create)
                yield name, coll
            except Exception as e:
                logger.warning(f"Skip collection {name}: {e}")


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

    
    def delete_chunks(self, collection_name: str, chunk_ids: List[str]):
        """Delete specific chunks from a collection by their IDs
        
        Args:
            collection_name: Name of the collection (e.g., 'xlsx_documents', 'pdf_documents')
            chunk_ids: List of chunk IDs to delete
        """
        if not chunk_ids:
            return
            
        try:
            # Get the appropriate collection
            if collection_name == "xlsx_documents":
                collection = self.xlsx_collection
            elif collection_name == "pdf_documents":
                collection = self.pdf_collection
            else:
                # Try to get from collection map
                collection = self.collection_map.get(collection_name)
                if not collection:
                    # Try with current model/dimension suffix
                    full_name = self.get_collection_key(collection_name)
                    collection = self.collection_map.get(full_name)
                    
            if not collection:
                logger.error(f"Collection {collection_name} not found")
                return
                
            # Delete the chunks
            collection.delete(ids=chunk_ids)
            logger.info(f"✅ Deleted {len(chunk_ids)} chunks from {collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete chunks: {e}")
            raise
    
    def add_xlsx_chunks(self, chunks: List[Dict[str, Any]], document_id: str):
        """Add XLSX chunks to the vector store with proper embedding handling"""
        if not chunks:
            return

        # Extract texts and metadata
        texts = [c["content"] for c in chunks]
        metadatas = [self._add_cite(c.get("metadata", {})) for c in chunks]  # add cite & normalize
        ids = [c["id"] for c in chunks]

        # Normalize expected dimensions/model from collection metadata
        collection_metadata = self.xlsx_collection.metadata or {}
        expected_dimensions = self._as_int(collection_metadata.get("embedding_dimensions"))
        expected_model = collection_metadata.get("embedding_model")

        # Path A: chroma-default (Chroma embeds on add)
        if isinstance(self.embedding_model, str):
            # If the collection expects non-384, error early (your policy)
            if expected_dimensions and expected_dimensions != 384:
                logger.error(f"❌ Collection expects {expected_dimensions}D but using ChromaDB default (384D)")
                raise ValueError(
                    f"Dimension mismatch: collection expects {expected_dimensions}D, ChromaDB default is 384D"
                )

            # Optional: warn if the collection was created without an embedding function bound (older Chroma)
            try:
                self.xlsx_collection.add(documents=["probe"], metadatas=[{}], ids=["__probe__tmp__"])
                self.xlsx_collection.delete(ids=["__probe__tmp__"])
            except Exception as e:
                logger.warning(f"⚠️ Chroma default embedding may not be bound; add() failed probe: {e}")

            # Add documents directly (Chroma will embed)
            # Consider batching if many chunks
            self.xlsx_collection.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"✅ Added {len(chunks)} XLSX chunks to {self.embedding_model_name} (chroma-default)")
            return

        # Path B: OCI (you provide embeddings explicitly)
        try:
            embeddings = self.embedding_model.embed_documents(texts)
            if not embeddings or not embeddings[0] or not hasattr(embeddings[0], "__len__"):
                raise RuntimeError("Embedder returned empty/invalid embeddings")

            actual_dimensions = len(embeddings[0])

            if expected_dimensions and actual_dimensions != expected_dimensions:
                # Try to find or create the correct collection
                correct_collection_name = f"xlsx_documents_{self.embedding_model_name}_{actual_dimensions}"
                logger.warning(
                    f"⚠️ Dimension mismatch: collection '{self.xlsx_collection.name}' "
                    f"expects {expected_dimensions}D, embedder produces {actual_dimensions}D"
                )
                logger.info(f"🔍 Looking for correct collection: {correct_collection_name}")

                try:
                    correct_collection = self.client.get_collection(correct_collection_name)
                    logger.info(f"✅ Found correct collection: {correct_collection_name}")
                except Exception:
                    # Create new collection with correct dimensions (sanitize metadata for Chroma)
                    metadata = {
                        "hnsw:space": "cosine",
                        "embedding_model": self.embedding_model_name,
                        "embedding_dimensions": actual_dimensions,  # keep as int internally
                    }
                    correct_collection = self.client.create_collection(
                        name=correct_collection_name,
                        metadata=self._safe_metadata(metadata)     # ← sanitize only here
                    )
                    logger.info(f"✅ Created new collection: {correct_collection_name}")

                # Add to the correct collection (explicit vectors)
                # Consider batching if many chunks
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
            raise  # Keep explicit; prevents silent dimension drift


    def add_pdf_chunks(self, chunks: List[Dict[str, Any]], document_id: str):
        """Add PDF chunks to the vector store with proper embedding handling."""
        if not chunks:
            return

        # Extract texts and metadata; add cite + normalize metadata
        texts = [c["content"] for c in chunks]
        metadatas = [self._add_cite(c.get("metadata", {})) for c in chunks]
        ids = [c["id"] for c in chunks]

        # Collection expectations (cast back to int to avoid string/int mismatches)
        coll_meta = self.pdf_collection.metadata or {}
        expected_dimensions = self._as_int(coll_meta.get("embedding_dimensions"))
        expected_model = coll_meta.get("embedding_model")

        # A) chroma-default path (Chroma embeds on add)
        if isinstance(self.embedding_model, str):
            if expected_model and self.embedding_model_name != expected_model:
                logger.warning(
                    f"⚠️ Model mismatch: collection expects '{expected_model}', got '{self.embedding_model_name}'"
                )

            # Your policy: chroma-default is 384D only
            if expected_dimensions and expected_dimensions != 384:
                raise ValueError(
                    f"Dimension mismatch: collection expects {expected_dimensions}D, "
                    f"but chroma-default produces 384D. Recreate the collection with chroma-default "
                    f"or switch to the correct OCI embedder."
                )

            # Optional: probe add for older Chroma builds without an embedding_function bound
            try:
                self.pdf_collection.add(documents=["__probe__"], metadatas=[{}], ids=["__probe__"])
                self.pdf_collection.delete(ids=["__probe__"])
            except Exception as e:
                logger.warning(f"⚠️ Chroma default embedder may not be bound; add() probe failed: {e}")

            # Add (consider batching if very large)
            self.pdf_collection.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"✅ Added {len(chunks)} PDF chunks via chroma-default (384D)")
            return

        # B) OCI path (explicit embeddings)
        try:
            embeddings = self.embedding_model.embed_documents(texts)
            if not embeddings or not embeddings[0] or not hasattr(embeddings[0], "__len__"):
                raise RuntimeError("Embedder returned empty/invalid embeddings")

            actual_dimensions = len(embeddings[0])

            # If the target collection's dim doesn't match, route/create the correct one
            if expected_dimensions and actual_dimensions != expected_dimensions:
                logger.warning(
                    f"⚠️ Dimension mismatch: collection '{self.pdf_collection.name}' expects "
                    f"{expected_dimensions}D, embedder produced {actual_dimensions}D"
                )
                correct_name = f"pdf_documents_{self.embedding_model_name}_{actual_dimensions}"
                try:
                    correct_collection = self.client.get_collection(correct_name)
                    # Sanity check: if it already contains data of a different dim (shouldn’t happen), bail
                    probe_meta = correct_collection.metadata or {}
                    probe_dim = self._as_int(probe_meta.get("embedding_dimensions"))
                    if probe_dim and probe_dim != actual_dimensions:
                        raise RuntimeError(
                            f"Existing collection '{correct_name}' is {probe_dim}D, expected {actual_dimensions}D"
                        )
                    logger.info(f"✅ Found correct PDF collection: {correct_name}")
                except Exception:
                    # Create with sanitized metadata (only at API boundary)
                    md = {
                        "hnsw:space": "cosine",
                        "embedding_model": self.embedding_model_name,
                        "embedding_dimensions": actual_dimensions,  # keep int internally
                    }
                    correct_collection = self.client.get_or_create_collection(
                        name=correct_name,
                        metadata=self._safe_metadata(md)  # sanitize here
                    )
                    logger.info(f"🆕 Created PDF collection: {correct_name}")

                # Add to the correct collection
                correct_collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )

                # Re-point handles
                self.pdf_collection = correct_collection
                self.collections[correct_name] = correct_collection
                self.current_pdf_collection_name = correct_name

                logger.info(f"✅ Added {len(chunks)} PDF chunks to {correct_name}")
            else:
                # Dimensions match; add directly
                self.pdf_collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
                logger.info(f"✅ Added {len(chunks)} PDF chunks ({actual_dimensions}D)")

        except Exception as e:
            logger.error(f"❌ Failed to add PDF chunks with OCI embeddings: {e}")
            raise  # keep explicit; prevents silent dimension drift

    


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
                            metadata=self._safe_metadata(metadata) 
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
        logger.info(
            "Create/get collections: PDF=%r, XLSX=%r | meta=%r (dim_field=%s:%s)",
            pdf_name,
            xlsx_name,
            metadata,
            "embedding_dimensions",
            type(metadata.get("embedding_dimensions")).__name__,
        )
        self.pdf_collection  = self.client.get_or_create_collection(
            name=pdf_name,
            metadata=self._safe_metadata(metadata) 
        )
        self.xlsx_collection = self.client.get_or_create_collection(
            name=xlsx_name,
            metadata=self._safe_metadata(metadata) 
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
