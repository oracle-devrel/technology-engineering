"""Small OCI lookup helpers shared by discovery surfaces."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

_T = TypeVar("_T")


def safe_lookup(
    call: Callable[[], _T],
    default: _T,
    attempts: int = 2,
    on_error: Callable[[Exception], None] | None = None,
) -> _T:
    """Run a best-effort lookup, retrying before returning a default."""

    if attempts < 1:
        return default
    for attempt in range(attempts):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 - read-only discovery is best-effort
            if attempt == attempts - 1:
                if on_error is not None:
                    on_error(exc)
                return default
    return default
