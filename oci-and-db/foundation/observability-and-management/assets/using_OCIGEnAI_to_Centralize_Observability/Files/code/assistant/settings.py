import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class Settings:
    mode: str = field(default_factory=lambda: os.getenv("APP_MODE", "live"))
    base_url: str = field(default_factory=lambda: os.getenv("PUBLIC_URL", "http://localhost:8000").rstrip("/"))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "/data")))
    config_dir: Path = field(default_factory=lambda: Path(os.getenv("CONFIG_DIR", "/config")))
    session_secret: str = field(default_factory=lambda: os.getenv("SESSION_SECRET", ""))
    issuer: str = field(default_factory=lambda: os.getenv("OIDC_ISSUER", "").rstrip("/"))
    client_id: str = field(default_factory=lambda: os.getenv("OIDC_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.getenv("OIDC_CLIENT_SECRET", ""))
    groups_claim: str = field(default_factory=lambda: os.getenv("OIDC_GROUPS_CLAIM", "groups"))
    model_id: str = field(default_factory=lambda: os.getenv("GENAI_MODEL_ID", ""))
    genai_compartment: str = field(default_factory=lambda: os.getenv("GENAI_COMPARTMENT_ID", ""))
    region: str = field(default_factory=lambda: os.getenv("OCI_REGION", "eu-frankfurt-1"))
    max_calls: int = 14
    daily_runs: int = 30
    max_concurrent: int = 2

    def validate(self):
        if self.mode not in {"live", "demo"}:
            raise ValueError("APP_MODE must be live or demo")
        if len(self.session_secret) < 32:
            raise ValueError("SESSION_SECRET must contain at least 32 characters")
        host = urlparse(self.base_url).hostname
        if self.mode == "demo":
            if host not in {"localhost", "127.0.0.1"}:
                raise ValueError("Demo mode is restricted to localhost")
        elif not all((self.issuer, self.client_id, self.client_secret, self.genai_compartment)):
            raise ValueError("Configure OIDC and OCI Generative AI before using live mode")
        elif not self.base_url.startswith("https://") or not self.issuer.startswith("https://"):
            raise ValueError("Live mode requires HTTPS for PUBLIC_URL and OIDC_ISSUER")
        elif any('REPLACE_' in v or 'YOUR_' in v for v in (self.client_id,self.client_secret,self.genai_compartment,self.issuer,self.session_secret)):
            raise ValueError("Replace the example configuration values before live startup")
        parsed = urlparse(self.base_url)
        if parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("PUBLIC_URL must be an origin, without a path, query or credentials")

    def load(self, name):
        result=json.loads((self.config_dir / name).read_text())
        if name=='access.json' and (self.data_dir/'mcp-connections.sqlite3').exists():
            from .connections import ConnectionRegistry
            result=ConnectionRegistry(self).merged_policy(result)
        return result


ROOT = Path(__file__).resolve().parent.parent
