# Oracle Access Governance REST Postman Request Samples

A Postman collection of sample REST API requests for Oracle Access Governance (OAG) that showcases the ability to submit requests, trigger guardrail violations and interrogate OAG objects using REST API calls. Note that these samples are meant for reference only and are not intended for use in production systems.

Review Date: 11.11.2025

# When to use this asset?

The collection can be used for demonstration purposes, to showcase the REST API capabilities of OAG or as a general reference in OAG request automation. This provides a streamlined approach to the more hardcoded flow described in the following Developer Coaching session: https://www.youtube.com/watch?v=bDUIrKldGU0

# How to use this asset?

## Pre-requisites

- The prerequisites section of the OAG REST API integration document must be followed in order to set up a client credentials authentication flow. More details at: https://docs.oracle.com/en/cloud/paas/access-governance/pmapi/prerequisites.html
- The collection relies on collection variables in order to properly construct the REST queries. Before running any of the queries please ensure you update the `{{ociiam_url}}` and `{{oag_url}}` variables in order to point to the OIG environment you intend to use. These URLs are the same values you have used in the configuration step above. In order to do that, access the "Variables" tab by first clicking on the Postman collection name. Feel free to also update the `{{beneficiary_filter}}` and `{{beneficiary_filter_violation}}` values as per your needs - these will be used as filters in the ID identification of the users who will act as beneficiaries for the two submitted access requests.
- Open the "Authorization" tab of the "Get Authorization Token" request and update the credentials with the client ID and client secret generated during the setup of the client credentials authentication flow. Note that Postman will automatically handle the required base64 encoding for you once you've filled in those details.

## Executing the queries

- Make sure you run the queries in sequence, as you will first need a valid `{{access_token}}`, then IDs for the access bundle used in the request, the associated access guardrail, and the two users: one that will trigger the access guardrail violation and one that will not. Note that it is up to you to set up the user details and access guardrail rule in such a way that the violation is triggered and the access requests are rejected during those API calls. For more details on how to do that please consult the Developer Coaching session video shared above.
- Note that the interrogation REST calls extracting the IDs for the access bundle and access guardrail will always save the first listed ID in the returned list. If this is not the intended behavior in your flow, please update these collection variables manually with the correct ID from the response of the corresponding requests.
- If set up properly, the response of the failed request should contain: `"justification": "Access Request REST API Guardrail Violation Test", "requestStatus": "FAILED"`, whereas the successful request response should contain: `"justification": "Access Request REST API Test", "requestStatus": "IN_PROGRESS"`, assuming the requested access bundle is protected by an approval workflow.

# Useful Links

- [Oracle Access Governance REST API reference](https://docs.oracle.com/en/cloud/paas/access-governance/pmapi/)
- [Postman collections guide](https://learning.postman.com/docs/collections/collections-overview/)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
