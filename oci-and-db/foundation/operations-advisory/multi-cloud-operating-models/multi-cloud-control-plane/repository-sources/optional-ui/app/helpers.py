import json
import re
from pathlib import Path
from typing import Any, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment as JinjaEnvironment
from jinja2 import meta
from markdown_it import MarkdownIt

from app.config import settings
from app.forms import normalize_form_value

# ============ Global Instances ============

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def github_oauth_client_kwargs(auth_mode: str) -> dict[str, str]:
    """Return the authorization parameters for the configured GitHub client."""
    if auth_mode == "github_app":
        return {}
    if auth_mode == "oauth_app":
        return {"scope": "read:user read:org repo"}
    raise ValueError(f"Unsupported GitHub authorization mode: {auth_mode}")


# OAuth config
oauth = OAuth()
oauth.register(
    name="github",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs=github_oauth_client_kwargs(settings.github_auth_mode),
)

_placeholder_re = re.compile(r"(?<![A-Za-z0-9_])(__[A-Za-z0-9_]+__)(?![A-Za-z0-9_])")
_jinja_env = JinjaEnvironment(autoescape=False)
_markdown = MarkdownIt("commonmark")
_optional_list_field_keys = {"nsg_ids", "network_security_groups"}


# ============ Template Placeholder Utilities ============

def _is_custom_placeholder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _to_template_str(obj: dict | list | str | Any) -> str:
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def _to_jinja_template(template_str: str) -> str:
    return _placeholder_re.sub(lambda m: "{{ " + m.group(1) + " }}", template_str)


def _undeclared_custom_variables(template_str: str) -> set[str]:
    ast = _jinja_env.parse(template_str)
    names = meta.find_undeclared_variables(ast)
    return {name for name in names if _is_custom_placeholder(name)}


def _build_placeholder_context(data: dict, placeholders: set[str]) -> tuple[dict, list[str]]:
    source = {k: normalize_form_value(v) for k, v in (data or {}).items()}
    context = dict(source)
    missing: list[str] = []

    for ph in placeholders:
        candidates = [ph, ph.strip("_"), ph.strip("_").lower(), ph.lower()]
        value = None
        for candidate in candidates:
            if candidate in source:
                candidate_value = source[candidate]
                if candidate_value not in (None, ""):
                    value = candidate_value
                    break
        if value is None:
            missing.append(ph)
            context[ph] = ph
        else:
            context[ph] = value
    return context, missing


def find_placeholders(obj: dict | list | str | Any) -> set[str]:
    """
    Recursively find placeholder strings (__KEY__) in nested structures.

    Example:
        >>> find_placeholders({"name": "__ADB_NAME__"})
        {'adb_name'}
    """
    raw = find_raw_placeholders(obj)
    return {item.strip("_").lower() for item in raw}


def find_raw_placeholders(obj: dict | list | str | Any) -> set[str]:
    """
    Recursively find raw placeholder strings (__KEY__) in nested structures.

    Example:
        >>> find_raw_placeholders({"name": "__ADB_NAME__"})
        {'__ADB_NAME__'}
    """
    template_str = _to_template_str(obj)
    jinja_template = _to_jinja_template(template_str)
    return _undeclared_custom_variables(jinja_template)


def replace_placeholders(
    template_str: str, data: dict, placeholders: Optional[set[str]] = None
) -> tuple[str, list[str]]:
    """
    Replace placeholders in a template string with values from data.

    Returns: (final_content, missing_placeholders)
    """
    jinja_template = _to_jinja_template(template_str)
    declared = _undeclared_custom_variables(jinja_template)
    placeholder_set = set(placeholders) if placeholders else declared
    if not placeholder_set:
        return template_str, []

    context, missing = _build_placeholder_context(data, placeholder_set)
    rendered = _render_placeholder_string(template_str, context, placeholder_set)
    return rendered, missing


def _render_placeholder_string(value: str, context: dict, placeholders: set[str]) -> Any:
    """Render placeholders inside a string without breaking JSON string escaping."""
    active_placeholders = find_raw_placeholders(value) & placeholders
    if not active_placeholders:
        return value
    if value in active_placeholders:
        return context.get(value, value)
    return _placeholder_re.sub(
        lambda match: str(context.get(match.group(1), match.group(1)))
        if match.group(1) in active_placeholders
        else match.group(0),
        value,
    )


def _render_placeholder_object(value: Any, context: dict, placeholders: set[str]) -> Any:
    """Render placeholders through Python objects instead of raw JSON text."""
    if isinstance(value, dict):
        rendered = {}
        for key, item in value.items():
            rendered_key = (
                _render_placeholder_string(key, context, placeholders)
                if isinstance(key, str)
                else key
            )
            rendered[str(rendered_key)] = _render_placeholder_object(item, context, placeholders)
        return rendered
    if isinstance(value, list):
        return [_render_placeholder_object(item, context, placeholders) for item in value]
    if isinstance(value, str):
        return _render_placeholder_string(value, context, placeholders)
    return value


def fill_template_with_missing(
    obj: dict | list | str | Any,
    data: dict,
    placeholders: Optional[set[str]] = None,
) -> tuple[dict | list | str | Any, list[str]]:
    """
    Substitute placeholders with values from data and return missing placeholders.

    Example:
        >>> fill_template_with_missing({"name": "__ADB_NAME__"}, {"adb_name": "my-db"})
        ({'name': 'my-db'}, [])
    """
    if isinstance(obj, str):
        return replace_placeholders(obj, data, placeholders)

    declared = find_raw_placeholders(obj)
    placeholder_set = set(placeholders) if placeholders else declared
    if not placeholder_set:
        return obj, []

    context, missing = _build_placeholder_context(data, placeholder_set)
    return _render_placeholder_object(obj, context, placeholder_set), missing


def fill_template(obj: dict | list | str | Any, data: dict) -> dict | list | str | Any:
    """
    Recursively substitute placeholders with values from data.

    Example:
        >>> fill_template({"name": "__ADB_NAME__"}, {"adb_name": "my-db"})
        {'name': 'my-db'}
    """
    rendered, _ = fill_template_with_missing(obj, data)
    return rendered


def extract_form_fields(obj: dict | list, prefix: str = "") -> list[dict]:
    """
    Extract form field definitions from a template structure.
    Returns list of dicts with: path, placeholder, label, key, required
    """
    fields = []
    seen_placeholders: set[str] = set()

    def _is_required_field(path: str, label_key: str) -> bool:
        key = (label_key or path.rsplit(".", 1)[-1].split("[", 1)[0]).lower()
        return key not in _optional_list_field_keys

    def _add_placeholder_fields(value: str, path: str, label_key: str = ""):
        raw_vars = find_raw_placeholders(value)
        for ph in sorted(raw_vars):
            if ph in seen_placeholders:
                continue
            seen_placeholders.add(ph)
            label_source = label_key or ph.strip("_")
            fields.append(
                {
                    "path": path,
                    "placeholder": ph,
                    "label": label_source.replace("_", " ").title(),
                    "key": label_source,
                    "required": _is_required_field(path, label_source),
                }
            )

    def _walk(node: Any, path_prefix: str = ""):
        if isinstance(node, dict):
            for key, value in node.items():
                path = f"{path_prefix}.{key}" if path_prefix else key
                if isinstance(key, str):
                    _add_placeholder_fields(key, path)
                if isinstance(value, str):
                    _add_placeholder_fields(value, path, key)
                elif isinstance(value, (dict, list)):
                    _walk(value, path)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                list_path = f"{path_prefix}[{idx}]"
                _walk(item, list_path)
        elif isinstance(node, str):
            list_key = path_prefix.rsplit(".", 1)[-1].split("[", 1)[0]
            _add_placeholder_fields(node, path_prefix, list_key)

    _walk(obj, prefix)
    return fields


# ============ Markdown Extraction Helpers ============

def extract_plan_from_markdown(body: str) -> Optional[str]:
    """Extract terraform plan from markdown fenced code blocks."""
    tokens = _markdown.parse(body or "")
    fences: list[tuple[str, str]] = []
    for token in tokens:
        if token.type != "fence":
            continue
        info = (token.info or "").strip().split()
        lang = info[0].lower() if info else ""
        fences.append((lang, token.content))

    if not fences:
        return None

    preferred = [content for lang, content in fences if lang in {"terraform", "hcl"}]
    candidates = preferred if preferred else [content for _, content in fences]
    best = max(candidates, key=len).strip()
    return best or None


def extract_status_from_markdown(body: str, label: str) -> Optional[str]:
    """Extract status from markdown pattern like **Format:** `success`."""
    target = (label or "").strip().lower()
    if not target:
        return None

    tokens = _markdown.parse(body or "")
    waiting_for_code = False

    for token in tokens:
        if token.type != "inline" or not token.children:
            continue
        for child in token.children:
            if child.type == "text":
                text = (child.content or "").strip().lower()
                normalized = text.replace("**", "").strip()
                if normalized.endswith(":") and normalized[:-1].strip() == target:
                    waiting_for_code = True
                    continue
                if waiting_for_code and normalized:
                    waiting_for_code = False
            elif child.type == "code_inline" and waiting_for_code:
                value = (child.content or "").strip()
                return value or None
            elif child.type not in {"softbreak", "hardbreak", "strong_open", "strong_close"}:
                waiting_for_code = False
    return None


def render_partial(template_name: str, request: Request, **context):
    """Render a Jinja partial with request injected into context."""
    return templates.TemplateResponse(request, template_name, {"request": request, **context})


def render_repository_state_error(request: Request):
    """Render the stable fail-closed response for unverifiable repo state."""
    return render_partial(
        "partials/state-error.html",
        request,
        title="Unable to verify repository state",
        message=(
            "Repository state could not be verified. "
            "No change was created. Please try again."
        ),
    )
