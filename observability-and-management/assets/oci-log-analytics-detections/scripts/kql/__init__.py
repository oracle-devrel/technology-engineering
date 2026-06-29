"""KQL→Logan QL subpackage.

Phase 6 extracted the converter pipeline out of ``scripts/convert_sentinel_kql.py``
into this package. The legacy facade re-exports the public API from D-15
(see ``.planning/phases/06-*/06-CONTEXT.md``); new callers should prefer the
typed surface here.
"""
