# **OCI Landing Zone Framework**

&nbsp; 


Welcome to the **OCI Landing Zone Framework (LZF)**.

The LZF was created by the EMEA Landing Zone Specialists, collaborating with worldwide Oracle, customers, and partners, to **simplify the OCI onboarding experience** and **reduce OCI day-one and day-two efforts**. It provides **best practices** covering the complete spectrum of OCI landing zones, from the **standards** to the **tailored** approaches, including landing zone extensions for specific **workloads**.

&nbsp; 


| APPROACH  |  OBJECTIVE | DESCRIPTION | 
|---|---|---|
| <a href="/landing-zones/standard_landing_zones/standard_landing_zones.md" ><img src="images/slz.jpg" alt= “” width="500" height=""></a>  | **Basic Workloads** | **Prescribed** and **ready to use** solutions with a **guided setup** and  **IaC**. This is the  recommended approach for initial landing zone deployments covering the **most-common workload scenarios**.  | 
| <a href="workload_landing_zones/workload_landing_zones.md" ><img src="images/wlz.jpg" alt= “” width="500" height=""> </a>  | **Specific Workloads** | A set of landing zones extension ready for specific **workloads**. Each flavour has a **design** with **IaC configurations** ready to be deployed. Examples are EBS, ExaCC, OCVS, OIC, OKE, CCC, etc. |  
| <a href="tailored_landing_zones/tailored_landing_zones.md" ><img src="images/tlz.jpg" alt= “” width="500" height=""> </a>  | **All Workloads** | An approach to solve **specific requirements** when the standard is not enough. These LZs run with **configuration-as-code** and are used to scale/bridge with existing **operating models**, complying with fine-grained **segregations of duties**, strong **network isolation**, and heterogeneous **workloads**.  |  


&nbsp; 

If you're **starting with OCI landing zones**:
1. Start with a **standard** landing zone as they're full of best practices. If it needs adjustments or **extensions on top** of the prescribed design, customize it by code or manually. 
2. If you have a **specific target workload** that is available as a **workload landing zone**, use it directly. If it's not available, talk to us or use the tailored approach to set up your extensions.
3. If your design is very **customized**, requiring **structural changes** to a standard landing zone (IAM or Network), and/or you need a **highly scalable operating model**, use the **tailored** approach to create your solution.

&nbsp; 

The following **assets** are also available to improve the OCI landing experience:
1. **Overview**: [Executive Overview of the Available Approaches](/landing-zones/commons/EMEA_LandingZonesSpecialists_ExecOverview.pdf)
2. **Solution Definition**: [Creating a Landing Zone Solution Definition (**SDD**)](/landing-zones/commons/lz_solution_definition.md)
3. **Workloads**: [How an OCI Workload Landing Zone Looks Like (**OCI EBS LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz/tree/master/examples/oci-ebs-lz)
4. **Tailored**: [How an OCI Tailored Landing Zone Looks Like (**OCI Open LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz)
5. **Learn**: [How to Design and Configure Landing Zones (**OCI Learn LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz/tree/master/examples/oci-learn-lz)
6. **Naming**: [Resource Naming Conventions for OCI](/landing-zones/commons/resource_naming_conventions.md)
7. **Identity**: [OCI User Identity Management](/landing-zones/commons/user_identity_management.md)
8. **Budgets**: [OCI Budgets and Tagging Recommendations](/landing-zones/commons/budgets_and_tagging.md)


&nbsp; 

&nbsp; 




# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
