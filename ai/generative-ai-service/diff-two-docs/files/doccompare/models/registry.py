"""Model registry — loads the model list from the project `.env`.

No python-dotenv dependency: we parse the `.env` ourselves (KEY=VALUE, `#`
comments, `${VAR}` expansion) so the file stays the single source of truth and
`os.environ` still wins if a var is exported in the shell.

Each active slug in `MODELS=` is turned into a `ModelSpec`. Per-slug variables
are prefixed with the UPPER-CASED slug, e.g. slug `gemini_pro` reads
`GEMINI_PRO_MODE`, `GEMINI_PRO_MODEL_ID`, ...

The service-endpoint URL is derived from the region, not stored, so the `.env`
never carries a URL to get out of sync.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

# project root = two levels up from this file (doccompare/models/registry.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

_VAR_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _service_endpoint(region: str) -> str:
    return f"https://inference.generativeai.{region}.oci.oraclecloud.com"


def parse_env_file(path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """Parse a `.env` into a dict. Shell environment overrides file values.

    Handles: blank lines, `#` full-line and inline comments, surrounding
    quotes, and `${VAR}` expansion against the values seen so far + os.environ.
    """
    values: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            # strip inline comment (a ` #` not inside quotes — values here are
            # OCIDs / ids / ints, none contain '#', so this is safe)
            if "#" in val:
                val = val.split("#", 1)[0]
            val = val.strip().strip('"').strip("'")
            # expand ${VAR} from already-parsed values or the environment
            def _sub(mobj: re.Match) -> str:
                name = mobj.group(1)
                return os.environ.get(name, values.get(name, ""))
            val = _VAR_RE.sub(_sub, val).strip()
            values[key] = val
    # shell environment wins
    for k, v in os.environ.items():
        values[k] = v
    return values


def _as_bool(v: str | None) -> bool | None:
    if v is None:
        return None
    v = v.strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None  # e.g. "unknown"


@dataclass
class ModelSpec:
    slug: str
    mode: str                      # "on_demand" | "dedicated"
    region: str
    service_endpoint: str
    compartment_id: str
    config_profile: str = "DEFAULT"
    model_id: str | None = None    # on_demand
    endpoint_ocid: str | None = None  # dedicated
    vision: bool | None = None     # None = unknown
    gpu: int | None = None         # H100 count for dedicated (cost axis)

    @property
    def serving_id(self) -> str:
        return self.endpoint_ocid if self.mode == "dedicated" else (self.model_id or "")

    def __str__(self) -> str:
        return f"{self.slug}[{self.mode}/{self.region}:{self.serving_id[-24:]}]"


def load_registry(path: Path = DEFAULT_ENV_PATH) -> dict[str, ModelSpec]:
    env = parse_env_file(path)
    profile = env.get("OCI_CONFIG_PROFILE", "DEFAULT")
    default_compartment = env.get("OCI_COMPARTMENT_OCID", "")
    slugs = [s.strip() for s in env.get("MODELS", "").split(",") if s.strip()]

    registry: dict[str, ModelSpec] = {}
    for slug in slugs:
        p = slug.upper()

        def g(suffix: str, default: str | None = None) -> str | None:
            return env.get(f"{p}_{suffix}", default)

        mode = (g("MODE") or "on_demand").strip()
        region = g("REGION")
        if not region:
            raise ValueError(f"[registry] {slug}: missing {p}_REGION")
        compartment = g("COMPARTMENT") or default_compartment
        if not compartment:
            raise ValueError(f"[registry] {slug}: no compartment (set OCI_COMPARTMENT_OCID)")

        spec = ModelSpec(
            slug=slug,
            mode=mode,
            region=region,
            service_endpoint=_service_endpoint(region),
            compartment_id=compartment,
            config_profile=profile,
            model_id=g("MODEL_ID"),
            endpoint_ocid=g("ENDPOINT_OCID"),
            vision=_as_bool(g("VISION")),
            gpu=int(g("GPU")) if (g("GPU") or "").strip().isdigit() else None,
        )
        if spec.mode == "dedicated" and not spec.endpoint_ocid:
            raise ValueError(f"[registry] {slug}: dedicated mode needs {p}_ENDPOINT_OCID")
        if spec.mode == "on_demand" and not spec.model_id:
            raise ValueError(f"[registry] {slug}: on_demand mode needs {p}_MODEL_ID")
        registry[slug] = spec
    return registry


if __name__ == "__main__":
    reg = load_registry()
    print(f"Loaded {len(reg)} models from {DEFAULT_ENV_PATH}:")
    for spec in reg.values():
        vis = {True: "vision", False: "text-only", None: "vision?"}[spec.vision]
        gpu = f" {spec.gpu}xH100" if spec.gpu else ""
        print(f"  {spec.slug:20s} {spec.mode:10s} {spec.region:16s} {vis}{gpu}")
        print(f"    -> {spec.serving_id}")
