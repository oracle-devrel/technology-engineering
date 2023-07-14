# STANDARD LANDING ZONES

&nbsp; 

<img src="../images/lzf_standard.png" alt= “” width="400" height="value">

&nbsp; 

## 1. What Are Standard Landing Zones

An SLZ is a **prescribed approach** to landing zones with a **guided setup**, that can be used in **self-service mode** by the user. To achieve this, a **set of configurations** are available with a predefined structure. This is the **recommended approach for initial landing zone deployments** covering the most-common workload scenarios. An SLZ can also be extended to implement specific requirements, but those extension resources would be manually created or by custom code.

Some characteristics of an SLZ:

- It provides a set of **best practices** and a prescriptive approach to deploying secure landing zones.
- It creates a **pre-defined** landing zone structure (compartments, networks, groups, policies, etc.)
- It’s a **configurable** setup, with no design or implementation activities.
- It provides a **secure footprint** to safely land and uses workloads.
- It has an **automated deployment** with **public** and **free** code
- It’s where you **start the journey** and later expand or extend toward specific requirements.

Please note that there are several solutions that fit this model, see below.

&nbsp; 

## 2. What Are The Solutions Available

Before starting, it's important to understand the existing OCI landing zone solution landscape. There are mainly two solutions to take into account:

&nbsp; 

* **[CIS LANDING ZONE (CIS LZ)](https://docs.oracle.com/en/solutions/cis-oci-benchmark/index.html)**:  This reference architecture provides a Terraform-based landing zone template that meets the security guidance prescribed in CIS Oracle Cloud Infrastructure Foundations Benchmark. This LZ brings in the ability to provision multiple VCNs, either in standalone mode or as constituent parts of a Hub and Spoke architecture. The VCNs can either follow a general purpose standard three-tier network topology or are oriented towards specific topologies. 
  * The current version is v2.x.
  * The v3 is coming and a highly configurable set of terraform modules are already available to configure with json/hcl any landing zone structure. For more details refer to the [Tailored Landing Zones](/tailored_landing_zones/tailored_landing_zones.md) approach. 


&nbsp; 
* **[ORACLE ENTERPRISE LANDING ZONE (OELZ)](https://blogs.oracle.com/cloudsecurity/post/enterprise-scale-baseline-landing-zone-version2)**: This is the new version of the enterprise version of the Cloud Adoption Framework (CAF) landing zone. This solution provides a scalable architecture and deployment that includes designs for governance, security segmentation, and separation of duties. It's possible to deploy multiple workloads with separate networks for isolation and access.
  * The current version is v2.x.



&nbsp; 

## 3. How Do You Decide Which Solution

Find below an executive review of some key requirements that will influence the standard landing zone decision - without any customization:

&nbsp; 


| DOMAIN  |  REQUIREMENT | SOLUTION  |  
|---|---|---|
| Segregation of Duties | A dedicated Network Team, Security Team, Database Team, and Applications Team, operating their respective resources is required| CIS LZ v2 |
| Segregation of Duties | A dedicated Network Team, Security Team, and possibly a Team per Application operating their respective resources is required | OELZ v2 |
| Isolation of Resources | A strong workload network isolation with NSGs is required | CIS LZ v2 |
| Security | The OCI Tenancy CIS Validation embedded on the solution is required | CIS LZ v2 |
| Security | The target tenancy doesn't have Identity Domains | CIS LZ v2 |
| Cost | Starting with no initial OCI consumption is required | CIS LZ v2 |

&nbsp; 

For other design considerations (such as hub & spoke, several environments, ExaCS ready, etc.), both solutions will fit. If after reviewing the table above it's still not clear to identify a solution: 
1. Visit [this asset](/commons/select_your_solution.pdf) for further consideration.
2. Might be in the case that a customization is required for a standard landing zone, which should be treated as an extension of it, and **not** as rebuilding it into a different shape. Choose the solution that is nearer to the requirements.
3. If it's required to rebuild/restructure a standard landing zone then  use it's recommended to use the [tailored landing zone](/tailored_landing_zones/tailored_landing_zones.md) approach.

&nbsp; 

## 4. How to Start

&nbsp; 

| STEP  |   DESCRIPTION | 
|:---:|---|
| 1 | Review the previous section | 
| 2 | Review the [**landing zone landscape**](/commons/select_your_solution.pdf) for complementary **considerations for using and before using**.  |
|3 | Select the solution:<br>- For the **CIS LZ [start here](/standard_landing_zones/cis_lz_v2/cis_landing_zone_v2.md)**. <br>- For the **OELZ [start here](/standard_landing_zones/oelz_v2/oelz_v2.md)**.
| 4 | If it's required a **custom design extending the standard landing zone**, there are three alternatives: <br>**a. OCI Console**: Update the resources after deploying the solution. The impact of this is operating the OCI landing zone with the OCI console, i.e., manually.<br>**b. Extended IaC**: Update the code to fit the needs and deploy the solution. The impact of this might be the effort and skills required. <br>**c. Tailored with IaC**: If it's required more design flexibility or the extensions break the standard solution and require structural changes, use the [tailored landing zone](/tailored_landing_zones/tailored_landing_zones.md) approach.

   
&nbsp; 

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/folder-structure/LICENSE) for more details.