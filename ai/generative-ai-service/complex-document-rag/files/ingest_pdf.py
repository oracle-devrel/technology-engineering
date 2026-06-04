# pdf_ingester_v2.py
import logging, time, uuid, re, os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tiktoken
import pandas as pd

# Hard deps you likely already have:
import pdfplumber

# Optional but recommended for tables
try:
    import camelot
    _HAS_CAMELOT = True
except Exception:
    _HAS_CAMELOT = False

# Optional for embedded files
try:
    from pypdf import PdfReader
    _HAS_PYPDF = True
except Exception:
    _HAS_PYPDF = False

logger = logging.getLogger(__name__)

class PDFIngester:
    """
    PDF -> chunks with consistent semantics to XLSXIngester.
    Strategy:
      1) Detect embedded spreadsheets -> delegate to XLSXIngester
      2) Try Camelot (lattice->stream) for vector tables
      3) Fallback to pdfplumber tables
      4) Extract remaining prose blocks
      5) Batch + select + batch-rewrite (same as XLSX flow)
    """

    def __init__(self, tokenizer: str = "BAAI/bge-small-en-v1.5",
                 chunk_rewriter=None,
                 batch_size: int = 16):
        self.tokenizer_name = tokenizer
        self.chunk_rewriter = chunk_rewriter
        self.batch_size = batch_size
        self.accurate_tokenizer = tiktoken.get_encoding("cl100k_base")

        self.stats = {
            'total_chunks': 0,
            'rewritten_chunks': 0,
            'high_value_chunks': 0,
            'processing_time': 0.0,
            'extraction_time': 0.0,
            'rewriting_time': 0.0,
            'selection_time': 0.0
        }

    # ---------- Utility parity with XLSX ----------
    def _count_tokens(self, text: str) -> int:
        if not text or not text.strip():
            return 0
        return len(self.accurate_tokenizer.encode(text))

    def _is_high_value_chunk(self, text: str, metadata: Dict[str, Any]) -> int:
        # Same heuristic as your XLSX version (copy/paste with tiny tweaks)
        if len(text.strip()) < 100:
            return 0
        score = 0
        if re.search(r'\d+\.?\d*\s*(%|MW|GW|tCO2|ktCO2|MtCO2|€|\$|£|million|billion)',
                     text, re.IGNORECASE):
            score += 2
        key_terms = ['revenue','guidance','margin','cash flow','eps',
                     'emission','target','reduction','scope','net-zero',
                     'renewable','sustainability','biodiversity']
        score += min(2, sum(1 for term in key_terms if term in text.lower()))
        if text.count('|') > 5:
            score += 1
        skip_indicators = ['cover', 'disclaimer', 'notice', 'table of contents']
        if any(skip in text.lower()[:200] for skip in skip_indicators):
            score = max(0, score - 2)
        return min(5, score)

    def _batch_rows_by_token_count(self, rows: List[str], max_tokens: int = 400) -> List[List[str]]:
        chunks, current, tok = [], [], 0.0
        for row in rows:
            if not row or not row.strip():
                continue
            est = len(row.split()) * 1.3
            if tok + est > max_tokens:
                if current: chunks.append(current)
                current, tok = [row], est
            else:
                current.append(row); tok += est
        if current: chunks.append(current)
        return chunks

    def _batch_rewrite_chunks(self, chunks_to_rewrite: List[Tuple[str, Dict[str, Any], int]]):
        if not chunks_to_rewrite or not self.chunk_rewriter:
            return chunks_to_rewrite
        start = time.time()
        results = []

        # Fast path if your rewriter supports batch
        if hasattr(self.chunk_rewriter, 'rewrite_chunks_batch'):
            BATCH_SIZE = min(self.batch_size, len(chunks_to_rewrite))
            batches = [chunks_to_rewrite[i:i+BATCH_SIZE]
                       for i in range(0, len(chunks_to_rewrite), BATCH_SIZE)]

            for bidx, batch in enumerate(batches, 1):
                batch_input = [{'text': t, 'metadata': m} for (t, m, _) in batch]
                try:
                    rewritten = self.chunk_rewriter.rewrite_chunks_batch(batch_input, batch_size=BATCH_SIZE)
                except Exception as e:
                    logger.warning(f"⚠️ Batch {bidx} failed: {e}")
                    rewritten = [None]*len(batch)
                for i, (orig_text, meta, idx) in enumerate(batch):
                    new_text = rewritten[i] if i < len(rewritten) else None
                    if new_text and new_text != orig_text:
                        meta = meta.copy()
                        meta['rewritten'] = True
                        self.stats['rewritten_chunks'] += 1
                        results.append((new_text, meta, idx))
                    else:
                        results.append((orig_text, meta, idx))
        else:
            # Sequential fallback
            for (t, m, idx) in chunks_to_rewrite:
                try:
                    new_t = self.chunk_rewriter.rewrite_chunk(t, metadata=m).strip()
                except Exception as e:
                    logger.warning(f"⚠️ Rewrite failed for chunk {idx}: {e}")
                    new_t = None
                if new_t and new_t != t:
                    m = m.copy(); m['rewritten'] = True
                    self.stats['rewritten_chunks'] += 1
                    results.append((new_t, m, idx))
                else:
                    results.append((t, m, idx))
        self.stats['rewriting_time'] += time.time() - start
        return results

    # ---------- Ingestion helpers ----------
    def _find_embedded_spreadsheets(self, pdf_path: Path) -> List[Tuple[str, bytes]]:
        if not _HAS_PYPDF:
            return []
        try:
            reader = PdfReader(str(pdf_path))
            names_tree = reader.trailer.get("/Root", {}).get("/Names", {})
            efiles = names_tree.get("/EmbeddedFiles", {})
            names = efiles.get("/Names", [])
            pairs = list(zip(names[::2], names[1::2]))
            out = []
            for fname, ref in pairs:
                spec = ref.getObject()
                if "/EF" in spec and "/F" in spec["/EF"]:
                    data = spec["/EF"]["/F"].getData()
                    if str(fname).lower().endswith((".xlsx", ".xls", ".csv")):
                        out.append((str(fname), data))
            return out
        except Exception:
            return []

    def _extract_tables_with_camelot(self, pdf_path: Path, pages="all") -> List[pd.DataFrame]:
        if not _HAS_CAMELOT:
            return []
        dfs: List[pd.DataFrame] = []
        try:
            # 1) lattice first
            tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor="lattice", line_scale=40)
            dfs.extend([t.df for t in tables] if tables else [])
            # 2) stream fallback if sparse
            if not dfs:
                tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor="stream", edge_tol=200)
                dfs.extend([t.df for t in tables] if tables else [])
        except Exception as e:
            logger.info(f"Camelot failed: {e}")
        return dfs

    def _extract_tables_with_pdfplumber(self, pdf_path: Path) -> List[Tuple[pd.DataFrame, int]]:
        out = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pno, page in enumerate(pdf.pages, 1):
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
                for tbl in tables:
                    if not tbl or len(tbl) < 2:  # need header + at least 1 row
                        continue
                    df = pd.DataFrame(tbl[1:], columns=tbl[0])
                    out.append((df, pno))
        return out

    def _df_to_rows(self, df: pd.DataFrame) -> List[str]:
        # Normalize like your XLSX rows
        df = df.copy()
        df = df.replace(r'\n', ' ', regex=True)
        df.columns = [str(c).strip() for c in df.columns]
        return [ " | ".join([str(v) for v in row if (pd.notna(v) and str(v).strip())])
                 for _, row in df.iterrows() ]

    def _extract_prose_blocks(self, pdf_path: Path) -> List[Tuple[str, int]]:
        blocks = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pno, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                text = re.sub(r'[ \t]+\n', '\n', text)  # unwrap ragged whitespace
                text = re.sub(r'\n{3,}', '\n\n', text)
                if len(text.strip()) >= 40:
                    blocks.append((text.strip(), pno))
        return blocks

    # ---------- Public API ----------
    def ingest_pdf(self,
                   file_path: str | Path,
                   entity: Optional[str] = None,
                   max_rewrite_chunks: int = 30,
                   min_chunk_score: int = 2,
                   delete_original_if_rewritten: bool = True,
                   prefer_tables_first: bool = True
                   ) -> Tuple[List[Dict[str, Any]], str, List[str]]:
        """
        Returns (chunks, document_id, original_chunk_ids_to_delete)
        """
        start = time.time()
        self.stats = {k: 0.0 if 'time' in k else 0 for k in self.stats}
        all_chunks: List[Dict[str, Any]] = []
        original_chunks_to_delete: List[str] = []
        doc_id = str(uuid.uuid4())

        file = Path(file_path)
        if not file.exists() or not file.is_file() or not file.suffix.lower() == ".pdf":
            raise FileNotFoundError(f"Not a PDF: {file_path}")
        if not entity or not isinstance(entity, str):
            raise ValueError("Entity name must be provided")
        entity = entity.strip().lower()

        # 0) Router: embedded spreadsheets?
        embedded = self._find_embedded_spreadsheets(file)
        if embedded:
            # Save, then delegate to your XLSX flow for each
            from your_xlsx_module import XLSXIngester  # <-- import your class
            xlsx_ingester = XLSXIngester(chunk_rewriter=self.chunk_rewriter)
            for fname, data in embedded:
                tmp = file.with_name(f"__embedded__{fname}")
                with open(tmp, "wb") as f: f.write(data)
                x_chunks, _, _ = xlsx_ingester.ingest_xlsx(
                    tmp, entity=entity,
                    max_rewrite_chunks=max_rewrite_chunks,
                    min_chunk_score=min_chunk_score,
                    delete_original_if_rewritten=delete_original_if_rewritten
                )
                # Tag source and page unknown for embedded
                for ch in x_chunks:
                    ch['metadata']['source_pdf'] = str(file)
                    ch['metadata']['embedded_file'] = fname
                    all_chunks.append(ch)
                try: os.remove(tmp)
                except Exception: pass
            # Note: continue to extract PDF content as well (often desirable)

        # 1) Tables (Camelot → pdfplumber)
        extraction_start = time.time()
        table_chunks: List[Dict[str, Any]] = []
        if prefer_tables_first:
            dfs = self._extract_tables_with_camelot(file)
            if not dfs:
                for df, pno in self._extract_tables_with_pdfplumber(file):
                    rows = self._df_to_rows(df)
                    if not rows: continue
                    chunks = self._batch_rows_by_token_count(rows)
                    for cidx, rows_batch in enumerate(chunks):
                        content = f"Detected Table (pdfplumber)\n" + "\n".join(rows_batch)
                        meta = {
                            "page": pno,
                            "source": str(file),
                            "filename": file.name,
                            "entity": entity,
                            "document_id": doc_id,
                            "type": "pdf_table",
                            "extractor": "pdfplumber"
                        }
                        table_chunks.append({'id': f"{doc_id}_chunk_{len(all_chunks)+len(table_chunks)}",
                                             'content': content, 'metadata': meta})
            else:
                # Camelot doesn't preserve page numbers directly; we’ll mark unknown unless available on t.parsing_report
                for t_idx, df in enumerate(dfs):
                    rows = self._df_to_rows(df)
                    if not rows: continue
                    chunks = self._batch_rows_by_token_count(rows)
                    for cidx, rows_batch in enumerate(chunks):
                        content = f"Detected Table (camelot)\n" + "\n".join(rows_batch)
                        meta = {
                            "page": None,  # could be added by parsing report if needed
                            "source": str(file),
                            "filename": file.name,
                            "entity": entity,
                            "document_id": doc_id,
                            "type": "pdf_table",
                            "extractor": "camelot",
                            "table_index": t_idx
                        }
                        table_chunks.append({'id': f"{doc_id}_chunk_{len(all_chunks)+len(table_chunks)}",
                                             'content': content, 'metadata': meta})

        # 2) Prose blocks
        prose_chunks: List[Dict[str, Any]] = []
        for text, pno in self._extract_prose_blocks(file):
            meta = {
                "page": pno, "source": str(file), "filename": file.name,
                "entity": entity, "document_id": doc_id, "type": "pdf_page_text"
            }
            prose_chunks.append({'id': f"{doc_id}_chunk_{len(all_chunks)+len(table_chunks)+len(prose_chunks)}",
                                 'content': text, 'metadata': meta})

        extracted = (table_chunks + prose_chunks) if prefer_tables_first else (prose_chunks + table_chunks)
        all_chunks.extend(extracted)
        self.stats['extraction_time'] = time.time() - extraction_start
        self.stats['total_chunks'] = len(all_chunks)

        # 3) Smart selection + rewriting (same semantics as XLSX)
        if self.chunk_rewriter and max_rewrite_chunks > 0 and all_chunks:
            # score
            selection_start = time.time()
            scored = []
            for i, ch in enumerate(all_chunks):
                s = self._is_high_value_chunk(ch['content'], ch['metadata'])
                if s >= min_chunk_score:
                    scored.append((ch['content'], ch['metadata'], i, s))
                    self.stats['high_value_chunks'] += 1
            scored.sort(key=lambda x: x[3], reverse=True)
            to_rewrite = [(t, m, idx) for (t, m, idx, _) in scored[:max_rewrite_chunks]]
            self.stats['selection_time'] = time.time() - selection_start

            # rewrite
            rewritten = self._batch_rewrite_chunks(to_rewrite)
            for new_text, new_meta, original_idx in rewritten:
                if new_meta.get('rewritten'):
                    original_id = all_chunks[original_idx]['id']
                    if delete_original_if_rewritten:
                        # replace in place but mark original id for vector-store deletion
                        original_chunks_to_delete.append(original_id)
                    new_id = f"{original_id}_rewritten"
                    all_chunks[original_idx]['id'] = new_id
                    all_chunks[original_idx]['content'] = new_text
                    all_chunks[original_idx]['metadata'] = {**all_chunks[original_idx]['metadata'], **new_meta,
                                                            "original_chunk_id": original_id}

        self.stats['processing_time'] = time.time() - start
        logger.info(f"✅ PDF processed: {file.name} — chunks: {len(all_chunks)}; "
                    f"extract {self.stats['extraction_time']:.2f}s; "
                    f"rewrite {self.stats['rewriting_time']:.2f}s")

        return all_chunks, doc_id, original_chunks_to_delete
