
# Using python SDK to create OCI Monitoring custom metric namespace: Services Limit monitoring example use case

## 1. INTRODUCTION
Describes how any user can create an OCI Monitoring ***custom metric namespace*** to being able to extend the default services metric namespaces. For that, we'll support on python SDK to create an script that can be run in an OCI VM (using instance principals authentication), or any other external system (using OCI IAM principals). To cover this educational example, we'll use as an example the creation of a custom metric namespace to monitor the OCI Services Limits usage. With this custom metric namespace, OCI alarms can be created and OCI Notification Service can be used to send the alarm information by different means to allow to create proactively a Service Limit Service Request to increase the limit before causing any disruption in the running services or services to be provisioned.

## 2. SOLUTION
We can see the overall architecture in the following logical diagram:

![Logical diagram](./files/Diagrams/custom-metrics-python-SDK-services-limit_solution1.png)

The script will take care of gathering the OCI Services Limits information and post as a custom metric namespace. The metrics where to post the data will be:

1. **used**: This is the amount of the Service Limit that it is being used
2. **max_limit**: This is the amount of the Service Limit that we can use (and increase with a SR)
3. **available**: This is the remaining amount of the Service Limit that we can use until get the max_limit
   
Not all the Services Limits are equal as they depend of the scope they have (Global, Regional or Availability Domain). We'll introduce the characteristics of a Service Limit as **Dimensions** of the metric, so we can select the Service Limit, the limit name and the scope to filter the specific limit. Thus, we'll have as **Dimensions**:

1. **service_name**: The name of the OCI Service that the Service Limit belongs to (e.g.: Compute)
2. **limit_name**: The name of the Service Limit (e.g.: bm-standard2-52-count)
3. **AD**: If the Service Limit has an AD availability, we can filter for the AD where we would like to filter the metric
 
With this raw data, we could be able to build Alarm Definitions on the specific Services Limits that we would like to monitor, as usually customers do not use all the possible OCI services.

Optionally, they could use any OCI Notification Service to being notified when the alarm fires receiving the notification message in any of the supported options. Some of them will enable the integration with 3rd party services.

## 3. SCRIPT'S LOGIC

Here we'll focus in reviewing the logic behind using the OCI Python SDK to get the objectives to monitor the Services Limits with OCI Monitoring.

We use 3 different OCI services API calls to gather the needed information to create the custom metric namespace for the Services Limit monitoring, these are:

1. [Identity and Access Management Service API](https://docs.oracle.com/en-us/iaas/api/#/en/identity/20160918/): To use the [ListAvailabilityDomains](https://docs.oracle.com/en-us/iaas/api/#/en/identity/20160918/AvailabilityDomain/ListAvailabilityDomains) API Call to get the list of the availability domains existing in the input tenancy.
2. [Monitoring API](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/): To use the [PostMetricData](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/MetricData/PostMetricData), to post the metrics information in the existing (or non yet existing) custom service metric namespace. If it doesn't exist yet, it just creates it so we don't need to explicitly create it before.
3. [Service Limits API](https://docs.oracle.com/en-us/iaas/api/#/en/limits/20181025/): To use the [ListLimitsDefinition](https://docs.oracle.com/en-us/iaas/api/#/en/limits/20181025/LimitDefinitionSummary/ListLimitDefinitions) to get the full list of Service Limits in a given compartment and the [GetResouceAvailability](https://docs.oracle.com/en-us/iaas/api/#/en/limits/20181025/ResourceAvailability/GetResourceAvailability), to gather the used and available limits depending in the scope (AD, regional, whole tenancy), of the known Service Limits from the previous list.
   
Basically the **logic** is:

````
Start
Gather the IAM user connection details from OCI Config
Set compartment_ocid
Initialize the clients for the different API calls (IAM, Monitoring, Service Limits)
Gather the full list of Service Limits Definitions sorted by Service Limit name
For the list of Service Limit names
    If the scope is Availability Domain
      For every AD
         Get the limits and usage for the Service Limit name within this AD
            Post in the custom metric namespace the metric with the dimension of the Service Limit, name and AD with the resources used, available and the service limit maximum
   For the non-AD Service Limit names (Global or Regional)
      Get the limits and usage for the Service Limit name 
            Post in the custom metric namespace the metric with the dimension of the Service Limit and name with the resources used, available and the service limit maximum
End
````

## 4. GETTING STARTED

To execute the script:

1. Ensure that the requirements are met with your desired variant (using IAM user or Instance Principals)
2. Upload the script into your administration VM inside OCI (IAM user or Instance Principals), or outside OCI (IAM user only)
3. Edit the script and put your OCI tenancy root compartment OCID in the compartment_ocid variable
4. To execute the script: 
   * For the IAM User principals authentication method, execute:
        ````
        $ python3 serviceLimitsMetricsIAM.py
        ````
        * The script is available [here](./files/Scripts/postServiceLimitsMetricsIAM.py)
   * For the Instance principal authentication method, execute:
        ````
        $ python3 serviceLimitsMetricsIP.py
        ````
        * The script is available **TBD**


## 5. REQUIREMENTS

We have different requirements depending on the variant of this asset that we would use:

1. **IAM User**
    * An existing OCI IAM user with an API signing key
    * An .oci/config profile for the tenancy, with the previous IAM user details
    * A policy granting the user to:
      * inspect resource-availability in tenancy
      * inspect limits in tenancy
      * use metrics in tenancy
  
2. **Instance Principal**
   * ***TBD***

3. ***Common requirements***
The VM where to run the script must have installed python3 with the following required packages installed with pip:
   *  **oci**

## 6. INPUT

The required input is the ***compartment_ocid*** with the OCID of your tenancy root compartment. Replace the value of the variable at the beginning of the script.

## 7. OUTPUT

Every time the script is run, it will feed a custom metric namespace called "**limits_metrics**" in the tenancy's root compartment with the information of the Services Limits usage.

You can check the custom metric extension from the OCI Metrics Explorer, where you will be able also to create an alarms from an specific metric query.

## 8.KNOWN PROBLEMS

None at this point.

## 9.RELEASE NOTES

There 2 scripts with same code except for the OCI authentication. Both scripts will be maintained in parallel with same versions:

2023-07-18 (version 0.1). Initial public release.





















## Objectives

* Overview of OCI Full Stack Disaster Recovery Service
* Gain knowledge on DR concepts and terminology and FSDR components
* Understand the different OCI interfaces available to manage FSDR service
* Explains how the service works
* Shows some typical use cases and supported OCI services OOB
* Shows how the provisioning operations can be done with the Console/OCI CLI
* Shows how the DR plan executions operations can be done with the Console/OCI CLI
* Provided OCI CLI Cheat Sheets

## Pre-requirements

* Basic knowledge of OCI Compute, Storage and DB Services
* Knowledge on Disaster Recovery practices are desired

## Inputs

N/A

## Outputs

[WorkshopFSDROperations_v0.2.pdf](./files/EXP#01o_WorkshopFSDROperations_v0.2.pdf)

## Stakeholders

* Architect teams
* Operation teams
* Development teams
  
## Guidelines

N/A

# Release notes

2023-07-12 (version 0.2). Initial public release.
  
# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
