# Full Stack Disaster Recovery

Full Stack Disaster Recovery is an Oracle Cloud Infrastructure (OCI) disaster recovery orchestration and management service that provides comprehensive disaster recovery capabilities for all layers of an application stack, including infrastructure, middleware, database, and application.

Using OCI Full Stack DR provides a single pane of glass monitoring and management capability for all disaster recovery needs. Full stack disaster recovery easily integrates Oracle platforms and non-Oracle applications and provides recovery for the entire application stack, instead of recovery of individual components, such as databases or compute instances.

Reviewed: 08.10.2026

# Team Publications

## Designing Full Stack Disaster Recovery

[Designing OCI Full Stack Disaster Recovery](./assets/designing-fsdr/README.md) provides guidance on defining application recovery boundaries, choosing moving or non-moving compute patterns, preparing replication and standby infrastructure, and organizing DR protection groups and recovery plans.

## Videos

- [Full Stack Disaster Recovery - MySQL HeatWave Step-by-Step Demo](https://www.youtube.com/watch?v=GVcT7Bq76hU)
    - Integrate MySQL HeatWave with Full Stack DR using preconfigured replication channels across OCI regions.
- [Full Stack Disaster Recovery - Integration of Oracle Kubernetes Engine](https://www.youtube.com/watch?v=S06FaJc5lHI)
    - Recover the MuShop application deployed on OKE and its associated Autonomous Database.
- [Full Stack Disaster Recovery - Enhanced DR Plan Management](https://www.youtube.com/watch?v=QyCzbKWTUkY&index=10&pp=iAQB)
    - Refresh existing DR plans after protection group member changes.
- [How to integrate Oracle EPM with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIzsIv-68QDYiqgahT3qq_yjf)
    - Configure recovery for Oracle Enterprise Performance Management across two OCI regions.
- [Full Stack Disaster Recovery - Use Capacity Reservation for moving instances](https://www.youtube.com/watch?v=XKrZfzeoo_A)
    - Use Compute Capacity Reservations when recovering moving instances.
- [Full Stack Disaster Recovery for File Storage Service](https://youtu.be/_Rhq5iPrl9k)
    - Integrate OCI File Storage with Full Stack DR using native member support.
- [Full Stack Disaster Recovery - Detach/Attach Block Volumes and Stop/Start a non-moving Compute Instance](https://youtu.be/GONlPCtQxqM)
    - Automate block volume attachment and detachment, and stop or start non-moving compute instances.
- [Full Stack Disaster Recovery for Load Balancer](https://youtu.be/dFd-Z1oBpjQ)
    - Add an OCI Load Balancer to a DR protection group.
- [OCI Full Stack Disaster Recovery, Video Series for a Custom Application](https://www.youtube.com/playlist?list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C)
    - A five-part video series demonstrating how to configure OCI Full Stack Disaster Recovery to automate and orchestrate disaster recovery for a custom application across two OCI regions, from creating DR protection groups to customizing, validating, and executing a switchover plan.
    - [Video 1: Introduction to the existing application deployment](https://www.youtube.com/watch?v=K9JgQnNBJT8&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=1)
        - Review the MuShop deployment and its DR prerequisites in both regions.
    - [Video 2: Create and Associate Disaster Recovery Protection Groups](https://www.youtube.com/watch?v=zpW_tBJwLmU&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=2)
        - Create and associate primary and standby DR protection groups.
    - [Video 3: Add members to the DR Protection groups](https://www.youtube.com/watch?v=byp0t35-xAU&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=3)
        - Add application resources as DR protection group members.
    - [Video 4: Create and Customize the DR Switchover Plan](https://www.youtube.com/watch?v=A3QsnIdW-r0&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=4)
        - Create a switchover plan in the standby protection group and add custom recovery steps.
    - [Video 5: Perform Prechecks and Execute Switchover](https://www.youtube.com/watch?v=uYLtJ85sE1A&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=5)
        - Run prechecks, execute the switchover, and validate the recovered application.

## Tutorials

- [Automate Recovery for MySQL HeatWave (OCI managed) as a native member](https://docs.oracle.com/en/learn/full-stack-dr-mysql-heatwave/index.html)
    - Automate MySQL HeatWave recovery using replication channels and native FSDR member support.
- [Automate Cold Disaster Recovery for Oracle HeatWave MySQL](https://docs.oracle.com/en/learn/full-stack-dr-heatwave-mysql/)
    - Automate MySQL HeatWave recovery from backups using Full Stack DR.
- [Automate Cold Disaster Recovery for OCI Database with PostgreSQL using OCI Full Stack Disaster Recovery](https://docs.oracle.com/en/learn/full-stack-dr-pgsql-cold-dr/index.html)
    - Automate OCI Database with PostgreSQL recovery from backups using Full Stack DR.
- [Automate recovery for Oracle EPM](https://docs.oracle.com/en/learn/fsdr-integration-epm/)
    - Automate recovery for Oracle Enterprise Performance Management.
- [Automate Disaster Recovery Plan Validation in OCI Using a Custom Precheck Tool](https://dev.to/amoubarak/automate-disaster-recovery-plan-validation-in-oci-using-a-custom-precheck-tool-1omo)
    - Run prechecks for all active plans in a DR protection group using a Python tool.

# Useful Links

## Videos

- [Deep dive playlist](https://www.youtube.com/playlist?list=PLKCk3OyNwIzuhTZbFY0d7pvbEUktcNqtH)
    - Explore OCI Full Stack Disaster Recovery concepts, architecture, and capabilities.
- [Full Stack DR : Implementing and Configuring](https://www.youtube.com/watch?v=dna14EPgkbM&list=PLKCk3OyNwIzsNFHC903WIJOfyrXZmeQoZ)
    - Configure and manage orchestrated recovery for application stacks across OCI regions.
- [How to integrate Oracle Analytics Cloud with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIztqvNuVwgsq5ahlGuRTSaBT)
    - Configure recovery for Oracle Analytics Cloud across OCI regions.
- [How to integrate PeopleSoft with Full Stack DR](https://www.youtube.com/watch?v=TCLlRwmGwlw&list=PLKCk3OyNwIzugTFmLTXnGv7-WZJ9omzt6)
    - Configure recovery for a single-instance PeopleSoft deployment across OCI regions.
- [How to integrate Oracle Integration Cloud with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIzuHnw1A3NZsMngfxBhN-M0p)
    - Automate disaster recovery for Oracle Integration across two OCI regions.
- [Oracle WebLogic Server with OCI Full Stack Disaster Recovery](https://www.youtube.com/watch?v=Ki-K_N6X-70&t=103s)
    - Integrate an Oracle WebLogic Server deployment from OCI Marketplace with Full Stack DR.
- [Automate Object storage recovery](https://www.youtube.com/watch?v=rMzcNMHWcjk)
    - Integrate an OCI Object Storage bucket with Full Stack DR to automate recovery.

## Tutorials

- [Move a virtual machine between OCI regions using Full Stack Disaster Recovery](https://docs.oracle.com/en/learn/full-stack-dr-to-move-vm/)
    - Move a compute VM with only a boot volume between OCI regions.
- [Non-moving instance new features](https://docs.oracle.com/en/learn/full-stack-dr-blkvolume-dr-drill/)
    - Attach and detach block volumes for non-moving compute instances using DR drill plans.
- [Automate Disaster Recovery switchover and failover operations for Oracle WebLogic Server with OCI Full Stack Disaster Recovery](https://docs.oracle.com/en/solutions/full-stack-dr-weblogic-platform)
    - Automate switchover and failover operations for Oracle WebLogic Server.
- [Oracle WebLogic Server for Oracle Cloud Infrastructure Disaster Recovery](https://www.oracle.com/a/otn/docs/middleware/maa-wls-mp-dr.pdf)
- [Automate DR for MuShop Demo Application Deployed on OKE with OCI Full Stack DR](https://docs.oracle.com/en/learn/full-stack-dr-oke-mushop)
    - Automate switchover and failover for the MuShop demo application deployed on OKE.
- [Automate recovery for Oracle Analytics Cloud ( OAC )](https://docs.oracle.com/en/learn/oci-full-stack-dr-integration-oac)
    - Configure recovery for Oracle Analytics Cloud as the sole application in the DR protection groups.
- [Automate recovery for Oracle Analytics Server (OAS)](https://blogs.oracle.com/analytics/post/oas-dr-fsdr)
    - Automate recovery for Oracle Analytics Server deployed on OCI.
- [Automate recovery for Oracle Integration (OIC)](https://docs.oracle.com/en/learn/fullstackdr-integration-oic/)
    - Automate recovery for Oracle Integration using Full Stack DR.
- [Automate recovery for PeopleSoft](https://docs.oracle.com/en/learn/full-stack-dr-integration-psft)
    - Automate recovery for a single-instance PeopleSoft deployment.
- [Prepare compute instance for run command](https://docs.oracle.com/en/learn/full-stack-dr-run-command)
    - Prepare a compute instance to execute custom recovery scripts through Run Command.
- [Create Full Stack DR resources using OCI CLI](https://docs.oracle.com/en/learn/full-stack-dr-oci-cli-command/)
    - Create Full Stack DR resources for a cold standby topology using OCI CLI.

## Other Useful Links

- [Documentation: Full Stack Disaster Recovery](https://docs.oracle.com/en-us/iaas/disaster-recovery/index.html)
- [Oracle.com: Full Stack Disaster Recovery](https://www.oracle.com/in/cloud/full-stack-disaster-recovery/)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
