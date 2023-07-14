# CIS LZ v2


<img src="../../images/landing_zone_300.png">

&nbsp; 

&nbsp; 

## 1. Before You Start
Before you start and create your configuration, we recommend:
1. Understand [CIS Landing Zone v2 Architecture](https://docs.oracle.com/en/solutions/cis-oci-benchmark/index.html) and the OCI elements involved, as you'll be configuring the solution.
2. Review the [GitHub Repository](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart) as it contains the complete solution documentation.
3. Execute the Live Labs ["Deploy a Secure Landing Zone in OCI"](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3662).



&nbsp; 

## 2. Create The Setup Configuration


Your deliverable will be an OCI Landing Zone configuration. This configuration will contain all the input parameter values, that any implementation team can follow and execute. This activity is important as it will create the master configuration to enable repeatable deployments.

There are two deployment models described below.
&nbsp; 


| DEPLOYMENT MODEL  | WHEN TO USE | GUIDELINES  |  EXAMPLES | 
|---|---|---|---|
| Oracle Resource Manager (ORM) | Use this option by default |[View](/standard_landing_zones/cis_lz_v2/orm/orm_configuration_guide.pdf)  | [Quick Start](/standard_landing_zones/cis_lz_v2/orm/samples/oci_cislz_configuration_example-quickstart_scenario.pdf)<br> [Production](/standard_landing_zones/cis_lz_v2/orm/samples/oci_cislz_configuration_example-production_scenario.pdf) |
| Terraform Command Line | Use this option if you have advanced terraform skills or require code extensions |*Soon* | |

A configuration for the ORM deployment can have the format of a document, with parameters/values per ORM step, while the Terraform Command Line can have the format of tfvars.

&nbsp; 

## 3. Deploy the Configuration

 This activity will execute the deployment configuration in a tenancy. The team responsible for this activity might not be the same in the previous step, and the configuration created will contain all the necessary information for the landing zone deployment. 

The guidelines below can be used and shared informally with the deployment team to guide the process.

&nbsp; 


| DEPLOYMENT MODEL  | WHEN TO USE | GUIDELINES  |  
|---|---|---|
| Oracle Resource Manager (ORM) | Use this option by default | [Review Steps](/standard_landing_zones/cis_lz_v2/orm/orm_deployment_guide.pdf)<br>[Review Live Lab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3662) | 
| Terraform Command Line | Use this option if you have advanced terraform skills or require code extensions | *Soon*


&nbsp; 



## 4. More on CIS LZ v2

The steps above present a standard configuration and deployment of the CIS Landing Zone v2, with guidance for the key configuration decision. In the table below you can find complementary public information on this solution to expand your knowledge.

&nbsp; 


ID                  | TOPIC   		| CONTENT	|  	
:---		                    |:------		      	|:---		   | 
1   |Architecture    | [Deploy a secure landing zone that meets the CIS Foundations Benchmark for Oracle Cloud](https://docs.oracle.com/en/solutions/cis-oci-benchmark/index.html#GUID-89CA48AA-73E1-4992-A43F-CA5FA5CE21CD) |
2         	| Repository		      	| [GitHub Repository](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart) |
3        | Deployment as a Non-admin  | 	[Tenancy Pre Configuration For Deploying CIS OCI Landing Zone as a non-Administrator](https://www.ateam-oracle.com/post/tenancy-pre-configuration-for-deploying-cis-oci-landing-zone-as-a-non-administrator) |
4              | Third-Party Firewalls  | [How to Deploy Landing Zone for a Security Partner Network Appliance](https://www.ateam-oracle.com/post/) / [Adding our security partners to a CIS OCI landing zonehow-to-deploy-landing-zone-for-a-security-partner-network-appliance](https://blogs.oracle.com/cloudmarketplace/post/adding-our-security-partners-to-a-cis-oci-landing-zone) |
5              | Cloud Guard | [Cloud Guard Support in CIS OCI Landing Zone](https://www.ateam-oracle.com/post/cloud-guard-support-in-cis-oci-landing-zone) |
6             | Logging | [Security Log Consolidation in CIS OCI Landing Zone](https://www.ateam-oracle.com/post/security-log-consolidation-in-cis-oci-landing-zone) |
7            | Vulnerability Scanning | [Vulnerability Scanning in CIS OCI Landing Zone](https://www.ateam-oracle.com/post/vulnerability-scanning-in-cis-oci-landing-zone) |
8           | ExaCS | [How to Deploy CIS Landing Zone v2 for Exadata Cloud Service](https://www.ateam-oracle.com/post/how-to-deploy-oci-secure-landing-zone-for-exadata-cloud-service) |
9             | Events and Alarms | [How to Operationalize the CIS Landing Zone with Alarms and Events](https://www.ateam-oracle.com/post/operational-monitoring-and-alerting-in-the-cis-landing-zone) |



&nbsp; 

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/folder-structure/LICENSE) for more details.