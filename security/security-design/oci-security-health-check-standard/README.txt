
OCI Security Health Check - Standard Edition
============================================
Owner: Olaf Heimburger

When to use this asset?

The OCI Security Health Check - Standard Edition checks an OCI tenancy for
CIS OCI Foundation Benchmark compliance.

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
  Using an auditor group is the recommended way to run the assessment script.
  To create a group for auditing do the following steps:

  - Log into OCI Console as OCI administrator
  - Create a group grp-auditors
  - Create a policy pcy-auditing with these statements:
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
  - Assign a user to the grp-auditors group
  - Log out of OCI Console

2 Using the Cloud Shell
  - Log into the OCI Console
  - Select the Developer Tools icon (looks like a small window).
  - From the menu select the Cloud Shell item.
  - When running it the first time:
    - Upload the provided ZIP file.
    - Extract it with unzip -q oci-security-health-check-standard-<version>.zip
  - Change directory into oci-security-health-check-standard-<version>
    $ cd oci-security-health-check-standard-<version>
    $ screen
  - In the oci-security-health-check-standard-<version> directory run the standard.sh
    script.
    - Run the script for all subscribed regions:
      $ ./standard.sh
    - Run the script for one subscribed region:
      $ ./standard.sh -r <region_name>
    - Get command line options:
      $ ./standard.sh -h

3 Gathering the results
  - In the directory oci-security-health-check-standard-<version> a directory will be created which
    holds all the output created by the scripts. This directory will be
    compressed in a single ZIP file and the resulting ZIP file will be moved to
    the home directory of the account running the script.
