from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import uuid
import time
import re
import tiktoken
import pdfplumber
import logging

logger = logging.getLogger(__name__)

class PDFIngester:
    def __init__(self, tokenizer: str = "BAAI/bge-small-en-v1.5", chunk_rewriter=None):
        self.chunk_rewriter = chunk_rewriter
        self.accurate_tokenizer = tiktoken.get_encoding("cl100k_base")
        self.tokenizer_name = tokenizer

        self.stats = {
            'total_chunks': 0,
            'rewritten_chunks': 0,
            'processing_time': 0,
            'rewriting_time': 0
        }

        logger.info("📄 PDF processor initialized")

    def _count_tokens(self, text: str) -> int:
        if not text or not text.strip():
            return 0
        return len(self.accurate_tokenizer.encode(text))

    def _should_rewrite(self, text: str) -> bool:
        if not text.strip() or self._count_tokens(text) < 120:
            return False

        pipe_count = text.count('|')
        number_ratio = sum(c.isdigit() for c in text) / len(text) if text else 0
        line_count = len(text.splitlines())

        is_tabular = (pipe_count > 10 or number_ratio > 0.3 or line_count > 20)
        messy = 'nan' in text.lower() or 'null' in text.lower()
        sentence_count = len([s for s in text.split('.') if s.strip()])
        is_prose = sentence_count > 3 and pipe_count < 5

        return (is_tabular or messy) and not is_prose

    def _rewrite_chunk(self, text: str, metadata: Dict[str, Any]) -> str:
        if not self.chunk_rewriter:
            return text
        try:
            rewritten = self.chunk_rewriter.rewrite_chunk(text, metadata=metadata).strip()
            if rewritten:
                self.stats['rewritten_chunks'] += 1
                return rewritten
        except Exception as e:
            logger.warning(f"⚠️ Rewrite failed: {e}")
        return text

    def process_pdf(
        self, 
        file_path: str | Path, 
        entity: Optional[str] = None,
        max_rewrite_chunks: int = 100
    ) -> Tuple[List[Dict[str, Any]], str]:
        start_time = time.time()
        self.stats = {
            'total_chunks': 0,
            'rewritten_chunks': 0,
            'processing_time': 0,
            'rewriting_time': 0
        }
        all_chunks = []
        rewrite_candidates = []
        document_id = str(uuid.uuid4())

        # -------- 1. Validate Inputs --------
        try:
            file = Path(file_path)
            if not file.exists() or not file.is_file():
                raise FileNotFoundError(f"File not found: {file_path}")
            if not str(file).lower().endswith(('.pdf',)):
                raise ValueError(f"File must be a PDF: {file_path}")
        except Exception as e:
            logger.error(f"❌ Error opening file: {e}")
            return [], document_id

        if not entity or not isinstance(entity, str):
            logger.error("❌ Entity name must be provided as a non-empty string when ingesting a PDF file.")
            return [], document_id
        entity = entity.strip().lower()

        logger.info(f"📄 Processing {file.name}")

        # -------- 2. Main Extraction --------
        try:
            with pdfplumber.open(file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract text from page {page_num+1}: {e}")
                        continue

                    if not text or len(text.strip()) < 50:
                        logger.debug(f"Skipping short/empty page {page_num+1}")
                        continue

                    metadata = {
                        "page": page_num + 1,
                        "source": str(file),
                        "filename": file.name,
                        "entity": entity,
                        "document_id": document_id,
                        "type": "pdf_page"
                    }

                    self.stats['total_chunks'] += 1

                    if self._should_rewrite(text):
                        rewrite_candidates.append((text, metadata))
                    else:
                        all_chunks.append({"content": text.strip(), "metadata": metadata})
        except Exception as e:
            logger.error(f"❌ PDF read error: {e}")
            return [], document_id

        # -------- 3. Rewrite Candidates (if needed) --------
        rewritten_chunks = []
        try:
            if self.chunk_rewriter and rewrite_candidates:
                logger.info(f"🧠 Rewriting {min(len(rewrite_candidates), max_rewrite_chunks)} of {len(rewrite_candidates)} chunks")
                rewrite_candidates = rewrite_candidates[:max_rewrite_chunks]
                for text, metadata in rewrite_candidates:
                    rewritten = self._rewrite_chunk(text, metadata)
                    metadata = dict(metadata)  # make a copy for safety
                    metadata["rewritten"] = True
                    rewritten_chunks.append({"content": rewritten, "metadata": metadata})
            else:
                rewritten_chunks = [{"content": text, "metadata": metadata} for text, metadata in rewrite_candidates]
        except Exception as e:
            logger.warning(f"⚠️ Error rewriting chunks: {e}")
            for text, metadata in rewrite_candidates:
                rewritten_chunks.append({"content": text, "metadata": metadata})

        all_chunks.extend(rewritten_chunks)

        # -------- 4. Finalize IDs and Metadata --------
        try:
            for i, chunk in enumerate(all_chunks):
                chunk["id"] = f"{document_id}_chunk_{i}"
                chunk.setdefault("metadata", {})
                chunk["metadata"]["document_id"] = document_id
        except Exception as e:
            logger.warning(f"⚠️ Error finalizing chunk IDs: {e}")

        self.stats['processing_time'] = time.time() - start_time
        logger.info(f"✅ PDF processing complete in {self.stats['processing_time']:.2f}s — Total: {len(all_chunks)}")

        return all_chunks, document_id
