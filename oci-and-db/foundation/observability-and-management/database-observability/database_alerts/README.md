# Alerts setup for OCI Database environment


## 1. Scope

This Terraform configuration creates a production-focused notification channel,
OCI Monitoring alarms, conditional Operations Insights reports, and conditional
Log Analytics critical-event alarms for Oracle databases already enabled for
the relevant OCI service. It creates one Notifications topic per selected
compartment and subscribes `test@acme.com` using the `EMAIL` protocol.

The configuration creates only alerting resources. It never enables, onboards,
or changes Database Management, Operations Insights, or Log Analytics. Those
services can require database credentials, private endpoints, IAM policy,
network access, and licensing decisions that must be approved separately.

## 2. Target

Provide one target selector in `terraform.tfvars`:

| Selector | Behaviour |
|---|---|
| `compartment_id` | Selects all Database Management managed databases in that compartment. This takes precedence over `tags`. |
| `tags` | Used only if `compartment_id` is null. Selects Database Management managed databases with all supplied free-form tag key/value pairs. |

The discovery query targets `DbmgmtManagedDatabase` resources, which is the
Database Management service check. A database that is not enabled for Database
Management is not selected and receives no metric alarms. If no eligible
database matches, Terraform creates no topic, subscription, or alarm and emits
the `database_management_not_enabled_warning` output.

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
| Tablespace utilization | Database Management and OCI Monitoring | `StorageUtilizationByTablespace` ≥80% / ≥90% | `db-prod-operations` / `db-prod-critical` | Warning / Critical | Recommended next phase |
| Data Guard transport lag | Database Management Full Management, Data Guard, and OCI Monitoring | `TransportLag` above the agreed RPO for two samples | `db-prod-critical` | Critical | Recommended next phase |
| Backup failure or recovery breach | Database Management Full Management and OCI Monitoring | Backup job fails, `RecoveryWindow` or `UnprotectedDataWindow` breaches policy | `db-prod-critical` | Critical | Recommended next phase |
| Database Management job failure | Database Management and OCI Monitoring | `dbmgmtJobExecutionsCount` with `status = Failed` | `db-prod-operations` | Warning | Recommended next phase |
| Session or process exhaustion | Database Management Full Management and OCI Monitoring | `SessionLimitUtilization` or `ProcessLimitUtilization` ≥75% / ≥90% | `db-prod-operations` / `db-prod-critical` | Warning / Critical | Recommended next phase |
| Persistent blocking sessions | Database Management Full Management and OCI Monitoring | `BlockingSessions` >0 for 15 minutes | `db-prod-operations` | Warning | Recommended next phase |
| Invalid objects or unusable indexes | Database Management Full Management and OCI Monitoring | New `InvalidObjects` or `UnusableIndexes` count >0 | `db-prod-operations` | Warning | Recommended next phase |
| Database or DB system unavailable | Database Service Events, OCI Events, and OCI Notifications | Database Critical, DB Node Critical, or DB System Critical event | `db-prod-critical` | Critical | Recommended next phase |
| DB node error / warning | Database Service Events, OCI Events, and OCI Notifications | DB Node Error or repeated DB Node Warning event | `db-prod-operations` | Warning | Recommended next phase |
| Capacity and inventory digest | Operations Insights News Reports | Weekly capacity-planning, actionable-insight, and top-database summary | `database-alerts` | Info | Created conditionally when a selected Database Insight is `ENABLED` |
| AWR ingestion delay | Operations Insights reporting | AWR import lag exceeds the agreed freshness target | `db-prod-operations` | Warning | Recommended next phase; requires a separate Ops Insights metric/alarm extension |
| Database crash | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Abnormal Termination` | `database-alerts` | Critical | Created conditionally when Log Analytics is onboarded and the target has an active entity with sources |
| Internal Oracle incident | Log Analytics, Database Alert/Trace Logs, and ingest-time detection rule | Label `Internal Error`; e.g. ORA-00600 or ORA-07445 | `database-alerts` | Critical | Created conditionally |
| Data corruption | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Data Corruption` | `database-alerts` | Critical | Created conditionally |
| Storage or I/O error | Log Analytics, Database Alert/Trace Logs, and ingest-time detection rule | Label `Storage Error` or `I/O Error` | `database-alerts` | Critical | Created conditionally |
| Database startup or availability failure | Log Analytics, Database Alert Logs, and ingest-time detection rule | Label `Availability Error` | `database-alerts` | Critical | Created conditionally |
| Listener connection failure burst | Log Analytics, Database Listener Alert Logs, and scheduled saved search | Label `Connection Error` ≥5 events per listener in 5 minutes | `db-prod-operations` | Warning | Recommended next phase |
| Database timeout burst | Log Analytics, Database Alert Logs, and scheduled saved search | Label `Timeout` ≥5 events per entity in 5 minutes | `db-prod-operations` | Warning | Recommended next phase |
| Privileged login or audit-policy change | Log Analytics and Oracle Unified DB Audit Logs | Privileged login outside approved window; audit policy changed | `db-security` | Warning / Critical | Recommended next phase |

### Notification channels

| Channel | Intended recipients and transport | Use |
|---|---|---|
| `database-alerts` | OCI Notifications `EMAIL` subscription to `test@acme.com` | The channel created by this Terraform deployment. It receives current Critical metric alarms, conditional Log Analytics critical events, and conditional weekly Ops Insights News Reports. Critical alarms repeat hourly while firing. |
| `db-prod-critical` | DBA/on-call pager, incident-management webhook, and optionally email | Immediate action for outages, Data Guard RPO breach, data corruption, FRA exhaustion, and monitoring blindness. Acknowledge and investigate 24×7. |
| `db-prod-operations` | DBA operations queue, ticketing integration, and email/Teams | Action during operational support hours for capacity pressure, failed jobs, blocking sessions, listener error bursts, and configuration problems. |
| `db-capacity-reports` | Capacity planner, service owner, and DBA distribution list | Scheduled weekly report rather than a pager. Covers Ops Insights forecasts, top consumers, utilization changes, and inventory changes. |
| `db-security` | Security Operations Center and DBA security owner | Security and audit events: privileged logons, failed-login bursts, grants/revokes, user changes, and audit-policy changes. |

Only `database-alerts` is created today. The other channels remain a
recommended extension for different operational and security audiences.
OCI sends a subscription confirmation email to `test@acme.com`; the channel is
not active until the recipient confirms it.

## 4. Deploy workflow

1. Change to the Terraform directory, then copy the example input file and set
   the target, thresholds, and resource tags.

   ```bash
   cd files
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Use the **Deploy to OCI** button to pre-load the published branch in
   Resource Manager. Set the working directory to
   `oci-and-db/foundation/observability-and-management/database-observability/database_alerts/files`, then review and apply the stack. Or deploy with the CLI from `files`:

   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. During planning, the configuration discovers only Database Management managed
   databases. When none are found, it reports
   `database_management_not_enabled_warning` and makes no alerting changes.
   It does not attempt to enable Database Management.

4. Terraform performs a per-target service preflight without enabling any
   service:

   - **Database Management:** only `DbmgmtManagedDatabase` targets are selected.
   - **Operations Insights:** an `ENABLED` Database Insight is required before a
     weekly News Report is created for its compartment.
   - **Log Analytics:** the tenancy must be onboarded and the target must have
     an active Log Analytics entity with at least one source association before
     critical-label detection rules and the corresponding alarm are created.

   Review `service_preflight_report` for targets that did not pass one of these
   checks. They are reported, skipped, and never enabled by this configuration.

5. Confirm the email subscription. Review the selected databases and topic IDs
   with the outputs below before relying on the alerts:

   - `selected_managed_databases`
   - `notification_topic_ids`
   - `email_subscription_status`
   - `database_management_not_enabled_warning`
   - `service_preflight_report`
   - `ops_insights_news_report_ids`
   - `log_analytics_alert_database_ids`

The Terraform principal requires permission to search Database Management
resources, read database metrics, and manage Monitoring alarms, Notifications
topics, and subscriptions in every selected compartment.

The button uses the public ZIP archive of the `sciunzi_Db_alerts` branch.
[Oracle's deploy-button documentation](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/deploybutton.htm)
describes the `zipUrl` parameter used to pre-load a configuration into Resource Manager.

[![Deploy to OCI](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/technology-engineering/raw/refs/heads/sciunzi_Db_alerts/oci-and-db/foundation/observability-and-management/database-observability/database_alerts/files/database-alerts-resource-manager.zip)

> The button pre-loads the public `sciunzi_Db_alerts` branch of the
> `oracle-devrel/technology-engineering` repository into OCI Resource Manager.
> In the Create stack page, set the working directory to
> `oci-and-db/foundation/observability-and-management/database-observability/database_alerts/files`, then review and apply the stack. OCI requires this review and apply step; the button does not bypass it.

