# OCI Security Health Check - Standard Edition

Owner: Olaf Heimburger

Version: 260105 (cis_report.py version 3.1.1.1) for CIS OCI Foundation Benchmark 3.0.0

## When to use this asset?

The *OCI Security Health Check - Standard Edition* checks an OCI tenancy for CIS OCI Foundation Benchmark compliance.

### Disclaimer

This asset covers the OCI platform as specified in the *CIS Oracle Cloud Infrastructure Foundations Benchmark*, only. Any workload provisioned in Databases, Compute VMs (running any Operating System), the Container Engine for Kubernetes, or in the VMware Solution is *out of scope* of the *OCI Security Health Check*.

**This is not an official Oracle application and it is not supported by Oracle Support.**

## Before you begin

The main goals of this script are:

- Make the run as easy and smooth as possible.
- Do not affect your desktop whenever possible.
- **For a successful run, this script requires an Internet connection.**

## Benefits of this package

This package includes *two* files
- standard.sh
- scripts/cis_reports/cis_reports.py

The file standard.sh acts as the entry point and does the following:

- Automatic check for Python runtime version
- Automatic venv creation and activation
- Automatic installation of required Python libraries
- Automatic **OCI Cloud Shell** and tenancy name detection
- Automatic creation of timestamped output directory
- Call of cis_reports.py
- Automatic output archive (ZIP file) creation
- Automatic runtime protocol
- Support for encrypted archive (ZIP file). New command line option `--zip-protect`.

Tested on **OCI Cloud Shell** with **Public network**, **Oracle Linux**, **MacOS 12** and higher.

## Usage

### Download and verify the release file

Before running the *OCI Security Health Check - Standard Edition* you should download and verify it.

  - Download the latest distribution [oci-security-health-check-standard-260105.zip](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-260105.zip).
  - Download the respective checksum file:
    - [oci-security-health-check-standard-260105.sha512](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-260105.sha512).
    - [oci-security-health-check-standard-260105.sha512256](https://github.com/oracle-devrel/technology-engineering/raw/main/security/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-260105.sha512256).
  - Verify the integrity of the distribution. Both files must be in the same directory (for example, in your downloads directory).

    On MacOS:
    ```
    cd <your_downloads_directory>
    shasum -a 512256 -c oci-security-health-check-standard-260105.sha512256
    ```

    On Linux (including Cloud Shell):
    ```
    cd <your_downloads_directory>
    sha512sum -c oci-security-health-check-standard-260105.sha512
    ```

**Reject the downloaded file when the check fails!**

### Prepare the OCI Tenancy

You can run the assessment as a member of the OCI `Administrator` group or
create a group for auditing and assign the respective user to it.

Running the assessment script as an OCI `Administrator` is the easiest and
quickest way. If you decide to use this option, please continue reading in
[Run the OCI Security Health Check in Cloud Shell](#run-the-oci-security-health-check-in-cloud-shell).

For recurring usage, setting up a group for auditing is recommended. The
steps for setting this up are described in the next chapter.

#### Setting up an *Auditor* group and related permissions

Using an auditor group is the recommended way to run the assessment script.
To create a group for auditing do the following steps:

  - Check whether your tenancy is still not migrated to Identity Domains:
    - Login to OCI Console as OCI administrator
    - Select "Identity & Security"
    - If "Domains" are listed you are migrated to Identity Domains
  - Create a group `grp-auditors`
  - Create a policy `pcy-auditing` with these statements:
    - For tenancies **with** Identity Domains use
      ```
      allow group 'Default'/'grp-auditors' to inspect all-resources in tenancy
      allow group 'Default'/'grp-auditors' to read audit-events in tenancy
      allow group 'Default'/'grp-auditors' to read buckets in tenancy
      allow group 'Default'/'grp-auditors' to read capture-filters in tenancy
      allow group 'Default'/'grp-auditors' to read data-safe-family in tenancy
      allow group 'Default'/'grp-auditors' to read domains in tenancy
      allow group 'Default'/'grp-auditors' to read file-family in tenancy
      allow group 'Default'/'grp-auditors' to read instance-configurations in tenancy
      allow group 'Default'/'grp-auditors' to read instances in tenancy
      allow group 'Default'/'grp-auditors' to read keys in tenancy
      allow group 'Default'/'grp-auditors' to read load-balancers in tenancy
      allow group 'Default'/'grp-auditors' to read logging-family in tenancy
      allow group 'Default'/'grp-auditors' to read nat-gateways in tenancy
      allow group 'Default'/'grp-auditors' to read network-security-groups in tenancy
      allow group 'Default'/'grp-auditors' to read public-ips in tenancy
      allow group 'Default'/'grp-auditors' to read resource-availability in tenancy
      allow group 'Default'/'grp-auditors' to read tag-namespaces in tenancy
      allow group 'Default'/'grp-auditors' to read usage-budgets in tenancy
      allow group 'Default'/'grp-auditors' to read usage-reports in tenancy
      allow group 'Default'/'grp-auditors' to read users in tenancy
      allow group 'Default'/'grp-auditors' to read vaults in tenancy
      allow group 'Default'/'grp-auditors' to read vss-family in tenancy
      allow group 'Default'/'grp-auditors' to use cloud-shell in tenancy
      allow group 'Default'/'grp-auditors' to use cloud-shell-public-network in tenancy
      allow group 'Default'/'grp-auditors' to use ons-family in tenancy where any {request.operation!=/Create*/, request.operation!=/Update*/, request.operation!=/Delete*/, request.operation!=/Change*/}

      ```
    - For tenancies **without** Identity Domains use
      ```
      allow group grp-auditors to inspect all-resources in tenancy
      allow group grp-auditors to read audit-events in tenancy
      allow group grp-auditors to read buckets in tenancy
      allow group grp-auditors to read capture-filters in tenancy
      allow group grp-auditors to read data-safe-family in tenancy
      allow group grp-auditors to read domains in tenancy
      allow group grp-auditors to read file-family in tenancy
      allow group grp-auditors to read instance-configurations in tenancy
      allow group grp-auditors to read instances in tenancy
      allow group grp-auditors to read keys in tenancy
      allow group grp-auditors to read load-balancers in tenancy
      allow group grp-auditors to read logging-family in tenancy
      allow group grp-auditors to read nat-gateways in tenancy
      allow group grp-auditors to read network-security-groups in tenancy
      allow group grp-auditors to read public-ips in tenancy
      allow group grp-auditors to read resource-availability in tenancy
      allow group grp-auditors to read tag-namespaces in tenancy
      allow group grp-auditors to read usage-budgets in tenancy
      allow group grp-auditors to read usage-reports in tenancy
      allow group grp-auditors to read users in tenancy
      allow group grp-auditors to read vaults in tenancy
      allow group grp-auditors to read vss-family in tenancy
      allow group grp-auditors to use cloud-shell in tenancy
      allow group grp-auditors to use cloud-shell-public-network in tenancy
      allow group grp-auditors to use ons-family in tenancy where any {request.operation!=/Create*/, request.operation!=/Update*/, request.operation!=/Delete*/, request.operation!=/Change*/}
      ```
  - Assign a user to the `grp-auditors` group
  - Log out of the OCI Console

### <a name="run_cloud_shell"></a>Run the OCI Security Health Check in OCI Cloud Shell

The recommended way is to run the *OCI Security Health Check - Standard* in the [OCI Cloud Shell](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellintro.htm). It does not require any additional configuration on a local desktop machine.

#### Required IAM Policy statements

The following policy statement is part of the recommended policy statements for the `grp-auditors` group, for example:
```
allow group 'Default'/'grp-auditors' to use cloud-shell in tenancy
allow group 'Default'/'grp-auditors' to use cloud-shell-public-network in tenancy
```

#### Networking Options for OCI Cloud Shell

OCI Cloud Shell sessions do not allow for any incoming connections, and there is no public IP address available.

So far, the *OCI Security Health Check - Standard Edition* in OCI Cloud Shell has been tested with Public Network Access only.

For details on OCI Cloud Shell Networking refer to [OCI Cloud Shell Networking](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellintro_topic-Cloud_Shell_Networking.htm#cloudshellintro_topic-Cloud_Shell_Networking) documentation.

<!--
##### Public Network Access

The best networking option. When enabled the *OCI Security Health Check - Standard* can be run without any additional conifguration steps. To enable this option the following policy statement must be assigned to the `grp-auditors`:

```
allow group 'Default'/'grp-auditors' to use cloud-shell-public-network in tenancy
```

##### OCI Service Network Access

The default networking option for OCI Cloud Shell. 

To use this option without access to the public Internet remove any presence of this policy statement:

```
allow group ... to use cloud-shell-public-network in tenancy
```

This option requires manual configuration of these Python libraries:
- [xlsxwriter]()
- [pytz]()
- [pandas]()
- [openpyxl]()
- [pyyaml]()
- [requests]()

For each library these steps need to done:

- Download the packages
- Upload the packages
- Unzip the packages
- Install the packages

##### Private Network Access

```
allow group 'Default'/'grp-auditors' to use subnets in compartment <compartment>
allow group 'Default'/'grp-auditors' to use vnics in compartment <compartment>
allow group 'Default'/'grp-auditors' to use network-security-groups in compartment <compartment>
allow group 'Default'/'grp-auditors' to inspect vcns in compartment <compartment>
```
-->


#### Upload the release file

  - Log into the OCI Console.
  - Select the *Developer Tools* icon (looks like a small window) in the header toolbar.
  - From the menu select the *Cloud Shell* item.
  - Wait until the Cloud Shell has been initialized.
  - On the green tool bar click on the *Settings* icon and select the *Upload ...* menu item.
  - Upload the distribution file.
  - Extract it
    ```
    unzip -q oci-security-health-check-standard-260105.zip
    ```

#### Run the script
  - Change directory into `oci-security-health-check-standard`:
    ```
    $ cd oci-security-health-check-standard
    ```
  - In the `oci-security-health-check-standard` directory:
    - Enable execution of script `standard.sh`:
      ```
      chmod +x standard.sh
      ```
    - Run the script for all subscribed regions:
      ```
      ./standard.sh
      ```
    - Run the script for one subscribed region:
      ```
      ./standard.sh -r <region_name>
      ```
    - Get command line options:
      ```
      ./standard.sh -h
      ```

### Using an OCI Compute VM (Oracle Linux)

  - Create a Dynamic Group
    `'Default'/'dgp-instance-principal'`

    This dynamic group must specify the compartment OCID (`resource.compartment.id`) or the Compute VM OCID (`resource.instance.id`), respectively.
  - Create permissions for the Dynamic Group
      ```
      allow dynamic-group 'Default'/'dgp-instance-principal' to inspect all-resources in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read audit-events in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read buckets in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read capture-filters in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read data-safe-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read domains in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read file-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read instance-configurations in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read instances in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read keys in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read load-balancers in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read logging-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read nat-gateways in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read network-security-groups in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read public-ips in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read resource-availability in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read tag-namespaces in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read usage-budgets in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read usage-reports in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read users in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read vaults in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read vss-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to use cloud-shell in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to use cloud-shell-public-network in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to use ons-family in tenancy where any {request.operation!=/Create*/, request.operation!=/Update*/, request.operation!=/Delete*/, request.operation!=/Change*/}
      ```
  - Preparing the Compute VM:
    - Log into the Compute VM
    - Make sure that Python 3 is installed:
      ```
      sudo yum list python39
      ```
    - If Python 3 is missing, install it:
      ```
      sudo yum install python39 -y
      ```
    - Update the link of python3 to /usr/bin/python3.9
      ```
      sudo alternatives --config python3
      ```
      Follow the instructions to select /usr/bin/python3.9
    - Log out

  - From your desktop, upload the `oci-security-health-check-standard-260105.zip` file to the Compute VM using any SFTP client.
  - Log into the Compute VM
    - Extract the distribution
      ```
      unzip -q oci-security-health-check-standard-260105.zip
      ```
    - Change directory into `oci-security-health-check-standard`:
      ```
      cd oci-security-health-check-standard
      ```
    - Enable execution of script `standard.sh`:
      ```
      chmod +x standard.sh
      ```
    - In the `oci-security-health-check-standard` directory run the assess.sh
      script.
      - Start the `screen` program:
        ```
        screen
        ```

      - Run the script for all subscribed regions:
        ```
        ./standard.sh -ip -t <tenancy_name>
        ```
      - Run the script for one subscribed region, only:
        ```
        ./standard.sh -ip -t <tenancy_name> -r <region_name>
        ```
      - Get command line options:
        ```
        ./standard.sh -h
        ```
      - When your Compute VM session has been ended due to inactivity you can
        resume without starting the script again.

        To resume the screen session, follow these steps
        (the output will be different in your *Compute VM*):
        - Connect to your *Compute VM* again.
          ```
          screen -ls
            1234.text
          screen -d 1234
          screen -r 1234
          ```

### Getting the results
  - In the directory `oci-security-health-check-standard` a directory will be created which
    holds all the output created by the scripts. This directory will be
    compressed in a single ZIP file and the resulting ZIP file will be moved to
    the parent directory of `oci-security-health-check-standard`.

### Checking the results

The report results are showing the compliance status of the related [CIS OCI Foundation Benchmark, version 2.0](https://www.cisecurity.org/benchmark/Oracle_Cloud) recommendations. Please download this benchmark before reading the report. (For license reasons, we cannot distribute the benchmark.)

The report results are summarized in two files:
- *cis_html_summary_report.html* &ndash; The report in HTML that displays the all recommendations and their compliance status, respectively.
- *Consolidated_Report.xslx* &ndash; An XSLX workbook with a summary and sheets for the non-compliant recommendations.

## Known Issues

1. Python 3.8 is not supported anymore.
   OCI Cloud Shell is the minimal required environment. The Python version used in OCI Cloud Shell is 3.9.
2. Diagrams are not part of the HTML page.
   This may be because of broken `numpy installation`. The following command should resolve this:
   `pip3 install --upgrade --force-reinstall --user numpy`

## Credits

The *OCI Security Health Check - Standard Edition* streamlines the usage of the [CIS Compliance Script](https://github.com/oci-landing-zones/oci-cis-landingzone-quickstart/blob/main/README.md).

The *OCI Security Health Check - Standard Edition* would not be possible without the great work of the [CIS OCI Landing Zone Quick Start Template Team](https://github.com/oci-landing-zones/oci-cis-landingzone-quickstart/graphs/contributors).

## Certification

The CIS Compliance Script has been certified by the [CIS Center of Internet Security for the OCI Oracle Cloud Foundation Benchmark v3.0.0, Level 1 and 2](https://www.cisecurity.org/partner/oracle).

## License

Copyright (c) 2022-2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.

