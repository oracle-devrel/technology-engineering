"""
Oracle 23ai Vector Store service for document embeddings.
Provides vector storage and similarity search using Oracle's AI Vector Search.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import oracledb

logger = logging.getLogger(__name__)


class OracleVectorStoreError(Exception):
    """Exception raised for Oracle vector store errors."""
    pass


class DocumentChunk:
    """Represents a document chunk with its embedding."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "metadata": self.metadata,
        }


class SearchResult:
    """Represents a vector search result."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        score: float,
        chunk_index: int = 0,
        filename: Optional[str] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.content = content
        self.score = score
        self.chunk_index = chunk_index
        self.filename = filename

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "score": self.score,
            "chunk_index": self.chunk_index,
            "filename": self.filename,
        }


class OracleVectorStore:
    """
    Oracle 23ai Vector Store for storing and searching document embeddings.

    Uses Oracle's native VECTOR data type and VECTOR_DISTANCE function
    for efficient similarity search.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        dsn: Optional[str] = None,
        wallet_dir: Optional[str] = None,
        table_name: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
    ):
        """
        Initialize Oracle Vector Store.

        Args:
            username: Database username. Defaults to ORACLE_DB_USERNAME env var.
            password: Database password. Defaults to ORACLE_DB_PASSWORD env var.
            dsn: Database DSN/TNS name. Defaults to ORACLE_DSN env var.
            wallet_dir: Path to wallet directory. Defaults to ORACLE_WALLET_DIR env var.
            table_name: Table name for vectors. Defaults to ORACLE_VECTOR_TABLE env var.
            embedding_dimension: Embedding dimension. Defaults to ORACLE_EMBEDDING_DIMENSION env var.
        """
        self.username = username or os.getenv("ORACLE_DB_USERNAME", "ADMIN")
        self.password = password or os.getenv("ORACLE_DB_PASSWORD", "")
        self.dsn = dsn or os.getenv("ORACLE_DSN", "")
        self.wallet_dir = wallet_dir or os.getenv("ORACLE_WALLET_DIR", "config/wallet")
        self.table_name = table_name or os.getenv("ORACLE_VECTOR_TABLE", "document_vectors")
        self.embedding_dimension = int(
            embedding_dimension or os.getenv("ORACLE_EMBEDDING_DIMENSION", "1536")
        )

        self._pool: Optional[oracledb.AsyncConnectionPool] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the connection pool and create tables if needed."""
        if self._initialized:
            return

        try:
            # Resolve wallet path (relative to backend directory or absolute)
            wallet_path = self.wallet_dir
            if not os.path.isabs(wallet_path):
                # Try relative to current working directory
                if not os.path.exists(wallet_path):
                    # Try relative to backend directory
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    wallet_path = os.path.join(backend_dir, self.wallet_dir)

            if not os.path.exists(wallet_path):
                raise OracleVectorStoreError(
                    f"Wallet directory not found: {self.wallet_dir}"
                )

            logger.info(f"Using wallet directory: {wallet_path}")

            # Create connection pool with wallet authentication
            # Note: create_pool_async() is synchronous in oracledb 2.x — it returns
            # an AsyncConnectionPool directly (not a coroutine).
            self._pool = oracledb.create_pool_async(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
                config_dir=wallet_path,
                wallet_location=wallet_path,
                wallet_password=None,  # Auto-login wallet (cwallet.sso)
                min=2,
                max=10,
                increment=1,
            )

            # Create tables if they don't exist
            await self._create_tables()

            self._initialized = True
            logger.info("Oracle Vector Store initialized successfully")

        except oracledb.Error as e:
            logger.error(f"Failed to initialize Oracle connection: {e}")
            raise OracleVectorStoreError(f"Database connection failed: {e}")

    async def _create_tables(self) -> None:
        """Create the vector storage tables if they don't exist."""
        async with self._get_connection() as conn:
            async with conn.cursor() as cursor:
                # Check if table exists
                await cursor.execute(
                    """
                    SELECT COUNT(*) FROM user_tables
                    WHERE table_name = UPPER(:table_name)
                    """,
                    {"table_name": self.table_name}
                )
                result = await cursor.fetchone()

                if result[0] == 0:
                    # Create the vector table
                    # Using VECTOR type with specified dimensions and FLOAT32 format
                    create_sql = f"""
                        CREATE TABLE {self.table_name} (
                            chunk_id VARCHAR2(64) PRIMARY KEY,
                            document_id VARCHAR2(64) NOT NULL,
                            chunk_index NUMBER NOT NULL,
                            content CLOB NOT NULL,
                            filename VARCHAR2(512),
                            embedding VECTOR({self.embedding_dimension}, FLOAT32),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            metadata CLOB
                        )
                    """
                    await cursor.execute(create_sql)

                    # Create index on document_id for faster lookups
                    await cursor.execute(
                        f"CREATE INDEX idx_{self.table_name}_doc_id ON {self.table_name}(document_id)"
                    )

                    # Create vector index for similarity search
                    # Using IVF (Inverted File) index for efficient approximate nearest neighbor search
                    await cursor.execute(
                        f"""
                        CREATE VECTOR INDEX idx_{self.table_name}_vec
                        ON {self.table_name}(embedding)
                        ORGANIZATION NEIGHBOR PARTITIONS
                        WITH DISTANCE COSINE
                        """
                    )

                    await conn.commit()
                    logger.info(f"Created vector table: {self.table_name}")
                else:
                    logger.info(f"Vector table already exists: {self.table_name}")

    @asynccontextmanager
    async def _get_connection(self):
        """Get a connection from the pool."""
        if self._pool is None:
            raise OracleVectorStoreError("Vector store not initialized. Call initialize() first.")

        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def store_chunks(
        self,
        document_id: str,
        chunks: list[dict],
        filename: Optional[str] = None,
    ) -> int:
        """
        Store document chunks with their embeddings.

        Args:
            document_id: The document identifier.
            chunks: List of dicts with 'content', 'embedding', and optional 'metadata'.
            filename: Optional filename for reference.

        Returns:
            Number of chunks stored.
        """
        if not self._initialized:
            await self.initialize()

        async with self._get_connection() as conn:
            async with conn.cursor() as cursor:
                stored_count = 0

                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_{idx}"
                    content = chunk.get("content", "")
                    embedding = chunk.get("embedding", [])
                    metadata = chunk.get("metadata")

                    if not embedding:
                        logger.warning(f"Skipping chunk {chunk_id}: no embedding")
                        continue

                    try:
                        # Convert embedding list to Oracle VECTOR format
                        # Oracle expects the vector as a string representation
                        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

                        await cursor.execute(
                            f"""
                            MERGE INTO {self.table_name} t
                            USING (SELECT :chunk_id AS chunk_id FROM dual) s
                            ON (t.chunk_id = s.chunk_id)
                            WHEN MATCHED THEN
                                UPDATE SET
                                    content = :content,
                                    embedding = TO_VECTOR(:embedding),
                                    filename = :filename,
                                    metadata = :metadata
                            WHEN NOT MATCHED THEN
                                INSERT (chunk_id, document_id, chunk_index, content, embedding, filename, metadata)
                                VALUES (:chunk_id, :document_id, :chunk_index, :content, TO_VECTOR(:embedding), :filename, :metadata)
                            """,
                            {
                                "chunk_id": chunk_id,
                                "document_id": document_id,
                                "chunk_index": idx,
                                "content": content,
                                "embedding": embedding_str,
                                "filename": filename,
                                "metadata": str(metadata) if metadata else None,
                            }
                        )
                        stored_count += 1

                    except oracledb.Error as e:
                        logger.error(f"Failed to store chunk {chunk_id}: {e}")
                        continue

                await conn.commit()
                logger.info(f"Stored {stored_count} chunks for document {document_id}")
                return stored_count

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_ids: Optional[list[str]] = None,
        score_threshold: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search for similar chunks using vector similarity.

        Args:
            query_embedding: The query embedding vector.
            top_k: Number of results to return.
            document_ids: Optional list of document IDs to filter by.
            score_threshold: Minimum similarity score (0-1, higher is better).

        Returns:
            List of SearchResult objects ordered by similarity.
        """
        if not self._initialized:
            await self.initialize()

        results = []

        async with self._get_connection() as conn:
            async with conn.cursor() as cursor:
                # Convert query embedding to Oracle VECTOR format
                embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

                # Build the query with optional document filter
                document_params = {
                    f"document_{index}": document_id
                    for index, document_id in enumerate(document_ids or [])
                }
                doc_filter = (
                    "AND document_id IN (" + ",".join(f":{key}" for key in document_params) + ")"
                    if document_params else ""
                )

                # Use VECTOR_DISTANCE for similarity search
                # COSINE distance returns 0 for identical vectors, 2 for opposite
                # We convert to similarity score: 1 - (distance / 2)
                query = f"""
                    SELECT
                        chunk_id,
                        document_id,
                        content,
                        chunk_index,
                        filename,
                        (1 - (VECTOR_DISTANCE(embedding, TO_VECTOR(:query_vec), COSINE) / 2)) as similarity
                    FROM {self.table_name}
                    WHERE embedding IS NOT NULL
                    {doc_filter}
                    ORDER BY VECTOR_DISTANCE(embedding, TO_VECTOR(:query_vec), COSINE)
                    FETCH FIRST :top_k ROWS ONLY
                """

                await cursor.execute(
                    query,
                    {
                        "query_vec": embedding_str,
                        "top_k": top_k,
                        **document_params,
                    }
                )

                rows = await cursor.fetchall()

                for row in rows:
                    chunk_id, document_id, content, chunk_index, filename, similarity = row

                    # Filter by score threshold
                    if similarity >= score_threshold:
                        results.append(
                            SearchResult(
                                chunk_id=chunk_id,
                                document_id=document_id,
                                content=content if isinstance(content, str) else content.read(),
                                score=float(similarity),
                                chunk_index=chunk_index or 0,
                                filename=filename,
                            )
                        )

        logger.info(f"Vector search returned {len(results)} results")
        return results

    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: The document identifier.

        Returns:
            Number of chunks deleted.
        """
        if not self._initialized:
            await self.initialize()

        async with self._get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE document_id = :document_id",
                    {"document_id": document_id}
                )
                deleted_count = cursor.rowcount
                await conn.commit()

                logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
                return deleted_count

    async def get_document_chunks(self, document_id: str) -> list[dict]:
        """
        Get all chunks for a document.

        Args:
            document_id: The document identifier.

        Returns:
            List of chunk dictionaries.
        """
        if not self._initialized:
            await self.initialize()

        chunks = []

        async with self._get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT chunk_id, chunk_index, content, filename, metadata
                    FROM {self.table_name}
                    WHERE document_id = :document_id
                    ORDER BY chunk_index
                    """,
                    {"document_id": document_id}
                )

                rows = await cursor.fetchall()

                for row in rows:
                    chunk_id, chunk_index, content, filename, metadata = row
                    chunks.append({
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,
                        "content": content if isinstance(content, str) else content.read(),
                        "filename": filename,
                        "metadata": metadata,
                    })

        return chunks

    async def health_check(self) -> dict:
        """Check the health of the Oracle vector store connection."""
        try:
            if not self._initialized:
                await self.initialize()

            async with self._get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1 FROM dual")
                    await cursor.fetchone()

                    # Get table stats
                    await cursor.execute(
                        f"SELECT COUNT(*) FROM {self.table_name}"
                    )
                    count = (await cursor.fetchone())[0]

            return {
                "status": "healthy",
                "table": self.table_name,
                "total_chunks": count,
                "embedding_dimension": self.embedding_dimension,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("Oracle Vector Store connection closed")
