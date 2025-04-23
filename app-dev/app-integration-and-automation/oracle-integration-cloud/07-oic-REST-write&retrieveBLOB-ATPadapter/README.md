# REST services to store and retrieve BLOB from ATP
Assets that contain oic project that can be used as template for the storing and retrieving attachments from Oracle ATP Database

## Using the Oracle Autonomous Transaction Processing Adapter to store and retrieve binary objects
This simple template project reflects some real use cases. E.g. customer/partner uses mobile/web application to register account based on photo of the Identity document. In our case it will be implementation of the REST services that stores the attached document to ATP and retrieval of the stored content based on some business key

## CICD - OIC3 quickstart Example
The template project demonstrates how you can send multipart mixed content payload through Oracle Integration to an Autonomous Database and then later retrieve the attachment from DB. All this can be invoked/consumed from an external application through REST API

Review Date: 15.04.2025

# When to use these assets?

These assets should be used whenever needed to design and implement REST processing of multipart/mixed payloads and retrieving the binary large objects from OIC Staging database(ATP).

# How to use these asset?

The information is generic in nature and not specified for a particular customer. 
 - Project solution and installation is described in the ./filex/OIC-Project-REST-write&retrieveBLOB-ATPadapter.pdf
 - Project solution logical view for the OCI Integration Cloud Architecture used is located in ./files/img
 - Postman collection and curl commands to test the services are located in ./filex/oic-clients 
 - OIC project archive .car file is located in ./files/oic-roject
 - Sql commands to create table necessary for the service run and sample payloads and content are located in ./files/oic-prereqs


# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
