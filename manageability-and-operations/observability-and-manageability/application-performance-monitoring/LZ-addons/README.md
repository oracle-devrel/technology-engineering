# OCI Landing Zone Add-On for Application Performance Monitoring
 
This landing zone add-on acts as a decision-making companion. It provides reference material to help plan your configuration of OCI Application Performance Monitoring (OCI APM).
 
Reviewed: 03.10.2025
 
# When to use this asset?
 
Use this asset after you’ve decided to instrument your application services with OCI APM. It highlights the main considerations when setting up APM domains, data sources, availability monitors, alarms, and related networking.
 
# How to use this asset?
 
The asset is organized into two sections:

* **[Design Decisions](files/apm-lz-design-decisions.md)**:
  * Covers key questions and options to evaluate when configuring OCI APM such as:
    * How to organize **[APM domains](files/apm-lz-design-decisions.md#domains)** for ingesting and processing end-to-end application traces
    * How to select and configure **[data sources](files/apm-lz-design-decisions.md#data-sources)** to collect trace telemetry from applications
    * How to manage **[availability monitors](files/apm-lz-design-decisions.md#availability-monitors)** to proactively test key features, endpoints, and user flows in applications
    * How to manage **[alarms](files/apm-lz-design-decisions.md#alarms)** to notify you on critical events in application telemetry or availability monitor runs
* **[Deployment Blueprint](files/apm-lz-deployment-blueprint.md)**:
    * Covers the network architecture of an APM-instrumented application, and how data sources transfer telemetry to APM as a public cloud service.
 
# Useful Links
 
- [Application Performance Monitoring](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/home.htm)
    - Official documentation for OCI APM
- [Get Started with APM](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/get-started-application-performance-monitoring.html)
    - Get Started section in official documentation
 
# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.