"""Local UI demo with explicit fake identity and no cloud connections."""
import json
import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
config = root/'data'/'demo-config'
config.mkdir(parents=True,exist_ok=True)
(config/'access.json').write_text((root/'config'/'access.example.json').read_text())
(config/'mcp.json').write_text('{}')
(config/'models.json').write_text((root/'config'/'models.example.json').read_text())
os.environ.update(APP_MODE='demo',PUBLIC_URL='http://localhost:8000',
    SESSION_SECRET=secrets.token_urlsafe(48),DATA_DIR=str(root/'data'/'demo'),CONFIG_DIR=str(config))
import uvicorn
uvicorn.run('assistant.web:create_app',factory=True,host='127.0.0.1',port=8000,workers=1,access_log=False)
