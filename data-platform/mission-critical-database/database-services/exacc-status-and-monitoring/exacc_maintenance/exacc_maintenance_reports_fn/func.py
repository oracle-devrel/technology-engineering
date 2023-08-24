# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
#
# This OCI function is called by OCI Events when a group of ExaCC Exadata Infrastructures
# is being patched during quarterly maintenances
#
# This function:
# 1) generates or updates an ExaCC maintenance report (HTML file) and store it in an exising OCI bucket
# 2) send a first email to a list of email addresses when the maintenance starts
#    This email contains an HTML link (using a PAR) to the HTML file.
#    By clicking the link, users can following the progress of the Exadata Infrastructure maintenance
# 3) send a second email to the same list of email addresses when the maintenance completes
#    note: the SMTP Email Server can be from OCI Email Delivery service or NOT
#
# Prerequisites:
# - Python 3.9 (for resp = resp | function() )
# - Object storage bucket to store reports and temporary files
# - Pre-authenticated request (PAR) allowing reads on the bucket (can read all objects)
# - Dynamic Group for the function with following matching rule
#   resource.id = '<ocid_function>'
# - Identity Policy to give required permissions to FaaS service and to the specific function (via dynamic group)
#   required statements:
#       "Allow dynamic-group <dg_name> to read exadata-infrastructures in tenancy",
#       "Allow dynamic-group <dg_name> to read buckets in compartment id <cpt_id> where target.bucket.name='<bucket_name>'",
#       "Allow dynamic-group <dg_name> to manage objects in compartment id <cpt_id> where target.bucket.name='<bucket_name>'",
#       "Allow service FaaS to use virtual-network-family in compartment id <cpt_id>",
#       "Allow service FaaS to read repos in tenancy" 
# - Configure following variables (keys/values) in the Function configuration:
#   bucket_name              : name of the object storage bucket used
#   bucket_region            : region containing the bucket (possibly different than the exacc region)
#   par_for_bucket_read      : a pre-authenticated request allowing read on the bucket (must end with /)
#   exainfra_group_name      : name of the ExaCC group
#   exainfra_ids             : comma separated list of Exadata infrastructure OCIDs belonging to the group
#   email_sender             : email address of the sender     
#   email_sender_name        : email name of the sender  
#   email_recipients         : email addresses of the recipients (list of email addresses separated by comma)
#   email_smtp_user          : user used to connect to SMTP server
#   email_smtp_host          : DNS hostname of the SMTP server
#   email_smtp_port          : port of the SMTP server (usually 587)
#   email_smtp_pwd_secret_id : OCID of OCI vault secret containing password used to connect to SMTP server
#   vault_secret_region      : region containing the vault secret
#
# Author       : Christophe Pauliat
#
# Versions
#    2022-05-03: Initial Version
#    2022-06-13: Modify the code to archive the reports in the bucket 
#                Use an existing PAR allowing reads on all objects in the bucket
#                Generate an index.html object in the bucket to browse archives reports
#    2022-06-14: Use a specific region for the bucket 
#                Use a specific region for the vault secret for emails 
#                (single bucket and single vault secret in one region for exacc machines in different regions)
# ----------------------------------------------------------------------------------------------------

# -------- import
import io
import json
import logging
import fdk.response
import smtplib
import email.utils
import oci
import base64
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

# -------- global variables
current_exainfra_group_name  = ""
current_exainfra_group_ids   = []
report_object_name_prefix    = "ExaCC_maintenance_report" 
report_object_name           = ""   
tempo_prefix                 = "tempo_data"
access_type                  = "ObjectRead"
datetime_format              = "%b %d %Y, %H:%M %Z"
email_smtp_pwd               = ""
IdentityClient               = ""
ObjectStorageClient          = ""
DatabaseClient               = ""
namespace                    = ""
compartments                 = []
RootCompartmentID            = ""

cfg_par_for_bucket_read      = ""
cfg_email_sender             = ""     
cfg_email_sender_name        = ""  
cfg_email_recipients         = ""
cfg_email_smtp_user          = ""
cfg_email_smtp_pwd_secret_id = ""
cfg_email_smtp_host          = ""
cfg_email_smtp_port          = ""
cfg_bucket_name              = ""
cfg_bucket_region            = ""
cfg_vault_secret_region      = ""
cfg_exainfra_groups          = []

# -------- Functions

# ---- Get the complete name of a compartment from its id, including parent and grand-parent..
def get_cpt_full_name_from_id(cpt_id):

    if cpt_id == RootCompartmentID:
        return "root"

    name=""
    for c in compartments:
        if (c.id == cpt_id):
            name = c.name
    
            # if the cpt is a direct child of root compartment, return name
            if c.compartment_id == RootCompartmentID:
                return name
            # otherwise, find name of parent and add it as a prefix to name
            else:
                name = get_cpt_full_name_from_id(c.compartment_id) + ":" + name
                return name

    return "Not-Found"

# ---- send an email
def send_email (email_subject, email_body_text, email_body_html):

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject
    msg['From']    = email.utils.formataddr((cfg_email_sender_name, cfg_email_sender))
    msg['To']      = cfg_email_recipients

    # Record the MIME types: text/plain and html
    part1 = MIMEText(email_body_text, 'plain')
    part2 = MIMEText(email_body_html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # send the EMAIL
    email_recipients_list = cfg_email_recipients.split(",")
    server = smtplib.SMTP(cfg_email_smtp_host, cfg_email_smtp_port)
    server.ehlo()
    server.starttls()
    #smtplib docs recommend calling ehlo() before & after starttls()
    server.ehlo()
    server.login(cfg_email_smtp_user, email_smtp_pwd)
    server.sendmail(cfg_email_sender, email_recipients_list, msg.as_string())
    server.close()

# ---- Send the first email notifying maintenance has started
def send_first_email():
    par_uri         = f"{cfg_par_for_bucket_read}{report_object_name}"
    email_subject   = f"Maintenance STARTED for ExaCC Exadata infrastructures group {current_exainfra_group_name}"
    email_body_text = ( f"The quarterly maintenance for Exadata Cloud @ Customer group {current_exainfra_group_name} just STARTED.\n\n"
                        f"You can follow the progress of the maintenance using the following link: \n{par_uri}\n" )
    email_body_html = ( f"The quarterly maintenance for Exadata Cloud @ Customer group <span style=\"color:#0000FF\";><b>{current_exainfra_group_name}</b></span> just STARTED.<br><br>"
                        f"You can follow the progress of the maintenance <a href=\"{par_uri}\">HERE<br>" )
    try:
        send_email (email_subject, email_body_text, email_body_html)
        resp = { "send_first_email()" : "SUCCESS: Email sent !" }
    except Exception as err3:
        resp = { "send_first_email()": f"ERROR during emailing: " + str(err3) }

    return resp

# ---- Send the second email notifying maintenance has completed
def send_second_email():
    # read the HTML content of the report
    response = ObjectStorageClient.get_object(
                    namespace_name  = namespace,
                    bucket_name     = cfg_bucket_name,
                    object_name     = report_object_name,
                    retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY)
    html_content = response.data.text

    email_subject   = f"Maintenance COMPLETED for ExaCC Exadata infrastructures group {current_exainfra_group_name}"
    email_body_text = ( f"The quarterly maintenance for Exadata Cloud @ Customer group '{current_exainfra_group_name}' just COMPLETED.\n\n" 
                        f"The maintenance report is stored as object {report_object_name} in OCI bucket {cfg_bucket_name}\n" )
    email_body_html = ( f"The quarterly maintenance for Exadata Cloud @ Customer group <span style=\"color:blue\"><b>{current_exainfra_group_name}</b></span> just COMPLETED.<br><br>"
                        f"The maintenance report is stored as object <span style=\"color:blue\"><b>{report_object_name}</b></span> "
                        f"in OCI bucket <span style=\"color:blue\"><b>{cfg_bucket_name}</b></span>. <br><br>" 
                        f"It is also shown below.<br><br>"
                        f"NOTE: You can browse all archived reports <a href=\"{cfg_par_for_bucket_read}index.html\">HERE</a><br><hr>")
    email_body_html += html_content   
    try:
        send_email (email_subject, email_body_text, email_body_html)
        resp = { "send_second_email()" : "SUCCESS: Email sent !" }
    except Exception as err3:
        resp = { "send_second_email()": f"ERROR during emailing: " + str(err3) }

    return resp

# ---- Read temporary objects in bucket containing event data
def get_exainfras():
    # initialize returned variable
    exaInfrasEvents = {}
    for exaInfraId in current_exainfra_group_ids:

        # Use an API call to get some details about the exaInfra
        response = DatabaseClient.get_exadata_infrastructure(
                      exadata_infrastructure_id = exaInfraId, 
                      retry_strategy            = oci.retry.DEFAULT_RETRY_STRATEGY)
        nb_dbservers = int(response.data.compute_count)

        # initialize events dictionary for the exaInfra
        events = {}
        events["exaInfraName"]                      = response.data.display_name
        events["compartmentId"]                     = response.data.compartment_id
        events["computeCount"]                      = nb_dbservers
        events["maintenance.begin"]                 = "..."
        events["maintenancecustomactiontime.begin"] = [ "..." ] * nb_dbservers 
        events["maintenancecustomactiontime.end"]   = [ "..." ] * nb_dbservers
        events["maintenancevm.begin"]               = [ "..." ] * nb_dbservers 
        events["maintenancevm.end"]                 = [ "..." ] * nb_dbservers
        events["maintenancestorageservers.begin"]   = "..."
        events["maintenancestorageservers.end"]     = "..."
        events["maintenancenetworkswitches.begin"]  = "..."
        events["maintenancenetworkswitches.end"]    = "..."
        events["maintenance.end"]                   = "..."
        events["maintenanceStatus"]                 = "NOT STARTED"

        # get the list of objects for a specific exaInfraId
        response = ObjectStorageClient.list_objects(
            namespace_name  = namespace,
            bucket_name     = cfg_bucket_name,
            prefix          = f"{tempo_prefix}/{current_exainfra_group_name}/{exaInfraId}",
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        objects_list = response.data.objects

        # read every event object from this list
        for object in objects_list:
            response = ObjectStorageClient.get_object(
                namespace_name  = namespace,
                bucket_name     = cfg_bucket_name,
                object_name     = object.name,
                retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY)
            event_dict = json.loads(response.data.text)

            event_type = event_dict["eventType"].replace("com.oraclecloud.databaseservice.exaccinfrastructure","")
            if event_type in [ "maintenance.begin",                "maintenance.end", 
                               "maintenancestorageservers.begin",  "maintenancestorageservers.end", 
                               "maintenancenetworkswitches.begin", "maintenancenetworkswitches.end" ]:
                events[event_type] = event_dict["eventTime"]
            elif event_type in ["maintenancevm.begin",               "maintenancevm.end", 
                                "maintenancecustomactiontime.begin", "maintenancecustomactiontime.end"]:
                dbserver_num = event_dict["dbserver"]   # example: 1, 2, 3, 4 for Half Rack
                events[event_type][int(dbserver_num) - 1] = event_dict["eventTime"]

            # maintenance status:
            if event_type == "maintenance.begin":
                status_begin = event_dict["lifecycleState"]
            elif event_type == "maintenance.end":   
                status_end   = event_dict["lifecycleState"]

        # maintenance status
        if events["maintenance.begin"] != "..." and events["maintenance.end"] == "...":
            events["maintenanceStatus"] = status_begin      # should be IN_PROGRESS
        elif events["maintenance.end"] != "...":
            events["maintenanceStatus"] = status_end        # should be SUCCEEDED or FAILED

        # save data events for a specific exaInfraId in a Python dictionary
        exaInfrasEvents[exaInfraId] = events

    return exaInfrasEvents

# ---- Generate the HTML report and store it in the bucket
def generate_and_store_report(region, exaInfras_events):
    # Get current Date and Time (UTC timezone)
    now_str = datetime.now(timezone.utc).strftime("%c %Z")

    # For each ExaCC, check if custom action is enabled
    custom_action_enabled = {}
    for exaInfraId in current_exainfra_group_ids:
        custom_action_enabled[exaInfraId] = False
        for dbsrv in range(exaInfras_events[exaInfraId]["computeCount"]):
            if exaInfras_events[exaInfraId]["maintenancecustomactiontime.begin"][dbsrv] != "..." or exaInfras_events[exaInfraId]["maintenancecustomactiontime.end"][dbsrv] != "...":
                custom_action_enabled[exaInfraId] = True
                break

    # Generate HTML content

    # begining of HTML report
    html_content = """
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <meta http-equiv="refresh" content="10">
    <title>ExaCC maintenance report</title>
    <style type="text/css">
      tr:nth-child(odd) {
        background-color: #f2f2f2;
      }
      tr:hover {
        background-color: #ffdddd;
      }
      table {
        border-collapse: collapse;
        font-family: Arial;
      }
      th {
        background-color: #ebccff;
      }
      tr {
        background-color: #fff5f0;
      }
      th,
      td {
        border: 1px solid #808080;
        text-align: center;
        padding: 7px;
      }
      caption {
        caption-side: bottom;
        padding: 10px;
        align: right;
        font-style: italic;
      }
      .inprogress {
        background-color: orange;
        color: black
      }
      .succeeded {
        background-color: green;
        color: white       
      }
      .failed {
        background-color: red;
        color: white       
      }
      .notstarted {
        background-color: blue;
        color: white  
      }
    </style>
  </head>
    """

    html_content += f"""
  <body>
    <h1>Maintenance report for ExaCC Exadata infrastructures group <span style="color:blue">{current_exainfra_group_name}<span></h1>
    <h2>Summary</h2>
    """    

    # -- display summary table for all exaInfras
    html_content += f"""
    <table>
      <caption>
        Date and time of report : <b>{now_str}</b>
      </caption>
      <tbody>
        <tr>
          <th>Region</th>
          <th>Compartment</th>
          <th>Name</th>
          <th>OCID</th>
          <th>Maintenance status</th>
          <th>Maintenance start</th>
          <th>Maintenance end</th>
        </tr>
    """

    for exaInfraId in current_exainfra_group_ids:
        cpt_full_name = get_cpt_full_name_from_id(exaInfras_events[exaInfraId]["compartmentId"])
        if exaInfras_events[exaInfraId]["maintenanceStatus"] == "SUCCEEDED":
            myclass = "succeeded"
        elif exaInfras_events[exaInfraId]["maintenanceStatus"] == "FAILED":
            myclass = "failed"
        elif exaInfras_events[exaInfraId]["maintenanceStatus"] == "IN_PROGRESS":
            myclass = "inprogress"
        else:
            myclass = "notstarted"
        html_content += f"""
        <tr>
          <td>&nbsp;{region}&nbsp;</td>
          <td>&nbsp;{cpt_full_name}&nbsp;</td>
          <td>&nbsp;<a href="#{exaInfras_events[exaInfraId]["exaInfraName"]}">{exaInfras_events[exaInfraId]["exaInfraName"]}</a>&nbsp;</td>
          <td>&nbsp;...{exaInfraId[-6:]}&nbsp;</td>
          <td class="{myclass}">&nbsp;<b>{exaInfras_events[exaInfraId]["maintenanceStatus"]}&nbsp;</b></td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenance.begin"]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenance.end"]}&nbsp;</td>
        </tr>
    """

    html_content += """
      </tbody>
    </table>
    """

    # -- for each exaInfra, display detailed table
    for exaInfraId in current_exainfra_group_ids:
        html_content += f"""
    <h2 id="{exaInfras_events[exaInfraId]["exaInfraName"]}">
      Detailed report for <span style="color:blue">{exaInfras_events[exaInfraId]["exaInfraName"]}</span></h2>
    <table>
      <caption>
        Date and time of report : <b>{now_str}</b>
      </caption>
      <tbody>
        <tr>
          <th>Maintenance operation</th>
          <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Start &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
          <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; End &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
        </tr>
        """

        html_content += f"""
        <tr>
          <td style="text-align: left">&nbsp;Entire maintenance</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenance.begin"]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenance.end"]}&nbsp;</td>
        </tr>
        """

        for dbsrv in range(exaInfras_events[exaInfraId]["computeCount"]):
            if custom_action_enabled[exaInfraId]:
                html_content += f"""
        <tr>
          <td style="text-align: left">&nbsp;db server #{dbsrv + 1} : custom action</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancecustomactiontime.begin"][dbsrv]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancecustomactiontime.end"][dbsrv]}&nbsp;</td>
        </tr>
                """

            html_content += f"""
        <tr>
          <td style="text-align: left">&nbsp;db server #{dbsrv + 1} : maintenance</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancevm.begin"][dbsrv]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancevm.end"][dbsrv]}&nbsp;</td>
        </tr>
            """

        html_content += f"""
        <tr>
          <td style="text-align: left">&nbsp;storage servers maintenance</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancestorageservers.begin"]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancestorageservers.end"]}&nbsp;</td>
        </tr>
        <tr>
          <td style="text-align: left">&nbsp;network switches maintenance</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancenetworkswitches.begin"]}&nbsp;</td>
          <td>&nbsp;{exaInfras_events[exaInfraId]["maintenancenetworkswitches.end"]}&nbsp;</td>
        </tr>
      </tbody>
    </table>
        """

    # End of report
    html_content += f"""
  </body>
</html>
    """

    # Save report to bucket
    response = ObjectStorageClient.put_object(
        namespace_name  = namespace,
        bucket_name     = cfg_bucket_name,
        object_name     = report_object_name,
        put_object_body = html_content,
        content_type    = "text/html",
        retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

    return { "generate_and_store_report()": "OK"}

# ---- Store Event information in an object storage temporary file
def store_event_in_bucket(eventType, eventTime, exaInfraName, exaInfraId, cptId, message, maintenanceMode, lifecycleState):
    content = {}
    # example of date time contained in Event:  2022-04-23T01:00:21Z
    event_datetime = datetime.fromisoformat(eventTime[:-1]).astimezone(timezone.utc)
    content["eventTime"]       = event_datetime.strftime(datetime_format)
    content["eventType"]       = eventType
    content["exaInfraName"]    = exaInfraName
    content["exaInfraId"]      = exaInfraId
    content["maintenanceMode"] = maintenanceMode
    content["compartmentId"]   = cptId
    content["lifecycleState"]  = lifecycleState

    # for maintenancevm.* and maintenancecustomactiontime.* events, the db server is noted in the message
    # example of message:
    # This is an Oracle Cloud Operations notice regarding the quarterly maintenance update of the 
    # Database Server component of your ExaCC Infrastructure instance exacc-infra-ecch, ocid 
    # ocid1.exadatainfrastructure.oc1.eu-frankfurt-1.abtheljtrl4efvwy23mvuq7o5z6pvrj35r6rpe2ftsijy6bequst3biv5vuq,
    # Database Server dbServer-1, ocid ocid1.dbserver.oc1.eu-frankfurt-1.antheljtefas42yanq5vkaurupmbr2a2qjw6bbfjwmrkm3ulvswv6w4ypika
    # has started. A follow-up notice will be sent when the Database Server maintenance operation has completed."
    m = re.search('Database Server dbServer-(.+?), ocid ocid1.dbserver.', message)
    if m:
        dbserver_num = m.group(1)
        content["dbserver"] = dbserver_num
        object_name = f"{tempo_prefix}/{current_exainfra_group_name}/{exaInfraId}/{eventType}.{dbserver_num}"
    else:
        object_name = f"{tempo_prefix}/{current_exainfra_group_name}/{exaInfraId}/{eventType}"

    # if the eventType is maintenance.begin and this object already exists, 
    # it means the maintenance initially failed, and it is retrying, so ignore the second mainenance.begin event
    # and keep the time of the first maintenance.begin
    if eventType == "com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.begin":
        try:
            response = ObjectStorageClient.get_object(
                namespace_name  = namespace,
                bucket_name     = cfg_bucket_name,
                object_name     = object_name,
                retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY)
            # if object exist, then don't overwrite it.
            return { "store_event_in_bucket()": "maintenance.begin object already exists, skipping this new one !" }   
        except:
            pass

    # put object into the bucket
    response = ObjectStorageClient.put_object(
        namespace_name  = namespace,
        bucket_name     = cfg_bucket_name,
        object_name     = object_name,
        put_object_body = json.dumps(content, sort_keys=True, indent=4),
        content_type    = "application/octet-stream",
        retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

    return { "store_event_in_bucket()": response.status }   

# ---- get the list of compartments
def get_compartments():
    global compartments

    response = oci.pagination.list_call_get_all_results(
                      IdentityClient.list_compartments,
                      RootCompartmentID,
                      compartment_id_in_subtree=True)
    compartments = response.data

    return { "get_compartments()": response.status }

# ---- Is maintenance of ExaCC infrastructures group just starting ?
def is_maintenance_starting():
    response = ObjectStorageClient.list_objects(
                  namespace_name  = namespace,
                  bucket_name     = cfg_bucket_name,
                  prefix          = f"{tempo_prefix}/{current_exainfra_group_name}",
                  retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
    return (len(response.data.objects) == 0)

# ---- Is maintenance of ExaCC infrastructures group just completed ?
def is_maintenance_complete(exaInfras_events):
    isCompleted = True
    for exaInfraId in current_exainfra_group_ids:
        if exaInfras_events[exaInfraId]["maintenanceStatus"] != "SUCCEEDED":
            isCompleted = False
            break
    return isCompleted

# ---- Rename the HTML report to archive it (rename object *_IN_PROGRESS.html to *_<date>.html)
def archive_object(now_str):
    global report_object_name

    old_name           = report_object_name
    report_object_name = old_name.replace("IN_PROGRESS.html",f"{now_str}.html")
    try:
        details  = oci.object_storage.models.RenameObjectDetails(
                        source_name             = old_name,
                        new_name                = report_object_name)
        response = ObjectStorageClient.rename_object(
                        namespace_name        = namespace,
                        bucket_name           = cfg_bucket_name,
                        rename_object_details = details,
                        retry_strategy        = oci.retry.DEFAULT_RETRY_STRATEGY)    
        return { "archive_object()": response.status }   
    
    except Exception as err:
        return { "archive_object()" : "ERROR : " + str(err) }

# ---- Delete temporary files in the bucket
def delete_tempo_data():
    # In May 2022, Python SDK for OCI does not provide bulk-delete operation, 
    # so deleting temporary objects 1 by 1
    try:
        response = ObjectStorageClient.list_objects(
                      namespace_name  = namespace,
                      bucket_name     = cfg_bucket_name,
                      prefix          = f"{tempo_prefix}/{current_exainfra_group_name}",
                      retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

        for object in response.data.objects:
            response = ObjectStorageClient.delete_object(
                          namespace_name  = namespace,
                          bucket_name     = cfg_bucket_name,
                          object_name     = object.name,
                          retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY)        

        return { "delete_tempo_data()": response.status }   
    
    except Exception as err:
        return { "delete_tempo_data()" : "ERROR : " + str(err) }

# ---- Create or update object index.html in the bucket
# ---- This file will contain an HTML/clickable list of html files
def generate_index_object():
    html_content        = ""

    try:
        # get the tenancy name
        response = IdentityClient.get_tenancy(
            tenancy_id      = RootCompartmentID,
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        tenancy_name = response.data.name.upper()

        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>ExaCC daily reports</title>
  </head>
  <body>
    <h2>List of ExaCC maintenance reports for OCI tenant <span style="color:blue">{tenancy_name}</span>:</h2>
    <ul>
        """

        # get the list of objects in the bucket
        response = ObjectStorageClient.list_objects(
                      namespace_name  = namespace,
                      bucket_name     = cfg_bucket_name,
                      retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

        # create an HTML list using only objects ending with ".html"
        for object in response.data.objects:
            if object.name.endswith(".html") and object.name != "index.html":
                html_content       += f'    <li><a href="{cfg_par_for_bucket_read}{object.name}">{object.name}</a></li>\n'

        # 
        html_content += """
    </ul>
  </body>
</html>
        """

        # save this list into object index.html
        response = ObjectStorageClient.put_object(
            namespace_name  = namespace,
            bucket_name     = cfg_bucket_name,
            object_name     = "index.html",
            put_object_body = html_content,
            content_type    = "text/html",
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        return { "generate_index_object()": response.status }   
    
    except Exception as err:
        return { "generate_index_object()" : "ERROR : " + str(err) }

# ---- Process the event
# -	If event = "maintenance begin" AND tempo_data folder does not exist in bucket:
#   o	Create it
#   o	Store event type and date in data folder
#   o	Generate HTML report in bucket (content-type: text/html)
#   o	Create PAR for this object (read only)
#   o	Send email saying "maintenance of 1st Exadata Infra Started" and giving PAR to access HTML report
# -	ELSE
#   o	Store event type and date in data folder
#   o	Generate new HTML report in bucket (content-type: text/html) with same name (no need to update PAR)
#   o	If event = "maintenance end":
#       	Send email saying "maintenance of last Exadata infra completed"
#       	Delete folder tempo_data in bucket
def process_event(eventType, eventTime, exaInfraName, exaInfraId, cptId, message, maintenanceMode, lifecycleState): 
    global IdentityClient
    global ObjectStorageClient
    global DatabaseClient
    global namespace
    global RootCompartmentID

    signer              = oci.auth.signers.get_resource_principals_signer()
    RootCompartmentID   = signer.tenancy_id
    IdentityClient      = oci.identity.IdentityClient(config={}, signer=signer)
    DatabaseClient      = oci.database.DatabaseClient(config={}, signer=signer)
    exacc_region        = signer.region
    signer2             = signer
    signer2.region      = cfg_bucket_region
    ObjectStorageClient = oci.object_storage.ObjectStorageClient(config={}, signer=signer2)
    namespace           = ObjectStorageClient.get_namespace().data

    # get list of compartments
    resp = get_compartments()

    # Is this event the first event for the first exaInfra in the group
    maintenance_just_starting = is_maintenance_starting()

    # store this event in the bucket
    resp = resp | store_event_in_bucket(eventType, eventTime, exaInfraName, exaInfraId, cptId, message, maintenanceMode, lifecycleState)

    # Get dates/times of events for all ExaCC infrastructures
    exaInfras_events = get_exainfras()

    # generate the HTML report using this event plus previous events (stored in the bucket)
    resp = resp | generate_and_store_report(exacc_region, exaInfras_events)

    # if this is the first maintenance event, create a PAR and send an email
    if maintenance_just_starting:
        resp = resp | send_first_email()

    # if all exaInfras patches are completed, copy the object to a new name, delete temporary data, generate a new index.html file and send the second email
    elif is_maintenance_complete(exaInfras_events):
        resp = resp | archive_object(datetime.fromisoformat(eventTime[:-1]).strftime("%Y-%m-%d"))
        resp = resp | delete_tempo_data()
        resp = resp | generate_index_object()
        resp = resp | send_second_email()

    return resp

# ---- get variables from Function configuration
def get_variables_from_fn_config(cfg):
    # global variables that will be modified in this function
    global cfg_bucket_name
    global cfg_par_for_bucket_read 
    global cfg_email_sender             
    global cfg_email_sender_name     
    global cfg_email_recipients      
    global cfg_email_smtp_user     
    global cfg_email_smtp_pwd_secret_id      
    global cfg_email_smtp_host     
    global cfg_email_smtp_port 
    global cfg_exainfra_groups 
    global cfg_bucket_region
    global cfg_vault_secret_region

    cfg_bucket_name              = cfg["bucket_name"]
    cfg_bucket_region            = cfg["bucket_region"]
    cfg_par_for_bucket_read      = cfg["par_for_bucket_read"]
    cfg_email_sender             = cfg["email_sender"]        
    cfg_email_sender_name        = cfg["email_sender_name"]    
    cfg_email_recipients         = cfg["email_recipients"]
    cfg_email_smtp_user          = cfg["email_smtp_user"]
    cfg_email_smtp_host          = cfg["email_smtp_host"]
    cfg_email_smtp_port          = cfg["email_smtp_port"]
    cfg_email_smtp_pwd_secret_id = cfg["email_smtp_pwd_secret_id"]
    cfg_vault_secret_region      = cfg["vault_secret_region"]

    # look for groups 1 to 9
    for i in range(1,10):
        try:
            group_name = cfg[f"exainfra_group{i}_name"]
            group_ids  = cfg[f"exainfra_group{i}_ids"].split(",")
            cfg_exainfra_groups.append({ "name": group_name, "ids": group_ids })
        except:
            pass

# ---- get SMTP password from OCI Vault secret (possible in a different region)
def get_smtp_pwd_from_oci_vault_secret():
    # global variable that will be modified in this function
    global email_smtp_pwd 

    signer            = oci.auth.signers.get_resource_principals_signer()
    signer.region     = cfg_vault_secret_region
    SecretsClient     = oci.secrets.SecretsClient(config={}, signer=signer)

    response          = SecretsClient.get_secret_bundle(cfg_email_smtp_pwd_secret_id)
    secret_bundle     = response.data
    b64_secret_bytes  = secret_bundle.secret_bundle_content.content.encode('ascii')
    b64_message_bytes = base64.b64decode(b64_secret_bytes)
    email_smtp_pwd    = b64_message_bytes.decode('ascii')

# ---- get the name of the exainfra group containing a specific OCID
def get_current_exainfra_group(exaInfraId):
    global report_object_name

    l_current_exainfra_group_name = None
    l_current_exainfra_group_ids = []
    for exainfra_group in cfg_exainfra_groups:
        if exaInfraId in exainfra_group["ids"]:
            l_current_exainfra_group_name = exainfra_group["name"]
            l_current_exainfra_group_ids  = exainfra_group["ids"]
            break

    if l_current_exainfra_group_name != None:
        report_object_name = f"{report_object_name_prefix}_{l_current_exainfra_group_name}_IN_PROGRESS.html"

    return l_current_exainfra_group_name, l_current_exainfra_group_ids

# -------- MAIN HANDLER   
def handler(ctx, data: io.BytesIO=None):
    global current_exainfra_group_name
    global current_exainfra_group_ids

    try:
        # get variables from Function configuration
        get_variables_from_fn_config(ctx.Config())

        # get SMTP password from OCI Vault secret
        get_smtp_pwd_from_oci_vault_secret()

        # get details from JSON input (sent by OCI Event service)
        try:
            body = json.loads(data.getvalue())
            eventType       = body["eventType"]
            eventTime       = body["eventTime"]
            exaInfraName    = body["data"]["resourceName"]
            exaInfraId      = body["data"]["resourceId"]
            cptId           = body["data"]["compartmentId"]
            message         = body["data"]["additionalDetails"]["message"]
            maintenanceMode = body["data"]["additionalDetails"]["maintenanceMode"]
            lifecycleState  = body["data"]["additionalDetails"]["lifecycleState"]

            # ignore event if lifecycleState is FAILED
            if lifecycleState == "FAILED":
                resp = { "main()": f"IGNORED EVENT {eventType} with status FAILED !"}

            # ignore events not related to actual maintenance 
            elif not(eventType in [ "com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.begin",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.end",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.begin",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.end",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.begin",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.end",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.begin",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.end",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.begin",
                                    "com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.end"]):
                resp = { "main()": f"IGNORED EVENT {eventType} !"}

            else:
                # find the exainfra group contains this exaInfraId
                current_exainfra_group_name, current_exainfra_group_ids = get_current_exainfra_group (exaInfraId)
                if current_exainfra_group_name == None:
                    # ignore event if ExaInfraId not in the list
                    resp = { "main()": "IGNORED EVENT: Exadata Infrastructure OCID of the event does not belong to configured groups !"}
                else:
                    # process event
                    resp = { "main()": f"ExaCC group name = {current_exainfra_group_name}" }
                    resp = resp | process_event(eventType, eventTime, exaInfraName, exaInfraId, cptId, message, maintenanceMode, lifecycleState) 

        except Exception as err2:
            resp = { "main()" : "ERROR2: Error in the input JSON data : " + str(err2) }

    except Exception as err1:
        resp = { "main()" : "ERROR1: Missing configuration key : " + str(err1) }

    # return result in JSON output
    return fdk.response.Response(
        ctx,
        response_data = json.dumps(resp),
        headers = { "Content-Type": "application/json" }
    )