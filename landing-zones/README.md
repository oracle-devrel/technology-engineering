# LANDING ZONE FRAMEWORK

&nbsp; 

Welcome to the **Landing Zone Framework (LZF)**. 

The LZF is a set of assets that aim to **simplify the OCI onboarding experience** and **reduce OCI day-one and day-two efforts**. It provide **best practices**, and approaches covering the complete spectrum of OCI landing zones, from the **Standards** ones with the CIS LZ and OELZ to the **Tailored** approaches with IaC configurations.  


&nbsp; 


| APPROACH  |  DESCRIPTION | ASSET  |  
|---|---|:---:|
| <a href="standard_landing_zones/standard_landing_zones.md" ><img src="images/slz.png" alt= “” width="600" height=""></a>  | A standard landing zone is a **prescribed** approach to landing zones with a **guided setup** by the user, using an **existing IaC solution**. This is the recommended approach for initial landing zone deployments covering the most-common workload scenarios.  | **[VIEW](/standard_landing_zones/standard_landing_zones.md)** | 
| <a href="tailored_landing_zones/tailored_landing_zones.md" ><img src="images/tlz.png" alt= “” width="600" height=""> </a>  | A tailored landing zone is a solution to **fit specific requirements** when the standard approach is not enough. It's an **IaC configuration-driven** approach, simple to set up, and is normally used to bridge with existing operating models, with fine-grained segregations of duties, strong network isolation, heterogeneous workloads, among others.  |  **[VIEW](/tailored_landing_zones/tailored_landing_zones.md)** |   | 
  

&nbsp; 

If you're starting with landing zones, we recommend the following **decision process**:
1. Start with the **standard** approach as they're full of best practices.
2. If it need adjustments or **extensions** on top of the prescribed design, customize it by code or manually. 
3. If the design requires **structural changes** to the standard landing zone and a **scalable operating model**, use the **tailored** approach with IaC configuration (json/hcl).

&nbsp; 


The following support assets are also available for a better OCI experience:
- [Resource Namining Conventions](/commons/resource_naming_conventions.md)
- [User Identity Management](/commons/user_identity_management.md)
- [Budgets and Tagging](/commons/budgets_and_tagging.md)


&nbsp; 

&nbsp; 


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/folder-structure/LICENSE) for more details.