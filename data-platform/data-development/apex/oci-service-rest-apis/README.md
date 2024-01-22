# Integrating with OCI Cloud Services
Reviewed: "17.11.2023"

REST APIs are used to integrate with OCI Cloud Services from APEX. understanding the nuances of the APIs and OCI authentication can be somewhat complex. The main challenge in our experience has been translating Documentation into Implementation.

To simplfy the creation of the REST Data Sources, we are assembling REST Source arctifacts into a Catalog as we gain experience using the APIs ourselves.

Hopefully, this will simplfy your project implementations as you work with these services.

The first set of samples will provide REST Data Sources for the OCI Document Understanding and Vision services.

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
