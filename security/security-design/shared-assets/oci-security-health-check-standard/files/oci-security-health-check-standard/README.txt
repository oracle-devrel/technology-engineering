
OCI Security Health Check - Standard Edition
============================================
Owner: Olaf Heimburger
Version: 240930 (cis_report.py version 2.8.4+)

When to use this asset?

The OCI Security Health Check - Standard Edition checks an OCI tenancy for
CIS OCI Foundation Benchmark compliance.

Disclaimer

This asset covers the OCI platform as specified in the "CIS Oracle Cloud
Infrastructure Foundations Benchmark", only. Any workload provisioned in
Databases, Compute VMs (running any Operating System), the Container Engine for
Kubernetes, the VMware Solution, etc. is "out of scope" of the
"OCI Security Health Check - Standard Edition".

This is not an official Oracle application and it is not supported
by Oracle Support.

Usage

1 Prepare the OCI Tenancy
  You can run the assessment as a member of the OCI Administrator group or
  create a group for auditing and assign the respective user to it.

  Running the assessment script as an OCI Administrator is the easiest and
  quickest way. If you decide to use this option, please continue reading 
  chapter 2.

  For recurring usage, setting up a group for auditing is recommended. The
  steps for setting this up are described in the next chapter.

1.1 Setup an Auditor group and policy
  - Check whether your tenancy is still not migrated to Identity Domains:
  - Login to OCI Console as OCI Administrator
    - Select "Identity & Security"
    - If "Domains" are listed you are migrated to Identity Domains
  - Create a group grp-auditors
  - Create a policy pcy-auditing with these statements:
  - For tenancies without Identity Domains use
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
  - For tenancies *with* Identity Domains use
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
  - Assign a user to the grp-auditors group
  - Log out of OCI Console

2 Using the Cloud Shell
  - Log into the OCI Console
  - Select the Developer Tools icon (looks like a small window).
  - From the menu select the Cloud Shell item.
  - When running it the first time:
    - Upload the provided ZIP file.
    - Extract it with unzip -q oci-security-health-check-standard-240930.zip
  - Change directory into oci-security-health-check-standard
    $ cd oci-security-health-check-standard
    $ screen
  - In the oci-security-health-check-standard directory run the standard.sh
    script.
    - Run the script for all subscribed regions:
      $ ./standard.sh
    - Run the script for one subscribed region:
      $ ./standard.sh -r <region_name>
    - Get command line options:
      $ ./standard.sh -h

### Using an OCI Compute VM (Oracle Linux)

  - Create a Dynamic Group
    'Default'/'dgp-instance-principal'
    This dynamic group must specify the compartment OCID (resource.compartment.id) or the Compute VM OCID (resource.instance.id), respectively.
  - Create permissions for the Dynamic Group
      allow dynamic-group 'Default'/'dgp-instance-principal' to inspect all-resources in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read audit-events in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read buckets in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read cloudevents-rules in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read dns in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read domains in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read file-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read instances in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read instance-configurations in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read keys in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read load-balancers in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read nat-gateways in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read network-security-groups in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read osms-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read public-ips in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read resource-availability in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read serviceconnectors in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read stream-family in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read users in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read vault in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read vlans in tenancy
      allow dynamic-group 'Default'/'dgp-instance-principal' to read vss-family in tenancy

  - Preparing the Compute VM:
    - Log into the Compute VM
    - Make sure that Python 3.9 is installed:
      sudo yum list python39

    - If Python 3.9 is missing, install it:
      sudo yum install python39 -y

    - Update the link of python3 to /usr/bin/python3.9
      sudo alternatives --config python3

      Follow the instructions to select /usr/bin/python3.9
    - Log out

  - From your desktop, upload the
    "oci-security-health-check-standard-240930.zip" file to the Compute VM
    using any SFTP client.
  - Log into the Compute VM
    - Extract the distribution
      unzip -q oci-security-health-check-standard-240930.zip

    - Change directory into "oci-security-health-check-standard":
      cd oci-security-health-check-standard

    - Enable execution of script "standard.sh":
      chmod +x standard.sh

    - In the "oci-security-health-check-standard" directory run the assess.sh
      script.
      - Start the "screen" program:
        screen

      - Run the script for all subscribed regions:
        ./standard.sh -ip -t <tenancy_name>

      - Run the script for one subscribed region, only:
        ./standard.sh -ip -t <tenancy_name> -r <region_name>

      - Get command line options:
        ./standard.sh -h

      - When your Compute VM session has been ended due to inactivity you can
        resume without starting the script again.

3 Gathering the results
  - In the directory oci-security-health-check-standard a directory will be
    created which holds all the output created by the scripts. This directory
    will be compressed in a single ZIP file and the resulting ZIP file will be
    moved to the home directory of the account running the script.

4 Checking the results
  The report results are showing the compliance status of the related
  "CIS OCI Foundation Benchmark, version 2.0"
  (https://www.cisecurity.org/benchmark/Oracle_Cloud) recommendations.

  Please download this benchmark before reading the report.
  (For license reasons, we cannot distribute the benchmark.)

  The report results are summarized in two files:
  - "cis_html_summary_report.html" -- The report in HTML that displays the all
                                      recommendations and their compliance
                                      status, respectively.
  - "Consolidated_Report.xslx" -- An XSLX workbook with a summary and sheets
                                  for the non-compliant recommendations.

5 Known Issues

No known issues.

6 Credits

The "OCI Security Health Check - Standard Edition" streamlines the usage of
the Compliance Checking Script
(https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/blob/main/compliance-script.md) bundled with the CIS OCI Landing Zone Quick Start Template
(https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart).

The "OCI Security Health Check - Standard Edition" would not be possible
without the great work of the CIS OCI Landing Zone Quick Start Template Team
(https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart/graphs/contributors).

Certification

The Compliance Checking Script is certified by the Center of Internet Security
(CIS) for the OCI Oracle Cloud Foundation Benchmark v1.2, Level 1 and 2
(https://www.cisecurity.org/partner/oracle).

License

Copyright (c) 2022-2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See the LICENSE file for more details.
