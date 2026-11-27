"""
Document chunking utilities for splitting text into smaller segments.
Supports various chunking strategies optimized for RAG applications.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk."""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "index": self.index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata or {},
        }


class DocumentChunker:
    """
    Splits documents into chunks suitable for embedding and retrieval.

    Supports multiple chunking strategies:
    - Fixed size with overlap
    - Sentence-based
    - Paragraph-based
    - Semantic (heading-aware)
    """

    DEFAULT_CHUNK_SIZE = 1000  # Characters
    DEFAULT_CHUNK_OVERLAP = 200  # Characters
    MIN_CHUNK_SIZE = 100  # Minimum characters per chunk

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        strategy: str = "recursive",
    ):
        """
        Initialize the document chunker.

        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of overlapping characters between chunks.
            strategy: Chunking strategy ('fixed', 'sentence', 'paragraph', 'recursive').
        """
        self.chunk_size = max(chunk_size, self.MIN_CHUNK_SIZE)
        self.chunk_overlap = min(chunk_overlap, chunk_size // 2)
        self.strategy = strategy

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """
        Split text into chunks using the configured strategy.

        Args:
            text: The text to chunk.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            List of Chunk objects.
        """
        if not text or not text.strip():
            return []

        # Clean the text
        text = self._clean_text(text)

        if self.strategy == "fixed":
            return self._chunk_fixed(text, metadata)
        elif self.strategy == "sentence":
            return self._chunk_by_sentence(text, metadata)
        elif self.strategy == "paragraph":
            return self._chunk_by_paragraph(text, metadata)
        else:  # recursive (default)
            return self._chunk_recursive(text, metadata)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _chunk_fixed(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """Split text into fixed-size chunks with overlap."""
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find a good break point (space, newline, punctuation)
            if end < len(text):
                # Look for a break point near the end
                break_point = self._find_break_point(text, end)
                if break_point > start:
                    end = break_point

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata=metadata,
                    )
                )
                index += 1

            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def _chunk_by_sentence(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """Split text by sentences, combining into chunks of target size."""
        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0
        index = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                end_char = start_char + len(chunk_text)

                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start_char,
                        end_char=end_char,
                        metadata=metadata,
                    )
                )
                index += 1

                # Start new chunk with overlap (last sentence)
                overlap_sentences = current_chunk[-1:] if self.chunk_overlap > 0 else []
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
                start_char = end_char - (len(overlap_sentences[0]) if overlap_sentences else 0)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=index,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=metadata,
                )
            )

        return chunks

    def _chunk_by_paragraph(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """Split text by paragraphs, combining small paragraphs."""
        # Split by double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0
        index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            # If single paragraph is too large, split it
            if para_length > self.chunk_size:
                # First, save any accumulated content
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(
                        Chunk(
                            content=chunk_text,
                            index=index,
                            start_char=start_char,
                            end_char=start_char + len(chunk_text),
                            metadata=metadata,
                        )
                    )
                    index += 1
                    start_char += len(chunk_text) + 2
                    current_chunk = []
                    current_length = 0

                # Split large paragraph with fixed chunking
                para_chunks = self._chunk_fixed(para, metadata)
                for pc in para_chunks:
                    pc.index = index
                    pc.start_char += start_char
                    pc.end_char += start_char
                    chunks.append(pc)
                    index += 1

                start_char += para_length + 2
                continue

            # If adding this paragraph would exceed chunk size
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                        metadata=metadata,
                    )
                )
                index += 1
                start_char += len(chunk_text) + 2
                current_chunk = []
                current_length = 0

            current_chunk.append(para)
            current_length += para_length

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=index,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=metadata,
                )
            )

        return chunks

    def _chunk_recursive(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """
        Recursively split text using a hierarchy of separators.

        This is the most intelligent chunking strategy, trying to preserve
        semantic boundaries in the document.
        """
        # Hierarchy of separators from most to least significant
        separators = [
            "\n\n\n",  # Multiple blank lines (sections)
            "\n\n",    # Paragraphs
            "\n",      # Lines
            ". ",      # Sentences
            "? ",      # Questions
            "! ",      # Exclamations
            "; ",      # Semicolons
            ", ",      # Commas
            " ",       # Words
        ]

        chunks = self._recursive_split(text, separators, metadata)

        # Re-index chunks
        for i, chunk in enumerate(chunks):
            chunk.index = i

        return chunks

    def _recursive_split(
        self,
        text: str,
        separators: list[str],
        metadata: Optional[dict] = None,
    ) -> list[Chunk]:
        """Recursively split text using separators hierarchy."""
        if len(text) <= self.chunk_size:
            if text.strip():
                return [
                    Chunk(
                        content=text.strip(),
                        index=0,
                        start_char=0,
                        end_char=len(text),
                        metadata=metadata,
                    )
                ]
            return []

        # Find the first separator that exists in text
        separator = None
        for sep in separators:
            if sep in text:
                separator = sep
                break

        if separator is None:
            # No separator found, use fixed chunking
            return self._chunk_fixed(text, metadata)

        # Split by separator
        parts = text.split(separator)
        chunks = []
        current_parts = []
        current_length = 0
        start_char = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            part_length = len(part)

            # If single part is too large, recursively split it
            if part_length > self.chunk_size:
                # First, save any accumulated content
                if current_parts:
                    chunk_text = separator.join(current_parts)
                    chunks.append(
                        Chunk(
                            content=chunk_text,
                            index=len(chunks),
                            start_char=start_char,
                            end_char=start_char + len(chunk_text),
                            metadata=metadata,
                        )
                    )
                    start_char += len(chunk_text) + len(separator)
                    current_parts = []
                    current_length = 0

                # Recursively split with remaining separators
                remaining_seps = separators[separators.index(separator) + 1:]
                if remaining_seps:
                    sub_chunks = self._recursive_split(part, remaining_seps, metadata)
                    for sc in sub_chunks:
                        sc.start_char += start_char
                        sc.end_char += start_char
                        chunks.append(sc)
                else:
                    # Fallback to fixed chunking
                    sub_chunks = self._chunk_fixed(part, metadata)
                    for sc in sub_chunks:
                        sc.start_char += start_char
                        sc.end_char += start_char
                        chunks.append(sc)

                start_char += part_length + len(separator)
                continue

            # If adding this part would exceed chunk size
            if current_length + part_length + len(separator) > self.chunk_size and current_parts:
                chunk_text = separator.join(current_parts)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=len(chunks),
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                        metadata=metadata,
                    )
                )
                start_char += len(chunk_text) + len(separator)

                # Add overlap
                overlap_parts = []
                overlap_length = 0
                for p in reversed(current_parts):
                    if overlap_length + len(p) <= self.chunk_overlap:
                        overlap_parts.insert(0, p)
                        overlap_length += len(p)
                    else:
                        break

                current_parts = overlap_parts + [part]
                current_length = sum(len(p) for p in current_parts)
            else:
                current_parts.append(part)
                current_length += part_length + len(separator)

        # Don't forget the last chunk
        if current_parts:
            chunk_text = separator.join(current_parts)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=metadata,
                )
            )

        return chunks

    def _find_break_point(self, text: str, position: int, window: int = 50) -> int:
        """Find a good break point near the given position."""
        # Look for break points in a window around the position
        start = max(0, position - window)
        end = min(len(text), position + window)

        # Priority: paragraph > sentence > word
        best_pos = position

        # Look for paragraph break
        for i in range(position, start, -1):
            if text[i:i+2] == '\n\n':
                return i + 2

        # Look for sentence end
        for i in range(position, start, -1):
            if text[i] in '.!?' and i + 1 < len(text) and text[i + 1] == ' ':
                return i + 2

        # Look for word break
        for i in range(position, start, -1):
            if text[i] == ' ':
                return i + 1

        return position


def chunk_document(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    strategy: str = "recursive",
    metadata: Optional[dict] = None,
) -> list[dict]:
    """
    Convenience function to chunk a document.

    Args:
        text: The document text to chunk.
        chunk_size: Target size for each chunk.
        chunk_overlap: Overlap between chunks.
        strategy: Chunking strategy.
        metadata: Optional metadata for chunks.

    Returns:
        List of chunk dictionaries.
    """
    chunker = DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy,
    )

    chunks = chunker.chunk_text(text, metadata)
    return [chunk.to_dict() for chunk in chunks]
