# OCI Security Health Check - Standard Edition

Owner: Olaf Heimburger

## When to use this asset?

The *OCI Security Health Check - Standard Edition* checks an OCI tenancy for CIS OCI Foundation Benchmark compliance.

## Usage

### Download and verify the release file

Before running the *OCI Security Health Check - Standard Edition* you should download and verify it.

  - Download the latest distribution [oci-security-health-check-standard-230630.zip](https://github.com/oracle-devrel/technology-engineering/releases/download/oci-security-health-check-std-230630/oci-security-health-check-standard-230630.zip).
  - Download the respective checksum file:
    - [oci-security-health-check-standard-230630.sha512](https://github.com/oracle-devrel/technology-engineering/releases/download/oci-security-health-check-std-230630/oci-security-health-check-standard-230630.sha512).
    - [oci-security-health-check-standard-230630.sha512256](https://github.com/oracle-devrel/technology-engineering/releases/download/oci-security-health-check-std-230630/oci-security-health-check-standard-230630.sha512256).
  - Verify the integrity of the distribution. Both files must be in the same directory (for example, in your downloads directory).

    On MacOS:
    ```
    $ cd <your_downloads_directory>
    $ shasum -a 512256 -c oci-security-health-check-standard-230630.sha512256
    oci-security-health-check-standard-230630.zip: OK
    ```

    On Linux (including Cloud Shell):
    ```
    $ cd <your_downloads_directory>
    $ sha512sum -c oci-security-health-check-standard-230630.sha512
    oci-security-health-check-standard-230630.zip: OK
    ```

**Reject the downloaded file if the check fails!**

### Prepare the OCI Tenancy

You can run the assessment as a member of the OCI `Administrator` group or
create a group for auditing and assign the respective user to it.

Running the assessment script as an OCI `Administrator` is the easiest and
quickest way. If you decide to use this option, please continue reading in
[Run the OCI Security Health Check in Cloud Shell](#run-the-oci-security-health-check-in-cloud-shell).

For recurring usage, setting up a group for auditing is recommended. The
steps for setting this up are described in the next chapter.

#### Setting up an *Auditor* group and policy

Using an auditor group is the recommended way to run the assessment script.
To create a group for auditing do the following steps:

  - Log into OCI Console as OCI administrator
  - Create a group `grp-auditors`
  - Create a policy `pcy-auditing` with these statements:
    ```
    allow group grp-auditors to inspect all-resources in tenancy
    allow group grp-auditors to read instances in tenancy
    allow group grp-auditors to read load-balancers in tenancy
    allow group grp-auditors to read buckets in tenancy
    allow group grp-auditors to read nat-gateways in tenancy
    allow group grp-auditors to read public-ips in tenancy
    allow group grp-auditors to read file-family in tenancy
    allow group grp-auditors to read instance-configurations in tenancy
    allow group grp-auditors to read network-security-groups in tenancy
    allow group grp-auditors to read resource-availability in tenancy
    allow group grp-auditors to read audit-events in tenancy
    allow group grp-auditors to read users in tenancy
    allow group grp-auditors to read vss-family in tenancy
    allow group grp-auditors to read dns in tenancy
    allow group grp-auditors to use cloud-shell in tenancy
    ```
  - Assign a user to the `grp-auditors` group
  - Log out of the OCI Console

### Run the OCI Security Health Check in OCI Cloud Shell

The recommended way is to run the *OCI Security Health Check - Standard* in the OCI Cloud Shell. It does not require any additional configuration on a local desktop machine.

#### Upload the release file

  - Log into the OCI Console.
  - Select the *Developer Tools* icon (looks like a small window) in the header toolbar.
  - From the menu select the *Cloud Shell* item.
  - Wait until the Cloud Shell has been initialized.
  - On the green tool bar click on the *Settings* icon and select the *Upload ...* menu item.
  - Upload the distribution file.
  - Extract it
    ```
    $ unzip -q oci-security-health-check-standard-230630.zip
    ```

### Run the script
  - Change directory into `oci-security-health-check-standard`:
    ```
    $ cd oci-security-health-check-standard
    ```
  - In the `oci-security-health-check-standard` directory:
    - Enable execution of script `standard.sh`:
      ```
      $ chmod +x standard.sh
      ```
    - Run the script for all subscribed regions:
      ```
      $ ./standard.sh
      ```
    - Run the script for one subscribed region:
      ```
      $ ./standard.sh -r <region_name>
      ```
    - Get command line options:
      ```
      $ ./standard.sh -h
      ```

### Getting the results
  - In the directory `oci-security-health-check-standard` a directory will be created which
    holds all the output created by the scripts. This directory will be
    compressed in a single ZIP file and the resulting ZIP file will be moved to
    the parent directory of `oci-security-health-check-standard`.

### Checking the results

The report results are showing the compliance status of the related [CIS OCI Foundation Benchmark, version 1.2](https://www.cisecurity.org/benchmark/Oracle_Cloud) recommendations. Please download this benchmark before reading the report. (For license reasons, we cannot distribute the benchmark.)

The report results are summarized in two files:
- *cis_html_summary_report.html* &ndash; The report in HTML that displays all recommendations and their compliance status, respectively.
- *Consolidated_Report.xslx* &ndash; An XSLX workbook with a summary and sheets for the non-compliant recommendations.

## Credits

The *OCI Security Health Check - Standard Edition* streamlines the usage of the bundled [Compliance Checking Script](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/blob/main/compliance-script.md) provided by the [CIS OCI Landing Zone Quick Start Template](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart).

The *OCI Security Health Check - Standard Edition* would not be possible without the great work of the [CIS OCI Landing Zone Quick Start Template Team](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/graphs/contributors).

# License

Copyright (c) 2022-2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
