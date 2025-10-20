# Migrating Your Oracle Integration Cloud (OIC) Instance: Key Considerations
### Author : Harris Qureshi

Planning an OIC instance migration? Whether driven by compliance or business continuity, a successful move requires meticulous preparation. While the technical steps are relatively straightforward, ensuring a seamless transition depends on strategic planning. Migration may involve moving to a different region or even a different tenancy, both of which introduce technical considerations that must be carefully managed alongside operational and access requirements.

This article highlights some of the key areas you should address when planning your migration strategy. 

---

## 1. Migrating Integrations
Oracle provides an **Export/Import Utility** that helps you migrate design-time artifacts (integrations, connections, lookups, libraries, etc.) from one instance to another.  
Refer to the official documentation: [Export and Import Design-Time Metadata](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/export-and-import-design-time-metadata.html)

This ensures your core integration logic is replicated, but it’s only part of the migration picture.

---
10-oic-instance-migration-key-considerations
## 2. User and Access Management
- Users, roles, and access policies are not carried over automatically.  
- Recreate the necessary user and role assignments for the new instance.  
- Coordinate with your identity and access management (IAM) team to align with organizational security practices.

---

## 3. Endpoint and URL Updates
- The new instance will have a **different base URL**. All client systems consuming your APIs must be updated to point to the new endpoint.  
- If you are using **custom endpoints**, replicate the same setup on the new instance. If not, this might be a good opportunity to setup custom endpoints to future proof your system. Refer to official documentation [Configure Custom Endpoints](https://docs.oracle.com/en/cloud/paas/application-integration/oracle-integration-oci/configure-custom-endpoint-instance.html)


---

## 4. Network and IP Address Changes
- Your new instance IP Address may change. If you have whitelisted OIC IP addresses in firewalls or partner systems, you must update those with the new instance’s IPs.  
- Validate all firewall and security group changes before switching traffic.
- Refer to official documentation [Obtain the Inbound and Outbound IP Addresses of the Oracle Integration Instance](https://docs.oracle.com/en/cloud/paas/application-integration/oracle-integration-oci/viewing-outbound-ip-address-menu.html)

---

## 5. Audit and Activity Stream Data
- Audit logs and activity stream data **cannot be migrated** between instances.  
- If historical logs are required, take a backup in **OCI Logging Service**. Refer to the official documentation [Capture the Activity Stream of Integrations in the Oracle Cloud Infrastructure Console](https://docs.oracle.com/en/cloud/paas/application-integration/oracle-integration-oci/capture-activity-stream-oracle-cloud-infrastructure-console.html)

---

## 6. OIC File Server
- If you are using **OIC File Server**, configure the same folder structures, users, and permissions in the new instance.  
- Ensure client applications update their endpoints accordingly.

---

## 7. Connectivity Agent Setup
- If you are using **Connectivity Agents** in current instance, ensure you install and setup connectivity agent for the new instance.
- Verify Prerequisites: Ensure all required certificates are transferred and updated, necessary libraries are installed, and firewall rules are configured for the new environment.
- Test End-to-End Connectivity: Execute connection tests from the new agent to every system or application it will access, confirming successful authentication and data flow.
- Refer to official documentation [Install the Connectivity Agent](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/downloading-and-running-premises-agent-installer.html#GUID-21BC1C0D-D3F8-41EF-B1A8-070DF5C39BD7)
---

## 8. Private Endpoint Setup
- If you are using **Private Endpoint** in your current instance, ensure you setup private endpoint for the new instance also.
- Test all connections that are using private endpoint to ensure every system or application can be reached and connections test successfully.
- Refer to official documentation [Configure a Private Endpoint](https://docs.oracle.com/en/cloud/paas/application-integration/oracle-integration-oci/configure-private-endpoint-instance.html) 
---

## 9. Other Capabilities (VBCS, Process, etc.)

As Oracle Integration Cloud (OIC) offers a wide range of capabilities, the list above focuses primarily on integration. However, if you are using additional features such as Visual Builder (VBCS), B2B, Robotic Process Automation (RPA), Decisions, or Process Automation, each capability requires its own migration planning and execution.

For example, here are some points for:

### Process Automation Migration

You can export process applications from the old instance and import them to the new instance. Either from the UI or you can use Rest API for this task to automate it. Refer to official documentation of OPA Rest API [Process Applications REST Endpoints](https://docs.oracle.com/en/cloud/paas/process-automation/rest-api-proca/api-process-applications.html)

Here are some considerations after importing applications.

- **Reassign Users and Groups**  
  Application roles are migrated but their user/group memberships are not. Repopulate these in the new environment.

- **Update Process URLs**  
  If your process application is being called from client applications like OIC, VBCS or any third party system, the application URLs will change. Communicate the new endpoints to all consumers and update integrations.

- **Reconfigure Authentication**  
  Authentication credentials for REST/Integration connections are not exported. Re-enter all authentication details in the new instance.

- **Address In-Flight Instances**  
  Active tasks and processes do not migrate. Choose one:
  - Complete all open tasks before cutover, OR
  - Run both old and new applications in parallel temporarily

---

## 10. Beyond the Technical Migration

While the technical migration of design artifacts is straightforward, the true complexity lies in managing the operational dependencies that extend beyond the OIC platform itself. A successful cutover requires careful coordination to reconfigure client applications, update security policies, and preserve archival data for compliance. Ultimately, a seamless transition is achieved not just by moving the integration, but by proactively planning for these impacts, maintaining clear communication with all stakeholders, and validating the entire ecosystem through rigorous testing.

> **Important Note**: This article is intended as a guidance document to help plan your OIC migration and is not an exhaustive list of all possible considerations. The specific steps and requirements for your migration may vary depending on your environment, configurations, and business needs. Always refer to the official Oracle documentation and validate your approach in a non-production environment.

---


