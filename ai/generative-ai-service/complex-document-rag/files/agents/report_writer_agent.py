from docx import Document
from docx.shared import Inches
import matplotlib.pyplot as plt
import os
import uuid
import logging
import datetime
import math
import re
from docx.oxml.shared import OxmlElement
from docx.text.run import Run

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

os.makedirs("charts", exist_ok=True)



_MD_TOKEN_RE = re.compile(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_)')

def add_inline_markdown_paragraph(doc, text: str):
    """
    Creates a paragraph and renders lightweight inline Markdown:
      **bold** or __bold__ → bold run
      *italic* or _italic_ → italic run
    Everything else is plain text. No links/lists/code handling.
    """
    p = doc.add_paragraph()
    i = 0
    for m in _MD_TOKEN_RE.finditer(text):
        # leading text
        if m.start() > i:
            p.add_run(text[i:m.start()])
        token = m.group(0)
        # strip the markers
        if token.startswith('**') or token.startswith('__'):
            content = token[2:-2]
            run = p.add_run(content)
            run.bold = True
        else:
            content = token[1:-1]
            run = p.add_run(content)
            run.italic = True
        i = m.end()
    # trailing text
    if i < len(text):
        p.add_run(text[i:])
    return p

def add_table(doc, table_data):
    """Create a Word table from list of dicts or list of lists, robustly."""
    if not table_data:
        return

    headers = []
    rows_normalized = []

    # Case 1: list of dicts
    if isinstance(table_data[0], dict):
        seen = set()
        for row in table_data:
            for k in row.keys():
                if k not in seen:
                    headers.append(k)
                    seen.add(k)
        rows_normalized = table_data

    # Case 2: list of lists
    elif isinstance(table_data[0], (list, tuple)):
        max_len = max(len(row) for row in table_data)
        headers = [f"Col {i+1}" for i in range(max_len)]
        for row in table_data:
            rows_normalized.append({headers[i]: row[i] if i < len(row) else "" 
                                    for i in range(max_len)})

    else:
        headers = ["Value"]
        rows_normalized = [{"Value": str(row)} for row in table_data]

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'

    header_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = header_row.cells[i]
        cell.text = str(h)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

    for row in rows_normalized:
        row_cells = table.add_row().cells
        for i, h in enumerate(headers):
            row_cells[i].text = str(row.get(h, ""))


def _color_for_label(label: str, entities: list[str] | tuple[str, ...] | None,
                     base="#a9bbbc", e1="#437c94", e2="#c74634") -> str:
    """Pick a bar color based on whether a label mentions one of the entities."""
    if not entities:
        return base
    lbl = label.lower()
    ents = [e for e in entities if isinstance(e, str)]
    if len(ents) >= 1 and ents[0].lower() in lbl:
        return e1
    if len(ents) >= 2 and ents[1].lower() in lbl:
        return e2
    return base


def detect_units(chart_data: dict, title: str = "") -> str:
    """Detect units of measure from chart data and title."""
    # Common patterns for currency
    currency_patterns = [
        (r'\$|USD|usd|dollar', 'USD'),
        (r'€|EUR|eur|euro', 'EUR'),
        (r'£|GBP|gbp|pound', 'GBP'),
        (r'¥|JPY|jpy|yen', 'JPY'),
        (r'₹|INR|inr|rupee', 'INR'),
    ]
    
    # Common patterns for other units - order matters!
    unit_patterns = [
        (r'million|millions|mn|mln|\$m|\$M', 'Million'),
        (r'billion|billions|bn|bln|\$b|\$B', 'Billion'),
        (r'thousand|thousands|k|\$k', 'Thousand'),
        (r'percentage|percent|%', '%'),
        (r'tonnes|tons|tonne|ton', 'Tonnes'),
        (r'co2e|CO2e|co2|CO2', 'CO2e'),
        (r'kwh|kWh|KWH', 'kWh'),
        (r'mwh|MWh|MWH', 'MWh'),
        (r'kg|kilogram|kilograms', 'kg'),
        (r'employees|headcount|people', 'Employees'),
        (r'days|day', 'Days'),
        (r'hours|hour|hrs', 'Hours'),
        (r'years|year|yrs', 'Years'),
    ]
    
    # Check title and keys for units - also check values if they're strings
    combined_text = title.lower() + " " + " ".join(str(k).lower() for k in chart_data.keys())
    # Also check string values which might contain unit info
    for v in chart_data.values():
        if isinstance(v, str):
            combined_text += " " + v.lower()
    
    detected_currency = None
    detected_scale = None
    detected_unit = None
    
    # Check for currency
    for pattern, unit in currency_patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            detected_currency = unit
            break
    
    # Check for scale (million, billion, etc.)
    for pattern, unit in unit_patterns[:4]:  # First 4 are scales
        if re.search(pattern, combined_text, re.IGNORECASE):
            detected_scale = unit
            break
    
    # Check for other units
    for pattern, unit in unit_patterns[4:]:  # Rest are units
        if re.search(pattern, combined_text, re.IGNORECASE):
            detected_unit = unit
            break
    
    # Combine detected elements
    if detected_currency and detected_scale:
        return f"{detected_scale} {detected_currency}"
    elif detected_currency:
        # If we detect currency but no scale, look for financial context clues
        if 'revenue' in combined_text or 'sales' in combined_text or 'income' in combined_text:
            # Financial data without explicit scale often means millions
            if 'fy' in combined_text or 'fiscal' in combined_text or 'quarterly' in combined_text:
                return "Million USD"  # Corporate financials are typically in millions
            return detected_currency
        return detected_currency
    elif detected_unit:
        if detected_scale and detected_unit not in ['%', 'Employees', 'Days', 'Hours', 'Years']:
            return f"{detected_scale} {detected_unit}"
        return detected_unit
    elif detected_scale:
        # If we only have scale (like "Million") without currency, check for financial context
        if any(term in combined_text for term in ['revenue', 'cost', 'profit', 'income', 'sales', 'expense', 'financial']):
            return f"{detected_scale} USD"
        return detected_scale
    
    # For financial metrics without explicit units, default to "Million USD"
    if any(term in combined_text for term in ['revenue', 'sales', 'profit', 'income', 'cost', 'expense', 'financial', 'fiscal', 'fy20']):
        return "Million USD"
    
    return "Value"  # Default fallback


def format_value_with_units(value: float, units: str) -> str:
    """Format a value with appropriate precision based on units."""
    if '%' in units:
        return f"{value:.1f}%"
    elif 'Million' in units or 'Billion' in units:
        return f"{value:,.1f}"
    elif value >= 1000:
        return f"{value:,.0f}"
    else:
        return f"{value:.1f}"


def make_chart(chart_data: dict, title: str = "", 
               entities: list[str] | tuple[str, ...] | None = None,
               units: str | None = None) -> str | None:
    """Generate a chart with conditional formatting and fallback for list values.
    If `entities` contains up to two names, bars whose labels include those names
    are highlighted in two distinct colors. Otherwise a default color is used.
    Units are detected automatically or can be passed explicitly.
    """

    import textwrap

    os.makedirs("charts", exist_ok=True)

    clean = {}
    for k, v in chart_data.items():
        # Reduce lists to latest numeric entry
        if isinstance(v, list):
            if all(isinstance(i, (int, float)) for i in v):
                v = v[-1]
            else:
                continue

        try:
            num = float(v)
            if not math.isnan(num) and not math.isinf(num):
                clean[str(k)[:80]] = num
        except Exception:
            continue

    if not clean:
        print("⚠️ No valid data to plot.")
        return None

    labels = list(clean.keys())
    values = list(clean.values())
    
    # Detect units if not provided
    if not units:
        units = detect_units(chart_data, title)
    
    # Update title to include units if not already present
    if units and units != "Value" and units.lower() not in title.lower():
        title = f"{title} ({units})"

    # Decide orientation
    max_label_length = max(len(label) for label in labels) if labels else 0
    if len(clean) > 12:
        horizontal = True
    elif max_label_length > 40:
        horizontal = True
    elif len(clean) <= 4 and max_label_length <= 20:
        horizontal = False
    elif len(clean) <= 6 and max_label_length <= 30:
        horizontal = False
    else:
        horizontal = True

    fig, ax = plt.subplots(figsize=(12, 8))

    if horizontal:
        wrapped_labels = ['\n'.join(textwrap.wrap(label, width=40)) for label in labels]
        colors = [_color_for_label(l, entities) for l in labels]
        bars = ax.barh(wrapped_labels, values, color=colors)
        ax.set_xlabel(units)  # Use detected units instead of "Value"
        ax.set_ylabel("Category")
        for bar in bars:
            width = bar.get_width()
            formatted_value = format_value_with_units(width, units)
            ax.annotate(formatted_value, xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0), textcoords="offset points",
                        ha='left', va='center', fontsize=8)
    else:
        wrapped_labels = ['\n'.join(textwrap.wrap(label, width=15)) for label in labels]
        colors = [_color_for_label(l, entities) for l in labels]
        bars = ax.bar(range(len(labels)), values, color=colors)
        ax.set_ylabel(units)  # Use detected units instead of "Value"
        ax.set_xlabel("Category")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(wrapped_labels, ha='center', va='top')
        for bar in bars:
            height = bar.get_height()
            formatted_value = format_value_with_units(height, units)
            ax.annotate(formatted_value, xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    ax.set_title(title[:100])
    ax.grid(axis="y" if not horizontal else "x", linestyle="--", alpha=0.6)
    fig.tight_layout()

    filename = f"chart_{uuid.uuid4().hex}.png"
    path = os.path.join("charts", filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return path


def append_to_doc(doc, section_data: dict, level: int = 2, citation_map: dict | None = None):
    """Append section to document with heading, paragraph, table, chart, and citations."""
    heading = section_data.get("heading", "Untitled Section")
    doc.add_heading(heading, level=level)

    text = section_data.get("text", "").strip()

    # Add citations to the text if sources are available
    if text and citation_map and section_data.get("sources"):
        citation_numbers = []
        for source in section_data.get("sources", []):
            source_key = f"{source.get('file', 'Unknown')}_{source.get('sheet', '')}_{source.get('entity', '')}"
            if source_key in citation_map:
                citation_numbers.append(citation_map[source_key])
        if citation_numbers:
            unique_citations = sorted(set(citation_numbers))
            citations_str = " " + "".join([f"[{num}]" for num in unique_citations])
            text = text + citations_str

    if text:
        add_inline_markdown_paragraph(doc, text)
        doc.add_paragraph(text)

    table_data = section_data.get("table", [])
    if isinstance(table_data, dict):
        table_data = [table_data]
    if isinstance(table_data, list) and table_data:
        add_table(doc, table_data)

    chart_data = section_data.get("chart_data", {})
    if isinstance(chart_data, dict) and chart_data:
        # Flatten nested chart data if needed
        flattened_chart_data = {}
        for k, v in chart_data.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    label = f"{k} ({sub_k})"
                    flattened_chart_data[label] = sub_v
            else:
                flattened_chart_data[k] = v

        # Pass dynamic entities (if present) so colors match those names
        entities = section_data.get("entities")
        # Pass units if available in section data
        units = section_data.get("units")
        chart_path = make_chart(flattened_chart_data, title=heading, entities=entities, units=units)
        if chart_path:
            doc.add_picture(chart_path, width=Inches(6))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = 1  # center


def save_doc(doc, filename: str = "_report.docx"):
    """Save the Word document."""
    doc.save(filename)
    logger.info(f"✅ Report saved: {filename}")


class SectionWriterAgent:
    def __init__(self, llm, tokenizer=None):
        self.llm = llm
        self.tokenizer = tokenizer
        if tokenizer:
            print("Tokenizer initialized for SectionWriterAgent")
        else:
            print("⚠️ No tokenizer provided for SectionWriterAgent")

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def log_token_count(self, text: str, tokenizer=None, label: str = "Prompt"):
        if not text:
            print(f"⚠️ Cannot log tokens: empty text for {label}")
            return
        if tokenizer:
            token_count = len(tokenizer.encode(text))
        else:
            token_count = self.estimate_tokens(text)
        print(f"{label} token count: {token_count}")

    def write_section(self, section_title: str, context_chunks: list[dict]) -> dict:
        from collections import defaultdict

        grouped = defaultdict(list)
        grouped_metadata = defaultdict(list)
        for chunk in context_chunks:
            entity = chunk.get("_search_entity", "Unknown")
            grouped[entity].append(chunk.get("content", ""))
            metadata = chunk.get("metadata", {})
            grouped_metadata[entity].append(metadata)

        entities = list(grouped.keys())
        if len(entities) == 2:
            return self._write_comparison_section(section_title, grouped, entities, grouped_metadata)
        elif len(entities) == 1:
            return self._write_single_entity_section(section_title, grouped, entities[0], grouped_metadata)
        else:
            logger.warning(f"⚠️ No valid entities found for section: {section_title}")
        return {
            "heading": section_title,
            "text": f"Insufficient data for analysis. Entities: {entities}",
            "table": [],
            "chart_data": {},
            "sources": [],
            # propagate for downstream report logic
            "is_comparison": False,
            "entities": entities
        }

    def _write_single_entity_section(self, section_title: str, grouped_chunks: dict, entity: str, grouped_metadata: dict | None = None) -> dict:
        text = "\n\n".join(grouped_chunks[entity])

        # Extract unique sources from metadata
        sources = []
        if grouped_metadata and entity in grouped_metadata:
            seen_sources = set()
            for metadata in grouped_metadata[entity]:
                source_key = f"{metadata.get('source', 'Unknown')}_{metadata.get('sheet', '')}"
                if source_key not in seen_sources:
                    sources.append({
                        "file": metadata.get("source", "Unknown"),
                        "sheet": metadata.get("sheet", ""),
                        "entity": entity
                    })
                    seen_sources.add(source_key)

        prompt = f"""Extract key data for {entity} on {section_title}.

Return JSON:
{{"heading": "title", "text": "2-sentence summary", "table": [metrics], "chart_data": {{numbers}}}}

Data:
{text[:2000]}

CRITICAL RULES:
1. NEVER use possessive forms or apostrophes (no 's). 
   - Wrong: "Oracle's revenue", "company's growth"
   - Right: "Oracle revenue", "company growth", "revenue of Oracle"
2. Use "N/A" for missing data.
3. Return valid JSON only - no apostrophes in text values."""

        try:
            self.log_token_count(prompt, self.tokenizer, label=f"SingleEntity Prompt ({section_title})")
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()

            from agents.agent_factory import UniversalJSONCleaner
            import ast

            json_str = UniversalJSONCleaner.clean_and_extract_json(response, expected_type="object")
            parsed = UniversalJSONCleaner.parse_with_validation(
                json_str,
                expected_structure="Object with 'heading', 'text', 'table', and 'chart_data' keys"
            )

            chart_data = parsed.get("chart_data", {})
            if isinstance(chart_data, str):
                try:
                    import ast as _ast
                    chart_data = _ast.literal_eval(chart_data)
                except Exception:
                    chart_data = {}

            table = parsed.get("table", [])
            if isinstance(table, str):
                try:
                    import ast as _ast
                    table = _ast.literal_eval(table)
                except Exception:
                    table = []

            return {
                "heading": parsed.get("heading", section_title),
                "text": parsed.get("text", ""),
                "table": table,
                "chart_data": chart_data,
                "sources": sources,
                # NEW: carry entity info so charts/titles can highlight correctly
                "is_comparison": False,
                "entities": [entity]
            }

        except Exception as e:
            logger.error("❌ Failed to write single-entity section: %s", e)
            return {
                "heading": section_title,
                "text": f"Could not generate section due to error: {e}",
                "table": [],
                "chart_data": {},
                "sources": sources,
                "is_comparison": False,
                "entities": [entity]
            }

    def _write_comparison_section(self, section_title: str, grouped_chunks: dict, entities: list[str], grouped_metadata: dict | None = None) -> dict:
        import ast
        from agents.agent_factory import UniversalJSONCleaner

        if len(entities) != 2:
            raise ValueError("Comparison section requires exactly two entities.")

        entity_a, entity_b = entities
        text_a = "\n\n".join(grouped_chunks[entity_a])
        text_b = "\n\n".join(grouped_chunks[entity_b])

        prompt = f"""
You are writing a structured section for a comparison report between {entity_a} and {entity_b}.

Topic: {section_title}

OBJECTIVE:
Summarize key data from the context and produce a clear, side-by-side comparison table.

Always follow this exact structure in your JSON output:
- heading: A short, descriptive title for the section
- text: A 1–2 sentence overview comparing {entity_a} and {entity_b}
- table: List of dicts formatted as: Metric | {entity_a} | {entity_b} | Analysis
- chart_data: A dictionary of comparable numeric values to plot

DATA:
=== {entity_a} ===
{text_a}

=== {entity_b} ===
{text_b}

INSTRUCTIONS:
- Extract specific metrics (numbers, %, dates) from the data
- Use "N/A" if one entity is missing a value
- Use analysis terms like: "Higher", "Lower", "Similar", "{entity_a} only", "{entity_b} only"
- Do not echo file names or metadata
- Keep values human-readable (e.g., "18,500 tonnes CO2e")

CRITICAL RULES:
1. NEVER use possessive forms or apostrophes (no 's).
   - Wrong: "Oracle's revenue", "company's performance"  
   - Right: "Oracle revenue", "company performance", "revenue of Oracle"
2. Ensure all JSON is valid - no apostrophes in text values.
3. Use proper escaping if quotes are needed in text.

Respond only in valid JSON format.
"""

        try:
            if self.tokenizer:
                self.log_token_count(prompt, self.tokenizer, label=f"Comparison Prompt ({section_title})")
            else:
                logger.warning("⚠️ No tokenizer available for token counting in SectionWriterAgent")

            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            logger.warning("🧪 RAW LLM OUTPUT:\n%s", response)

            json_str = UniversalJSONCleaner.clean_and_extract_json(response, expected_type="object")
            logger.debug("🧪 Cleaned JSON string before parsing:\n%s", json_str)

            parsed = UniversalJSONCleaner.parse_with_validation(
                json_str,
                expected_structure="Object with 'heading', 'text', 'table', and 'chart_data' keys"
            )

            chart_data = parsed.get("chart_data", {})
            if isinstance(chart_data, str):
                try:
                    chart_data = ast.literal_eval(chart_data)
                except Exception as e:
                    logger.warning("⚠️ Failed to parse chart_data: %s", e)
                    chart_data = {}
            if not isinstance(chart_data, dict):
                chart_data = {}

            table = parsed.get("table", [])
            if isinstance(table, str):
                try:
                    table = ast.literal_eval(table)
                except Exception:
                    table = []
            if isinstance(table, dict):
                table = [table]
            elif not isinstance(table, list):
                table = []

            validated = []
            for row in table:
                if not isinstance(row, dict):
                    continue
                validated_row = {
                    "Metric": row.get("Metric", "Unknown Metric"),
                    entity_a: row.get(entity_a, "N/A"),
                    entity_b: row.get(entity_b, "N/A"),
                    "Analysis": row.get("Analysis", "N/A")
                }
                if validated_row[entity_a] != "N/A" or validated_row[entity_b] != "N/A":
                    validated.append(validated_row)

            flat_chart_data = {}
            for k, v in chart_data.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat_chart_data[f"{k} - {sub_k}"] = sub_v
                else:
                    flat_chart_data[k] = v

            # Extract unique sources
            sources = []
            if grouped_metadata:
                seen_sources = set()
                for entity in entities:
                    if entity in grouped_metadata:
                        for metadata in grouped_metadata[entity]:
                            source_key = f"{metadata.get('source', 'Unknown')}_{metadata.get('sheet', '')}_{entity}"
                            if source_key not in seen_sources:
                                sources.append({
                                    "file": metadata.get("source", "Unknown"),
                                    "sheet": metadata.get("sheet", ""),
                                    "entity": entity
                                })
                                seen_sources.add(source_key)

            return {
                "heading": parsed.get("heading", section_title),
                "text": parsed.get("text", ""),
                "table": validated,
                "chart_data": flat_chart_data,
                "sources": sources,
                # NEW: signal comparison + entities for downstream styling and charts
                "is_comparison": True,
                "entities": [entity_a, entity_b]
            }

        except Exception as e:
            logger.error("⚠️ Failed to write comparison section: %s", e)
            sources = []
            if grouped_metadata:
                seen_sources = set()
                for entity in entities:
                    if entity in grouped_metadata:
                        for metadata in grouped_metadata[entity]:
                            source_key = f"{metadata.get('source', 'Unknown')}_{metadata.get('sheet', '')}_{entity}"
                            if source_key not in seen_sources:
                                sources.append({
                                    "file": metadata.get("source", "Unknown"),
                                    "sheet": metadata.get("sheet", ""),
                                    "entity": entity
                                })
                                seen_sources.add(source_key)

            return {
                "heading": section_title,
                "text": f"Could not generate summary due to error: {e}",
                "table": [],
                "chart_data": {},
                "sources": sources,
                "is_comparison": True,
                "entities": entities
            }


class ReportWriterAgent:
    def __init__(self, doc=None, model_name: str = "unknown", llm=None):
        self.model_name = model_name
        self.llm = llm  # Store LLM for generating summaries

    def _generate_executive_summary(self, sections: list[dict], is_comparison: bool, entities: list[str], target_language: str = "english", query: str | None = None) -> str:
        if not self.llm:
            return self._generate_intro_section(is_comparison, entities)

        section_summaries = []
        for section in sections:
            heading = section.get("heading", "Unknown Section")
            text = section.get("text", "")
            if text:
                section_summaries.append(f"{heading}: {text}")

        sections_text = "\n\n".join(section_summaries)

        language_instruction = ""
        if target_language == "arabic":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in Arabic (العربية). Use professional Arabic business terminology."
        elif target_language == "spanish":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in Spanish. Use professional Spanish business terminology."
        elif target_language == "french":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in French. Use professional French business terminology."

        query_context = f"\nUser's Original Request:\n{query}\n" if query else ""

        if is_comparison:
            prompt = f"""
You are writing an executive summary for a comparison report between {entities[0]} and {entities[1]}.
{query_context}
Based on the user's request and the following section summaries, create a 2-3 paragraph executive summary that:
1. Directly addresses what the user asked for
2. Highlights the most significant findings and differences relevant to their query
3. Provides a clear overview of how the report answers their specific questions

Section Summaries:
{sections_text}

CRITICAL: Never use possessive forms (no apostrophes). Write "Oracle revenue" not "Oracle's revenue", "company performance" not "company's performance".

Write in a professional, analytical tone. Focus on answering the user's specific request.{language_instruction}
"""
        else:
            prompt = f"""
You are writing an executive summary for a report about {entities[0] if entities else 'the organization'}.
{query_context}
Based on the user's request and the following section summaries, create a 2-3 paragraph executive summary that:
1. Directly addresses what the user asked for
2. Highlights the most significant findings relevant to their query
3. Provides a clear overview of how the report answers their specific questions

Section Summaries:
{sections_text}

CRITICAL: Never use possessive forms (no apostrophes). Write "Oracle revenue" not "Oracle's revenue", "company performance" not "company's performance".

Write in a professional, analytical tone. Focus on answering the user's specific request.{language_instruction}
"""

        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            return response
        except Exception as e:
            logger.warning(f"Failed to generate executive summary: {e}")
            return self._generate_intro_section(is_comparison, entities)

    def _generate_conclusion(self, sections: list[dict], is_comparison: bool, entities: list[str], target_language: str = "english", query: str | None = None) -> str:
        if not self.llm:
            return "This analysis provides insights based on available data from retrieved documents."

        key_findings = []
        for section in sections:
            heading = section.get("heading", "Unknown Section")
            text = section.get("text", "")
            table = section.get("table", [])

            if table and isinstance(table, list):
                for row in table[:3]:
                    if isinstance(row, dict):
                        metric = row.get("Metric", "")
                        if metric:
                            key_findings.append(f"{heading}: {metric}")

            if text:
                key_findings.append(f"{heading}: {text}")

        findings_text = "\n".join(key_findings[:8])

        language_instruction = ""
        if target_language == "arabic":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in Arabic (العربية). Use professional Arabic business terminology."
        elif target_language == "spanish":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in Spanish. Use professional Spanish business terminology."
        elif target_language == "french":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in French. Use professional French business terminology."

        query_context = f"\nUser's Original Request:\n{query}\n" if query else ""

        if is_comparison:
            prompt = f"""
Based on the analysis of {entities[0]} and {entities[1]}, write a conclusion that directly answers the user's request.
{query_context}
Key Findings:
{findings_text}

Write 2-3 paragraphs that:
- Directly answer what the user asked for
- Summarize the main differences and similarities relevant to their query
- Provide actionable insights based on their specific needs
- Include specific recommendations if appropriate

CRITICAL: Never use possessive forms (no apostrophes). Write "Oracle revenue" not "Oracle's revenue", "company growth" not "company's growth".

Focus on providing value for the user's specific use case.{language_instruction}
"""
        else:
            prompt = f"""
Based on the analysis of {entities[0] if entities else 'the organization'}, write a conclusion that directly answers the user's request.
{query_context}
Key Findings:
{findings_text}

Write 2-3 paragraphs that:
- Directly answer what the user asked for
- Summarize the main insights relevant to their query
- Provide actionable insights based on their specific needs
- Include specific recommendations if appropriate

CRITICAL: Never use possessive forms (no apostrophes). Write "Oracle revenue" not "Oracle's revenue", "company growth" not "company's growth".

Focus on providing value for the user's specific use case.{language_instruction}
"""

        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            return response
        except Exception as e:
            logger.warning(f"Failed to generate conclusion: {e}")
            return "This analysis provides insights based on available data from retrieved documents."

    def _filter_failed_sections(self, sections: list[dict]) -> list[dict]:
        filtered_sections = []
        error_patterns = [
            "Could not generate",
            "due to error:",
            "Expecting ',' delimiter:",
            "Failed to",
            "Error:",
            "Exception:",
            "Traceback"
        ]
        for section in sections:
            text = section.get("text", "")
            heading = section.get("heading", "")
            has_error = any(pattern in text for pattern in error_patterns)
            if not has_error:
                filtered_sections.append(section)
            else:
                logger.info(f"🚫 Filtered out failed section: {heading}")
        return filtered_sections

    def _apply_document_styling(self, doc):
        from docx.shared import Pt, RGBColor
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        heading1_style = doc.styles['Heading 1']
        heading1_style.font.name = 'Times New Roman'
        heading1_style.font.size = Pt(18)
        heading1_style.font.bold = True
        heading1_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
        heading2_style = doc.styles['Heading 2']
        heading2_style.font.name = 'Times New Roman'
        heading2_style.font.size = Pt(14)
        heading2_style.font.bold = True
        heading2_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    def _generate_report_title(self, is_comparison: bool, entities: list[str], query: str | None, sections: list[dict]) -> str:
        if query and self.llm:
            try:
                entity_context = f"{entities[0]} vs {entities[1]}" if is_comparison and len(entities) >= 2 else entities[0] if entities else "Organization"
                prompt = f"""Generate a concise, professional report title (max 10 words) based on:
User Query: {query}
Entities: {entity_context}
Type: {'Comparison' if is_comparison else 'Analysis'} Report

CRITICAL: Never use possessive forms (no apostrophes). Write "Oracle Performance" not "Oracle's Performance".

Return ONLY the title, no quotes or extra text."""
                title = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
                title = title.replace('"', '').replace("'", '').strip()
                if len(title) > 100:
                    title = title[:97] + "..."
                return title
            except Exception as e:
                logger.warning(f"Failed to generate dynamic title: {e}")

        if query:
            query_lower = query.lower()
            if "esg" in query_lower or "sustainability" in query_lower:
                topic_type = "ESG & Sustainability"
            elif "financial" in query_lower or "performance" in query_lower:
                topic_type = "Financial Performance"
            elif "risk" in query_lower:
                topic_type = "Risk Assessment"
            elif "governance" in query_lower:
                topic_type = "Corporate Governance"
            elif "climate" in query_lower or "carbon" in query_lower:
                topic_type = "Climate & Environmental"
            else:
                topic_type = "Business Analysis"
        else:
            section_topics = [s.get("heading", "") for s in sections[:3]]
            if any("climate" in h.lower() or "carbon" in h.lower() for h in section_topics):
                topic_type = "Climate & Environmental"
            elif any("esg" in h.lower() or "sustainability" in h.lower() for h in section_topics):
                topic_type = "ESG & Sustainability"
            else:
                topic_type = "Business Analysis"

        if is_comparison and len(entities) >= 2:
            return f"{topic_type} Report: {entities[0]} vs {entities[1]}"
        elif entities:
            return f"{topic_type} Report: {entities[0]}"
        else:
            return f"{topic_type} Report"

    def _add_report_header(self, doc, report_title: str, is_comparison: bool, entities: list[str]):
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        title_paragraph = doc.add_heading(report_title, level=1)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if is_comparison and len(entities) >= 2:
            subtitle = f"Comparative Analysis: {entities[0]} and {entities[1]}"
        elif entities:
            subtitle = f"Analysis of {entities[0]}"
        else:
            subtitle = "Comprehensive Analysis Report"

        subtitle_paragraph = doc.add_paragraph(subtitle)
        subtitle_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_run = subtitle_paragraph.runs[0]
        subtitle_run.font.size = Pt(12)
        subtitle_run.italic = True

        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%H:%M")

        doc.add_paragraph()
        metadata_paragraph = doc.add_paragraph()
        metadata_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        metadata_text = f"Generated on {date_str} at {time_str}\nPowered by OCI Generative AI"
        metadata_run = metadata_paragraph.add_run(metadata_text)
        metadata_run.font.size = Pt(10)
        metadata_run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)

        doc.add_paragraph()
        separator = doc.add_paragraph("─" * 50)
        separator.alignment = WD_ALIGN_PARAGRAPH.CENTER
        separator_run = separator.runs[0]
        separator_run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
        doc.add_paragraph()

    def _detect_target_language(self, query: str | None) -> str:
        if not query:
            return "english"
        q = query.lower()
        arabic_indicators = [
            "بالعربية", "باللغة العربية", "in arabic", "arabic report", "تقرير",
            "تحليل", "باللغة العربيه", "عربي", "arabic language"
        ]
        arabic_chars = any('\u0600' <= char <= '\u06FF' for char in query)
        if any(ind in q for ind in arabic_indicators) or arabic_chars:
            return "arabic"
        if "en español" in q or "in spanish" in q:
            return "spanish"
        if "en français" in q or "in french" in q:
            return "french"
        return "english"

    def _ensure_language_consistency(self, sections: list[dict], target_language: str, query: str | None) -> list[dict]:
        if not self.llm or target_language == "english":
            return sections
        logger.info(f"🔄 Ensuring language consistency for {target_language}")
        corrected_sections = []
        for section in sections:
            corrected_section = section.copy()
            heading = section.get("heading", "")
            text = section.get("text", "")
            table = section.get("table", [])

            if heading and not self._is_in_target_language(heading, target_language):
                corrected_section["heading"] = self._translate_text(heading, target_language, "section heading")
            if text and not self._is_in_target_language(text, target_language):
                corrected_section["text"] = self._translate_text(text, target_language, "section text")

            if table and isinstance(table, list):
                corrected_table = []
                for row in table:
                    if isinstance(row, dict):
                        corrected_row = {}
                        for key, value in row.items():
                            k = str(key)
                            v = str(value)
                            translated_key = self._translate_text(k, target_language, "table header") if not self._is_in_target_language(k, target_language) else k
                            # keep numeric strings unchanged
                            if not self._is_in_target_language(v, target_language) and not v.replace('.', '').replace(',', '').isdigit():
                                translated_value = self._translate_text(v, target_language, "table value")
                            else:
                                translated_value = v
                            corrected_row[translated_key] = translated_value
                        corrected_table.append(corrected_row)
                corrected_section["table"] = corrected_table

            corrected_sections.append(corrected_section)
        return corrected_sections

    def _is_in_target_language(self, text: str, target_language: str) -> bool:
        if not text or target_language == "english":
            return True
        if target_language == "arabic":
            arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
            total_chars = sum(1 for char in text if char.isalpha())
            if total_chars == 0:
                return True
            return arabic_chars / total_chars > 0.3
        return True

    def _translate_text(self, text: str, target_language: str, context: str = "") -> str:
        if not text or not self.llm:
            return text
        language_names = {"arabic": "Arabic", "spanish": "Spanish", "french": "French"}
        target_lang_name = language_names.get(target_language, target_language.title())
        prompt = f"""Translate the following {context} to {target_lang_name}. 
Maintain the professional tone and technical accuracy. 
If it's already in {target_lang_name}, return it unchanged.

Text to translate: {text}

Translation:"""
        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            logger.info(f"Translated {context}: '{text[:50]}...' → '{response[:50]}...'")
            return response
        except Exception as e:
            logger.warning(f"Failed to translate {context}: {e}")
            return text

    def _generate_intro_section(self, is_comparison: bool, entities: list[str]) -> str:
        if is_comparison:
            comparison_note = f"This report compares data between {entities[0]} and {entities[1]} across key topics."
        else:
            comparison_note = f"This report presents information for {entities[0]}."
        return (
            f"{comparison_note} All data is sourced from retrieved documents and structured using LLM-based analysis.\n\n"
            "The analysis includes tables and charts where possible. Missing data is noted explicitly."
        )

    def _organize_sections_with_llm(self, sections: list[dict], query: str | None, entities: list[str]) -> list[dict]:
        if not query or not self.llm or not sections:
            return sections
        section_info = []
        for i, section in enumerate(sections):
            section_info.append(f"{i+1}. {section.get('heading', 'Untitled Section')}")
        sections_list = "\n".join(section_info)

        prompt = f"""You are organizing sections for a report about {', '.join(entities)}.

User's Original Request:
{query}

Available Sections (numbered):
{sections_list}

Based on the user's request, create a hierarchical structure for these sections. The user's request may contain numbered main categories (like 1) Climate Impact, 2) Social Impact, etc.).

Return a JSON structure that organizes these sections hierarchically. Use the section numbers to reference them.

Format:
{{
  "structure": [
    {{
      "title": "Main Category Title from User's Request",
      "level": 1,
      "sections": [1, 3, 5]
    }},
    {{
      "title": "Another Main Category",
      "level": 1,
      "sections": [2, 4, 6]
    }}
  ],
  "orphan_sections": [7, 8]
}}

IMPORTANT:
- Extract main category titles from the user's request if they provided structured sections
- Group related sections under appropriate main categories
- Use level 1 for main categories, sections will be level 2
- List any sections that don't fit as orphan_sections
- Use the exact section numbers from the list above

Return ONLY valid JSON."""

        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            import json, re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                structure = json.loads(json_str)

                organized = []
                used_sections = set()

                for category in structure.get("structure", []):
                    organized.append({
                        "heading": category.get("title", "Category"),
                        "level": 1,
                        "is_category_header": True
                    })
                    for section_num in category.get("sections", []):
                        idx = section_num - 1
                        if 0 <= idx < len(sections) and idx not in used_sections:
                            section_copy = sections[idx].copy()
                            section_copy["level"] = 2
                            organized.append(section_copy)
                            used_sections.add(idx)

                for section_num in structure.get("orphan_sections", []):
                    idx = section_num - 1
                    if 0 <= idx < len(sections) and idx not in used_sections:
                        section_copy = sections[idx].copy()
                        section_copy["level"] = 2
                        organized.append(section_copy)
                        used_sections.add(idx)

                for i, section in enumerate(sections):
                    if i not in used_sections:
                        section_copy = section.copy()
                        section_copy["level"] = 2
                        organized.append(section_copy)

                return organized
        except Exception as e:
            logger.warning(f"Failed to organize sections with LLM: {e}")

        return sections

    def _build_references_section(self, sections: list[dict]) -> tuple[dict, str]:
        all_sources = []
        citation_map = {}
        citation_counter = 1
        seen_sources = set()
        for section in sections:
            sources = section.get("sources", [])
            for source in sources:
                source_key = f"{source.get('file', 'Unknown')}_{source.get('sheet', '')}_{source.get('entity', '')}"
                if source_key not in seen_sources:
                    all_sources.append(source)
                    citation_map[source_key] = citation_counter
                    citation_counter += 1
                    seen_sources.add(source_key)

        references_text = []
        for i, source in enumerate(all_sources, 1):
            file_name = source.get("file", "Unknown")
            sheet = source.get("sheet", "")
            entity = source.get("entity", "")
            if sheet:
                ref_text = f"[{i}] {file_name}, Sheet: {sheet}"
            else:
                ref_text = f"[{i}] {file_name}"
            if entity:
                ref_text += f" ({entity})"
            references_text.append(ref_text)

        return citation_map, "\n".join(references_text)

    def write_report(self, sections: list[dict], filter_failures: bool = True, query: str | None = None) -> str:
        if not isinstance(sections, list):
            raise TypeError("Expected list of sections")

        target_language = self._detect_target_language(query)
        logger.info(f"🌐 Detected target language: {target_language}")

        if filter_failures:
            sections = self._filter_failed_sections(sections)
            logger.info(f"📊 After filtering failures: {len(sections)} sections remaining")

        if target_language != "english":
            sections = self._ensure_language_consistency(sections, target_language, query)

        doc = Document()
        self._apply_document_styling(doc)

        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)

        # NEW: infer comparison/entity context from first valid section (or defaults)
        is_comparison = False
        entities: list[str] = []
        for s in sections:
            if "entities" in s:
                entities = list(s.get("entities") or [])
            if "is_comparison" in s:
                is_comparison = bool(s.get("is_comparison"))
            if entities:
                break

        report_title = self._generate_report_title(is_comparison, entities, query, sections)
        self._add_report_header(doc, report_title, is_comparison, entities)

        from concurrent.futures import ThreadPoolExecutor
        if self.llm:
            with ThreadPoolExecutor(max_workers=2) as summary_executor:
                summary_future = summary_executor.submit(
                    self._generate_executive_summary, sections, is_comparison, entities, target_language, query
                )
                conclusion_future = summary_executor.submit(
                    self._generate_conclusion, sections, is_comparison, entities, target_language, query
                )

                doc.add_heading("Executive Summary", level=2)
                executive_summary = summary_future.result()
                add_inline_markdown_paragraph(doc, executive_summary)
                doc.add_paragraph(executive_summary)
                doc.add_paragraph()

                organized_sections = self._organize_sections_with_llm(sections, query, entities)
                citation_map, references_text = self._build_references_section(organized_sections)

                for section in organized_sections:
                    if section.get("is_category_header"):
                        doc.add_heading(section.get("heading", "Category"), level=1)
                    else:
                        level = section.get("level", 2)
                        append_to_doc(doc, section, level=level, citation_map=citation_map)
                        doc.add_paragraph()

                doc.add_heading("Conclusion", level=2)
                conclusion = conclusion_future.result()
                add_inline_markdown_paragraph(doc, conclusion)
                doc.add_paragraph(conclusion)

                if references_text:
                    doc.add_paragraph()
                    doc.add_heading("References", level=2)
                    doc.add_paragraph(references_text)
        else:
            doc.add_heading("Executive Summary", level=2)
            executive_summary = self._generate_intro_section(is_comparison, entities)
            doc.add_paragraph(executive_summary)
            doc.add_paragraph()

            citation_map, references_text = self._build_references_section(sections)
            for section in sections:
                append_to_doc(doc, section, level=2, citation_map=citation_map)
                doc.add_paragraph()

            doc.add_heading("Conclusion", level=2)
            conclusion = "This analysis provides insights based on available data from retrieved documents."
            doc.add_paragraph(conclusion)
            if references_text:
                doc.add_paragraph()
                doc.add_heading("References", level=2)
                doc.add_paragraph(references_text)

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"report_{self.model_name}_{now}.docx"
        filepath = os.path.join(reports_dir, filename)
        save_doc(doc, filepath)
        return filepath


# Example usage
if __name__ == "__main__":
    doc = Document()
    sample_section = {
        "heading": "Climate Commitments",
        "text": "Both Acme Bank and Globex Bank have committed to net-zero targets...",
        "table": [{"Bank": "Acme Bank", "Target": "Net-zero 2050"},
                  {"Bank": "Globex Bank", "Target": "Net-zero 2050"}],
        "chart_data": {"Acme Bank": 42, "Globex Bank": 36},
        # NEW: tell the pipeline which two entities are being compared
        "entities": ["Acme Bank", "Globex Bank"],
        "is_comparison": True
    }
    agent = ReportWriterAgent(doc)
    agent.write_report([sample_section])
