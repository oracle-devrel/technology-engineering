# Knowledge Base — OCI Prometheus → OTEL Monitoring

Troubleshooting reference for this suite. Each entry: **Symptom → Root cause →
Resolution → Affected file**. Search by error message, component, or service name.
The fixes below were found while validating the project end-to-end on real OCI
infrastructure (see [`PROJECT_REVIEW.md`](../PROJECT_REVIEW.md) for the test report).

> Use this when you hit an error. If your symptom isn't here, fix it and add an
> entry so the next person doesn't re-debug it.

---

## Index

- [Windows proxy: MSI / installer / services](#windows-proxy-msi--installer--services)
- [OCI Management Agent (Prometheus emitter)](#oci-management-agent-prometheus-emitter)
- [OCI data source & Monitoring](#oci-data-source--monitoring)
- [Linux targets & firewall](#linux-targets--firewall)
- [OpenTelemetry export path](#opentelemetry-export-path)
- [Discovery (discover-oci-instances.sh)](#discovery-discover-oci-instancessh)

---

## Windows proxy: MSI / installer / services

### KB-01 — `windows_exporter` service missing after a clean first boot (msiexec 1618)
- **Symptom:** Script reports success but `Get-Service windows_exporter` shows nothing; no metrics on `:9182`.
- **Root cause:** At first boot the OS / Oracle Cloud Agent run their own MSIs. The exporter MSI then fails with **1618 (another install in progress)**; the original code didn't check the exit code and continued.
- **Resolution:** `Invoke-Msi` retries on 1618 (waits for the Windows Installer mutex), validates the exit code, then verifies + starts the service. Applied to the Java MSI too.
- **File:** `Install-OCI-Prometheus.ps1` (`Invoke-Msi`, `Install-WindowsExporter`).

### KB-02 — `windows_exporter` exits immediately: `unknown collector cs`
- **Symptom:** Service installs but stops; event log shows `unknown collector cs`.
- **Root cause:** The `cs` collector was removed in windows_exporter ≥ 0.31 (its data moved to `cpu_info`/`memory`).
- **Resolution:** Collector list is now `cpu,cpu_info,logical_disk,net,os,service,system,textfile,memory,tcp,udp`.
- **File:** `Install-OCIPrometheus.ps1` (`Install-WindowsExporter`).

### KB-03 — NSSM download fails (HTTP 503) → Prometheus service never installed
- **Symptom:** Prometheus service absent; logs show a failed download from `nssm.cc`.
- **Root cause:** `nssm.cc` intermittently returns **503** and was a single point of failure; the downloader swallowed the error and continued.
- **Resolution:** `Download-File` now retries (3×), validates non-empty output, and fail-fasts. `Install-NSSM` tries multiple sources (`nssm.cc` → durable Internet Archive mirror) and supports a **bundled** `vendor\nssm\win64\nssm.exe` for fully offline installs.
- **File:** `Install-OCI-Prometheus.ps1` (`Download-File`, `Install-NSSM`), `vendor/nssm/`.

### KB-04 — Script aborts on Windows PowerShell 5.1 with a parser error
- **Symptom:** `The term '?' is not recognized` / parser error on Server 2012 R2 / Windows 8.1.
- **Root cause:** PowerShell-7-only ternary `? :` syntax doesn't parse on Windows PowerShell 5.1.
- **Resolution:** Replaced with `if/else` and `switch`.
- **File:** `Install-OCI-Prometheus.ps1`.

### KB-05 — Unattended/cloud-init run hangs at the end
- **Symptom:** cloud-init never completes; the script sits at `Press Enter to exit`.
- **Root cause:** `Read-Host` blocks when there's no interactive console.
- **Resolution:** The final pause is guarded by `[Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost'`.
- **File:** `Install-OCI-Prometheus.ps1` (MAIN).

### KB-06 — Legacy Windows: `windows_exporter` 0.31 won't run
- **Symptom:** Exporter fails to start on Windows 8.1 / Server 2012 R2.
- **Root cause:** windows_exporter 0.31.x requires Windows 10 / Server 2016 (build 10240)+.
- **Resolution:** `Get-WindowsExporterVersion` falls back to `0.25.1` on older OS.
- **File:** `Install-OCI-Prometheus.ps1` (`Get-WindowsExporterVersion`).

---

## OCI Management Agent (Prometheus emitter)

### KB-07 — Agent never installs: `installer.bat` ignores the response file
- **Symptom:** Agent install "runs" but no agent registers in OCI.
- **Root cause:** The Management Agent `installer.bat` takes the response file **positionally** (`installer.bat <input.rsp>`); the code passed `Correlation.rspFile="…"`, which it doesn't parse.
- **Resolution:** Pass the `.rsp` path positionally.
- **File:** `Install-OCI-Prometheus.ps1` (`Install-OCIAgent`).

### KB-08 — Agent `configure` aborts: *"JAVA_HOME … is not SET"*
- **Symptom:** Agent configure step fails complaining about JAVA_HOME despite Java being installed.
- **Root cause:** An MSI-installed JDK does not propagate `JAVA_HOME` to the current process.
- **Resolution:** `Ensure-Java8` resolves the Corretto path and sets `JAVA_HOME` at Machine + process scope before configuring.
- **File:** `Install-OCI-Prometheus.ps1` (`Ensure-Java8`).

### KB-09 — Agent `configure` fails the FIPS password complexity check
- **Symptom:** `configure` rejects the wallet password.
- **Root cause:** `CredentialWalletPassword` in `input.rsp` must be **≥16 chars with upper + lower + digit + special**.
- **Resolution:** Set a compliant wallet password in `input.rsp` before running.
- **File:** `input.rsp` (operator-provided), README "Management Agent prerequisites".

### KB-10 — Windows Management Agent zip "download" returns HTML / 401
- **Symptom:** `AgentZipPathOrUrl` download yields an error page, not a zip.
- **Root cause:** The agent image is **not** an anonymous object; it needs an authenticated fetch.
- **Resolution:** `oci os object get --namespace <ns> --bucket-name agent_images --name Windows-x86_64/latest/oracle.mgmt_agent.zip --file oracle.mgmt_agent.zip` (namespace from `oci management-agent agent-image list`).
- **File:** README "OCI Configuration".

### KB-11 — Privileged steps fail under OCI run-command on Windows
- **Symptom:** run-command can read logs/services but can't install services or set machine env vars.
- **Root cause:** OCI run-command on Windows runs as `nt service\ocarun` (**non-admin**).
- **Resolution:** Do privileged install steps via cloud-init (runs as SYSTEM) or RDP, not run-command.
- **File:** operational note.

---

## OCI data source & Monitoring

### KB-12 — OCI Monitoring shows only Prometheus' own telemetry, not node/windows metrics
- **Symptom:** The namespace has `prometheus_*` series but no `node_*` / `windows_*`.
- **Root cause:** The data source pointed at `/metrics` (Prometheus' own internals). Scraped exporter series live in the TSDB and are only re-exported via **`/federate`**.
- **Resolution:** Point the data source at `http://localhost:9090/federate?match[]={job=~".+"}` (percent-encoded in CLI).
- **File:** `README.md`, `Install-OCI-Prometheus.ps1` final summary, `manage-oci-datasource.sh` (`DEFAULT_URL`).

### KB-13 — Duplicate data sources created on re-runs
- **Symptom:** Each run adds another identical Prometheus data source on the agent.
- **Root cause:** `create` didn't check for an existing source.
- **Resolution:** `manage-oci-datasource.sh create` is **idempotent** — it lists existing sources and skips if the name exists. Use `destroy` then `create` to recreate.
- **File:** `manage-oci-datasource.sh`.

### KB-14 — No metrics in OCI Monitoring even though the agent is ACTIVE
- **Symptom:** Agent is healthy but `summarize-metrics-data` returns nothing.
- **Root cause (checklist):** missing IAM (`USE METRICS` for the agent dynamic group); wrong namespace queried; the data source URL hits `/metrics` not `/federate` (see KB-12); the proxy can't reach the targets (see KB-15).
- **Resolution:** Verify the dynamic-group + policy (README "Management Agent prerequisites"), confirm the namespace, then `oci monitoring metric-data summarize-metrics-data` for a `node_*` query.
- **File:** `README.md`.

---

## Linux targets & firewall

### KB-15 — Prometheus scrape of a Linux target times out (exporter is "up" locally)
- **Symptom:** `curl localhost:9100/metrics` works on the node, but Prometheus shows the target DOWN / context deadline exceeded.
- **Root cause:** OCI Linux images ship a **host firewall** (firewalld on Oracle Linux/RHEL, default iptables REJECT on Ubuntu). The OCI security list allowing the port is not enough.
- **Resolution:** `install-node-exporter.sh` / `install-gcp-exporter.sh` now open the port (firewalld → ufw → iptables, whichever is active). Also confirm the **VCN security list / NSG** allows the port from the proxy.
- **File:** `install-node-exporter.sh`, `install-gcp-exporter.sh` (`open_firewall_port`).

### KB-16 — GCP `stackdriver_exporter`: 429 / rate-limit or high cost
- **Symptom:** GCP exporter logs rate-limit errors or the GCP Monitoring bill rises.
- **Root cause:** Pulling all metric types from the GCP Monitoring API.
- **Resolution:** Pass specific `--monitoring.metrics-type-prefixes` (e.g. `compute.googleapis.com/instance/cpu`). Service account needs `roles/monitoring.viewer`.
- **File:** `install-gcp-exporter.sh`, `Install-OCI-Prometheus.ps1` (`Install-GCPExporter`).

---

## OpenTelemetry export path

### KB-17 — OTEL enabled but the collector won't start: no exporter configured
- **Symptom:** `Install-OTELCollector` throws *"OTEL enabled but no OtlpEndpoint or OtelPromRemoteWriteEndpoint configured"*.
- **Root cause:** `OtelEnabled=true` with both endpoints empty.
- **Resolution:** Set at least one of `OtelOtlpEndpoint` or `OtelPromRemoteWriteEndpoint` in `config.json`.
- **File:** `Install-OCI-Prometheus.ps1` (`Install-OTELCollector`), `install-otel-collector.sh`.

### KB-18 — Proxy aggregates metrics but nothing reaches any backend
- **Symptom:** `/federate` returns series on the proxy, but neither OCI Monitoring nor your OTEL sink receives them.
- **Root cause:** Both export paths are disabled (`OciMonitoringEnabled=false` **and** `OtelEnabled=false`).
- **Resolution:** The script now logs a WARN in this case. Enable at least one export path.
- **File:** `Install-OCI-Prometheus.ps1` (MAIN, proxy branch).

### KB-19 — Can't confirm metrics actually traversed the OTEL Collector
- **Symptom:** Series show up in the destination Prometheus, but you want proof they went through OTEL (not directly).
- **Root cause:** The Prometheus receiver tags series with `otel_scope_name`.
- **Resolution:** In the destination, query a series (e.g. `node_load1`) and confirm the **`otel_scope_name="…/prometheusreceiver"`** label. The `otel-destination/` stack visualizes this.
- **File:** `otel-destination/`, `README.md` validation section.

### KB-20 — Destination Grafana password / wide-open test stack
- **Symptom:** The test stack runs anonymous-admin Grafana with `admin/admin`.
- **Root cause:** It's a **test sink**, intentionally open for convenience.
- **Resolution:** Override `GF_SECURITY_ADMIN_PASSWORD` (now env-driven: `GF_SECURITY_ADMIN_PASSWORD=… docker compose up -d`). Never expose this stack publicly; add TLS/auth for any real use.
- **File:** `otel-destination/docker-compose.yml`, `otel-destination/README.md`.

---

## Discovery (discover-oci-instances.sh)

### KB-21 — Discovery returns no instances / `NotAuthorizedOrNotFound`
- **Symptom:** `discover-oci-instances.sh` prints "No RUNNING instances…" or an auth error.
- **Root cause:** Missing read IAM, wrong compartment/region, or the principal can't see the subtree.
- **Resolution:** Grant (per scanned compartment): `inspect instances`, `read instance-images` (OS detection), `read virtual-network-family` (VNIC private IP), and `inspect compartments` in tenancy for `--tenancy-scan`. Confirm `--region` matches where the instances live.
- **File:** `discover-oci-instances.sh` (header documents the IAM).

### KB-22 — Discovered instance has no IP / is skipped
- **Symptom:** A running instance doesn't appear in the output.
- **Root cause:** No primary VNIC private IP resolved (instance has no attached VNIC the principal can read, or `read virtual-network-family` is missing).
- **Resolution:** Grant `read virtual-network-family`; verify the instance has a primary VNIC. Instances without a resolvable private IP are intentionally skipped (nothing to scrape).
- **File:** `discover-oci-instances.sh` (`primary_private_ip`).

### KB-23 — OS detected as `linux` for a Windows host
- **Symptom:** A Windows instance is assigned port 9100 instead of 9182.
- **Root cause:** The image's `operating-system` field didn't contain "Windows" (custom image), or `read instance-images` is missing so OS defaults to linux.
- **Resolution:** Grant `read instance-images`; for custom images, edit the generated target's port to 9182 (or fix the merged `config.json`).
- **File:** `discover-oci-instances.sh` (`os_family_for_image`).

---

## Cross-cloud (GCP) & Linux Management Agent

### KB-24 — Linux Management Agent install aborts: *"Agent only supports JDK 8 … Please set JAVA_HOME"*
- **Symptom:** `install-oci-agent-linux.sh` / the agent `installer.sh` stops at "Checking Java version" with *"JAVA_HOME is not set or not readable to root"* / *"Agent only supports JDK 8 with a minimum upgrade version JDK 8u281"*.
- **Root cause:** Unlike some bundles, the Linux Management Agent ZIP does **not** ship a JRE — it requires **JDK 8 (>= 8u281)** on the host with `JAVA_HOME` set (the Linux analog of the Windows KB-08).
- **Resolution:** `install-oci-agent-linux.sh` now installs OpenJDK 8 (`openjdk-8-jdk-headless` on Debian/Ubuntu, `java-1.8.0-openjdk-devel` on RHEL/OEL) and exports `JAVA_HOME` before running `installer.sh`.
- **File:** `install-oci-agent-linux.sh` (`ensure_java8`).

### KB-25 — `manage-oci-datasource.sh` crashes with `JSONDecodeError` on a fresh agent
- **Symptom:** `list` / `create` / `destroy` throw `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.
- **Root cause:** `oci management-agent agent list-data-sources` prints **nothing** (empty stdout) when an agent has zero data sources; the script piped that empty output into `json.load`.
- **Resolution:** `list_raw` now emits `{}` when the CLI returns empty, so JSON parsing is always valid.
- **File:** `manage-oci-datasource.sh` (`list_raw`).

### KB-26 — Cross-cloud agent: metrics never reach OCI Monitoring
- **Symptom:** Agent is ACTIVE on a non-OCI VM (GCP/AWS/on-prem) but the OCI Monitoring namespace stays empty.
- **Root cause (checklist):** the data-source URL points at `/metrics` not `/federate` (KB-12); the dynamic-group/policy granting `USE METRICS` is missing; or the VM's egress can't reach OCI (`*.oraclecloud.com` 443). The agent itself registers over 443 outbound, which most clouds allow by default.
- **Resolution:** Use the `/federate` URL, ensure the `managementagent` dynamic group + `USE METRICS` policy exist in the compartment, and confirm outbound 443 to OCI. Verify with `oci monitoring metric-data summarize-metrics-data --namespace <ns> --query-text 'node_load1[1m].mean()'`.
- **File:** `install-oci-agent-linux.sh`, `manage-oci-datasource.sh`, README "Cross-cloud".

### KB-27 — Agent install fails at first boot (apt/dpkg busy)
- **Symptom:** On a freshly-booted Azure/AWS Ubuntu VM, `install-oci-agent-linux.sh` exits with no/little output and the agent never installs; re-running a few minutes later works.
- **Root cause:** At first boot `cloud-init` / `unattended-upgrades` hold the apt/dpkg lock, so the JDK 8 install fails transiently — and under `set -e` the script exits before printing much.
- **Resolution:** `install-oci-agent-linux.sh` now waits for the apt/dpkg lock to clear (`wait_for_apt`) and retries the install (`apt_install`). If you still hit it on a very busy first boot, wait ~2 min and re-run, or pre-install `openjdk-8-jdk-headless`.
- **File:** `install-oci-agent-linux.sh` (`wait_for_apt`, `apt_install`).

### KB-28 — No SSH to a cloud VM (port 22 blocked/flaky) — use the control plane
- **Symptom:** `ssh`/`scp` to a fresh cloud VM times out on port 22 (intermittently or always), blocking setup.
- **Root cause:** Network path / egress restrictions to that cloud's public IPs, or a security group/NSG gap.
- **Resolution:** Drive the VM over the cloud's control-plane exec instead of SSH — **Azure**: `az vm run-command invoke … --command-id RunShellScript`; **AWS**: attach an SSM instance profile (`AmazonSSMManagedInstanceCore`) and `aws ssm send-command` (reboot once if it was launched without the profile); **GCP**: `gcloud compute ssh` (IAP) or the serial console. For large files (e.g. the 115 MB agent ZIP), create an OCI pre-authenticated request (PAR) and `curl` it on the VM.
- **File:** operational note (cross-cloud testing).
