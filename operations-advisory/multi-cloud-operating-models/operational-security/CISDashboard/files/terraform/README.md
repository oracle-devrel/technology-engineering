# Oracle Cloud Infrastructure Log Analytics Custom Content Import

This Terraform code is used to import custom content into Oracle Cloud Infrastructure (OCI) Log Analytics.

## Prerequisites

* Oracle Cloud Infrastructure account
* Terraform installed (version >= 1.0.0, <1.6.0)
* OCI provider configured (version "~> 7.2")

## Usage

1. Initialize the Terraform working directory by running `terraform init`.
2. Create a `terraform.tfvars` file with the required variables:
   * `log_analytics_custom_content_files`: a set of filepaths to the custom content files to be imported.
   * `namespace`: the Log Analytics namespace.

Example `terraform.tfvars`:
```hcl
log_analytics_custom_content_files = [
  "path/to/custom/content/file1",
  "path/to/custom/content/file2"
]

namespace = "your_log_analytics_namespace"
```

3. Run `terraform apply` to import the custom content files into Log Analytics.

## Variables

* `log_analytics_custom_content_files`: a set of filepaths to the custom content files to be imported.
* `namespace`: the Log Analytics namespace.

## Notes

* The `is_overwrite` flag is set to `true` by default, which means that existing custom content with the same name will be overwritten.
* Make sure to replace the filepaths and namespace with your actual values in the `terraform.tfvars` file.