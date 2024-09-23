# OCI Security Health Check - Standard Edition

Owner: Olaf Heimburger

Version: 240930

Reviewed: 01.02.2024

# Introduction
![Flyer](./files/resources/OCI_Security_Health_Check_Standard.png)

[Download the flyer](./files/resources/OCI%20Security%20Health%20Check%20-%20Standard%20-%20Flyer.pdf)

## When to use this asset?

The *OCI Security Health Check - Standard Edition* checks an OCI tenancy for [CIS Oracle Cloud Infrastructure Foundations Benchmark](https://www.cisecurity.org/benchmark/Oracle_Cloud) compliance.

### Disclaimer

This asset covers the OCI platform as specified in the *CIS Oracle Cloud Infrastructure Foundations Benchmark*, only. Any workload provisioned in Databases, Compute VMs (running any Operating System), the Container Engine for Kubernetes, or in the VMware Solution is *out of scope* of the *OCI Security Health Check*.

## Complete Runtime Example

See the *OCI Security Health Check - Standard Edition* in action and watch the [OCI Health Checks - Self Service video](https://www.youtube.com/watch?v=EzjKLxfxaAM).

# Getting Started with the *OCI Security Health Check - Standard Edition*

## Download and verify the release file

Before running the *OCI Security Health Check - Standard Edition* you should download and verify it.

  - Download the latest distribution [oci-security-health-check-standard-240930.zip](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-240930.zip).
  - Download the respective checksum file:
    - [oci-security-health-check-standard-240930.sha512](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-240930.sha512).
    - [oci-security-health-check-standard-240930.sha512256](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-240930.sha512256).
  - Verify the integrity of the distribution. Both files must be in the same directory (for example, in your downloads directory).

    On MacOS:
    ```
    cd <your_downloads_directory>
    shasum -a 512256 -c oci-security-health-check-standard-240930.sha512256
    ```

    On Linux (including Cloud Shell):
    ```
    cd <your_downloads_directory>
    sha512sum -c oci-security-health-check-standard-240930.sha512
    ```

**Reject the downloaded file if the check fails!**

## Prepare the OCI Tenancy

### Single Run

You can run the assessment as a member of the OCI `Administrator` group or
create a group for auditing and assign the respective user to it.

Running the assessment script as an OCI `Administrator` is the easiest and
quickest way. If you decide to use this option, please continue reading in
[Run the OCI Security Health Check in Cloud Shell](files/oci-security-health-check-standard/README.md#run-the-oci-security-health-check-in-cloud-shell).

### Recurring usage

For recurring usage, setting up a group for auditing is recommended. For setting this up follow the steps documented next.

### Setting up an *Auditor* group and policy

Using an auditor group is the recommended way to run the assessment script.
To create a group for auditing do the following steps:

  - Log into OCI Console as OCI administrator.
  - In your Default domain create a group `grp-auditors`
  - Create a policy `pcy-auditing` with these statements (if your tenancy does not have Domains, replace `'Default'/'grp-auditors'` with `grp-auditors`):
    ```
      allow group 'Default'/'grp-auditors' to inspect all-resources in tenancy
      allow group 'Default'/'grp-auditors' to read instances in tenancy
      allow group 'Default'/'grp-auditors' to read load-balancers in tenancy
      allow group 'Default'/'grp-auditors' to read buckets in tenancy
      allow group 'Default'/'grp-auditors' to read nat-gateways in tenancy
      allow group 'Default'/'grp-auditors' to read public-ips in tenancy
      allow group 'Default'/'grp-auditors' to read file-family in tenancy
      allow group 'Default'/'grp-auditors' to read instance-configurations in tenancy
      allow group 'Default'/'grp-auditors' to read network-security-groups in tenancy
      allow group 'Default'/'grp-auditors' to read resource-availability in tenancy
      allow group 'Default'/'grp-auditors' to read audit-events in tenancy
      allow group 'Default'/'grp-auditors' to read users in tenancy
      allow group 'Default'/'grp-auditors' to read vss-family in tenancy
      allow group 'Default'/'grp-auditors' to read dns in tenancy
      allow group 'Default'/'grp-auditors' to use cloud-shell in tenancy
    ```
  - Assign a user to the `grp-auditors` group.
  - Log out of the OCI Console.

## Run the OCI Security Health Check in OCI Cloud Shell

For a detailed description go to [Run the OCI Security Health Check in OCI Cloud Shell](https://github.com/oracle-devrel/technology-engineering/blob/main/security/security-design/oci-security-health-check-standard/files/oci-security-health-check-standard/README.md#run-the-oci-security-health-check-in-cloud-shell)

## Sample Output

After a completed run you will find a directory with a name starting with your tenancy name followed by a timestamp in your working directory (like `tenancy_name_YYYYMMDDHHmmss_standard`). A zip archive for easier download using the same name will be created, too. Both hold data files for your review.

To start with reviewing the results, open the file named [cis_html_summary_report.html](files/resources/cis_html_summary_report.html) (sample report).

# Credits

The *OCI Security Health Check - Standard Edition* streamlines the usage of the bundled [Compliance Checking Script](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/blob/main/compliance-script.md) provided by the [CIS OCI Landing Zone Quick Start Template](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart).

The *OCI Security Health Check - Standard Edition* would not be possible without the great work of the [CIS OCI Landing Zone Quick Start Template Team](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/graphs/contributors).

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
