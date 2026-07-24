#!/usr/bin/env python3
"""
Disable telemetry for various libraries to prevent startup errors.
Import this module at the very beginning of your main script.
"""

import os

# Disable telemetry for various libraries
def disable_all_telemetry():
    """Disable telemetry for all known libraries that might send it."""
    
    # Disable LangChain telemetry
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGCHAIN_ENDPOINT"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""
    os.environ["LANGCHAIN_PROJECT"] = ""
    
    # Disable ChromaDB telemetry
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    os.environ["CHROMA_TELEMETRY_IMPL"] = "none"
    
    # Disable Hugging Face telemetry
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"
    
    # Disable other common telemetry
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["TELEMETRY_DISABLED"] = "1"
    
    # Silent by default — this is startup plumbing, and it was the first thing on
    # screen in a demo. VERBOSE=1 brings it back.
    if os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes"):
        print("✅ Telemetry disabled for all libraries")

# Auto-disable when imported
disable_all_telemetry()
