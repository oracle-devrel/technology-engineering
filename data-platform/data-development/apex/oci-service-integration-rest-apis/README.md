# Integrating with OCI Cloud Services

REST APIs are used to integrate with OCI Cloud Services from APEX. understanding the nuances of the APIs and OCI authentication can be somewhat complex. The main challenge in our experience has been translating Documentation into Implementation.

Reviewed: 18.11.2024

# When to use this asset?
Use this asset when you need to integrate Oracle APEX with OCI Cloud Services via REST APIs to automate tasks, manage resources, or access data stored in OCI services. This asset is ideal when your application requires operations such as uploading files to OCI Object Storage, querying data from Autonomous Databases, or managing OCI resources like compute instances or network configurations. It’s particularly useful for applications that need secure, scalable, and programmatic access to OCI services without requiring direct user interaction or manual handling of OCI resources. Use this asset to streamline cloud operations, automate workflows, or enable APEX apps to communicate with OCI in real time.

# How to use this asset?
This asset enables the integration of Oracle APEX with OCI Cloud Services using REST APIs. To use it, you need to set up authentication by generating API signing keys and obtaining necessary OCI identifiers (Tenancy OCID, User OCID, Compartment OCID, and API key fingerprint). Once authenticated, you can install the asset in APEX, configure it with OCI service endpoints, and use APEX’s REST capabilities or PL/SQL to interact with OCI services like Object Storage or Autonomous Database. 

# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
 
# Team Publications

-  [Interacting with OCI REST APIs in APEX — Empty POST Request](https://medium.com/@devpiotrekk/interacting-with-oci-rest-apis-in-apex-empty-post-request-ce270d15cbb6 "Tip: Submitting Empty Body")
 
# Useful Links

- [Oracle Documentation - Document Understanding API](https://docs.oracle.com/en-us/iaas/api/#/en/document-understanding/20221109/)
    - Document AI helps customers perform various analysis on their documents.
- [Oracle Documentation - Vision API](https://docs.oracle.com/en-us/iaas/api/#/en/vision/20220125/)
    - Vision AI allows customers to detect and classify objects in uploaded images.
- [Blog: Empowering Search with OCI Vision in Oracle APEX](https://blogs.oracle.com/apex/post/empowering-search-with-oci-vision-in-oracle-apex)
- [Blog: Building Innovative Q&A Experiences: Oracle APEX Meets OCI Generative AI](https://blogs.oracle.com/apex/post/building-innovative-qa-experiences-oracle-apex-meets-oci-generative-ai)

# License

Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
