# Automating SAML Metadata Retrieval in OCI Identity Domains

This solution provisions an **OCI Identity Domain** with Terraform and securely retrieves its **SAML metadata** for integration with external identity providers.

Instead of making the SAML metadata publicly accessible by enabling the *“Configure client access”* option under *Access Signing Certificate*, this approach uses a **temporary confidential OAuth client** to authenticate and download the metadata.

The workflow is:

1. **Provisioning with Terraform (Optional)**

   * Deploy the OCI Identity Domain.
   * Trigger a shell script via `null_resource` provisioner after domain creation.

2. **Automated Metadata Retrieval via Shell Script**

   * Register a **temporary confidential application** that supports the *client credentials* grant type via OCI CLI.
   * Request an `access_token` from the Identity Domain OAuth endpoint using the app's credentials.
   * Call the `/fed/v1/metadata` endpoint with `Authorization: Bearer` header.
   * Download and save the SAML metadata XML to a local file (`oci_idcs_metadata.xml`).
   * Deactivate and delete the temporary confidential app (cleanup).
   * Print the `client_id` and masked `client_secret` to stdout (not stored in Terraform state).

3. **Security Benefits**

   * **No Public Exposure**: The SAML metadata endpoint remains private and is never exposed to the internet.
   * **Authenticated Access**: Only the temporary, authenticated client can retrieve the metadata.
   * **Ephemeral Credentials**: The OAuth client is destroyed immediately after use, minimizing the attack surface.
   * **State-Free Secrets**: The client credentials are never written to the Terraform state file.

This method provides both **automation** and **security**, ensuring SAML metadata can be retrieved programmatically without compromising the confidentiality of signing certificates.


## Resources Created

### By Terraform (Optional):
1. **OCI Identity Domain** (`oci_identity_domain.identity_domain`) - A managed identity domain in OCI with specified compartment, display name, description, license type, and home region
2. **Null Resource** (`null_resource.configure_idcs_app`) - Triggers the shell script after domain creation
3. The **OCI Identity Domain** is not destroyed after creation. The SAML metadate would then be invalid.

### By Shell Script (`create_confidential_app_and_get_saml_meta_data.sh`):
1. **Confidential OAuth Client App** - Created in the new identity domain with:
   - Client credentials grant type
   - Confidential client type
   - Custom web app template
2. **SAML Metadata XML File** (`oci_idcs_metadata.xml`) - Downloaded to local filesystem
3. **Cleanup** - By default, the script deactivates and deletes the confidential app after downloading metadata (unless `KEEP_APP=true`)

## Prerequisites

### Required Tools:
- **OCI CLI** with Identity Domains commands
- **jq** (JSON processor)
- **curl**
- **python3**
- **Terraform** ≥ 1.5.0

### Required Configuration:
1. **OCI CLI configured** with valid profile (default: `DEFAULT`)
2. **terraform.tfvars** populated with:
   - `compartment_id` (OCID of the enclosing compartment)
   - `region`
   - `domain_display_name`
   - `domain_description`
   - `license_type`
   - `tenancy_ocid`
   - `oci_profile` 

### Optional (for cleanup):
- `ADMIN_ACCESS_TOKEN` or
- `ADMIN_CLIENT_ID` + `ADMIN_CLIENT_SECRET` (for proper app cleanup with admin privileges)

## How to Run

1. **Initialize**: `terraform init`
2. **Plan**: `terraform plan -out tfplan`
3. **Apply**: `terraform apply tfplan`

### Environment Variables (optional):
- `APP_NAME` - Custom app name (default: `saml-metadata-client`)
- `SCOPE` - OAuth scope (default: `urn:opc:idm:__myscopes__`)
- `OUT_XML` - Output file path (default: `oci_idcs_metadata.xml`)
- `KEEP_APP` - Set to `true` to prevent app deletion

The script automatically receives `IDCS_ENDPOINT` and `PROFILE` from Terraform.

## Terraform Flow

During `apply`, the configuration creates the OCI Identity Domain. After the domain exists, Terraform triggers `scripts/create_confidential_app_and_get_saml_meta_data.sh`, which:

- provisions a confidential OAuth client against the new domain via the OCI CLI,
- regenerates the client secret if necessary,
- retrieves a client-credentials token, and
- downloads the SAML metadata document to `oci_idcs_metadata.xml` (override via `OUT_XML`).

The script prints the confidential app ID, client ID, and a masked client secret—store the full secret securely outside of Terraform state.

## Running the Script Standalone

If an identity domain already exists, you can run the script directly without Terraform:

```bash
IDCS_ENDPOINT="https://idcs-<hash>.identity.oraclecloud.com" \
PROFILE="oci_profile_name" \
bash scripts/create_confidential_app_and_get_saml_meta_data.sh
```

### Optional Environment Variables:
- `APP_NAME` - Custom app name (default: `saml-metadata-client`)
- `SCOPE` - OAuth scope (default: `urn:opc:idm:__myscopes__`)
- `OUT_XML` - Output file path (default: `oci_idcs_metadata.xml`)
- `KEEP_APP` - Set to `true` to prevent app deletion after metadata retrieval
- `ADMIN_ACCESS_TOKEN` - Bearer token with Identity Domain Administrator rights (preferred for cleanup)
- `ADMIN_CLIENT_ID` / `ADMIN_CLIENT_SECRET` - Admin confidential app credentials (alternative for cleanup)
- `ADMIN_SCOPE` - Admin scope (default: `urn:opc:idm:__myscopes__`)

### Example with custom settings:
```bash
IDCS_ENDPOINT="https://idcs-abc123.identity.oraclecloud.com" \
PROFILE="my-oci-profile" \
APP_NAME="my-metadata-app" \
OUT_XML="custom_metadata.xml" \
KEEP_APP="false" \
bash scripts/create_confidential_app_and_get_saml_meta_data.sh
```

This is useful when you need to retrieve SAML metadata from an existing identity domain without provisioning a new one. When you want to keep the confidential application, set the variable KEEP_APP to false.
