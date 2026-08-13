# Direct GitHub pull requests

Start only after the platform team has completed the selected environment's `environment_information.md`. OCI references are generated from the Landing Zone. Azure and GCP references are entered by the platform team in a separate reviewed handoff pull request. Blank handoff sections are not usable.

The steps below describe the direct GitHub pull-request route. The optional UI
and Codex assistant use the same catalog and handoff values to prepare the
same aggregate manifest and governed pull request.

Azure and GCP workload requests become available only after Cloud Operations
has completed the reviewed direct-reference section for that cloud in the
same handoff. They are workload paths, not independent foundation bootstrap
paths.

1. Choose one VM or ADB template from `gitops-templates/resources-catalog`.
2. Select exactly one cloud, environment, and region.
3. Copy direct foundation references from that environment's handoff. Do not invent resource groups, networks, subnets, NSGs, service accounts, ODB Networks, or ODB Subnets.
4. Replace resource-secret fields with an environment-qualified runtime placeholder such as `__DEV_AZURE_ADB_ADMIN_PASSWORD__` or `__DEV_GCP_VM_SSH_PUBLIC_KEY__`. Google ADB uses the handed-off Secret Manager reference.
5. Merge the rendered entry into the canonical aggregate manifest. If it is the first entry, replace `{}`. Do not create a second file with the same Terraform root.
6. Open one focused pull request. Review the plan for only the requested create, update, or delete, obtain independent approval, and merge through the governed process.

| Cloud | VM manifest | ADB manifest |
|---|---|---|
| OCI | `oci/{environment}/{region}/compute/compute.json` | `oci/{environment}/{region}/database/database.json` |
| Azure | `azure/{environment}/{region}/compute/compute.json` | `azure/{environment}/{region}/database/database.json` |
| Google | `gcp/{environment}/{region}/compute/compute.json` | `gcp/{environment}/{region}/workloads/adb.json` |

## Worked request: OCI VM

The following is the rendered entry shape for one private OCI VM. The OCIDs
and names are illustrative: replace them only with the selected environment's
handed-off values. Keep the entry in the existing `instances` object rather
than creating a second manifest.

```json
{
  "instances_configuration": {
    "default_compartment_id": "ocid1.compartment.oc1..exampleappcompartment",
    "default_ssh_public_key_path": "/home/github-runner/.ssh/oci_vm_key.pub",
    "instances": {
      "orders_api_vm": {
        "compartment_id": "ocid1.compartment.oc1..exampleappcompartment",
        "cis_level": "1",
        "name": "orders-api-dev-01",
        "shape": "VM.Standard.A1.Flex",
        "flex_shape_settings": { "ocpus": "1", "memory": "6" },
        "platform_image": {
          "ocid": "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaal42ffbltq2gqeh5xlcxvszrk24hkth4vbz4cgxez5wbsqkfy6vya"
        },
        "placement": { "availability_domain": "1", "fault_domain": "1" },
        "boot_volume": {
          "size": "50",
          "preserve_on_instance_deletion": "false"
        },
        "networking": {
          "hostname": "orders-api-dev-01",
          "subnet_id": "ocid1.subnet.oc1..exampleprivateappsubnet",
          "network_security_groups": ["orders_app_nsg"]
        }
      }
    }
  }
}
```

The supplied OCI Compute catalog template carries this Frankfurt image OCID as
the default. Before approving the request, confirm manually that the selected
image is appropriate. Keep it for a Frankfurt `VM.Standard.A1.Flex` request,
or provide the exact regional image OCID for an override; the request is
validated without an OCI CLI lookup.

VMs are private-only. Public-IP fields are rejected. To remove the final resource from one manifest, replace the complete file with the canonical empty object:

```json
{}
```

Removing a declaration is destructive. Confirm the plan identifies only that resource and never edit Terraform state manually.
