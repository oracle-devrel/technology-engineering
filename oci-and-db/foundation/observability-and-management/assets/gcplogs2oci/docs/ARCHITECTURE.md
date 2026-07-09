# Architecture

## Data Flow

```
GCP Cloud Logging
      │
      ▼
Log Router Sink (filter: severity >= DEFAULT, audit logs, etc.)
      │
      ▼
GCP Pub/Sub Topic (oci-log-export-topic)
      │  ← 7-day message retention buffer
      ▼
Pull Subscription (fluentd-oci-bridge-sub)
      │
      ▼
┌─────────────────────────────────┐
│  Bridge (pick one)              │
│                                 │
│  A) Python SDK bridge           │
│     (bridge/main.py)            │
│     Uses google-cloud-pubsub    │
│     + oci Python SDK            │
│                                 │
│  B) Fluentd container           │
│     (docker/Dockerfile)         │
│     Uses fluent-plugin-gcloud   │
│     + fluent-plugin-kafka       │
└─────────────────────────────────┘
      │
      ▼
OCI Streaming (gcp-inbound-stream)
      │  ← Kafka-compatible, partitioned buffer
      ▼
Connector Hub (GCP-Stream-to-LogAnalytics)
      │  ← Managed cursor, auto-retry
      ▼
OCI Log Analytics
      │  ← GCP Cloud Logging JSON Parser (44 field mappings)
      ▼
Log Group: GCPLogs
      │  ← 40 custom fields: Cloud Provider, Resource Type, HTTP fields, ...
      ▼
Dashboards & Queries
```

## Components

| Stage            | Component                    | Protocol         | Resilience                         |
|------------------|------------------------------|------------------|-----------------------------------|
| Primary Buffer   | GCP Pub/Sub                  | gRPC / REST      | 7-day retention, pull delivery     |
| Forwarder        | Python bridge / Fluentd      | gRPC → REST/Kafka| Stateless, restartable             |
| Secondary Buffer | OCI Streaming                | Kafka (TCP/9092) | Partitioned, configurable retention|
| Orchestration    | Connector Hub                | Internal         | Managed cursor, retry              |
| Parsing          | GCP Cloud Logging JSON Parser| Internal         | 44 JSON field mappings             |
| Destination      | OCI Log Analytics            | Internal         | Indexed, queryable, dashboardable  |

## OCI Resources Created by `setup_oci.sh`

The setup script provisions **7 resources** in sequence:

| Step | Resource | Type | Purpose |
|------|----------|------|---------|
| 1 | Stream Pool | OCI Streaming | Kafka-compatible pool with SASL/SSL |
| 2 | Stream | OCI Streaming | Message buffer (`gcp-inbound-stream`) |
| 3 | Kafka info | — | Prints bootstrap servers for Fluentd |
| 4 | Log Group | Log Analytics | `GCPLogs` target group |
| 5 | Fields + Parser | Log Analytics | 40 custom fields + JSON parser with 44 mappings |
| 6 | Source | Log Analytics | `GCP Cloud Logging Logs` source (references parser) |
| 7 | Connector Hub | SCH | Streaming → Log Analytics connector |

## Log Analytics Field Mapping

The GCP Cloud Logging JSON Parser extracts fields from the [LogEntry](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry) JSON structure:

### Built-in Fields

| OCI Field | JSON Path | GCP Field |
|-----------|-----------|-----------|
| Message | `$.jsonPayload.message` | jsonPayload.message |
| Severity | `$.severity` | severity |
| Time | `$.timestamp` | timestamp |
| Method | `$.protoPayload.methodName` | protoPayload.methodName |

### Multicloud Field

| OCI Field | JSON Path | Description |
|-----------|-----------|-------------|
| Cloud Provider | `$.cloudProvider` | Injected by bridge (`"GCP"`) for multicloud dashboards |

### Core GCP LogEntry Fields

| OCI Field | JSON Path |
|-----------|-----------|
| GCP Insert ID | `$.insertId` |
| GCP Log Name | `$.logName` |
| GCP Resource Type | `$.resource.type` |
| GCP Project ID | `$.resource.labels.project_id` |
| GCP Service Name | `$.protoPayload.serviceName` |
| GCP Method Name | `$.protoPayload.methodName` |
| GCP Principal Email | `$.protoPayload.authenticationInfo.principalEmail` |
| GCP Zone | `$.resource.labels.zone` |
| GCP Instance ID | `$.resource.labels.instance_id` |
| GCP Trace ID | `$.trace` |
| GCP Span ID | `$.spanId` |
| GCP Text Payload | `$.textPayload` |
| GCP Receive Timestamp | `$.receiveTimestamp` |

### HTTP Request Fields (Cloud Run, Load Balancer)

| OCI Field | JSON Path |
|-----------|-----------|
| GCP HTTP Method | `$.httpRequest.requestMethod` |
| GCP HTTP URL | `$.httpRequest.requestUrl` |
| GCP HTTP Status | `$.httpRequest.status` |
| GCP HTTP Latency | `$.httpRequest.latency` |
| GCP HTTP Protocol | `$.httpRequest.protocol` |
| GCP HTTP Remote IP | `$.httpRequest.remoteIp` |
| GCP HTTP Request Size | `$.httpRequest.requestSize` |
| GCP HTTP Response Size | `$.httpRequest.responseSize` |
| GCP HTTP Server IP | `$.httpRequest.serverIp` |
| GCP HTTP User Agent | `$.httpRequest.userAgent` |

### Cloud Run Resource Labels

| OCI Field | JSON Path |
|-----------|-----------|
| GCP Configuration Name | `$.resource.labels.configuration_name` |
| GCP Location | `$.resource.labels.location` |
| GCP Cloud Run Service | `$.resource.labels.service_name` |
| GCP Revision Name | `$.resource.labels.revision_name` |
| GCP Label Instance ID | `$.labels.instanceId` |

### Audit Log Extended Fields

| OCI Field | JSON Path |
|-----------|-----------|
| GCP Resource Name | `$.protoPayload.resourceName` |
| GCP Caller IP | `$.protoPayload.requestMetadata.callerIp` |
| GCP Caller User Agent | `$.protoPayload.requestMetadata.callerSuppliedUserAgent` |

### Resource Labels (Multi-Type)

| OCI Field | JSON Path | Resource Types |
|-----------|-----------|----------------|
| GCP Subscription ID | `$.resource.labels.subscription_id` | pubsub_subscription |
| GCP Topic ID | `$.resource.labels.topic_id` | pubsub_topic |
| GCP Sink Name | `$.resource.labels.name` | logging_sink |
| GCP Sink Destination | `$.resource.labels.destination` | logging_sink |

### Operation & Source Location

| OCI Field | JSON Path |
|-----------|-----------|
| GCP Operation ID | `$.operation.id` |
| GCP Source File | `$.sourceLocation.file` |
| GCP Source Line | `$.sourceLocation.line` |
| GCP Source Function | `$.sourceLocation.function` |

### Multicloud Dashboard Support

The bridge injects `cloudProvider: "GCP"` into every log entry before sending to OCI Streaming. This enables multicloud dashboards:

```
'Cloud Provider' = 'GCP' | stats count by 'GCP Resource Type'
```

```
* | stats count by 'Cloud Provider'
```

The parser handles partial field extraction — fields not present in a particular log entry (e.g., `httpRequest` for stdout logs) are null.

## Bridge Options

### Option A: Python SDK Bridge (Recommended for Development & Testing)

- Runs as a long-lived Python process
- Uses `google-cloud-pubsub` streaming pull API with callback-based processing
- Writes to OCI Streaming via `oci` Python SDK PutMessages API
- Supports drain mode (`--drain`) — exits after inactivity timeout
- GCP auth: Application Default Credentials (ADC) or service account key
- OCI auth: API signing key from `OCI_KEY_FILE` (local) or `OCI_KEY_CONTENT` (CI/containers)

### Option B: Fluentd Container (Recommended for Production on OCI)

- Runs as a Docker container on OCI Container Instances
- Uses `fluent-plugin-gcloud-pubsub-custom` for GCP pull
- Uses `fluent-plugin-kafka` for OCI Streaming output (Kafka protocol)
- Secrets mounted from OCI Vault at `/mnt/secrets/`
- No VM required (serverless container instance)

## Security

- **GCP credentials**: Application Default Credentials for local dev; service account JSON key stored in OCI Vault for production, never committed to git
- **OCI credentials**: API signing key via file path (local) or inline PEM (CI); auth token for Kafka interface
- **Network**: Container Instance runs in private subnet with NAT gateway (outbound only)
- **Encryption**: TLS 1.2 in transit, AES-256 at rest (both clouds)
- **Least privilege**: GCP bridge SA uses resource-scoped Pub/Sub roles; OCI uses explicit SCH/bridge policies (see `docs/IAM_PRIVILEGES.md`)

## Failure Modes

1. **Bridge crash**: GCP Pub/Sub retains unacknowledged messages; bridge resumes from last checkpoint
2. **OCI Streaming down**: Python bridge buffer fills and backpressure stops pulls; Fluentd `overflow_action block` does the same
3. **Log Analytics maintenance**: Connector Hub holds its cursor; Stream retains data (configurable up to 7 days)
4. **Parser mismatch**: JSON parser extracts null for missing fields (no errors); raw JSON is always stored in `Original Log Content`
