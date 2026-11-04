"""Run the demo: uv run python scripts/serve.py  (gateway on :8001, web on :3000, both loopback)."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / ".env").exists():
    raise SystemExit("Create .env from .env.example first (endpoint and compartment OCIDs).")
if not (ROOT / "web/.next/BUILD_ID").exists():
    raise SystemExit("Build the web app first: cd web && npm install && npm run build")
processes = []


def shutdown(*_):
    for process in processes:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    for process in processes:
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)


signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
try:
    processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "gateway.app:app", "--host", "127.0.0.1", "--port", "8001"], cwd=ROOT, start_new_session=True))
    processes.append(subprocess.Popen(["npm", "run", "start", "--", "--hostname", "127.0.0.1", "--port", "3000"], cwd=ROOT / "web", start_new_session=True))
    print("\nLabSense: http://localhost:3000\nPress Ctrl+C to stop both services.\n", flush=True)
    while all(p.poll() is None for p in processes):
        time.sleep(1)
finally:
    shutdown()
