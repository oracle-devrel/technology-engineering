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
# Version: 0.2
###

import io, oci, datetime, logging, json

from pytz import timezone
from fdk import response

# Functions definition

# postMetric: posts custom monitoring metric information for compartment, metric(used,available,max_limit) and with its dimensions (service, limit name and availability domain(if AD specific))
def postMetric(compartment_ocid, m_name, s_name,l_name, value, monitoring_client, a_domain=None):
    # Get the timestamp for setup the monitoring metric post information    
    times_stamp = datetime.datetime.now(timezone('UTC'))
    if a_domain is None:
        post_metric_data_response = monitoring_client.post_metric_data(
            post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                metric_data=[
                    oci.monitoring.models.MetricDataDetails(
                        namespace = "limits_metrics",
                        compartment_id = compartment_ocid,
                        name = m_name,
                        dimensions={
                            'service_name': s_name,
                            'limit_name': l_name,
                            },
                        datapoints=[
                            oci.monitoring.models.Datapoint(
                                timestamp=datetime.datetime.strftime(
                                    times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                value = value)]
                        )]
            )
        )
    else:
        post_metric_data_response = monitoring_client.post_metric_data(
            post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                metric_data=[
                    oci.monitoring.models.MetricDataDetails(
                        namespace = "limits_metrics",
                        compartment_id = compartment_ocid,
                        name = m_name,
                        dimensions={
                            'service_name': s_name,
                            'limit_name': l_name,
                            'availability_domain': a_domain
                            },
                        datapoints=[
                            oci.monitoring.models.Datapoint(
                                timestamp=datetime.datetime.strftime(
                                    times_stamp,"%Y-%m-%dT%H:%M:%S.%fZ"),
                                value = value)]
                        )]
            )
        )
    return post_metric_data_response

# getServiceLimitsUsage: gets the existing limits for a service and limit name in a compartment and, if AD specific, for its AD
def getServiceLimitsUsage(s_name, l_name, compartment_ocid, limits_client, a_domain=None):
    if a_domain is None:
        # We gather the service limit usage
        get_resource_availability_response = limits_client.get_resource_availability(service_name = s_name, limit_name = l_name, compartment_id = compartment_ocid)

        # We need to gather the service limit limit
        list_limit_values_response = limits_client.list_limit_values(compartment_id = compartment_ocid, service_name = s_name, limit = 1)
    else:
        # We gather the service limit usage
        get_resource_availability_response = limits_client.get_resource_availability(service_name = s_name, limit_name = l_name, compartment_id = compartment_ocid, availability_domain = a_domain)

        # We need to gather the service limit limit
        list_limit_values_response = limits_client.list_limit_values(compartment_id = compartment_ocid, service_name = s_name, availability_domain = a_domain, limit = 1)

    usage = json.loads(str(get_resource_availability_response.data))
    used = usage["used"]
    available = usage["available"]
    limit_limit = json.loads(str(list_limit_values_response.data[0]))
    max_limit = limit_limit["value"]

    # We create the return type data dictionary
    values = {
        "used": used,
        "available": available,
        "max_limit": max_limit
    }
    return json.dumps(values)

def handler(ctx, data: io.BytesIO = None):

    resp={}
    resp["Result"] = "OK"
    logger = logging.getLogger()

    # We gather the input arguments from the function configuration:
    try:
       cfg = dict(ctx.Config())
       compartment_ocid = cfg["compartment_ocid"]
       region = cfg["region"]
    except (Exception, ValueError) as ex:
       logger.error(str(ex))

    # Start:
    logger.info("Starting OCI Service Metrics limits gathering and customer metrics post...")

    # Setup the signer for the resource principals auth method
    signer = oci.auth.signers.get_resource_principals_signer()
    
    # We gather the list of availability domains in the region
    identity_client = oci.identity.IdentityClient(config={'region': region}, signer=signer)

    # Let's check if the provided region is valid and it is among the subscribed regions
    try:
        list_regions_response = identity_client.list_regions()  
        for e in list_regions_response.data:
            reg = json.loads(str(e))
            if reg["name"] == region:
                break
        else:
            resp["Result"] = "NOT OK"
            resp["ERROR"] = "Wrong or non-subscribed OCI region."
            logger.error('Wrong or non-subscribed OCI region.')
            exit(1)
    except (Exception, ValueError) as ex:
        logger.error(str(ex))


    # Check tenancy compartment OCID given
    try:
        list_availability_domains_response = identity_client.list_availability_domains(compartment_id = compartment_ocid)
    except Exception as ex:
        resp["Result"] = "NOT OK"
        resp["ERROR"] = "The given compartment is wrong or you aren't authorized to list the availability domains."
        exit(1)

    service_endpoint = "https://telemetry-ingestion." + region + ".oraclecloud.com"

    # Initialize service client with default config file
    monitoring_client = oci.monitoring.MonitoringClient(config={'region': region},service_endpoint=service_endpoint, signer=signer)

    # Get Service Limits

    # Initialize service client
    limits_client = oci.limits.LimitsClient(config={'region': region}, signer=signer)

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
        
        # If the resource limit has an AD scope, we have to specify the AD or we'll get an API 400 response
        if l_scope == "AD" :
            # We have AD scope, we've to gather the limit for all the ADs in the region and include the availabilityDomain
            for AD in list_availability_domains_response.data:
                
                a_domain = json.loads(str(AD))

                limit_usage = json.loads(getServiceLimitsUsage(s_name, l_name, compartment_ocid, limits_client ,a_domain["name"]))

                # Posting custom metrics to oci monitoring for each of the metrics (max, used, available)

                # Max limit
                postMetric(compartment_ocid, "max_limit", s_name, l_name, limit_usage["max_limit"], monitoring_client, a_domain["name"])

                # Used
                postMetric(compartment_ocid, "used", s_name, l_name, limit_usage["used"], monitoring_client, a_domain["name"])

                # Available
                postMetric(compartment_ocid, "available", s_name, l_name, limit_usage["available"], monitoring_client, a_domain["name"])

        else : 
            # We are in GLOBAL or REGION case

            limit_usage = json.loads(getServiceLimitsUsage(s_name, l_name, compartment_ocid, limits_client))

            max_limit = limit_usage["max_limit"]
            used = limit_usage["used"]

            if max_limit == "null" : 
                continue

            # Posting custom metrics to oci monitoring for each of the metrics (max, used, available)

            # Max limit
            postMetric(compartment_ocid, "max_limit", s_name, l_name, max_limit, monitoring_client)

            if used is None : 
                continue

            # Used
            postMetric(compartment_ocid, "used", s_name, l_name, used, monitoring_client)

            # Available
            postMetric(compartment_ocid, "used", s_name, l_name, limit_usage["available"], monitoring_client)


    # Finish:
    logger.info("Finish OCI Service Metrics limits gathering and customer metrics post.")
    return resp
