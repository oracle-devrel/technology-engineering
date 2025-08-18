from docx import Document
from docx.shared import Inches
import matplotlib.pyplot as plt
import os
import uuid
import logging
import datetime
import matplotlib.pyplot as plt

import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

os.makedirs("charts", exist_ok=True)

def add_table(doc, table_data):
    """Create a professionally styled Word table from list of dicts."""
    if not table_data:
        return
    
    headers = []
    seen = set()
    for row in table_data:
        for k in row.keys():
            if k not in seen:
                headers.append(k)
                seen.add(k)

    # Create table with proper styling
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    
    # Style header row
    header_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = header_row.cells[i]
        cell.text = str(h)
        # Make header bold
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

    # Add data rows
    for row in table_data:
        row_cells = table.add_row().cells
        for i, h in enumerate(headers):
            row_cells[i].text = str(row.get(h, ""))



def make_chart(chart_data: dict, title: str = "") -> str | None:
    """Generate a chart with conditional formatting and fallback for list values."""
    import numpy as np
    import textwrap

    os.makedirs("charts", exist_ok=True)

    clean = {}
    for k, v in chart_data.items():
        # NEW: Reduce lists to latest entry if all elements are numeric
        if isinstance(v, list):
            if all(isinstance(i, (int, float)) for i in v):
                v = v[-1]  # use the latest value
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

    # Decide chart orientation based on label length and count - create more variety
    max_label_length = max(len(label) for label in labels) if labels else 0
    
    # More nuanced decision for chart orientation
    if len(clean) > 12:  # Many items -> horizontal
        horizontal = True
    elif max_label_length > 40:  # Very long labels -> horizontal  
        horizontal = True
    elif len(clean) <= 4 and max_label_length <= 20:  # Few items, short labels -> vertical
        horizontal = False
    elif len(clean) <= 6 and max_label_length <= 30:  # Medium items, medium labels -> vertical
        horizontal = False
    else:  # Default to horizontal for edge cases
        horizontal = True

    fig, ax = plt.subplots(figsize=(12, 8))  # Increased figure size for better readability

    if horizontal:
        # Wrap long labels for horizontal charts
        wrapped_labels = ['\n'.join(textwrap.wrap(label, width=40)) for label in labels]
        bars = ax.barh(wrapped_labels, values, color=["#2e7d32" if "aelwyn" in l.lower() else "#f9a825" if "elinexa" in l.lower() else "#4472C4" for l in labels])
        ax.set_xlabel("Value")
        ax.set_ylabel("Category")
        for bar in bars:
            width = bar.get_width()
            ax.annotate(f"{width:.1f}", xy=(width, bar.get_y() + bar.get_height() / 2), xytext=(5, 0),
                        textcoords="offset points", ha='left', va='center', fontsize=8)
    else:
        # Wrap long labels for vertical charts
        wrapped_labels = ['\n'.join(textwrap.wrap(label, width=15)) for label in labels]
        bars = ax.bar(range(len(labels)), values, color=["#2e7d32" if "aelwyn" in l.lower() else "#f9a825" if "elinexa" in l.lower() else "#4472C4" for l in labels])
        ax.set_ylabel("Value")
        ax.set_xlabel("Category")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(wrapped_labels, ha='center', va='top')
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}", xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 5),
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_title(title[:100])
    ax.grid(axis="y" if not horizontal else "x", linestyle="--", alpha=0.6)
    fig.tight_layout()

    filename = f"chart_{uuid.uuid4().hex}.png"
    path = os.path.join("charts", filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')  # Higher DPI and tight bbox for better quality
    plt.close(fig)
    return path




def append_to_doc(doc, section_data: dict, level: int = 2, citation_map: dict | None = None):
    """Append section to document with heading, paragraph, table, chart, and citations."""
    heading = section_data.get("heading", "Untitled Section")
    # Use the level parameter to control heading hierarchy
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
            # Add unique citation numbers at the end of the text
            unique_citations = sorted(set(citation_numbers))
            citations_str = " " + "".join([f"[{num}]" for num in unique_citations])
            text = text + citations_str
    
    if text:
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

        chart_path = make_chart(flattened_chart_data, title=heading)
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
        # naive estimate: 1 token ≈ 4 characters for English-like text
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

        # Group chunks by entity and preserve metadata
        grouped = defaultdict(list)
        grouped_metadata = defaultdict(list)
        for chunk in context_chunks:
            entity = chunk.get("_search_entity", "Unknown")
            grouped[entity].append(chunk.get("content", ""))
            # Preserve metadata for citations
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
            "sources": []
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

        # OPTIMIZED: Shorter, more focused prompt for faster processing
        prompt = f"""Extract key data for {entity} on {section_title}.

Return JSON:
{{"heading": "title", "text": "2-sentence summary", "table": [metrics], "chart_data": {{numbers}}}}

Data:
{text[:2000]}

CRITICAL: Never use possessive forms (no apostrophes). Instead of "manager's approval" write "manager approval" or "approval from manager". Use "N/A" for missing data. Valid JSON only."""


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
                    chart_data = ast.literal_eval(chart_data)
                except Exception:
                    chart_data = {}

            table = parsed.get("table", [])
            if isinstance(table, str):
                try:
                    table = ast.literal_eval(table)
                except Exception:
                    table = []

            return {
                "heading": parsed.get("heading", section_title),
                "text": parsed.get("text", ""),
                "table": table,
                "chart_data": chart_data,
                "sources": sources
            }

        except Exception as e:
            logger.error("❌ Failed to write single-entity section: %s", e)
            return {
                "heading": section_title,
                "text": f"Could not generate section due to error: {e}",
                "table": [],
                "chart_data": {},
                "sources": sources
            }

    def _write_comparison_section(self, section_title: str, grouped_chunks: dict, entities: list[str], grouped_metadata: dict | None = None) -> dict:
        import ast
        from agents.agent_factory import UniversalJSONCleaner

        if len(entities) != 2:
            raise ValueError("Comparison section requires exactly two entities.")

        entity_a, entity_b = entities
        text_a = "\n\n".join(grouped_chunks[entity_a])
        text_b = "\n\n".join(grouped_chunks[entity_b])

        # Construct prompt
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
    - Use analysis terms like: "Higher", "Lower", "Similar", "{entity_a} Only", "{entity_b} Only"
    - Do not echo file names or metadata
    - Keep values human-readable (e.g., "18,500 tonnes CO2e")
    
    CRITICAL: Never use possessive forms (no apostrophes). Instead of "company's target" write "company target" or "target for company".

    Respond only in JSON format.
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

            # Chart data cleanup
            chart_data = parsed.get("chart_data", {})
            if isinstance(chart_data, str):
                try:
                    chart_data = ast.literal_eval(chart_data)
                except Exception as e:
                    logger.warning("⚠️ Failed to parse chart_data: %s", e)
                    chart_data = {}
            if not isinstance(chart_data, dict):
                chart_data = {}

            # Table cleanup
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

            # Flatten chart_data if nested
            flat_chart_data = {}
            for k, v in chart_data.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat_chart_data[f"{k} - {sub_k}"] = sub_v
                else:
                    flat_chart_data[k] = v

            # Extract unique sources from metadata
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
                "sources": sources
            }

        except Exception as e:
            logger.error("⚠️ Failed to write comparison section: %s", e)
            # Still try to extract sources
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
                "sources": sources
            }



class ReportWriterAgent:
    def __init__(self, doc=None, model_name: str = "unknown", llm=None):
        # Don't store the document - create fresh one for each report
        self.model_name = model_name
        self.llm = llm  # Store LLM for generating summaries

    def _generate_executive_summary(self, sections: list[dict], is_comparison: bool, entities: list[str], target_language: str = "english", query: str | None = None) -> str:
        """Generate an executive summary based on actual section content and user query"""
        if not self.llm:
            return self._generate_intro_section(is_comparison, entities)
        
        # Extract key information from sections
        section_summaries = []
        for section in sections:
            heading = section.get("heading", "Unknown Section")
            text = section.get("text", "")
            if text:
                section_summaries.append(f"**{heading}**: {text}")
        
        sections_text = "\n\n".join(section_summaries)
        
        # Add language instruction if not English
        language_instruction = ""
        if target_language == "arabic":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in Arabic (العربية). Use professional Arabic business terminology."
        elif target_language == "spanish":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in Spanish. Use professional Spanish business terminology."
        elif target_language == "french":
            language_instruction = "\n\nIMPORTANT: Write the entire executive summary in French. Use professional French business terminology."
        
        # Include user query context if available
        query_context = ""
        if query:
            query_context = f"\nUser's Original Request:\n{query}\n"
        
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

Write in a professional, analytical tone. Focus on answering the user's specific request.{language_instruction}
"""
        
        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            return response
        except Exception as e:
            logger.warning(f"Failed to generate executive summary: {e}")
            return self._generate_intro_section(is_comparison, entities)

    def _generate_conclusion(self, sections: list[dict], is_comparison: bool, entities: list[str], target_language: str = "english", query: str | None = None) -> str:
        """Generate a conclusion based on actual section content and user query"""
        if not self.llm:
            return "This analysis provides insights based on available data from retrieved documents."
        
        # Extract key findings from sections
        key_findings = []
        for section in sections:
            heading = section.get("heading", "Unknown Section")
            text = section.get("text", "")
            table = section.get("table", [])
            
            # Extract key metrics from tables
            if table and isinstance(table, list):
                for row in table[:3]:  # Top 3 rows
                    if isinstance(row, dict):
                        metric = row.get("Metric", "")
                        if metric:
                            key_findings.append(f"{heading}: {metric}")
            
            if text:
                key_findings.append(f"{heading}: {text}")
        
        findings_text = "\n".join(key_findings[:8])  # Limit to prevent token overflow
        
        # Add language instruction if not English
        language_instruction = ""
        if target_language == "arabic":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in Arabic (العربية). Use professional Arabic business terminology."
        elif target_language == "spanish":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in Spanish. Use professional Spanish business terminology."
        elif target_language == "french":
            language_instruction = "\n\nIMPORTANT: Write the entire conclusion in French. Use professional French business terminology."
        
        # Include user query context if available
        query_context = ""
        if query:
            query_context = f"\nUser's Original Request:\n{query}\n"
        
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

Focus on providing value for the user's specific use case.{language_instruction}
"""
        
        try:
            response = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
            return response
        except Exception as e:
            logger.warning(f"Failed to generate conclusion: {e}")
            return "This analysis provides insights based on available data from retrieved documents."
    
    def _filter_failed_sections(self, sections: list[dict]) -> list[dict]:
        """Filter out sections that contain error messages or failed processing"""
        filtered_sections = []
        
        for section in sections:
            text = section.get("text", "")
            heading = section.get("heading", "")
            
            # Check for common error patterns
            error_patterns = [
                "Could not generate",
                "due to error:",
                "Expecting ',' delimiter:",
                "Failed to",
                "Error:",
                "Exception:",
                "Traceback"
            ]
            
            # Check if section contains error messages
            has_error = any(pattern in text for pattern in error_patterns)
            
            if not has_error:
                filtered_sections.append(section)
            else:
                logger.info(f"🚫 Filtered out failed section: {heading}")
        
        return filtered_sections
    
    def _apply_document_styling(self, doc):
        """Apply professional styling to the document"""
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Set default font for the document
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Style headings
        heading1_style = doc.styles['Heading 1']
        heading1_style.font.name = 'Times New Roman'
        heading1_style.font.size = Pt(18)
        heading1_style.font.bold = True
        heading1_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)  # Black
        
        heading2_style = doc.styles['Heading 2']
        heading2_style.font.name = 'Times New Roman'
        heading2_style.font.size = Pt(14)
        heading2_style.font.bold = True
        heading2_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)  # Black
    
    def _generate_report_title(self, is_comparison: bool, entities: list[str], query: str | None, sections: list[dict]) -> str:
        """Generate a dynamic, informative report title based on user query"""
        if query and self.llm:
            # Use LLM to generate a more specific title based on the query
            try:
                entity_context = f"{entities[0]} vs {entities[1]}" if is_comparison and len(entities) >= 2 else entities[0] if entities else "Organization"
                
                prompt = f"""Generate a concise, professional report title (max 10 words) based on:
User Query: {query}
Entities: {entity_context}
Type: {'Comparison' if is_comparison else 'Analysis'} Report

Return ONLY the title, no quotes or extra text."""
                
                title = self.llm.invoke([type("Msg", (object,), {"content": prompt})()]).content.strip()
                # Clean up the title
                title = title.replace('"', '').replace("'", '').strip()
                # Ensure it's not too long
                if len(title) > 100:
                    title = title[:97] + "..."
                return title
            except Exception as e:
                logger.warning(f"Failed to generate dynamic title: {e}")
                # Fall back to default title generation
        
        # Default title generation logic
        if query:
            # Extract key topics from the query
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
            # Infer from section headings
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
        """Add a professional report header with title, date, and metadata"""
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Main title
        title_paragraph = doc.add_heading(report_title, level=1)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add subtitle with entity information
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
        
        # Add generation date and metadata
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%H:%M")
        
        doc.add_paragraph()  # spacing
        
        # Create a professional metadata section
        metadata_paragraph = doc.add_paragraph()
        metadata_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        metadata_text = f"Generated on {date_str} at {time_str}\nPowered by OCI Generative AI"
        metadata_run = metadata_paragraph.add_run(metadata_text)
        metadata_run.font.size = Pt(10)
        metadata_run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)  # Gray color
        
        # Add separator line
        doc.add_paragraph()
        separator = doc.add_paragraph("─" * 50)
        separator.alignment = WD_ALIGN_PARAGRAPH.CENTER
        separator_run = separator.runs[0]
        separator_run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
        
        doc.add_paragraph()  # spacing after header
    
    def _detect_target_language(self, query: str | None) -> str:
        """Detect the target language from the query"""
        if not query:
            return "english"
        
        query_lower = query.lower()
        
        # Arabic language indicators
        arabic_indicators = [
            "بالعربية", "باللغة العربية", "in arabic", "arabic report", "تقرير", 
            "تحليل", "باللغة العربيه", "عربي", "arabic language"
        ]
        
        # Check for Arabic script
        arabic_chars = any('\u0600' <= char <= '\u06FF' for char in query)
        
        # Check for explicit language requests
        if any(indicator in query_lower for indicator in arabic_indicators) or arabic_chars:
            return "arabic"
        
        # Add more languages as needed
        if "en español" in query_lower or "in spanish" in query_lower:
            return "spanish"
        
        if "en français" in query_lower or "in french" in query_lower:
            return "french"
        
        return "english"
    
    def _ensure_language_consistency(self, sections: list[dict], target_language: str, query: str | None) -> list[dict]:
        """Ensure all sections are in the target language"""
        if not self.llm or target_language == "english":
            return sections
        
        logger.info(f"🔄 Ensuring language consistency for {target_language}")
        
        corrected_sections = []
        
        for section in sections:
            corrected_section = section.copy()
            
            # Check and translate heading if needed
            heading = section.get("heading", "")
            if heading and not self._is_in_target_language(heading, target_language):
                corrected_section["heading"] = self._translate_text(heading, target_language, "section heading")
            
            # Check and translate text if needed
            text = section.get("text", "")
            if text and not self._is_in_target_language(text, target_language):
                corrected_section["text"] = self._translate_text(text, target_language, "section text")
            
            # Handle table translations
            table = section.get("table", [])
            if table and isinstance(table, list):
                corrected_table = []
                for row in table:
                    if isinstance(row, dict):
                        corrected_row = {}
                        for key, value in row.items():
                            # Translate table headers and values
                            translated_key = self._translate_text(str(key), target_language, "table header") if not self._is_in_target_language(str(key), target_language) else str(key)
                            translated_value = self._translate_text(str(value), target_language, "table value") if not self._is_in_target_language(str(value), target_language) and not str(value).replace('.', '').replace(',', '').isdigit() else str(value)
                            corrected_row[translated_key] = translated_value
                        corrected_table.append(corrected_row)
                corrected_section["table"] = corrected_table
            
            corrected_sections.append(corrected_section)
        
        return corrected_sections
    
    def _is_in_target_language(self, text: str, target_language: str) -> bool:
        """Check if text is already in the target language"""
        if not text or target_language == "english":
            return True
        
        if target_language == "arabic":
            # Check if text contains Arabic characters
            arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
            total_chars = sum(1 for char in text if char.isalpha())
            if total_chars == 0:
                return True  # No alphabetic characters, assume it's fine
            return arabic_chars / total_chars > 0.3  # At least 30% Arabic characters
        
        # Add more language detection logic as needed
        return True  # Default to assuming it's correct
    
    def _translate_text(self, text: str, target_language: str, context: str = "") -> str:
        """Translate text to target language using LLM"""
        if not text or not self.llm:
            return text
        
        language_names = {
            "arabic": "Arabic",
            "spanish": "Spanish", 
            "french": "French"
        }
        
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
        """Fallback intro section when LLM is not available"""
        if is_comparison:
            comparison_note = (
                f"This report compares data between {entities[0]} and {entities[1]} across key topics."
            )
        else:
            comparison_note = f"This report presents information for {entities[0]}."

        return (
            f"{comparison_note} All data is sourced from retrieved documents and structured using LLM-based analysis.\n\n"
            "The analysis includes tables and charts where possible. Missing data is noted explicitly."
        )
    
    def _organize_sections_with_llm(self, sections: list[dict], query: str | None, entities: list[str]) -> list[dict]:
        """Use LLM to intelligently organize sections into a hierarchical structure"""
        if not query or not self.llm or not sections:
            return sections
        
        # Create a list of section titles
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
      "sections": [1, 3, 5]  // section numbers that belong under this category
    }},
    {{
      "title": "Another Main Category",
      "level": 1,
      "sections": [2, 4, 6]
    }}
  ],
  "orphan_sections": [7, 8]  // sections that don't fit under any main category
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
            
            # Clean and parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                structure = json.loads(json_str)
                
                # Build organized sections list
                organized = []
                used_sections = set()
                
                for category in structure.get("structure", []):
                    # Add main category as a header-only section
                    organized.append({
                        "heading": category.get("title", "Category"),
                        "level": 1,
                        "is_category_header": True
                    })
                    
                    # Add sections under this category
                    for section_num in category.get("sections", []):
                        idx = section_num - 1  # Convert to 0-based index
                        if 0 <= idx < len(sections) and idx not in used_sections:
                            section_copy = sections[idx].copy()
                            section_copy["level"] = 2
                            organized.append(section_copy)
                            used_sections.add(idx)
                
                # Add orphan sections at the end
                for section_num in structure.get("orphan_sections", []):
                    idx = section_num - 1
                    if 0 <= idx < len(sections) and idx not in used_sections:
                        section_copy = sections[idx].copy()
                        section_copy["level"] = 2
                        organized.append(section_copy)
                        used_sections.add(idx)
                
                # Add any sections not mentioned in the structure
                for i, section in enumerate(sections):
                    if i not in used_sections:
                        section_copy = section.copy()
                        section_copy["level"] = 2
                        organized.append(section_copy)
                
                return organized
                
        except Exception as e:
            logger.warning(f"Failed to organize sections with LLM: {e}")
            # Return original sections if organization fails
            pass
        
        # Return original sections if LLM organization fails or isn't attempted
        return sections
    
    
    
    def _build_references_section(self, sections: list[dict]) -> tuple[dict, str]:
        """Build a references section from all sources in sections and return citation map"""
        all_sources = []
        citation_map = {}
        citation_counter = 1
        
        # Collect all unique sources
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
        
        # Build references text
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
        
        # Detect requested language from query
        target_language = self._detect_target_language(query)
        logger.info(f"🌐 Detected target language: {target_language}")
        
        # Filter out failed sections if requested
        if filter_failures:
            sections = self._filter_failed_sections(sections)
            logger.info(f"📊 After filtering failures: {len(sections)} sections remaining")
        
        # Validate and fix language consistency across all sections
        if target_language != "english":
            sections = self._ensure_language_consistency(sections, target_language, query)
        
        # Create a fresh document for each report to prevent accumulation
        doc = Document()
        
        # Apply professional document styling
        self._apply_document_styling(doc)
        
        # Create reports directory if it doesn't exist
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Extract metadata from sections
        is_comparison = sections[0].get("is_comparison", False) if sections else False
        entities = sections[0].get("entities", []) if sections else []
        
        # Generate dynamic report title
        report_title = self._generate_report_title(is_comparison, entities, query, sections)
        
        # Add professional header
        self._add_report_header(doc, report_title, is_comparison, entities)

        # PARALLEL GENERATION of executive summary and conclusion while processing sections
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        summary_and_conclusion_futures = []
        
        if self.llm:  # Only if LLM is available for intelligent generation
            with ThreadPoolExecutor(max_workers=2) as summary_executor:
                # Start executive summary generation in parallel
                summary_future = summary_executor.submit(
                    self._generate_executive_summary, sections, is_comparison, entities, target_language, query
                )
                summary_and_conclusion_futures.append(("summary", summary_future))
                
                # Start conclusion generation in parallel
                conclusion_future = summary_executor.submit(
                    self._generate_conclusion, sections, is_comparison, entities, target_language, query
                )
                summary_and_conclusion_futures.append(("conclusion", conclusion_future))
                
                # Add executive summary
                doc.add_heading("Executive Summary", level=2)
                executive_summary = summary_future.result()  # Wait for completion
                doc.add_paragraph(executive_summary)
                doc.add_paragraph()  # spacing

                # Organize sections hierarchically using LLM
                organized_sections = self._organize_sections_with_llm(sections, query, entities)
                
                # Build citation map before adding sections
                citation_map, references_text = self._build_references_section(organized_sections)
                
                # Add organized sections with citations
                for section in organized_sections:
                    if section.get("is_category_header"):
                        # This is a main category header
                        doc.add_heading(section.get("heading", "Category"), level=1)
                    else:
                        # Regular section with appropriate level and citations
                        level = section.get("level", 2)
                        append_to_doc(doc, section, level=level, citation_map=citation_map)
                        doc.add_paragraph()  # spacing between sections

                # Add conclusion
                doc.add_heading("Conclusion", level=2)
                conclusion = conclusion_future.result()  # Wait for completion
                doc.add_paragraph(conclusion)
                
                # Add References section (already built above)
                if references_text:
                    doc.add_paragraph()  # spacing
                    doc.add_heading("References", level=2)
                    doc.add_paragraph(references_text)
        else:
            # Fallback for when no LLM is available
            doc.add_heading("Executive Summary", level=2)
            executive_summary = self._generate_intro_section(is_comparison, entities)
            doc.add_paragraph(executive_summary)
            doc.add_paragraph()  # spacing

            # Build citation map
            citation_map, references_text = self._build_references_section(sections)
            
            # Add all sections with citations (no LLM available for organization)
            for section in sections:
                append_to_doc(doc, section, level=2, citation_map=citation_map)
                doc.add_paragraph()  # spacing between sections

            doc.add_heading("Conclusion", level=2)
            conclusion = "This analysis provides insights based on available data from retrieved documents."
            doc.add_paragraph(conclusion)
            
            # Add References section (already built above)
            if references_text:
                doc.add_paragraph()  # spacing
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
        "text": "Both Elinexa and Aelwyn have committed to net-zero targets...",
        "table": [{"Bank": "Elinexa", "Target": "Net-zero 2050"},
                  {"Bank": "Aelwyn", "Target": "Net-zero 2050"}],
        "chart_data": {"Elinexa": 42, "Aelwyn": 36}
    }
    agent = ReportWriterAgent(doc)
    agent.write_report([sample_section])
