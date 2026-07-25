# IAM Privileges by Used Service

This project touches both **Google Cloud** and **Oracle Cloud Infrastructure (OCI)** services. The recommendations below are derived from the API operations in:

- `bridge/gcp_subscriber.py`
- `bridge/oci_stream_sender.py`
- `scripts/setup_gcp.sh`
- `scripts/setup_oci.sh`
- `scripts/test_gcp_credentials.py`
- `scripts/test_oci_credentials.py`

Two IAM helper scripts are provided and are idempotent:

- `./scripts/setup_gcp_iam.sh`
- `./scripts/setup_oci_iam.sh`

## Canonical Service Names (Vendor Docs)

| CSP | Service name used in this repo | Vendor documentation |
|---|---|---|
| GCP | Cloud Logging | [Cloud Logging docs](https://docs.cloud.google.com/logging/docs) |
| GCP | Pub/Sub | [Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview) |
| OCI | Streaming | [Streaming docs](https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm) |
| OCI | Log Analytics | [Log Analytics docs](https://docs.oracle.com/en-us/iaas/log-analytics/home.htm) |
| OCI | Connector Hub (formerly Service Connector Hub) | [Connector Hub overview](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm) |

## GCP

### Runtime and Integration Principals

| Principal | Used service | Why | Recommended privilege | Documentation |
|---|---|---|---|---|
| Bridge service account (`oci-log-shipper-sa`) | Pub/Sub subscription | `SubscriberClient.subscribe()` + ack/nack | `roles/pubsub.subscriber` on the bridge subscription | [Pub/Sub IAM access control](https://docs.cloud.google.com/pubsub/docs/access-control) |
| Bridge service account (`oci-log-shipper-sa`) | Pub/Sub topic/subscription metadata | Credential/status diagnostics (`get_topic`, `get_subscription`) | `roles/pubsub.viewer` on the bridge topic and subscription | [Pub/Sub IAM access control](https://docs.cloud.google.com/pubsub/docs/access-control) |
| Logging sink writer identity (`gcp-to-oci-sink`) | Cloud Logging + Pub/Sub topic | Cloud Logging sink publishes exported logs into Pub/Sub | `roles/pubsub.publisher` on the bridge topic | [Route log entries (Log Router)](https://docs.cloud.google.com/logging/docs/routing/overview), [Pub/Sub IAM access control](https://docs.cloud.google.com/pubsub/docs/access-control) |

### Setup Principal (Optional, automation only)

If you use a dedicated principal for `setup_gcp.sh`, grant:

- `roles/serviceusage.serviceUsageAdmin`
- `roles/pubsub.admin`
- `roles/logging.configWriter`
- `roles/iam.serviceAccountAdmin`
- `roles/iam.serviceAccountKeyAdmin`
- `roles/resourcemanager.projectIamAdmin`

References:

- [Service Usage IAM](https://docs.cloud.google.com/service-usage/docs/access-control)
- [Pub/Sub IAM access control](https://docs.cloud.google.com/pubsub/docs/access-control)
- [Cloud Logging IAM roles](https://docs.cloud.google.com/logging/docs/access-control)
- [IAM roles overview](https://docs.cloud.google.com/iam/docs/understanding-roles)

`setup_gcp_iam.sh` applies these optional setup roles only when `GCP_SETUP_PRINCIPAL` is set.

## OCI

### Runtime and Integration Principals

| Principal | Used service | Why | Recommended privilege | Documentation |
|---|---|---|---|---|
| Bridge runtime group (API-key user in this group) | Streaming | `StreamClient.put_messages()` in `bridge/oci_stream_sender.py` | `use stream-push` in target compartment | [Streaming docs](https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm), [Streaming policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/streamingpolicyreference.htm) |
| Bridge runtime group (API-key user in this group) | Streaming metadata | `StreamAdminClient.get_stream()` in `scripts/test_oci_credentials.py` | `inspect streams` in target compartment | [Streaming policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/streamingpolicyreference.htm) |
| Connector Hub service principal (formerly Service Connector Hub) | Streaming | Reads from OCI Stream source | `use stream-pull` + `use stream-consume` with `request.principal.type='serviceconnector'` | [Connector Hub overview](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm), [Streaming policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/streamingpolicyreference.htm) |
| Connector Hub service principal (formerly Service Connector Hub) | Log Analytics | Writes into target log group | `use log-analytics-log-group` with `request.principal.type='serviceconnector'` | [Log Analytics docs](https://docs.oracle.com/en-us/iaas/log-analytics/home.htm), [Log Analytics policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/loganalyticspolicyreference.htm) |

### Setup Operator Group (Optional, automation only)

If you use a dedicated OCI group for `setup_oci.sh` / `destroy_oci.sh`, grant:

- `manage stream-pools`
- `manage streams`
- `manage serviceconnectors`
- `manage log-analytics-log-group`
- `manage loganalytics-features-family`

All scoped to the target compartment.

References:

- [Connector Hub policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/serviceconnectorhubpolicyreference.htm)
- [Streaming policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/streamingpolicyreference.htm)
- [Log Analytics policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/loganalyticspolicyreference.htm)

Note: OCI IAM resource-types above intentionally use exact policy-reference spellings (`serviceconnectors`, `loganalytics-features-family`, `stream-pull`, `stream-push`).

## Usage

### Apply GCP IAM

```bash
./scripts/setup_gcp_iam.sh
```

Optional setup roles:

```bash
GCP_SETUP_PRINCIPAL="user:admin@example.com" ./scripts/setup_gcp_iam.sh
```

### Apply OCI IAM

`setup_oci_iam.sh` always applies Connector Hub runtime policy.

```bash
./scripts/setup_oci_iam.sh
```

To also apply operator + bridge group policies:

```bash
OCI_IAM_OPERATOR_GROUP="gcplogs2oci-operators" \
OCI_IAM_BRIDGE_GROUP="gcplogs2oci-bridge" \
./scripts/setup_oci_iam.sh
```

Connector-Hub-only mode:

```bash
./scripts/setup_oci_iam.sh --sch-only
```
