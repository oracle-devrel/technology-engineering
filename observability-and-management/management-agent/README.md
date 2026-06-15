# OCI Management Agent Installation

This folder contains the OCI Management Agent software package used for the
VM installation workflow.

[Download bootstrap script](./files/install_oci_management_agent.sh)


## Prerequisites

- OCI CLI configured with access to the target tenancy and compartment.
- SSH access to the VM as `<ssh_user>`.
- VM can reach OCI Management Agent endpoints.
- Linux VM with `sudo`, `systemd`, `rpm`, and `tar`.
- `curl` is required only when using `--java-url` or package URL downloads.
- `dnf` or `yum` is required only when explicitly using `--java-install-mode package`.

The VM-side installer checks for Java 8u281 or newer. It does not install Java
through the OS package manager by default, so it does not change customer Java
alternatives. If no supported Java runtime exists, provide one of these options:

- `--java-home <java_home_path>`
- `--java-tarball <java8_tarball_path>`
- `--java-url <java8_tarball_url>`

Standalone Java is extracted to `<standalone_java_install_dir>` when
`--java-install-dir` is provided, or to the script default otherwise. It is
exported as `JAVA_HOME` only for the Management Agent install/configure
commands. Use `--java-install-mode package` only if you explicitly want the OS
package-manager behavior.

The same Java options can be passed to `oci_bootstrap_management_agent_vm.sh`.
When `--java-tarball <java8_tarball_path>` is used with the bootstrap script,
the tarball is copied to the VM and then passed to the VM-side installer.

## Example 1. Public Internet Java Download

If the VM has outbound HTTPS access, the bootstrap script can ask the remote
installer to download Eclipse Temurin Java 8 directly from Adoptium:

```bash
OCI_MGMT_AGENT_DOWNLOAD_DIR=<local_agent_download_dir> \
bash scripts/oci_bootstrap_management_agent_vm.sh \
  --compartment-name <compartment_name> \
  --vm-host <vm_public_ip_or_dns> \
  --ssh-key <ssh_private_key_path> \
  --java-url "https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jdk/hotspot/normal/eclipse"
```

The VM needs outbound HTTPS access to `api.adoptium.net` and the redirected
binary download location. See the Adoptium Temurin releases page for Java 8 LTS
and REST API download options:
<https://adoptium.net/temurin/releases/?version=8>.

## Example 2. Standalone Java Location

Unless `--java-install-dir <standalone_java_install_dir>` is provided, the
VM-side installer extracts standalone Java to:

```text
/opt/oci-management-agent-java
```

Verify it on the VM with:

```bash
<standalone_java_install_dir>/bin/java -version
```

For the default location:

```bash
/opt/oci-management-agent-java/bin/java -version
```

## Wallet Password Rules

`OCI_MGMT_AGENT_WALLET_PASSWORD` must:

- Be at least 16 characters.
- Include lowercase, uppercase, and numeric characters.
- Include at least one special character from `!@#%^&*`.
- Avoid other special characters such as `_`.

If you press Enter at the wallet prompt, the bootstrap script generates a
compliant wallet password automatically. Do not commit install keys, response
files, or wallet passwords.

## Full Bootstrap Install

Run this from the workspace root:

```bash
OCI_MGMT_AGENT_DOWNLOAD_DIR=/tmp \
bash oci_bootstrap_management_agent_vm.sh \
  --compartment-name <compartment_name> \
  --vm-host <vm_public_ip_or_dns> \
  --ssh-key <ssh_private_key_path>
```

The bootstrap script:

1. Resolves the compartment.
2. Creates a short-lived Management Agent install key.
3. Detects the VM architecture over SSH.
4. Downloads the current Linux Management Agent RPM into `files/`.
5. Writes a temporary `input.rsp` response file.
6. Copies the installer, package, and response file to the VM.
7. Runs the VM-side installer through `sudo`.
8. Removes the generated response file after installation.

## VM-Side Local Package Install

If the RPM is already on the VM, run the VM-side installer directly:

```bash
sudo OCI_MGMT_AGENT_INSTALL_KEY_FILE=<install_key_file_path> \
  OCI_MGMT_AGENT_WALLET_PASSWORD_FILE=<wallet_password_file_path> \
  OCI_MGMT_AGENT_PACKAGE=<remote_agent_package_path> \
  bash <remote_installer_script_path>
```

## Verify

On the VM:

```bash
sudo systemctl status mgmt_agent
```

From OCI CLI:

```bash
oci management-agent agent list \
  --compartment-id <compartment_ocid> \
  --all
```

Look for `availability-status` and `lifecycle-state` equal to `ACTIVE`, and for
the `logan` plugin status equal to `RUNNING` when Log Analytics is enabled.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
