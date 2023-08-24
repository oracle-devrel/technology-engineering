# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
#
# This OCI function is called by a OCI Events when a new object is added to an OCI bucket.
#
# This function:
# 1) generates or updates file index.html in this bucket
# 2) This files contains the list of html files (other than index.html) in the buckets and HTML links to them
#
# Prerequisites:
# - Python 3.9 (for resp = resp | function() )
# - Object storage bucket 
# - Dynamic Group for the function with following matching rule
#   resource.id = '<ocid_function>'
# - Identity Policy to give required permissions to FaaS service and to the specific function (via dynamic group)
#   required statements:
#       "Allow dynamic-group <dg_name> to read buckets in compartment id <cpt_id> where target.bucket.name='<bucket_name>'",
#       "Allow dynamic-group <dg_name> to manage objects in compartment id <cpt_id> where target.bucket.name='<bucket_name>'",
#       "Allow service FaaS to use virtual-network-family in compartment id <cpt_id>",
#       "Allow service FaaS to read repos in tenancy" 
# - Configure following variables (keys/values) in the Function configuration:
#   par_for_bucket_read      : a pre-authenticated request allowing read on the bucket.
#
# Author        : Christophe Pauliat
#
# Versions
#    2022-06-09 : Initial Version
#    2022-07-20 : Only process objects with a specific prefix and create a table with 1 cell per month
#    2022-08-17 : Sort the file names by name for each month
#    2022-08-17 : Remove <ul> and <li> HTML tags (just use <br>)
#    2022-08-18 : Optimize indentation in HTML page
# ----------------------------------------------------------------------------------------------------

# -------- import
import io
import json
# import logging
import fdk.response
import oci
from datetime import datetime

# -------- global variables
signer              = ""
IdentityClient      = ""
ObjectStorageClient = ""
namespace           = ""
tenancy_name        = ""
object_names        = []
years_months        = []

# -------- Functions

# ---- Get the list of objects names to process
def oci_init():
    global signer
    global IdentityClient
    global ObjectStorageClient
    global namespace

    signer              = oci.auth.signers.get_resource_principals_signer()
    IdentityClient      = oci.identity.IdentityClient(config={}, signer=signer)
    ObjectStorageClient = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    namespace           = ObjectStorageClient.get_namespace().data

def get_objects_names(bucketName):
    global tenancy_name
    global object_names
    global years_months

    try:
        # get the tenancy name
        response = IdentityClient.get_tenancy(
            tenancy_id      = signer.tenancy_id,
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        tenancy_name = response.data.name.upper()

        # get the list of objects in the bucket filtering using the object name prefix
        response = ObjectStorageClient.list_objects(
                      namespace_name  = namespace,
                      bucket_name     = bucketName,
                      prefix          = cfg_object_name_prefix,
                      retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

        # save the object names in a list
        object_names = []
        for object in response.data.objects:
            if object.name.startswith(cfg_object_name_prefix) and object.name.endswith(".html"):
                if not(object.name in object_names):
                    object_names.append(object.name)

        # sort the list of object names
        object_names.sort()

        # extract the years/months (yyyy_mm format) after prefix
        l = len(cfg_object_name_prefix)
        years_months = []
        for object_name in object_names:
            year_month = object_name[l:l+7]
            if not(year_month in years_months):
                years_months.append(year_month)
        years_months.sort()

        return { "get_objects_names()": response.status }   

    except Exception as err:
        return { "get_objects_names()" : "ERROR: " + str(err) }

# ---- Create or update object index.html in the bucket
# ---- This file will contain an HTML/clickable list of html files
def month_name_year(year_month):
    year     = year_month[0:4]
    month_nb = year_month[5:7]
    datetime_object = datetime.strptime(month_nb, "%m")
    month_name = datetime_object.strftime("%B")
    return f"{month_name} {year}"

def generate_index_object_table(bucketName):
    html_content        = ""

    try:
        # HTML content
        html_content = """
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>ExaCC daily status reports</title>
      <style type="text/css">
        table {
            border-collapse: collapse;
            font-family:Arial;
        }
        tr {
            background-color: #FFF5F0;
        }
        td {
            border: 1px solid #808080;
            text-align: left;
            vertical-align: top;
            padding: 20px;
        }
    </style>
  </head>
  <body>"""
        html_content += f"""
    <h2>List of ExaCC status reports for OCI tenant <span style="color:blue">{tenancy_name}</span>:</h2>
    <table>"""
        cpt = 0
        for year_month in years_months:
            # max 4 columns per row
            if cpt % 4 == 0:            
                html_content += f"""
      <tr>"""

            html_content += f"""
        <td>
          <span style="text-align: center"><h3>{month_name_year(year_month)}</h3></span>"""
            
            for object_name in object_names:
                if object_name.startswith(cfg_object_name_prefix + year_month):
                    html_content += f'''
          <a href="{cfg_par_for_bucket_read}{object_name}">{object_name}</a><br>'''

            html_content += """
        </td>"""

            #
            cpt += 1

            # max 4 columns per row
            if cpt % 4 == 0:            
                html_content += f"""
      </tr>"""


        # add final </tr> if not yet present
        if cpt % 4 != 0:            
            html_content += """
      </tr>"""

        # end of HTML page
        html_content += """
    </table>
  </body>
</html>
        """

        # save this list into object index.html
        response = ObjectStorageClient.put_object(
            namespace_name  = namespace,
            bucket_name     = bucketName,
            object_name     = "index.html",
            put_object_body = html_content,
            content_type    = "text/html",
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        return { "generate_index_object_table()": response.status }   
    
    except Exception as err:
        return { "generate_index_object_table()" : "ERROR: " + str(err) }

def generate_index_object_list(bucketName):
    html_content        = ""

    try:
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>ExaCC daily reports</title>
  </head>
  <body>
    <h2>List of ExaCC reports for OCI tenant <span style="color:blue">{tenancy_name}</span>:</h2>
    <ul>
        """

        # create an HTML list using only objects ending with ".html"
        for object_name in object_names:
                html_content += f'    <li><a href="{cfg_par_for_bucket_read}{object_name}">{object_name}</a></li>\n'

        # 
        html_content += """
    </ul>
  </body>
</html>
        """

        # save this list into object index.html
        response = ObjectStorageClient.put_object(
            namespace_name  = namespace,
            bucket_name     = bucketName,
            object_name     = "index.html",
            put_object_body = html_content,
            content_type    = "text/html",
            retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 
        return { "generate_index_object_list()": response.status }   
    
    except Exception as err:
        return { "generate_index_object_list()" : "ERROR: " + str(err) }

# ---- get variables from Function configuration
def get_variables_from_fn_config(cfg):
    # global variables that will be modified in this function
    global cfg_par_for_bucket_read 
    global cfg_object_name_prefix 

    cfg_par_for_bucket_read = cfg["par_for_bucket_read"]
    cfg_object_name_prefix  = cfg["object_name_prefix"]

# Example of PAR for bucekt read:
# https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/oYzo9YuSFZxKlb5i1Qj9t_4A6JXbK-5TYHqlvtHlLUPZC_aStVZ7gabGQXwSA9W9/n/oscemea001/b/ExaCC_daily_reports/o/

# -------- MAIN HANDLER   
def handler(ctx, data: io.BytesIO=None):

    try:
        # get variables from Function configuration
        get_variables_from_fn_config(ctx.Config())

        # get bucket and objects Name from JSON input (sent by OCI Event service)
        try:
            body = json.loads(data.getvalue())
            objectName = body["data"]["resourceName"]
            bucketName = body["data"]["additionalDetails"]["bucketName"]

            # if the new object ends with .html then create/update object index.html in the bucket
            if objectName.startswith(cfg_object_name_prefix) and objectName.endswith(".html"):
                oci_init()
                resp = get_objects_names(bucketName)
                resp = resp | generate_index_object_table(bucketName)
                # resp = resp | generate_index_object_list(bucketName)
            else:
                resp = { "main()": f"Ignoring object as name not starting with '{cfg_object_name_prefix}' or not ending with '.html' !"}

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