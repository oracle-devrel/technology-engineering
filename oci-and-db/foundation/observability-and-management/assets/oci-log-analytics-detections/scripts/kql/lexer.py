"""KQL stage splitter.

Phase 6 delegates to the legacy implementation in
``scripts/convert_sentinel_kql.py`` so behavior is preserved. Plan 06-10
replaces the delegation with the real implementation moved here.
"""

from __future__ import annotations

from typing import List


def split_kql_stages(kql: str) -> List[str]:
    """Split a KQL query into top-level pipeline stages.

    Behavior-preserving wrapper around ``_split_kql_stages`` in the legacy
    facade module. Imported lazily to avoid an import cycle (the facade
    re-exports symbols from this package).
    """

    from scripts import convert_sentinel_kql as _legacy

    return _legacy._split_kql_stages(kql)


__all__ = ["split_kql_stages"]
