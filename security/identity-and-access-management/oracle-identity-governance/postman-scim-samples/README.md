# Oracle Identity Governance SCIM Postman Samples

A Postman collection of sample SCIM API requests for Oracle Identity Governance (OIG) that showcases the ability to quickly create organizations, managers and users via SCIM API calls. Note that these samples are meant for reference only and are not intended for use in production systems.

Review Date: 13.11.2023

# When to use this asset?

The collection can be used for demonstration purposes, to showcase the SCIM capabilities of OIG or as a general reference in SCIM request automation.

# How to use this asset?

## Pre-requisites

- The collection relies on collection variables in order to properly construct the SCIM queries. Before running any of the queries please ensure you update the `{{host}}` and `{{port}}` variables in order to point to the OIG environment you intend to use. In order to do that, access the "Variables" tab by first clicking on the Postman collection name. Feel free to also update the `{{organization_name}}` and manager user details as per your needs.
- Open the "Authorization" tab of the "Get Authorization Token" request and update the credentials with a valid username and password. Any user with OIG API access (system administrators) can be used.

## Executing the queries

- Make sure you run the queries in sequence, as you will first need a valid `{{access_token}}`, then a valid `{{organization_id}}` to create the manager and reportees from the sample CSV file.
- Use the "Run Collection" batch functionality in Postman on the "Create User(s) CSV" request in order to import all the sample user entries in the provided CSV file (or from one of your own choosing). Note that the sample CSV file and all user names are provided only for reference. Any similarity to actual persons is purely coincidental and unintended.

# Useful Links

- [Oracle Identity Governance SCIM API reference](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/using-scim-rest-services.html)
- [Postman collections guide](https://learning.postman.com/docs/collections/collections-overview/)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
