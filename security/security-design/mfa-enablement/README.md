# OCI Multi-factor Authentication Enablement

Multi-factor Authentication (MFA) for OCI is enforced for each OCI tenancy in July/August 2023. These changes should apply to any instance of [OCI Identity Domains](https://docs.oracle.com/en-us/iaas/Content/Identity/home.htm) or [Identity Cloud Service](https://docs.oracle.com/en/cloud/paas/identity-cloud/) and their respective non-federated users.

This video explains how to find, verify, and use the implemented changes.

[Watch the video](files/OCI_IAM_MFA_Enforcement.mp4).

## Notification Email

Every customer will be informed by an Email explaining the changes for the instances in use and at which date these changes apply to the respective tenancy.

### What if I use Federation and MFA for local users already?

Nothing, the current configuration will not be impacted.

### What if I don't change anything?

When the OCI Administrators do find any time to enable (activate) Multi-factor Authentication before the date mentioned in the Email, the changes will be actived automatically.

## More information

All changes, their configurations, and the impact for OCI Identity Domains and Identity CLoud Service are fully documented in the [OCI Security Guide for IAM MFA](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security_topic-IAM_MFA.htm).


# License

Copyright &copy; 2023 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
