# Project Review & End-to-End Test: 2026-06-16

## Project: OCIPrometheusMonitoring
- **Status:** Active — validated end-to-end on real OCI infrastructure.

## End-to-End Test (2026-06-16, OCI eu-frankfurt-1)

Provisioned a full topology and ran the **actual project scripts**:

| Role | OS | Exporter | Result |
|------|----|----------|--------|
| Target | Ubuntu 22.04 | `node_exporter` 1.11.1 (via `install-node-exporter.sh`) | ✅ active, scraped |
| Target | Oracle Linux 9 | `node_exporter` 1.11.1 (via `install-node-exporter.sh`) | ✅ active, scraped |
| Proxy | Windows Server 2022 | `windows_exporter` 0.31.7 + Prometheus 3.12.0 + OCI Management Agent | ✅ all services Running, agent **ACTIVE** |

**Validated pipeline:** `node_exporter (Ubuntu+OEL) → Prometheus (Windows proxy, /federate) → OCI Management Agent → OCI Monitoring`. OCI Monitoring (`summarize-metrics-data`, namespace `promtest_prometheus`) returned `node_*` series for **both** Linux hosts with `instance`/`job` dimensions. 105+ distinct node metrics landed.

## Bugs found & fixed in this repo

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | HIGH | `Install-OCIAgent` passed `installer.bat Correlation.rspFile="…"`; the real Management Agent `installer.bat` takes the response file **positionally** (`installer.bat <input.rsp>`) → agent never installs. | Positional arg. |
| 2 | HIGH | `Ensure-Java8` installed Corretto but never set **`JAVA_HOME`** → agent `configure` aborts with *"JAVA_HOME … is not SET"*. | Resolve + set `JAVA_HOME` (Machine + process). |
| 3 | HIGH | NSSM downloaded from `nssm.cc` (returned **503** in 3 of 3 hits across runs) with no error handling → `Download-File` continued and Prometheus service silently never installed; even with retry, `nssm.cc` is a single point of failure. | `Download-File` now retries + validates + fail-fasts; `Install-NSSM` tries **multiple sources** (`nssm.cc` → durable Internet Archive mirror of the same file) and supports a **bundled** `vendor\nssm\win64\nssm.exe` for offline installs. |
| 4 | HIGH | `windows_exporter` collector list included **`cs`**, removed in ≥0.31 → service exits with `unknown collector cs`. | Collector list now `cpu,cpu_info,logical_disk,net,os,service,system,textfile,memory,tcp,udp`. |
| 5 | HIGH | **Data source design**: README told users to scrape `http://localhost:9090/metrics`, which only exposes Prometheus' *own* telemetry — the exporter series require **`/federate`**. | README + final message now document `/federate?match[]={job=~".+"}` + the `create-prometheus-datasource` CLI. |
| 6 | HIGH | `install-node-exporter.sh` / `install-gcp-exporter.sh` never opened the **host firewall**; OCI Linux images block 9100/9255 (firewalld on OEL, default iptables REJECT on Ubuntu) → Prometheus scrapes time out. | Both scripts now open the port (firewalld/ufw/iptables). |
| 7 | HIGH (earlier) | PowerShell 7-only `? :` ternary broke on Windows PowerShell 5.1 (Win8.1/Server2012). | `if/else` + `switch`. |
| 8 | MED | Final `Read-Host "Press Enter to exit"` blocked unattended/cloud-init runs. | Guarded by `[Environment]::UserInteractive`. |
| 9 | MED | Proxy mode hardcoded exporter port 9182, ignoring `$Config.ExporterPort`. | Honors config. |
| 10 | MED | Proxy's own `windows_exporter` was installed but never scraped by Prometheus. | Added `windows_proxy` scrape job (`localhost:9182`). |
| 11 | MED | `config.json` `WindowsExporterVersion`/`PrometheusVersion` fields are never read (script uses `$Default*` constants). | Documented (left as-is to avoid behavior change). |
| 12 | LOW | Component versions stale (Feb→Jun 2026). | Bumped: Prometheus 3.12.0, node_exporter 1.11.1, windows_exporter 0.31.7, stackdriver_exporter 0.19.0. |
| 13 | HIGH | `Install-WindowsExporter` ran `msiexec` without checking the exit code. At first boot the OS / Oracle Cloud Agent run their own MSIs, so the exporter MSI can fail with **1618 (another install in progress)** and the script silently continued → no `windows_exporter` service. (Reproduced on a clean run; the prior run was timing-lucky.) | New `Invoke-Msi` helper retries on 1618 (waits for the installer mutex), validates exit code, and the install now verifies + starts the service. Applied to the Java MSI too. |

## New component: OpenTelemetry export (2026-06-17)

Added an optional **second export path** so the same metrics can be sent to a
user's OTEL collector / Prometheus / Grafana / 3rd-party tool, alongside OCI Monitoring:

- `Install-OTELCollector` (Windows proxy) and `install-otel-collector.sh` (Linux):
  install the OpenTelemetry Collector (contrib `0.154.0`), which uses a `prometheus`
  receiver scraping the local `/federate` endpoint and exports via **OTLP/HTTP**
  and/or **Prometheus `remote_write`**.
- New `config.json` keys: `OtelEnabled`, `OtelOtlpEndpoint`, `OtelPromRemoteWriteEndpoint`.
- `otel-destination/` — a ready-to-run **OTEL → Prometheus → Grafana** Docker stack
  that stands in for the user's tooling (and is used as the e2e test sink).

Architecture:
```
exporters → Prometheus (proxy) ─┬─ OCI Mgmt Agent /federate → OCI Monitoring
                                └─ OTEL Collector /federate → OTLP / remote_write → user's OTEL/Prometheus/Grafana
```

## Data source lifecycle helper (2026-06-17)

`manage-oci-datasource.sh` manages the OCI Management Agent Prometheus data source from
any OCI-CLI host (the Windows proxy has no OCI CLI):
- `list` — show existing data sources on the agent.
- `create` — **idempotent**: checks existing data sources first and skips if the name
  already exists (no duplicates), otherwise creates the `/federate` data source.
- `destroy` — deletes the data source(s) (all, or a single `--name`) via `delete-data-source`.

## Operational notes (for users)

- The Windows Management Agent zip is **not** an anonymous download; fetch it with an authenticated `oci os object get … agent_images …` (object URL/namespace from `oci management-agent agent-image list`). README documents this.
- The agent's `CredentialWalletPassword` (in `input.rsp`) must be **≥16 chars with upper+lower+digit+special**, or `configure` fails the FIPS complexity check.
- OCI **run-command on Windows runs as `nt service\ocarun` (non-admin)** — it can read logs/query services but cannot install services or set machine env vars; use cloud-init (SYSTEM) or RDP for privileged steps.

## Cross-cloud validation (GCP + Azure + AWS) — 2026-06-18

Provisioned a real Ubuntu 22.04 VM in **each** of GCP, Azure, and AWS, and ran the
**actual project scripts** to prove a non-OCI instance can feed both targets at once:
`node_exporter → Prometheus /federate → [OCI Management Agent → OCI Monitoring] AND
[OTEL Collector → Grafana/Prometheus sink]`.

| Cloud (CLI, region) | Exec path | OCI Monitoring namespace | OCI Monitoring result | 3rd-party sink (OTEL) |
|---|---|---|---|---|
| **GCP** (`gcloud`, europe-west1) | SSH | `prometheus_gcp` | ✅ 25+ `node_*`; `node_load1=0.09`, `MemAvailable≈7.27 GB` | ✅ 255 `node_*`, `otel_scope_name=…/prometheusreceiver` (Grafana screenshot in README) |
| **Azure** (`az`, westeurope) | `az vm run-command` (SSH blocked) | `prometheus_azure` | ✅ 451 `node_*`; `node_load1=0.33` | ✅ 247 `node_*`, otel receiver label |
| **AWS** (`aws`, eu-central-1) | `aws ssm send-command` (SSH flaky) | `prometheus_aws` | ✅ 266 `node_*`; `node_load1=0.27` | ✅ `node_load1` via OTEL in sink |

All three used the **same** cloud-agnostic scripts (`install-node-exporter.sh`,
`install-oci-agent-linux.sh`, `install-otel-collector.sh`, `manage-oci-datasource.sh`);
only the VM provisioning differs per cloud. The agent registers to OCI over outbound
443, so the agent ZIP was delivered to the VMs via an OCI pre-authenticated request.

Issues found & fixed: **KB-24** (Linux agent requires JDK 8 + `JAVA_HOME`),
**KB-25** (`manage-oci-datasource.sh` crashed on an agent with zero data sources),
**KB-27** (first-boot apt lock — now waited/retried), **KB-28** (no-SSH → use the
cloud control plane). **Every** GCP, Azure, AWS, and OCI test resource (VMs, networks,
IAM roles/SG, agents, install key, dynamic group, policy, data sources, temp bucket)
was **destroyed** afterward; OCI Monitoring namespace data auto-expires (~93 days).

## Reference
- OCI CLI / Ansible install reference added to the `oci-observability-dbm-opsi` skill: `references/management-agent-prometheus.md`.
- Linux Management Agent bootstrap reference: oracle-devrel `observability-and-management/management-agent`.
