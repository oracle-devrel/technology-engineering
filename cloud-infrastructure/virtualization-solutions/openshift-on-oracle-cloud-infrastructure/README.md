
<!-- <img src="templates/intro.png" alt="OpenShift on Oracle Cloud Infrastructure" width="100%" height="250">-->

# OpenShift on Oracle Cloud Infrastructure

`Reviewed: 12.11.2025` | [last commit](https://github.com/oracle-devrel/technology-engineering/commits/main/cloud-infrastructure/virtualization-solutions/openshift-on-oci/)

This repository is a curated documentation and asset hub for running Red Hat OpenShift on Oracle Cloud Infrastructure (OCI) as a self-managed platform. It provides structured, field-tested guidance, proven architecture patterns, and practical examples to support consistent and repeatable cluster design, deployment, and operations on OCI.

OpenShift can be hosted on OCI without relying on a fully managed service. This model keeps key decisions and responsibilities in your hands, including the installation approach, networking and DNS design, security baselines, upgrade planning, and Day 2 operations. 

Oracle supports this operating model with Terraform templates and OCI integration building blocks that accelerate provisioning and align OpenShift with OCI constructs such as compartments, IAM policies, networking components, and object storage.

## The repository is organized to support the full lifecycle:

- Overview content and curated references to official Red Hat and Oracle documentation
- Reference architectures and design patterns for common OCI topologies
- Installation guidance covering Oracle Terraform templates, Assisted Installer, agent-based workflows, and fully controlled manual installations
- OCI integration guides for operational use cases, including storage and connectivity patterns
- Day 2 operations such as adding nodes, ISO-based node onboarding, enforcing naming standards, troubleshooting guidance, and upgrade strategy
- Reusable scripts to automate recurring OCI and OpenShift tasks and validate outcomes
- Examples for architectures, CI/CD patterns, and sample configurations

The goal is to reduce ambiguity and replace tribal knowledge with modular, maintainable documentation that can be applied across development, test, and production environments.

## Team Publications

The folder layout is designed for quick navigation across documentation, scripts, and examples.

```text
├─ README.md
├─ documents/               Documentation (core entry point) 
│  ├─ 00-overview/          Intro, scope, curated references, blogs
│  ├─ 01-architecture/      Reference architectures and design patterns
│  ├─ 02-installation/      Installation methods and prerequisites
│  ├─ 03-integrations/      OCI integrations (e.g. Storage, Loki, MTV, MTC etc.)
│  ├─ 04-day2-operations/   Operations, upgrades, node expansion, ISO flows
│  └─ 05-assets/            Diagrams and examples used by docs
├─ scripts/                 Reusable automation helpers (OCI and OpenShift)
│  ├─ 00-oci/               OCI scripts and code snippets
│  └─ 00-openshift/         OpenShift manifests and code snippets
├─ examples/                End-to-end examples and sample configs
├─ templates/               Templates for assets and pages reusable         
````

## Documentation map
This section acts as the central entry point to navigate the repository content by lifecycle phase. Use it to jump directly to the relevant documentation area.

* [Documents](documents/) Central documentation hub covering the full OpenShift on OCI lifecycle. It includes overview and scope, architecture patterns, installation methods and prerequisites, integration guides, and Day 2 operations such as upgrades and scaling, plus shared diagrams and examples.

* [Scripts](scripts/) Reusable automation helpers for OCI and OpenShift, kept as practical scripts, manifests, and command snippets. They capture recurring tasks such as platform setup, configuration changes, and validation checks, so operations stay consistent, repeatable, and easier to audit across environments.

* [Examples](examples/) End-to-end reference implementations and sample configurations that can be used as blueprints for real deployments. They show recommended file layouts, defaults, and integration patterns in a concrete form, helping teams start faster and reduce trial-and-error across environments.

## Useful Links

#### Oracle
* [Console](https://cloud.oracle.com/) - Oracle Cloud Console
* [Quick-Start](https://github.com/oracle-quickstart/oci-openshift) - Oracle OpenShift Quick-Start / GitHub
* [Stack Releases](https://github.com/oracle-quickstart/oci-openshift/releases) - Oracle OpenShift Terraform Stack Releases
* [Documentation](https://docs.oracle.com/en-us/iaas/Content/openshift-on-oci/overview.htm) - Official Oracle Cloud Infrastructure Documentation
* [Blog](https://blogs.oracle.com/?s=openshift/) - Official Oracle OpenShift Blogs
#### Red Hat
* [Console](http://console.redhat.com/) - Official Red Hat OpenShift Web Console
* [Documentation](https://docs.openshift.com/) - Official Red Hat OpenShift Documentation
* [Product Lifecycle Policy](https://access.redhat.com/support/policy/updates/openshift/) Official Red Hat OpenShift Product Lifecycle Policy 
* [Blog](https://www.redhat.com/en/blog/) - Official Red Hat OpenShift Blog
* [Upstream](https://github.com/openshift/) - Official Red Hat OpenShift Upstream / GitHub
* [Operator HUB](https://catalog.redhat.com/en/software/containers/openshift4/ose-operator-marketplace/5cddce4dbed8bd5717d6789d/) - Official Red Hat OpenShift Market Place (Operator Hub)


## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
