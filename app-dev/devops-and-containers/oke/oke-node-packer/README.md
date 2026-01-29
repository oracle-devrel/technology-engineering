# OKE Custom Node Image Builder

This project uses Packer to create custom images for Oracle Kubernetes Engine (OKE) nodes based on Oracle-provided base images. The customizations include:
1. Updating all packages to their latest versions.
2. Installing `oci-fss-utils` for in-transit encryption support.
3. Installing `oci` cli to enable cloud-init to modify oracle cloud agent capabilities
4. Stop the `dnf-makecache` timer to improve stability and resource utilization.
5. Upgrading to cgroups v2.

## Prerequisites
- Packer installed (version compatible with the oracle plugin ~>1).
- Oracle Cloud Infrastructure (OCI) CLI configured with necessary credentials.
- Access to an OCI compartment, subnet, and a base OKE node image OCID.
- Only Oracle Linux 8 base images are supported for this Packer build.
- If you're not an administrator, ensure your user group (e.g., PackerGroup) has the following OCI IAM policies:
  ```
  Allow group PackerGroup to manage instance-family in compartment ${COMPARTMENT_NAME}
  Allow group PackerGroup to manage instance-images in compartment ${COMPARTMENT_NAME}
  Allow group PackerGroup to use virtual-network-family in compartment ${COMPARTMENT_NAME}
  Allow group PackerGroup to manage compute-image-capability-schema in tenancy
  ```
  Replace `PackerGroup` with your actual group name and `${COMPARTMENT_NAME}` with your compartment name.

## Setup
1. Clone this repository or copy the files to your local machine.
2. Edit `vars.pkrvars.hcl` to provide your specific OCI details (see below for placeholders).

### Configuring vars.pkrvars.hcl
Update the file with your values:
- `availability_domain`: Your OCI availability domain (e.g., "XXXX:REGION-AD-1").
- `base_image_ocid`: OCID of the Oracle-provided OKE base image. To find the latest base image OCID, refer to the [Find OKE base images section](#find-oke-base-images).
- `compartment_ocid`: OCID of your OCI compartment.
- `image_prefix`: Prefix for the generated image name (default: "oke-custom-image").
- `shape`: VM shape (e.g., "VM.Standard.E4.Flex").
- `ocpus`: Number of OCPUs (default: 1).
- `memory_in_gbs`: Memory in GB (default: 8).
- `subnet_ocid`: OCID of the subnet for the build instance.
- `region`: OCI region (e.g., "eu-frankfurt-1").
- `skip_create_image`: Set to true to skip image creation (default: false).

## Usage
1. Ensure you're in the project directory.
2. Run the build script:
   ```
   ./run-packer.sh
   ```
3. Packer will provision a temporary instance, apply customizations, and create the custom image in your compartment.

## Find OKE Worker Node base images

The latest Oracle Linux 8 OKE images can be found on the official release page: [Oracle Linux 8 OKE Worker Node Images](https://docs.oracle.com/en-us/iaas/images/oke-worker-node-oracle-linux-8x/index.htm).

Alternatively, run `find-oke-images.sh` to find the latest available images for your OKE cluster:
1. In `find-oke-images.sh`, set the `REGION`, `CLUSTER_OCID` and `OKE_VERSION` accordingly
2. Be sure to have `jq` installed and `oci` CLI configured
3. Run the script:
    ```
    ./find-oke-images.sh
    ```

## Files Overview
- `oke-custom-image.pkr.hcl`: Main Packer configuration.
- `variables.pkr.hcl`: Variable definitions.
- `vars.pkrvars.hcl`: User-configurable variables.
- `run-packer.sh`: Script to execute the Packer build.
- `find-oke-images.sh`: Script to output the OCID of the latest OKE base worker node images

## Troubleshooting
- If the build fails, check OCI permissions and network access.
- Use the `-debug` flag in run-packer.sh for detailed logs.
- Base images are constantly updated by Oracle, ensure you use the latest OCID.

For more details on Packer and OCI integration, refer to the [Packer OCI Plugin documentation](https://developer.hashicorp.com/packer/integrations/hashicorp/oracle/latest/components/builder/oci).

# OKE Custom Node Image Builder - Cloud Shell

For users who prefer to use the cloud shell, there is a version of this script that runs on a cloud shell.

[![Open in Code Editor](https://raw.githubusercontent.com/oracle-devrel/oci-code-editor-samples/main/images/open-in-code-editor.png)](https://cloud.oracle.com/?region=home&cs_repo_url=https://github.com/alcampag/oke-node-packer-cs.git&cs_branch=main&cs_readme_path=README.md&cs_open_ce=true)
