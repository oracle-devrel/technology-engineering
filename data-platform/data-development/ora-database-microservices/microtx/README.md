# Oracle Transaction Manager for Microservices (MicroTX)
In microservices architectures, ensuring data consistency across distributed services can be challenging due to the lack of built-in transaction management. The "Dual Write" problem, where data updates must be written to multiple services or databases, often leads to inconsistencies. Tools like MicroTX are essential for managing these distributed transactions, maintaining data integrity, and simplifying development.

Oracle Transaction Manager for Microservices (**MicroTX or OTMM**) is a powerful tool designed to manage distributed transactions in a microservices architecture. It simplifies the microservices architecture and development, ensuring data consistency across multiple microservices without any additional code for compensation. MicroTx supports not only Oracle databases but also multiple datasource types, providing flexibility for various application requirements.

MicroTx supports various transaction models; the Saga pattern, Try Confirm/Cancel (TCC) pattern and two-phase commit (2PC), providing flexibility for different application requirements. It enables seamless integration and coordination of complex business processes across diverse microservices environments.

MicroTx is available in two editions:
  - **Oracle Transaction Manager for Microservices Free**: The Free version of MicroTx provides access to core transaction management features with a limitation of **100 transactions per minute**. This version is ideal for small-scale applications or for developers looking to explore OTMM capabilities without incurring costs.
  - **Oracle Transaction Manager for Microservices Enterprise**: The Enterprise version of MicroTx offers unlimited transactions per minute and includes advanced features, enhanced performance, and dedicated support. It is designed for large-scale, mission-critical applications requiring robust transaction management across multiple microservices.

Additionally, MicroTx provides libraries for the most popular development languages and frameworks, making it easy for developers to integrate and use MicroTx in their existing projects.

#### Oracle Transaction Manager for Microservices Enterprise main Features

##### Advanced Monitoring and Diagnostics
MicroTx Enterprise includes advanced monitoring and diagnostic tools that provide deep insights into transaction processing, helping identify and resolve issues quickly.

##### Enhanced Security Features
MicroTx Enterprise offers enhanced security features, including advanced encryption and access control mechanisms, to protect sensitive transaction data and ensure compliance with industry standards.

##### High Availability and Disaster Recovery
MicroTx Enterprise supports high availability and disaster recovery configurations, like transaction status persistence, ensuring that transaction processing can continue uninterrupted in the event of hardware failures or other disruptions.

##### Scalability
MicroTx Enterprise can handle a large number of transactions and scale horizontally to accommodate growing workloads, making it ideal for applications with high transaction volumes.

##### Dedicated Support
MicroTx Enterprise includes dedicated support from Oracle, offering expert assistance and quicker resolution of issues to ensure smooth operation of mission-critical applications.
Oracle Transaction Manager for Microservices provides a robust, high-performance solution for managing distributed transactions in a microservices architecture. By ensuring transactional integrity and offering flexible transaction models, MicroTx simplifies the development and operation of complex business processes, making it a powerful tool for modern applications.

Reviewed: "09.06.2024"

# Table of Contents

1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Tutorials / How To's](#tutorials--how-tos)
4. [License](#license)


# Team Publications
- Cloud Coaching Session: [Simplify Microservices Architectures: Oracle Transaction Manager for Microservices](https://www.youtube.com/watch?v=my4KMotFKwM&list=PLPIzp-E1msrZbCMh7NObbSSoI7q924MZS&index=1&t=7s)

# Useful Links
- [Oracle Transaction Manager for Microservices Whitepaper](https://www.oracle.com/docs/tech/oracle-transaction-manager-for-microservices.pdf)
- [Oracle Transaction Manager for Microservices Home Page](https://www.oracle.com/database/transaction-manager-for-microservices/)
- [Oracle Transaction Manager for Microservices Documentation](https://docs.oracle.com/en/database/oracle/transaction-manager-for-microservices/23.4/)
- [Oracle MicroTX Code Samples - Github](https://github.com/oracle-samples/microtx-samples)
- Video: [Transaction patterns for mission-critical microservices in Kubernetes](https://www.youtube.com/watch?v=fBXowP7X92k)
- Video: [Oracle Transaction Manager for Microservices High-Level Introduction](https://www.youtube.com/watch?v=4j74C4GobzY)


# Tutorials / How To's
- Oracle LiveLabs: [Maintain data consistency across microservices using Oracle MicroTx](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3445)
- Oracle LiveLabs: [Simplify distributed transactions with Oracle MicroTx to prevent inconsistent data and financial losses](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3725)
- Oracle LiveLabs: [Ensure data consistency in distributed transactions across ORDS applications using Oracle MicroTx](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3886)
- [Software project: Creating a real-life transactional microservices application on Kubernetes](https://medium.com/@mika.rinne/software-project-creating-a-real-life-transactional-microservices-application-on-kubernetes-ea490e9cdfa1)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
