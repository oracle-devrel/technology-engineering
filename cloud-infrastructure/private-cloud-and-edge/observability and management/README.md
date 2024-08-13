# C3 OKE - Monitoring with OCI Log Analytics

## Introduction

This page details an all OCI solution for monitoring kubernetes clusters
running on a C3. 

## Overview

C3 includes an OKE compatible Kubernetes-as-a-Service that allows the
easy provisioning of kubernetes clusters. Currently the C3 contains no
utilities to aid the user in management of multiple clusters on the
rack, currently up to 20 per rack. While it is possible to use widely
available solutions for cluster management such as Rancher or Lens some
customers are looking for an \"all Oracle\" solution. Fortunately OCI
Log Analytics provides a [Kubernetes
solution](https://docs.oracle.com/en-us/iaas/logging-analytics/doc/kubernetes-solution.html)
that allows customers to:

>... to monitor and generate insights into your Kubernetes deployed in
OCI, third party public clouds, private clouds, or on-premises including
managed Kubernetes deployments.

This solution will allow a user to monitor C3 clusters from their OCI
tenancy across multiple C3 racks. There are 5 provided dashboards which
work with the solution\'s log and metric collection to visualise cluster
status.

![](LogAnalyticsDashboard.png)

The OCI Log Analytics solution for Kubernetes provides a push button
solution for registering OKE clusters running in OCI. For other clusters
such as non-OKE ones or those running on C3 there is an alternative
registration method using the [Helm](https://helm.sh/) package manager.
The helm packages and installation instructions are published by Oracle
in the
[oci-kubernetes-monitoring](https://github.com/oracle-quickstart/oci-kubernetes-monitoring/tree/main?tab=readme-ov-file)
GitHub repo. Once the pre-requisite OCI resources have been set up it\'s
possible to deploy the solution with a single helm install command
together with the customisations required per cluster. The solution will
deploy 3 elements to the target cluster: 

1.  An OCI Management Agent running in a pod. By default there is only a
    single instance of the management agent per cluster, additional
    replicas can be specified. 

    1.  The agent collects kubernetes specific metrics in the
        *mgmtagent_kubernetes_metrics* namespace.

2.  Log collectors running on each node. These collectors use the OCI
    Log Analytics log ingestion API to send OS, kubernetes and container
    logs to Log Analytics for future analysis.

3.  An OCI management discovery task running as a kubernetes cron job.
    This detects the required entities, e.g. clusters and nodes, and
    keeps changes to the cluster in sync.

## Summary of Prerequisites

There are some OCI prerequisites required to install the solution that
are listed in the [Pre-requisite
section](https://github.com/oracle-quickstart/oci-kubernetes-monitoring/tree/main?tab=readme-ov-file#pre-requisites)
in GitHub. These include: 

-   Initial onboarding of the OCI Log Analytics service in the parent
    tenancy. 

-   A Log Analytics Log Group. Note that the OCI Logging service also
    has a resource named Log Group! 

-   An [OCI Management Agent install
    key](https://docs.oracle.com/en-us/iaas/management-agents/doc/management-agents-administration-tasks.html#GUID-C841426A-2C32-4630-97B6-DF11F05D5712)
    must be created.

-   The user groups and policies required. 

    -   Note that a dynamic group is required for all the OCI management
        agents that the solution registers in the OCI tenancy. A policy
        that allows this dynamic group to use the OCI metrics service.

    -   A dynamic group for the OKE instances on the C3 will **not**
        allow workload identity propagation as per OCI OKE instances. 

    -   The solution deployed on C3 should use authentication based on a
        user principal with the OCI config file deployed within the
        pods. In the helm values override file the
        [*[authtype]{.underline}* should be set to
        *[config]{.underline}*](https://github.com/oracle-quickstart/oci-kubernetes-monitoring/blob/main/docs/FAQ.md#how-to-use-configfile-based-authz-user-principal-instead-of-default-authz-instance-principal-).
        A policy that allows the user group to upload to the Log
        Analytics service is also required.

-   The solution requires images to be pulled from external repositories
    therefore, if required, [a proxy should
    configured](https://docs.oracle.com/en-us/iaas/compute-cloud-at-customer/topics/oke/configuring-a-proxy.htm)
    in **all** the cluster\'s nodes (worker and master). This also
    implies that the master nodes **must** be configured with an [SSH
    public
    key](https://docs.oracle.com/en-us/iaas/compute-cloud-at-customer/topics/oke/creating-a-kubernetes-cluster.htm#:~:text=Your%20public%20SSH%20key.).

## Example Custom Values File

Helm allows default values to be overridden using a yaml file. This
example can be customised for cluster and tenancy specifics. 

### override-values.yaml ###

```yaml
global:
  # OCID for OKE cluster or a unique ID for other Kubernetes clusters. Use the ocid from C3.
  kubernetesClusterID: ocid1.cluster.rackserno.c3region.77777777777777777777777777777777777
  # Provide a unique name for the cluster. This would help in
  # uniquely identifying the logs and metrics data at OCI Logging Analytics
  # and OCI Monitoring respectively.
  kubernetesClusterName: auniqueclustername

oci-onm-logan:
  # Go to OCI Logging Analytics Administration, click Service Details,
  # and note the namespace value.
  ociLANamespace: namespace

  privileged: true

  # OCI Logging Analytics Log Group OCID
  ociLALogGroupID: ocid1.loganalyticsloggroup.oc1.uk-london-1.77777777777777777777777777777777777777

  # On C3 use config file based authenticatio
  authtype: config

  # OCI API Key Based authentication details. Required when authtype set to config
  oci:

    # Path to the OCI API config file. Ensure this matches the path in the config file below.
    path: /var/opt/.oci
    #Config file name
    file: config

    configFiles:
      config: |-
      # Replace each of the below fields with actual values.

      [DEFAULT]
      user=ocid1.user.oc1..auserinocitenancy
      fingerprint=AP:IK:EY:FI:NG:ER:PR:IN:T
      key_file=/var/opt/.oci/private.pem
      tenancy=ocid1.tenancy.oc1..parenttenancy
      region=an-ociregion-1
    private.pem: |-
      -----BEGIN RSA PRIVATE KEY-----
      UsersPEMprivatekey=
      -----END RSA PRIVATE KEY-----

oci-onm-mgmt-agent:
  mgmtagent:
  # Provide the base64 encoded content of the Management Agent Install
  # Key file. Copy file as per
  # https://docs.oracle.com/en-us/iaas/management-agents/doc/management-agents-administration-taskshtml#GUID-3101FB2F-D774-42CA-A461-A850F0A4087C
  # and base64 encode.
    installKeyFileContent: base64encodedinstallkey=
```

## Limitations and Alternatives

This solution is based on OCI\'s Log Analytics and as such is a
\"read-only\" solution, i.e. kubernetes resources can not be modified.
Drilling in to the details soon brings up underlying log entries rather
than deatils like k8s resource spec etc. \
There are associated log storage costs beyond 10GB , see
<https://www.oracle.com/uk/manageability/pricing/#logging-analytics>.

There are associated monitoring costs for metrics, see
<https://www.oracle.com/uk/manageability/pricing/#monitoring>.

As the OKE clusters on C3 are CNCF conformant then most other k8s
monitoring solutions should work, e.g. Rancher or Lens. In some cases it
may not be desirable to allow access by k8s cluster users to the OCI
Console and services like Log Analytics so a management utility running
on the C3, like Rancher, or running on the users workstation, like Lens,
may be a better choice.
