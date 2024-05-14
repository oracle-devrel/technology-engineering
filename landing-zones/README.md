# **OCI Landing Zone Framework**

&nbsp; 


Welcome to the **OCI Landing Zone Framework (LZF)**.

The LZF was created by the EMEA Landing Zone Specialists, collaborating with worldwide Oracle, customers, and partners, to **simplify the OCI onboarding experience** and **reduce OCI day-one and day-two efforts**. It provides **best practices** covering the complete spectrum of OCI landing zones, from the **standards** to the **tailored** approaches, including landing zone extensions for specific **workloads**.

&nbsp; 


| APPROACH  |  OBJECTIVE | DESCRIPTION | 
|---|---|---|
| <a href="/landing-zones/standard_landing_zones/readme.md"><img src="images/slz.jpg" alt= “” width="500" height=""></a>  | **Best Practices</br>3 Shapes** | **Three standard shapes/models** for different organization scopes, **ready to use** with **design blueprints** and  **IaC configurations**. Use these models directly or tailor them to your needs.  | 
| <a href="tailored_landing_zones/readme.md" ><img src="images/tlz.jpg" alt= “” width="500" height=""> </a>  | **Tailored Design </br> Any Shape** | An approach to solve **specific requirements** when the standard models are not enough. A tailored model has **dedicated design views** to match requirements and an IaC runtime. This approach is commonly used to bridge **existing customer practices** in other CSPs. |  
| <a href="workload_landing_zones/readme.md" ><img src="images/wext.jpg" alt= “” width="500" height=""> </a>  | **Workload Ready</br>Plug & Play** | **Complement your landing zone** with extensions ready for **specific workloads**. Each flavor has a **design** with **IaC configurations** ready to be deployed on top of standard or tailored landing zones. Examples are EBS, ExaCC, OCVS, OIC, OKE, CCC, etc. |  

&nbsp; 


If you're **starting with OCI landing zones**:
1. Start with [**Standard Landing Zones**](/landing-zones/standard_landing_zones/readme.md) as they're full of best practices. There are [**three models/shapes**](/landing-zones/standard_landing_zones/readme.md#2-what-are-the-models-available) available for different scopes, we'll help you find the best fit [**here**](/landing-zones/standard_landing_zones/readme.md#3-decide-on-the-model-to-use).
2. If your design is very **customized**, requiring **structural changes** to a standard landing zone (IAM or Network), and/or you need a **highly scalable operating model**, use the [**Tailored Landing Zones**](/landing-zones/tailored_landing_zones/readme.md) approach to create your solution.
3. Complementary, if you have a **specific target workload** that is available as [**Workload Extensions**](/landing-zones/workload_extensions/readme.md), use it directly on top of your landing zone. If it's not available, feel free to reach out to us or use the tailored approach to set up your extensions.


&nbsp; 

The following **assets** are also available to improve the OCI landing experience:
1. **Landing Zones**: [How a Complete OCI Landing Zone Looks Like (**OCI Open LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz/tree/master/design)
2. **Workloads Extensions**: [How an OCI Workload Extensions Looks Like (**OCI EBS LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz/tree/master/examples/oci-ebs-lz)
3. **Infrastructure-as-Code (IaC)**: [The Configurable IaC approach to OCI Landing Zones **(CIS Modules)**](/landing-zones/commons/oci_landingzones_iac.md).
4. **Learn/DIY**: [How to Design and Configure OCI Landing Zones (**OCI Learn LZ**)](https://github.com/oracle-quickstart/terraform-oci-open-lz/tree/master/examples/oci-learn-lz)
5. **Naming Conventions**: [Resource Naming Conventions for OCI](/landing-zones/commons/resource_naming_conventions.md)
6. **Identity**: [OCI User Identity Management](/landing-zones/commons/user_identity_management.md)
7. **Budgets**: [OCI Budgets and Tagging Recommendations](/landing-zones/commons/budgets_and_tagging.md)
8. **Solution Definition**: [Creating a Landing Zone Solution Definition (**SDD**)](/landing-zones/commons/lz_solution_definition.md)


&nbsp; 

&nbsp; 




# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
