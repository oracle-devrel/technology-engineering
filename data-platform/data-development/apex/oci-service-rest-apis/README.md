# Development & Operations (DevOps) for the Database and APEX
Reviewed: "`17.11.2023"

## The development lifecycle is the process of periodically: (Development)
- Selecting a set of bugs and features that will improve your app
- Dividing up the work among teammates,and
- Testing the result before releasing it to end users

## Every development team's goal: (Operations)
- Steady,incremental progress against prioritized list of issues and ideas
- Delivering a fewchange requests at a time to end users
- Through a series of high-quality releases on a regular cadence

# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Reusable Assets Overview](#reusable-assets-overview)
 
# Team Publications
-  TBD
 
# Useful Links
- [Oracle Documentation - Document Understanding API](https://docs.oracle.com/en-us/iaas/api/#/en/document-understanding/20221109/)
    - Document AI helps customers perform various analysis on their documents.
- [Oracle Documentation - Vision API](https://docs.oracle.com/en-us/iaas/api/#/en/vision/20220125/)
    - Vision AI allows customers to detect and classify objects in uploaded images.

# Reusable Assets Overview
- [Sample REST Data Catalog](./sample-rest-catalog)
    - [REST Catalog - OCI Document Understanding](./sample-rest-catalog/rest-catalog-document-understanding-api.sql)
    - [REST Catalog - OCI Vision](./sample-rest-catalog/rest-catalog-vision-api.sql)

## USAGE: Sample REST Data Catalog
### Setup and Prerequisites
- [Oracle Documentation - Developers Guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/devguidesetupprereq.htm "Setting User with Required Keys and OCIDs")

### Import the REST Catalog into the APEX Workspace
- From the relevant application
    - [] Navigate to REST Data Sources *from Shared Components*
    - [] Createa a new REST Data Source *from a REST Source Catalog*
    - [] Use the *+* to select the REST Data Source and click *Next*
    - [] Select *Create New* from the Credentials field

### Create a new Web Credential
    - Provide
        - [] Name
        - [] Static ID
        - [] Authentication Type => *Oracle Cloud Infrastructure (OCI)*
        - [] OCI User ID => *OCI User OCID*
        - [] OCI Private Key => *Entire contents Private Key associated with the uploaded Public PEM file in the User's API Keys*
        - [] OCI Tenancy ID => *OCI Tenant OCID*
        - [] OCI Public Key Fingerprint => *Fingerprint of the uploaded Public Key PEM file in the User's API Keys*


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
