# OCI Load Balancer

The Oracle Cloud Infrastructure Load Balancer LBaaS service provides automated traffic distribution from one entry point to multiple servers reachable from your virtual cloud network (VCN). The service offers a load balancer with your choice of a public or private IP address and provisioned bandwidth.

The Load Balancer service enables you to create a public or private load balancer within your VCN. A public load balancer has a public IP address that is accessible from the internet. A private load balancer has an IP address from the hosting subnet, which is visible only within your VCN. You can configure multiple listeners  for an IP address to load balance transport Layer 4 and Layer 7 (TCP and HTTP) traffic. Both public and private load balancers act as reverse proxies and can route data traffic to any backend server that is reachable from the VCN.

Network Load Balancer provides automated traffic distribution from one entry point to multiple backend servers in your virtual cloud network (VCN). It operates at the connection level and load balances incoming client connections to healthy backend servers based on Layer 3/Layer 4 (IP protocol) data. The service offers a load balancer with your choice of a regional public or private IP address that is elastically scalable and scales up or down based on client traffic with no bandwidth configuration requirement.

Network Load Balancer provides the benefits of flow high availability, source and destination IP addresses, and port preservation. It is designed to handle volatile traffic patterns and millions of flows, offering high throughput while maintaining ultra-low latency. Network load balancers have a default 1 million concurrent connection limit. A network Load Balancer is the ideal load-balancing solution for latency-sensitive workloads.

Reviewed: 06.02.2024
 
# Useful Links

- [NLB Vs LBaas](https://www.ateam-oracle.com/post/comparing-oci-load-balancers)
- [LBaas Video Tutorial](https://www.youtube.com/watch?v=88wIK_zZVzw)
- [LBaas Autoscaling Video](https://www.youtube.com/watch?v=2A9tq3rDkVM)
- [LBaaS and SSL configuration](https://www.youtube.com/watch?v=8VzFO-kPGDI)
- [LBaas troubleshooting](https://www.ateam-oracle.com/post/loadbalancer-troubleshooting)
- [Comparison LBs](https://www.ateam-oracle.com/post/comparing-oci-load-balancers)
- [FAQ](https://www.oracle.com/cloud/networking/load-balancing/faq/)

## Reference Architectures & Step-by-step Guides

-[OCI Network Load Balancer Types, Use Cases, and Best Practices](https://www.ateam-oracle.com/post/oci-network-load-balancer-types-use-cases-and-best-practice)

## Blogs
 
- [Announcing Oracle Cloud Infrastructure Flexible Load Balancing](https://blogs.oracle.com/cloud-infrastructure/post/announcing-oracle-cloud-infrastructure-flexible-load-balancing)
- [Application load balancing on Oracle Cloud Infrastructure](https://blogs.oracle.com/developers/post/application-load-balancing-on-oracle-cloud-infrastructure)
- [Comparing OCI Load Balancers: Quickly and Easily](https://www.ateam-oracle.com/post/comparing-oci-load-balancers)
- [Configure Oracle Cloud Infrastructure (OCI) Network Load Balancer for Oracle Analytics Server on Oracle Cloud Marketplace](https://blogs.oracle.com/analytics/post/configure-oracle-cloud-infrastructure-oci-network-load-balancer-for-oracle-analytics-server-on-oracle-cloud-marketplace)

## Videos & Podcasts

- [Oracle Cloud Infrastructure Load Balancing: Overview](https://www.youtube.com/watch?v=HaCzcFrTF-g)
- [Deploy High Availability (HA) applications using Load Balancer in OCI](https://www.youtube.com/watch?v=bOwEwfu78Zg)
- [Tutorial](https://www.youtube.com/watch?v=88wIK_zZVzw)
- [AutoScaling Tutorial](https://www.youtube.com/watch?v=2A9tq3rDkVM)
- [LBaaS and SSL Management](https://www.youtube.com/watch?v=8VzFO-kPGDI)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
