# EventHubsNamespaceToOCIStreaming (Event Hub-triggered Azure Function)

Purpose:
- Processes events from Azure Event Hub in real-time and forwards them to Oracle Cloud Infrastructure (OCI) Streaming using the PutMessages API.
- Batching with 1MB and count limits, base64-encodes payloads as required by OCI.
- Event Hub trigger processes events as they arrive (no polling/scheduling).

Folder contents:
- eventhub_to_oci/__init__.py: Function logic (Event Hub trigger + OCI sender)
- eventhub_to_oci/function.json: Event Hub trigger binding (real-time processing)
- requirements.txt: Python deps (azure-functions, azure-eventhub, oci)
- host.json: Function host configuration (extension bundle v4+)

Supported configuration (App Settings):
- EventHubsConnectionString: Event Hubs namespace-level connection string (RootManageSharedAccessKey with Listen)
- EventHubName: Single Event Hub name bound to the trigger (first hub if you listed multiple)
- MessageEndpoint or OCI_MESSAGE_ENDPOINT: OCI Streaming message endpoint (e.g., https://cell-1.streaming.<region>.oci.oraclecloud.com)
- StreamOcid or OCI_STREAM_OCID: Target OCI stream OCID
- OCI credentials:
  - user: OCI user OCID
  - key_content: Private key content (single-line supported; function rewraps to PEM)
  - pass_phrase: Optional
  - fingerprint: API key fingerprint (must match the private key)
  - tenancy: OCI tenancy OCID
  - region: OCI region name
- Optional:
  - MaxBatchSize (default 100): Maximum messages per batch
  - MaxBatchBytes (default 1048576): Maximum batch size in bytes (1MB OCI limit)

Deploy from Azure portal (custom template)
- Use deploy/azuredeploy.json with Azure Portal > Create a resource > Template deployment (custom). The template prompts for Function App name, Event Hubs connection, consumer group, the single `EventHubName` required by the trigger, optional CSV of hubs for helper scripts, OCI credentials, message endpoint, stream OCID, and optional batch sizes.
- Provide an HTTPS URL to the packaged zip (WEBSITE_RUN_FROM_PACKAGE) so the portal can deploy without CLI. You can generate the zip locally or use the GitHub Actions artifact described below.

Trigger:
- Event Hub trigger: Processes events in real-time as they arrive in the configured Event Hub.

Prerequisites:
- Azure:
  - Event Hubs namespace and hubs populated with logs
  - Azure subscription + permissions to create Function App and Storage
  - Consumer group for this function
- OCI:
  - Streaming Stream in target compartment
  - API signing keys configured for the user whose OCID is used
- Tools:
  - Azure CLI (az)
  - zip (or 7z) for packaging deploy artifacts

One-liner to list hub names and build EventHubNamesCsv:
az eventhubs eventhub list -g <rg> --namespace-name <namespace> --query "[].name" -o tsv | paste -sd, -

Local run (optional):
- Create EventHubsNamespaceToOCIStreaming/local.settings.json (do not check into source):
{
  "IsEncrypted": false,
  "Values": {
  "AzureWebJobsStorage": "UseDevelopmentStorage=true",
  "FUNCTIONS_WORKER_RUNTIME": "python",
  "EventHubsConnectionString": "Endpoint=sb://<ns>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=...;",
  "EventHubConsumerGroup": "$Default",
  "EventHubName": "insights-activity-logs",
  "EventHubNamesCsv": "insights-activity-logs",
  "MessageEndpoint": "https://cell-1.streaming.<region>.oci.oraclecloud.com",
  "StreamOcid": "ocid1.stream.oc1..xxxx",
    "user": "ocid1.user.oc1..xxxx",
    "key_content": "-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----",
    "pass_phrase": "",
    "fingerprint": "<fingerprint>",
    "tenancy": "ocid1.tenancy.oc1..xxxx",
    "region": "<oci-region>",
    "MaxBatchSize": "100",
    "MaxBatchBytes": "1048576",
    "InactivityTimeout": "10"
  }
}
- Run: func start
- For a quick local smoke test against OCI, copy `.env.example` to `.env.local` at repo root, set EventHubsConnectionString and the OCI *stream* OCID (not stream pool), then run `./scripts/drain_eventhub_to_oci.sh --from-beginning`. The script will read `.env.local` or `local.settings.json` and confirm it can put messages to OCI.
- Need help populating `.env.local`? Run `./scripts/setup_eventhub_to_oci.sh` to auto-discover existing Event Hubs and OCI streams when there is a single clear match, resolve the connection string, and prompt for OCI settings; it writes `.env.local` (git-ignored).

Deploy to Azure using Azure CLI / Functions Core Tools:
1) Variables
RG="<resource-group>"
LOC="westeurope"
SA="<unique_storage_account_name>"
APP="<function_app_name>"

2) Resource group + storage + function app (Linux, Python 3.11, Functions v4)
az group create -n "$RG" -l "$LOC"
az storage account create -g "$RG" -n "$SA" -l "$LOC" --sku Standard_LRS
az functionapp create -g "$RG" -n "$APP" --consumption-plan-location "$LOC" --runtime python --runtime-version 3.11 --functions-version 4 --os-type linux --storage-account "$SA"

3) App settings
# Event Hubs + consumer group
az functionapp config appsettings set -g "$RG" -n "$APP" --settings \
  EventHubsConnectionString="Endpoint=sb://<ns>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=..." \
  EventHubConsumerGroup='$Default' \
  EventHubName="insights-activity-logs" \
  EventHubNamesCsv="insights-activity-logs,another-hub"

# OCI target
az functionapp config appsettings set -g "$RG" -n "$APP" --settings \
  MessageEndpoint="https://cell-1.streaming.<region>.oci.oraclecloud.com" \
  StreamOcid="ocid1.stream.oc1..xxxx"

# OCI credentials (consider storing in Key Vault and referencing)
az functionapp config appsettings set -g "$RG" -n "$APP" --settings \
  user="ocid1.user.oc1..xxxx" \
  key_content="-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----" \
  pass_phrase="" \
  fingerprint="<fingerprint>" \
  tenancy="ocid1.tenancy.oc1..xxxx" \
  region="<oci-region>"

# Optional tuning
az functionapp config appsettings set -g "$RG" -n "$APP" --settings \
  MaxBatchSize="100" MaxBatchBytes="1048576"
# (InactivityTimeout is ignored for the Event Hub trigger)

4) Publish the function with remote build
cd function/EventHubsNamespaceToOCIStreaming
func azure functionapp publish "$APP" --python --build remote --force
cd - 1>/dev/null

Fallback if Functions Core Tools is unavailable:
cd function/EventHubsNamespaceToOCIStreaming
# Remove host-specific dependencies before packaging for Azure Linux
rm -rf .python_packages
zip -r ../../function-deploy.zip .
cd - 1>/dev/null
az functionapp deployment source config-zip -g "$RG" -n "$APP" --src "function-deploy.zip"

5) Validate logs and execution
az webapp log tail -g "$RG" -n "$APP"
# or use Functions Core Tools
# func azure functionapp logstream "$APP" --resource-group "$RG"
# Look for "Config summary" and per-hub "summary: sent=..." lines confirming messages are forwarded.
- Note: logstream is not supported on Linux Consumption. Use a premium plan (EP1) via provision_azure_to_oci.sh or open Application Insights Live Metrics in the portal.
- If you see a warning about Stream Pool OCIDs, update StreamOcid to the Stream OCID (ocid1.stream...) instead of the Stream Pool (ocid1.streampool...).
- If you set the consumer group from a shell command, use `EventHubConsumerGroup='$Default'` so the shell preserves the literal value.

Operational notes:
- The Event Hub trigger reads continuously from the configured `EventHubName` and consumer group. Use the drain script for one-time backfill (`--from-beginning` or `--start-iso`).
- For checkpointing across runs, integrate Azure Blob checkpoint store (not included by default). Current design updates partition checkpoints in-session only.
- Use a dedicated consumer group to avoid interference with other consumers.
- Ensure the Function App has outbound access to OCI endpoints (consider firewall/vnet rules).
- Secure key_content via Azure Key Vault references in app settings for production.
- Helper script update: scripts/drain_eventhub_to_oci.sh now reads MessageEndpoint / StreamOcid from local.settings.json if OCI_MESSAGE_ENDPOINT / OCI_STREAM_OCID are not exported, preventing the “OCI_MESSAGE_ENDPOINT and/or OCI_STREAM_OCID not set” error during local validation.

Packaging options (zip for portal or CI/CD)
- Local zip: build the package on Linux, or skip local dependency packaging and use a remote build. Do not upload a macOS/Windows-built `.python_packages` directory to an Azure Linux Function App.
  (cd function/EventHubsNamespaceToOCIStreaming && rm -rf .python_packages && zip -qry ../../azurelogs2oci-function.zip .)
  Upload azurelogs2oci-function.zip to a storage container with a SAS URL and paste that URL into the portal template packageUri field.
- GitHub Actions: trigger .github/workflows/deploy-azure-function.yml (workflow_dispatch). It builds the zip, uploads it as an artifact, and can deploy directly when AZURE_FUNCTIONAPP_PUBLISH_PROFILE is provided as a secret.

Cleanup guidance (repo):
- You can retain this function folder as the authoritative Event Hub trigger → OCI implementation.
- Candidate items to archive/remove if no longer needed: earlier experimental connectors or duplicate templates. Consider moving older folders into an archive/ directory for traceability.
