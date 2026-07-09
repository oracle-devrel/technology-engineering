# Parser Readiness: EventData

**Status:** pending parser extraction
**Phase:** 9

`EventData` is a dynamic Sentinel payload container. The Phase 9 mapping points it at `Original Log Content` and marks it `parser_change_required: true` so converter output remains skipped with `parser_readiness:pending:EventData` until a SOC parser extracts the required nested values.

Required next step: add parser extraction for the specific EventData keys used by the candidate query, then update the field dictionary and remove the pending flag only after synthetic and live validation pass.

