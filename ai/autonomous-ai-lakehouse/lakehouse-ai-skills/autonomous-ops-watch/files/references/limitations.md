# Limitations

This skill is intentionally limited to SQL-observable read-only evidence from one connected Oracle Autonomous AI Lakehouse.

## Not supported in v0.1

- Certifying patch readiness.
- Certifying operational health or safety.
- OCI API, OCI Events, Console, CLI, SDK, Resource Principal views, or OCI Logging integration.
- Lifecycle operations such as start, stop, restart, online restart, scale, terminate, clone, restore, or patch.
- Operator access enablement or disablement.
- External ETL jobs, schedulers, pipelines, or orchestration tools.
- DBMS_SCHEDULER job health checks.
- Object Storage posture, cost, budget, autoscaling, or backup posture checks.
- Multi-database inventory or comparison.
- Mutating SQL.

## Operational stance

The skill should help an operator understand evidence, not make operational approvals. If a user asks whether a system is ready, safe, or healthy, redirect to the evidence it can inspect and state what remains outside SQL visibility.
