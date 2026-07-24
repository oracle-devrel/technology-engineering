import base64
import io
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from src.grok_openai_image import generate_from_env

# Resolve paths from the repo root, not the process CWD (avoids wrong/missing photos when
# uvicorn is started from another directory — a common reason the "old" or stock image appears).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = _PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Photo overlay geometry (fractions of width / height). MUST stay in sync with _paste_exact_employee_photo.
# Two-column layout tuned for a 16:9 card:
#   left margin 7%  | photo column 7-36%  | gap 36-43%  | text column 43-93%  | right margin 7%
# This gives the body text a 50% wide column — comfortable for paragraph wrapping in Georgia at body size.
_PHOTO_COLUMN_X0_FRAC = 0.070
_PHOTO_COLUMN_W_FRAC = 0.290
_PHOTO_TARGET_W_FRAC = 0.235
_PHOTO_TARGET_H_FRAC = 0.330
_PHOTO_TOP_FRAC = 0.250
# Matches spacing below photo + single-line name row in _paste_exact_employee_photo (approximate).
_PHOTO_NAME_GAP_BELOW_FRAC = 0.030
_PHOTO_NAME_ROW_FRAC = 0.070
_PHOTO_NAME_STRIP_BOTTOM_FRAC = (
    _PHOTO_TOP_FRAC + _PHOTO_TARGET_H_FRAC + _PHOTO_NAME_GAP_BELOW_FRAC + _PHOTO_NAME_ROW_FRAC
)

# Left edge of the right-hand text column. Tightened so body sits closer to the photo.
_BODY_TEXT_MIN_LEFT_FRAC = 0.385
_BODY_TEXT_MAX_RIGHT_FRAC = 0.93

# Oracle wordmark placement (top-right corner, software-rendered).
# Sized to match the proportion used in Oracle Redwood brand slide deck headers — present but not
# dominant. Roughly 12–15% of card width once aspect ratio is applied to the wordmark.
_LOGO_RIGHT_MARGIN_FRAC = 0.050
_LOGO_TOP_MARGIN_FRAC = 0.062
_LOGO_HEIGHT_FRAC = 0.045

# Oracle brand colors.
_ORACLE_RED = (197, 19, 25, 255)  # PMS 485 approximation — official Oracle brand red
_ORACLE_WHITE = (255, 255, 255, 255)


def _is_dark_theme(theme: Optional[str]) -> bool:
    """Robust dark-theme detection: a card is dark unless the theme explicitly says 'light'."""
    t = (theme or "").lower().strip()
    if "dark" in t or "navy" in t or "midnight" in t or "black" in t or "night" in t:
        return True
    if "light" in t or "cream" in t or "white" in t or "ivory" in t:
        return False
    # Default: treat unknown themes as light (matches Pydantic default "Oracle Light").
    return False

# If the UI does not see this in JSON, the request is not hitting this app (wrong port / old process).
API_FINGERPRINT = "recognition-card-api-v9-aligned-headline-smaller-logo"
print(
    f"[{API_FINGERPRINT}] module={__file__!s} project_root={_PROJECT_ROOT} "
    "(dev: uvicorn … --port 8055 — avoid 8001; it often has duplicate listeners on Windows)",
    flush=True,
)


class GenerateCardRequest(BaseModel):
    employee_name: Optional[str] = "Employee"
    manager_name: Optional[str] = "Manager"
    manager_position: Optional[str] = "Manager"
    recognition_type: Optional[str] = "Performance"
    theme: Optional[str] = "Oracle Light"
    has_photo: Optional[bool] = False
    photo_asset_id: Optional[str] = ""
    model_config = {"extra": "ignore"}


def _recognition_instructions(recognition_type: str, recognition_context: str) -> str:
    normalized = recognition_type.strip().lower()
    context = recognition_context.strip()

    scenarios = {
        "welcome": (
            "Write a warm welcome thank-you note that appreciates the employee for joining the team and their early impact."
        ),
        "milestone": (
            "Write an appreciative milestone thank-you note recognizing sustained contribution and commitment."
        ),
        "performance": (
            "Write a specific results-focused thank-you note that links the achievement to meaningful team or business impact."
        ),
        "team contribution": (
            "Write a gratitude-focused note thanking the employee for collaboration, support, and enabling team success."
        ),
        "culture & values": (
            "Write a values-based appreciation note thanking the employee for modeling Oracle culture and behaviors."
        ),
        "promotion": (
            "Write a congratulatory thank-you note recognizing growth, trust, and readiness for expanded responsibility."
        ),
    }
    scenario_note = scenarios.get(
        normalized,
        "Use a professional employee-recognition tone appropriate for HR communication.",
    )
    if context:
        return f"{scenario_note} Additional scenario context: {context}."
    return scenario_note


def _card_headline(recognition_type: str) -> str:
    """Full headline phrase — avoids the model printing only one word e.g. Performance."""
    normalized = recognition_type.strip().lower()
    titles = {
        "welcome": "Welcome & Recognition",
        "milestone": "Milestone Recognition",
        "performance": "Performance Recognition",
        "team contribution": "Team Contribution Recognition",
        "culture & values": "Culture & Values Recognition",
        "promotion": "Promotion Recognition",
    }
    return titles.get(normalized, "Employee Recognition")


app = FastAPI(title="Recognition Card API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_prompt(payload: GenerateCardRequest, *, reserve_left_for_photo_overlay: bool) -> str:
    """Oracle Redwood brand-styled abstract background prompt.

    The image model paints ONLY a Redwood-style abstract background: a calm base color across
    the centre with hand-drawn organic blob shapes anchored in the corners, painted in the muted
    earthy Redwood palette (mustard, burnt sienna, slate teal, dark olive, cream) with subtle
    hand-drawn interior textures (hatching, dots, woven cross-hatch). Software composites the
    Oracle wordmark, employee photo, and all card text on top afterwards.

    Why this approach: image models are unreliable at constrained slide layouts but excellent at
    expressive art. Restricting them to art only — in a clearly defined brand language — gives
    us painterly Redwood-correct backgrounds while guaranteeing typography, identity, and brand
    placement deterministically through software composition.
    """
    del reserve_left_for_photo_overlay  # unused: same Redwood background works for both paths

    is_dark = _is_dark_theme(payload.theme)

    if is_dark:
        base_description = (
            "deep warm slate charcoal base color (approximately #2D2E32, warm dark grey, NOT pure "
            "black, NOT navy blue) covering the full canvas with a subtle warm undertone"
        )
        palette_description = (
            "muted EARTHY Redwood palette: warm mustard yellow (#D6A23A), burnt sienna terracotta "
            "(#C25E2D), slate teal grey-green (#5A7B7F), dark forest olive (#4A5238), warm cream "
            "(#E8DDC3). All colors are MUTED and earthy — NEVER saturated, NEVER neon, NEVER bright."
        )
        contrast_note = (
            "Shapes are medium-toned so they read clearly against the dark slate background, "
            "but never high-contrast or jarring."
        )
    else:
        base_description = (
            "warm cream base color (approximately #F0E9D9 — soft off-white with a warm sandy "
            "undertone, NOT pure white, NOT cool grey) covering the full canvas"
        )
        palette_description = (
            "SOFT PASTEL Redwood palette ONLY — every color must be a LIGHT, GENTLE, AIRY pastel "
            "that harmonises with the cream background. Allowed colors: pale butter yellow (#EAD79A), "
            "soft peach (#E8C7A8), dusty pale sage green (#C7D2B5), light dusty teal (#BDCDCC), "
            "pale rose-blush (#E5C2B8), warm beige (#DDCDB2). "
            "ABSOLUTELY DO NOT use any of these dark or saturated colors: NO burnt sienna, NO terracotta, "
            "NO red-orange, NO dark forest green, NO dark olive, NO dark teal, NO charcoal, NO black, "
            "NO bright saturated colors. The whole image must feel LIGHT, AIRY, SOFT, PASTEL — like a "
            "soft watercolor wash on warm paper."
        )
        contrast_note = (
            "Shapes are pale and gentle, only slightly more saturated than the cream background — "
            "low contrast, soft and elegant, NEVER bold or punchy."
        )

    return (
        f"Oracle Redwood brand style abstract background, 16:9 aspect ratio, {base_description}. "

        "STYLE — high-quality hand-drawn editorial illustration. Painterly, refined, sophisticated, "
        "inspired by the Oracle Redwood design language and modern editorial design. Imagine a clean "
        "page from the Oracle Redwood brand style guide. Matte finish like fine gouache, soft pastel "
        "wash, or printed ink on premium paper. NOT vector-perfect, NOT digital-glossy, NOT 3D, NOT "
        "sci-fi, NOT corporate-stock. Polished and elegant, never rough or scratchy. "

        f"COLOR PALETTE — {palette_description} {contrast_note} "

        "SHAPES — 2 large hand-drawn organic blob shapes (smooth pebble or leaf forms with gently "
        "irregular organic outlines, like calm brush-painted shapes). Each shape is filled with ONE "
        "color from the palette as a CLEAN MATTE FILL. Outlines are softly hand-drawn — slightly "
        "imperfect but elegant, NEVER scratchy, NEVER scribbled, NEVER mathematically perfect. "

        "INTERIOR TEXTURES — keep textures EXTREMELY SUBTLE and minimal. Most of each shape is a clean "
        "matte fill of its single color. Optionally add a SMALL textural accent in ONE small region of "
        "the shape (covering at most 25% of the shape area): a few sparse dots, a small patch of fine "
        "hatching, or a small woven cross-hatch area. Textures are gentle accents, NEVER busy, NEVER "
        "covering the whole shape, NEVER scratchy or rough. The overall feel is calm, refined, polished. "

        "COMPOSITION — sparse, minimal, breathable. Place ONE large blob anchored in the TOP-LEFT "
        "corner (extending up to ~28% width and ~30% height inward from the corner), and ONE large "
        "blob anchored in the BOTTOM-RIGHT corner (extending up to ~25% width and ~25% height inward "
        "from the corner). The TOP-RIGHT corner MUST stay completely empty (reserved for a header "
        "element). The CENTRAL 55% of the canvas (roughly x: 22%-77%, y: 22%-78%) MUST remain pure "
        "calm base color — NO shapes, NO textures, NO marks, NO lines anywhere in the centre. Generous "
        "negative space. Shapes never overlap each other. "

        "STRICT NEGATIVES — the image must NOT contain ANY of the following, anywhere: "
        "(a) text of ANY kind: no letters, words, numbers, glyphs, captions, headlines, paragraphs, "
        "signatures, dates, watermarks, or single character marks; "
        "(b) any logos, wordmarks, brand marks, trademarks, ® or ™ symbols, or text reading 'Oracle'; "
        "(c) any people, faces, headshots, silhouettes, avatars, portraits, or human figures; "
        "(d) any rectangles, panels, plates, frames, slates, banners, tiles, header strips, footer "
        "strips, divider lines, columns, rounded boxes, or enclosing shapes of any kind; "
        "(e) any tinted regions or color blocks that carve the canvas into separate areas — the base "
        "color must remain ONE continuous calm surface beneath and around the blob shapes; "
        "(f) any icons, charts, diagrams, photographs, real-world objects, buildings, technology, "
        "computers, screens, abstract sci-fi 3D renders, glow effects, lens flares, or photorealistic "
        "elements; "
        "(g) any bright saturated colors, neon, fluorescent, glossy gradients, or 3D shading "
        "(shapes are flat matte color with optional subtle texture only); "
        "(h) any rough, scratchy, sketchy, or low-quality marks — the work must read as a polished "
        "editorial illustration, not a rough sketch. "

        "The final image must look like a high-quality, polished page from the Oracle Redwood brand "
        "style guide: a calm "
        + ("earthy" if is_dark else "soft pastel")
        + " background with 2 large refined hand-drawn organic shapes in opposite corners, very subtle "
        "painterly accents, lots of empty calm space, sophisticated and warm."
    )


_RECOGNITION_BODIES: dict[str, str] = {
    "welcome": (
        "Welcome to Oracle. Your fresh perspective and early contributions have already made a "
        "meaningful impact, and the team is genuinely glad to have you on board. We look forward "
        "to your continued growth and success with us."
    ),
    "milestone": (
        "Thank you for the years of sustained dedication and impact you have brought to Oracle. "
        "Your commitment continues to shape our success, and we are grateful for the consistent "
        "excellence you deliver to your colleagues and to the business."
    ),
    "performance": (
        "Your outstanding performance has driven meaningful results for the team and contributed "
        "directly to Oracle's continued success. Thank you for the dedication, focus, and "
        "measurable impact you bring to your work every day."
    ),
    "team contribution": (
        "Thank you for the way you lift the team up every day. Your collaboration, support, and "
        "willingness to share your expertise have made a real difference, and we deeply appreciate "
        "the strength you bring to everyone around you."
    ),
    "culture & values": (
        "Thank you for living Oracle's values in everything you do. The way you lead by example, "
        "treat your colleagues with respect, and uphold the standards that define our culture is "
        "truly appreciated and inspires those around you."
    ),
    "promotion": (
        "Congratulations on your well-earned promotion. Your growth, dedication, and consistent "
        "results have made this moment possible, and we are confident you will continue to deliver "
        "excellence in your expanded role."
    ),
}


def _recognition_body(recognition_type: str) -> str:
    """Body paragraph for the recognition card. Templated per scenario for predictable quality."""
    normalized = (recognition_type or "").strip().lower()
    return _RECOGNITION_BODIES.get(
        normalized,
        "Thank you for the dedication, energy, and excellence you bring to Oracle every day. "
        "Your contributions make a real difference to the team and to our continued success.",
    )


def _short_title(value: str) -> str:
    cleaned = (value or "").replace(",", " ").replace("-", " ").replace("_", " ").replace("/", " ").strip()
    if not cleaned:
        return "Manager"
    banned = {"department", "global", "team", "division", "unit", "function", "of"}
    tokens = [token for token in cleaned.split() if token and token.lower() not in banned]
    if not tokens:
        return "Manager"
    return " ".join(tokens[:4])


_PHOTO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def _norm_photo_key(name: str) -> str:
    """Normalize for fuzzy match (Excel/CSV names vs filenames)."""
    lower = (name or "").lower()
    lower = lower.replace("\u2019", "'").replace("\u2018", "'")
    return "".join(ch for ch in lower if ch.isalnum())


def _resolve_photo_file(photo_asset_id: str, employee_name: Optional[str] = None) -> Optional[Path]:
    raw = (photo_asset_id or "").strip()
    raw = raw.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    raw = raw.replace("\u200b", "").replace("\ufeff", "")
    raw = raw.strip("\"' \t\r\n").replace("\\", "/")
    raw = raw.rstrip(".,;:")
    if not raw:
        return None

    candidate = raw
    if raw.startswith("/"):
        candidate = raw[1:]
    if candidate.startswith("employee-photos/"):
        candidate = f"frontend/public/{candidate}"
    elif candidate.startswith("frontend/public/"):
        candidate = candidate
    else:
        candidate = f"frontend/public/employee-photos/{candidate}"

    primary = _PROJECT_ROOT / candidate
    if primary.is_file():
        return primary.resolve()

    # Fallback: tolerate accidental embedded quotes in file stem, e.g. celebratory".png
    cleaned_candidate = candidate.replace('"', "").replace("'", "")
    cleaned = _PROJECT_ROOT / cleaned_candidate
    if cleaned.is_file():
        return cleaned.resolve()

    photo_dir = _PROJECT_ROOT / "frontend" / "public" / "employee-photos"
    if not photo_dir.is_dir():
        return None

    want_name = Path(candidate).name
    want_key = _norm_photo_key(Path(want_name).stem)

    # Case-insensitive exact filename (helps Linux deploys; Windows often already matches).
    for item in photo_dir.iterdir():
        if item.is_file() and item.suffix.lower() in _PHOTO_EXTENSIONS and item.name.lower() == want_name.lower():
            return item.resolve()

    # Fuzzy stem: sara-alfarsi vs sara-al-farsi, etc.
    if want_key:
        for item in photo_dir.iterdir():
            if not item.is_file() or item.suffix.lower() not in _PHOTO_EXTENSIONS:
                continue
            if _norm_photo_key(item.stem) == want_key:
                return item.resolve()

    # Match by employee display name when CSV path drifts from disk filename (exact normalized stem).
    em_key = _norm_photo_key((employee_name or "").strip())
    if len(em_key) >= 4:
        for item in photo_dir.iterdir():
            if not item.is_file() or item.suffix.lower() not in _PHOTO_EXTENSIONS:
                continue
            stem_key = _norm_photo_key(item.stem)
            if stem_key and stem_key == em_key:
                return item.resolve()

    return None


_GEORGIA_FILES: dict[str, tuple[str, ...]] = {
    "regular": ("georgia.ttf", "Georgia.ttf"),
    "bold": ("georgiab.ttf", "Georgiab.ttf"),
    "italic": ("georgiai.ttf", "Georgiai.ttf"),
    "bold-italic": ("georgiaz.ttf", "Georgiaz.ttf"),
}

# Oracle wordmark fallback fonts in order of preference (closest visual match to Oracle Sans first).
_LOGO_FONT_CANDIDATES: tuple[str, ...] = ("ariblk.ttf", "arialbd.ttf", "calibrib.ttf", "segoeuib.ttf")


def _draw_oracle_wordmark(card: Image.Image, *, theme: str) -> Image.Image:
    """Render the Oracle wordmark in the top-right corner deterministically.

    Uses an asset PNG if one is provided at frontend/public/oracle-logo.png (recommended for exact
    brand fidelity). Otherwise falls back to rendering 'ORACLE' in Arial Black with a small ®
    superscript — visually close to Oracle Sans and consistent across every generation.
    """
    rgba = card.convert("RGBA")
    w, h = rgba.size
    is_dark = _is_dark_theme(theme)
    fill = _ORACLE_WHITE if is_dark else _ORACLE_RED
    right_margin = int(w * _LOGO_RIGHT_MARGIN_FRAC)
    top_margin = int(h * _LOGO_TOP_MARGIN_FRAC)

    # Theme-specific asset takes priority for brand-perfect rendering. Place either:
    #   frontend/public/oracle-logo-white.png  (used on dark themes)
    #   frontend/public/oracle-logo-red.png    (used on light themes)
    #   frontend/public/oracle-logo.png        (legacy single-file fallback, used on either theme)
    public_dir = _PROJECT_ROOT / "frontend" / "public"
    candidates = (
        ["oracle-logo-white.png"] if is_dark else ["oracle-logo-red.png"]
    ) + ["oracle-logo.png"]
    asset: Optional[Path] = None
    for name in candidates:
        p = public_dir / name
        if p.is_file():
            asset = p
            break
    if asset is not None:
        try:
            logo = Image.open(asset).convert("RGBA")
            target_h = int(h * _LOGO_HEIGHT_FRAC)
            ratio = logo.width / max(1, logo.height)
            target_w = max(1, int(target_h * ratio))
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
            rgba.alpha_composite(logo, (w - right_margin - target_w, top_margin))
            return rgba.convert("RGB")
        except OSError:
            pass  # fall through to text rendering

    # Fallback: render the wordmark with Arial Black.
    font_size = max(28, int(h * _LOGO_HEIGHT_FRAC))
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    font: ImageFont.ImageFont = ImageFont.load_default()
    for name in _LOGO_FONT_CANDIDATES:
        path = windir / "Fonts" / name
        if path.is_file():
            try:
                font = ImageFont.truetype(str(path), size=font_size)
                break
            except OSError:
                continue

    r_size = max(10, int(font_size * 0.40))
    r_font = font
    for name in _LOGO_FONT_CANDIDATES:
        path = windir / "Fonts" / name
        if path.is_file():
            try:
                r_font = ImageFont.truetype(str(path), size=r_size)
                break
            except OSError:
                continue

    text = "ORACLE"
    r_glyph = "\u00ae"
    draw = ImageDraw.Draw(rgba)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    r_bbox = draw.textbbox((0, 0), r_glyph, font=r_font)
    r_w = r_bbox[2] - r_bbox[0]
    gap = max(2, int(font_size * 0.06))
    total_w = text_w + gap + r_w

    x = w - right_margin - total_w
    draw.text((x, top_margin), text, font=font, fill=fill)
    # ® sits raised, near the top of the wordmark.
    draw.text((x + text_w + gap, top_margin + int(font_size * 0.05)), r_glyph, font=r_font, fill=fill)
    return rgba.convert("RGB")


def _georgia_font(size: int, weight: str = "regular") -> ImageFont.ImageFont:
    """Load a Georgia variant. Falls back to regular Georgia, then PIL default if missing.

    Valid weights: 'regular', 'bold', 'italic', 'bold-italic'.
    """
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = _GEORGIA_FILES.get(weight, _GEORGIA_FILES["regular"])
    for name in candidates:
        p = windir / "Fonts" / name
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    if weight != "regular":
        return _georgia_font(size, weight="regular")
    return ImageFont.load_default()


def _wrap_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Greedy word-wrap: split text into lines whose pixel width fits within max_width."""
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _render_card_text(
    card: Image.Image,
    *,
    employee_name: str,
    manager_name: str,
    manager_title: str,
    recognition_type: str,
    theme: str,
    has_photo: bool,
) -> Image.Image:
    """Draw all card copy (headline, greeting, body, sign-off) in real Georgia.

    The image model only paints background + curves + Oracle logo. This function owns every
    glyph the recipient will read, guaranteeing typography (Georgia across the board) and
    layout (no AI-drawn boxes, plates, or stray captions).
    """
    rgba = card.convert("RGBA")
    w, h = rgba.size
    is_dark = _is_dark_theme(theme)
    text_fill = (245, 248, 252, 255) if is_dark else (28, 32, 42, 255)
    muted_fill = (190, 200, 215, 255) if is_dark else (90, 96, 110, 255)

    text_left_frac = _BODY_TEXT_MIN_LEFT_FRAC if has_photo else 0.08
    text_left = int(w * text_left_frac)
    text_right = int(w * _BODY_TEXT_MAX_RIGHT_FRAC)
    text_width = text_right - text_left

    headline_size = max(28, int(h * 0.058))
    body_size = max(16, int(h * 0.037))
    signoff_size = max(14, int(h * 0.029))

    headline_font = _georgia_font(headline_size, weight="bold")
    body_font = _georgia_font(body_size)
    signoff_italic = _georgia_font(signoff_size, weight="italic")
    signoff_font = _georgia_font(signoff_size)

    headline = _card_headline(recognition_type)
    greeting = f"Dear {employee_name},"
    body_text = _recognition_body(recognition_type)

    draw = ImageDraw.Draw(rgba)
    body_lines = _wrap_text_to_width(draw, body_text, body_font, text_width)

    headline_lh = int(headline_size * 1.20)
    body_lh = int(body_size * 1.45)
    signoff_lh = int(signoff_size * 1.40)

    gap_after_headline = int(h * 0.045)
    gap_greeting_to_body = int(body_lh * 0.45)
    gap_body_to_signoff = int(h * 0.045)

    total_h = (
        headline_lh
        + gap_after_headline
        + body_lh  # greeting
        + gap_greeting_to_body
        + body_lh * len(body_lines)
        + gap_body_to_signoff
        + signoff_lh * 3
    )

    # When a photo is present, top-align the headline with the photo top so the two columns sit on
    # the same baseline (the user explicitly wants headline and photo at the SAME visual level).
    # The small negative offset compensates for the cap-height padding inside the headline glyphs
    # so the optical top of the letters lines up with the optical top of the photo card.
    if has_photo:
        y = max(int(h * 0.10), int(h * _PHOTO_TOP_FRAC) - int(headline_size * 0.18))
    else:
        # No photo: vertically centre the whole text block in the canvas as before.
        text_area_top = int(h * 0.20)
        text_area_bottom = int(h * 0.90)
        text_area_h = text_area_bottom - text_area_top
        y = text_area_top + max(0, (text_area_h - total_h) // 2)

    draw.text((text_left, y), headline, font=headline_font, fill=text_fill)
    y += headline_lh + gap_after_headline

    draw.text((text_left, y), greeting, font=body_font, fill=text_fill)
    y += body_lh + gap_greeting_to_body

    for line in body_lines:
        draw.text((text_left, y), line, font=body_font, fill=text_fill)
        y += body_lh
    y += gap_body_to_signoff

    draw.text((text_left, y), "With appreciation,", font=signoff_italic, fill=text_fill)
    y += signoff_lh
    draw.text((text_left, y), f"\u2014 {manager_name} \u2014", font=signoff_font, fill=text_fill)
    y += signoff_lh
    draw.text((text_left, y), manager_title, font=signoff_font, fill=muted_fill)

    return rgba.convert("RGB")


def _paste_exact_employee_photo(
    card: Image.Image,
    photo_path: Path,
    *,
    employee_name: str,
    theme: str,
) -> Image.Image:
    """Paste disk image pixels unchanged (scale-to-fit + rounded mask + soft drop shadow).

    Adds a subtle drop shadow and a thin hairline accent so the composited photo reads as a polished
    design element instead of a floating cutout. Name caption is centred under the photo on its own
    baseline (kept clear of any AI-drawn ornaments because the prompt forbids them).
    """
    card_rgba = card.convert("RGBA")
    emp = Image.open(photo_path).convert("RGBA")
    w, h = card_rgba.size
    is_dark = _is_dark_theme(theme)
    name_fill = (248, 250, 252, 255) if is_dark else (28, 32, 42, 255)
    shadow_alpha = 140 if is_dark else 90

    column_x0 = int(w * _PHOTO_COLUMN_X0_FRAC)
    column_w = int(w * _PHOTO_COLUMN_W_FRAC)
    center_x = column_x0 + column_w // 2
    target_w = int(w * _PHOTO_TARGET_W_FRAC)
    target_h = int(h * _PHOTO_TARGET_H_FRAC)
    top = int(h * _PHOTO_TOP_FRAC)
    left = column_x0 + max(0, (column_w - target_w) // 2)

    fitted = ImageOps.contain(emp, (target_w, target_h), method=Image.Resampling.LANCZOS)
    px = left + max(0, (target_w - fitted.width) // 2)
    py = top + max(0, (target_h - fitted.height) // 2)
    ny = min(top + target_h + int(h * _PHOTO_NAME_GAP_BELOW_FRAC), h - int(h * 0.055))

    rad = max(10, int(min(fitted.width, fitted.height) * 0.07))
    rounded = Image.new("L", fitted.size, 0)
    ImageDraw.Draw(rounded).rounded_rectangle((0, 0, fitted.width, fitted.height), radius=rad, fill=255)
    alpha = fitted.split()[3] if fitted.mode == "RGBA" else Image.new("L", fitted.size, 255)
    mask = ImageChops.multiply(rounded, alpha)

    # Soft drop shadow under the photo for a polished, intentional look.
    shadow_pad = max(12, int(min(fitted.width, fitted.height) * 0.06))
    shadow_size = (fitted.width + shadow_pad * 2, fitted.height + shadow_pad * 2)
    shadow_layer = Image.new("RGBA", shadow_size, (0, 0, 0, 0))
    shadow_mask_full = Image.new("L", shadow_size, 0)
    shadow_mask_full.paste(rounded, (shadow_pad, shadow_pad))
    shadow_layer.putalpha(shadow_mask_full)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_pad * 0.55))
    # Reduce the shadow opacity uniformly without darkening RGB.
    sa = shadow_layer.split()[3].point(lambda v: int(v * (shadow_alpha / 255)))
    shadow_rgba = Image.new("RGBA", shadow_size, (0, 0, 0, 0))
    shadow_rgba.putalpha(sa)
    sx = px - shadow_pad
    sy = py - shadow_pad + int(shadow_pad * 0.35)  # slight downward offset
    card_rgba.alpha_composite(shadow_rgba, (sx, sy))

    card_rgba.paste(fitted, (px, py), mask)

    # Hairline accent under the photo — subtle separator that anchors the name caption to the photo.
    accent_color = (210, 218, 230, 90) if is_dark else (80, 90, 110, 90)
    line_y = py + fitted.height + max(6, int(h * 0.012))
    line_half = int(fitted.width * 0.30)
    ImageDraw.Draw(card_rgba).line(
        [(center_x - line_half, line_y), (center_x + line_half, line_y)],
        fill=accent_color,
        width=max(1, int(h * 0.0025)),
    )

    label = (employee_name or "Employee").strip() or "Employee"
    fs = max(20, int(h * 0.040))
    font = _georgia_font(fs)
    draw = ImageDraw.Draw(card_rgba)
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((center_x - tw // 2, ny), label, font=font, fill=name_fill)

    return card_rgba.convert("RGB")


@app.get("/")
def root() -> dict:
    """Identify this service without relying on /api prefix (helps debug wrong process on a port)."""
    return {
        "app": API_FINGERPRINT,
        "api_schema_version": 4,
        "module_path": str(Path(__file__).resolve()),
        "hints": ["GET /api/version", "GET /api/health", "POST /api/generate-card", "GET /docs"],
    }


@app.get("/api/health")
def health() -> dict:
    photo_dir = _PROJECT_ROOT / "frontend" / "public" / "employee-photos"
    return {
        "status": "ok",
        "fingerprint": API_FINGERPRINT,
        "api_schema_version": 4,
        "project_root": str(_PROJECT_ROOT),
        "photo_dir": str(photo_dir),
        "photo_dir_exists": photo_dir.is_dir(),
        "photo_mode": "exact_disk_overlay_after_generation",
    }


@app.get("/api/version")
def api_version() -> dict:
    return {
        "fingerprint": API_FINGERPRINT,
        "api_schema_version": 4,
        "module_path": str(Path(__file__).resolve()),
        "project_root": str(_PROJECT_ROOT),
    }


@app.post("/api/generate-card")
def generate_card(payload: GenerateCardRequest) -> dict:
    try:
        photo_path: Optional[Path] = None
        should_use_photo = bool((payload.photo_asset_id or "").strip()) or bool(payload.has_photo)
        if should_use_photo:
            photo_path = _resolve_photo_file(
                payload.photo_asset_id or "",
                employee_name=payload.employee_name,
            )
            if photo_path is None:
                raise FileNotFoundError(
                    "Employee photo not found. Put the file under frontend/public/employee-photos "
                    f"and verify photo_asset_id path. Received: {payload.photo_asset_id!r}"
                )

        prompt = _build_prompt(payload, reserve_left_for_photo_overlay=photo_path is not None)
        # AI generates ABSTRACT BACKGROUND ONLY (gradient + curves). Software then composites:
        # (1) Oracle wordmark, (2) employee photo, (3) all card text. This separation guarantees
        # brand fidelity, identity preservation, Georgia typography, and a deterministic layout
        # — none of which the image model can be relied on to produce consistently.
        image = generate_from_env(prompt)

        employee_name_clean = (payload.employee_name or "Employee").strip() or "Employee"
        manager_name_clean = (payload.manager_name or "Manager").strip() or "Manager"
        manager_title_clean = _short_title(payload.manager_position or "Manager")
        recognition_type_clean = (payload.recognition_type or "Performance").strip() or "Performance"
        theme_clean = (payload.theme or "Oracle Light").strip() or "Oracle Light"

        image = _draw_oracle_wordmark(image, theme=theme_clean)

        if photo_path is not None:
            image = _paste_exact_employee_photo(
                image,
                photo_path,
                employee_name=employee_name_clean,
                theme=theme_clean,
            )

        image = _render_card_text(
            image,
            employee_name=employee_name_clean,
            manager_name=manager_name_clean,
            manager_title=manager_title_clean,
            recognition_type=recognition_type_clean,
            theme=theme_clean,
            has_photo=photo_path is not None,
        )

        file_name = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        file_path = OUTPUT_DIR / file_name
        image.save(file_path, format="PNG")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_b64 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
        body = {
            "fingerprint": API_FINGERPRINT,
            "status": "ok",
            "api_schema_version": 4,
            "prompt": prompt,
            "image_base64": image_b64,
            "output_file": str(file_path.resolve()),
            "photo_passed_to_model": False,
            "photo_exact_overlay": bool(photo_path is not None),
            "photo_path_used": str(photo_path) if photo_path is not None else "",
            "photo_path_absolute": str(photo_path.resolve()) if photo_path is not None else "",
            "project_root": str(_PROJECT_ROOT),
        }
        return JSONResponse(content=body)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc
