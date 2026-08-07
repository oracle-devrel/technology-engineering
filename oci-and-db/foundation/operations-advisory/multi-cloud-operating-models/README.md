# Multi-Cloud Operating Models

A Multi-Cloud Operating Model is a combination of processes, governance, organisational practices, and the tools which make it possible, that companies uses to manage and operate workloads across multiple cloud providers.

Multi-Cloud Operating Model also brings simplicity for managing different cloud deployment options, as within OCI with Public cloud, Dedicated Cloud, Hybrid Cloud (Cloud@Customer), Sovereign Cloud and, Multi-Cloud (OD@), where the use of different realms and consoles can increase the operational complexity and a common model is desirable to simplify the overall model.

Operational Advisory team work in making the Multi-Cloud Operating Models a reality, bringing the concepts and standardising how to setup to simplify customers on-boarding in complex setups.

We see Multi-Cloud Control Planes structured in the following areas:

* Operating Model
* Operational Security
* Multi-Cloud Control Plane

Reviewed: 2026-08-07

# Team Publications

## Operating Model

| Asset | Purpose |
|-------|---------|
| [GitOps](./gitops/README.md) | GitOps, a modern operational model designed to manage and scale infrastructure across multi-cloud environments.  |

## Operational Security

| Asset | Purpose |
|-------|---------|
| [Git Security](./operational-security/git-security/README.md) | Learn what security best practices can be leveraged while using Git. |
| [CICD Security](./operational-security/cicd-security/README.md) | Learn what security best practices can be leveraged while using CICD automation. |

| [CIS Dashboard](./operational-security/CISDashboard/README.md) | Visualise and control your OCI CIS Compliance from an OCI Log Analytics Dashboard. |
| [OCI Terraform GitHub Actions Worload Identity Federation Example](https://github.com/dgutierrezcolodra/oci-terraform-github-actions-wif-example) | Step-by-step example for GitHub Actions OIDC to OCI IAM Workload Identity Federation using JWT-to-UPST token exchange and Terraform `SecurityToken` authentication. See the [setup guide](https://github.com/dgutierrezcolodra/oci-terraform-github-actions-wif-example/blob/main/SETUP.md). |
| [Programmatic Access to OCI for CI/CD Pipelines](./operational-security/programatic-access-cicd/README.md) | Best practices to configure OCI Authentication from 3rd party CI/CD Automation Pipelines. |
| [Cloud Guard Activity Reporter.](./operational-security/cloud-guard-activity-reporter/README.md) | Tool to gathered Cloud Guard activity from OCI tenancies. |
| [Automate Security List Updates.](./operational-security/automate-security-list-updates/README.md) | Tool that automates massive Security List updates in OCI tenancies. |

## Multi-Cloud Control Plane

| Asset | Purpose |
|-------|---------|
| [Multi-Cloud Control Plane](./multi-cloud-control-plane/README.md) | Use this blueprint to setup a true Multi-Cloud Control Plane that uses GitOps to operate multiple clouds or OCI realms at scale for Day 1 & Day 2 Operations |

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
