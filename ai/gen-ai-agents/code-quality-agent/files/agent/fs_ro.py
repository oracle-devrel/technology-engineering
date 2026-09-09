"""
File name: fs_ro.py
Author: Luigi Saetta
Date last modified: 2026-01-07
Python Version: 3.11

License:
    MIT

Description:
    Read-only, sandboxed filesystem access to a root folder and its subfolders.
    Prevents path traversal and forbids access outside the configured root.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.config import FILES_PATTERN

# max file size to read
MAX_BYTES = 2_000_000


# for listing any file (not only python)
ALL_FILES_PATTERN = "*"


class SandboxViolation(Exception):
    """Raised when attempting to access paths outside the configured sandbox root."""


@dataclass(frozen=True)
class ReadOnlySandboxFS:
    root_dir: Path

    def __post_init__(self) -> None:
        root = self.root_dir.expanduser().resolve(strict=True)
        object.__setattr__(self, "root_dir", root)

    def _resolve_under_root(self, path: Path) -> Path:
        # Join relative paths to root; allow absolute paths only if still under root.
        candidate = (self.root_dir / path) if not path.is_absolute() else path
        resolved = candidate.expanduser().resolve(strict=False)

        # Python 3.11: Path.is_relative_to exists
        if not resolved.is_relative_to(self.root_dir):
            raise SandboxViolation(f"Access outside sandbox is forbidden: {resolved}")
        return resolved

    def list_source_files(self) -> list[Path]:
        """
        Return absolute Paths for all files under root matching pattern (recursive).

        For now we support only .py files.
        """
        return sorted(self.root_dir.rglob(FILES_PATTERN))

    def list_all_files(self) -> list[Path]:
        """
        Return absolute Paths for all files under root (recursive).
        """
        return sorted(
            [p for p in self.root_dir.rglob(ALL_FILES_PATTERN) if p.is_file()]
        )

    def read_text(
        self, rel_or_abs_path: str | Path, *, max_bytes: int = MAX_BYTES
    ) -> str:
        """Read a file as UTF-8 text (best-effort)."""
        p = self._resolve_under_root(Path(rel_or_abs_path))
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(str(p))

        # Guardrail for huge files
        size = p.stat().st_size
        if size > max_bytes:
            raise ValueError(f"File too large ({size} bytes). Refusing to read: {p}")

        data = p.read_bytes()
        return data.decode("utf-8", errors="replace")

    def relpath(self, abs_path: Path) -> Path:
        """Convert an absolute path under root to a relative path."""
        abs_resolved = abs_path.expanduser().resolve(strict=False)
        if not abs_resolved.is_relative_to(self.root_dir):
            raise SandboxViolation(f"Not under sandbox root: {abs_resolved}")
        return abs_resolved.relative_to(self.root_dir)
