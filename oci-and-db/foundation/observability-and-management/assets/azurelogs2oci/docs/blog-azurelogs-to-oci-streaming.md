# Ship Azure logs to OCI Streaming (Event Hub trigger, Azure portal + OCI console)

Azure Event Hubs is a convenient landing zone for platform and Entra ID logs. When you also need those logs in Oracle Cloud Infrastructure (OCI) Streaming, you can bridge the two clouds with a tiny Python Azure Function. This guide is ready for blog publication and includes screenshot placeholders for both the Azure portal and the OCI console.

## Architecture at a glance
- Azure Function with an Event Hub trigger (per-hub binding) sends to OCI Streaming via PutMessages.
- Base64 encoding and 1MB/count-aware batching to respect OCI limits.
- Uses OCI API signing keys (user OCID, private key, fingerprint, tenancy, region).
- Works on Linux Consumption/Premium; deployment via custom ARM template or zip deploy.
- Backfill/drain scripts are included for one-time migrations.
- [Screenshot: Architecture diagram - Event Hub → Function → OCI Streaming]

## Prerequisites
- Azure: Event Hubs namespace with the hub carrying your logs, Azure subscription, Azure CLI.
- OCI: Streaming stream in your tenancy, user API signing keys (fingerprint must match the private key you deploy).
- Tools: zip (or 7z), Functions Core Tools (optional for local runs), GitHub Actions secret `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` if using the workflow.
- Security: keep `key_content` to the key block only (no trailing comments), prefer Key Vault references for production.
- [Screenshot: Azure Portal - Event Hubs namespace overview]
- [Screenshot: OCI Console - Streaming service landing page]

## Step 0: Prepare OCI Streaming
1) Create (or identify) the target stream in OCI.  
   - [Screenshot: OCI Console - Create Stream form]  
2) Create/confirm the API key on the OCI user and capture:
   - user OCID, tenancy OCID, region, fingerprint, and the private key PEM (single-line is okay; the function rewraps it).
   - [Screenshot: OCI Console - User API keys tab with fingerprint highlighted]  
3) Record the Stream OCID and the message endpoint (https://cell-1.streaming.<region>.oci.oraclecloud.com).  
   - [Screenshot: OCI Console - Stream details page showing OCID + endpoint]

## Step 1: Prepare Azure Event Hub
1) List hubs in the namespace and pick the hub for the trigger:  
   ```bash
   az eventhubs eventhub list -g <rg> --namespace-name <namespace> --query "[].name" -o tsv
   ```  
2) Choose a dedicated consumer group (e.g., `$Default` or `oci-bridge`).  
3) Keep the namespace-level connection string (RootManageSharedAccessKey with Listen).  
4) [Screenshot: Azure Portal - Event Hub overview showing consumer groups]

## Step 2: Package the function (or grab the workflow artifact)
Local option:
```bash
python3 -m pip install -r function/EventHubsNamespaceToOCIStreaming/requirements.txt \
  --target function/EventHubsNamespaceToOCIStreaming/.python_packages/lib/site-packages
(cd function/EventHubsNamespaceToOCIStreaming && zip -qry ../../azurelogs2oci-function.zip .)
# Upload azurelogs2oci-function.zip to blob storage with a SAS URL
```
GitHub Actions option:
- Trigger `.github/workflows/deploy-azure-function.yml` with `function_app_name` set.
- Secret required: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` (download from Function App blade).
- The workflow builds the zip, deploys, and publishes the artifact for reuse.
- [Screenshot: GitHub Actions run showing build + deploy]

## Step 3: Deploy from the Azure portal (custom template)
1) Portal: **Create a resource** → **Template deployment (deploy using custom templates)**.  
   - [Screenshot: Azure Portal - Template deployment blade]  
2) Upload `deploy/azuredeploy.json`.  
3) Fill parameters (matches the form fields):
   - Function App name/region, EventHubsConnectionString, EventHubConsumerGroup, EventHubName.
   - OCI credentials: user, key_content, pass_phrase (optional), fingerprint (matching the key), tenancy, region.
   - Target stream: MessageEndpoint, StreamOcid.
   - Optional: MaxBatchSize, MaxBatchBytes (InactivityTimeout is ignored for the Event Hub trigger).
   - packageUri: HTTPS URL to your zip (SAS or GitHub artifact).
   - [Screenshot: Azure Portal - Template parameters filled in]  
4) Review + create. The template provisions storage, plan, Function App, app settings, and sets WEBSITE_RUN_FROM_PACKAGE to your zip.  
   - [Screenshot: Azure Portal - Deployment succeeded]

## Step 4: Validate end-to-end
- Tail logs (choose one):
  ```bash
  az webapp log tail -g <rg> -n <app>
  func azure functionapp logstream <app> --resource-group <rg>   # Core Tools
  ```
  Look for "Config summary", partition start/close, batch flush counts, and OCI send status.  
  - [Screenshot: Azure Function log stream showing batches sent]  
- Confirm ingestion in OCI:
  - Check the stream metrics and partition offsets.  
  - [Screenshot: OCI Console - Stream metrics/partitions showing new messages]  
- If you see a warning about Stream Pool OCIDs, update to a Stream OCID (ocid1.stream...).
- For Linux Consumption, logstream in CLI may be unavailable; use EP1 or Application Insights Live Metrics.

## Step 5: Backfill and local validation (optional)
- Generate a local `.env.local` interactively: `./scripts/setup_eventhub_to_oci.sh` (discovers hubs, resolves connection string).
- Drain/backfill locally: `./scripts/drain_eventhub_to_oci.sh --from-beginning` (uses EventHubName/consumer group and writes to OCI).  
- Quick credential check: `python scripts/test_oci_simple.py` (prefers `.env.local`, falls back to legacy `.env`).
- [Screenshot: Terminal output from drain script showing sent counts]  

## Operational tips
- Use a dedicated consumer group so other consumers remain unaffected.
- Ensure `fingerprint` matches the deployed private key and that `key_content` ends at `-----END PRIVATE KEY-----` with no trailing text.
- Use the OCI *stream* OCID (not the stream pool OCID).
- Keep outbound access from the Function App to `cell-*.streaming.<region>.oci.oraclecloud.com`.
- For persistent checkpoints beyond the binding defaults, integrate Azure Blob checkpointing.

With this setup, Azure logs flow continuously from Event Hubs to OCI Streaming with a small, auditable code surface and repeatable deployment steps. Replace the placeholders with real screenshots and publish.
