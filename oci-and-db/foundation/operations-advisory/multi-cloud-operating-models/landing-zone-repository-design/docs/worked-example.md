# Worked Example

[Back to overview](../README.md)

This page follows one organization from a single-stack Landing Zone to the [minimum split](../README.md#minimum-split-for-a-small-team), and then to a second region. The configuration fragments use the file formats of the [OCI Landing Zones orchestrator](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator) and the key style of the [reference implementation](https://github.com/multicloud-control-plane/oci-landing-zone). They are trimmed to the fields that matter for the example.

## Starting point

- One-OE Landing Zone in the home region, `eu-frankfurt-1`.
- One Git repository and one ORM stack with one state file. The deployment runs in steps (step 1, firewall configuration, step 2) on the same stack.
- A small central team of six to eight people.
- Next goals: separate production from non-production, and add a DR region.

The team has already seen the first symptoms: a change to tags on all compartments failed and blocked every other change until it was fixed.

## Step 1: target layout

The team adopts the minimum split with consolidated IAM (Pattern A in [IAM placement](component-distribution.md#iam-placement)):

```text
acme-landing-zone/
├── common/                         # OP.00  stack 1
│   ├── iam.json
│   ├── governance.json
│   ├── security.json
│   └── observability.json
├── lze_prod/
│   └── eu-frankfurt-1/             # OP.01  stack 2
│       ├── network.json
│       ├── security.json
│       └── observability.json
├── workload_prod/
│   └── eu-frankfurt-1/             # OP.02  stack 3
│       ├── network.json
│       └── observability.json
└── workload_nonprod/
    └── eu-frankfurt-1/             # OP.02  stack 4
        ├── network.json
        └── observability.json
```

Four stacks, four state files. A failure in `workload_nonprod` no longer blocks `workload_prod`, and nothing in the regional folders depends on IAM being in the same stack.

## Step 2: IAM in `common/`

All compartments are defined once, by key. The regional stacks never create compartments; they only refer to these keys.

```json
{
  "compartments_configuration": {
    "enable_delete": "true",
    "compartments": {
      "CMP-LANDINGZONE-KEY": {
        "name": "cmp-landingzone",
        "description": "Enclosing Landing Zone compartment",
        "children": {
          "CMP-LZ-NETWORK-KEY":  { "name": "cmp-lz-network",  "description": "Shared network" },
          "CMP-LZ-SECURITY-KEY": { "name": "cmp-lz-security", "description": "Shared security" },
          "CMP-LZ-PROD-KEY": {
            "name": "cmp-lz-prod",
            "description": "Production workload environment",
            "children": {
              "CMP-LZ-PROD-NETWORK-KEY": { "name": "cmp-lz-prod-network", "description": "Production network" }
            }
          },
          "CMP-LZ-NONPROD-KEY": {
            "name": "cmp-lz-nonprod",
            "description": "Non-production workload environment",
            "children": {
              "CMP-LZ-NONPROD-NETWORK-KEY": { "name": "cmp-lz-nonprod-network", "description": "Non-production network" }
            }
          }
        }
      }
    }
  }
}
```

After apply, the orchestrator generates `compartments_output.json`. Every other stack reads it:

```json
{
  "compartments": {
    "CMP-LANDINGZONE-KEY":        { "id": "ocid1.compartment.oc1..aaaa1" },
    "CMP-LZ-NETWORK-KEY":         { "id": "ocid1.compartment.oc1..aaaa2" },
    "CMP-LZ-PROD-NETWORK-KEY":    { "id": "ocid1.compartment.oc1..aaaa3" },
    "CMP-LZ-NONPROD-NETWORK-KEY": { "id": "ocid1.compartment.oc1..aaaa4" }
  }
}
```

## Step 3: hub in `lze_prod/eu-frankfurt-1/`

The hub refers to its compartment by key and defines the DRG that the spokes will use. The region code (`FRA`) is part of every key, so the same keys never appear in two regions.

```json
{
  "network_configuration": {
    "network_configuration_categories": {
      "shared": {
        "category_compartment_id": "CMP-LZ-NETWORK-KEY",
        "non_vcn_specific_gateways": {
          "dynamic_routing_gateways": {
            "DRG-FRA-LZ-HUB-KEY": { "display_name": "drg-fra-lz-hub" }
          }
        },
        "vcns": {
          "VCN-FRA-LZ-HUB-KEY": {
            "display_name": "vcn-fra-lz-hub",
            "cidr_blocks": ["10.200.0.0/21"]
          }
        }
      }
    }
  }
}
```

After apply, `network_output.json` contains the DRG under its key:

```json
{
  "network_resources": {
    "dynamic_routing_gateways": {
      "DRG-FRA-LZ-HUB-KEY": { "id": "ocid1.drg.oc1.eu-frankfurt-1.aaaa5" }
    },
    "vcns": {
      "VCN-FRA-LZ-HUB-KEY": { "id": "ocid1.vcn.oc1.eu-frankfurt-1.aaaa6" }
    }
  }
}
```

## Step 4: spoke in `workload_prod/eu-frankfurt-1/`

The spoke uses two dependencies: the compartment key from `common/` and the DRG key from the hub. It creates its own VCN and injects its attachment into the existing hub DRG, so the hub configuration does not change for the attachment.

```json
{
  "network_configuration": {
    "network_configuration_categories": {
      "prod": {
        "category_compartment_id": "CMP-LZ-PROD-NETWORK-KEY",
        "non_vcn_specific_gateways": {
          "inject_into_existing_drgs": {
            "DRG-FRA-LZ-HUB-KEY": {
              "drg_id": "DRG-FRA-LZ-HUB-KEY",
              "drg_attachments": {
                "DRGATT-FRA-LZ-PROD-KEY": {
                  "display_name": "drgatt-fra-lz-prod",
                  "network_details": {
                    "attached_resource_key": "VCN-FRA-LZ-PROD-KEY",
                    "type": "VCN"
                  }
                }
              }
            }
          }
        },
        "vcns": {
          "VCN-FRA-LZ-PROD-KEY": {
            "display_name": "vcn-fra-lz-prod",
            "cidr_blocks": ["10.200.8.0/21"],
            "route_tables": {
              "RT-FRA-LZ-PROD-KEY": {
                "display_name": "rt-fra-lz-prod",
                "route_rules": {
                  "to-hub": {
                    "description": "Route to the hub through the DRG",
                    "destination": "10.200.0.0/21",
                    "destination_type": "CIDR_BLOCK",
                    "network_entity_key": "DRG-FRA-LZ-HUB-KEY"
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

The hub still needs a small, separate change for the new spoke CIDR: routing and firewall rules in `lze_prod/eu-frankfurt-1/`. That is step 3 of [Changes that cross stacks](dependencies-and-state.md#changes-that-cross-stacks).

## How the stacks are wired

**With Terraform CLI (pipelines).** Each job initializes its own state key and passes the upstream output files as dependencies. With the orchestrator `rms-facade` in file mode, the variables for the spoke stack look like this:

```hcl
configuration_source        = "file"
local_config_file_paths     = ["workload_prod/eu-frankfurt-1/network.json"]
local_dependency_file_paths = ["deps/compartments_output.json", "deps/network_output.json"]
save_output                 = true
output_format               = "json"
output_folder_path          = "out/workload_prod/eu-frankfurt-1"
```

The pipeline fills `deps/` before `plan`, either by reading the upstream state (as the reference implementation does) or by downloading the saved output files.

```text
terraform init -backend-config="key=workload_prod/eu-frankfurt-1/terraform.tfstate" ...
```

**With ORM.** Each folder is its own ORM stack, created in the region it manages. In the stack's *Input Files*, the configuration files point to the folder, the *Dependency Files* point to the saved `compartments_output.json` and hub `network_output.json`, and *Save Output* writes this stack's outputs under its own prefix. ORM can read these files only from a private GitHub repository or an OCI bucket (see [Runtime](runtime.md)).

## Step 5: adding the DR region

The team adds `eu-amsterdam-1`:

```text
acme-landing-zone/
├── common/                         # unchanged: IAM is not repeated
├── lze_prod/
│   ├── eu-frankfurt-1/
│   └── eu-amsterdam-1/             # OP.01  new stack: own hub, AMS keys
└── workload_prod/
    ├── eu-frankfurt-1/
    └── eu-amsterdam-1/             # OP.02  new stack: spoke attached to the AMS hub
```

- The new folders are copies of the Frankfurt ones with `AMS` keys, new CIDR ranges, and no IAM.
- The DR resources use the same compartments as Frankfurt, because compartments exist in every subscribed region. New compartments, if ever needed, are added to `common/iam.json`, which is applied in the home region.
- Their state keys live in a state bucket in `eu-amsterdam-1`. With ORM, their stacks are created in `eu-amsterdam-1`.
- The Amsterdam spoke reads the Amsterdam hub output, never the Frankfurt one.
- The remote peering between the two hubs is a network change on each hub stack.

## Result

| Stack | State key | State location | Runs when |
|---|---|---|---|
| `common/` | `common/terraform.tfstate` | Home region | IAM, tags, budgets or Cloud Guard change |
| `lze_prod/eu-frankfurt-1` | `lze_prod/eu-frankfurt-1/terraform.tfstate` | Frankfurt | Frankfurt hub or shared security changes |
| `workload_prod/eu-frankfurt-1` | `workload_prod/eu-frankfurt-1/terraform.tfstate` | Frankfurt | Production spoke changes |
| `workload_nonprod/eu-frankfurt-1` | `workload_nonprod/eu-frankfurt-1/terraform.tfstate` | Frankfurt | Non-production spoke changes |
| `lze_prod/eu-amsterdam-1` | `lze_prod/eu-amsterdam-1/terraform.tfstate` | Amsterdam | Amsterdam hub changes |
| `workload_prod/eu-amsterdam-1` | `workload_prod/eu-amsterdam-1/terraform.tfstate` | Amsterdam | DR spoke changes |

For a new tenancy, the stacks are applied in order: `common/`, then each `lze_*`, then each `workload_*`. After that, each change runs only in the stack that owns it. The tag change that once blocked everything now runs in `common/` alone; if it fails, the regional stacks can still be changed.

To move the existing resources from the original stack into these stacks without recreating them, follow [Moving resources between stacks](adoption.md#moving-resources-between-stacks).
