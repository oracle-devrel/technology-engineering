# **[OCI Landing Zone Application Performance Monitoring Service](#)**
## **An OCI Open LZ Addon to enable Application Performance Monitoring in your LZ**
&nbsp; 

This landing zone add-on provides the necessary configuration steps to enable OCI Application Performance Monitoring (OCI APM). OCI APM offers tools to collect and explore frontend-to-backend traces of application operations to locate performance bottlenecks and dependencies.

|Step  |  Name| Link|
|---|---|---|
| 1  | Design Decisions | Link |
| 2  | WIP | Coming Soon  |
| 3 | WIP| Coming Soon |
| 4  | WIP | Coming Soon|
&nbsp; 

## 3. Deployment Scenario

Based on the outlined design decisions, a basic deployment of OCI APM will look like the blueprint below:

ADD BLUEPRINT IMAGE 
&nbsp;

An APM domain is deployed with its own Oracle-managed storage and data uploadd endpoint accessible from within the OCI service network as opposed to customer-managed virtual cloud networks (VCN). This means data sources collecting front-end and back-end telemetry will need to be able to reach the domain endpoint ending in "oci.oraclecloud.com" via HTTPS (Port 443) - either over the internet, through a proxy, or via the OCI service gateway if the application services run in OCI VCNs. All data transmissions are egress-only, meaning no ports need to be opened to allow ingress traffic for the data sources on clients, servers or containers.

All data sources need to use data keys belonging to the APM domain endpoint for validation before upload. The public data key is used for the browser agent while the private data key is used for back-end data sources. The reason there are two types of keys is due to the nature of the browser agent and front-end monitoring done with JavaScript. The code including the data key is exposed to any browser loading it when visiting a monitored web page. This is different from back-end spans instrumented by data sources only exposed to anyone with private access to the application server or container. For this reason, back-end spans are validated with a private key not exposed in browsers. See [here](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/obtain-data-upload-endpoint-and-data-keys.html) for more.

When the domain is created and data sources are configured to transfer data, additional configurations to any of these can be made as outlined in section 2.

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](/LICENSE.txt) for more details.
