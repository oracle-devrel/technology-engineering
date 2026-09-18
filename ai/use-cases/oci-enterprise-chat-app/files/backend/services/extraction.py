"""Local extraction service for extracting parameters from documents using regex patterns."""

import logging
import re
import time

from models.document import ExtractedParameter, ExtractionResult

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Exception raised for extraction-related errors."""

    pass


class ExtractionService:
    """Service for extracting parameters from documents using local regex patterns."""

    def __init__(self) -> None:
        """Initialize the extraction service."""
        pass

    async def extract_parameters(
        self, document_text: str, document_id: str | None = None
    ) -> ExtractionResult:
        """Extract parameters from document text using regex patterns.

        Args:
            document_text: The text content of the document.
            document_id: Optional document ID for logging.

        Returns:
            ExtractionResult with extracted parameters.
        """
        start_time = time.time()

        if not document_text.strip():
            return ExtractionResult(
                parameters=[],
                processing_time_ms=0,
                error_message="Document text is empty",
            )

        try:
            parameters = self._extract(document_text)
            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"Extracted {len(parameters)} parameters from document "
                f"{document_id or 'unknown'} in {processing_time:.2f}ms"
            )

            return ExtractionResult(
                parameters=parameters,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error during extraction: {e}")
            return ExtractionResult(
                parameters=[],
                processing_time_ms=processing_time,
                error_message=f"Extraction failed: {str(e)}",
            )

    def _build_page_index(self, document_text: str) -> list[tuple[int, int, int]]:
        """Build an index mapping character offsets to page numbers.

        The extracted text uses '--- Page N ---' markers inserted by pdfplumber.
        This method finds each marker and returns a list of (start, end, page_num)
        tuples so we can look up which page a given character offset belongs to.

        Args:
            document_text: The full document text with page markers.

        Returns:
            Sorted list of (page_start_offset, page_end_offset, page_number).
        """
        page_marker_pattern = r"--- Page (\d+) ---"
        markers = list(re.finditer(page_marker_pattern, document_text))

        if not markers:
            # No page markers found — treat entire text as page 1
            return [(0, len(document_text), 1)]

        pages: list[tuple[int, int, int]] = []
        for i, marker in enumerate(markers):
            page_num = int(marker.group(1))
            page_start = marker.end()
            page_end = markers[i + 1].start() if i + 1 < len(markers) else len(document_text)
            pages.append((page_start, page_end, page_num))

        return pages

    def _get_page_for_offset(
        self, offset: int, page_index: list[tuple[int, int, int]]
    ) -> int | None:
        """Return the page number for a given character offset.

        Args:
            offset: Character offset in the document text.
            page_index: Page index built by _build_page_index.

        Returns:
            1-based page number, or None if not found.
        """
        for page_start, page_end, page_num in page_index:
            if page_start <= offset < page_end:
                return page_num
        return None

    def _extract(self, document_text: str) -> list[ExtractedParameter]:
        """Extract parameters from document text using regex patterns.

        Args:
            document_text: The text content of the document.

        Returns:
            List of extracted parameters.
        """
        parameters = []
        page_index = self._build_page_index(document_text)

        # Date patterns
        date_patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
            r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, document_text, re.IGNORECASE):
                parameters.append(
                    ExtractedParameter(
                        name="Date",
                        value=match.group(1),
                        confidence=0.7,
                        source_page=self._get_page_for_offset(match.start(), page_index),
                        source_text=document_text[
                            max(0, match.start() - 30) : match.end() + 30
                        ],
                    )
                )

        # Money/Amount patterns
        money_patterns = [
            r"\$[\d,]+\.?\d*",
            r"USD\s*[\d,]+\.?\d*",
            r"[\d,]+\.?\d*\s*(?:dollars|USD)",
        ]

        for pattern in money_patterns:
            for match in re.finditer(pattern, document_text, re.IGNORECASE):
                parameters.append(
                    ExtractedParameter(
                        name="Amount",
                        value=match.group(0),
                        confidence=0.8,
                        source_page=self._get_page_for_offset(match.start(), page_index),
                        source_text=document_text[
                            max(0, match.start() - 30) : match.end() + 30
                        ],
                    )
                )

        # Email patterns
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        for match in re.finditer(email_pattern, document_text):
            parameters.append(
                ExtractedParameter(
                    name="Email",
                    value=match.group(0),
                    confidence=0.95,
                    source_page=self._get_page_for_offset(match.start(), page_index),
                    source_text=document_text[
                        max(0, match.start() - 30) : match.end() + 30
                    ],
                )
            )

        # Phone patterns
        phone_patterns = [
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            r"\(\d{3}\)\s*\d{3}[-.]?\d{4}",
            r"\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}",
        ]

        for pattern in phone_patterns:
            for match in re.finditer(pattern, document_text):
                parameters.append(
                    ExtractedParameter(
                        name="Phone Number",
                        value=match.group(0),
                        confidence=0.85,
                        source_page=self._get_page_for_offset(match.start(), page_index),
                        source_text=document_text[
                            max(0, match.start() - 30) : match.end() + 30
                        ],
                    )
                )

        # Percentage patterns
        percentage_pattern = r"\b\d+\.?\d*\s*%"
        for match in re.finditer(percentage_pattern, document_text):
            parameters.append(
                ExtractedParameter(
                    name="Percentage",
                    value=match.group(0),
                    confidence=0.9,
                    source_page=self._get_page_for_offset(match.start(), page_index),
                    source_text=document_text[
                        max(0, match.start() - 30) : match.end() + 30
                    ],
                )
            )

        # Remove duplicates based on value
        seen_values = set()
        unique_parameters = []
        for param in parameters:
            if param.value not in seen_values:
                seen_values.add(param.value)
                unique_parameters.append(param)

        return unique_parameters[:50]  # Limit to 50 parameters
