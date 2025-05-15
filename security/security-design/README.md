# Security Design

The Cloud Security Design Advisory team is covering end-to-end OCI security topics depending on customers' needs and requirements.
We are working closely with OCI Domain Specialists (networking, infrastructure security, data management, and observability), to provide the customer the best deep dive expertise, both on Cloud Security and Cloud Solutions.


Reviewed: 29.10.2024

# Table of Contents
 
1. [Team Publications](#team-publications)
3. [Reusable Assets Overview](#reusable-assets-overview)
2. [Useful Links](#useful-links)
   
# Team Publications

 
 
## Oracle Blogs

- [New Oracle Data Safe Reference Architectures to Quickly Secure Your Databases](https://blogs.oracle.com/cloudsecurity/post/oracle-data-safe-architectures-to-quickly-secure-your-databases)
    - Are you concerned about data safety and security? Whether it’s your customers’ or employees’ data, Oracle Database customers can help reduce the risk of a data breach and simplify compliance by using Oracle Data Safe.
      
## OCI Architecture Center
 
- [Connect Oracle Data Safe to Exadata and Autonomous Databases](https://docs.oracle.com/en/solutions/data-safe-exadata-adb/index.html)
    - This reference architecture highlights the different ways you can connect Exadata and Autonomous databases to Oracle Data Safe. It also describes the security measures you need to take to provide a safe deployment of a connection to a specific target database.
 - [Connect Oracle Data Safe to Oracle Databases on multicloud and hybrid cloud environments](https://docs.oracle.com/en/solutions/data-safe-multicloud-ods-hybrid/index.html)
     - This reference architecture highlights the different ways you can connect multicloud environments and Oracle Database Service for Azure to Oracle Data Safe. It also describes the security measures you need to take to provide a safe deployment of a connection to a specific target.
 - [Implement Oracle Data Safe for your on-premises and OCI deployed databases](https://docs.oracle.com/en/solutions/data-safe-on-oci-onprem/index.html) 
      - This reference architecture highlights the different ways you can connect target databases to Oracle Data Safe. It also describes the security measures you need to take to provide a safe deployment of a connection to a specific target database. 
 
## Cloud Coaching Webinars

- [OCI Cloud Security Posture Management - Prevention and Remediation](https://www.youtube.com/watch?v=zDJeS3ZPvTo)
     - In this session, you will see how to implement best practices for a strong and secure cloud environment including your containers, virtual machines, and databases.
- [Managing Identities across OCI IAM, Azure AD and Oracle SaaS](https://www.youtube.com/watch?v=9dFj9rePOuc)
     - This session will cover the details of how to enable Single Sign On (SSO) between OCI IAM and Microsoft Azure Active Directory (Azure AD), Oracle Fusion Apps, and Databases.
       
# Reusable Assets Overview

- [Bastion Session Script](shared-assets/bastion-session-script/README.md)
- [OCI Security Health Check Standard](shared-assets/oci-security-health-check-standard/README.md)
- [Data Safe Audit Database to OCI Logging](shared-assets/fn-datasafe-dbaudit-to-oci-logging/README.md)
- [Importing your own key into OCI Vault](shared-assets/kms-import-keys/README.md)
- [OCI IAM SDK Example](shared-assets/iam-py-sdk/README.md)
- [Setting up IP-based TLS certificates on OCI Load Balancer](shared-assets/zerossl-lb-test-certificate-setup/README.md)
- [Bastion Session Script, Python SDK version](shared-assets/bastion-py-script/README.md)      
- [Bypassing MFA for Service Accounts for specific applications](shared-assets/iam-mfa-bypass-svc-accts/README.md)
      
# Useful Links
 
 - [Oracle Security](https://www.oracle.com/security/)
 - Protect your most valuable data in the cloud and on-premises with Oracle’s security-first approach. Oracle has decades of experience securing data and applications; Oracle Cloud Infrastructure delivers a more secure cloud to our customers, building trust and protecting their most valuable data.
 - [Oracle Cloud Compliance](https://www.oracle.com/corporate/cloud-compliance/)
     - Oracle is committed to helping customers operate globally in a fast-changing business environment and address the challenges of an ever more complex regulatory environment.
 - [Security in OCI - OCI Best Practices for security adoption](https://www.oracle.com/cloud/oci-best-practices-guide/#security-on-oci)
 - [Security Checklist for OCI](https://docs.oracle.com/en/solutions/oci-security-checklist/#GUID-D27BD123-8CFB-49A4-84AF-3546022638CE)
 - [Zero Trust Security Model](https://www.oracle.com/security/what-is-zero-trust/)
 - [Cloud Security Documentation](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security.htm#Security_Guide_and_Announcements)
 - [OCI Architecture Center](https://www.oracle.com/uk/cloud/architecture-center/)
 - [Integrate APEX with OCI IAM Domains](https://docs.oracle.com/en/learn/apex-identitydomains-sso/index.html#task-4-create-a-new-authentication-scheme-in-oracle-apex-for-the-sample-application)
     - Oracle APEX is the premier low code tool. With Oracle OCI IAM you can add proper governance to user management and authorization governance though OCI IAM groups mapped to APEX roles. Since APEX is using OAUTH for integration with Oracle OCI IAM, users is not required to managed within APEX, only user and group assignments to users is managed in APEX. If you want to manage user profile within APEX, this can easily be added by adding a post. In the post below, step 7 and 8 gives one example of how a post authentication function can be built. This can be extended to use REST to retrieve additional attributes from OCI IAM Domains, or more common use case, create a local user profile in a local table, if a local user profile does not exist for the current user. The elegant piece, is that the OCI IAM Domain integration provides username and authorization available though standard APEX API for later usage in your code
The link above details how to integrate APEX with OCI IAM Domain, utilizing OAUTH, and then leave the user governance entirely to OCI IAM Domains.


# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

