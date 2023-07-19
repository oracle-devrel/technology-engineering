# Copyright (c) 2023 Oracle and/or its affiliates.

# The Universal Permissive License (UPL), Version 1.0

# Subject to the condition set forth below, permission is hereby granted to any
# person obtaining a copy of this software, associated documentation and/or data
# (collectively the "Software"), free of charge and under any and all copyright
# rights in the Software, and any and all patent rights owned or freely
# licensable by each licensor hereunder covering either (i) the unmodified
# Software as contributed to or provided by such licensor, or (ii) the Larger
# Works (as defined below), to deal in both

# (a) the Software, and
# (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
# one is included with the Software (each a "Larger Work" to which the Software
# is contributed by such licensors),

# without restriction, including without limitation the rights to copy, create
# derivative works of, display, perform, and distribute the Software and make,
# use, sell, offer for sale, import, export, have made, and have sold the
# Software and the Larger Work(s), and to sublicense the foregoing rights on
# either these or other terms.

# This license is subject to the following condition:
# The above copyright notice and either this complete permission notice or at
# a minimum a reference to the UPL must be included in all copies or
# substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

###
# This is a sample python script that post a custom metric (service_limits) to oci monitoring based on Tenancy Service Limits information.
# Run this script on any host with python with access to your tenancy.
# Command: python3 postServiceLimitsMetricsIP.py
# Version: 0.1
###

import oci,datetime,json
from pytz import timezone

# Vars:
# Replace here with your tenancy's root compartment OCID
compartment_ocid = "ocid1.tenancy.oc1....."

# Start:
now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
print("[", now,"] Starting OCI Service Metrics limits gathering and customer metrics post...")

# Setup the signer for the instance principal auth method
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

# We gather the list of availability domains in the region
identity_client = oci.identity.IdentityClient(config={}, signer=signer)
list_availability_domains_response = identity_client.list_availability_domains(compartment_id = compartment_ocid)

# Get the data from response
print(list_availability_domains_response.data)

# Initialize service client with default config file
#monitoring_client = oci.monitoring.MonitoringClient(config={}, signer=signer)
monitoring_client = oci.monitoring.MonitoringClient(config={},service_endpoint="https://telemetry-ingestion.eu-frankfurt-1.oraclecloud.com",signer=signer)

# Get Service Limits

# Initialize service client with default config file
limits_client = oci.limits.LimitsClient(config={}, signer=signer)

# Send the request to service, some parameters are not required, see API
# doc for more info
list_limit_definitions_response = limits_client.list_limit_definitions(
    compartment_id = compartment_ocid,
    sort_by="name",
    sort_order="ASC")

# We iterate the list of all the service limits
for x in list_limit_definitions_response.data:
    limit = json.loads(str(x))
    s_name = limit["service_name"]
    l_name = limit["name"]
    l_scope = limit["scope_type"]

    print ("Service: ", s_name, "Limit: ", l_name, "Scope: ", l_scope)
    
    # If the resource limit has an AD scope, we have to specify the AD or we'll get an API 400 response
    if l_scope == "AD" :
        # We have AD scope, we've to gather the limit for all the ADs in the region and include the availabilityDomain
        for AD in list_availability_domains_response.data:
            
            a_domain = json.loads(str(AD))
            print("Availability Domain: ", a_domain)

            # We gather the service limit usage
            get_resource_availability_response = limits_client.get_resource_availability(
            service_name = s_name,
            limit_name = l_name,
            compartment_id = compartment_ocid,
            availability_domain = a_domain["name"])
            usage = json.loads(str(get_resource_availability_response.data))
            used = usage["used"]
            available = usage["available"]

            # Get the data from response
            print(get_resource_availability_response.data)

            # We need to gather the service limit limit
            list_limit_values_response = limits_client.list_limit_values(
            compartment_id = compartment_ocid,
            service_name = s_name,
            availability_domain = a_domain["name"],
            limit = 1)
            limit_limit = json.loads(str(list_limit_values_response.data[0]))
            max_limit = limit_limit["value"]

            # Get the timestamp for setup the monitoring metric post information    
            times_stamp = datetime.datetime.now(timezone('UTC'))

            # Posting custom metrics to oci monitoring for each of the metrics (max, used, available)

            # Max limit
            post_metric_data_response = monitoring_client.post_metric_data(
                post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                    metric_data=[
                        oci.monitoring.models.MetricDataDetails(
                            namespace = "limits_metrics",
                            compartment_id = compartment_ocid,
                            name = "max_limit",
                            dimensions={
                                'service_name': s_name,
                                'limit_name': l_name,
                                'availability_domain': a_domain["name"]
                                },
                            datapoints=[
                                oci.monitoring.models.Datapoint(
                                    timestamp=datetime.datetime.strftime(
                                        times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                    value = max_limit)]
                            )]
                )
            )
            print("Max_limit: ", post_metric_data_response.data)

            # Used
            post_metric_data_response = monitoring_client.post_metric_data(
                post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                    metric_data=[
                        oci.monitoring.models.MetricDataDetails(
                            namespace = "limits_metrics",
                            compartment_id = compartment_ocid,
                            name = "used",
                            dimensions={
                                'service_name': s_name,
                                'limit_name': l_name,
                                'availability_domain': a_domain["name"]
                                },
                            datapoints=[
                                oci.monitoring.models.Datapoint(
                                    timestamp=datetime.datetime.strftime(
                                        times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                    value = used)]
                            )]
                )
            )
            print("Used: ", post_metric_data_response.data)

            # Available
            post_metric_data_response = monitoring_client.post_metric_data(
                post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                    metric_data=[
                        oci.monitoring.models.MetricDataDetails(
                            namespace = "limits_metrics",
                            compartment_id = compartment_ocid,
                            name = "available",
                            dimensions={
                                'service_name': s_name,
                                'limit_name': l_name,
                                'availability_domain': a_domain["name"]
                                },
                            datapoints=[
                                oci.monitoring.models.Datapoint(
                                    timestamp=datetime.datetime.strftime(
                                        times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                    value = available)]
                            )]
                )
            )
            print("Available: ", post_metric_data_response.data)

    else : 
        # We are in GLOBAL or REGION case

        # We gather the service limit usage
        get_resource_availability_response = limits_client.get_resource_availability(
        service_name = s_name,
        limit_name = l_name,
        compartment_id = compartment_ocid)
        usage = json.loads(str(get_resource_availability_response.data))
        used = usage["used"]
        available = usage["available"]

        # Get the data from response
        print(get_resource_availability_response.data)

        # We need to gather the service limit limit
        list_limit_values_response = limits_client.list_limit_values(
        compartment_id = compartment_ocid,
        service_name = s_name,
        limit = 1)
        limit_limit = json.loads(str(list_limit_values_response.data[0]))
        max_limit = limit_limit["value"]

        print(list_limit_values_response.data)

        print("max_limit: ", max_limit)
        if max_limit == "null" : 
            continue

        # Get the timestamp for setup the monitoring metric post information    
        times_stamp = datetime.datetime.now(timezone('UTC'))

        # Posting custom metrics to oci monitoring for each of the metrics (max, used, available)

        # Max limit
        post_metric_data_response = monitoring_client.post_metric_data(
            post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                metric_data=[
                    oci.monitoring.models.MetricDataDetails(
                        namespace = "limits_metrics",
                        compartment_id = compartment_ocid,
                        name = "max_limit",
                        dimensions={
                            'service_name': s_name,
                            'limit_name': l_name
                            },
                        datapoints=[
                            oci.monitoring.models.Datapoint(
                                timestamp=datetime.datetime.strftime(
                                    times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                value = max_limit)]
                        )]
            )
        )
        print("Max_limit: ", post_metric_data_response.data)

        print("used: ", used)
        if used is None : 
            continue

        # Used
        post_metric_data_response = monitoring_client.post_metric_data(
            post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                metric_data=[
                    oci.monitoring.models.MetricDataDetails(
                        namespace = "limits_metrics",
                        compartment_id = compartment_ocid,
                        name = "used",
                        dimensions={
                            'service_name': s_name,
                            'limit_name': l_name
                            },
                        datapoints=[
                            oci.monitoring.models.Datapoint(
                                timestamp=datetime.datetime.strftime(
                                    times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                value = used)]
                        )]
            )
        )
        print("Used: ", post_metric_data_response.data)

        # Available
        post_metric_data_response = monitoring_client.post_metric_data(
            post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                metric_data=[
                    oci.monitoring.models.MetricDataDetails(
                        namespace = "limits_metrics",
                        compartment_id = compartment_ocid,
                        name = "available",
                        dimensions={
                            'service_name': s_name,
                            'limit_name': l_name                            },
                        datapoints=[
                            oci.monitoring.models.Datapoint(
                                timestamp=datetime.datetime.strftime(
                                    times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                value = available)]
                        )]
            )
        )
        print("Available: ", post_metric_data_response.data)


# Finish:
now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
print("[", now,"] Finish OCI Service Metrics limits gathering and customer metrics post.")
