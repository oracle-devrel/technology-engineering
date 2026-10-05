# Full Stack Disaster Recovery

Full Stack Disaster Recovery is an Oracle Cloud Infrastructure (OCI) disaster recovery orchestration and management service that provides comprehensive disaster recovery capabilities for all layers of an application stack, including infrastructure, middleware, database, and application.

Using OCI Full Stack DR provides a single pane of glass monitoring and management capability for all disaster recovery needs. Full stack disaster recovery easily integrates Oracle platforms and non-Oracle applications and provides recovery for the entire application stack, instead of recovery of individual components, such as databases or compute instances.

Reviewed: 05.10.2026

# Team Publications

## Videos

- [Full Stack Disaster Recovery - MySQL HeatWave Step-by-Step Demo](https://www.youtube.com/watch?v=GVcT7Bq76hU)
    - This video walk through the process of integrating a MySQL HeatWave DB System with Full Stack Disaster Recovery on OCI. As part of the demo, we’ve preconfigured inbound channel replication between two MySQL DB Systems deployed across different OCI regions.
- [Full Stack Disaster Recovery - Integration of Oracle Kubernetes Engine](https://www.youtube.com/watch?v=S06FaJc5lHI)
    - This video demonstrate how to integrate Oracle Kubernetes Engine (OKE) with Full Stack DR. As part of the demo, we have deployed the Mushop application in an OKE cluster, showcasing how Full Stack DR can recover both the Mushop application and its associated Autonomous Database. Please refer to the reference section to follow the step-by-step tutorial to set up the Mushop application in OKE.
- [Full Stack Disaster Recovery - Enhanced DR Plan Management](https://www.youtube.com/watch?v=QyCzbKWTUkY&index=10&pp=iAQB)
    - Previously, any changes made to the members within a protection group would result in the deletion of the DR plan. This required customers to recreate their DR plans from scratch, making the process time-consuming and inefficient.
- [How to integrate Oracle EPM with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIzsIv-68QDYiqgahT3qq_yjf)
    - Videos showing how to configure Full Stack DR to manage DR operations for Oracle Enterprise Performance Management(EPM) which is deployed across two OCI regions.
- [Full Stack Disaster Recovery - Use Capacity Reservation for moving instances](https://www.youtube.com/watch?v=XKrZfzeoo_A)
    - This video shows how to use Compute Capacity Reservation with Full Stack Disaster Recovery in a DR scenario.
- [Full Stack Disaster Recovery for File Storage Service](https://youtu.be/_Rhq5iPrl9k)
    - This video shows how Full Stack Disaster Recovery natively support File Storage Service.
- [Full Stack Disaster Recovery - Detach/Attach Block Volumes and Stop/Start a non-moving Compute Instance](https://youtu.be/GONlPCtQxqM)
    - Attach Block Volumes to, and Detach Block Volumes from a non-moving OCI VM instance with Full Stack DR with stop/start a non-moving Compute Instance.
- [Full Stack Disaster Recovery for Load Balancer](https://youtu.be/dFd-Z1oBpjQ)
    - This video show how to add a Load Balancer to a Disaster Recovery Protection Group of OCI Full Stack Disaster Recovery.
- [OCI Full Stack Disaster Recovery, Video Series for a Custom Application](https://www.youtube.com/playlist?list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C)
    - In this video series you will see how to use FSDR (Full Stack Disaster Recovery) for a Custom application to automate and orchestrate the DR plans between two OCI regions
- [Video 1: Introduction to the existing application deployment](https://www.youtube.com/watch?v=K9JgQnNBJT8&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=1)
    - In this video, we will see how the MuShop application is already deployed in OCI with all the DR capabilities in both OCI regions. These are the prerequisites for the application to work with Full Stack Disaster Recovery Service.
- [Video 2: Create and Associate Disaster Recovery Protection Groups](https://www.youtube.com/watch?v=zpW_tBJwLmU&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=2)
    - In this video, we will Create and Associate Disaster Recovery Protection Groups (DRPG). Ashburn is a primary region, and Phoenix is the standby region.
- [Video 3: Add members to the DR Protection groups](https://www.youtube.com/watch?v=byp0t35-xAU&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=3)
    - In this video, we will add members to the DR Protection groups created and associated in the previous video.
- [Video 4: Create and Customize the DR Switchover Plan](https://www.youtube.com/watch?v=A3QsnIdW-r0&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=4)
    - In this video, we will create a DR Switchover plan and customize the plan with additional steps (User Defined steps). DR Plan must be created in the standby region.
- [Video 5: Perform Prechecks and Execute Switchover](https://www.youtube.com/watch?v=uYLtJ85sE1A&list=PLKCk3OyNwIzt4gjcRbo2dA5DwsQPEWI5C&index=5)
    - In this video, we will execute Run Prechecks for the DR switchover plan created in the previous video. We will also execute the actual switchover plan. The switchover plan will execute the series of steps in the DR switchover plan. Finally, we will validate that the MuShop application is working properly in the DR region (Phoenix).

## Tutorials

- [Automate Recovery for MySQL HeatWave (OCI managed) as a native member](https://docs.oracle.com/en/learn/full-stack-dr-mysql-heatwave/index.html)
    - Automate Disaster Recovery for MySQL HeatWave with Replication Channels Using OCI Full Stack Disaster Recovery
- [Automate Cold Disaster Recovery for Oracle HeatWave MySQL](https://docs.oracle.com/en/learn/full-stack-dr-heatwave-mysql/)
    - Automate Cold (Backup/Restore) Disaster Recovery for Oracle HeatWave MySQL using OCI Full Stack Disaster Recovery
- [Automate Cold Disaster Recovery for OCI Database with PostgreSQL using OCI Full Stack Disaster Recovery](https://docs.oracle.com/en/learn/full-stack-dr-pgsql-cold-dr/index.html)
    - Automate Cold (Backup/Restore) Disaster Recovery for OCI Database with PostgreSQL using OCI Full Stack Disaster Recovery
- [Automate recovery for Oracle EPM](https://docs.oracle.com/en/learn/fsdr-integration-epm/)
    - Automate Recovery for Oracle Enterprise Performance Management using OCI Full Stack Disaster Recovery
- [Automate Disaster Recovery Plan Validation in OCI Using a Custom Precheck Tool](https://dev.to/amoubarak/automate-disaster-recovery-plan-validation-in-oci-using-a-custom-precheck-tool-1omo)
    - Automate Disaster Recovery Plan Validation in OCI Using a Custom Precheck Tool This Python-based tool automates the validation (precheck) of all active DR plans associated with an OCI Disaster Recovery Protection Group (DRPG)

# Useful Links

- [Deep dive playlist](https://www.youtube.com/playlist?list=PLKCk3OyNwIzuhTZbFY0d7pvbEUktcNqtH)
    - This series of videos covers the same exact deep dive presentation our Full Stack DR product managers give to cloud architects, engineers, OCI customers and Oracle partners
- [Full Stack DR : Implementing and Configuring](https://www.youtube.com/watch?v=dna14EPgkbM&list=PLKCk3OyNwIzsNFHC903WIJOfyrXZmeQoZ)
    - Videos to help you add and manage orchestrated recovery across OCI regions for your existing business systems (application stacks) using OCI Full Stack Disaster Recovery
- [How to integrate Oracle Analytics Cloud with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIztqvNuVwgsq5ahlGuRTSaBT)
    - Videos showing how to configure Full Stack DR to manage recovery for Oracle Analyics Cloud service across OCI regions
- [How to integrate PeopleSoft with Full Stack DR](https://www.youtube.com/watch?v=TCLlRwmGwlw&list=PLKCk3OyNwIzugTFmLTXnGv7-WZJ9omzt6)
    - Videos showing how to configure Full Stack DR to manage recovery for a single instance deployment of Oracle PeopleSoft Application across OCI regions
- [How to integrate Oracle Integration Cloud with Full Stack DR](https://www.youtube.com/playlist?list=PLKCk3OyNwIzuHnw1A3NZsMngfxBhN-M0p)
    - Videos showing how to configure Full Stack DR to manage DR operations for Oracle Integration which is deployed across two OCI regions
- [Oracle WebLogic Server with OCI Full Stack Disaster Recovery](https://www.youtube.com/watch?v=Ki-K_N6X-70&t=103s)
    - Integrate Oracle WebLogic server deployed using OCI marketplace image with Full Stack DR. Oracle WebLogic Server is a unified and extensible platform for developing, deploying and running enterprise applications, such as Java, for on-premises and in the cloud.
- [Automate Object storage recovery](https://www.youtube.com/watch?v=rMzcNMHWcjk)
    - In this video, Suraj Ramesh will show you how to integrate an object storage bucket with Full Stack DR.

- [Move a virtual machine between OCI regions using Full Stack Disaster Recovery](https://docs.oracle.com/en/learn/full-stack-dr-to-move-vm/)
    - To move a compute VM that has just a boot volume attached to it from one region to another region using Full Stack Disaster Recovery.
- [Non-moving instance new features](https://docs.oracle.com/en/learn/full-stack-dr-blkvolume-dr-drill/)
    - Use OCI Full Stack DR to Attach or Detach a Non-Moving Compute Block Volumes with DR Drill Plans
- [Automate Disaster Recovery switchover and failover operations for Oracle WebLogic Server with OCI Full Stack Disaster Recovery](https://docs.oracle.com/en/solutions/full-stack-dr-weblogic-platform)
    - To automate Disaster Recovery Switchover and Failover operations of Oracle WebLogic Server using OCI Stack Disaster Recovery.
- [Oracle WebLogic Server for Oracle Cloud Infrastructure Disaster Recovery](https://www.oracle.com/a/otn/docs/middleware/maa-wls-mp-dr.pdf)
- [Automate DR for MuShop Demo Application Deployed on OKE with OCI Full Stack DR](https://docs.oracle.com/en/learn/full-stack-dr-oke-mushop)
    - Automate a Switchover and Failover Plan for a Demo Application Deployed on OCI Kubernetes Engine with OCI Full Stack Disaster Recovery
- [Automate recovery for Oracle Analytics Cloud ( OAC )](https://docs.oracle.com/en/learn/oci-full-stack-dr-integration-oac)
    - This tutorial assumes that Oracle Analytics Cloud is the only application being added to the DR protection groups.
- [Automate recovery for Oracle Analytics Server (OAS)](https://blogs.oracle.com/analytics/post/oas-dr-fsdr)
    - Disaster Recovery of Oracle Analytics Server on Oracle Cloud using OCI Full Stack Disaster Recovery
- [Automate recovery for Oracle Integration (OIC)](https://docs.oracle.com/en/learn/fullstackdr-integration-oic/)
    - Automate Recovery for Oracle Integration using OCI Full Stack Disaster Recovery
- [Automate recovery for PeopleSoft](https://docs.oracle.com/en/learn/full-stack-dr-integration-psft)
    - Automate Recovery Operations for Single Instance Oracle PeopleSoft application with OCI Full Stack Disaster Recovery
- [Prepare compute instance for run command](https://docs.oracle.com/en/learn/full-stack-dr-run-command)
    - Invoke custom scripts using the run command with Oracle Cloud Infrastructure Full Stack Disaster Recovery
- [Create Full Stack DR resources using OCI CLI](https://docs.oracle.com/en/learn/full-stack-dr-oci-cli-command/)
    - Automate Full Stack Disaster Recovery with OCI CLI for a Cold Standby Topology


- [Documentation: Full Stack Disaster Recovery](https://docs.oracle.com/en-us/iaas/disaster-recovery/index.html)
- [Oracle.com: Full Stack Disaster Recovery](https://www.oracle.com/in/cloud/full-stack-disaster-recovery/)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
