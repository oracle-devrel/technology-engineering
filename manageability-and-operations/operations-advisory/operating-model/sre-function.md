<!--
    Owners: Manuela Fioramonti, Ralf Lange
    Last Change: 10 April 2024
    Review Status: Live
    Review Notes: -
-->


# SRE Function in Cloud Operating Model
When defining the Cloud Operating Model, the Site Reliability Engineering (SRE) function embodies the core of Cloud Operations.
SRE team will have a size of a minimun of 8 engineers for operations and on-call duties. There are several theories around the ideal ratio of SREs vs Developers. The truth is the magic number will change as the organization, and workloads, evolve and mature.
The more automation and AiOps are leveraged the less repetitive tasks and manual intervetion will be needed, allowing SRE team members to focus on the real egineering part.


# SRE Role in Day-2 Operations

**SRE** funtion encompasses reliability concepts into DevOps, focusing on designing and implementing highly scalable and resilient systems, addressing automatically potential and in-progress issues. In other words, each service can run an repair itself, extending the concept of 'autonomous' to virtually any service. 
[SRE on Git](https://github.com/dastergon/awesome-sre?tab=readme-ov-file#sre-tools).

**DevOps** is more a philosophy, than a function, focusing on streamlining development and deployment processes, increasing the speed at which new features are delivered. Tasks in development - Dev- and operations - Ops - are part of a continuous loop that includes building, deploying, testing, and monitoring applications and services.
To achieve this, [DevOps](https://docs.oracle.com/en-us/iaas/Content/GSG/Reference/getting-started-as-devops.htm) relies on methodologies, such as CI/CD, Agile Development and automation.

[OCI DevOps Service](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/devops/using/devops_overview.htm)
provides a powerful end-to-end platform for your DevOps practice, including private Git repositories as well as connection capability to GitHub, GitLab and other external repos.

1. Adopt a version control system in the form of a single repository.

2. Automate building, testing and deployment.

3. Exploit IaC.

4. Keep drift under control with configuration management tools such as [Ansible](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/API/SDKDocs/ansible.htm).

5. Include security to prevent and address vulnerability in the deployment cycle.

# SRE Best Practises and OCI Support for them

1. Define Service Level Objectives: these should be identified based on relevance to the business. Each organization will need to think it through, and most likely will define SLOs based on 'internal' SLOs, like resource utilization and response time, and 'end-users' SLOs like availabilty and end-user experience. They could also be device-dependent (like a Mobile Apps adoption or availability).

2. Unify the Observability platform, possibly with native SLOs features. OCI provides the capability to define thresholds and [custom metrics](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/publishingcustommetrics.htm) to achieve this. Besides, available plug-ins and APIs, can expose the same metrics available to external tools such as [Grafana](https://grafana.com/grafana/plugins/oci-metrics-datasource/).

3. Define granularity and frequency (resolution) of metrics collection based on architecture, usefulness and related effort/cost per metric. Review these parameters as your architecture evolves over time.

4. Implement Alerting tools for quick detection of potential issues. With [OCI Notifications](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm), you can easily detect and be notified in human-readable format, when something happens in OCI. Keep Alerts definition and triggering as simple as possible.

5. Leverage Automation. EaC -Everything as a Code- and Ansible support SRE work throught the entire lifecycle management, from provisioning to configuration changes. Ansible playbooks promote consistency and idempotency, for repetitive tasks as well as rollback when needed.

6. Use 'canary deployments' approach to minimize effects on a limited number of users and for early detection of defects. Select metrics, canary population and duration depending on the 

7. Automate remediation mechanisms. Once Notifications are implemented, automation can be easily achieved via [Functions](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm#automation). Examples may be from filing Jira Tickets to resizing VMs and many more.

8. Unify the ticketing platform: OCI gives the chance to integrate MyOracleSupport with your ticketing system via [Support Management APIs](https://docs.oracle.com/en-us/iaas/api/#/en/incidentmanagement/20181231/).

9. Define After Action Review Process (AAR) and post-mortem analysis.

10. Plan for Capacity. OCI offers a powerful tool to help you with forecasting your capacity needs via [Operations Insight](https://docs.oracle.com/en-us/iaas/operations-insights/doc/capacity-planning.html#GUID-B2A3E104-494B-46A5-9F3E-8E3977C9328F).

11. Avoid proliferation of tools and maximize integrations among those used.

12. Document standards, processes and tools.

13. Evolve your SRE ecosystem along your environment lifecycle.

