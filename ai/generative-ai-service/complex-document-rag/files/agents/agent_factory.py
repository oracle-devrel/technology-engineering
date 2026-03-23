from typing import List, Dict, Any, ClassVar, Optional
from pydantic import BaseModel, Field, ValidationError
from langchain.prompts import ChatPromptTemplate
from docx import Document
import logging
import warnings
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import re, unicodedata
from transformers import logging as transformers_logging
from agents.report_writer_agent import ReportWriterAgent, SectionWriterAgent

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

# Suppress specific transformers warnings
transformers_logging.set_verbosity_error()
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
        # For each entity, replace Foo"s with Foo's
        for ent in entities:
            # Replace only if "s is after the entity (word boundary)
            text = re.sub(rf'{re.escape(ent)}["”`′″]s\b', f"{ent}'s", text)
        return text

    @staticmethod
    def clean_and_extract_json(response: str, expected_type: str = "auto", entities=None) -> str:
        logger.info("🔧 Starting universal JSON cleanup...")
        if UniversalJSONCleaner.DEBUG_JSON_LOGGING:
            logger.debug(f"📝 Raw LLM response:\n{response}")

        response = unicodedata.normalize("NFKC", response)
        response = UniversalJSONCleaner._normalize_quotes(response)
        response = UniversalJSONCleaner._normalize_quotes_and_symbols(response)

        # If entities provided, try to fix broken possessives for each
        if entities:
            response = UniversalJSONCleaner._fix_broken_possessives(response, entities)
        else:
            # fallback: try to fix generic Foo"s → Foo's
            response = re.sub(r'(\b[A-Z][a-zA-Z0-9]*)["”`′″]s\b', r"\1's", response)

        # Strip code fences & comments
        response = re.sub(r"^```[\w-]*\s*|\s*```$", "", response, flags=re.MULTILINE).strip()
        response = re.sub(r'^\s*//.*$', "", response, flags=re.MULTILINE).strip()

        response = UniversalJSONCleaner._fix_common_json_issues(response)
        json_str = UniversalJSONCleaner._escape_quotes_in_values(response)

        if UniversalJSONCleaner.DEBUG_JSON_LOGGING:
            logger.debug(f"🧹 After pre-parse cleanup:\n{json_str}")

        response = json_str.strip()
        # Extract only array/object
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

    @staticmethod
    def _escape_quotes_in_values(json_str: str) -> str:
        def replacer(match):
            prefix = match.group(1)
            content = match.group(2)
            # Escape internal double quotes and fix possessives
            content = re.sub(r'(\b\w+)"s\b', r"\1's", content)
            content = re.sub(r'(?<!\\)"', r'\\"', content)
            return f'{prefix}{content}"'
        pattern = r'(":\s*")((?:[^"\\]|\\.)*?)"(?=\s*[,\}])'
        return re.sub(pattern, replacer, json_str)

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


    
    


def log_token_count(text: str, tokenizer, label: str = "Prompt"):
    """Log token count using provided tokenizer"""
    if not text or not tokenizer:
        print(f"⚠️ Cannot log tokens: text or tokenizer missing for {label}")
        return
    token_count = len(tokenizer.encode(text))
    print(f"🧮 {label} token count: {token_count}")


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
        """Log a prompt being sent to the LLM"""
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
        """Log a response received from the LLM"""
        # Log the response but truncate if it's too long
        if len(response) > 500:
            truncated_response = response[:500] + "... [response truncated]"
            logger.info(f"\n{'='*80}\n{prefix} Response:\n{'-'*40}\n{truncated_response}\n{'='*80}")
        else:
            logger.info(f"\n{'='*80}\n{prefix} Response:\n{'-'*40}\n{response}\n{'='*80}")


class DummyMessage:
    def __init__(self, content):
        self.content = content


class PlanStep(BaseModel):
    """Individual planning step with validation"""
    description: str = Field(description="Step description containing named entities")
    entities: Optional[List[str]] = Field(default=None, description="Named entities for retrieval")

class PlanningResponse(BaseModel):
    """Validated planning response structure"""
    steps: List[str] = Field(description="List of planning step descriptions")
    reasoning: Optional[str] = Field(default=None, description="Optional reasoning")

class RobustJSONParser:
    """Industry-standard robust JSON parsing with multiple fallback strategies."""

    @staticmethod
    def clean_json_text(text: str) -> str:
        """Clean and normalize JSON-ish text before extraction."""
        # Normalize smart quotes and characters
        

        # Replace smart double quotes and apostrophes with standard ones
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")

        # Fix common JSON mis-quote error: Aelwyn"s → Aelwyn's
        text = re.sub(r'(\b\w+)"s\b', r"\1's", text)

        # Remove markdown fences
        fence = re.compile(r"^```[\w-]*\s*|\s*```$", re.MULTILINE)
        text = fence.sub("", text).strip()

        # Remove // comments
        comment_lines = re.compile(r'^\s*//.*$', re.MULTILINE)
        text = comment_lines.sub("", text).strip()

        return text

    @staticmethod
    def extract_json_array(text: str) -> str:
        start = text.find("[")
        end = text.rfind("]")
        return text[start:end + 1].strip() if start != -1 and end > start else text

    @staticmethod
    def extract_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        return text[start:end + 1].strip() if start != -1 and end > start else text

    @staticmethod
    def parse_with_fallbacks(text: str, max_retries: int = 3) -> List[str]:
        """Attempt multiple fallback strategies for step extraction."""
        original_text = text
        cleaned = RobustJSONParser.clean_json_text(text)

        # Strategy 1: Try JSON array directly
        try:
            result = json.loads(RobustJSONParser.extract_json_array(cleaned))
            if isinstance(result, list):
                return [str(item) for item in result]
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")

        # Strategy 2: JSON object with steps-like keys
        try:
            result = json.loads(RobustJSONParser.extract_json_object(cleaned))
            if isinstance(result, dict):
                for key in ['steps', 'tasks', 'plan', 'items', 'list']:
                    if key in result and isinstance(result[key], list):
                        return [str(item) for item in result[key]]
                # fallback: any list value
                for val in result.values():
                    if isinstance(val, list):
                        return [str(item) for item in val]
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")

        # Strategy 3: Regex-based list parsing
        try:
            numbered = re.findall(r'^\s*\d+\.\s*(.+)$', cleaned, re.MULTILINE)
            if len(numbered) >= 2:
                return [s.strip() for s in numbered]
            bulleted = re.findall(r'^\s*[-*•]\s*(.+)$', cleaned, re.MULTILINE)
            if len(bulleted) >= 2:
                return [s.strip() for s in bulleted]
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")

        # Strategy 4: Line-by-line filter
        try:
            lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
            steps = [
                line for line in lines
                if len(line) > 10 and not any(line.startswith(c) for c in '{[}"') and ':' not in line[:10]
            ]
            if len(steps) >= 2:
                return steps[:20]
        except Exception as e:
            logger.debug(f"Strategy 4 failed: {e}")

        # Final fallback
        logger.warning(f"All parsing strategies failed. Original input: {original_text[:200]}...")
        return [
            "Analyze the main requirements and objectives",
            "Gather relevant information and context", 
            "Identify key stakeholders and entities",
            "Compare and contrast different approaches",
            "Synthesize findings into actionable insights"
        ]


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
            response = self.llm.invoke([DummyMessage(prompt)])

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
        
        # Clean up each part
        results = []
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
                
                cleaned = '\n'.join(filtered_lines).strip()
                if cleaned:
                    results.append(cleaned)
        
        # If we didn't get enough results, try alternative parsing
        if len(results) < expected_chunks:
            # Use debug level instead of warning for demo mode
            if DEMO_MODE:
                logger.debug(f"Expected {expected_chunks} results, got {len(results)}. Trying fallback parsing.")
            else:
                logger.warning(f"⚠️ Expected {expected_chunks} results, got {len(results)}. Trying fallback parsing.")
            return self._fallback_parse(response_text, expected_chunks)
        
        # Pad with empty results if needed
        while len(results) < expected_chunks:
            results.append("No rewritten content available for this chunk.")
        
        return results[:expected_chunks]
    
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
        
        # Ultimate fallback: split the text evenly
        if DEMO_MODE:
            logger.debug(f"All parsing methods failed. Using even split fallback.")
        else:
            logger.warning(f"⚠️ All parsing methods failed. Using even split fallback.")
        
        lines = response_text.split('\n')
        lines_per_chunk = max(1, len(lines) // expected_chunks)
        
        results = []
        for i in range(expected_chunks):
            start_idx = i * lines_per_chunk
            end_idx = start_idx + lines_per_chunk if i < expected_chunks - 1 else len(lines)
            chunk_lines = lines[start_idx:end_idx]
            chunk_text = '\n'.join(chunk_lines).strip()
            results.append(chunk_text if chunk_text else f"Chunk {i+1} content not available.")

        return results


class PlannerAgent(Agent):
    # ────────────────────────────────────────────────────────────────
    # 1.  Normalise quotes  *and* remove Markdown fences / extra text
    # ────────────────────────────────────────────────────────────────

    """Agent responsible for breaking down problems and planning steps"""
    def __init__(self, llm):
        super().__init__(
            name="Planner",
            role="Strategic Planner",
            description="Breaks down complex problems into manageable steps",
            llm=llm
        )
 
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

        Returns:
            (plan, entities, is_comparison)
        """

        # 1) Determine comparison intent and entities (keep your existing logic)
        is_comparison = self._detect_comparison_query(query) or is_comparison_report

        if provided_entities:
            entities = [e for e in provided_entities if isinstance(e, str) and e.strip()]
            logger.info(f"[Planner] Using provided entities: {entities}")
        else:
            entities = self._extract_entities(query)
            logger.info(f"[Planner] Detected entities: {entities} | Comparison task: {is_comparison}")

        # If comparison requested but <2 entities, degrade gracefully to single-entity mode
        if is_comparison and len(entities) < 2:
            logger.warning(f"⚠️ Comparison requested but only {len(entities)} entity found: {entities}. Falling back to single-entity.")
            is_comparison = False

        # 2) Ask the LLM ONLY for topics (strings), not full objects — we’ll build steps ourselves
        #    This avoids fragile JSON with missing "topic" keys.
        topic_prompt = f"""
Extract the main section topics from the TASK PROMPT. 
Use the user's own headings/bullets/order when present. 
If none are explicit, infer 5–10 concise, non-overlapping topics that reflect the user's request.

TASK PROMPT:
{query}

Return ONLY a JSON array of strings, e.g. ["Executive Summary","Revenue Analysis","Profitability"]. 
No prose, no keys, no markdown.
"""
        self.log_prompt(topic_prompt, "Planner: Topic Extraction")
        raw_topics = None
        topics: list[str] = []
        try:
            raw_topics = self.llm(topic_prompt).strip()
            json_str = UniversalJSONCleaner.clean_and_extract_json(raw_topics, expected_type="array")
            parsed = UniversalJSONCleaner.parse_with_validation(json_str, expected_structure=None)
            if isinstance(parsed, list):
                # Keep only non-empty strings
                topics = [str(t).strip() for t in parsed if isinstance(t, (str, int, float)) and str(t).strip()]
        except Exception as e:
            logger.error(f"❌ Topic extraction failed: {e}")
            logger.debug(f"Raw topic response:\n{raw_topics}")

        # 2b) Hard fallback: if still empty, derive topics from obvious headings in the query
        if not topics:
            # Grab capitalized/bulleted lines as headings
            lines = [ln.strip() for ln in (query or "").splitlines()]
            bullets = [ln.lstrip("-*• ").strip() for ln in lines if ln.strip().startswith(("-", "*", "•"))]
            caps = [ln for ln in lines if ln and ln == ln.title() and len(ln.split()) <= 8]
            candidates = bullets or caps
            if candidates:
                topics = [t for t in candidates if len(t) >= 3][:10]

        # 2c) Ultimate fallback: generic buckets (kept minimal, not domain-specific)
        if not topics:
            topics = [
                "Executive Summary",
                "Key Metrics",
                "Section 1",
                "Section 2",
                "Section 3",
                "Risks & Considerations",
                "Conclusion"
            ]

        # 3) Build plan objects and MIRROR steps across entities (no hardcoded content)
        plan: list[dict] = []
        for t in topics:
            t_clean = str(t).strip()
            if not t_clean:
                continue

            if is_comparison and len(entities) >= 2:
                # One retrieval step per entity — mirrored wording
                steps = [f"Find all items requested under '{t_clean}' for {entities[0]}",
                         f"Find all items requested under '{t_clean}' for {entities[1]}"]
            else:
                # Single entity (or unknown)
                e0 = entities[0] if entities else "The Entity"
                steps = [f"Find all items requested under '{t_clean}' for {e0}"]

            plan.append({"topic": t_clean, "steps": steps})

        # 4) Log and return
        try:
            self.log_response(json.dumps(plan, ensure_ascii=False, indent=2), "Planner: Plan (topics→steps)")
        except Exception:
            pass

        return plan, entities, is_comparison





class ResearchAgent(Agent):
    """Agent responsible for gathering and analyzing information"""
    
    TOP_K: ClassVar[int] = 3
    MAX_CHARS: ClassVar[int] = 1000
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

        # OPTIMIZED: Reduce TOP_K for faster retrieval, increase MAX_CHARS for better context
        def run_qfn(qfn, sq, entity=None):
            return qfn(sq, n_results=min(self.TOP_K, 2), entity=entity.lower() if entity else None) or []

        # === Handle comparison mode ===
        if is_comparison:
            ents = entities or self._detect_entities_from_step(step) or []
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
                    chunks = run_qfn(self.vector_store.query_pdf_collection, sq, e)
                    chunks += run_qfn(self.vector_store.query_xlsx_collection, sq, e)
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
            chunks = run_qfn(self.vector_store.query_pdf_collection, step)
            chunks += run_qfn(self.vector_store.query_xlsx_collection, step)

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

    def _detect_entities_from_step(self, step: str) -> List[str]:
        """Extract entity names (e.g., Aelwyn, Elinexa) from a task step"""
        known = ["aelwyn", "elinexa"]
        entities = [e for e in known if e in step.lower()]
        return entities if len(entities) == 2 else known

  

class ReasoningAgent(Agent):
    """Agent responsible for logical reasoning and analysis"""
    def __init__(self, llm):
        super().__init__(
            name="Reasoner",
            role="Logic and Analysis",
            description="Applies logical reasoning to information and draws conclusions",
            llm=llm
        )
        
    def reason(self, query: str, step: str, context: List[Dict[str, Any]]) -> str:
        logger.info(f"\n🤔 Reasoning about step: {step}")
        
        template = """Analyze the information and draw a clear conclusion for this step.
        
        Step: {step}
        Context: {context}
        Query: {query}
        
        Conclusion:"""
        
        # Create context string but don't log it
        context_str = "\n\n".join([f"Context {i+1}:\n{item['content']} {item['metadata']['cite']}" for i, item in enumerate(context)])
        prompt = ChatPromptTemplate.from_template(template)
        messages = prompt.format_messages(step=step, query=query, context=context_str)
        prompt_text = "\n".join([str(msg.content) for msg in messages])
        self.log_prompt(prompt_text, "Reasoner")
        
        response = self.llm.invoke(messages)
        self.log_response(response.content, "Reasoner")
        return response.content

class SynthesisAgent(Agent):
    MAX_STEP_CHARS: ClassVar[int] = 1000
    MAX_STEPS_USED: ClassVar[int] = 40
    RETRY_LIMIT: ClassVar[int]    = 1
    CITE_RE: ClassVar[re.Pattern] = re.compile(r"\[[^\[\]]+:\d+\]")

    def __init__(self, llm):
        super().__init__(
            name="Synthesizer",
            role="Information Synthesizer",
            description="Combines multiple pieces of information into a coherent response",
            llm=llm
        )

    def synthesize(self, query: str, grouped_steps: dict[str, list[str]]) -> str:
        logger.info("📝 Synthesizing answer from %d sections", len(grouped_steps))

        sections = []

        for section_name, steps in grouped_steps.items():
            logger.info(f"📚 Synthesizing section: {section_name} ({len(steps)} steps)")
            try:
                section_text = self._synthesize_section(query, section_name, steps)
                sections.append(section_text)
            except Exception as e:
                logger.warning(f"⚠️ Skipping section '{section_name}' due to error: {e}")

        return "\n\n".join(sections)

    def _synthesize_section(self, query: str, section_name: str, reasoning_steps: List[str]) -> str:
        trimmed = []
        required_cites = set()

        for step in reasoning_steps[:self.MAX_STEPS_USED]:
            txt = step[:self.MAX_STEP_CHARS] + ("…" if len(step) > self.MAX_STEP_CHARS else "")
            trimmed.append(txt)
            required_cites.update(self.CITE_RE.findall(txt))

        steps_str = "\n\n".join(trimmed)

        template = """You are a senior analyst. Write a focused, well-structured section for a report, based only on the reasoning steps below.

**Section: {section_name}**

Query: {query}

STEPS:
{steps}

GUIDELINES:
1. Write a short intro paragraph summarizing key findings.
2. Use well-structured, readable language — plain but authoritative.
3. Every factual sentence **must** include an existing cite token like [BANK_2024:3].
4. Finish with a summary paragraph.
5. At the end, add a markdown **References:** list of all cite tokens.

Section Output:
"""

        missing = set()
        for attempt in range(self.RETRY_LIMIT + 1):
            prompt = ChatPromptTemplate.from_template(template)
            messages = prompt.format_messages(
                query=query,
                steps=steps_str,
                section_name=section_name
            )
            self.log_prompt("\n".join(str(m.content) for m in messages), "Synthesizer")

            answer = self.llm.invoke(messages).content.strip()
            self.log_response(answer, "Synthesizer")

            found_cites = set(self.CITE_RE.findall(answer))
            missing = required_cites - found_cites

            if not missing:
                return f"## {section_name}\n\n{answer}"

            logger.warning(f"Missing cites in section '{section_name}': {list(missing)[:3]} (attempt {attempt+1})")

        raise ValueError(f"❌ Failed to include required citations in section: {section_name}")


def create_ingestion_only_agents(llm):
    """Agents needed only for ingestion and preprocessing, not full agentic reasoning"""
    return {
        "chunk_rewriter": ChunkRewriteAgent(llm)
    }
def create_agents(llm, vector_store=None, model_name="unknown", tokenizer=None):
    """Create and return the set of specialized agents"""
    return {
        "planner": PlannerAgent(llm),
        "researcher": ResearchAgent(llm, vector_store) if vector_store else None,
        "reasoner": ReasoningAgent(llm),
        "synthesizer": SynthesisAgent(llm),
        "section_writer": SectionWriterAgent(llm, tokenizer=tokenizer),
        "report_agent": ReportWriterAgent(doc=None, model_name=model_name, llm=llm),
        "chunk_rewriter": ChunkRewriteAgent(llm)
    }
