# azurelogs2oci

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green)

Stream Azure Event Hub logs (e.g., Entra ID audit logs) end-to-end into Oracle Cloud Infrastructure Log Analytics — with a custom parser, multicloud tagging, and one-click OCI deployment.
This is a personal project, to proove the product capabilities, not an Oracle Product. 

## Overview

This project implements an end-to-end log-shipping pipeline that extracts telemetry from **Azure Event Hubs** (Entra ID audit logs) and ingests it into **OCI Log Analytics** through **OCI Streaming** and **Service Connector Hub**, with a custom parser that maps all Azure EntraID audit structured fields.

```
Azure Event Hub (EntraID Audit Logs)
  → Azure Function (Event Hub trigger + Cloud Provider enrichment)
  → OCI Streaming (Kafka-compatible)
  → Service Connector Hub
  → Log Analytics (Azure Logs source, Azure EntraID Audit parser, 26 field mappings)
```

## Repository Layout

```
├── function/EventHubsNamespaceToOCIStreaming/
│   ├── eventhub_to_oci/__init__.py    # Function logic (trigger + OCI sender + enrichment)
│   ├── eventhub_to_oci/function.json  # Event Hub trigger binding (real-time)
│   ├── requirements.txt               # azure-functions, azure-eventhub, oci
│   ├── host.json                      # Function host configuration
│   ├── README.md                      # Details and operational notes
│   └── QUICKSTART.md                  # Step-by-step deployment guide
├── scripts/
│   ├── lib/common.sh                  # Shared helpers (logging, prompts, env management)
│   ├── discover_resources.sh          # Azure + OCI backend resource discovery
│   ├── provision_azure_to_oci.sh      # End-to-end provisioning (Azure + OCI + Log Analytics)
│   ├── setup_oci_log_analytics.sh     # OCI Log Analytics setup (stream, log group, parser, source, SCH)
│   ├── setup_eventhub_to_oci.sh       # Interactive helper to collect settings and write .env.local
│   ├── drain_eventhub_to_oci.sh       # Ad-hoc drain from Event Hub to OCI
│   ├── teardown_azurelogs2oci.sh      # Destroy Azure + OCI resources (reverse of setup)
│   ├── teardown_oci_log_analytics.py  # Delete LA custom content (source, parser, fields)
│   └── eventhub_consumer.py           # Consumer helper used by the drain script
├── stack/                             # OCI Resource Manager Stack (Terraform)
│   ├── main.tf                        # Provider, data sources, resource blocks
│   ├── variables.tf                   # Input variables
│   ├── outputs.tf                     # Output values (OCIDs, endpoints)
│   ├── iam.tf                         # IAM policies for Service Connector Hub
│   ├── schema.yaml                    # OCI Console UI form definition
│   └── scripts/
│       └── setup_log_analytics.py     # Custom fields, parser, source (post-deploy)
├── deploy/
│   └── azuredeploy.json               # Azure portal template (custom deployment)
├── docs/
│   ├── EVENT_FORMAT_DOCUMENTATION.md  # Notes on expected event formats and metadata
│   └── blog-azurelogs-to-oci-streaming.md  # Blog-ready walkthrough
├── .env.example                       # Configuration template (copy to .env.local)
└── LICENSE.txt                        # UPL v1.0
```

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Azure CLI (`az`) | Latest | Azure resource provisioning |
| Python | 3.11+ | Azure Function runtime, OCI field/parser creation |
| `oci` CLI | Latest | OCI resource provisioning |
| OCI Python SDK | >= 2.124.0 | Log Analytics parser/field creation |
| `zip` or `7z` | Any | Packaging the function for deployment |
| Terraform | >= 1.2.0 (Optional) | OCI Resource Manager Stack deployment |

**Azure requirements:**
- Event Hubs namespace with one or more hubs (e.g., Entra ID audit logs diagnostic setting)
- Azure subscription with permission to create Function App + Storage
- Authenticated via `az login` before running provisioning scripts

**OCI requirements:**
- Tenancy with Streaming and Log Analytics services enabled
- **Log Analytics must be onboarded** in your tenancy (one-time: OCI Console > Observability & Management > Log Analytics > click "Start Using Log Analytics"). If not onboarded, namespace auto-detection will fail.
- API signing key configured (`~/.oci/config` or `OCI_KEY_FILE` / `OCI_KEY_CONTENT`)
- IAM policies: user must manage streams, log-analytics, and service-connectors in the target compartment
- OCI Python SDK installed (`pip install oci`) — required by the parser/field creation scripts

## Quick Start

```bash
# 1. Prerequisites
az login                        # authenticate Azure CLI
pip install oci                 # OCI Python SDK (for Log Analytics setup)

# 2. Configure
cp .env.example .env.local      # keep real values only in .env.local (gitignored)

# 3. Option A: End-to-end provisioning (Azure + OCI + Log Analytics)
./scripts/provision_azure_to_oci.sh

# 3. Option B: Step-by-step
#    a. Set up Azure/OCI settings interactively
#       Auto-discovers existing hubs/streams when there is a single clear match
./scripts/setup_eventhub_to_oci.sh
#    b. Set up OCI Log Analytics (stream, log group, parser, source, SCH)
./scripts/setup_oci_log_analytics.sh

# 4. Test end-to-end
./scripts/drain_eventhub_to_oci.sh --from-beginning

# 5. Verify in OCI Log Analytics Log Explorer
#    Query: 'Cloud Provider' = 'Azure' | stats count by 'Azure Operation'
```

## Teardown / Cleanup

Remove all provisioned Azure and OCI resources when you're done testing or want a fresh start.

```bash
# Delete all Azure + OCI resources
./scripts/teardown_azurelogs2oci.sh

# OCI only
./scripts/teardown_azurelogs2oci.sh --oci-only

# Azure only
./scripts/teardown_azurelogs2oci.sh --azure-only

# Preview without deleting
./scripts/teardown_azurelogs2oci.sh --dry-run

# Keep resource group but delete contained Azure resources
./scripts/teardown_azurelogs2oci.sh --azure-only --keep-rg

# Keep Log Analytics fields (shared with other pipelines like gcplogs2oci)
./scripts/teardown_azurelogs2oci.sh --oci-only --keep-fields
```

The teardown script sources `.env.local` (and falls back to legacy `.env`) to discover resource IDs and names automatically. It deletes resources in reverse dependency order (SCH first, then Stream Pool last) and handles already-deleted resources gracefully.

The setup scripts (`setup_oci_log_analytics.sh`, `provision_azure_to_oci.sh`) also offer a built-in **destroy & recreate** option: run the setup script and choose option `[3]` from the discovery menu to tear down existing resources inline before creating new ones.

## OCI Resource Manager (Terraform) Deployment

Deploy the OCI infrastructure directly from the OCI Console with the Resource Manager Stack:

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/adibirzu/azurelogs2oci/releases/latest/download/azurelogs2oci-stack.zip)

### Manual Stack Deployment

1. **Package the stack:**
   ```bash
   cd stack && zip -r ../azurelogs2oci-stack.zip . && cd ..
   ```

2. **Upload to OCI Resource Manager:**
   - Navigate to **OCI Console > Developer Services > Resource Manager > Stacks**
   - Click **Create Stack** > Upload `.zip` file
   - Fill in the form (compartment, stream names, etc.)
   - Click **Plan** then **Apply**

3. **Create Log Analytics custom content** (parser, fields, source):
   ```bash
   pip install oci                # OCI Python SDK (if not already installed)
   export LA_NAMESPACE="<your-namespace>"
   export OCI_COMPARTMENT_ID="<your-compartment-ocid>"
   python3 stack/scripts/setup_log_analytics.py
   ```
   The script auto-detects auth from OCI Resource Principal, `~/.oci/config`, or environment variables. Source creation also requires the `oci` CLI.

4. **Or apply locally with Terraform:**
   ```bash
   cd stack
   terraform init
   terraform plan -var="compartment_ocid=ocid1.compartment..." \
                  -var="region=us-ashburn-1" \
                  -var="tenancy_ocid=ocid1.tenancy..."
   terraform apply
   ```

The stack creates: Stream Pool, Stream, Log Analytics Log Group, Service Connector Hub, and IAM policies. The Python helper script handles Log Analytics custom content (38 fields, 2 JSON parsers, source) which has no Terraform provider support.

## Azure Logs Source & Parsers

The `setup_oci_log_analytics.sh` script (or `stack/scripts/setup_log_analytics.py` for Terraform deployments) creates a custom **Azure Logs** source with **two JSON parsers** in OCI Log Analytics, covering all Azure log types forwarded via Event Hub.

The Azure Function injects `cloudProvider: "Azure"` into every log entry for multicloud dashboard filtering.

### Parser 1: Azure EntraID Audit (26 field mappings)

Handles **Unified Audit Log** format from EntraID and Office 365 diagnostic settings.

**Built-in** (4): Message, Severity, Time, Method

**Multicloud** (1): Cloud Provider (`$.cloudProvider`)

**Core EntraID Audit** (15): Time Generated, Event ID, Operation, Record Type, Result Status, User Type, User ID, User Key, Workload, Object ID, Client IP, Organization ID, Schema Version, Creation Time, AD Event Type

**Actor / Target Context** (6): Actor Context ID, Actor IP Address, Inter Systems ID, Intra System ID, Target Context ID, Application ID

### Parser 2: Azure Diagnostic Log (21 field mappings)

Handles **Azure Monitor common schema** for Activity Logs, Resource Logs, and all Azure services streaming via Event Hub diagnostic settings (Network Watcher, Storage, Functions, VMs, Event Hubs, SQL, Key Vault, App Service, etc.).

**Built-in** (4): Message, Severity, Time, Method

**Multicloud** (1): Cloud Provider (`$.cloudProvider`)

**Azure Monitor Common** (16): Resource ID, Resource Group, Resource Type, Resource Provider, Subscription ID, Correlation ID, Caller, Level, Tenant ID, Location, Category, Duration Ms, Result Type, Result Signature, Result Description, Caller IP

### Example Queries

```
'Cloud Provider' = 'Azure' | stats count by 'Azure Operation'
```

```
'Azure Category' = 'Administrative' | stats count by 'Azure Caller'
```

For multicloud environments with both `gcplogs2oci` and `azurelogs2oci`, use:

```
'Cloud Provider' in ('Azure', 'GCP') | stats count by 'Cloud Provider', msg
```

## Getting Started (Detailed)

The fastest way to deploy is with the function-specific quickstart.

- Quickstart (Function): function/EventHubsNamespaceToOCIStreaming/QUICKSTART.md
- Details and operational notes: function/EventHubsNamespaceToOCIStreaming/README.md
- Azure portal template (custom deployment): deploy/azuredeploy.json
- GitHub Actions manual zip deploy: .github/workflows/deploy-azure-function.yml

High-level steps:
1) Create or identify the Azure Event Hubs namespace and the hub carrying your logs.
2) Create an OCI Streaming stream and prepare OCI API signing keys (fingerprint must match the private key you deploy).
3) Deploy the Function App (Linux, Python 3.11, Functions v4) and bind the Event Hub trigger (EventHubName).
4) Configure App Settings:
   - EventHubsConnectionString, EventHubConsumerGroup, EventHubName (for the trigger), EventHubNamesCsv (scripts only)
   - MessageEndpoint (or OCI_MESSAGE_ENDPOINT), StreamOcid (or OCI_STREAM_OCID)
   - OCI credentials: user, key_content, pass_phrase (optional), fingerprint (matching the private key), tenancy, region
5) Publish the function and monitor logs.
- The provision script auto-resolves the namespace connection string (RootManageSharedAccessKey), auto-discovers existing Azure/OCI resources when there is a single clear match, rejects Stream Pool OCIDs, writes `.env.local`, and prefers `func azure functionapp publish --python --build remote --force` for Linux-safe deployment.

### Local Smoke Test

- Copy `.env.example` to `.env.local` (kept out of git) and fill Event Hubs connection + OCI settings. Use the OCI *stream* OCID (not the stream pool OCID) in StreamOcid/OCI_STREAM_OCID; or run `./scripts/setup_eventhub_to_oci.sh` to auto-discover existing Event Hubs and OCI streams and build `.env.local` interactively.
- Run `./scripts/drain_eventhub_to_oci.sh --from-beginning` to drain locally and verify messages reach OCI Streaming.
- For full provisioning + deployment from scratch, run `./scripts/provision_azure_to_oci.sh` (creates RG/storage/Function App, configures settings, publishes with remote build, and optionally sets up OCI Log Analytics).

### Tail Function Logs (CLI)

- `az webapp log tail -g <rg> -n <app>`
- or `func azure functionapp logstream <app> --resource-group <rg>` if you have Functions Core Tools
- Note: Azure CLI/Core Tools logstream is not supported on Linux Consumption. Use `--plan premium` during provisioning (EP1) or open Application Insights Live Metrics in the portal.
- Look for "Config summary" and "summary: sent=..." lines to confirm settings from provisioning are applied and messages are forwarded.
- If logs show a warning about StreamOcid pointing to a Stream Pool (ocid1.streampool...), switch the setting to the Stream OCID (ocid1.stream...).
- If you set the consumer group in a shell command, use `EventHubConsumerGroup='$Default'` so the shell does not expand `$Default` to an empty value.

### Linux Deployment Caveat

- Do not deploy a locally built `.python_packages` directory from macOS or Windows into an Azure Linux Function App. Native wheels from the wrong platform can prevent the host from indexing the function.
- Preferred deployment path: `cd function/EventHubsNamespaceToOCIStreaming && func azure functionapp publish <app> --python --build remote --force`
- GitHub Actions is safe here because the workflow builds on `ubuntu-latest`.

## Notes/Issues

- Trigger behavior: The Function uses an Event Hub trigger bound to `EventHubName` and reads continuously from the configured consumer group. Use the drain script for backfill (`--from-beginning` or `--start-iso`).
- Checkpointing: Default binding checkpoints within a session. For persistent cross-run checkpoints, integrate Azure Blob checkpoint store (not included by default).
- Consumer Group: Use a dedicated consumer group to avoid interfering with other consumers.
- Networking: Ensure outbound access from the Function App to OCI Streaming endpoints.

## URLs

- Azure Functions: https://learn.microsoft.com/azure/azure-functions/
- Azure Event Hubs: https://learn.microsoft.com/azure/event-hubs/
- OCI Streaming: https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm
- OCI Log Analytics: https://docs.oracle.com/en-us/iaas/logging-analytics/home.htm
- OCI Resource Manager: https://docs.oracle.com/en-us/iaas/Content/ResourceManager/home.htm

## Contributing

This project welcomes contributions from the community. Before submitting a pull
request, please [review our contribution guide](./CONTRIBUTING.md).

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE.txt) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK.
