# Infrastructure as Code - IaC

Infrastructure As Code (IaC) is a methodology in which scripts automate infrastructure and configuration management. IaC tools allow you to abstract away details about your physical environment, allowing you to focus on what matters. It brings several benefits.


**Cost reduction**: By automating time-consuming, frequent, and repeatable tasks, like configuring compute instances and storage, businesses can minimize costs.

**Flexibility**: Modify the parameter of deployed resources by simply changing a variable.

**Speed**: IaC allows automation for everything, leading to quicker provisioning and Time to Market.

**Consistency** IaC makes it possible to avoid human errors and inconsistency and minimize drift over time.

Reviewed: 13/11/2023

# Declarative Automation

In this scenario the desired end-state of the resource is declared, The provider takes care of all the steps needed to achieve the desired state.

***Adopt it when:***

1.        The required OCI Resources are available in Terraform for the scope of the automation;

2.      Provisioning cloud-native OCI Infrastructure and (1) exists;

3.      Change OCI Infrastructure that was provisioned with this method (2) and (1) exists;

4.      Terraform practice is known.

***Prerequisites***

- Decide on  **Git repository organization**  for shared code and dedicated configurations.
- Decide on  **Orchestration technology**.
- Decide on  **State file resource scope**. This decision can influence how many root modules you have. A good segmentation rule is to base state file granularity on resources that are bound to be together, such as Environment Type, OCI Region, etc.
- Decide on the  **Module granularity**. This is related to the  **state file ** decision and  **data structures**  in the  **tfvars**  files.




# Procedural Automation

Enables Operations automation using a procedural approach, with command line & scripting.

Procedural automation consists of a set of activities required to achieve the goal of the automation.  Procedural systems are general in application and are capable of any automation task.

***Possible use cases***

1.      Provision workloads resources such as ExaCS and DBCS;
2.      Provisioning OCI Resources that don't have OCI cloud-native interfaces;
3.      Targeting lifecycle operations on workloads or resources after provisioning;
4.      Targeting configuration management operations on workloads or resources.


***Prerequisites***

- Decide on  **Git repository organization**  for shared code and dedicated configurations
- Decide on  **Orchestration technology**.
- Identifying the  **Operational Scenarios**  and prioritizing them based on the frequency of use and effort.
- Decide on the  **scripting**  technology.



# Useful Links

[What is Infrastructure as Code](https://developer.oracle.com/learn/technical-articles/what-is-iac)


[Oracle Cloud Infrastrucure Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)

[Set Up a Simple OCI Infrastructure with OCI Terraform](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/tf-simple-infrastructure/01-summary.htm)

[OCI Ansible Collection](https://docs.oracle.com/iaas/tools/oci-ansible-collection/latest/)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
