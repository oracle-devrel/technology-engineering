# Oracle Database on Containers
Reviewed: "08.04.2024"

Oracle Database can be run in containers. Oracle offers convenient, containerized images (Podman and Docker) for a single instance, sharded, and Oracle Real Application Clusters (Oracle RAC) databases running on single or multiple hosts, reducing deployment and management work.

## Autonomous Database Free Container Image

ADB free container image comes pre-built with the following components exactly like our cloud offering:

- Apex
- Oracle Rest Data Services (ORDS)
- Database Actions including SQL Developer
- MongoDB API

Autonomous Database Free Container Image is now available on [Oracle Container Registry](https://container-registry.oracle.com/ords/f?p=113:4:110784766203219:::RP,4:P4_REPOSITORY,AI_REPOSITORY,P4_REPOSITORY_NAME,AI_REPOSITORY_NAME:2223,2223,Oracle%20Autonomous%20Database%20Free,Oracle%20Autonomous%20Database%20Free&cs=3iytyP0Ctunr3v0-nv7dCZfzaGtZqSixvp3qYkAgNzNQ1JCtVBaBA_eK_z3EK1p272JeUVOsEGVfeSXev4b1QEg), you can perform local development with an ADB free container image and have the ability to merge your work later in a cloud instance.


# Table of Contents
 
1. [Useful Links](#useful-links)

# Useful Links
- [Oracle Databases for Containers Home Page](https://www.oracle.com/uk/database/kubernetes-for-container-database/#containers)
- [Oracle Container Registry - DB Container images](https://container-registry.oracle.com/ords/f?p=113:1:34719206165212:::1:P1_BUSINESS_AREA:3&cs=3rBnBDYRNiptu1u8KdtUPwHirFedLIDGdBgu8CfXGsv0CrwBdI2-1OM6HOaUtgqyvEwMORUvVOmbJtIExSNWhWw)
- [Official source of container configurations, images, and examples for Oracle products and projects](https://github.com/oracle/docker-images/tree/main/OracleDatabase)
- [Running and Licensing Oracle Programs in Containers and Kubernetes](https://www.oracle.com/a/tech/docs/running-and-licensing-programs-in-containers-and-kubernetes.pdf)

## ADB Free Container Image
- [ADB Free Container Image Documentation](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-docker-container.html)
- [Introducing ADB Free Container Image (PM Blog)](https://blogs.oracle.com/datawarehousing/post/autonomous-database-free-container-image)
- [Deploy Oracle Autonomous Database Free Container Image on Mac with Apple Silicon](https://medium.com/oracledevs/deploy-oracle-autonomous-database-free-container-image-on-mac-with-apple-silicon-7857004c84)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
