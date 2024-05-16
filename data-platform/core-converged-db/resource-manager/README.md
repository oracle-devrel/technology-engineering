# Database Resource Manager


Computing resources in either a Cloud environment or a traditional data center environment represent a significant cost to any organization. Proper management of those computing issues in one business application from impacting another. Oracle’s resource management tools include the ability to manage system resources so that each database (and therefore each business application) receives the desired minimum amount of system resources, and each database does not exceed the amount of allocated resources. With Database Resource Manager the database has more control over how hardware resources are allocated. When database resource allocation decisions are left to the operating system, you may encounter problems with workload management. 

Database Resource Manager helps to overcome these problems like inappropriate allocation of resources, and excessive overhead by allowing the database more control over how hardware resources are allocated. In an environment with multiple concurrent user sessions that run jobs with differing priorities, all sessions should not be treated equally. Database Resource Manager enables you to classify sessions into groups based on session attributes and then allocate resources to those groups in a way that optimizes hardware utilization for your application environment.

Reviewed: 16.04.2024

# Useful Links

## Documentation

- [Database Administrator’s Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-resources-with-oracle-database-resource-manager.html#GUID-2BEF5482-CF97-4A85-BD90-9195E41E74EF)
- [PL/SQL Packages and Types Reference: DBMS_RESOURCE_MANAGER](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_RESOURCE_MANAGER.html#GUID-F3B685CB-5F15-4DFB-90FD-6FBBA9B6F6DB)
- [PL/SQL Packages and Types Reference: DBMS_RESOURCE_MANAGER_PRIVS](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_RESOURCE_MANAGER_PRIVS.html#GUID-B8B082C6-DF53-466B-9B11-1CAFCC3F0509)


## Videos

- [How to Use Resource Manager in Oracle with CDB and PDB - Oracle database resource manager](https://www.youtube.com/watch?v=rXSWGo2pWE4)

## Blogs and technical briefs

- [High Performance Database Deployment with Resource Manager](https://blogs.oracle.com/exadata/post/high-performance-database-deployment-with-resource-manager)
- [Multitenant: Dynamic CPU Scaling - Resource Manager Control of CPU using CPU_COUNT and CPU_MIN_COUNT](https://oracle-base.com/articles/19c/multitenant-dynamic-cpu-scaling-19c)
- [Best Practices for Database Consolidation](https://www.oracle.com/docs/tech/database/maa-consolidation.pdf)

# Team Publications

- [Scripts to create a simple resource plan](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/resource-manager/scripts)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
