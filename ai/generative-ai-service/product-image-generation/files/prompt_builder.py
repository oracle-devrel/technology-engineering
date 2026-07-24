"""
Prompt builder for SKU lifestyle imagery.
Translates structured product inputs into effective image generation prompts,
optimized for current model capabilities (no text, no complex spatial specs).
"""

# Shot type → visual direction mapping
SHOT_STYLES = {
    "Lifestyle — Editorial":  "editorial lifestyle photography, clean composition, aspirational mood",
    "Lifestyle — Candid":     "candid lifestyle photography, natural light, authentic atmosphere",
    "Flat Lay":               "flat lay product photography, overhead shot, arranged on clean surface",
    "On-Model":               "on-model product photography, full or partial figure, natural pose",
    "Product Only":           "isolated product photography, clean background, studio lighting",
}

# Market → visual/demographic context
MARKET_CONTEXTS = {
    "Global / Neutral":         "neutral setting, diverse aesthetic",
    "Middle East":              "warm tones, refined luxury aesthetic, elegant atmosphere",
    "Western Europe":           "understated elegance, muted palette, northern European light",
    "North America":            "bright natural light, approachable and aspirational feel",
    "South & Southeast Asia":   "warm ambient light, rich textures, vibrant but tasteful setting",
}

# Setting → environment descriptors
SETTING_DESCRIPTORS = {
    "Minimal Studio":       "minimal white studio, soft even lighting, clean backdrop",
    "Home / Interior":      "warm home interior, natural materials, lifestyle context",
    "Outdoor / Urban":      "urban outdoor setting, architectural background, natural daylight",
    "Café / Workspace":     "café or workspace setting, warm ambient light, lifestyle props",
    "Nature / Travel":      "natural outdoor environment, open space, travel atmosphere",
}


def build_prompt(
    product_name: str,
    description: str,
    market: str,
    shot_type: str,
    setting: str,
) -> str:
    """
    Constructs an optimized prompt for lifestyle/product image generation.
    Avoids requesting text, complex spatial layouts, or precise technical specs
    that current models handle poorly.
    """
    shot_style   = SHOT_STYLES.get(shot_type, "")
    market_ctx   = MARKET_CONTEXTS.get(market, "")
    setting_desc = SETTING_DESCRIPTORS.get(setting, "")

    # Base product description — keep it visual and qualitative
    product_context = product_name
    if description.strip():
        product_context += f", {description.strip().rstrip('.')}"

    prompt = (
        f"{shot_style}, {setting_desc}, featuring {product_context}. "
        f"{market_ctx}. "
        f"High quality commercial photography aesthetic, no text, no logos, "
        f"photorealistic, sharp focus, professional color grading."
    )

    return prompt
