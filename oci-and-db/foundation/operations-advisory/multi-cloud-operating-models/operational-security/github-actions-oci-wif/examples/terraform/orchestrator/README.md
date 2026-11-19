# Terraform OCI LZ Orchestrator RPST bucket demo

This demo runs the official [OCI Landing Zones Orchestrator](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator)
as the Terraform root with provider-native Workload Identity Federation. It
creates one private Object Storage bucket and deletes it in the same run.
Follow the [setup runbook](../../../SETUP.md) first.

## Run

Set `OCI_TENANCY` to your tenancy OCID in repository Actions secrets, in addition
to the six shared secrets in the runbook.

1. Open **Actions → Demo Terraform OCI LZ Orchestrator RPST Bucket → Run workflow**.
2. Select `plan`. The workflow requires exactly one bucket creation with
   `NoPublicAccess` before it can proceed to apply.
3. Run again with `apply-and-destroy` to create and delete the bucket.
4. Check plan, apply, and destroy in the summary, then confirm bucket absence
   in OCI.

GitHub requires the workflow on the repository's default branch for manual
dispatch.

## Configuration

The workflow fetches Orchestrator commit
`4faa47489242abe056fb5ceb0288c51e29522902`, observed on upstream `main` and tag
`v2.1.4` on 8 October 2026. It executes that checkout directly and leaves the
upstream Terraform source unchanged. Terraform is **1.16.5** and the OCI provider
is locked to **9.8.0**. The lock includes all providers required by the
Orchestrator and checksums for Linux AMD64 and macOS ARM64.

[inputs.tfvars.json.example](./inputs.tfvars.json.example) contains the accepted
inputs. The workflow fills in tenancy, region, compartment, and a unique bucket
name in a protected temporary copy. `compartment_id: null` selects
`default_compartment_id`. Other configuration families remain unset. The
Orchestrator also reads the tenancy, regions, and Object Storage namespace.

Authentication uses `OCI_AUTH=WorkloadIdentityFederation` and the shared RPST
exchange settings. The workflow obtains a fresh source JWT before plan, apply,
and destroy. The provider generates and manages its RPST and signing key.

Terraform initializes the upstream modules even when their configuration
families are disabled. Their source refs are those declared by the selected
Orchestrator commit; the provider lock does not lock Git module revisions.

The bucket is named `rpst-orchestrator-<run_id>`. Source, inputs, provider data,
plan, and local state stay under `$RUNNER_TEMP/rpst-orchestrator` and are removed
after the run. If destroy fails, delete the named bucket manually; state is not
retained for another run.

## Execution

On 8 October 2026, [plan, apply, and destroy](https://github.com/dgutierrezcolodra/oci-terraform-github-actions-wif-example/actions/runs/37769008078)
passed with native WIF and the runbook's two IAM policies. The plan check
confirmed exactly one private bucket; Terraform created it and deleted it.
An independent OCI query confirmed its absence. Init, validate, and runtime
cleanup also passed.
