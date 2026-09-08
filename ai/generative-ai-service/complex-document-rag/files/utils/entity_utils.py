"""Deterministic, human-in-the-loop entity-name suggestion.

The entity tag is the join key between ingestion and retrieval: retrieval filters
chunks with an exact-match `where={"entity": <name>.lower()}`, so the name chosen at
ingestion must be reproduced exactly at query time. Relying on an LLM to re-extract that
name from the prompt is non-deterministic and varies by model, which silently yields
empty results. Instead we derive up to N candidate names from the filename with a plain
regex and let the user pick (or override) — deterministic, model-independent, confirmed.
"""
import re
from pathlib import Path

# Tokens that describe the document, not the party — stripped from suggestions.
DOC_TYPE_TOKENS = {
    "msa", "agreement", "contract", "tender", "proposal", "rfq", "rfp", "sow", "nda",
    "bid", "offer", "quote", "quotation", "draft", "final", "signed", "execution",
    "copy", "detailed", "demo", "report", "standard", "response", "submission",
    "v1", "v2", "v3", "rev", "r1", "r2", "en", "de", "fr", "es", "shaped",
}


def _camel_split(token: str) -> list[str]:
    """Split CamelCase / alnum runs: 'NorthBridge' -> ['North','Bridge']."""
    return re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", token) or [token]


def suggest_entities_from_filename(filename: str, max_variants: int = 3) -> list[str]:
    """Return up to `max_variants` candidate entity names derived from a filename.

    Ordered most-specific first: original tokens minus doc-type words, then a
    CamelCase-expanded variant, then the full stem. Deduplicated case-insensitively.
    """
    stem = re.sub(r"\.(pdf|xlsx?|docx?|csv|txt)$", "", str(Path(filename).name), flags=re.I)
    parts = [p for p in re.split(r"[_\-\s]+", stem) if p]
    if not parts:
        return []

    core_orig = [p for p in parts if p.lower() not in DOC_TYPE_TOKENS]
    expanded = [w for p in parts for w in _camel_split(p)]
    core_exp = [w for w in expanded if w.lower() not in DOC_TYPE_TOKENS]

    candidates = [
        " ".join(core_orig),                                   # 'NorthBridge'
        " ".join(core_exp),                                    # 'North Bridge'
        " ".join(_camel_split(core_orig[0])) if core_orig else "",
        " ".join(expanded),                                    # 'North Bridge MSA'
    ]

    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        c = c.strip()
        key = c.lower()
        if c and key not in seen:
            seen.add(key)
            out.append(c)
    return out[:max_variants]
