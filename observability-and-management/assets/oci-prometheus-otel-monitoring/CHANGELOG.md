# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **`discover-cloud-instances.sh`** — multicloud companion to the OCI discoverer;
  enumerates running instances in AWS, Azure, GCP, or OCI (or `all`) and emits
  cloud-labelled Prometheus targets (table / file_sd / config.json merge).
- **Unified multicloud showcase** — `external_labels: {cloud: …}` per VM so all
  clouds land in **one** OCI Monitoring namespace (`prometheus_multicloud`) and
  **one** Grafana, split by the `cloud` dimension. New
  `otel-destination/dashboards/multicloud.json` + a live 3-cloud Grafana screenshot.
  Validated with one VM each in GCP/Azure/AWS reporting simultaneously.
- **Cross-cloud OCI Monitoring** via `install-oci-agent-linux.sh` — installs the OCI
  Management Agent on any Linux host (GCP/Azure/AWS/on-prem), so non-OCI instances can
  push to OCI Monitoring through a Prometheus `/federate` data source. Installs
  OpenJDK 8, sets `JAVA_HOME`, and waits out first-boot apt locks. Validated
  end-to-end on real VMs in **GCP** (`europe-west1`), **Azure** (`westeurope`), and
  **AWS** (`eu-central-1`) — each feeding **both** OCI Monitoring (its own namespace)
  and a 3rd-party Grafana/Prometheus sink.
- README "Cross-cloud" section + mermaid diagram + a GCP→OTEL→Grafana screenshot.
- KB-24 (Linux agent needs JDK 8 + `JAVA_HOME`), KB-25 (empty `list-data-sources`),
  KB-26 (cross-cloud agent → OCI Monitoring checklist), KB-27 (first-boot apt lock),
  KB-28 (no-SSH → drive via `az vm run-command` / `aws ssm send-command`).
- `discover-oci-instances.sh` — enumerate RUNNING OCI compute instances in a
  compartment (or whole tenancy subtree) and generate Prometheus scrape targets,
  with per-OS exporter ports (Linux 9100 / Windows 9182). Outputs a human table,
  a `discovered-targets.json` (Prometheus `file_sd_config`), or a non-destructive
  merge into `config.json` `TargetNodes`.
- `docs/KNOWLEDGE_BASE.md` — searchable troubleshooting KB (23 entries) derived
  from the end-to-end validation.
- Public-repo scaffolding: `LICENSE` (UPL-1.0), `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, GitHub issue/PR templates, and a `lint.yml` CI workflow
  (shellcheck + PSScriptAnalyzer + `docker compose config`).

### Changed
- **OCI Monitoring is now optional.** New `OciMonitoringEnabled` config flag. The
  proxy can run as a pure OpenTelemetry / `remote_write` exporter to a non-OCI
  backend; the Management Agent zip/response-file prompts and install only happen
  when OCI Monitoring is enabled. The final summary reflects the active export
  paths, and the script warns if no export path is enabled.
- `otel-destination/docker-compose.yml` — Grafana admin password is now
  env-overridable (`GF_SECURITY_ADMIN_PASSWORD`).
- Hardened `.gitignore` (secrets, `.env*`, `*.pem`, `*.key`, `*.rsp`,
  `discovered-targets.json`).
- Removed a developer-specific local path from `PROJECT_REVIEW.md`.

### Fixed
- `manage-oci-datasource.sh` no longer crashes with a JSON parse error when an agent
  has zero data sources (the CLI returns empty output) — KB-25.

## [0.1.0] — 2026-06-17

### Added
- Initial validated suite: Windows/Linux exporter installers, Windows Prometheus
  proxy, OCI Management Agent integration, optional GCP `stackdriver_exporter`,
  OpenTelemetry export path, `manage-oci-datasource.sh` lifecycle helper, and the
  `otel-destination/` test sink.
- `PROJECT_REVIEW.md` — end-to-end test report on real OCI infrastructure with 13
  documented bug fixes.
