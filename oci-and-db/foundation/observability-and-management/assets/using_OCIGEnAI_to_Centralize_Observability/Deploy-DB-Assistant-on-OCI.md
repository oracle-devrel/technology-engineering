# Deploy your own DB Assistant on OCI

A practical companion to **GenAI Observability (R)evolution: From Dashboards to Answers**.

This guide deploys the reference assistant on an existing Oracle Kubernetes Engine (OKE) cluster. It connects OCI Generative AI to Database Management, Operations Insights and Log Analytics through governed MCP calls, adds company sign-in and conversation history, and optionally exports execution traces to OCI APM.

**All supplied configuration uses examples.** There are no real tenancy identifiers, user identifiers, OCIDs, signing keys or live service addresses in this deployment package. Values beginning with `REPLACE_WITH_` must be supplied privately by the operator. Short `ocid1.*.test` identifiers in automated tests are synthetic fixtures, not resources to deploy.

## 1. What you will deploy

```text
DBA browser
  → HTTPS load balancer
  → DB Assistant: sign-in, conversations, environment grants
    → selected OCI-hosted GenAI model
    → skills + policy-enforcing MCP gateway
      → Oracle Database Observability MCP → Database Management / Operations Insights
      → LogAn MCP                         → Log Analytics
      → project-owned identity and model-catalog MCP adapters
    → SQLite + encrypted connection registry on persistent storage
    → optional metadata-only OpenTelemetry traces → OCI APM
```

The supplied deployment uses an **internal HTTPS load balancer**, one application replica, one worker and a persistent volume. Users need a routed corporate network or VPN connection. This is a reference prototype; an external queue, shared database and additional operational engineering are needed before scaling it to multiple replicas.

The MCP servers are installed into the container image and launched on demand as isolated STDIO processes for a test or investigation. You do not start a laptop MCP server for this deployment. An existing remote MCP is an optional later configuration.

### Package layout

All implementation files and templates are in [Files/code](Files/code/README.md):

| Path | Purpose |
|---|---|
| `Files/code/assistant/` | Web backend, GenAI adapters, MCP clients, gateway, authorization, conversations and tracing. |
| `Files/code/static/` | Chat interface, model menu and administrator configuration page. |
| `Files/code/skills/` | Coverage, application errors, incident correlation and SQL-performance workflows. |
| `Files/code/config/` | Example access, model, MCP and OCI configuration. |
| `Files/code/deploy/` | OKE workload, persistent storage, HTTPS service and network policy. |
| `Files/code/scripts/` | Configuration preparation, preview, connection checks and session revocation. |
| `Files/code/tests/` | Local tests with synthetic identities and mocked services. |

## 2. Prepare the prerequisites

An OCI administrator needs to prepare the following:

- An OKE cluster with working OCI load-balancer integration, a reachable Kubernetes API and an `oci-bv` storage class. Check that the CNI enforces Kubernetes NetworkPolicy.
- Worker capacity for the manifest's requests and limits: 500 millicores / 1 GiB requested; 2 CPUs / 4 GiB maximum per assistant pod, plus a 50 GiB volume.
- A hostname such as `db-assistant.example.com`, a trusted matching TLS certificate and private key, DNS control, and network access from users to the internal load balancer.
- An OCI IAM Identity Domain for human sign-in and an administrator able to register a confidential application.
- A dedicated backend service user, API signing key and scoped OCI permissions. This identity is separate from the human users who log in to the website.
- OCI GenAI inference and catalog access in the chosen region, with at least one available OCI-hosted Chat model supported by the application. Availability and tool-call compatibility must be checked in your tenancy.
- Database Management and Operations Insights already enabled on the targets you want to investigate, and Log Analytics already collecting their relevant logs. Confirm that sample data is recent in the native services first.
- Optionally, an APM domain and a dedicated private ingestion key for the assistant.
- Local OCI CLI, `kubectl`, Docker with Buildx, Python 3.13 and access to your container registry. Image builds also need GitHub and Python package-index access.

These instructions do not provision a VCN, OKE cluster, database or management agent. Onboard those resources using your organization's normal OCI process before connecting them to this assistant. Connecting an MCP does not enable collection or create historical data.

Budget for OKE infrastructure, load balancing, storage, model inference, observability collection and retention. Resource sizing and application query budgets do not establish a monetary spending cap.

## 3. Open the source package and optionally preview the UI

Run commands from the extracted deployment package directory:

```sh
cd Files/code
python3.13 -m venv .venv
.venv/bin/python -m pip install -e .
```

For a local demonstration without cloud calls:

```sh
.venv/bin/python -m scripts.preview
```

Open `http://localhost:8000` and choose **Sign in**. The preview uses a labelled fake user and sample answers. It does not verify OCI, IAM, GenAI or either MCP. Stop it before continuing; never expose demo mode as a deployed service.

## 4. Prepare private configuration

Create working copies and generate a fresh session secret and connection-encryption key:

```sh
.venv/bin/python -m scripts.prepare_config
```

The helper refuses to overwrite existing configuration. It creates `.env`, `config/access.json`, `config/mcp.json`, `config/models.json`, and `secrets/config`. It does not contact OCI or create a cloud identity.

Edit the working files locally. They are excluded from version control and the container build context.

| Setting or file | What to enter |
|---|---|
| `.env`: `PUBLIC_URL` | Exact HTTPS origin, for example `https://db-assistant.example.com`; no path or trailing slash. |
| `.env`: `OIDC_ISSUER` | Your identity domain's issuer from OIDC discovery. |
| `.env`: `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` | The dedicated application's credentials from step 5. |
| `.env`: `OCI_REGION` | Region used for monitoring and GenAI in this initial deployment. |
| `.env`: `GENAI_COMPARTMENT_ID` | Your approved GenAI inference/catalog compartment identifier. |
| `.env`: `OCI_LA_NAMESPACE` | Your Log Analytics namespace. |
| `.env`: `GENAI_MODEL_ID` | Optional preferred model identifier; leave empty to choose from the discovered catalog. |
| `secrets/config` | Dedicated service user, tenancy, public-key fingerprint and region. Keep `key_file=/secrets/oci/key.pem`, the container mount path. |
| `secrets/key.pem` | The corresponding service user's private API signing key. |
| `config/access.json` | Exact monitored compartment name and identifier, allowed groups/subjects, and an administrator subject. |

Register the public half of your service user's API key in OCI. Keep the private half only in protected operator storage and your approved secret-delivery system. The service account does not need a console password for API signing.

Keep the generated `CONNECTION_ENCRYPTION_KEY` stable across restarts. Back it up separately from the data volume; losing it prevents decrypting registered MCP credentials. `SESSION_SECRET` protects OIDC state and must also be kept private. Neither key should be pasted into the article, screenshots or shared examples.

### Environment grants

In `config/access.json`, change the example compartment name and identifier together: the identity adapter verifies that they match. Each environment queries **one exact compartment**. Parent access does not grant descendants; configure authorized children separately. Optional `parent_compartment_id` values only organize the selector hierarchy.

Use the exact group strings present in the verified ID-token claim, or explicit verified subjects. A successful sign-in does not itself grant an environment. The `administrators` entry separately controls access to the connection-configuration page.

## 5. Configure company sign-in

In your OCI IAM Identity Domain:

1. Register a dedicated confidential OIDC application for the assistant.
2. Enable authorization-code flow, client-secret authentication and PKCE using S256.
3. Register `https://db-assistant.example.com/auth/callback`, replacing the example hostname with the exact deployed hostname.
4. Allow the `openid`, `profile` and `email` scopes. Assign the intended users/groups and activate the application.
5. Configure a list-valued `groups` claim in the ID token, or use explicit subject grants in the assistant. Set `OIDC_GROUPS_CLAIM` if your claim has a different name.
6. Put the issuer, client ID and secret in the private `.env` file.

After deployment, a signed-in user can inspect `/api/me` to see their verified subject and group values. The administrator can use those values for the environment grants. Do not assume the login name, email address and OIDC subject are interchangeable.

Human sign-in controls portal access. The backend service identity supplies OCI credentials for MCP and GenAI calls; the prototype does not impersonate the human user's OCI console session.

## 6. Grant the backend OCI permissions

Create a dedicated backend group and service user in your selected identity domain. The [example policy file](Files/code/deploy/iam-policy.example.txt) uses the fictional domain `ExampleDomain`, group `DBAssistantBackend`, monitoring compartment `ExampleObservability` and GenAI compartment `ExampleGenAI`.

Replace these names with your own privately and have the administrator review the statements. Install policies at a level that can grant the named scopes; tenancy-scoped statements need tenancy-level authority. The deployment operator's OKE/registry provisioning permissions are separate and are not granted to the running assistant.

The example grants observability reads and billable GenAI chat. Certain Log Analytics query/schema resource types require tenancy scope; log-content access is constrained by the authorized log groups and the assistant's exact-compartment query arguments. Review inherited IAM grants as well as this file. Do not resolve a denied read by granting `manage all-resources`.

Consult the current primary references for your target features: [GenAI IAM](https://docs.oracle.com/en-us/iaas/Content/generative-ai/iam-policies.htm), [Database Management permissions](https://docs.oracle.com/en-us/iaas/database-management/doc/database-management-permissions.html), [Operations Insights policies](https://docs.oracle.com/en-us/iaas/operations-insights/doc/create-policies-using-console.html) and [Log Analytics policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/loganalyticspolicyreference.htm).

Enabling monitoring may require additional service-onboarding policies and database credentials. Those are administrator tasks, separate from this runtime read policy. Database edition and feature entitlement also affect available performance evidence.

## 7. Review the MCPs, skills and model policy

The supplied `config/mcp.example.json` defines these server-side connections:

| Entry | Implementation |
|---|---|
| `db` | `oracle.oci-db-observability-mcp-server`, installed in `/opt/db`. |
| `logan` | `oci-logan-mcp`, installed in `/opt/logan`, with the included STDIO launcher. |
| `identity` | Project-owned adapter that verifies configured compartments through OCI Identity. |
| `model_catalog` | Project-owned adapter that discovers regional OCI GenAI offerings. |

The upstream projects are [Oracle Database Observability MCP](https://github.com/oracle/mcp/tree/main/src/oci-db-observability-mcp-server) and [LogAn MCP](https://github.com/rishabh-ghosh24/logan-mcp-server). The Dockerfile fetches specific source commits. Its documented OCI SDK compatibility override and Logan packaging adjustment are part of this reference build; validate any dependency update with the connection checks.

The assistant exposes a curated read-only subset through its gateway. Installing an upstream MCP does not make every upstream operation available to the model. Detailed application workflows live in `skills/*/SKILL.md`; the upstream Database Observability skill catalog is separate discovery metadata.

The model menu uses live OCI discovery. `config/models.json` can additionally allow or block model identifiers. Use models hosted within OCI; unsupported APIs, external-provider offerings and ineligible models are disabled. Catalog presence does not prove inference entitlement or reliable function calling.

## 8. Build and publish the image

Choose the platform matching your OKE workers: `linux/arm64` for Ampere or `linux/amd64` for x86. Authenticate to your OCI Container Registry using your organization's approved credential mechanism; avoid putting passwords in commands or shared history.

```sh
export IMAGE_REGISTRY='REPLACE_WITH_OCIR_REGISTRY_HOST'
export IMAGE_NAMESPACE='REPLACE_WITH_REGISTRY_NAMESPACE'
export IMAGE_TAG='reference-0.2.0'
export TARGET_PLATFORM='linux/arm64'

docker login "$IMAGE_REGISTRY"
docker buildx build --platform "$TARGET_PLATFORM" \
  -t "$IMAGE_REGISTRY/$IMAGE_NAMESPACE/db-assistant:$IMAGE_TAG" \
  --push .
```

Record the published digest. Replace `REPLACE_WITH_OCIR_IMAGE_DIGEST` in `deploy/oke.yaml` with your immutable image reference, using the form `registry.example.com/example/db-assistant@sha256:REPLACE_WITH_DIGEST`.

The container build installs application and MCP dependencies. The source bundle does not contain upstream MCP source trees, binaries or a prebuilt image. Review third-party licenses and scan/lock the image and dependencies in your release process.

## 9. Create Kubernetes configuration and secrets

Connect your OCI CLI and Kubernetes client to the intended cluster. For example, with an operator-supplied identifier:

```sh
export OKE_CLUSTER_ID='REPLACE_WITH_YOUR_CLUSTER_IDENTIFIER'
oci ce cluster create-kubeconfig --cluster-id "$OKE_CLUSTER_ID" \
  --file "$HOME/.kube/config" --region 'REPLACE_WITH_YOUR_REGION' \
  --token-version 2.0.0 --kube-endpoint PRIVATE_ENDPOINT
kubectl config current-context
kubectl get nodes
kubectl get storageclass oci-bv
```

Use your cluster's supported endpoint and routing. Inspect the context before creating resources. Then, from `Files/code`:

```sh
kubectl create namespace db-assistant

kubectl -n db-assistant create configmap db-assistant-config \
  --from-file=access.json=config/access.json \
  --from-file=mcp.json=config/mcp.json \
  --from-file=models.json=config/models.json \
  --from-file=logan_stdio.py=config/logan_stdio.py

kubectl -n db-assistant create secret generic db-assistant-settings \
  --from-env-file=.env

kubectl -n db-assistant create secret generic db-assistant-oci \
  --from-file=config=secrets/config \
  --from-file=key.pem=secrets/key.pem

kubectl -n db-assistant create secret tls db-assistant-tls \
  --cert=secrets/fullchain.pem --key=secrets/tls.key
```

Place your trusted certificate chain and its private key at those protected paths first. Create the `ocir-pull` image-pull secret through your approved registry-secret workflow, or adjust the manifest to your cluster's supported pull authentication. Prefer your organization's Vault integration for ongoing secret delivery. Kubernetes Secret objects also require suitable RBAC, storage encryption and administrative controls.

These are first-install commands. If a namespace or object already exists, inspect it and use a reviewed update process rather than overwriting another deployment.

## 10. Optionally configure OCI APM

In the APM domain chosen for this deployment, create a dedicated **private** data key for DB Assistant. Put the values into a protected `secrets/apm.env` file using the [example](Files/code/config/apm.env.example):

```sh
kubectl -n db-assistant create secret generic db-assistant-apm \
  --from-env-file=secrets/apm.env
```

Use the domain's actual data-upload endpoint with the `/20200101/opentelemetry/private/v1/traces` suffix. The application adds the `Authorization: dataKey ...` header; do not append the key to the URL. See [Oracle's OpenTelemetry configuration](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/configure-opentelemetry.html).

The application records a conversation trace ID, separate interaction spans and child spans for GenAI, skills, gateway operations and MCP calls. The creation-root span is short; it does not measure the whole lifetime of a conversation. Prompt text, answers, raw logs, tool arguments, user identities and credentials are excluded from the configured APM attributes. Persisted conversation content remains in the application's data volume and needs its own retention controls.

Leave both APM settings empty and omit the optional secret to disable export. Never use the literal example key. Confirm ingestion in APM after deployment; exporter startup alone is insufficient evidence.

## 11. Deploy the workload and HTTPS endpoint

Before applying the manifests:

1. Set the image digest and confirm storage class, capacity and worker architecture.
2. Keep one replica, `Recreate` and one Uvicorn worker for SQLite and local jobs.
3. Review `deploy/service.yaml`. Its default is an internal flexible OCI load balancer with TLS termination on port 443 and HTTP to backend port 8000.
4. Replace the documentation-only ingress CIDR `192.0.2.0/24` in `deploy/network-policy.yaml` with the actual permitted LB/node source CIDRs for your CNI and traffic path. It intentionally does not describe a working network.
5. Ensure DNS and outbound HTTPS connectivity to OCI APIs and the identity issuer. The network policy permits HTTPS egress generally; apply destination controls through your network design where required.
6. Configure private load-balancer subnets, NSGs, health-check paths and VCN routing as required by your cluster. The manifests do not create these network prerequisites. If you require encrypted backend traffic, add a TLS-capable backend/proxy and the corresponding LB configuration.

```sh
kubectl apply -f deploy/oke.yaml
kubectl apply -f deploy/network-policy.yaml
kubectl apply -f deploy/service.yaml
kubectl -n db-assistant rollout status deployment/db-assistant --timeout=300s
kubectl -n db-assistant get pods,pvc,service
```

Configure DNS for the chosen HTTPS hostname using the load balancer's assigned address. Confirm certificate trust and the exact sign-in callback URL. The annotations follow the [OKE load-balancer reference](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingloadbalancer_topic-Summaryofannotations.htm).

If a public endpoint is required, review network exposure, allowed clients, certificate management and identity settings before changing the internal-LB annotation. This guide keeps the deployment private by default.

## 12. Verify the complete path

First inspect the model catalog:

```sh
kubectl -n db-assistant exec deployment/db-assistant -- \
  /opt/app/bin/python -m scripts.check_connections --list-models
```

Then check model function calling, identity verification and MCP discovery:

```sh
kubectl -n db-assistant exec deployment/db-assistant -- \
  /opt/app/bin/python -m scripts.check_connections
```

The second command makes one small **billable** model request. Use `--model REPLACE_WITH_SERVER_ISSUED_MODEL_ALIAS` to test another eligible menu choice. Discovery checks do not retrieve monitoring evidence; complete the browser checks too.

| Check | Evidence to look for |
|---|---|
| Assigned user signs in | Only authorized environments appear. |
| Unassigned user signs in | No environment access; direct API attempts are rejected. |
| “Check database and log monitoring coverage.” | Actual database/insight inventory and log query results, including last-seen timestamps and explicit gaps. |
| “Which database has the highest CPU utilization?” | Measured CPU samples with units and time window; an empty response must not become zero utilization. |
| “Show recent alert-log rows for EXAMPLEDB.” | Database/entity/source mapping verified from evidence, actual log rows and timestamps. |
| “Show top SQL by elapsed time for EXAMPLEDB.” | Database Observability/AWR path, SQL IDs, actual snapshot interval and any target/feature limitations. |
| Follow up in the same conversation | Earlier context is available and the environment remains fixed. |
| Trace the two-message conversation | One conversation trace ID with distinct interaction spans and actual GenAI/skill/MCP child spans in APM. |
| Restart the application | Saved history survives on the PVC; unfinished investigations are marked interrupted. |
| Request a restart or another unauthorized compartment | No mutation or out-of-scope tool executes. |

Replace `EXAMPLEDB` with a database returned by your own inventory. A ready pod or healthy `/healthz` endpoint only confirms web-process health. It does not establish model, MCP or data availability.

## 13. Add another MCP connection

Sign in as a configured portal administrator and open **Configuration**:

1. Select **Database Observability** or **LogAn**.
2. Choose a bundled MCP or an already-running HTTPS MCP. Supply an operator-provisioned OCI profile or the required service credentials, target region and compartment. LogAn also needs its namespace.
3. Use **Save, start & test**. The test verifies compartment identity and a scoped read.
4. Assign tested connections to a named environment and grant specific verified groups/subjects. Paired connections must use the same tenancy and region.
5. Start a new conversation in that environment.

The page starts only bundled, pinned MCP implementations; it does not install arbitrary customer packages or accept shell commands. A remote server must already expose compatible MCP Streamable HTTP on public HTTPS port 443 with a trusted certificate. Private remote endpoints and certificate bypasses are not supported by this prototype.

For another tenancy, use credentials authorized there or an independently configured remote server. Inference remains in the assistant's configured OCI GenAI compartment, so review the sharing of monitoring evidence across that boundary. Adding a connection does not automatically add new tool types or new skills.

## 14. Troubleshooting

| Symptom | First checks |
|---|---|
| No assigned environments | Inspect the current user's `/api/me` subject/groups and compare them with `access.json`; verify the mounted configuration refreshed. Reauthenticate after group changes. |
| Login/callback error | Exact HTTPS origin and redirect URI, OIDC issuer discovery, client credentials, assignment, token claim shape and clock synchronization. |
| Image pull or pending pod | Registry credential, image/platform, worker capacity, PVC binding and storage class. |
| 502/503 or unreachable website | Service endpoints, ready pod, LB backend health, source CIDRs, NSGs, CNI policy support and DNS/TLS. |
| MCP startup failure | Image contains `/opt/db` and `/opt/logan`, launch paths match, signing-key mount is readable, OCI profile is valid, and outbound APIs are reachable. |
| Log query rejected | Distinguish gateway query restrictions from OCI IAM denial. Check authorized log groups, correct namespace and exact compartment before changing permissions. |
| No CPU samples | Check the requested window, returned managed-database and insight IDs, monitoring enrollment and source freshness. Missing samples do not prove an idle database. |
| Empty/ineligible model menu | Region, catalog permission, hosted-model availability, supported API format and model policy. Run the connection checker for each selected model. |
| No APM traces | Private endpoint/key pair, secret loading, HTTPS egress and APM indexing. Search using the UI trace ID and service name `db-assistant`. |
| Cannot open stored MCP credentials | Restore the original `CONNECTION_ENCRYPTION_KEY`; changing it does not re-encrypt old records. |

Inspect deployment events and logs in your protected operator session:

```sh
kubectl -n db-assistant describe pod -l app=db-assistant
kubectl -n db-assistant logs deployment/db-assistant --tail=100
```

Do not attach unreviewed logs, transcripts, private configuration or data-volume contents to a public issue.

## 15. Operate, update and remove the prototype

- Back up the SQLite data volume and protect conversation/report contents. Upstream MCPs may also write runtime artifacts; apply a retention policy to the entire volume.
- Keep backend IAM permissions, portal environment grants and administrator grants aligned. They are separate controls.
- Rotate signing keys, OIDC credentials, registry credentials and TLS certificates through your secret-management process. Environment-variable secret changes require a new pod.
- Preserve the connection-encryption key when restoring the database. Back up before a software update or schema migration.
- Sign-in group claims are cached in the app session. For immediate revocation, remove access grants and use the included operator command with the verified subject:

```sh
kubectl -n db-assistant exec deployment/db-assistant -- \
  /opt/app/bin/python -m scripts.revoke_sessions --subject 'REPLACE_WITH_VERIFIED_SUBJECT'
```

- Build a new immutable image and update the digest for a release. Keep the previous image and a compatible pre-update data backup for rollback. Recreate deployments cause a short outage and interrupt active investigations.
- A simple restart is:

```sh
kubectl -n db-assistant rollout restart deployment/db-assistant
kubectl -n db-assistant rollout status deployment/db-assistant --timeout=300s
```

To remove a dedicated test installation, first back up any required history and confirm the namespace contains only this prototype. Deleting the namespace removes its secrets and PVC; storage deletion depends on the volume reclaim policy.

```sh
kubectl delete namespace db-assistant
```

Verify load-balancer and volume cleanup in OCI. Remove the dedicated OIDC app, service-user key and now-unused policies/registry credentials through your administrator process. Leave shared observability services and monitored targets intact.

## Validation status and publication boundary

This is a sanitized source snapshot adapted from the prototype. The replacement configuration deliberately cannot connect to the original environment. Local source/configuration checks are documented in [VALIDATION.md](Files/code/VALIDATION.md); a fresh image build, live cloud deployment and the acceptance checks above remain required in the reader's tenancy.

Only share the provided source package. Do not rebuild a public archive from a configured working directory: `.gitignore` does not protect files copied by a generic archiver. Exclude private `.env` files, signing/TLS keys, active configuration, databases, backups, run artifacts and logs. Review publication rights and dependency licenses before making a repository public.
