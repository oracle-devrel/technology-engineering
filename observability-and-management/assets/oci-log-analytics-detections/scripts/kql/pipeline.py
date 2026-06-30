"""KQL→Logan QL pipeline entry point.

Phase 6 PR-1: ``convert()`` delegates to the legacy
``convert_kql_to_logan`` to preserve behavior. Plan 06-10 replaces this
delegation with real ``OPERATOR_REGISTRY`` dispatch.
"""

from __future__ import annotations


def convert(kql: str, mapping: dict, allowed_aliases=None):
    """Convert a KQL query string to Logan QL.

    Signature matches the legacy ``convert_kql_to_logan(kql, mapping)``
    so callers can migrate import paths without behavior change.
    """

    from scripts import convert_sentinel_kql as _legacy

    return _legacy.convert_kql_to_logan(kql, mapping)


__all__ = ["convert"]
