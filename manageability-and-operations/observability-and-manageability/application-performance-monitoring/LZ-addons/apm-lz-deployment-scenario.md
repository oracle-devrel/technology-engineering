# **[OCI Landing Zone Application Performance Monitoring Service](#)**
## **Deployment Blueprint for OCI Application Performance Monitoring**
&nbsp;

Based on the design decisions made for OCI Application Performance Monitoring (OCI APM) (click [here](./apm-lz-design-decisions.md) for more), a basic deployment of OCI APM will look like the blueprint below:

![OCI APM Deployment](../images/apm_deployment.png) 
&nbsp;

An APM domain is deployed with its own Oracle-managed storage and data uploadd endpoint accessible from within the OCI service network as opposed to customer-managed virtual cloud networks (VCN). This means data sources collecting front-end and back-end telemetry will need to be able to reach the domain endpoint ending in "oci.oraclecloud.com" via HTTPS (Port 443) - either over the internet, through a proxy, or via the OCI Service Gateway if the application services run in OCI VCNs. All data transmissions are egress-only, meaning no ports need to be opened to allow ingress traffic for the data sources on clients, servers or containers.

All data sources need to use data keys belonging to the APM domain endpoint for validation before upload. The public data key is used for the browser agent while the private data key is used for back-end data sources. The reason there are two types of keys is due to the nature of the browser agent and front-end monitoring done with JavaScript. The code including the data key is exposed via e.g. developer tools when visiting a monitored web page during browser sessions. This is different from back-end instrumentation. The details of back-end data sources are only exposed to anyone with private access to the application server or container. For this reason, back-end spans are validated with a private key which is not meanth to be exposed in browsers. See [here](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/obtain-data-upload-endpoint-and-data-keys.html) for more.

When the domain is created and data sources are configured to transfer data, additional configurations to any of these can be made as outlined [here](./apm-lz-design-decisions.md).

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](/LICENSE.txt) for more details.