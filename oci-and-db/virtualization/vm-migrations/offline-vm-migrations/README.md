# OCI Offline Migration Assistant

The [OCI Offline Migration Assistant](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant) brings virtual machines into Oracle Cloud Infrastructure. It runs as a single VM in your OCI tenancy with a web UI: log in to the source platform, pick the VMs, choose where they should land in OCI, and follow the progress. The tool creates OCI instances from the source disks and maps firmware and sizing to supported OCI options. Review the [guest prerequisites and limitations](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/limitations.md) before migration; some guests need driver installation or manual configuration to boot correctly.

**Migrate from**

- **VMware** — vCenter or a standalone ESXi host
- **Hyper-V** — a Hyper-V host (Hyper-V Manager)
- **Oracle Linux Virtualization Manager** — OLVM (oVirt) engine
- **Nutanix AHV** — Prism Central or Prism Element
- **Proxmox VE** — a node or cluster (API on TCP 8006, disks read over SSH)
- **Microsoft Azure**
- **Amazon Web Services** — EC2 instances
- **Google Cloud** — Compute Engine VMs
- **Manual import** — an OVA/OVF, VMDK, or QCOW2 uploaded to OCI Object Storage

**Extra features**

- **Create OCI instance from ISO** — boot a new instance from an installer ISO and install the OS through a Remote Console session
- **OCI Remote Console** — open the VNC console of any compute instance in your browser
- **Export from OCI to OVA/OVF** — turn an OCI instance into an OVA/OVF package in Object Storage

Linux guests support optional initramfs, DHCP network and cloud-agent fixes on the OCI copy. Windows guests may need VirtIO drivers installed before migration. Live migration with delta sync, VMware Workstation/Fusion and unmanaged KVM (a host that is not OLVM) are not supported. See [limitations](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/limitations.md).

Reviewed: 04.11.2026

# Table of Contents

1. [Quick start](#quick-start)
2. [Documentation](#documentation)
3. [License](#license)

# Quick start

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/raw/b06d57108b8c31ec8dc9f7649c9ff898d64fc0e4/oci-offline-migration-assistant-stack.zip)

The button uses a verified stack revision. If an already-open Create stack page shows an older description, close it and open the button again. Existing stacks retain their saved configuration.

1. **Deploy** the tool VM with the button above. Resource Manager opens *Create stack* with the stack preloaded; choose the compartment, the subnet the VM should live in and the IP ranges that may use the web UI, then apply. Manual Terraform deployment and all settings are described in [install-helper.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/install-helper.md).
2. **Open the web UI** at `https://<tool-vm-ip>:8443/` and accept the self-signed certificate. On the first visit you can protect the UI with a password (optional; change it later under *Setup*).
3. **Pick what you want to do** on the start page: a source platform to migrate from, or one of the extra features. Each card explains what it needs, and the *(i)* buttons show how to prepare the source credentials.

Without a UI password, anyone who can reach the UI can create an anonymous session and manage OCI resources within the tool VM's IAM scope. All unlocked sessions share that authority; source login does not isolate jobs by user. Configure a password on first use and restrict access to administrators.

# Documentation

Full documentation lives in the [OCI Offline Migration Assistant repository](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant):

- [install-helper.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/install-helper.md) — deployment, IAM, configuration reference
- [how-it-works.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/how-it-works.md) — migration mechanism, supported sources, network flows
- [architecture.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/architecture.md) — internals of the migration pipeline
- [os-mapping.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/os-mapping.md) — guest OS, launch option and shape mapping tables
- [limitations.md](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/docs/limitations.md) — known limitations and troubleshooting

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.

The OCI Offline Migration Assistant tool is licensed under [UPL 1.0](https://github.com/RichardORCL/OCI-Offline-Migration-Assistant/blob/main/LICENSE) in its source repository.
