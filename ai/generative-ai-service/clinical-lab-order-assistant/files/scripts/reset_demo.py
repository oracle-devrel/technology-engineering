"""Reload the fictional seed patients: uv run python scripts/reset_demo.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gateway import records  # noqa: E402

print(f"Reloaded {records.reset()} fictional patients into {records.DB_PATH}")
