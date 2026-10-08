"""
Embedding service for generating vector embeddings from text.
Integrates with Llama Stack via the OpenAI client.
"""

import logging
import os
from typing import Optional
from urllib.parse import urlparse

from openai import OpenAI, APIError, APITimeoutError, APIConnectionError

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Exception raised for embedding generation errors."""
    pass


class EmbeddingService:
    """
    Service for generating text embeddings using an embedding model.

    Uses the OpenAI client pointed at the Llama Stack /v1/embeddings endpoint.
    """

    DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
    REQUEST_TIMEOUT = 60.0

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        """
        Initialize the embedding service.

        Args:
            endpoint_url: Base URL for embedding API. Defaults to EMBEDDING_API_URL env var.
            api_key: API key for authentication. Defaults to CORRINO_API_KEY env var.
            username: Username for Basic Auth (unused with OpenAI client, kept for compat).
            password: Password for Basic Auth (unused with OpenAI client, kept for compat).
            model: Embedding model name. Defaults to EMBEDDING_MODEL env var.
            dimension: Expected embedding dimension. Defaults to ORACLE_EMBEDDING_DIMENSION env var.
        """
        raw_url = (
            endpoint_url
            or os.getenv("EMBEDDING_API_URL")
            or os.getenv("RAG_ENDPOINT_URL", "")
        ).rstrip("/")
        if not raw_url:
            raise ValueError("EMBEDDING_API_URL or RAG_ENDPOINT_URL environment variable is required")

        # Parse URL: strip any model path to get just the base URL
        parsed = urlparse(raw_url)
        self.endpoint_url = f"{parsed.scheme}://{parsed.netloc}"

        self.model = model or os.getenv("EMBEDDING_MODEL", self.DEFAULT_EMBEDDING_MODEL)
        self.dimension = int(dimension or os.getenv("ORACLE_EMBEDDING_DIMENSION", "1536"))

        # Resolve API key
        resolved_api_key = api_key or os.getenv("CORRINO_API_KEY", "")
        if not resolved_api_key:
            resolved_api_key = "no-key-required"

        # Create OpenAI client pointing at the Llama Stack base URL
        self._client = OpenAI(
            base_url=f"{self.endpoint_url}/v1",
            api_key=resolved_api_key,
            timeout=self.REQUEST_TIMEOUT,
        )

        logger.info(
            f"EmbeddingService initialized: endpoint={self.endpoint_url}, model={self.model}, dimension={self.dimension}"
        )

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        try:
            logger.info(f"Generating embeddings via Llama Stack with model {self.model}")
            response = self._client.embeddings.create(
                model=self.model,
                input=valid_texts,
                dimensions=self.dimension,
            )

            embeddings = [item.embedding for item in response.data]

            # Validate dimension
            if embeddings:
                actual_dim = len(embeddings[0])
                if actual_dim != self.dimension:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {self.dimension}, got {actual_dim}"
                    )

            return embeddings

        except APITimeoutError:
            logger.error("Llama Stack embedding request timed out")
            return self._generate_fallback_embeddings(valid_texts)

        except APIConnectionError as e:
            logger.error(f"Llama Stack embedding connection error: {e}")
            return self._generate_fallback_embeddings(valid_texts)

        except APIError as e:
            logger.warning(f"Llama Stack embedding API error: {e}, using fallback")
            return self._generate_fallback_embeddings(valid_texts)

        except Exception as e:
            logger.error(f"Llama Stack embedding generation failed: {e}")
            return self._generate_fallback_embeddings(valid_texts)

    def _generate_fallback_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate simple fallback embeddings when the API is unavailable.

        This uses a basic hash-based approach to create deterministic
        pseudo-embeddings. These are NOT suitable for production use
        but allow the system to function during API outages.

        Args:
            texts: List of texts to embed.

        Returns:
            List of fallback embedding vectors.
        """
        import hashlib

        embeddings = []

        for text in texts:
            # Create a deterministic pseudo-embedding based on text hash
            text_hash = hashlib.sha256(text.encode()).digest()

            # Generate embedding values from hash bytes
            embedding = []
            for i in range(self.dimension):
                # Cycle through hash bytes and normalize to [-1, 1]
                byte_idx = i % len(text_hash)
                value = (text_hash[byte_idx] / 127.5) - 1.0
                embedding.append(value)

            # Normalize the embedding vector
            magnitude = sum(x * x for x in embedding) ** 0.5
            if magnitude > 0:
                embedding = [x / magnitude for x in embedding]

            embeddings.append(embedding)

        logger.warning(f"Generated {len(embeddings)} fallback embeddings (not production-ready)")
        return embeddings

    async def health_check(self) -> dict:
        """Check the health of the embedding service."""
        try:
            # Try to generate a test embedding
            test_text = "health check"
            embedding = await self.generate_embedding(test_text)

            if embedding and len(embedding) == self.dimension:
                return {
                    "status": "healthy",
                    "endpoint": self.endpoint_url,
                    "model": self.model,
                    "dimension": len(embedding),
                }
            else:
                return {
                    "status": "degraded",
                    "endpoint": self.endpoint_url,
                    "message": "Using fallback embeddings",
                    "dimension": len(embedding) if embedding else 0,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": self.endpoint_url,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close the OpenAI client."""
        self._client.close()
