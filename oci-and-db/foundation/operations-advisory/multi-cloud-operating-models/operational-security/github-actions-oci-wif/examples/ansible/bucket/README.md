# Ansible RPST bucket demo

This demo creates one private Object Storage bucket and deletes it in the same
run. Follow the [setup runbook](../../../SETUP.md) first.

## Run

Open **Actions → Demo Ansible RPST Bucket → Run workflow**, select the branch,
and run it. Review the RPST exchange, create, and delete outcomes in the job
summary. GitHub requires the workflow on the default branch for manual dispatch.

The workflow obtains a GitHub OIDC token and calls the local credential action.
That action generates an RSA key, exchanges the JWT for an RPST, and writes the
RPST and key under `$RUNNER_TEMP/oci-ansible-wif` with mode 600. The collection
uses `OCI_ANSIBLE_AUTH_TYPE=resource_principal` and the SDK's file-based resource
principal interface:

| Variable | Value |
| --- | --- |
| `OCI_RESOURCE_PRINCIPAL_VERSION` | `2.2` |
| `OCI_RESOURCE_PRINCIPAL_RPST` | Absolute path to the protected RPST file |
| `OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM` | Absolute path to the protected private key file |
| `OCI_RESOURCE_PRINCIPAL_REGION` | OCI region |

Only file paths, the region, and authentication settings go into `GITHUB_ENV`.
The client secret stays in the exchange step's environment.
[Oracle authentication guide](https://docs.oracle.com/en-us/iaas/tools/oci-ansible-collection/latest/guides/authentication.html).

The playbook reads the namespace and sets the bucket state to `present` or
`absent`. The bucket is named `rpst-ansible-<run_id>` with `NoPublicAccess`.
Deletion runs even after a failed create attempt, with a fresh GitHub JWT and
RPST. Credentials, dependencies, caches, and Ansible temporary files are removed
in the final cleanup. If deletion fails, remove the named bucket manually.

## Dependencies and local syntax check

The workflow pins Python 3.11, Ansible Core 2.15.13, OCI Python SDK 2.182.1,
and the OCI collection source commit in [requirements.yml](../requirements.yml).

```bash
python3 -m venv /tmp/oci-rpst-ansible
/tmp/oci-rpst-ansible/bin/pip install 'ansible-core==2.15.13' 'oci==2.182.1'
/tmp/oci-rpst-ansible/bin/ansible-galaxy collection install -r examples/ansible/requirements.yml
/tmp/oci-rpst-ansible/bin/ansible-playbook --syntax-check examples/ansible/bucket/playbook.yml
```

Syntax checking does not call OCI. Do not use verbose Ansible output or HTTP
debug logging when running with credentials. These short workflows request
fresh credentials before bucket operations; they do not run a background
refresh process for long playbooks.

## Execution

The [8 October 2026 execution](https://github.com/dgutierrezcolodra/oci-terraform-github-actions-wif-example/actions/runs/37766766106)
passed from `main`: RPST exchange, bucket creation, deletion, and runtime cleanup.
An independent OCI query confirmed bucket absence. This record covers the short
bucket workflow; it does not establish support for playbooks longer than the
issued RPST lifetime.
