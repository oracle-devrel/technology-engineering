---
name: database-sql-performance
description: Rank expensive Oracle SQL statements using verified Database Management AWR evidence. Use for top SQL and statement performance requests, rather than log searches.
---

Use Database Observability MCP through db_catalog and db_read. Discover managed databases in the selected compartment before selecting a database. If the user named a database, match its returned display name; otherwise report separate per-database rankings and exclusions rather than claiming a fleet winner.

For each supported target, call list_awr_dbs with the returned managed_database_id. Use its awr_db_id and container_id for list_awr_db_snapshots, then get_awr_db_report. These are Database Management identifiers; no Operations Insights AWR Hub is needed. Follow inventory pagination. Test one target before expanding. Report unsupported targets and failed requests individually.

Omit snapshot-ID filters in get_awr_db_report. The gateway selects the widest verified same-startup snapshot pair inside the requested window and forces a TEXT AWR report. Use the returned effective_window, snapshot IDs and SQL sections. Its verified_snapshot_count and startup_instance_groups describe available evidence; the selected pair does not mean that only one pair exists. Explain excluded periods and restart boundaries. If no complete snapshot interval fits, explain the missing coverage and suggest a wider look-back; do not silently expand the interval. AWR coverage is narrower than the selected window.

Unless specified, rank by elapsed time and label that choice. Report CPU and executions separately when the AWR tables provide them, with their actual units and attribution interval. Preserve SQL IDs and available statement text; distinguish missing text from absent SQL. Module or Action labels are metadata, not SQL text; report unavailable text explicitly instead of putting those labels in a statement column. A few report sections or truncated rows are not a complete workload inventory. A single AWR interval cannot establish degradation without a comparable baseline.

Log counts, alert rows, SQL-looking text in logs, and catalog discovery do not establish a top-SQL ranking. If the report or its SQL sections are unavailable, state that limitation and return partial evidence. Do not request broader IAM access unless a tool explicitly establishes a permission failure.
