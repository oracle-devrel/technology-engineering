# Disaster Recovery

Oracle Data Guard or Active Data Guard is the most effective solution to protect the data of any enterprise and make it available on a 24x7 basis in the face of disasters and other calamities. Data Guard or Active Data Guard is essential for Mission Critical Enterprise Database. Data Guard Cloud functionality includes MAA configuration, Data Guard role transitions, and Monitoring.
A database disaster is an event that causes DATA LOSS or SERIOUS DISRUPTION to applications and services. There can be various causes: power failure, hardware failure, cyber-attacks, natural disasters, fire, earthquakes, vandalism, human error, planned maintenance, or anything else. Most database server disasters cannot be prevented. Disaster Recovery provides SERVICE CONTINUITY in case of geographical disasters or planned outages by recovering or resuming services from a geographically different location. This page will help you get started to understand some basic requirements for Disaster Recovery Opportunities with Data Guard/Active Data Guard.

# Team Publications

## Training Videos

- [Provision Data Guard or Active Data Guard Virtual Machine Database Systems in OCI - Youtube](https://youtu.be/FKaJGB4IYDo?si=02tJyYj7GzR_6JVN)
    - This video shows how to create a Data Guard or Active Data Guard in Oracle Cloud Infrastructure on a single node database system on Virtual Machine.
- [Change Roles in Active Data Guard on Virtual Machine Database Systems- Switchover/Failover/Reinstate - Youtube](https://youtu.be/OqxQeIRCfIo?si=YQZuO-6VA8gkGWm7)
    - This video shows how to change roles in Data Guard or Active Data Guard in Oracle Cloud Infrastructure using the UI console. Oracle database operates in one of the two roles: primary or standby. Oracle Data Guard maintains the standby database by transmitting and applying redo data from the primary database.
- [Provision Active Data Guard on Two Node RAC Virtual Machine Database Systems - Youtube](https://youtu.be/9bilFD2oQaQ?si=SCYQzP0NUmy9-yd-)
    - This video shows how to create an Active Data Guard in Oracle Cloud Infrastructure on two node RAC Virtual Machine Database Systems using the UI.
- [Active Data Guard DML Redirection 19c - Youtube](https://youtu.be/VTuW0hWPRlM?si=6dfLBj4ejosRPvXj)
    - This video depicts Active Data Guard DML Redirection feature. This feature was introduced in 19c and allows you to perform occasional DML using a read only standby database.
- [Oracle Active Data Guard vs Storage Remote Mirroring - Youtube](https://youtu.be/xN4CkY2bJL0?si=nfu_TRhIW27J50tE)
    - Data replication is the process of copying data from one location to another, to ensure data availability and disaster recovery.Oracle Active Data Guard and Storage remote mirroring, are two common data replication solutions, used in enterprise environments.This video, is intended to provide a quick brief, as to why Oracle Active Data Guard is preferred, to traditional storage disaster recovery technologies.
- [Snapshot standby database on Autonomous Database on Dedicated Exadata Infrastructure and ExaCC - Youtube](https://youtu.be/-dLYp9k7BOs?si=dv7cS0Q-oF0IJzPq)
    - This video shows how to convert a physical standby database to a snapshot standby database on ADB-D using the OCI console.
- [Backup and restore from standby database for ExaDB-D and BaseDB - Youtube](https://youtu.be/8CVjWQ7lqsA?si=usFCqpBCu1XZUXmg)
    - In this short video let's explore the ability to backup and restore from a standby database for Oracle Exadata Database on Dedicated Infrastructure ExaDB-D and BaseDB with OCI Object storage as the backup destination.
- [Part-1 Deploy a Manual Oracle Database Data Guard in OCI using RMAN Restore from Service - Youtube](https://youtu.be/seZ0YUMaX7U?si=n14lTqCr3VYzL5pb)
    - In this video I will show how you can seamlessly deploy a Manual Oracle data guard in OCI using RMAN Restore from Service. To make it simple to understand I have broken the entire Configuration into these few Topics - Architecture and Use Cases, Prerequisites, Prepare the network and the database, deploy and then DR Readiness. Standby databases across Regions ensures disaster recovery, higher resiliency in the event of a Disaster. Data Guard enables you to quickly restore your workload to the standby database in OCI. In this video, we will be emulating a disaster recovery scenario in OCI Base database environment using RMAN restore from service. This video focuses on some primary use cases such as Multiple Data Guard environments in OCI Base Database, Multicloud Oracle Database for Azure Base Database Disaster Recovery, Hybrid Data Guard.
- [Part-2 Deploy a Manual Oracle Database Data Guard in OCI using RMAN Restore from Service - Youtube](https://youtu.be/KQg_qF5oSfg?si=mGu1YhgtK2JeybmS)
    - In this video we will see the DEMO to seamlessly deploy a Manual Oracle data guard in OCI using RMAN Restore from Service. Kindly refer to the video Part-1 - Deploy a Manual Oracle Database Data Guard in OCI using RMAN Restore from Service before watching this session. The primary database is in London and we are creating the standby database in Amsterdam. We are using putty to connect to the DB system VMs. The putty session with a grey background is the Primary system and the putty session with the white background is the standby system.
- [Disaster Recovery - Cross Region Active Data Guard on Exadata Database on Dedicated Infrastructure - Youtube](https://youtu.be/VsyjvJlBQzw?si=MP_5QXZEUULVsC9C)
    - This videos shows how to set up Cross Region Active Data Guard on Exadata Database on Dedicated Infrastructure in OCI using UI for Disaster Recovery.



## Technical Guides



## LiveLabs Workshops
- [Protect your data with Active Data Guard](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=625)
    - This workshop focuses on Creating Active Data Guard 19c in Oracle Cloud Infrastructure using the Oracle Cloud. Explore fundamentals of Active Data Guard on 19c. Perform switchover, failover, DML Redirection and more.
- [Active/Passive Data Recovery](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=715)
    - This workshop will leverage rsync to sync application files between the primary and DR servers, set up DR failover using Oracle Data Guard through the OCI console, and simulate DR for solution verification.
- [Oracle Database Hybrid Active Data Guard](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=609)
    - This workshop shows how to setup hybrid data guard from on-premise to Oracle Cloud Infrastructure. You will use a compute instance in the OCI to simulate the on-premise primary database, and provision a database system on OCI to act as the standby database in the cloud.
- [Setting Up Active Data Guard For On-Premises](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=873)
    - This workshop focuses on Creating Active Data Guard 19c on cloud compute systems. It will be similar to creating Active Data Guard on-premises. After creating the systems, you can proceed to the Active Data Guard Fundamentals LiveLab to explore the features such as DML redirect, automatic block media recovery.
- [Full Stack Disaster Recovery](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3357)
    - Join this lab to learn how easily you can automate the Full Stack Disaster Recovery orchestration for a Cloud-native Application deployed in OCI.



# Useful Links

- FAQs for Data Guard (Doc ID 2930929.1) (Login to MOS and search for Doc)
- [Disaster Recovery](https://www.oracle.com/cloud/backup-and-disaster-recovery/what-is-disaster-recovery/#cloud-based-deployment)
- [Data Guard Best Practices](https://docs.oracle.com/en/database/oracle/oracle-database/19/haovw/oracle-data-guard-best-practices.html)
- [Base DB - Oracle Data Guard Association](https://docs.oracle.com/en/cloud/paas/bm-and-vm-dbs-cloud/dataguard.html)
- [ExaC@C - Oracle Data Guard Association](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-using-data-guard.html#GUID-6EBC4D6A-C58B-4721-B756-F22FC6819A45)
- [ExaDB-D - Oracle Data Guard Association](https://docs.oracle.com/en/engineered-systems/exadata-cloud-service/ecscm/using-data-guard-with-exacc.html#GUID-6EBC4D6A-C58B-4721-B756-F22FC6819A45)
- [Architecture Centre - Reference Architecture - Deploy Exadata Database Service with Data Guard in a single region](https://docs.oracle.com/en/solutions/exacs-data-guard-single-region/index.html#GUID-D56ECB76-366B-44EC-B02E-6CFFD379E219)
- [Architecture Centre - Reference Architecture - Deploy Exadata Database Service with Data Guard in multiple regions](https://docs.oracle.com/en/solutions/exacs-data-guard-multi-region/index.html#GUID-F25AA974-B5AC-48BD-BF5A-37C1043EADFD)
- [OCI CLI - Command Reference for Data Guard Association](https://docs.oracle.com/en-us/iaas/tools/oci-cli/3.40.1/oci_cli_docs/cmdref/db/data-guard-association.html)
- [Introduction to Full Stack Disaster Recovery](https://www.youtube.com/watch?v=GiyFs8Cpksg&t=587s)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
