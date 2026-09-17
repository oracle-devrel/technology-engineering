"""
RAG (Retrieval-Augmented Generation) service for document chat.
Integrates with Oracle 23ai Vector Store for intelligent document retrieval
and Llama Stack endpoint for answer generation.
"""

import logging
import os
import time
from typing import Optional
from urllib.parse import urlparse

from openai import OpenAI, APIError, APITimeoutError, APIConnectionError

from services.oracle_vector_store import OracleVectorStore, OracleVectorStoreError
from services.embedding_service import EmbeddingService
from services.chunking import DocumentChunker, chunk_document

logger = logging.getLogger(__name__)


class RAGSource:
    """Represents a source document reference."""

    def __init__(
        self,
        document_name: Optional[str] = None,
        page_number: Optional[int] = None,
        snippet: str = "",
        relevance_score: float = 0.5,
    ):
        self.document_name = document_name
        self.page_number = page_number
        self.snippet = snippet
        self.relevance_score = relevance_score

    def to_dict(self) -> dict:
        return {
            "document_name": self.document_name,
            "page_number": self.page_number,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
        }


class RAGResponse:
    """Represents a RAG query response."""

    def __init__(
        self,
        message: str,
        sources: list[RAGSource] = None,
        confidence: float = 0.0,
        processing_time_ms: Optional[float] = None,
    ):
        self.message = message
        self.sources = sources or []
        self.confidence = confidence
        self.processing_time_ms = processing_time_ms

    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "sources": [s.to_dict() for s in self.sources],
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
        }


class RAGService:
    """
    Service class for RAG-based document chat operations.

    Integrates with:
    - Oracle 23ai Vector Store for semantic retrieval
    - Embedding service for query vectorization
    - Llama Stack endpoint for answer generation (via OpenAI client)
    """

    REQUEST_TIMEOUT = 60.0
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.3

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        vector_store: Optional[OracleVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        use_vector_search: bool = True,
    ):
        """
        Initialize RAG service.

        Args:
            endpoint_url: Optional custom RAG endpoint URL
            username: Username for Basic Auth. Defaults to env var.
            password: Password for Basic Auth. Defaults to env var.
            api_key: API key for Bearer auth. Defaults to env var.
            vector_store: Optional pre-configured vector store instance.
            embedding_service: Optional pre-configured embedding service.
            use_vector_search: Whether to use vector search (True) or full text (False).
        """
        raw_url = (
            endpoint_url
            or os.getenv("RAG_ENDPOINT_URL", "")
        ).rstrip("/")
        if not raw_url:
            raise ValueError("RAG_ENDPOINT_URL environment variable is required")

        # Parse URL: use the cleaned base URL (trailing slash stripped)
        parsed = urlparse(raw_url)
        self.endpoint_url = f"{parsed.scheme}://{parsed.netloc}/v1"
        self.model = os.getenv("RAG_MODEL", "meta.llama-4-maverick-17b-128e-instruct-fp8")

        # Resolve API key for OpenAI client: prefer explicit api_key, then env vars
        resolved_api_key = api_key or os.getenv("RAG_API_KEY", "")
        if not resolved_api_key:
            # Llama Stack doesn't require an API key; use a placeholder
            resolved_api_key = "no-key-required"

        # Create OpenAI client pointing at the Llama Stack base URL
        self._client = OpenAI(
            base_url=self.endpoint_url,
            api_key="fake",
            timeout=self.REQUEST_TIMEOUT,
        )

        logger.info(
            f"RAGService initialized: endpoint={self.endpoint_url}, model={self.model}"
        )

        # Vector search components
        self.use_vector_search = use_vector_search
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._vector_store_initialized = False

    async def _get_vector_store(self) -> OracleVectorStore:
        """Get or create the vector store instance."""
        if self._vector_store is None:
            self._vector_store = OracleVectorStore()

        if not self._vector_store_initialized:
            try:
                await self._vector_store.initialize()
                self._vector_store_initialized = True
            except OracleVectorStoreError as e:
                logger.warning(f"Vector store initialization failed: {e}")
                self.use_vector_search = False
                raise

        return self._vector_store

    async def _get_embedding_service(self) -> EmbeddingService:
        """Get or create the embedding service instance."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @staticmethod
    def _classify_model(model_id: str) -> str:
        """Classify a model as 'embedding', 'rerank', or 'llm' based on its ID."""
        lower_id = model_id.lower()
        if "embed" in lower_id:
            return "embedding"
        if "rerank" in lower_id:
            return "rerank"
        return "llm"

    async def list_models(self) -> list[dict]:
        """Fetch available models from the Llama Stack endpoint.

        Returns:
            List of model dicts with 'id' and 'type' fields.
            Type is one of: 'llm', 'embedding', 'rerank'.
        """
        try:
            models_page = self._client.models.list()
            result = []
            for m in models_page.data:
                result.append({
                    "id": m.id,
                    "type": self._classify_model(m.id),
                })
            return result
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def index_document(
        self,
        document_id: str,
        text: str,
        filename: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> int:
        """
        Index a document by chunking and storing embeddings.

        Args:
            document_id: Unique document identifier.
            text: Document text content.
            filename: Optional filename for reference.
            chunk_size: Size of each chunk in characters.
            chunk_overlap: Overlap between chunks.

        Returns:
            Number of chunks indexed.
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for document {document_id}")
            return 0

        try:
            vector_store = await self._get_vector_store()
            embedding_service = await self._get_embedding_service()

            # Chunk the document
            chunks = chunk_document(
                text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                strategy="recursive",
                metadata={"filename": filename, "document_id": document_id},
            )

            if not chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                return 0

            logger.info(f"Generated {len(chunks)} chunks for document {document_id}")

            # Generate embeddings for all chunks
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)

            if len(embeddings) != len(chunks):
                logger.error(
                    f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks"
                )
                return 0

            # Prepare chunks with embeddings
            chunks_with_embeddings = []
            for chunk, embedding in zip(chunks, embeddings):
                chunks_with_embeddings.append({
                    "content": chunk["content"],
                    "embedding": embedding,
                    "metadata": chunk.get("metadata"),
                })

            # Store in vector store
            stored_count = await vector_store.store_chunks(
                document_id=document_id,
                chunks=chunks_with_embeddings,
                filename=filename,
            )

            logger.info(f"Indexed {stored_count} chunks for document {document_id}")
            return stored_count

        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            raise

    async def delete_document_vectors(self, document_id: str) -> int:
        """
        Delete all vectors for a document.

        Args:
            document_id: The document identifier.

        Returns:
            Number of chunks deleted.
        """
        try:
            vector_store = await self._get_vector_store()
            return await vector_store.delete_document(document_id)
        except Exception as e:
            logger.error(f"Failed to delete vectors for document {document_id}: {e}")
            return 0

    async def query(
        self,
        query: str,
        document_texts: list[dict],
        conversation_history: list[dict] = None,
        max_sources: int = 5,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        model_settings: dict | None = None,
        inference_model: str | None = None,
    ) -> RAGResponse:
        """
        Query the RAG system with documents context.

        Uses vector search to retrieve relevant chunks, then sends
        the context to the LLM for answer generation.

        Args:
            query: User's question
            document_texts: List of dicts with 'id', 'filename', 'text' keys
            conversation_history: Optional previous conversation messages
            max_sources: Maximum number of source references to return
            top_k: Number of chunks to retrieve from vector search
            score_threshold: Minimum similarity score for retrieved chunks
            model_settings: Optional dict with keys like temperature, max_tokens,
                top_p, frequency_penalty, presence_penalty to override defaults.

        Returns:
            RAGResponse with answer and sources
        """
        start_time = time.time()
        conversation_history = conversation_history or []

        # Extract document IDs for filtering
        document_ids = [doc.get("id") for doc in document_texts if doc.get("id")]

        # Try vector search first
        retrieved_chunks = []
        if self.use_vector_search and document_ids:
            try:
                retrieved_chunks = await self._retrieve_relevant_chunks(
                    query=query,
                    document_ids=document_ids,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )
                logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks via vector search")
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to full text: {e}")
                retrieved_chunks = []

        # Build context from retrieved chunks or full documents
        if retrieved_chunks:
            # Use retrieved chunks
            combined_text = self._build_context_from_chunks(retrieved_chunks)
        else:
            # Fallback: use full document text
            combined_text = "\n\n---\n\n".join(
                f"[Document: {doc.get('filename', 'Unknown')}]\n{doc.get('text', '')}"
                for doc in document_texts
            )

        # Build conversation history context
        history_context = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.get('content', '')}")
            history_context = "\n".join(history_lines)

        # Build the prompt
        system_prompt = """You are a helpful document analysis assistant. Answer questions based on the provided document excerpts accurately and concisely.

When answering:
1. Base your response strictly on the information in the provided excerpts
2. If the answer cannot be found in the excerpts, clearly state that
3. Cite specific parts of the documents when relevant
4. Be concise but thorough"""

        user_prompt = f"""Based on the following document excerpt(s), please answer the user's question.

DOCUMENT EXCERPTS:
{combined_text}

{f"PREVIOUS CONVERSATION:{chr(10)}{history_context}{chr(10)}{chr(10)}" if history_context else ""}USER QUESTION:
{query}

Please provide a helpful and accurate answer based on the information in the document excerpts."""

        try:
            # Build request kwargs
            settings = model_settings or {}
            active_model = inference_model or self.model
            kwargs = {
                "model": active_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": settings.get("temperature", 0.3),
                "max_tokens": settings.get("max_tokens", 2048),
            }
            if "top_p" in settings:
                kwargs["top_p"] = settings["top_p"]
            if "frequency_penalty" in settings:
                kwargs["frequency_penalty"] = settings["frequency_penalty"]
            if "presence_penalty" in settings:
                kwargs["presence_penalty"] = settings["presence_penalty"]

            logger.info(f"Sending chat request to Llama Stack with model {active_model}")
            response = self._client.chat.completions.create(**kwargs)

            processing_time = (time.time() - start_time) * 1000

            # Extract answer from response
            answer = response.choices[0].message.content if response.choices else ""

            if not answer:
                logger.warning("Llama Stack returned empty answer")
                return self._fallback_response(query, processing_time, "Empty response")

            # Build sources
            sources_data = retrieved_chunks if retrieved_chunks else document_texts
            sources = self._build_sources(
                answer, sources_data, max_sources, use_chunks=bool(retrieved_chunks)
            )

            # Calculate confidence
            if sources:
                avg_score = sum(s.relevance_score for s in sources) / len(sources)
                confidence = min(avg_score + 0.1, 1.0)
            else:
                confidence = 0.5

            return RAGResponse(
                message=answer,
                sources=sources,
                confidence=confidence,
                processing_time_ms=processing_time,
            )

        except APITimeoutError:
            processing_time = (time.time() - start_time) * 1000
            logger.error("Llama Stack chat request timed out")
            return RAGResponse(
                message="Request timed out. Please try again.",
                sources=[],
                confidence=0.0,
                processing_time_ms=processing_time,
            )

        except APIConnectionError as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Llama Stack connection error: {e}")
            return self._fallback_response(query, processing_time, str(e))

        except APIError as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Llama Stack API error: {e}")
            return self._fallback_response(query, processing_time, str(e))

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Llama Stack chat error: {e}")
            return self._fallback_response(query, processing_time, str(e))

    async def _retrieve_relevant_chunks(
        self,
        query: str,
        document_ids: list[str],
        top_k: int = 5,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """
        Retrieve relevant chunks using vector similarity search.

        Args:
            query: The user's query.
            document_ids: List of document IDs to search within.
            top_k: Number of results to retrieve.
            score_threshold: Minimum similarity score.

        Returns:
            List of relevant chunk dictionaries.
        """
        vector_store = await self._get_vector_store()
        embedding_service = await self._get_embedding_service()

        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)

        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []

        # Search for similar chunks
        results = await vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            score_threshold=score_threshold,
        )

        # Convert to dict format
        chunks = []
        for result in results:
            chunks.append({
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "content": result.content,
                "score": result.score,
                "filename": result.filename,
                "chunk_index": result.chunk_index,
            })

        return chunks

    def _build_context_from_chunks(self, chunks: list[dict]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        # Group chunks by document
        doc_chunks = {}
        for chunk in chunks:
            doc_id = chunk.get("document_id", "unknown")
            filename = chunk.get("filename", "Unknown Document")
            key = f"{doc_id}:{filename}"

            if key not in doc_chunks:
                doc_chunks[key] = {
                    "filename": filename,
                    "chunks": [],
                }
            doc_chunks[key]["chunks"].append(chunk)

        # Build context with document grouping
        for key, doc_data in doc_chunks.items():
            filename = doc_data["filename"]
            doc_chunks_sorted = sorted(
                doc_data["chunks"],
                key=lambda x: x.get("chunk_index", 0)
            )

            chunk_texts = []
            for chunk in doc_chunks_sorted:
                score = chunk.get("score", 0)
                content = chunk.get("content", "")
                chunk_texts.append(f"[Relevance: {score:.2f}]\n{content}")

            context_parts.append(
                f"[Document: {filename}]\n" + "\n\n".join(chunk_texts)
            )

        return "\n\n---\n\n".join(context_parts)

    def _build_sources(
        self,
        answer: str,
        sources_data: list[dict],
        max_sources: int,
        use_chunks: bool = False,
    ) -> list[RAGSource]:
        """Build source references from retrieved chunks or documents."""
        sources = []

        if use_chunks:
            for chunk in sources_data[:max_sources]:
                sources.append(
                    RAGSource(
                        document_name=chunk.get("filename"),
                        page_number=chunk.get("chunk_index", 0) + 1,
                        snippet=chunk.get("content", "")[:500],
                        relevance_score=chunk.get("score", 0.7),
                    )
                )
        else:
            for doc in sources_data[:max_sources]:
                text = doc.get("text", "")
                snippet = self._find_relevant_snippet(answer, text)
                sources.append(
                    RAGSource(
                        document_name=doc.get("filename"),
                        page_number=1,
                        snippet=snippet,
                        relevance_score=0.7,
                    )
                )

        return sources

    def _find_relevant_snippet(self, answer: str, doc_text: str, max_length: int = 300) -> str:
        """Find a relevant snippet from document text based on answer."""
        if not doc_text:
            return ""

        answer_words = set(answer.lower().split())
        sentences = doc_text.replace("\n", " ").split(".")

        best_sentence = ""
        best_score = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            sentence_words = set(sentence.lower().split())
            overlap = len(answer_words & sentence_words)
            score = overlap / max(len(sentence_words), 1)

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            return best_sentence[:max_length] + ("..." if len(best_sentence) > max_length else "")

        return doc_text[:max_length] + ("..." if len(doc_text) > max_length else "")

    def _fallback_response(
        self,
        query: str,
        processing_time: float,
        error_message: Optional[str] = None,
    ) -> RAGResponse:
        """Generate a fallback response when RAG service is unavailable."""
        logger.warning(f"Using fallback response. Error: {error_message}")

        message = (
            "I'm currently unable to connect to the AI service to process your question. "
            "This could be due to the service being temporarily unavailable.\n\n"
            "**What you can try:**\n"
            "- Wait a moment and try again\n"
            "- Check that the AI service is running and accessible\n\n"
            "Your question was: \"" + query[:100] + ("..." if len(query) > 100 else "") + "\""
        )

        return RAGResponse(
            message=message,
            sources=[],
            confidence=0.0,
            processing_time_ms=processing_time,
        )

    async def health_check(self) -> dict:
        """Check RAG service health including Llama Stack and vector store."""
        health = {
            "status": "healthy",
            "endpoint": self.endpoint_url,
            "model": self.model,
            "vector_search_enabled": self.use_vector_search,
        }

        # Check Llama Stack health via listing models
        try:
            models = self._client.models.list()
            health["llm_status"] = "healthy" if models.data else "degraded"
        except Exception as e:
            health["llm_status"] = "unavailable"
            health["llm_error"] = str(e)

        # Check vector store
        if self.use_vector_search:
            try:
                vector_store = await self._get_vector_store()
                vs_health = await vector_store.health_check()
                health["vector_store"] = vs_health
            except Exception as e:
                health["vector_store"] = {"status": "unavailable", "error": str(e)}

        # Check embedding service
        try:
            embedding_service = await self._get_embedding_service()
            emb_health = await embedding_service.health_check()
            health["embedding_service"] = emb_health
        except Exception as e:
            health["embedding_service"] = {"status": "unavailable", "error": str(e)}

        # Overall status
        if health.get("llm_status") == "unavailable":
            health["status"] = "degraded"
        if health.get("vector_store", {}).get("status") == "unhealthy":
            health["status"] = "degraded"

        return health

    async def close(self):
        """Close all connections."""
        self._client.close()

        if self._vector_store is not None:
            await self._vector_store.close()

        if self._embedding_service is not None:
            await self._embedding_service.close()
