# ocm-migration-using-object-storage
 
*Upload Content from OCI Object Storage to Oracle Content Management*
 
# When to use this asset?
 
OCI Object Storage has been designed as a first-class service for storing documents. Document creation needs to happen before a document gets uploaded into an Object Storage bucket.  Likewise, even though Object Storage supports document versioning, editing the document itself typically requires the document to be downloaded, edited locally and uploaded back into Object Storage with the desired changes.

Oracle Content offers a number of native tools and 3rd party integrations to create and edit documents.  Administrators can define text-based asset types that allow business users to create and edit plain text, markup, markdown or JSON data directly in the Web UI.  Microsoft Office documents can be created and edited directly in Office or Office 365.  Oracle Content includes a connector for Adobe Creative Cloud to allow users to create and edit documents in the corresponding Creative Cloud tools like InDesign, Photoshop, Premier Pro, etc.  Oracle Content will also support integration with Desygner in the coming months.
 
# How to use this asset?
 
This asset is provided as an example. Please tailor the code according to your needs and your context.

See [files/ocm-migration-using-object-storage/README.md](files/ocm-migration-using-object-storage/README.md) for asset details.
 
# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
