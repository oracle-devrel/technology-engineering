# Microsoft Dynamics365 CRM Architecture on OCI
 
## Overview

Oracle Cloud Infrastructure Identity and Access Management (OCI IAM) Identity Domain [Sign-on Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/signonpolicies/managingsignonpolicies.htm) are a key element for managing access to applications deployed on Oracle Cloud Infrastructure (OCI).

This tutorial is inspired by a customer use case and outlines how an ISV or an Application Services Provider can implement sign-on policies to allow authentication to the applications they deliver to end-users while preventing these from accessing the OCI console.

For this tutorial, two applications are used: an Oracle Analytics Cloud application and an APEX application running on Autonomous Transaction Processing (ATP) service.


### Before you Begin

- Create and configure a compartment and Identity Domain for the applications.
- Deploy one Oracle Analytics Cloud application and one APEX application using ATP.
- Integrate these two applications with OCI IAM Identity Domains.
- Configure Sign-On Policies to allow application access, while preventing application users from signing-on to the OCI Console.
 
## Architecture

### Diagram

### Components

TBD

This architecture has the following components:

- __Tenancy__

Oracle Autonomous Transaction Processing is a self-driving, self-securing, self-repairing database service that is optimized for transaction processing workloads. You do not need to configure or manage any hardware, or install any software. Oracle Cloud Infrastructure handles creating the database, as well as backing up, patching, upgrading, and tuning the database.

- __Region__

An Oracle Cloud Infrastructure region is a localized geographic area that contains one or more data centers, called availability domains. Regions are independent of other regions, and vast distances can separate them (across countries or even continents).

- __Compartment__

Compartments are cross-region logical partitions within an Oracle Cloud Infrastructure tenancy. Use compartments to organize your resources in Oracle Cloud, control access to the resources, and set usage quotas. To control access to the resources in a given compartment, you define policies that specify who can access the resources and what actions they can perform..

- __Availability domains__

Availability domains are standalone, independent data centers within a region. The physical resources in each availability domain are isolated from the resources in the other availability domains, which provides fault tolerance. Availability domains don’t share infrastructure such as power or cooling, or the internal availability domain network. So, a failure at one availability domain is unlikely to affect the other availability domains in the region.

- __Fault domains__

A fault domain is a grouping of hardware and infrastructure within an availability domain. Each availability domain has three fault domains with independent power and hardware. When you distribute resources across multiple fault domains, your applications can tolerate physical server failure, system maintenance, and power failures inside a fault domain.

- __Virtual cloud network (VCN) and subnets__

A VCN is a customizable, software-defined network that you set up in an Oracle Cloud Infrastructure region. Like traditional data center networks, VCNs give you complete control over your network environment. A VCN can have multiple non-overlapping CIDR blocks that you can change after you create the VCN. You can segment a VCN into subnets, which can be scoped to a region or to an availability domain. Each subnet consists of a contiguous range of addresses that don't overlap with the other subnets in the VCN. You can change the size of a subnet after creation. A subnet can be public or private.

- __Load balancer__

The Oracle Cloud Infrastructure Load Balancing service provides automated traffic distribution from a single entry point to multiple servers in the back end.

The load balancer provides access to different applications.

- __Security list__

For each subnet, you can create security rules that specify the source, destination, and type of traffic that must be allowed in and out of the subnet.

- __NAT gateway__

The NAT gateway enables private resources in a VCN to access hosts on the internet, without exposing those resources to incoming internet connections.

- __Service gateway__

The service gateway provides access from a VCN to other services, such as Oracle Cloud Infrastructure Object Storage. The traffic from the VCN to the Oracle service travels over the Oracle network fabric and never traverses the internet.

- __Cloud Guard__

You can use Oracle Cloud Guard to monitor and maintain the security of your resources in Oracle Cloud Infrastructure. Cloud Guard uses detector recipes that you can define to examine your resources for security weaknesses and to monitor operators and users for risky activities. When any misconfiguration or insecure activity is detected, Cloud Guard recommends corrective actions and assists with taking those actions, based on responder recipes that you can define.

- __Security zone__

Security zones ensure Oracle's security best practices from the start by enforcing policies such as encrypting data and preventing public access to networks for an entire compartment. A security zone is associated with a compartment of the same name and includes security zone policies or a "recipe" that applies to the compartment and its sub-compartments. You can't add or move a standard compartment to a security zone compartment.

- __Object storage__

Object storage provides quick access to large amounts of structured and unstructured data of any content type, including database backups, analytic data, and rich content such as images and videos. You can safely and securely store and then retrieve data directly from the internet or from within the cloud platform. You can seamlessly scale storage without experiencing any degradation in performance or service reliability. Use standard storage for "hot" storage that you need to access quickly, immediately, and frequently. Use archive storage for "cold" storage that you retain for long periods of time and seldom or rarely access.

- __FastConnect__

Oracle Cloud Infrastructure FastConnect provides an easy way to create a dedicated, private connection between your data center and Oracle Cloud Infrastructure. FastConnect provides higher-bandwidth options and a more reliable networking experience when compared with internet-based connections.

- __Local peering gateway (LPG)__

An LPG enables you to peer one VCN with another VCN in the same region. Peering means the VCNs communicate using private IP addresses, without the traffic traversing the internet or routing through your on-premises network.

- __Component__

Description


## Recommendations

TBD

Use the following recommendations as a starting point. Your requirements might differ.

- __VCN__

When you create a VCN, determine the number of CIDR blocks required and the size of each block based on the number of resources that you plan to attach to subnets in the VCN. Use CIDR blocks that are within the standard private IP address space.

Select CIDR blocks that don't overlap with any other network (in Oracle Cloud Infrastructure, your on-premises data center, or another cloud provider) to which you intend to set up private connections.

After you create a VCN, you can change, add, and remove its CIDR blocks.

When you design the subnets, consider your traffic flow and security requirements. Attach all the resources within a specific tier or role to the same subnet, which can serve as a security boundary.

Use regional subnets.

- __Security__

Use Oracle Cloud Guard to monitor and maintain the security of your resources in Oracle Cloud Infrastructure proactively. Cloud Guard uses detector recipes that you can define to examine your resources for security weaknesses and to monitor operators and users for risky activities. When any misconfiguration or insecure activity is detected, Cloud Guard recommends corrective actions and assists with taking those actions, based on responder recipes that you can define.

For resources that require maximum security, Oracle recommends that you use security zones. A security zone is a compartment associated with an Oracle-defined recipe of security policies that are based on best practices. For example, the resources in a security zone must not be accessible from the public internet and they must be encrypted using customer-managed keys. When you create and update resources in a security zone, Oracle Cloud Infrastructure validates the operations against the policies in the security-zone recipe, and denies operations that violate any of the policies.

- __Cloud Guard__
The following is an Oracle-recommended best practice. Don't remove it.

Clone and customize the default recipes provided by Oracle to create custom detector and responder recipes. These recipes enable you to specify what type of security violations generate a warning and what actions are allowed to be performed on them. For example, you might want to detect Object Storage buckets that have visibility set to public.

Apply Cloud Guard at the tenancy level to cover the broadest scope and to reduce the administrative burden of maintaining multiple configurations.

You can also use the Managed List feature to apply certain configurations to detectors.

- __Security zones__

Clone and customize the default recipes provided by Oracle to create custom detector and responder recipes. These recipes enable you to specify what type of security violations generate a warning and what actions are allowed to be performed on them. For example, you might want to detect Object Storage buckets that have visibility set to public.

Apply Cloud Guard at the tenancy level to cover the broadest scope and to reduce the administrative burden of maintaining multiple configurations.

You can also use the Managed List feature to apply certain configurations to detectors.

- __Network security groups (NSGs)__

You can use NSGs to define a set of ingress and egress rules that apply to specific VNICs. We recommend using NSGs rather than security lists, because NSGs enable you to separate the VCN's subnet architecture from the security requirements of your application.

You can use NSGs to define a set of ingress and egress rules that apply to specific VNICs. We recommend using NSGs rather than security lists, because NSGs enable you to separate the VCN's subnet architecture from the security requirements of your application.

- __Load balancer bandwidth__

While creating the load balancer, you can either select a predefined shape that provides a fixed bandwidth, or specify a custom (flexible) shape where you set a bandwidth range and let the service scale the bandwidth automatically based on traffic patterns. With either approach, you can change the shape at any time after creating the load balancer.

- __Component/Topic__

Description


## Considerations

TBD

Consider the following points when deploying this reference architecture.


- __Performance__

Description

- __Security__

Description

- __Availability__

Description

- __Cost__

Description

- __Factor__

Description

## Explore More

TBD


## Acknowledgements

TBD


# License
 
Copyright (c) 2023 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.