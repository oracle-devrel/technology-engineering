# Oracle Integration Cloud

Oracle Integration (OIC) is an enterprise connectivity and automation platform for quickly modernizing applications, business processes, APIs, and data. Developers and cloud architects can connect SaaS and on-premises applications six times faster with a visual development experience, prebuilt integrations, and embedded best practices. Oracle Integration gives you native access to events in Oracle Cloud ERP, HCM, and CX. Connect app-specific analytic silos to simplify requisition-to-receipt, recruit-to-pay, lead-to-invoice, and other critical processes. Finally, give your IT and business leaders end-to-end visibility.

Review Date: 03.11.2023

# Team Publications

- [Make Filezilla talk to OICs' file server on Linux](http://aroundmiddleware.blogspot.com/2023/12/make-filezilla-talk-to-oics-file-server_22.html)

# Useful Links

- [Integration Partner & Developer Community - VideoHub Channel](https://videohub.oracle.com/channel/Oracle%2BPartner%2BCommunity)
  - Regular news and monthly webcast recordings from Product Management
- Articles
  - [Integration Blog](https://blogs.oracle.com/integration/)
  - [Niall Commiskey's Blog](http://niallcblogs.blogspot.com/)
  - [A-Team Chronicles](https://www.ateam-oracle.com/category/atm-integration)
- [EMEA Cloud Coaching On-Demand: AI and App Innovation](https://www.oracle.com/emea/cloud/events/cloud-coaching/on-demand/#ai-innovation)
  - Webcast recordings and on-demand videos created by Oracle EMEA Cloud Specialists
- [Integration Hands-On Bootcamps](https://go.oracle.com/LP=110450?elqCampaignId=296318)
- [LiveLabs](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/livelabs-workshop-cards) (filter on product *Oracle Integration Cloud*)
- [Reference Architectures](https://docs.oracle.com/solutions/?q=&cType=reference-architectures%2Csolution-playbook%2Cbuilt-deployed&product=Integration%20Generation%202%2CIntegration%20Cloud%20Service%2CIntegration%203%2CIntegration%20Adapters&sort=date-desc&lang=en)
- Oracle University - Learning Path and Certification - [Become an Application Integration Professional (2023)](https://mylearn.oracle.com/ou/learning-path/become-an-application-integration-professional-2023/122249)

## General Product Links

- [Oracle Integration Product Page](https://www.oracle.com/integration/application-integration/)
    - Official page for OIC 
- Oracle Integration Documentation
    - [Integration 3](https://docs.oracle.com/iaas/application-integration/index.html)
    - [OIC3 Guides](https://docs.oracle.com/en/cloud/paas/application-integration/books.html)
    - [Integration Generation 2](https://docs.oracle.com/en-us/iaas/integration/index.html)
    - [OIC Gen2 Guides](https://docs.oracle.com/en/cloud/paas/integration-cloud/books.html)
- Oracle Architecture Center
    - [Modern App Development - Messaging](https://docs.oracle.com/en/solutions/mad-messaging-pattern/index.html#GUID-48F3D3C1-CCD1-489B-8BE2-43D9289CA42C): Build messaging solutions that are highly available, reliable, and flexible
    - [Best practices for building resilient asynchronous integrations](https://docs.oracle.com/en/solutions/best-practices-resilient-asynch-integrations/index.html#GUID-B18DDA79-78FD-4767-BEE6-DB213B5EC073): Covers parking lot pattern in detail. In this pattern data is stored in an intermediary stage prior to complete processing the data from the intermediate stage to the end system.
    - [Practical Guide to use HCM Data Loader with Oracle Integration](https://blogs.oracle.com/integration/post/practical-guide-to-use-hcm-data-loader-with-oracle-integration): Covers tips and guides on how to use HCM Data Loader from OIC, steps required for initial setup on HCM side as well as working with nxsd file in OIC
    - [Learn about loading and extracting data in Oracle Human Resources Cloud](https://docs.oracle.com/en/solutions/data-loading-extraction-hcm-cloud/index.html#GUID-777CF4DC-5408-414C-960A-ED7D425DAA26): If you want to load or extract a lot of data with Oracle Human Resources Cloud, such as during batch migration, initial setup, or to integrate external data feeds, you may have difficulty choosing between the different tools. This solution describes the options that are available for bulk-loading and extracting your data in Oracle Human Resources Cloud.
    - [Simplify the process to import file-based data for enterprise resource planning (ERP)](https://docs.oracle.com/en/solutions/import-data-for-enterprise-resource-planning/index.html#GUID-9CE2963A-F66A-4A6B-BB18-0627C2832D11): The file-based data import process generates a file-based data import (FBDI) file, uploads the file to ERP, and then receives a callback from the ERP service. You can use Oracle Integration to schedule, package, load, and report on the success of data transfers into Oracle Enterprise Resource Planning Cloud
    - [Integration Design Patterns & Antipatterns](https://docs.oracle.com/en/cloud/paas/integration-cloud/integrations-user/common-integration-style-pitfalls-and-design-best-practices.html#GUID-09CEC808-3110-4EE4-9478-666A17451458): Common Integration Style Pitfalls and Design Best Practices
      - [Architectural principles](https://youtu.be/1LmJO2jC9G4)
      - [Integration types and common patterns](https://youtu.be/hs283FRfw4U)
      - [Integration anti-patterns: common pitfalls](https://youtu.be/2nqh780RQsc)
    - [HA and DR in OIC](https://www.oracle.com/a/ocom/docs/ha-dr-l300.pdf): High Availability Concepts and Architecture
    - [VPN, Fastconnect, Agent: private and public peering patterns](VPN, Fastconnect, Agent: private and public peering patterns): https://docs.oracle.com/en/cloud/paas/integration-cloud/integrations-user/integrations-concepts.html#GUID-1CBE5448-ACD2-40AB-9D65-0D4523CF7BBD

## OIC Live Labs

### Getting Started With Oracle Integration

This workshop shows you how to create two connections using Oracle Integration - One for File Server and one for an On Oracle Autonomous Database. You will learn how to create an integration flow that reads a file from File Server and insert records into Oracle Autonomous Database.

- https://apexapps.oracle.com/pls/apex/f?p=133:180:16648774210317::::wid:3231
- https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3430 (the same Gen3)

### Getting Started With Oracle Integration B2B

This workshop shows how to design and develop a B2B Integration in Oracle Integration that helps an Integration developer to onboard Trading Partners and exchange documents (for example Purchase Order, Invoices, etc) in a secured way using protocols like FTP, AS2

- https://apexapps.oracle.com/pls/apex/f?p=133:180:329245978004::::wid:880

### Oracle Integration - Cookbook - ERP Cloud Real-Time Synchronization

This workshop shows how to design and develop a Real-time Integration Usecase in Oracle Integration integrating with the ERP cloud. Out-of-the-box ERP Cloud adapter helps an Integration developer to quickly consume Business Events and Business Services in a secured way using various authentication schemes.

- https://apexapps.oracle.com/pls/apex/f?p=133:180:115416947475021::::wid:3232

### Oracle Integration - Experiential - ERP Business Events

The ERP Cloud Business Event Workshop will cover the recommended steps to complete an end-to-end use case based on ERP Cloud Business Events. This workshop will leverage the Oracle ERP Cloud Adapter, which enables you to create an integration with Oracle Enterprise Resource Planning (ERP) applications. One of the key differentiators of this adapter is support for subscribing to business events raised by various modules in Oracle ERP Cloud and Oracle Supply Chain Cloud. This workshop will showcase the event subscription capabilities to create an App Driven i.e., real-time integration, with updates in ERP Cloud sent immediately to a database table using orchestration with Oracle Integration. The steps outlined in this workshop can be used to demo the event-driven capabilities of the ERP Cloud adapter in Oracle Integration.

- https://apexapps.oracle.com/pls/apex/f?p=133:180:104975630545104::::wid:3150

### Oracle Integration 3 - Cookbook - ERP Cloud FBDI Import

This workshop shows you how to design and develop File-based Data Integration (FBDI) Import use cases in Oracle Integration 3 with the ERP Cloud. Out of the box, an ERP Cloud adapter helps an Integration developer quickly import the data into the ERP Cloud in a secure way using various authentication schemes

- https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3525

### Oracle Integration 3 - Understand Rest Adapter

This workshop shows you how to use REST Adapter as Trigger and Invoke a role using Oracle Integration 3 - You will learn how to create an integration flow that exposes the REST Interface and consumes OAuth-enabled REST API. In the bonus lab, you will learn how to secure OIC Integration Flow with OAuth.

- https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3697



## Other related content

- [Provision and configure OIC instance using Terraform](https://medium.com/oracledevs/provision-and-configure-oracle-integration-cloud-instance-using-terraform-6baa89c257a)
  

# Reusable Assets Overview

Relevant reusable assets can be found in subfolders and [Shared Assets](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/app-integration-and-automation/shared-assets) page.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
