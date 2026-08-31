# Alerts setup for OCI Database environment

## 1. Scope

This Terraform configuration creates a production-focused notification channel
and baseline Database Service critical-event rule for the selected compartment,
even when Database Management, Operations Insights, and Log Analytics are not
enabled. It also creates OCI Monitoring alarms, conditional Operations Insights
reports, and conditional Log Analytics critical-event alarms when their source
service is available. It creates one Notifications topic per selected
compartment and subscribes `test@acme.com` using the `EMAIL` protocol. If an
active topic with the configured name already exists, Terraform reuses it.

The configuration creates only alerting resources. It never enables, onboards,
or changes Database Management, Operations Insights, or Log Analytics. Those
services can require database credentials, private endpoints, IAM policy,
network access, and licensing decisions that must be approved separately.


### Architecture

The diagram shows the always-on baseline path: Terraform creates an OCI Events
rule for Database Service critical events, routes them to the
`database-alerts` Notifications topic, and delivers the notification by email.
Database Management metric alarms, Operations Insights reports, and Log
Analytics detection rules join the same topic only after their respective
service check succeeds. A failed check is reported in Terraform outputs and
does not enable or configure the missing service.

The editable source is available in [Draw.io format](files/database-alerts-architecture.drawio).

![OCI Database Alerts architecture](files/database-alerts-architecture1.png)

[![Deploy to OCI](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https%3A%2F%2Fgithub.com%2Foracle-devrel%2Ftechnology-engineering%2Farchive%2Frefs%2Fheads%2Fsciunzi_Db_alerts.zip)



## 2. Target

Provide one target selector in `terraform.tfvars`:

| Selector | Behaviour |
|---|---|
| `compartment_id` | Selects all Database Management managed databases in that compartment. This takes precedence over `tags`. |
| `tags` | Used only if `compartment_id` is null. Selects Database Management managed databases with all supplied free-form tag key/value pairs. |

`notification_topic_name` defaults to `database-alerts`. Set it to a different
name if the existing topic is not the intended notification channel.

The discovery query targets `DbmgmtManagedDatabase` resources, which is the
Database Management service check. A database that is not enabled for Database
Management is not selected and receives no metric alarms. When
`compartment_id` is set, the baseline Notifications topic, email subscription,
and Database Service critical-event rule are nevertheless created. If no
eligible database matches, Terraform emits the
`database_management_not_enabled_warning` output.

Example configuration:

```hcl
compartment_id = "ocid1.compartment.oc1..replace_me"

# Ignored because compartment_id is set.
tags = {
  environment = "production"
}
```

## 3. Description of the alerts created

Rows marked **Created conditionally** are created automatically only when the
service check reports that the relevant service is already enabled for the
selected database. Terraform reports an unavailable service in
`service_preflight_report` and does not attempt to enable it.

| Alert or report | OCI service needed to detect it | Signal / condition | Notification channel | Severity | Deployment status |
|---|---|---|---|---|---|
| Database Management collection failure | Database Management and OCI Monitoring | `oracle_oci_database` / `MonitoringStatus` has `errorSeverity = ERROR` | `database-alerts` | Critical | Created now |
| Sustained CPU utilization | Database Management and OCI Monitoring | `CpuUtilization` ≥ `cpu_critical_percent` | `database-alerts` | Critical | Created now |
| Database storage utilization | Database Management and OCI Monitoring | `StorageUtilization` ≥ `storage_critical_percent` | `database-alerts` | Critical | Created now |
| Flash Recovery Area utilization | Database Management Full Management and OCI Monitoring | `FRAUtilization` ≥ `fra_critical_percent` | `database-alerts` | Critical | Created now when `enable_full_management_alarms = true` |
| Data Guard apply lag | Database Management Full Management, Data Guard, and OCI Monitoring | `ApplyLag` ≥ `dataguard_apply_lag_critical_seconds` | `database-alerts` | Critical | Created now when `enable_full_management_alarms = true` |
| Tablespace utilization | Database Management and OCI Monitoring | `StorageUtilizationByTablespace` ≥ `tablespace_warning_percent` / `storage_critical_percent` | `database-alerts` | Warning / Critical | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Data Guard transport lag | Database Management Full Management, Data Guard, and OCI Monitoring | `TransportLag` ≥ `dataguard_apply_lag_critical_seconds` | `database-alerts` | Critical | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Backup failure or recovery breach | Database Management Full Management and OCI Monitoring | `BackupJobFailure` or `RecoveryWindow` metric reports a value | `database-alerts` | Critical | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Database Management job failure | Database Management and OCI Monitoring | `dbmgmtJobExecutionsCount` with `status = Failed` | `database-alerts` | Warning | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Session or process exhaustion | Database Management Full Management and OCI Monitoring | `SessionLimitUtilization` or `ProcessLimitUtilization` ≥ warning / critical threshold | `database-alerts` | Warning / Critical | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Persistent blocking sessions | Database Management Full Management and OCI Monitoring | `BlockingSessions` >0 for 15 minutes | `database-alerts` | Warning | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Invalid objects or unusable indexes | Database Management Full Management and OCI Monitoring | `InvalidObjects` or `UnusableIndexes` >0 | `database-alerts` | Warning | Created conditionally when Database Management is enabled and `enable_recommended_alarms = true` |
| Database, DB node, or DB system critical condition | Database Service Events, OCI Events, and OCI Notifications | Database Critical, DB Node Critical, or DB System Critical event | `database-alerts` | Critical | Created now, even without Database Management, Ops Insights, or Log Analytics |
| DB node error / warning | Database Service Events, OCI Events, and OCI Notifications | DB Node Error or DB Node Warning event | `database-alerts` | Warning | Created now when `enable_recommended_alarms = true` |
| Capacity and inventory digest | Operations Insights News Reports | Weekly capacity-planning, actionable-insight, and top-database summary | `database-alerts` | Info | Created conditionally when a selected OpsInsights is `ENABLED` |
| AWR ingestion delay | Operations Insights reporting and OCI Monitoring | `AwrIngestionLag` ≥ `awr_ingestion_lag_warning_seconds` | `database-alerts` | Warning | Created conditionally when a selected OpsInsights is `ENABLED` and `enable_recommended_alarms = true` |
| Database crash | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Abnormal Termination` | `database-alerts` | Critical | Created conditionally when Log Analytics is onboarded and the target has an active entity with sources |
| Internal Oracle incident | Log Analytics, Database Alert/Trace Logs, and ingest-time detection rule | Label `Internal Error`; e.g. ORA-00600 or ORA-07445 | `database-alerts` | Critical | Created conditionally |
| Data corruption | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Data Corruption` | `database-alerts` | Critical | Created conditionally |
| Storage or I/O error | Log Analytics, Database Alert/Trace Logs, and ingest-time detection rule | Label `Storage Error` or `I/O Error` | `database-alerts` | Critical | Created conditionally |
| Database startup or availability failure | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Availability Error` | `database-alerts` | Critical | Created conditionally |
| Listener connection failure burst | Log Analytics and Database Listener Alert Logs | Label `Connection Error` | `database-alerts` | Warning | Created conditionally when Log Analytics is active and `enable_recommended_alarms = true` |
| Database timeout burst | Log Analytics and Database Alert Logs | Label `Timeout` | `database-alerts` | Warning | Created conditionally when Log Analytics is active and `enable_recommended_alarms = true` |
| Privileged login or audit-policy change | Log Analytics and Oracle Unified DB Audit Logs | Label `Privileged Login` or `Audit Policy Change` | `database-alerts` | Warning / Critical | Created conditionally when Log Analytics is active and `enable_recommended_alarms = true` |

### Notification channels

| Channel | Intended recipients and transport | Use |
|---|---|---|
| `database-alerts` | OCI Notifications `EMAIL` subscription to `test@acme.com` | The channel created or reused by this Terraform deployment. It receives Database Service events, all Database Management alarms, conditional Log Analytics events, and conditional Operations Insights reports. Critical alarms repeat hourly while firing. |
| `db-prod-critical` | DBA/on-call pager, incident-management webhook, and optionally email | Immediate action for outages, Data Guard RPO breach, data corruption, FRA exhaustion, and monitoring blindness. Acknowledge and investigate 24×7. |
| `db-prod-operations` | DBA operations queue, ticketing integration, and email/Teams | Action during operational support hours for capacity pressure, failed jobs, blocking sessions, listener error bursts, and configuration problems. |
| `db-capacity-reports` | Capacity planner, service owner, and DBA distribution list | Scheduled weekly report rather than a pager. Covers Ops Insights forecasts, top consumers, utilization changes, and inventory changes. |
| `db-security` | Security Operations Center and DBA security owner | Security and audit events: privileged logons, failed-login bursts, grants/revokes, user changes, and audit-policy changes. |

All implemented alarms route to `database-alerts`. The other named channels
remain optional routing extensions for teams that want separate operational,
capacity, or security recipients.
OCI sends a subscription confirmation email to `test@acme.com`; the channel is
not active until the recipient confirms it.


## 4. References

- [Database Management tagging and Search](https://docs.oracle.com/en-us/iaas/database-management/doc/tags-and-search-database-management.html) documents the `DbmgmtManagedDatabase` OCI Search resource type and query examples.
- [OCI Search overview](https://docs.oracle.com/en-us/iaas/Content/Search/Concepts/queryoverview.htm) documents resource-query scope and supported resource types.
- [OCI Resource Manager deploy button](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/deploybutton.htm) documents pre-loading a stack with a public ZIP URL.


