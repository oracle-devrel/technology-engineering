# Integrating with OCI Cloud Services

REST APIs are used to integrate with OCI Cloud Services from APEX. Understanding the nuances of the APIs and OCI authentication can be somewhat complex. The main challenge in our experience has been translating Documentation into Implementation.

To simplify the creation of the REST Data Sources, we are assembling REST Source artifacts into a Catalog as we gain experience using the APIs ourselves.

Hopefully, this will simplify your project implementations as you work with these services.

The first set of samples will provide REST Data Sources for the OCI Document Understanding and Vision services.

Reviewed: 08.02.2024
 
# When to use this asset?

To learn how to integrate OCI REST API's to APEX.

# How to use this asset?

## USAGE: Sample REST Data Catalog

### Setup and Prerequisites

- [Oracle Documentation - Developers Guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/devguidesetupprereq.htm "Setting User with Required Keys and OCIDs")

### Import the REST Catalog into the APEX Workspace

    - From the relevant application
        - [] Navigate to REST Data Sources *from Shared Components*
        - [] Create a new REST Data Source *from a REST Source Catalog*
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

# Team Publications

-  [Interacting with OCI REST APIs in APEX — Empty POST Request](https://medium.com/@devpiotrekk/interacting-with-oci-rest-apis-in-apex-empty-post-request-ce270d15cbb6 "Tip: Submitting Empty Body")
 
# Useful Links
- [Oracle Documentation - Document Understanding API](https://docs.oracle.com/en-us/iaas/api/#/en/document-understanding/20221109/)
    - Document AI helps customers perform various analyses on their documents.
- [Oracle Documentation - Vision API](https://docs.oracle.com/en-us/iaas/api/#/en/vision/20220125/)
    - Vision AI allows customers to detect and classify objects in uploaded images.
- [Blog: Empowering Search with OCI Vision in Oracle APEX](https://blogs.oracle.com/apex/post/empowering-search-with-oci-vision-in-oracle-apex)
- [Blog: Building Innovative Q&A Experiences: Oracle APEX Meets OCI Generative AI](https://blogs.oracle.com/apex/post/building-innovative-qa-experiences-oracle-apex-meets-oci-generative-ai)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
