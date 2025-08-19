#!/usr/bin/env python3
"""
Fast XLSX Processor - Optimized for speed without sacrificing quality
Combines best practices from both implementations
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json, uuid, re, warnings, argparse, time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import tiktoken
from transformers import AutoTokenizer
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class XLSXIngester:
    """Fast XLSX processor - optimized for demo speed without sacrificing quality"""
    
    def __init__(self, tokenizer: str = "BAAI/bge-small-en-v1.5", 
                 chunk_rewriter=None, batch_size: int = 16):  # Larger batch size
        """Initialize processor with speed optimizations"""
        self.tokenizer_name = tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        self.chunk_rewriter = chunk_rewriter
        self.batch_size = batch_size
        
        # Use tiktoken for accurate token counting
        self.accurate_tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Performance tracking
        self.stats = {
            'total_chunks': 0,
            'rewritten_chunks': 0,
            'high_value_chunks': 0,
            'processing_time': 0.0,
            'extraction_time': 0.0,
            'rewriting_time': 0.0,
            'selection_time': 0.0
        }
        
        logger.info("⚡ Fast XLSX processor initialized")
    
    def _count_tokens(self, text: str) -> int:
        """Accurate token counting using tiktoken"""
        if not text or not text.strip():
            return 0
        return len(self.accurate_tokenizer.encode(text))
    
    def _is_high_value_chunk(self, text: str, metadata: Dict[str, Any]) -> int:
        """
        Score chunks by value (0-5) to prioritize rewriting.
        Higher scores = more valuable for rewriting.
        """
        if len(text.strip()) < 100:
            return 0
        
        score = 0
        
        # High value: Contains metrics with units (most important)
        if re.search(r'\d+\.?\d*\s*(%|MW|GW|tCO2|ktCO2|MtCO2|€|$|£|million|billion)', text, re.IGNORECASE):
            score += 2
        
        # High value: Contains key ESG terms
        key_terms = ['emission', 'target', 'goal', 'reduction', 'scope', 'carbon', 
                     'net-zero', 'renewable', 'sustainability', 'biodiversity']
        term_count = sum(1 for term in key_terms if term in text.lower())
        if term_count > 0:
            score += min(2, term_count)  # Cap at 2 points
        
        # Medium value: Contains structured data (tables)
        if text.count('|') > 5:
            score += 1
        
        # Skip known low-value content
        skip_indicators = ['cover', 'disclaimer', 'notice', 'page', 'table of contents']
        if any(skip in text.lower()[:200] for skip in skip_indicators):
            score = max(0, score - 2)
        
        return min(5, score)  # Cap at 5
    
    def _extract_section_titles(self, df: pd.DataFrame) -> List[str]:
        """Fast extraction of section titles from dataframe"""
        titles = []
        for idx, row in df.head(5).iterrows():  # Only check first 5 rows
            row_text = ' '.join(str(val) for val in row if pd.notna(val))
            if row_text and not any(char.isdigit() for char in row_text[:20]):
                titles.append(row_text.strip()[:100])  # Limit length
        return titles
    
    def _batch_rows_by_token_count(self, rows: List[str], max_tokens: int = 400) -> List[List[str]]:
        """Batch rows by token count - optimized version"""
        chunks = []
        current_chunk = []
        token_count = 0
        
        for row in rows:
            if not row or not row.strip():
                continue
            
            # Quick token estimate (faster than tiktoken for batching)
            estimated_tokens = len(row.split()) * 1.3  # Rough estimate
            
            if token_count + estimated_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [row]
                token_count = estimated_tokens
            else:
                current_chunk.append(row)
                token_count += estimated_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _batch_rewrite_chunks(self, chunks_to_rewrite: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
        """Fast parallel batch rewriting"""
        if not chunks_to_rewrite or not self.chunk_rewriter:
            return chunks_to_rewrite
        
        start_time = time.time()
        results = []
        
        # Check if batch rewriting is supported
        if hasattr(self.chunk_rewriter, 'rewrite_chunks_batch'):
            logger.info(f"🚀 Fast batch rewriting for {len(chunks_to_rewrite)} chunks")
            
            # Larger batch size for fewer API calls
            BATCH_SIZE = min(16, len(chunks_to_rewrite))
            MAX_WORKERS = 2  # Limited parallelism to avoid rate limits
            
            # Split into batches
            batches = [
                chunks_to_rewrite[i:i + BATCH_SIZE]
                for i in range(0, len(chunks_to_rewrite), BATCH_SIZE)
            ]
            
            logger.info(f"📦 Processing {len(batches)} batches of size {BATCH_SIZE}")
            
            def process_batch(batch_idx: int, batch: List[Tuple[str, Dict[str, Any]]]):
                batch_input = [{'text': text, 'metadata': metadata} for text, metadata in batch]
                try:
                    logger.info(f"  Processing batch {batch_idx + 1}/{len(batches)}")
                    rewritten_texts = self.chunk_rewriter.rewrite_chunks_batch(batch_input, batch_size=BATCH_SIZE)
                    
                    batch_result = []
                    for i, (original_text, metadata) in enumerate(batch):
                        rewritten_text = rewritten_texts[i] if i < len(rewritten_texts) else None
                        if rewritten_text and rewritten_text != original_text:
                            metadata = metadata.copy()
                            metadata["rewritten"] = True
                            self.stats['rewritten_chunks'] += 1
                            batch_result.append((rewritten_text, metadata))
                        else:
                            batch_result.append((original_text, metadata))
                    
                    logger.info(f"  ✅ Batch {batch_idx + 1} complete")
                    return batch_result
                except Exception as e:
                    logger.warning(f"  ⚠️ Batch {batch_idx + 1} failed: {e}")
                    return batch
            
            # Process with limited parallelism
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_batch = {
                    executor.submit(process_batch, idx, batch): batch 
                    for idx, batch in enumerate(batches)
                }
                for future in as_completed(future_to_batch):
                    results.extend(future.result())
            
            self.stats['rewriting_time'] = time.time() - start_time
            logger.info(f"✅ Rewriting completed in {self.stats['rewriting_time']:.2f}s")
            return results
        else:
            # Fallback to sequential processing
            logger.info(f"🔄 Sequential rewriting for {len(chunks_to_rewrite)} chunks")
            for text, metadata in chunks_to_rewrite:
                try:
                    rewritten = self.chunk_rewriter.rewrite_chunk(text, metadata=metadata).strip()
                    if rewritten:
                        metadata = metadata.copy()
                        metadata["rewritten"] = True
                        self.stats['rewritten_chunks'] += 1
                        results.append((rewritten, metadata))
                    else:
                        results.append((text, metadata))
                except Exception as e:
                    logger.warning(f"Failed to rewrite chunk: {e}")
                    results.append((text, metadata))
            
            self.stats['rewriting_time'] = time.time() - start_time
            return results
    
    def ingest_xlsx(
        self,
        file_path: str | Path,
        entity: Optional[str] = None,
        max_rewrite_chunks: int = 30,  # Reasonable default
        min_chunk_score: int = 2  # Only rewrite chunks with score >= 2
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Fast XLSX processing with smart chunk selection"""
        
        start_time = time.time()
        self.stats = {
            'total_chunks': 0,
            'rewritten_chunks': 0,
            'high_value_chunks': 0,
            'processing_time': 0.0,
            'extraction_time': 0.0,
            'rewriting_time': 0.0,
            'selection_time': 0.0
        }
        all_chunks = []
        document_id = str(uuid.uuid4())
        
        # Validate inputs
        file = Path(file_path)
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not str(file).lower().endswith(('.xlsx', '.xls')):
            raise ValueError(f"File must be XLSX or XLS: {file_path}")
        
        if not entity or not isinstance(entity, str):
            raise ValueError("Entity name must be provided")
        entity = entity.strip().lower()
        
        logger.info(f"⚡ Fast processing {file.name}")
        logger.info(f"📊 Entity: {entity}")
        
        # Single-pass extraction using pandas (faster than double extraction)
        extraction_start = time.time()
        try:
            # Read all sheets at once
            dfs = pd.read_excel(file, sheet_name=None, header=None)
            
            for sheet_name, df in dfs.items():
                if df.empty:
                    continue
                
                # Skip cover/disclaimer sheets
                if any(skip in sheet_name.lower() for skip in ['cover', 'disclaimer', 'notice']):
                    logger.info(f"  Skipping sheet: {sheet_name}")
                    continue
                
                # Extract section titles (fast)
                section_titles = self._extract_section_titles(df)
                
                # Convert to text rows
                text_rows = []
                for idx, row in df.iterrows():
                    row_values = [str(val) for val in row if pd.notna(val) and str(val).strip()]
                    if row_values:
                        text_rows.append(" | ".join(row_values))
                
                # Batch into chunks
                chunks = self._batch_rows_by_token_count(text_rows)
                
                # Create chunk objects
                for chunk_idx, chunk_rows in enumerate(chunks):
                    chunk_text = "\n".join(chunk_rows)
                    
                    # Add metadata
                    full_text = f"Sheet: {sheet_name}\n"
                    if section_titles:
                        full_text += f"Sections: {' | '.join(section_titles[:3])}\n"
                    full_text += chunk_text
                    
                    metadata = {
                        "sheet": sheet_name,
                        "chunk_index": chunk_idx,
                        "source": str(file),
                        "document_id": document_id,
                        "entity": entity,
                        "filename": file.name
                    }
                    
                    chunk_obj = {
                        'id': f"{document_id}_chunk_{len(all_chunks)}",
                        'content': full_text,
                        'metadata': metadata
                    }
                    
                    all_chunks.append(chunk_obj)
                    self.stats['total_chunks'] += 1
            
            self.stats['extraction_time'] = time.time() - extraction_start
            logger.info(f"📊 Extracted {len(all_chunks)} chunks in {self.stats['extraction_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to extract chunks: {e}")
            raise
        
        # Smart chunk selection for rewriting
        selection_start = time.time()
        if self.chunk_rewriter and max_rewrite_chunks > 0:
            # Score all chunks
            scored_chunks = []
            for chunk in all_chunks:
                score = self._is_high_value_chunk(chunk['content'], chunk['metadata'])
                if score >= min_chunk_score:
                    scored_chunks.append((chunk['content'], chunk['metadata'], score))
                    self.stats['high_value_chunks'] += 1
            
            # Sort by score and take top N
            scored_chunks.sort(key=lambda x: x[2], reverse=True)
            chunks_to_rewrite = [(text, meta) for text, meta, _ in scored_chunks[:max_rewrite_chunks]]
            
            self.stats['selection_time'] = time.time() - selection_start
            logger.info(f"🎯 Selected {len(chunks_to_rewrite)} high-value chunks from {self.stats['high_value_chunks']} candidates in {self.stats['selection_time']:.2f}s")
            
            if chunks_to_rewrite:
                # Rewrite selected chunks
                rewritten = self._batch_rewrite_chunks(chunks_to_rewrite)
                
                # Create mapping for quick lookup
                rewritten_map = {}
                for text, meta in rewritten:
                    if meta.get('rewritten'):
                        key = f"{meta['sheet']}_{meta.get('chunk_index', 0)}"
                        rewritten_map[key] = text
                
                # Update original chunks with rewritten content
                for chunk in all_chunks:
                    key = f"{chunk['metadata']['sheet']}_{chunk['metadata'].get('chunk_index', 0)}"
                    if key in rewritten_map:
                        chunk['content'] = rewritten_map[key]
                        chunk['metadata']['rewritten'] = True
        
        self.stats['processing_time'] = time.time() - start_time
        
        # Final stats
        logger.info(f"\n{'='*60}")
        logger.info(f"⚡ FAST PROCESSING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"📊 Total chunks: {len(all_chunks)}")
        logger.info(f"🎯 High-value chunks: {self.stats['high_value_chunks']}")
        logger.info(f"🔥 Rewritten chunks: {self.stats['rewritten_chunks']}")
        logger.info(f"\n⏱️ TIMING BREAKDOWN:")
        logger.info(f"  Extraction:    {self.stats['extraction_time']:.2f}s")
        logger.info(f"  Selection:     {self.stats['selection_time']:.2f}s")
        logger.info(f"  Rewriting:     {self.stats['rewriting_time']:.2f}s")
        logger.info(f"  ─────────────────────")
        logger.info(f"  TOTAL TIME:    {self.stats['processing_time']:.2f}s")
        logger.info(f"  Speed:         {len(all_chunks)/self.stats['processing_time']:.1f} chunks/sec")
        logger.info(f"{'='*60}\n")
        
        return all_chunks, document_id

def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description="Optimized XLSX Processor")
    parser.add_argument("--input", required=True, help="XLSX file path")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--entity", required=True, help="Entity name")
    parser.add_argument("--max-rewrite", type=int, default=30, help="Maximum chunks to rewrite")
    parser.add_argument("--min-score", type=int, default=2, help="Minimum score for rewriting (0-5)")
    parser.add_argument("--no-rewrite", action="store_true", help="Skip chunk rewriting")
    
    args = parser.parse_args()
    
    # Initialize chunk rewriter if needed
    chunk_rewriter = None
    if not args.no_rewrite:
        try:
            from agents.agent_factory import create_agents
            from local_rag_agent import OCIModelHandler, LocalLLM
            from vector_store import EnhancedVectorStore 
            
            vector_store = EnhancedVectorStore()
            oci_handler = OCIModelHandler(config_profile="DEFAULT")
            llm = LocalLLM(oci_handler)
            agents = create_agents(llm, vector_store=vector_store)
            chunk_rewriter = agents.get("chunk_rewriter")
            
            if chunk_rewriter:
                logger.info("✅ Chunk rewriter initialized")
            else:
                logger.info("⚠️ Chunk rewriter not available")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize chunk rewriter: {e}")
    
    # Initialize processor
    processor = XLSXIngester(chunk_rewriter=chunk_rewriter)
    
    # Process file
    try:
        chunks, doc_id = processor.ingest_xlsx(
            args.input, 
            entity=args.entity,
            max_rewrite_chunks=args.max_rewrite,
            min_chunk_score=args.min_score
        )
        
        # Save results
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        result_data = {
            "document_id": doc_id,
            "chunks": chunks,
            "stats": processor.stats
        }
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {args.output}")
        
    except Exception as e:
        logger.error(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
