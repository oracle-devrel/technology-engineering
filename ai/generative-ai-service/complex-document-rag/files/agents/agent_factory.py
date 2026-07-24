import os

# MUST be the first thing in this module, before any third-party import. langchain
# pulls in transformers transitively, and transformers emits its "None of PyTorch,
# TensorFlow >= 2.0, or Flax have been found" banner *during* import — so these have
# to be set before that first import line runs, not merely before we use it.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

from typing import List, Dict, Any, ClassVar, Optional, Set
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from docx import Document
import logging
import warnings
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import re, unicodedata
from agents.report_writer_agent import ReportWriterAgent, SectionWriterAgent
from contracts import Chunk, PlanSection, Plan, SectionDraft, ReportResult

import re, json, unicodedata, logging
from typing import Any, Optional

# Try to use demo logger if available, fallback to standard logging
try:
    from utils.demo_logger import demo_logger, setup_demo_logging
    logger = setup_demo_logging()
    DEMO_MODE = True
except ImportError:
    # Fallback to standard logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    DEMO_MODE = False

def _verbose() -> bool:
    """Full logging detail, for debugging rather than presenting."""
    return os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes") or \
        os.environ.get("RAG_VERBOSE", "").lower() in ("1", "true", "yes")


# transformers is no longer imported at all. It was pulled in solely to call
# set_verbosity_error() — but the import itself emits the "None of PyTorch,
# TensorFlow >= 2.0, or Flax have been found" banner, so importing it to silence it
# was self-defeating. Nothing here uses the library.
warnings.filterwarnings("ignore", message="Setting `pad_token_id` to `eos_token_id`")



class UniversalJSONCleaner:
    """Unified JSON cleaning utility for all agents"""

    DEBUG_JSON_LOGGING = True

    @staticmethod
    def _normalize_quotes_and_symbols(text: str) -> str:
        replacements = {
            "“": '"', "”": '"', "‘": "'", "’": "'",
            "–": "-", "—": "-", "…": "...",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    @staticmethod
    def _normalize_quotes(text: str) -> str:
        replacements = {
            '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
            '\u2032': "'", '\u2033': '"', '\u00ab': '"', '\u00bb': '"',
            '\u0060': "'", '\u00b4': "'",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    @staticmethod
    def _guess_entities_from_json(text):
        # crude guess, picks up "Aelwyn", "Elinexa", "Apple", etc.
        return list(set(re.findall(r'\b([A-Z][a-zA-Z0-9]{2,})\b', text)))

    @staticmethod
    def _fix_broken_possessives(text, entities):
        # For each entity, replace Foo"s with Foo's.
        # Match case-insensitively: entities arrive lowercased from the UI
        # (entity.strip().lower()) while the model writes them capitalised, so a
        # case-sensitive pass silently missed every occurrence of Supremo1"s.
        # Preserve the casing the model actually used rather than the entity's.
        for ent in entities or []:
            text = re.sub(
                rf'({re.escape(ent)})["”`′″]s\b',
                lambda m: f"{m.group(1)}'s",
                text,
                flags=re.IGNORECASE,
            )
        # Always run the generic pass too. An entity list that fails to match the
        # model's spelling must not suppress the fallback that would have caught it.
        return re.sub(r'(\b[A-Z][a-zA-Z0-9]*)["”`′″]s\b', r"\1's", text)

    @staticmethod
    def clean_and_extract_json(response: str, expected_type: str = "auto", entities=None) -> str:
        logger.info("🔧 Starting universal JSON cleanup...")
        if UniversalJSONCleaner.DEBUG_JSON_LOGGING:
            logger.debug(f"📝 Raw LLM response:\n{response}")

        response = unicodedata.normalize("NFKC", response)
        response = UniversalJSONCleaner._normalize_quotes(response)
        response = UniversalJSONCleaner._normalize_quotes_and_symbols(response)

        # Fix broken possessives. Handles both the entity-specific and generic cases
        # internally — passing entities no longer skips the generic pass.
        response = UniversalJSONCleaner._fix_broken_possessives(response, entities)

        # Strip code fences & comments
        response = re.sub(r"^```[\w-]*\s*|\s*```$", "", response, flags=re.MULTILINE).strip()
        response = re.sub(r'^\s*//.*$', "", response, flags=re.MULTILINE).strip()

        response = UniversalJSONCleaner._fix_common_json_issues(response)
        response = response.strip()

        # Extract only array/object
        # NOTE: extraction must precede quote escaping. The escaper scans for string
        # boundaries, so any prose the model emits before the JSON ("Here is the
        # "report":") would put it inside a string literal and it would then escape
        # the object's own key quotes — yielding "Expecting property name enclosed in
        # double quotes" at the very first key.
        if expected_type == "array" or (expected_type == "auto" and response.startswith("[")):
            start = response.find("[")
            end = response.rfind("]")
            json_str = response[start:end + 1] if start != -1 and end > start else response

        elif expected_type == "object" or (expected_type == "auto" and response.startswith("{")):
            start = response.find("{")
            end = response.rfind("}")
            json_str = response[start:end + 1] if start != -1 and end > start else response
        else:
            array_match = re.search(r'\[.*?\]', response, re.DOTALL)
            object_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if array_match:
                json_str = array_match.group(0)
            elif object_match:
                json_str = object_match.group(0)
            else:
                json_str = response

        # Now that only the JSON payload remains, repair unescaped inner quotes.
        json_str = UniversalJSONCleaner._escape_quotes_in_values(json_str)

        if UniversalJSONCleaner.DEBUG_JSON_LOGGING:
            logger.debug(f"🧹 After pre-parse cleanup:\n{json_str}")

        logger.info(f"🔧 Cleaned JSON (first 200 chars): {json_str[:200]}...")
        return json_str

    @staticmethod
    def _fix_common_json_issues(json_str: str) -> str:
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        json_str = re.sub(r'(":)\s*""(.*?)"', r'\1 "\2"', json_str)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
        json_str = re.sub(r"'([^']*?)'", r'"\1"', json_str)
        json_str = re.sub(r'(["\}\]])\s+(?=")', r'\1, ', json_str)
        json_str = re.sub(r'([}\]])\s*([{\[])', r'\1, \2', json_str)
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
        json_str += ']' * (json_str.count('[') - json_str.count(']'))
        json_str += '}' * (json_str.count('{') - json_str.count('}'))
        return json_str

    # A quote inside a string is a *closing* quote only if the next meaningful
    # character continues the JSON grammar. Anything else means the model emitted an
    # unescaped quote mid-sentence.
    _JSON_STRUCTURAL_AFTER_STRING = set(',:}]')

    @staticmethod
    def _escape_quotes_in_values(json_str: str) -> str:
        """
        Escape unescaped double quotes that appear inside JSON string literals.

        This is the single most common malformed-JSON failure from the section
        writers — the model writes prose containing quotation marks and does not
        escape them, producing `Expecting ',' delimiter` at the first inner quote.

        Implemented as a scanner rather than a regex. The previous pattern was

            (":\\s*")((?:[^"\\\\]|\\\\.)*?)"(?=\\s*[,\\}])

        which had two defects that between them let most real failures through:

        1. The content group could not match a bare `"`, so the very values that
           needed repair — those containing an inner quote — never matched at all.
        2. The `":\\s*"` prefix only matched object values. String elements inside
           arrays were never considered, and `findings` is an array of prose strings.

        A character scan handles both, and correctly leaves already-escaped quotes,
        keys, and non-string tokens alone.
        """
        out: List[str] = []
        in_string = False
        i = 0
        length = len(json_str)

        while i < length:
            char = json_str[i]

            if not in_string:
                out.append(char)
                if char == '"':
                    in_string = True
                i += 1
                continue

            # Inside a string literal.
            if char == '\\':
                # Preserve the escape pair verbatim.
                out.append(char)
                if i + 1 < length:
                    out.append(json_str[i + 1])
                    i += 2
                else:
                    i += 1
                continue

            if char == '"':
                # Closing quote, or an unescaped quote in the middle of prose?
                j = i + 1
                while j < length and json_str[j].isspace():
                    j += 1
                is_terminator = (
                    j >= length
                    or json_str[j] in UniversalJSONCleaner._JSON_STRUCTURAL_AFTER_STRING
                )
                if is_terminator:
                    out.append(char)
                    in_string = False
                else:
                    out.append('\\"')
                i += 1
                continue

            out.append(char)
            i += 1

        return "".join(out)

    @staticmethod
    def parse_with_validation(json_str: str, expected_structure: str = None, entities=None) -> Any:
        try:
            result = json.loads(json_str)
            logger.info("🔧 JSON parsing successful")
            if UniversalJSONCleaner.DEBUG_JSON_LOGGING:
                logger.debug(f"🧾 Parsed JSON object:\n{json.dumps(result, indent=2)}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"🔧 JSON parsing failed: {e}")
            logger.error(f"🔧 Error position: {e.pos}")
            if e.pos < len(json_str):
                error_context = json_str[max(0, e.pos-50):e.pos+50]
                logger.error(f"🔧 Error context: '{error_context}'")
            logger.warning("🔧 Attempting ultimate fallback JSON repair...")
            try:
                # Guess entities if not provided
                local_entities = entities or UniversalJSONCleaner._guess_entities_from_json(json_str)
                repaired = UniversalJSONCleaner._fix_broken_possessives(json_str, local_entities)
                result = json.loads(repaired)
                logger.info("🔧 Ultimate fallback repair successful!")
                return result
            except Exception as repair_error:
                logger.error(f"🔧 Ultimate fallback also failed: {repair_error}")
                raise


    
    


class Agent(BaseModel):
    """Base agent class with common properties"""
    name: str
    role: str
    description: str
    llm: Any = Field(description="Language model for the agent")
    vector_store: Optional[Any] = Field(default=None, description="Optional vector store for searching")
    
    class Config:
        arbitrary_types_allowed = True

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
    
    def log_prompt(self, prompt: str, prefix: str = ""):
        """Log a prompt being sent to the LLM. Debug detail — verbose mode only."""
        if DEMO_MODE and not _verbose():
            # A full task prompt is thousands of characters; dumping it buries the
            # pipeline narrative. Kept behind VERBOSE=1 for debugging.
            logger.debug(f"{prefix} prompt ({len(prompt)} chars)")
            return
        # Check if the prompt contains context
        if "Context:" in prompt:
            # Split the prompt at "Context:" and keep only the first part
            parts = prompt.split("Context:")
            # Keep the first part and add a note that context is omitted
            truncated_prompt = parts[0] + "Context: [Context omitted for brevity]"
            if len(parts) > 2 and "Key Findings:" in parts[1]:
                # For researcher prompts, keep the "Key Findings:" part
                key_findings_part = parts[1].split("Key Findings:")
                if len(key_findings_part) > 1:
                    truncated_prompt += "\nKey Findings:" + key_findings_part[1]
            logger.info(f"\n{'='*80}\n{prefix} Prompt:\n{'-'*40}\n{truncated_prompt}\n{'='*80}")
        else:
            # If no context, log the full prompt
            logger.info(f"\n{'='*80}\n{prefix} Prompt:\n{'-'*40}\n{prompt}\n{'='*80}")
        
    def log_response(self, response: str, prefix: str = ""):
        """Log a response received from the LLM. Debug detail — verbose mode only."""
        if DEMO_MODE and not _verbose():
            logger.debug(f"{prefix} response ({len(response)} chars)")
            return
        # Log the response but truncate if it's too long
        if len(response) > 500:
            truncated_response = response[:500] + "... [response truncated]"
            logger.info(f"\n{'='*80}\n{prefix} Response:\n{'-'*40}\n{truncated_response}\n{'='*80}")
        else:
            logger.info(f"\n{'='*80}\n{prefix} Response:\n{'-'*40}\n{response}\n{'='*80}")


# RobustJSONParser has been removed (Step 8).
# Topic extraction now uses PlannerAgent._extract_topics_from_llm().
# Section JSON parsing still uses UniversalJSONCleaner.


class ChunkRewriteAgent(Agent):
    """Agent to rewrite flattened Excel chunks into retrievable factual statements"""

    def __init__(self, llm):
        super().__init__(
            name="ChunkRewriter",
            role="Tabular Rewriter",
            description="Rewrites tabular Excel chunks into factual statements",
            llm=llm
        )

    def rewrite_chunk(self, chunk_text: str, metadata: Dict[str, Any]) -> str:
        """Single chunk rewriting (legacy method for compatibility)"""
        return self.rewrite_chunks_batch([{"text": chunk_text, "metadata": metadata}])[0]

    def rewrite_chunks_batch(self, chunks: List[Dict[str, Any]], batch_size: int = 8) -> List[str]:
        """
        Batch rewrite multiple chunks in fewer API calls for significant speedup.
        
        Args:
            chunks: List of dicts with 'text' and 'metadata' keys
            batch_size: Number of chunks to process per API call
            
        Returns:
            List of rewritten chunk texts
        """
        if not chunks:
            return []
        
        logger.info(f"🔥 Batch rewriting {len(chunks)} chunks with batch_size={batch_size}")
        
        all_results = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_results = self._process_batch(batch)
            all_results.extend(batch_results)
            
            logger.info(f"✅ Processed batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
        
        return all_results
    
    def _clean_chunk_text(self, text: str) -> str:
        lines = text.strip().split('\n')
        cleaned = [
            line for line in lines
            if not re.match(r'^CHUNK\s+\d+:', line.strip()) and not line.strip() == '---CHUNK_END---'
        ]
        return '\n'.join(cleaned).strip()
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[str]:
        """Process a single batch of chunks with improved rewrite prompt for grouping similar facts."""
        
        # Use demo logger if available
        if DEMO_MODE and hasattr(logger, 'stage_header'):
            logger.stage_header("CHUNK REWRITING", f"Processing batch of {len(batch)} chunks")
        
        prompt_parts = [
            "You are transforming tabular content into clear, natural-language statements for downstream retrieval.",
            "",
            "REWRITE RULES:",
            " USE THE SAME LANGUAGE AS THE INPUT. If unclear, use what seems to be the main language",
            "- Begin with the company name and context (sheet, section) if available.",
            "- Group similar facts under shared headers (e.g., sectors, years, categories).",
            "- Avoid repeating similar phrases; merge where possible.",
            "- Use natural language and consistent units.",
            "- Do NOT include tables or JSON in the output.",
            "- Avoid unnecessary boilerplate like 'This shows that...'",
            "",
            "OUTPUT FORMAT: For each chunk, output a compact and grouped rewrite, ending with '---CHUNK_END---'.",
            "",
            "BEGIN CHUNKS (remember: if these are *not* in ENGLISH then you *must* switch languages to the appropriate language!):",
            ""
        ]

        for idx, chunk in enumerate(batch, 1):
            metadata = chunk.get("metadata", {})
            chunk_text = chunk.get("text", "")
            
            section_titles = metadata.get('section_titles', '') or ''
            section_titles_str = ", ".join(section_titles) if isinstance(section_titles, list) else str(section_titles or "")
            
            prompt_parts.extend([
                f"CHUNK {idx}:",
                f"entity: {metadata.get('entity', 'unknown')}",
                f"Sheet: {metadata.get('sheet', 'unknown')}",
                f"Section Titles: {section_titles_str}",
                "",
                "Raw Chunk:",
                chunk_text,
                "",
                f"Rewrite CHUNK {idx} in grouped, efficient form:",
                ""
            ])

        prompt = "\n".join(prompt_parts)
        self.log_prompt(prompt, f"ChunkRewriter (Batch of {len(batch)})")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Handle different LLM response styles
            if hasattr(response, "content"):
                text = response.content.strip()
            elif isinstance(response, list) and isinstance(response[0], dict):
                text = response[0].get("generated_text") or response[0].get("text")
                if not text:
                    raise ValueError("⚠️ No valid 'generated_text' found in response.")
                text = text.strip()
            else:
                raise TypeError(f"⚠️ Unexpected response type: {type(response)} — {response}")

            self.log_response(text, f"ChunkRewriter (Batch of {len(batch)})")
            rewritten_chunks = self._parse_batch_response(text, len(batch))
            rewritten_chunks = [self._clean_chunk_text(chunk) for chunk in rewritten_chunks]

            # Enhanced logging with side-by-side comparison
            paired = list(zip(batch, rewritten_chunks))
            for i, (original_chunk, rewritten_text) in enumerate(paired, 1):
                # Get the actual raw chunk text, not the metadata
                original_text = original_chunk.get("text", "")
                metadata = original_chunk.get("metadata", {})
                
                # Use demo logger for visual comparison if available
                if DEMO_MODE and hasattr(logger, 'chunk_comparison'):
                    # Pass the actual chunk text, not metadata
                    logger.chunk_comparison(original_text, rewritten_text, metadata)
                else:
                    logger.info(f"⚙ Rewritten Chunk {i}:\n{rewritten_text}\nMetadata: {json.dumps(metadata, indent=2)}\n")

            return rewritten_chunks
            
        except Exception as e:
            # Handle timeout and other errors gracefully
            logger.error(f"❌ Batch processing failed: {e}")
            # Return None for each chunk to indicate failure (not empty strings!)
            return [None] * len(batch)

    
    def _parse_batch_response(self, response_text: str, expected_chunks: int) -> List[str]:
        """Parse the batched response into individual chunk results"""
        # Split by the chunk separator
        parts = response_text.split("---CHUNK_END---")
        
        # Clean up each part. This is positional: result[i] must correspond to the i-th
        # chunk handed to the model. Skipping empty parts instead of recording them
        # would shift every later chunk onto the wrong chunk's metadata.
        results = [""] * expected_chunks
        for i, part in enumerate(parts):
            if i >= expected_chunks:
                break

            cleaned = part.strip()
            if cleaned:
                # Remove any "CHUNK N:" headers that might have been included
                lines = cleaned.split('\n')
                filtered_lines = []
                for line in lines:
                    if not re.match(r'^CHUNK \d+:', line.strip()):
                        filtered_lines.append(line)

                results[i] = '\n'.join(filtered_lines).strip()

        parsed_count = sum(1 for r in results if r)

        # Nothing parsed at all — the model likely ignored the delimiter, so try the
        # alternative patterns. A partial parse is kept as-is: the chunks that did come
        # back are correctly aligned, and the blanks make the caller keep those
        # originals. Re-parsing the whole response would discard good content.
        if parsed_count == 0:
            if DEMO_MODE:
                logger.debug(f"No chunks parsed from response. Trying fallback parsing.")
            else:
                logger.warning(f"⚠️ No chunks parsed from response. Trying fallback parsing.")
            return self._fallback_parse(response_text, expected_chunks)

        if parsed_count < expected_chunks:
            logger.warning(
                f"⚠️ Parsed {parsed_count}/{expected_chunks} chunks; "
                f"keeping originals for the remainder."
            )

        return results
    
    def _fallback_parse(self, response_text: str, expected_chunks: int) -> List[str]:
        """Fallback parsing when the main method fails"""
        # Try to split by common patterns
        patterns = [
            r'\n\n(?=\d+\.)',  # Split on double newline before numbered items
            r'\n(?=CHUNK \d+)',  # Split on CHUNK headers
            r'\n(?=\d+\.\s)',   # Split on numbered lists
        ]
        
        for pattern in patterns:
            parts = re.split(pattern, response_text)
            if len(parts) >= expected_chunks:
                results = []
                for part in parts[:expected_chunks]:
                    cleaned = part.strip()
                    if cleaned:
                        results.append(cleaned)
                
                if len(results) == expected_chunks:
                    if DEMO_MODE:
                        logger.debug(f"Fallback parsing successful with pattern: {pattern}")
                    else:
                        logger.info(f"✅ Fallback parsing successful with pattern: {pattern}")
                    return results
        
        # Ultimate fallback: abandon this batch. Splitting the response evenly by line
        # count assumes the model emitted equal-length chunks in order; when it did not,
        # each chunk is stored against another chunk's metadata. Silently misattributed
        # content is worse than no rewrite, so return "" and let the caller keep the
        # originals.
        if DEMO_MODE:
            logger.debug("All parsing methods failed. Keeping original chunk text.")
        else:
            logger.warning(
                f"⚠️ All parsing methods failed for {expected_chunks} chunks. "
                f"Keeping original text rather than risking misaligned content."
            )

        return [""] * expected_chunks


class PlannerAgent(Agent):
    """Agent responsible for breaking down problems and planning steps"""

    known_tags: Optional[Set[str]] = Field(default=None, description="Known entity tags from vector store")

    # Cap on criteria text carried into a retrieval step. Keeps the embedded query
    # inside the embedding model's window and stops one verbose topic from diluting
    # its own search terms.
    MAX_CRITERIA_CHARS: ClassVar[int] = 1400

    def __init__(self, llm, known_tags: Optional[Set[str]] = None):
        super().__init__(
            name="Planner",
            role="Strategic Planner",
            description="Breaks down complex problems into manageable steps",
            llm=llm,
        )
        if known_tags is not None:
            self.known_tags = known_tags
 
    def _detect_comparison_query(self, query: str) -> bool:
            """Use LLM to detect whether the query involves a comparison."""
            prompt = f"""
Does the query below involve a **side-by-side comparison between two or more named entities such as companies, organizations, or products**?
Include comparisons to frameworks (e.g., CSRD, ESRS), legal standards, or regulations.

Query:
"{query}"

Respond with a single word: "yes" or "no".
"""

            try:
                response = self.llm(prompt).strip().lower()
                return response.startswith("y")
            except Exception as e:
                logger.warning(f"⚠️ LLM comparison detection failed, defaulting to keyword check: {e}")
                # Fallback to keyword match
                comparison_keywords = [
                    "compare", "comparison", "vs", "versus", "between", "against",
                    "difference", "differences", "contrast", "side-by-side",
                    "which is better", "how do they differ", "similarities and differences"
                ]
                return any(k in query.lower() for k in comparison_keywords)

    

    @staticmethod
    def _looks_like_entity(entity: str) -> bool:
        """
        Naive but practical filter for 'real' entities (companies/organizations).
        """
        # Exclude empty, regulatory clause numbers, and keywords
        if not entity or not isinstance(entity, str):
            return False
        if re.match(r"^(AR\d+|ESRS|E\d+|Clause|clause|\d{2,})$", entity, re.IGNORECASE):
            return False
        # Avoid common pronouns or generic words
        if entity.lower() in {"entity", "organization", "entity", "entities", "the entity"}:
            return False
        # Must have at least one uppercase (usually a name)
        if not re.search(r"[A-Z]", entity):
            return False
        # Avoid anything too short or likely to be noise
        if len(entity.strip()) < 2:
            return False
        return True


    @staticmethod
    def extract_first_json_list(text):
        """Extract the first JSON list from text, if present."""
        # Look for the first substring that looks like a JSON list
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        # Fallback: extract all "quoted strings" as names
        return re.findall(r'"([^"]+)"', text)

    def _extract_entities(self, query: str) -> List[str]:
        """Prefer exact vector-store tags typed by the user; LLM only as fallback."""
        import re
        logger = getattr(self, "logger", None) or __import__("logging").getLogger(__name__)

        # --- 0) known tag set from your vector store (lowercased) ---
        # Populate this once at init: self.known_tags = {id.lower() for id in vector_store_ids()}
        known = getattr(self, "known_tags", None)

        tagged = []

        # A) Existing FY/Q pattern (kept)
        tagged += [m.group(0) for m in re.finditer(
            r"\b[A-Za-z][A-Za-z0-9\-]*_(?:FY|Q[1-4])\d{2,4}\b", query, flags=re.I
        )]

        # B) NEW: generic "<slug>_<year>" e.g., "mof_2022", "mof_2024"
        tagged += [m.group(0) for m in re.finditer(
            r"\b[A-Za-z][A-Za-z0-9\-]*_\d{2,4}\b", query
        )]

        # C) (Optional but useful) quoted tokens like "mof_2022"
        tagged += [m.group(1) for m in re.finditer(
            r'"([A-Za-z0-9][A-Za-z0-9_\-]{1,80})"', query
        )]

        # De-dup preserve order (case-insensitive)
        seen = set()
        tagged_unique: List[str] = []
        for t in tagged:
            k = t.lower()
            if k not in seen:
                # If we know the store IDs, only keep those that exist
                if not known or k in known:
                    seen.add(k)
                    tagged_unique.append(t)

        # --- Early return: if user typed valid tags, trust them verbatim ---
        if tagged_unique:
            if logger:
                logger.info(f"[Entity Extractor] Exact tags: {tagged_unique}")
            return tagged_unique

        # --- Fallback: your original LLM extraction (unchanged) ---
        prompt = f"""
    Extract company/organization names mentioned in the query and return a CLEANED JSON list.

    CLEANING RULES (apply to each name before returning):
    - Lowercase everything.
    - Remove legal suffixes at the end: plc, ltd, inc, llc, lp, l.p., corp, corporation, co., co, s.a., s.a.s., ag, gmbh, bv, nv, oy, ab, sa, spa, pte, pvt, pty, srl, sro, k.k., kk, kabushiki kaisha.
    - Remove punctuation except internal ampersands (&). Collapse multiple spaces.
    - No duplicates.

    CONSTRAINTS:
    - Return ONLY a JSON list of strings, e.g. ["aelwyn","elinexa"]
    - No prose, no keys, no explanations.
    - Do not include standards, clause numbers, sectors, or generic words like "entity".
    - If none are present, return [].

    Now process this query:

    {query}
    """
        try:
            raw = self.llm(prompt).strip()
            entities = self.extract_first_json_list(raw)
            entities = [e.strip() for e in entities if isinstance(e, str) and e.strip()]

            final: List[str] = []
            seen2 = set()

            for e in entities:
                k = e.lower()
                if (not known or k in known) and k not in seen2:
                    seen2.add(k)
                    final.append(e)

            if not final and logger:
                logger.warning(f"[Entity Extractor] No plausible entities extracted. LLM: {entities} | tags: []")

            if logger:
                logger.info(f"[Entity Extractor] Raw: {raw} | Tags: [] | Final: {final}")
            return final

        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Failed to robustly extract entities via LLM: {e}")
            return []



    def plan(
        self,
        query: str,
        context: List[Dict[str, Any]] | None = None,
        is_comparison_report: bool = False,
        comparison_mode: str | None = None,   # kept for compatibility, not used to hardcode content
        provided_entities: Optional[List[str]] = None
    ) -> tuple[list[Dict[str, Any]], list[str], bool]:
        """
        PROMPT-DRIVEN PLANNER
        - Derive section topics from the user's TASK PROMPT (not hardcoded).
        - For each topic, emit one mirrored retrieval step per entity.
        - Output shape: List[{"topic": str, "steps": List[str]}], plus (entities, is_comparison).
        - Now supports up to 10 entities for multi-entity comparisons (e.g., tender responses)

        Returns:
            (plan, entities, is_comparison)
        """

        # 1) Determine comparison intent and entities (updated to support up to 10 entities)
        # Short-circuit before _detect_comparison_query — it is an LLM round trip, and
        # both an explicit is_comparison_report flag and 2+ caller-supplied entities
        # already answer the question.
        if is_comparison_report or (provided_entities and len(provided_entities) >= 2):
            is_comparison = True
        else:
            is_comparison = self._detect_comparison_query(query)

        if provided_entities:
            entities = [e for e in provided_entities if isinstance(e, str) and e.strip()]
            # Limit to 10 entities maximum for performance reasons
            if len(entities) > 10:
                logger.warning(f"⚠️ Limiting to first 10 entities from {len(entities)} provided")
                entities = entities[:10]
            logger.info(f"[Planner] Using provided entities: {entities}")
        else:
            entities = self._extract_entities(query)
            # Support up to 10 entities
            if len(entities) > 10:
                logger.warning(f"⚠️ Limiting to first 10 entities from {len(entities)} detected")
                entities = entities[:10]
            logger.info(f"[Planner] Detected entities: {entities} | Comparison task: {is_comparison}")

        # If comparison requested but <2 entities, degrade gracefully to single-entity mode
        if is_comparison and len(entities) < 2:
            logger.warning(f"⚠️ Comparison requested but only {len(entities)} entity found: {entities}. Falling back to single-entity.")
            is_comparison = False

        # 2) Ask the LLM ONLY for topics (strings), not full objects — we'll build steps ourselves
        #    This avoids fragile JSON with missing "topic" keys.
        topic_prompt = f"""
Extract the main section topics from the TASK PROMPT, and for each topic list the specific
criteria, metrics and policy areas the user wants covered under it.

Use the user's own headings/bullets/order when present.
If none are explicit, infer 5–10 concise, non-overlapping topics that reflect the user's request.

Assign every criterion the user lists to the topic it belongs under. Reuse the user's own
wording: the criteria are embedded verbatim as the search query against the source documents,
so concrete nouns (sector names, policy names, metric names, standards, thresholds) retrieve
far better than abstract prose.

TASK PROMPT:
{query}

Also classify each topic by how it must be written:
- "compare"   : reports data about the subjects — needs source documents retrieved
- "synthesize": summarises or judges across the other sections (executive summaries,
                overall assessments, conclusions) — uses no new source data
- "recommend" : proposes actions based on gaps found in the other sections

Return ONLY a JSON array of objects, e.g.
[{{"topic":"Environmental Performance","role":"compare","criteria":"Scope 1/2/3 GHG targets; renewable electricity sourcing; thermal coal financing policy"}},
 {{"topic":"Recommendations","role":"recommend","criteria":""}}]
Each object must have exactly the keys "topic" (short heading), "role" (one of compare,
synthesize, recommend) and "criteria" (a single line of semicolon-separated search terms;
use "" for synthesize and recommend topics).
No prose, no markdown.
"""
        self.log_prompt(topic_prompt, "Planner: Topic + Criteria Extraction")
        topic_specs: list[dict] = self._extract_topic_specs_from_llm(topic_prompt)

        # 2b) Hard fallback: if still empty, derive topics from obvious headings in the query.
        #     Fallback paths yield no criteria, so their steps degrade to the topic label alone.
        if not topic_specs:
            # Grab capitalized/bulleted lines as headings
            lines = [ln.strip() for ln in (query or "").splitlines()]
            bullets = [ln.lstrip("-*• ").strip() for ln in lines if ln.strip().startswith(("-", "*", "•"))]
            caps = [ln for ln in lines if ln and ln == ln.title() and len(ln.split()) <= 8]
            candidates = bullets or caps
            if candidates:
                topic_specs = [
                    {"topic": t, "criteria": "", "role": self._infer_role(t)}
                    for t in candidates if len(t) >= 3
                ][:10]

        # 2c) Ultimate fallback: generic buckets (kept minimal, not domain-specific)
        if not topic_specs:
            topic_specs = [{"topic": t, "criteria": "", "role": self._infer_role(t)} for t in (
                "Executive Summary",
                "Key Metrics",
                "Section 1",
                "Section 2",
                "Section 3",
                "Risks & Considerations",
                "Conclusion",
            )]

        # 3) Build plan objects and MIRROR steps across entities (now supports multi-entity)
        plan: list[dict] = []
        for spec in topic_specs:
            t_clean = str(spec.get("topic", "")).strip()
            if not t_clean:
                continue

            # The step string IS the retrieval query (see ResearchAgent.research, which
            # embeds f"{step} {entity}"). Carrying the user's criteria here is what lets
            # retrieval reach criterion-specific chunks; a bare topic label cannot.
            criteria = " ".join(str(spec.get("criteria") or "").split())
            if len(criteria) > self.MAX_CRITERIA_CHARS:
                criteria = criteria[:self.MAX_CRITERIA_CHARS].rsplit(" ", 1)[0] + "…"

            role = str(spec.get("role") or "").strip().lower()
            if role not in ("compare", "synthesize", "recommend"):
                role = self._infer_role(t_clean)

            def _step_for(entity: str, _t=t_clean, _c=criteria) -> str:
                if _c:
                    return f"{_t}: {_c} — for {entity}"
                return f"Find all items requested under '{_t}' for {entity}"

            # synthesize/recommend sections read the written compare sections rather
            # than the source documents, so they get no retrieval steps at all.
            if role in ("synthesize", "recommend"):
                steps = []
            elif is_comparison and len(entities) >= 2:
                # One retrieval step per entity — mirrored wording for all entities
                steps = [_step_for(entity) for entity in entities]
            else:
                # Single entity (or unknown)
                e0 = entities[0] if entities else "The Entity"
                steps = [_step_for(e0)]

            plan.append({"topic": t_clean, "steps": steps, "role": role})

        # 4) Log and return
        try:
            self.log_response(json.dumps(plan, ensure_ascii=False, indent=2), "Planner: Plan (topics→steps)")
        except Exception:
            pass

        return plan, entities, is_comparison

    def plan_typed(
        self,
        query: str,
        *,
        is_comparison_report: bool = False,
        provided_entities: Optional[List[str]] = None,
        max_topics: int = 10,
    ) -> Plan:
        """Return a typed Plan model. Preferred over plan() for new code."""
        plan_list, entities, is_comparison = self.plan(
            query,
            is_comparison_report=is_comparison_report,
            provided_entities=provided_entities,
        )
        # Limit topics
        plan_list = plan_list[:max_topics]
        return Plan.from_legacy_tuple(plan_list, entities, is_comparison)

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences from LLM output."""
        return re.sub(r"^```[\w-]*\s*|\s*```$", "", text, flags=re.MULTILINE).strip()

    @staticmethod
    def _normalize_smart_quotes(text: str) -> str:
        """Replace smart/curly quotes with ASCII equivalents."""
        replacements = {
            "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
            "\u2032": "'", "\u2033": '"',
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    @staticmethod
    def _infer_role(topic: str) -> str:
        """
        Fallback role classification from the topic heading, used when the LLM omits
        or mangles "role". Defaults to "compare" — the safe choice, since a compare
        section still retrieves and reports data rather than producing nothing.
        """
        t = topic.strip().lower()
        if any(k in t for k in ("recommend", "next step", "action plan", "improvement")):
            return "recommend"
        if any(k in t for k in (
            "executive summary", "overall", "conclusion", "summary",
            "assessment", "verdict", "overview",
        )):
            return "synthesize"
        return "compare"

    def _extract_topic_specs_from_llm(self, topic_prompt: str) -> list[dict]:
        """
        Extract [{"topic": str, "criteria": str}, ...] from the LLM.

        A bare array of strings is also accepted, so a model that ignores the object
        format degrades to label-only steps (the previous behaviour) rather than
        failing the plan outright.
        """
        raw = None
        for attempt in range(2):
            try:
                if attempt == 0:
                    raw = self.llm(topic_prompt).strip()
                else:
                    retry_prompt = (
                        "Your previous response was not valid JSON. Return ONLY a valid JSON "
                        'array of objects, each with keys "topic" and "criteria". '
                        f"Fix this output:\n{raw}"
                    )
                    raw = self.llm(retry_prompt).strip()

                cleaned = self._normalize_smart_quotes(self._strip_fences(raw))

                # Extract array substring
                start = cleaned.find("[")
                end = cleaned.rfind("]")
                if start != -1 and end > start:
                    cleaned = cleaned[start:end + 1]

                parsed = json.loads(cleaned)
                if not isinstance(parsed, list):
                    continue

                specs: list[dict] = []
                for item in parsed:
                    if isinstance(item, dict):
                        topic = str(item.get("topic", "")).strip()
                        criteria = item.get("criteria", "")
                        # Models often return criteria as a list despite the instruction
                        if isinstance(criteria, (list, tuple)):
                            criteria = "; ".join(str(c).strip() for c in criteria if str(c).strip())
                        criteria = str(criteria or "").strip()
                        role = str(item.get("role", "")).strip().lower()
                    elif isinstance(item, (str, int, float)):
                        topic, criteria, role = str(item).strip(), "", ""
                    else:
                        continue
                    if topic:
                        if role not in ("compare", "synthesize", "recommend"):
                            role = self._infer_role(topic)
                        specs.append({"topic": topic, "criteria": criteria, "role": role})

                if specs:
                    with_criteria = sum(1 for s in specs if s["criteria"])
                    roles = ", ".join(f"{s['topic']}={s['role']}" for s in specs)
                    logger.info(
                        f"[Planner] Extracted {len(specs)} topics, "
                        f"{with_criteria} with criteria | roles: {roles}"
                    )
                    return specs

            except Exception as e:
                logger.warning(f"Topic/criteria extraction attempt {attempt + 1} failed: {e}")

        logger.warning("Topic extraction: falling back to heuristic parsing")
        return []

    def _extract_topics_from_llm(self, topic_prompt: str) -> list[str]:
        """
        Extract topic list from LLM with simplified parsing:
        1. Try json.loads after stripping fences + normalizing quotes.
        2. One retry with corrective prompt.
        3. Heuristic fallback.
        """
        raw_topics = None
        for attempt in range(2):
            try:
                if attempt == 0:
                    raw_topics = self.llm(topic_prompt).strip()
                else:
                    retry_prompt = (
                        "Your previous response was not valid JSON. "
                        "Return ONLY a valid JSON array of strings. "
                        f"Fix this output:\n{raw_topics}"
                    )
                    raw_topics = self.llm(retry_prompt).strip()

                cleaned = self._strip_fences(raw_topics)
                cleaned = self._normalize_smart_quotes(cleaned)

                # Extract array substring
                start = cleaned.find("[")
                end = cleaned.rfind("]")
                if start != -1 and end > start:
                    cleaned = cleaned[start:end + 1]

                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    topics = [str(t).strip() for t in parsed
                              if isinstance(t, (str, int, float)) and str(t).strip()]
                    if topics:
                        return topics

            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Topic extraction attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    continue

        # Heuristic fallback: never reaches UniversalJSONCleaner
        logger.warning("Topic extraction: falling back to heuristic parsing")
        return []


class ResearchAgent(Agent):
    """Agent responsible for gathering and analyzing information"""
    
    # Chunks retrieved per entity per section. Env-tunable because it is the main
    # lever on prompt size, and prompt size drives section-write latency: measured on
    # one Environmental section, 16 chunks/28.5k chars = 69.8s, 8 chunks/14.6k = 58.3s,
    # 4 chunks/7.5k = 42.5s. Below 4 the table starts losing rows, so lowering this is
    # a coverage trade, not a free win — verify against the criteria list before
    # reducing it for a corpus larger than the current 8 chunks per entity.
    TOP_K: ClassVar[int] = int(os.environ.get("RESEARCH_TOP_K", "8"))
    # Chunks run ~1500-2500 chars; at 1000 the tail (later sheet rows — sector
    # targets, programme names) was silently cut before the writer ever saw it.
    MAX_CHARS: ClassVar[int] = 2500
    MAX_WORKERS: ClassVar[int] = 4  

    def __init__(self, llm, vector_store):
        super().__init__(
            name="Researcher",
            role="Information Gatherer",
            description="Gathers and analyzes relevant information from knowledge bases",
            llm=llm,
            vector_store=vector_store
        )


    def research(
        self,
        query: str,
        step: str,
        context: Optional[List[Dict[str, Any]]] = None,
        is_comparison: bool = False,
        entities: Optional[List[str]] = None,
        collection: str = "xlsx"   # allowed: "xlsx", "pdf", "multi"
    ) -> List[Dict[str, Any]]:
        logger.info(f"🔍 Researching: {step} [collection={collection}]")

        def run_qfn(qfn, sq, entity=None):
            return qfn(sq, n_results=self.TOP_K, entity=entity.lower() if entity else None) or []

        # === Handle comparison mode ===
        if is_comparison:
            ents = entities or []
            ents = [e.strip() for e in ents if isinstance(e, str) and e.strip()]
            if not ents:
                logger.warning("⚠️ No entities detected/provided for comparison step")
                return []

            results_by_entity: Dict[str, List[Dict[str, Any]]] = {}

            def _fetch_for_entity(e: str):
                sq = f"{step} {e}".strip()
                if collection == "xlsx":
                    chunks = run_qfn(self.vector_store.query_xlsx_collection, sq, e)
                elif collection == "pdf":
                    chunks = run_qfn(self.vector_store.query_pdf_collection, sq, e)
                else:  # multi
                    chunks = run_qfn(self.vector_store.query_collection, sq, e)
                for c in chunks:
                    txt = (c.get("content") or "").strip()
                    if len(txt) > self.MAX_CHARS:
                        c["content"] = txt[:self.MAX_CHARS] + "…"
                    c["_search_entity"] = e
                return e, chunks

            with ThreadPoolExecutor(max_workers=min(self.MAX_WORKERS, max(1, len(ents)))) as ex:
                futures = {ex.submit(_fetch_for_entity, e): e for e in ents}
                for fut in as_completed(futures):
                    e = futures[fut]
                    try:
                        e, chunks = fut.result()
                    except Exception as err:
                        logger.warning(f"⚠️ Lookup failed for entity '{e}': {err}")
                        chunks = []
                    results_by_entity[e] = chunks

            interleaved = self._interleave_chunks(results_by_entity)

            seen = set()
            deduped_scored = []
            for c in interleaved:
                txt = (c.get("content") or "").strip()
                if not txt or txt in seen:
                    continue
                seen.add(txt)
                e = c.get("_search_entity", "unknown")
                c["_entity_score"] = self._score_chunk(c, step, e)
                deduped_scored.append(c)

            logger.info(f"✅ Retrieved {len(deduped_scored)} unique chunks for step: {step}")
            return deduped_scored

        # === Single-entity mode ===
        chunks = []
        if collection == "xlsx":
            chunks = run_qfn(self.vector_store.query_xlsx_collection, step)
        elif collection == "pdf":
            chunks = run_qfn(self.vector_store.query_pdf_collection, step)
        else:  # multi
            chunks = run_qfn(self.vector_store.query_collection, step)

        seen = set()
        out = []
        for c in chunks:
            txt = (c.get("content") or "").strip()
            if not txt or txt in seen:
                continue
            seen.add(txt)
            if len(txt) > self.MAX_CHARS:
                c["content"] = txt[:self.MAX_CHARS] + "…"
            c["_search_entity"] = "unknown"
            c["_entity_score"] = self._score_chunk(c, step, "unknown")
            out.append(c)

        logger.info(f"✅ Retrieved {len(out)} unique chunks for step: {step}")
        return out



    def _score_chunk(self, chunk: Dict[str, Any], step: str, entity: str) -> float:
        """Score chunk relevance to the step and entity"""
        content = chunk.get("content", "").lower()
        metadata = chunk.get("metadata", {}) or {}

        score = 0
        if entity.lower() in content:
            score += 5
        if entity.lower() in (metadata.get("entity", "").lower() or ""):
            score += 3

        step_words = set(step.lower().split())
        overlap = len(step_words.intersection(content.split()))
        score += overlap * 0.5

        if any(k in content for k in ["%","target","score","rating","goal"]):
            score += 1

        return score

    def _interleave_chunks(self, entity_chunks: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Interleave chunks from each entity to maintain balanced representation"""
        interleaved = []
        max_len = max(len(v) for v in entity_chunks.values())

        for i in range(max_len):
            for entity in sorted(entity_chunks.keys()):
                chunks = entity_chunks[entity]
                if i < len(chunks):
                    interleaved.append(chunks[i])
        return interleaved

    def research_typed(
        self,
        query: str,
        step: str,
        *,
        is_comparison: bool = False,
        entities: Optional[List[str]] = None,
        collection: str = "multi",
        k: int = 3,
    ) -> List[Chunk]:
        """Return typed Chunk models instead of raw dicts."""
        raw = self.research(
            query, step, is_comparison=is_comparison,
            entities=entities, collection=collection,
        )
        return [Chunk.from_legacy_dict(d) for d in raw]

  

def create_ingestion_only_agents(llm):
    """Agents needed only for ingestion and preprocessing, not full agentic reasoning"""
    return {
        "chunk_rewriter": ChunkRewriteAgent(llm)
    }
def create_agents(llm, vector_store=None, model_name="unknown", tokenizer=None, known_tags=None):
    """Create and return the set of specialized agents"""
    return {
        "planner": PlannerAgent(llm, known_tags=known_tags),
        "researcher": ResearchAgent(llm, vector_store) if vector_store else None,
        "section_writer": SectionWriterAgent(llm, tokenizer=tokenizer),
        "report_agent": ReportWriterAgent(doc=None, model_name=model_name, llm=llm),
        "chunk_rewriter": ChunkRewriteAgent(llm)
    }
