---
name: application-error-investigator
description: List or investigate application errors using scoped log evidence, grouped signatures, freshness and targeted next checks.
---

1. Establish the real namespace, source, entity or service identity. A text match on a friendly application name is a candidate, not verified identity.
   For a log-row listing, first discover source/entity pairs using `* | stats count as Records, max(Time) as LastSeen by 'Log Source', Entity | head 50`. Match the requested DB to an observed entity; the source may be `Database Alert Logs`, not the DB name. Use exact observed values in the pre-pipe filter. OCI queries are pipelines, not SQL, and use `stats count` rather than `count()`.
2. Use log_query to check counts and max(Time) for that identity in the fixed window. If absent, report missing coverage and ask the user to select a historical window before widening it.
3. Search a selective pre-pipe application filter plus error predicates; aggregate by component/error signature and first/last seen, then retrieve a bounded sample. Discover and validate field names from returned records. Preserve is_partial and truncated indicators.
4. Group repeated stack-trace lines, retries and Kubernetes snapshots carefully. Do not label log-line counts as unique failed requests. Compute an error rate only with a matching request denominator.
5. For investigation intent, build a chronological evidence table and rank likely explanations. Seek independent counterevidence and a concrete next check. For listing intent, stop after counts and examples.
   If the user asks for all alert rows, count that exact source/entity filter and then retrieve up to 50 rows with the same filter and `| fields time, mtgt, msrcid, msg | sort time | head 50`. Those internal fields return Time, Entity, Log Source and Message. Without fields, the server may return only source/entity metadata. Present every returned timestamp and message; claim completeness only if the count and returned rows agree and no partial/truncation flag is set. Do not substitute a monitoring-coverage audit, require Operations Insights, or add an errors-only predicate to an all-alert request.
6. The portal's exact-scope gateway does not expose the native Logan incident/report orchestrator because that tool cannot explicitly exclude subcompartments. This port performs bounded log investigation through run_query and produces the portal report. State any unavailable baseline comparison, parser triage or source-health check; do not imply the native orchestrator ran.
7. Explain historical versus current findings, freshness, unresolved identity, failed checks and coverage limits. Redact sensitive values. Do not change infrastructure or send messages.
