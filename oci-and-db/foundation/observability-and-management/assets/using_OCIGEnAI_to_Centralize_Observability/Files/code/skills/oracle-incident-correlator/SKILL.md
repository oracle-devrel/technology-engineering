---
name: oracle-incident-correlator
description: Correlate application symptoms with verified database and host evidence in a shared time window. Use for incident relationships, not automatic remediation.
---

1. Establish explicit resource links using service configuration, returned identifiers, observed endpoints or trace/request IDs. Similar names and a shared compartment are insufficient. Keep application/resource ID/link evidence/confidence in a small mapping table.
2. Collect scoped log evidence through log_query and approved DB/host metrics through db_catalog and db_read. List the correct inventory first. Stop a branch when a prerequisite, resource mapping or operation is unavailable.
3. Use the selected absolute UTC window; preserve backend rounding and lag. Distinguish parent CDB and PDB load, DB Management and Operations Insights IDs, rates and cumulative counters.
4. Align events by event time, not query execution time. Compare observed ordering, plausible mechanism, dependency mapping and counterevidence. Label temporal overlap as a lead unless stronger evidence supports causation.
5. Return a timeline, ranked explanations, uncertainty and one targeted next check per material gap. Missing samples do not establish an idle or healthy resource.
6. APM queries, direct SQL, blocking-session actions, arbitrary infrastructure tools and changes are unavailable here. Do not infer their results. Use the error workflow for log details and disclose the native orchestrator limitation. No external notifications or automatic remediation.
