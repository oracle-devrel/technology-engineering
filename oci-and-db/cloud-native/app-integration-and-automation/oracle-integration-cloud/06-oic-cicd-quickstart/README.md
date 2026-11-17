# OIC CICD QuickStart
Review Date: 2026-Oct-08

## Promoting OIC Code Between Environments

Promoting OIC code involves exporting artifacts from a source environment and importing them into a target environment. OIC Projects and Project Deployments are packaged as `.CAR` archives containing XML files. You can extract these archives for inspection, but you should not modify their contents manually.

### Export and import options

You can export and import artifacts through the OIC console or automate the process with the [OIC Developer APIs](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/op-ic-api-integration-v1-projects-id-archive-post.html). An API-driven approach offers flexibility for CI/CD: the APIs can be called from Java, Python, or shell scripts and integrated with Jenkins, GitHub Actions, GitLab CI/CD, Azure DevOps, or OCI DevOps.

For guidance on choosing an approach, see [CI/CD Approaches for Oracle Integration](https://blogs.oracle.com/integration/ci-cd-approaches-for-oracle-integration).

### Practical examples

1. For an example using the OIC Developer APIs, Unix shell scripts, and OCI DevOps, see the article [OIC e OCI DevOps – Exemplos para sua esteira CI/CD](https://blogs.oracle.com/lad-cloud-experts-pt/oic-e-oci-devops-exemplos-para-sua-esteira-ci-cd) and its [GitHub repository](https://github.com/rchafik/oicDevops). The article is in Portuguese but can be translated in a browser.

1. Assets included in this repository:
    - **CICD - OIC3 quickstart Example**. Postman collection implementing the OIC Developer API requests. Before using OIC APIs, configure OAuth authentication through IAM by following [Call the Developer APIs with Client Credentials](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/call-developer-apis-client-credentials.html).

## Managing the OIC instance

Assets included in this repository:
- **OCI - API Signing Example for OIC (CICD Quick-Start)**. Postman collection implementing the API request signing required by the Oracle Cloud Infrastructure API, as well as capturing some sample OCI requests.

# When to use these assets?

These assets should be used whenever needed to design automatic Integrations deployment or OIC instance management.

# How to use these asset?

The information is generic in nature and not specified for a particular customer. 

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
