# OKE Observability Runbook

This runbook captures the reusable OKE and OCI Kubernetes Monitoring checks used
for Forge and Octo APM OKE deployments. Keep it placeholder-safe: do not commit
tenancy names, OCIDs, public IPs, API tokens, backend URLs, or OCI profile names
from a live environment.

## Required Variables

Set these in your shell or CI secret context before running live checks:

```bash
export OCI_PROFILE="<oci-profile>"
export OCI_COMPARTMENT_ID="<observability-compartment-ocid>"
export OKE_CLUSTER_ID="<oke-cluster-ocid>"
export OKE_CLUSTER_NAME="<cluster-name>"
export ONM_NAMESPACE="oci-onm"
export LA_NAMESPACE="<log-analytics-namespace>"
export METRICS_NAMESPACE="mgmtagent_kubernetes_metrics"
```

For a generic product cluster, replace `oci-onm` only if the Helm release was
installed into a different namespace.

## OKE Deployment Checks

Before pushing a new container image, check the node architecture. Apple/ARM
workstations produce ARM images by default, while OKE workers are often AMD64.

```bash
kubectl config current-context
kubectl get nodes -o custom-columns=NAME:.metadata.name,ARCH:.status.nodeInfo.architecture,VERSION:.status.nodeInfo.kubeletVersion
```

Build and push for the node architecture, not the workstation architecture:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t "$IMAGE_REPO:$IMAGE_TAG" \
  --push .
```

Then apply the manifest and verify the rollout:

```bash
envsubst < deploy/oke/forge-frontend.yaml | kubectl apply -f -
kubectl rollout status deployment/<deployment-name> -n <namespace> --timeout=180s
kubectl get deploy,svc,pods -n <namespace> -o wide
```

For exposed web apps, verify through the external hostname and confirm old
admin or legacy routes are not exposed:

```bash
curl -k -I --max-time 20 "https://<hostname>/<expected-path>"
curl -k -fsS --max-time 20 "https://<hostname>/api/health"
curl -k -I --max-time 20 "https://<hostname>/<legacy-admin-path>"
```

Expected production posture:

- Public ingress is through the approved OCI Load Balancer and certificate.
- The app runs as non-root, with dropped Linux capabilities and no service
  account token unless the workload explicitly requires Kubernetes API access.
- Backend credentials are injected through Kubernetes secrets or an approved
  secret manager.
- The UI does not render tenancy data, OCIDs, backend URLs, tokens, public IPs,
  or profile names.

## OCI Kubernetes Monitoring Data Path

OCI Kubernetes Monitoring from `oracle-quickstart/oci-kubernetes-monitoring`
uses two distinct paths:

- Log Analytics path: `oci-onm-logan`, `oci-onm-logan-tcpconnect`, and the
  `oci-onm-discovery` CronJob upload Kubernetes logs, TCP-connect logs, object
  logs, and discovery payloads to Log Analytics.
- Metrics path: `oci-onm-mgmt-agent` writes Kubernetes metrics into OCI
  Monitoring, normally under `mgmtagent_kubernetes_metrics`.

This path does not require creating a new Service Connector Hub connector for
the Kubernetes logs collected by ONM.

Healthy baseline:

```bash
kubectl get pods -n "$ONM_NAMESPACE" -o wide
helm status oci-kubernetes-monitoring -n "$ONM_NAMESPACE"
kubectl get cm oci-onm-metrics -n "$ONM_NAMESPACE" -o json |
  jq -r '.data["monitoring.properties"]'
```

The `monitoring.properties` config should include:

```text
compartmentId=<observability-compartment-ocid>
clusterName=<cluster-key-used-by-metrics>
kubernetesNamespace=*
monitoringNamespace=mgmtagent_kubernetes_metrics
```

## Symptom: Latest Telemetry Unknown

If the OCI Kubernetes Monitoring Solution UI shows:

- `Cluster Created` as `Invalid Date`
- CPU and memory as blank
- `Latest telemetry` as `Unknown`

do not assume the collector is dead. First check whether telemetry is present
but the Log Analytics entity metadata is malformed.

### 1. Verify Discovery Uploads

```bash
latest_job=$(kubectl get jobs -n "$ONM_NAMESPACE" \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

kubectl logs -n "$ONM_NAMESPACE" "job/$latest_job" --tail=160 |
  rg 'Timestamp|Total count|Successfully uploaded|Response OPC|completed|Flag'
```

Expected signs:

- The job counts Kubernetes objects such as pods, services, nodes, and
  namespaces.
- It logs `Successfully uploaded object logs to OCI`.
- It logs `Successfully uploaded discovery payload to OCI`.
- It finishes with `Kubernetes discovery is successfully completed`.

### 2. Verify Current Metrics

```bash
START=$(python3 -c 'from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)-timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"))')

for metric in nodeCpuUsage nodeMemoryUsage podCpuUsage podMemoryUsage; do
  echo "== $metric =="
  oci monitoring metric-data summarize-metrics-data \
    --profile "$OCI_PROFILE" \
    -c "$OCI_COMPARTMENT_ID" \
    --namespace "$METRICS_NAMESPACE" \
    --query-text "${metric}[1m]{clusterName = \"$OKE_CLUSTER_NAME\"}.mean()" \
    --start-time "$START" \
    --resolution 1m \
    --output json |
    jq '.data[]? | {dimensions, points:(."aggregated-datapoints"|length), latest:(."aggregated-datapoints"[-1]?)}'
done
```

If these return current datapoints, ONM metrics are flowing. The console issue
is likely entity metadata or a UI refresh delay.

### 3. Inspect the Kubernetes Cluster Entity

```bash
oci log-analytics entity list \
  --profile "$OCI_PROFILE" \
  --namespace-name "$LA_NAMESPACE" \
  --compartment-id "$OCI_COMPARTMENT_ID" \
  --name-contains "$OKE_CLUSTER_NAME" \
  --limit 10 \
  --output json |
  jq '.data.items[]? | select(."entity-type-name"=="Kubernetes Cluster") |
      {entityName:.name, timeLastDiscovered:."time-last-discovered",
       metadata:(.metadata.items | map(select(.name=="cluster" or
         .name=="cluster_date" or .name=="name" or .name=="cluster_name" or
         .name=="metrics_namespace")))}'
```

The Oracle quickstart expects these metadata values:

| Metadata | Expected value |
|---|---|
| `cluster` | Cluster key used by the solution UI and metrics joins |
| `name` | Same cluster key |
| `cluster_name` | Human cluster name |
| `cluster_date` | Real RFC3339 timestamp, not `null` |
| `metrics_namespace` | OCI Monitoring namespace for Kubernetes metrics |

For greenfield installs, create the entity correctly before Helm install. For
existing installs, the entity name may be immutable; update metadata instead of
trying to rename it.

### 4. Derive a Valid Cluster Creation Timestamp

Some OKE API responses can return top-level `time-created` as `null`. In that
case, use `metadata["time-created"]` from the list response:

```bash
CLUSTER_CREATED=$(oci ce cluster list \
  --profile "$OCI_PROFILE" \
  -c "$OCI_COMPARTMENT_ID" \
  --name "$OKE_CLUSTER_NAME" \
  --output json |
  jq -r --arg id "$OKE_CLUSTER_ID" '.data[] | select(.id==$id) |
    .metadata["time-created"] | sub("\\+00:00$";"Z")')
```

The value should look like:

```text
YYYY-MM-DDTHH:MM:SSZ
```

### 5. Repair Existing Entity Metadata

```bash
ENTITY_JSON=/tmp/oke-entity.json
METADATA_JSON=/tmp/oke-entity-metadata.json

oci log-analytics entity list \
  --profile "$OCI_PROFILE" \
  --namespace-name "$LA_NAMESPACE" \
  --compartment-id "$OCI_COMPARTMENT_ID" \
  --name-contains "$OKE_CLUSTER_NAME" \
  --limit 10 \
  --output json > "$ENTITY_JSON"

ENTITY_ID=$(jq -r '.data.items[] |
  select(."entity-type-name"=="Kubernetes Cluster") | .id' "$ENTITY_JSON" |
  head -n 1)

jq --arg cluster "$OKE_CLUSTER_NAME" --arg date "$CLUSTER_CREATED" '
  (.data.items[] | select(."entity-type-name"=="Kubernetes Cluster") | .metadata) as $metadata
  | $metadata
  | .items |= map(
      if .name == "cluster" then .value = $cluster
      elif .name == "name" then .value = $cluster
      elif .name == "cluster_date" then .value = $date
      elif .name == "deployment_status" then .value = "ACTIVE"
      else . end
    )
' "$ENTITY_JSON" > "$METADATA_JSON"

oci log-analytics entity update \
  --profile "$OCI_PROFILE" \
  --namespace-name "$LA_NAMESPACE" \
  --entity-id "$ENTITY_ID" \
  --metadata "file://$METADATA_JSON" \
  --time-last-discovered "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --force
```

Note: use `--time-last-discovered` on metadata updates. Otherwise the update
can clear the last-discovered value, which may also feed solution UI freshness.

### 6. Force Discovery and Recheck

```bash
job="oci-onm-discovery-manual-$(date +%s)"
kubectl create job -n "$ONM_NAMESPACE" --from=cronjob/oci-onm-discovery "$job"
kubectl wait -n "$ONM_NAMESPACE" --for=condition=complete "job/$job" --timeout=120s
kubectl logs -n "$ONM_NAMESPACE" "job/$job" --tail=140 |
  rg 'Successfully uploaded|Kubernetes discovery|Response OPC|completed'
```

After the forced run:

- `timeLastDiscovered` should advance.
- `cluster_date` should remain valid.
- Node and pod metrics should still return current datapoints.
- The OCI Console Solution UI can take a few minutes to refresh.

## Common Failure Modes

| Symptom | Likely cause | Check |
|---|---|---|
| `Invalid Date` | `cluster_date` is `null` or malformed | Inspect entity metadata |
| `Latest telemetry Unknown` with live metrics | Entity `cluster`/`name` does not match metrics `clusterName` or `timeLastDiscovered` is stale | Compare entity metadata and MQL dimensions |
| Discovery jobs complete but no metrics | Management Agent path is unhealthy or metric namespace/name is wrong | Check `oci-onm-mgmt-agent`, `oci-onm-metrics`, and MQL |
| Metrics present for old cluster key only | Helm values or entity metadata changed after install | Query metric definitions grouped by `clusterName` |
| Image pulls but pod crashes immediately | Image built for wrong CPU architecture | Compare image platform with `kubectl get nodes` architecture |
| UI exposes legacy/admin route | Routing or Next middleware gap | `curl -I` the old route and expect `404` |

## Reusable Acceptance Checklist

Use this checklist for other OKE clusters or product demos:

- `kubectl get nodes` confirms target CPU architecture before image build.
- OKE deployment uses an image built for that architecture.
- Rollout is complete and all replicas are ready.
- Public routes return expected status codes and security headers.
- Legacy/admin routes are not exposed.
- ONM Helm release is deployed and expected DaemonSets/StatefulSets/CronJobs
  are healthy.
- Discovery upload logs show successful object and discovery payload uploads.
- Log Analytics Kubernetes Cluster entity metadata has valid `cluster_date`,
  `cluster`, `name`, `cluster_name`, and `metrics_namespace`.
- OCI Monitoring has current `nodeCpuUsage`, `nodeMemoryUsage`, `podCpuUsage`,
  and `podMemoryUsage` datapoints for the same cluster key.
- No committed docs, manifests, or UI output contain live OCIDs, public IPs,
  profile names, backend URLs, or secrets.
