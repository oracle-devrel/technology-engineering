# Production environment handoff

Cloud Operations publishes OCI references automatically. Azure uses an existing foundation, resource inputs in the request/JSON and a configured runner; its section below is optional documentation, not a prerequisite handoff PR. Subscription and authentication stay on the runner. Google Cloud still requires its reviewed foundation references before a request. Never record secret values here.

## Azure

| Reference | Value |
|---|---|
| Subscription ID | |
| Resource group | |
| Region | |
| ADB connectivity (private or public mTLS) | |
| VM Subnet ID | |
| ADB Subnet ID | |
| NSG ID | |
| VNet ID | |

Private Azure ADB needs the VNet and delegated ADB subnet. Public mTLS ADB needs neither; it accepts connections from any IP with a client wallet and database authentication. Record the approved choice before the first request.

## Google Cloud

| Reference | Value |
|---|---|
| Project ID | |
| Zone | |
| Subnetwork | |
| Service account | |
| ODB Network ID | |
| ODB Subnet ID | |
| Password secret | |
