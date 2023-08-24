#!/usr/bin/env python3

# --------------------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
#
# This script generates HTML reports for Exadata Cloud at Customer (ExaCC) machines 
# in an Oracle Cloud Infrastructure (OCI) tenant using OCI Python SDK 
#
# It looks in all compartments in the given OCI region or in all subscribed OCI regions
#
# Note: OCI tenant given by an OCI CLI PROFILE or by instance principal authentication
#
# Authors       : Christophe Pauliat / Matthieu Bordonné
# Platforms     : MacOS / Linux
# prerequisites : - Python 3 with OCI Python SDK installed
#                 - OCI config file configured with at least 1 profile (not needed if using instance principal authentication)
# Versions
#    2020-09-21: Initial Version for VM clusters only
#    2021-01-18: HTML output showing a table with VM clusters details and status
#    2021-05-11: Add a retry strategy for some OCI calls in to avoid potential error "Too many requests for the tenants"
#    2021-08-18: Add a new table showing status for ExaCC Exadata Infrastructures
#    2021-08-18: Show VM clusters contained in each Exadata infrastructure in the Exadata infrastructure table
#    2021-08-18: Show the Exadata infrastructure for each VM cluster in the VM clusters table
#    2021-08-18: Add a 3rd table for autonomous VM clusters
#    2021-08-24: Optimize code for empty tables
#    2021-08-24: Add more details for Exadata infrastructures (Matthieu)
#    2021-09-01: Show Memory for VM clusters (Matthieu)
#    2021-11-30: Show number of DB nodes on regular VM clusters (not on Autonomous VM clusters)
#    2021-11-30: Replace "xx".format() strings by f-strings
#    2021-12-01: Add a retry strategy for ALL OCI calls in to avoid potential error "Too many requests for the tenants"
#    2022-01-03: use argparse to parse arguments
#    2022-04-27: Add the 'Quarterly maintenances" column
#    2022-05-03: Fix minor bug in HTML code (</tr> instead of <tr> for table end line)
#    2022-06-03: Add the --email option to send the HTML report by email
#    2022-06-08: Add the --inst-principal option to use instance principal authentication instead of user authentication
#    2022-06-08: Add the --bucket-name option to store the reports in an OCI object storage bucket
#    2022-06-15: Replace console.{home_region}.oraclecloud.com by cloud.oracle.com in get_url_link*() functions
#    2022-06-15: Print error messages to stderr instead of stdout
#    2022-07-11: Add GI/OS versions for VM Clusters (Matthieu)
#    2022-07-12: Add Maintenance info for Autonomous VM Clusters (Matthieu)
#    2022-07-19: Add the --databases option to list DATABASE HOMES, CDB and PDB databases
#    2022-07-19: Sort the tables 
#    2022-07-19: Add the --bucket-suffix option to add a suffix to object name in OCI object storage bucket
#    2022-07-19: Replace tables captions by title at the beginning of the page
#    2022-07-19: Use automatic font sizes (font sizes automatically changed depending on Web/Email window size)
#    2022-07-22: Add colors for PDBs open modes in DB Homes table (--databases option)
#    2022-07-27: Add the --report-options option to dynamically modify a report viewed in Web browser using Javascript
#    2022-08-10: Add the --license option to get license model for VM clusters and Autonomous VM clusters
#    2022-08-10: Block the header at the top of HTML page
#    2022-08-10: Add local storage and Exadata storage for VM clusters and Autonomous VM clusters
#    2022-08-10: Add memory and available OCPUs for Autonomous VM clusters
#    2022-08-10: For Exadata Infrastructures, display available OCPUs instead of used OCPUs
#    2022-08-11: Display the db servers used by each VM cluster
#    2022-08-11: Display version (DB Server and Storage Server) for each Exadata Infrastructure
#    2022-08-12: Add installed and available resources (memory, local storage and Exadata storage) for Exadata Infrastructures
#    2022-08-12: Add Autonomous DB storage (available and Total) for Autonomous VM clusters
#    2022-08-18: Highlight version information if a newer version is available for VM clusters and DB homes
#    2022-08-18: For Exadata Infrastructures, display patching mode and replace shape by human readable model name
#    2022-08-18: For Autonomous Container Databases, display compartment name
#    2022-08-29: For Exadata Infrastructures, display rack serial number if available
#    2022-08-30: Fix minor bug in patching mode display
# --------------------------------------------------------------------------------------------------------------

# -------- import
import oci
import sys
import argparse
import os
import smtplib
import email.utils
import operator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from pkg_resources import parse_version

# -------- variables
days_notification       = 15                 # Number of days before scheduled maintenance
color_date_soon         = "#FF0000"          # Color for maintenance scheduled soon (less than days_notification days)
color_not_available     = "#FF0000"          # Color for lifecycles different than AVAILABLE and ACTIVE
color_resources_warning = "#FF0000"          # Color to highlight low availability of resources
color_new_version_avail = "#FF0000"          # Color to highlight the fact there is a newer version
color_pdb_read_write    = "#009900"
color_pdb_read_only     = "#FF9900"
color_pdb_others        = "#FF0000"
configfile              = "~/.oci/config"    # Define config file to be used.
exadatainfrastructures  = []
vmclusters              = []
autonomousvmclusters    = []
db_homes                = []
auto_cdbs               = []
auto_dbs                = []
threshold_ocpus         = 0.80               # if more than 80% of OCPUs are used, used a specific/warning color for available OCPUs
threshold_memory        = 0.80               # if more than 80% of Memory is used, used a specific/warning color for available Memory
threshold_storage       = 0.80               # if more than 80% of storage is used, used a specific/warning color for available storage
shapes_models           = [                  # Conversion from shape to human readable model name
                            { "shape": "ExadataCC.QuarterX9M.124", "model": "Quarter Rack X9M" },
                            { "shape": "ExadataCC.HalfX9M.248",    "model": "Half Rack X9M" },
                            { "shape": "ExadataCC.FullX9M.496",    "model": "Full Rack X9M" },
                            { "shape": "ExadataCC.QuarterX8M.100", "model": "Quarter Rack X8M" },
                            { "shape": "ExadataCC.HalfX8M.200",    "model": "Half Rack X8M" },
                            { "shape": "ExadataCC.FullX9M.400",    "model": "Full Rack X8M" },
                            { "shape": "ExadataCC.Quarter3.100",   "model": "Quarter Rack X8" },
                            { "shape": "ExadataCC.Half3.200",      "model": "Half Rack X8" },
                            { "shape": "ExadataCC.Full3.400",      "model": "Full Rack X8" },
                            { "shape": "ExadataCC.Quarter2.92",    "model": "Quarter Rack X7" },
                            { "shape": "ExadataCC.Half2.184",      "model": "Half Rack X7" },
                            { "shape": "ExadataCC.Full2.368",      "model": "Full Rack X7" },
                            { "shape": "ExadataCC.Quarter1.84",    "model": "Quarter Rack X6" },
                            { "shape": "ExadataCC.Half1.168",      "model": "Half Rack X6" },
                            { "shape": "ExadataCC.Full1.336",      "model": "Full Rack X6" },
    ] 

# -------- functions

# ---- Get the complete name of a compartment from its id, including parent and grand-parent..
def get_cpt_name_from_id_single_line(cpt_id):

    if cpt_id == RootCompartmentID:
        return "root"

    name=""
    for c in compartments:
        if (c.id == cpt_id):
            name=c.name
    
            # if the cpt is a direct child of root compartment, return name
            if c.compartment_id == RootCompartmentID:
                return name
            # otherwise, find name of parent and add it as a prefix to name
            else:
                name = get_cpt_name_from_id_single_line(c.compartment_id)+":"+name
                return name

def get_cpt_name_from_id(cpt_id):
    cpt_name = get_cpt_name_from_id_single_line(cpt_id)
    cpt_name_ml = cpt_name.replace(":","<br>&nbsp;:")
    return cpt_name_ml

# ---- Get url link to a specific Exadata infrastructure in OCI Console
def get_url_link_for_exadatainfrastructure(exadatainfrastructure):
    return f"https://cloud.oracle.com/exacc/infrastructures/{exadatainfrastructure.id}?tenant={tenant_name}&region={exadatainfrastructure.region}"

# ---- Get url link to a specific VM cluster in OCI Console
def get_url_link_for_vmcluster(vmcluster):
    return f"https://cloud.oracle.com/exacc/clusters/{vmcluster.id}?tenant={tenant_name}&region={vmcluster.region}"

# ---- Get url link to a specific autonomous VM cluster in OCI Console
def get_url_link_for_autonomousvmcluster(vmcluster):
    return f"https://cloud.oracle.com/exacc/autonomousExaVmClusters/{vmcluster.id}?tenant={tenant_name}&region={vmcluster.region}"

# ---- Get url link to a specific DB home in OCI Console
def get_url_link_for_db_home(db_home):
    return f"https://cloud.oracle.com/exacc/db_homes/{db_home.id}?tenant={tenant_name}&region={db_home.region}"

# ---- Get url link to a specific database in OCI Console
def get_url_link_for_database(database, region):
    return f"https://cloud.oracle.com/exacc/databases/{database.id}?tenant={tenant_name}&region={region}"

# ---- Get url link to a specific pdb in OCI Console
def get_url_link_for_pdb(pdb, region):
    return f"https://cloud.oracle.com/exacc/pluggableDatabases/{pdb.id}?tenant={tenant_name}&region={region}"

# ---- Get url link to a specific autonomous container database in OCI Console
def get_url_link_for_auto_cdb(auto_cdb):
    return f"https://cloud.oracle.com/exacc/autonomousContainerDatabases/{auto_cdb.id}?tenant={tenant_name}&region={auto_cdb.region}"

# ---- Get url link to a specific autonomous  database in OCI Console
def get_url_link_for_auto_db(auto_db):
    return f"https://cloud.oracle.com/exacc/autonomousDatabases/{auto_db.id}?tenant={tenant_name}&region={auto_db.region}"

# ---- Get an Exadata Infrastructure from its OCID
def get_exadatainfrastructure_from_id(exainfra_id):
    for exainfra in exadatainfrastructures:
        if exainfra.id == exainfra_id:
            return exainfra
    return None

# ---- Get the details for a next maintenance run
def get_next_maintenance_date(DatabaseClient, maintenance_run_id):
    if maintenance_run_id:
        response = DatabaseClient.get_maintenance_run (maintenance_run_id = maintenance_run_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
        return response.data.time_scheduled
    else:
        return ""

# ---- Get the details for a last maintenance run
def get_last_maintenance_dates(DatabaseClient, maintenance_run_id):
    if maintenance_run_id:
        response = DatabaseClient.get_maintenance_run (maintenance_run_id = maintenance_run_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
        return response.data.time_started, response.data.time_ended
    else:
        date_started = ""
        date_ended   = ""
        return date_started, date_ended

# ---- Get details for an Exadata infrastructure
def exadatainfrastructure_get_details (exadatainfrastructure_id):
    global exadatainfrastructures

    # get details about exadatainfrastructure
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_exadata_infrastructure (exadata_infrastructure_id = exadatainfrastructure_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    exainfra = response.data

    # add more details
    if authentication_mode == "user_profile":
        exainfra.region = config["region"]
    else:
        exainfra.region = signer.region
    exainfra.last_maintenance_start, exainfra.last_maintenance_end = get_last_maintenance_dates(DatabaseClient, exainfra.last_maintenance_run_id)
    exainfra.next_maintenance = get_next_maintenance_date(DatabaseClient, exainfra.next_maintenance_run_id)

    # get the list of DB servers for this Exadata Infrastructure
    response = DatabaseClient.list_db_servers (
        compartment_id = exainfra.compartment_id,
        exadata_infrastructure_id = exadatainfrastructure_id, 
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    dbservers = sorted(response.data, key=operator.attrgetter('display_name'))
    exainfra.db_servers = []
    for dbserver in dbservers:
        exainfra.db_servers.append({ "id": dbserver.id, "display_name": dbserver.display_name})

    # save details to list
    exadatainfrastructures.append (exainfra)

# ---- Get details for a VM cluster
def vmcluster_get_details (vmcluster_id):
    global vmclusters

    # get details about vmcluster from regular API 
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_vm_cluster (vm_cluster_id = vmcluster_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    vmclust = response.data
    if authentication_mode == "user_profile":
        vmclust.region = config["region"]
    else:
        vmclust.region = signer.region

    # Get the available GI updates for the VM Cluster
    response = DatabaseClient.list_vm_cluster_updates (vm_cluster_id = vmcluster_id, update_type = "GI_PATCH", retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    vmclust_gi_updates = response.data
    vmclust.gi_update_available = vmclust.gi_version
    for gi_updates in vmclust_gi_updates:
        if parse_version(gi_updates.version) > parse_version(vmclust.gi_update_available):
            vmclust.gi_update_available = gi_updates.version

    # Get the available System updates for the VM Cluster
    response = DatabaseClient.list_vm_cluster_updates (vm_cluster_id = vmcluster_id, update_type = "OS_UPDATE", retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    vmclust_sys_updates = response.data
    vmclust.system_update_available = vmclust.system_version
    for sys_updates in vmclust_sys_updates:
        if parse_version(sys_updates.version) > parse_version(vmclust.system_update_available):
            vmclust.system_update_available = sys_updates.version

    # save details to list
    vmclusters.append (vmclust)

# ---- Get details for an autonomous VM cluster
def autonomousvmcluster_get_details (autonomousvmcluster_id):
    global autonomousvmclusters

    # get details about autonomous vmcluster from regular API 
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_autonomous_vm_cluster (autonomous_vm_cluster_id = autonomousvmcluster_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    autovmclust = response.data
    if authentication_mode == "user_profile":
        autovmclust.region = config["region"]
    else:
        autovmclust.region = signer.region

    # last_maintenance_run_id is currently not populated, hence the workaround below 
    # Get a list of historical maintenance runs for that AVM Cluster and find the latest
    response = DatabaseClient.list_maintenance_runs(compartment_id = autovmclust.compartment_id,
        target_resource_id = autovmclust.id, 
        sort_by = "TIME_ENDED", 
        sort_order = "ASC",
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    if len(response.data) > 0:
        last_maintenance_run_id = response.data[-1].id
    else:
        last_maintenance_run_id = autovmclust.last_maintenance_run_id

    autovmclust.last_maintenance_start, autovmclust.last_maintenance_end = get_last_maintenance_dates(DatabaseClient, last_maintenance_run_id)
    # End of workaround. Once fixed, replace by this call:
    # autovmclust.last_maintenance_start, autovmclust.last_maintenance_end = get_last_maintenance_dates(DatabaseClient, autovmclust.last_maintenance_run_id)
    autovmclust.next_maintenance = get_next_maintenance_date(DatabaseClient, autovmclust.next_maintenance_run_id)

    # save details to list
    autonomousvmclusters.append (autovmclust)

# ---- Get details for a DB home
def db_home_get_details (db_home_id):
    global db_homes

    # get details about db_home from regular API 
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_db_home (db_home_id = db_home_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    db_home = response.data
    if authentication_mode == "user_profile":
        db_home.region = config["region"]
    else:
        db_home.region = signer.region

    # Get the latest patch available (DB version) for the DB HOME
    response = DatabaseClient.list_db_home_patches (db_home_id = db_home_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    db_home_updates = response.data
    db_home.db_update_latest = db_home.db_version
    for update in db_home_updates:
        if parse_version(update.version) > parse_version(db_home.db_update_latest):
            db_home.db_update_latest = update.version

    # get the list of databases (and pluggable databases) using this DB home
    response = DatabaseClient.list_databases (compartment_id = db_home.compartment_id, db_home_id = db_home_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    db_home.databases = response.data
    for database in db_home.databases:
        # OCI pluggable database management is supported only for Oracle Database 19.0 or higher
        try:
            if database.is_cdb:
                response = DatabaseClient.list_pluggable_databases (database_id = database.id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                database.pdbs = response.data
        except:
            pass

    # save details to list
    db_homes.append (db_home)

# ---- Get details for an autonomous container database
def auto_cdb_get_details (auto_cdb_id):
    global auto_cdbs

    # get details about autonomous cdb from regular API 
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_autonomous_container_database (autonomous_container_database_id = auto_cdb_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    auto_cdb = response.data
    if authentication_mode == "user_profile":
        auto_cdb.region = config["region"]
    else:
        auto_cdb.region = signer.region

    # save details to list
    auto_cdbs.append (auto_cdb)

# ---- Get details for an autonomous database
def auto_db_get_details (auto_db_id):
    global auto_dbs

    # get details about autonomous database from regular API 
    if authentication_mode == "user_profile":
        DatabaseClient = oci.database.DatabaseClient(config)
    else:
        DatabaseClient = oci.database.DatabaseClient(config={}, signer=signer)
    response = DatabaseClient.get_autonomous_database (autonomous_database_id = auto_db_id, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    auto_db = response.data
    if authentication_mode == "user_profile":
        auto_db.region = config["region"]
    else:
        auto_db.region = signer.region

    # save details to list
    auto_dbs.append (auto_db)

# ---- Get the list of Exadata infrastructures
def search_exadatainfrastructures():
    query = "query exadatainfrastructure resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query), 
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        exadatainfrastructure_get_details (item.identifier)

# ---- Get the list of VM clusters
def search_vmclusters():
    query = "query vmcluster resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query),
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        vmcluster_get_details (item.identifier)

# ---- Get the list of autonomous VM clusters
def search_autonomousvmclusters():
    query = "query autonomousvmcluster resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query),
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        if item.lifecycle_state != "TERMINATED":
            autonomousvmcluster_get_details (item.identifier)

# ---- Get the list of DB homes (for VM clusters)
def search_db_homes():
    query = "query dbhome resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query),
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        db_home_get_details (item.identifier)

# ---- Get the list of Autonomous Container Databases (for autonomous VM clusters)
def search_auto_cdbs():
    query = "query autonomouscontainerdatabase resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query),
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        auto_cdb_get_details (item.identifier)

# ---- Get the list of Autonomous Databases (for autonomous VM clusters)
def search_auto_dbs():
    query = "query autonomousdatabase resources"
    if authentication_mode == "user_profile":
        SearchClient = oci.resource_search.ResourceSearchClient(config)
    else:
        SearchClient = oci.resource_search.ResourceSearchClient(config={}, signer=signer)
    response = SearchClient.search_resources(
        oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query),
        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
    sorted_items = sorted(response.data.items, key=operator.attrgetter('display_name'))
    for item in sorted_items:
        auto_db_get_details (item.identifier)

# ---- Generate HTML page 
def generate_html_headers():
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>ExaCC status report</title>
    <style type="text/css">
        tr:nth-child(odd) {{ background-color: #f2f2f2; }}
        tr:hover          {{ background-color: #ffdddd; }}
        body {{
            font-family: Arial;
            z-index: 0;
            background-color: white;
        }}
        table {{
            border-collapse: collapse;
        }}
        .tiny_tables {{
            border-collapse: separate;  
            margin: auto; 
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr {{
            background-color: #FFF5F0;
        }}
        th, td {{
            border: 1px solid #808080;
            text-align: center;
            padding: 7px;
        }}
        .td_dbserver {{
            font-family: Courier;
            border: 0px;
            background-color: #4467be;
            text-align: center;
            padding: 6px;
            padding-left: 9px;
            padding-right: 9px;
            border-radius: 50%;
        }}
        .td_dbserver_unused {{
            opacity: 0.3;
        }}
        .td_dbserver_used {{
            color: white;
            opacity: 1;
        }}
        .auto_td_th {{
            font-size: 0.85vw;
        }}
        .auto_h1 {{
            font-size: 2vw;
        }}
        .auto_h2 {{
            font-size: 1.5vw;
        }}
        .auto_h3 {{
            font-size: 1.1vw;
        }}
        .auto_text_outside_tables {{
            font-size: 0.95vw;
        }}
        caption {{
            caption-side: bottom;
            padding: 10px;
            font-style: italic;
        }}
        #my_header {{
            position: sticky;
            top: 0;
            width: 100%;
            z-index: 1;
            background-color: white;
        }}
        a.pdb_link_read_write:link {{
            color: {color_pdb_read_write};
        }}
        a.pdb_link_read_write:visited {{
            color: {color_pdb_read_write};
        }}
        a.pdb_link_read_only:link {{
            color: {color_pdb_read_only};
        }}
        a.pdb_link_read_write:visited {{
            color: {color_pdb_read_only};
        }}
        a.pdb_link_others:link {{
            color: {color_pdb_others};
        }}
        a.pdb_link_others:visited {{
            color: {color_pdb_others};
        }}'''

    html_content += '''
    </style>'''

    return html_content

def exainfra_ocpus_threshold_reached(exadatainfrastructure):
    used     = exadatainfrastructure.cpus_enabled
    total    = exadatainfrastructure.max_cpu_count
    pct_used = used / total
    return pct_used > threshold_ocpus

def exainfra_memory_threshold_reached(exadatainfrastructure):
    used     = exadatainfrastructure.memory_size_in_gbs
    total    = exadatainfrastructure.max_memory_in_gbs
    pct_used = used / total
    return pct_used > threshold_memory

def exainfra_local_storage_threshold_reached(exadatainfrastructure):
    used     = exadatainfrastructure.db_node_storage_size_in_gbs
    total    = exadatainfrastructure.max_db_node_storage_in_g_bs
    pct_used = used / total
    return pct_used > threshold_storage

def exainfra_exadata_storage_threshold_reached(exadatainfrastructure):
    used     = exadatainfrastructure.data_storage_size_in_tbs
    total    = exadatainfrastructure.max_data_storage_in_t_bs
    pct_used = used / total
    return pct_used > threshold_storage

def get_exacc_model_from_shape(shape):
    model = shape.replace("ExadataCC.","")
    for sm in shapes_models:
        if sm['shape'] == shape:
            model = sm['model'] 
    return model

def generate_html_table_exadatainfrastructures():
    html_content  = '''
    <div id="div_exainfras">
        <h2>ExaCC Exadata infrastructures</h2>'''

    # if there is no exainfra, just display None
    if len(exadatainfrastructures) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 exainfra, so display a table
    html_content += '''
        <table id="table_exainfras">
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>EXADATA<br>INFRASTRUCTURE</th>
                    <th>Compartment</th>
                    <th class="exacc_maintenance">Quarterly<br>maintenances</th>
                    <th>Model</th>
                    <th>Servers<br><br>Compute<hr>Storage</th>
                    <th>Status</th>
                    <th>OCPUs<br><br>Available<hr>Total</th>
                    <th>Memory<br><br>Available<hr>Total</th>
                    <th>Local storage<br><br>Available<hr>Total</th>
                    <th>Exadata storage<br><br>Available<hr>Total</th>
                    <th>VM cluster(s)</th>
                    <th>Autonomous<br>VM cluster(s)</th>
                    <th>Version<br><br>DB Server<hr>Storage Server</th>
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        format     = "%b %d %Y %H:%M %Z"
        cpt_name   = get_cpt_name_from_id(exadatainfrastructure.compartment_id)
        url        = get_url_link_for_exadatainfrastructure(exadatainfrastructure)
        html_style1 = f' style="color: {color_not_available}"' if (exadatainfrastructure.lifecycle_state != "ACTIVE") else ''
        html_style2 = f' style="color: {color_resources_warning}"' if exainfra_ocpus_threshold_reached(exadatainfrastructure) else ''
        html_style3 = f' style="color: {color_resources_warning}"' if exainfra_memory_threshold_reached(exadatainfrastructure) else ''
        html_style4 = f' style="color: {color_resources_warning}"' if exainfra_local_storage_threshold_reached(exadatainfrastructure) else ''
        html_style5 = f' style="color: {color_resources_warning}"' if exainfra_exadata_storage_threshold_reached(exadatainfrastructure) else ''

        try:
            serial_number = exadatainfrastructure.rack_serial_number
        except:
            serial_number = "not available"

        html_content += f'''
                <tr>
                    <td>{exadatainfrastructure.region}</td>
                    <td><b><a href="{url}">{exadatainfrastructure.display_name}</a></b><br><br>S/N: {serial_number}</td>
                    <td style="text-align: left">{cpt_name}</td>
                    <td class="exacc_maintenance" style="text-align: left">Last maintenance: <br>'''

        try:
            html_content += f'''
                         - {exadatainfrastructure.last_maintenance_start.strftime(format)} (start)<br>'''
        except:
            html_content += f'''
                         - no date/time (start)<br>'''

        try:
            html_content += f'''
                         - {exadatainfrastructure.last_maintenance_end.strftime(format)} (end)<br><br>'''
        except:
            html_content += f'''
                         - no date/time (end)<br><br>'''
        
        html_content += f'''
                        Next maintenance: <br>'''

        if exadatainfrastructure.next_maintenance == "":
            html_content += f'''
                         - Not yet scheduled<br><br>'''
        else: 
            html_style6 = f' style="color: {color_date_soon}"' if (exadatainfrastructure.next_maintenance - now < timedelta(days=days_notification)) else ''       
            html_content += f'''
                         - <span{html_style6}>{exadatainfrastructure.next_maintenance.strftime(format)}</span><br><br>'''

        html_content += f'''
                        Patching mode: {exadatainfrastructure.maintenance_window.patching_mode}</td>'''

        ocpus_available           = exadatainfrastructure.max_cpu_count               - exadatainfrastructure.cpus_enabled
        memory_available          = exadatainfrastructure.max_memory_in_gbs           - exadatainfrastructure.memory_size_in_gbs
        local_storage_available   = exadatainfrastructure.max_db_node_storage_in_g_bs - exadatainfrastructure.db_node_storage_size_in_gbs
        exadata_storage_available = exadatainfrastructure.max_data_storage_in_t_bs    - exadatainfrastructure.data_storage_size_in_tbs

        html_content += f'''
                    <td>{get_exacc_model_from_shape(exadatainfrastructure.shape)}</td>
                    <td>{exadatainfrastructure.compute_count}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <hr> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{exadatainfrastructure.storage_count}</td>
                    <td><span{html_style1}>{exadatainfrastructure.lifecycle_state}</span></td>
                    <td><span{html_style2}>{ocpus_available}</span> <hr> {exadatainfrastructure.max_cpu_count}</td>
                    <td><span{html_style3}>{memory_available} GB</span> <hr> {exadatainfrastructure.max_memory_in_gbs} GB</td>
                    <td><span{html_style4}>{local_storage_available} GB</span> <hr> {exadatainfrastructure.max_db_node_storage_in_g_bs} GB</td>
                    <td><span{html_style5}>{exadata_storage_available:0.1f} TB</span> <hr> {exadatainfrastructure.max_data_storage_in_t_bs:0.1f} TB</td>'''

        vmc = []
        for vmcluster in vmclusters:
            if vmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                url = get_url_link_for_vmcluster(vmcluster)
                vmc.append(f'<a href="{url}">{vmcluster.display_name}</a>')
        separator = '<br>'
        html_content += f'''
                    <td>{separator.join(vmc)}</td>'''

        avmc = []
        for autonomousvmcluster in autonomousvmclusters:
            if autonomousvmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                url = get_url_link_for_autonomousvmcluster(autonomousvmcluster)
                avmc.append(f'<a href="{url}">{autonomousvmcluster.display_name}</a>')
        separator = '<br>'
        html_content += f'''
                    <td>{separator.join(avmc)}</td>
                    <td>{exadatainfrastructure.db_server_version}<hr>{exadatainfrastructure.storage_server_version}</td>
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def display_db_servers(vmcluster,exadatainfrastructure):
    str = '<table class="tiny_tables"><tr>'
    for db_server in exadatainfrastructure.db_servers:
        # print (f"DEBUG: display_db_servers() db_server = {db_server}",file=sys.stderr)
        num = db_server['display_name'][-1]    # number = last character 
        if db_server['id'] in vmcluster.db_servers:
            str += f'<td class="td_dbserver td_dbserver_used">{num}</td>'
        else:
            str += f'<td class="td_dbserver td_dbserver_unused">{num}</td>'

    str += '</tr></table>'

    return str

def generate_html_table_vmclusters():
    html_content  = '''
    <div id="div_vmclusters">
        <br>
        <h2>ExaCC VM Clusters</h2>'''

    # if there is no vm cluster, just display None
    if len(vmclusters) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 vm cluster, so display a table
    html_content += '''
        <table id="table_vmclusters">
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>Exadata<br>infrastructure</th>
                    <th>VM CLUSTER</th>
                    <th>Compartment</th>
                    <th>Status</th>
                    <th>DB<br>servers</th>
                    <th>OCPUs</th>
                    <th>Memory</th>
                    <th>Local<br>Storage</th>
                    <th>Exadata<br>Storage</th>
                    <th>GI Version<br><br>Current<hr>Latest</th>
                    <th>OS Version<br><br>Current<hr>Latest</th>'''
    if display_license:
        html_content += '''
                    <th class="license">License model</th>'''        
    if display_dbs:
        html_content += '''
                    <th class="exacc_databases">DB Home(s) : <i>Databases...</i></th>'''

    html_content += '''
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        for vmcluster in vmclusters:
            if vmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                url1        = get_url_link_for_exadatainfrastructure(exadatainfrastructure)      
                url2        = get_url_link_for_vmcluster(vmcluster)
                cpt_name    = get_cpt_name_from_id(vmcluster.compartment_id)
                html_style1 = f' style="color: {color_not_available}"' if (vmcluster.lifecycle_state != "AVAILABLE") else ''
                html_style2 = f' style="color: {color_new_version_avail}"' if (vmcluster.gi_version != vmcluster.gi_update_available) else ''
                html_style3 = f' style="color: {color_new_version_avail}"' if (vmcluster.system_version != vmcluster.system_update_available) else ''

                html_content += f'''
                <tr>
                    <td>{vmcluster.region}</td>
                    <td><a href="{url1}">{exadatainfrastructure.display_name}</a></td>
                    <td><b><a href="{url2}">{vmcluster.display_name}</a></b> </td>
                    <td style="text-align: left">{cpt_name}</td>
                    <td><span{html_style1}>{vmcluster.lifecycle_state}</span></td>
                    <td>{display_db_servers(vmcluster,exadatainfrastructure)}</td>
                    <td>{vmcluster.cpus_enabled}</td>
                    <td>{vmcluster.memory_size_in_gbs} GB</td>
                    <td>{vmcluster.db_node_storage_size_in_gbs} GB</td>
                    <td>{vmcluster.data_storage_size_in_tbs} TB</td>
                    <td><span{html_style2}>{vmcluster.gi_version}</span><hr>{vmcluster.gi_update_available}</td>
                    <td><span{html_style3}>{vmcluster.system_version}</span><hr>{vmcluster.system_update_available}</td>'''

                if display_license:
                    html_content += f'''
                    <td class="license">{vmcluster.license_model}</td>'''  

                if display_dbs:
                    html_content += '''
                    <td class="exacc_databases" style="text-align: left">'''
                    for db_home in db_homes:
                        if db_home.vm_cluster_id == vmcluster.id:
                            url = get_url_link_for_db_home(db_home)
                            html_content += f'''
                        <a href="{url}">{db_home.display_name}</a> : '''
                            for database in db_home.databases:
                                html_content += f'''
                            <i>{database.db_name}</i>'''
                            html_content += f'''
                            <br>'''
                    html_content += '''
                    </td>'''

                html_content += '''
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def generate_html_table_db_homes():
    format   = "%b %d %Y %H:%M %Z"
    html_content  = '''
    <div id="div_dbhomes">
        <br>
        <h2>ExaCC Database Homes</h2>'''

    # if there is no db home, just display None
    if len(db_homes) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 vm cluster, so display a table
    html_content += f'''
        <table id="table_dbhomes">
            <caption>Note: Color coding for pluggable databases (PDBs) open mode in last column: 
                <span style="color: {color_pdb_read_write}">READ_WRITE</span>
                <span style="color: {color_pdb_read_only}">READ_ONLY</span>
                <span style="color: {color_pdb_others}">MOUNTED and others</span>
            </caption>
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>Exadata<br>Infrastructure</th>
                    <th>VM cluster</th>
                    <th>DB HOME</th>
                    <th>Status</th>
                    <th>DB version<br><br>Current<hr>Latest</th>
                    <th>Databases : PDBs</th>
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        for vmcluster in vmclusters:
            if vmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                for db_home in db_homes:
                    if db_home.vm_cluster_id == vmcluster.id:
                        url1        = get_url_link_for_exadatainfrastructure(exadatainfrastructure)
                        url2        = get_url_link_for_vmcluster(vmcluster)
                        url3        = get_url_link_for_db_home(db_home)
                        html_style1 = f' style="color: {color_not_available}"' if (db_home.lifecycle_state != "AVAILABLE") else ''
                        html_style2 = f' style="color: {color_new_version_avail}"' if (db_home.db_version != db_home.db_update_latest) else ''

                        html_content += f'''
                <tr>
                    <td>{db_home.region}</td>
                    <td><a href="{url1}">{exadatainfrastructure.display_name}</a> </td>
                    <td><a href="{url2}">{vmcluster.display_name}</a> </td>
                    <td><b><a href="{url3}">{db_home.display_name}</a></b> </td>
                    <td><span{html_style1}>{db_home.lifecycle_state}</span></td>
                    <td><span{html_style2}>{db_home.db_version}</span><hr>{db_home.db_update_latest}</td>
                    <td style="text-align: left">'''

                        for database in db_home.databases:
                            url4          = get_url_link_for_database(database, db_home.region)
                            html_content += f'''
                        <a href="{url4}">{database.db_name}</a> : '''
                            # OCI pluggable database management is supported only for Oracle Database 19.0 or higher
                            try:
                                if database.is_cdb:
                                    for pdb in database.pdbs:
                                        url5 = get_url_link_for_pdb(pdb, db_home.region) #TUTU
                                        pdb_link_class = "pdb_link_others"
                                        if pdb.open_mode == "READ_WRITE":
                                            pdb_link_class = "pdb_link_read_write"
                                        elif pdb.open_mode == "READ_ONLY":
                                            pdb_link_class = "pdb_link_read_only"
                                        html_content += f'''
                        <a href="{url5}" class="pdb {pdb_link_class}">{pdb.pdb_name}</a>  '''
                            except:
                                pass

                            html_content += f'''
                        <br>'''

                        html_content += f'''
                    </td>
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def generate_html_table_autonomousvmclusters():
    format   = "%b %d %Y %H:%M %Z"
    html_content  = '''
    <div id="div_autovmclusters">
        <br>
        <h2>ExaCC Autonomous VM Clusters</h2>'''

    # if there is no autonomous vm cluster, just display None
    if len(autonomousvmclusters) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 autonomous vm cluster, so display a table
    html_content += '''
        <table id="table_autovmclusters">
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>Exadata<br>infrastructure</th>
                    <th>AUTONOMOUS<br>VM CLUSTER</th>
                    <th>Compartment</th>
                    <th class="exacc_maintenance">Maintenance runs</th>
                    <th>Status</th>
                    <th>OCPUs<br><br>Available<hr>Total</th>
                    <th>Memory</th>
                    <th>Local<br>Storage</th>
                    <th>Exadata<br>Storage</th>
                    <th>Autonomous DB Storage<br><br>Available<hr>Total</th>'''

    if display_license:
        html_content += '''
                    <th class="license">License model</th>'''        

    if display_dbs:
        html_content += '''
                    <th class="exacc_databases">Autonomous<br>Container<br>Database(s)</th>'''

    html_content += '''
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        for autonomousvmcluster in autonomousvmclusters:
            if autonomousvmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                cpt_name   = get_cpt_name_from_id(autonomousvmcluster.compartment_id)
                url1       = get_url_link_for_exadatainfrastructure(exadatainfrastructure)      
                url2       = get_url_link_for_autonomousvmcluster(autonomousvmcluster)

                html_content += f'''
                <tr>
                    <td>{autonomousvmcluster.region}</td>
                    <td><a href="{url1}">{exadatainfrastructure.display_name}</a></td>
                    <td><b><a href="{url2}">{autonomousvmcluster.display_name}</a></b> </td>
                    <td style="text-align: left">{cpt_name}</td>
                    <td class="exacc_maintenance" style="text-align: left">Last maintenance: <br>'''

                try:
                    html_content += f'''
                         - {autonomousvmcluster.last_maintenance_start.strftime(format)} (start)<br>'''
                except:
                    html_content += f'''
                         - no date/time (start)<br>'''

                try:
                    html_content += f'''
                         - {autonomousvmcluster.last_maintenance_end.strftime(format)} (end)<br><br>'''
                except:
                    html_content += f'''
                         - no date/time (end)<br><br>'''
                
                html_content += f'''
                        Next maintenance: <br>'''

                if autonomousvmcluster.next_maintenance == "":
                    html_content += f'''
                         - Not yet scheduled </td>'''
                else:
                    # if the next maintenance date is soon, highlight it using a different color
                    if (autonomousvmcluster.next_maintenance - now < timedelta(days=days_notification)):
                        html_content += f'''
                         - <span style="color: {color_date_soon}">{autonomousvmcluster.next_maintenance.strftime(format)}</span></td>'''
                    else:
                        html_content += f'''
                         - {autonomousvmcluster.next_maintenance.strftime(format)}</td>'''

                html_style1 = f' style="color: {color_not_available}"' if (autonomousvmcluster.lifecycle_state != "AVAILABLE") else ''
                html_style2 = f' style="color: {color_resources_warning}"' if autovmcl_storage_threshold_reached(autonomousvmcluster) else ''
                html_content += f'''
                    <td><span{html_style1}>{autonomousvmcluster.lifecycle_state}</span></td>
                    <td>{autonomousvmcluster.available_cpus}<hr>{autonomousvmcluster.cpus_enabled}</td>
                    <td>{autonomousvmcluster.memory_size_in_gbs} GB</td>
                    <td>{autonomousvmcluster.db_node_storage_size_in_gbs} GB</td>
                    <td>{autonomousvmcluster.data_storage_size_in_tbs} TB</td>
                    <td><span{html_style2}>{autonomousvmcluster.available_autonomous_data_storage_size_in_tbs} TB</span><hr>{autonomousvmcluster.autonomous_data_storage_size_in_tbs} TB</td>'''

                if display_license:
                    html_content += f'''
                    <td class="license">{autonomousvmcluster.license_model}</td>'''   

                if display_dbs:
                    acdbs = []
                    for auto_cdb in auto_cdbs:
                        if auto_cdb.autonomous_vm_cluster_id == autonomousvmcluster.id:
                            url = get_url_link_for_auto_cdb(auto_cdb)
                            acdbs.append(f'<a href="{url}">{auto_cdb.display_name}</a>')
                    separator = '<br>'
                    html_content += f'''
                    <td class="exacc_databases">{separator.join(acdbs)}</td>'''

                html_content += '''
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def autovmcl_storage_threshold_reached(autonomousvmcluster):
    avail    = autonomousvmcluster.available_autonomous_data_storage_size_in_tbs
    total    = autonomousvmcluster.data_storage_size_in_tbs
    used     = total - avail
    pct_used = used / total
    return pct_used > threshold_storage

def generate_html_table_autonomous_cdbs():
    format   = "%b %d %Y %H:%M %Z"
    html_content  = '''
    <div id="div_autocdbs">
        <br>
        <h2>ExaCC Autonomous Container Databases</h2>'''

    # if there is no autonomous container database, just display None
    if len(auto_cdbs) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 autonomous container database, so display a table
    html_content += '''
        <table id="table_autocdbs">
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>Exadata<br>infrastructure</th>
                    <th>Autonomous<br>VM Cluster</th>
                    <th>AUTONOMOUS<br>CONTAINER<br>DATABASE</th>
                    <th>Compartment</th>
                    <th>Version</th>
                    <th>Status</th>
                    <th>OCPUs<br><br>Available<hr>Total</th>
                    <th>Autonomous<br>Data Guard</th>
                    <th>Autonomous<br>Database(s)</th>
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        for autonomousvmcluster in autonomousvmclusters:
            if autonomousvmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                for auto_cdb in auto_cdbs:
                    if auto_cdb.autonomous_vm_cluster_id == autonomousvmcluster.id:
                        cpt_name  = get_cpt_name_from_id(auto_cdb.compartment_id)
                        url1      = get_url_link_for_exadatainfrastructure(exadatainfrastructure)      
                        url2      = get_url_link_for_autonomousvmcluster(autonomousvmcluster)
                        url3      = get_url_link_for_auto_cdb(auto_cdb)
                        dataguard = "Not enabled" if (auto_cdb.role == None) else auto_cdb.role

                        html_content += f'''
                <tr>
                    <td>{auto_cdb.region}</td>
                    <td><a href="{url1}">{exadatainfrastructure.display_name}</a></td>
                    <td><a href="{url2}">{autonomousvmcluster.display_name}</a> </td>
                    <td><b><a href="{url3}">{auto_cdb.display_name}</a></b> </td>
                    <td style="text-align: left">{cpt_name}</td>
                    <td>{auto_cdb.db_version}</td>
                    <td>{auto_cdb.lifecycle_state}</td>
                    <td>{auto_cdb.available_cpus}<hr>{auto_cdb.total_cpus}</td>
                    <td>{dataguard}</td>'''

                        adbs = []
                        for auto_db in auto_dbs:
                            if auto_db.autonomous_container_database_id == auto_cdb.id:
                                url4 = get_url_link_for_auto_db(auto_db)
                                adbs.append(f'<a href="{url4}">{auto_db.display_name}</a>')
                        separator = '<br>'
                        html_content += f'''
                    <td>{separator.join(adbs)}</td>'''
                
                        html_content += '''
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def generate_html_table_autonomous_dbs():
    format   = "%b %d %Y %H:%M %Z"
    html_content  = '''
    <div id="div_autodbs">
        <br>
        <h2>ExaCC Autonomous Databases</h2>'''

    # if there is no autonomous database, just display None
    if len(auto_dbs) == 0:
        html_content += '''
        None
    </div>'''
        return html_content

    # there is at least 1 autonomous database, so display a table
    html_content += '''
        <table id="table_autodbs">
            <tbody>
                <tr>
                    <th>Region</th>
                    <th>Exadata<br>infrastructure</th>
                    <th>Autonomous<br>VM Cluster</th>
                    <th>Autonomous<br>Container<br>Database</th>
                    <th>AUTONOMOUS<br>DATABASE</th>
                    <th>Status</th>
                    <th>DB Name</th>
                    <th>OCPUs</th>
                    <th>Storage</th>
                    <th>Workload<br>type</th>
                </tr>'''

    for exadatainfrastructure in exadatainfrastructures:
        for autonomousvmcluster in autonomousvmclusters:
            if autonomousvmcluster.exadata_infrastructure_id == exadatainfrastructure.id:
                for auto_cdb in auto_cdbs:
                    if auto_cdb.autonomous_vm_cluster_id == autonomousvmcluster.id:
                        for auto_db in auto_dbs:
                            if auto_db.autonomous_container_database_id == auto_cdb.id:
                                url1       = get_url_link_for_exadatainfrastructure(exadatainfrastructure)      
                                url2       = get_url_link_for_autonomousvmcluster(autonomousvmcluster)
                                url3       = get_url_link_for_auto_cdb(auto_cdb)
                                url4       = get_url_link_for_auto_db(auto_db)
                                html_style = f' style="color: {color_not_available}"' if (auto_db.lifecycle_state != "AVAILABLE") else ''
                                html_content += f'''
                <tr>
                    <td>{auto_db.region}</td>
                    <td><a href="{url1}">{exadatainfrastructure.display_name}</a></td>
                    <td><a href="{url2}">{autonomousvmcluster.display_name}</a> </td>
                    <td><a href="{url3}">{auto_cdb.display_name}</a> </td>
                    <td><b><a href="{url4}">{auto_db.display_name}</a></b> </td>
                    <td><span{html_style}>{auto_db.lifecycle_state}</span></td>
                    <td>{auto_db.db_name}</td>
                    <td>{auto_db.ocpu_count}</td>
                    <td>{auto_db.data_storage_size_in_gbs} GB </td>
                    <td>{auto_db.db_workload}</td>
                </tr>'''

    html_content += '''
            </tbody>
        </table>
    </div>'''

    return html_content

def generate_html_script_head():
    html_content  = '''
    <script>
        function removeClassFromTags(tags, className) {
            for (tag of tags)
            {
                tag.classList.remove(className);
            }            
        }
        
        function addClassToTags(tags, className) {
            for (tag of tags)
            {
                tag.classList.add(className);
            }            
        }

        function automatic_font_sizes_on_off(input_id) {
            var checkbox_val = document.getElementById(input_id).value;
            var td_th_tags = document.querySelectorAll('td,th');
            var h1_tags = document.querySelectorAll('h1');
            var h2_tags = document.querySelectorAll('h2');
            var h3_tags = document.querySelectorAll('h3');
            var text_tags = document.getElementsByClassName("text_outside_tables");
            if (checkbox_val == "on") {
                // disabling
                removeClassFromTags(td_th_tags, "auto_td_th");
                removeClassFromTags(h1_tags, "auto_h1");
                removeClassFromTags(h2_tags, "auto_h2");
                removeClassFromTags(h3_tags, "auto_h3");
                removeClassFromTags(text_tags, "auto_text_outside_tables");
                document.getElementById(input_id).value = "off";
            } else {
                // enabling
                addClassToTags(td_th_tags, "auto_td_th");
                addClassToTags(h1_tags, "auto_h1");
                addClassToTags(h2_tags, "auto_h2");
                addClassToTags(h3_tags, "auto_h3");
                addClassToTags(text_tags, "auto_text_outside_tables");
                document.getElementById(input_id).value = "on";
            }
        }

        function hide_show_rows_in_column(myclass, display, hide_show) {
            var all_col = document.getElementsByClassName(myclass);
                for(var i=0;i<all_col.length;i++)
                {
                    all_col[i].style.display = display;
                }
                document.getElementById(myclass).value = hide_show;
        }

        function hide_show_div(hide_show, div_id) {
            const mydiv = document.getElementById(div_id);
            if (hide_show == "show") {
                mydiv.style.display = 'block';
            } else {
                mydiv.style.display = 'none';
            }
        }

        function hide_show_column(input_id) {
            var checkbox_val = document.getElementById(input_id).value;
            if(checkbox_val == "hide")
            {
                hide_show_rows_in_column(input_id, "none", "show");
            } else {
                hide_show_rows_in_column(input_id, "table-cell", "hide");
            }
            if (input_id == "exacc_databases") {
                hide_show_div(checkbox_val, "div_dbhomes")
                hide_show_div(checkbox_val, "div_autocdbs")
                hide_show_div(checkbox_val, "div_autodbs")
            }
        }
    </script>'''

    return html_content

def generate_html_script_body():
    html_content  = '''
    <script>
        hide_show_column("exacc_maintenance")'''

    if display_license:
        html_content += '''
        hide_show_column("license")'''

    if display_dbs:
        html_content += '''
        hide_show_column("exacc_databases")'''

    html_content += '''
    </script>'''

    return html_content

def generate_html_report_options():
    html_content = '''
            <b>Report options:</b><br>
            <input type="checkbox" value="off" id="automatic_font_sizes" onchange="automatic_font_sizes_on_off(this.id);">Automatic font sizes<br>
            <input type="checkbox" value="show" id="exacc_maintenance" onchange="hide_show_column(this.id);" checked>Display quarterly maintenances information<br>'''

    if display_license:
        html_content += '''
            <input type="checkbox" value="show" id="license" onchange="hide_show_column(this.id);" checked>Display license models for VM clusters and Autonomous VM clusters<br>'''

    if display_dbs:
        html_content += '''
            <input type="checkbox" value="show" id="exacc_databases" onchange="hide_show_column(this.id);" checked>Display databases (DB Homes, databases, PDBs, Autonomous Container databases and Autonomous Databases)<br>'''

    html_content += '''
            <br>'''

    return html_content

def generate_html_report():

    # headers
    html_report = generate_html_headers()

    # Javascript code in head
    if report_options:
        html_report += generate_html_script_head()

    # head end and body start
    html_report += '''
</head>
<body>'''

    # Title
    html_report += f'''
    <div id="my_header">
        <h1>ExaCC status report for OCI tenant <span style="color: #0000FF">{tenant_name.upper()}<span></h1>
        <div class="text_outside_tables">
            <b>Date:</b> {now_str}<br>
            <br>'''

    if report_options:
        html_report += generate_html_report_options()

    html_report += f'''
        </div>
        <hr>
        <br>
    </div>'''

    # ExaCC Exadata infrastructures
    html_report += generate_html_table_exadatainfrastructures()

    # ExaCC VM Clusters
    html_report += generate_html_table_vmclusters()

    # ExaCC DB homes
    if display_dbs:
        html_report += generate_html_table_db_homes()
    
    # ExaCC Autonomous VM Clusters
    html_report += generate_html_table_autonomousvmclusters()

    # ExaCC Autonomous Container Databases
    if display_dbs:
        html_report += generate_html_table_autonomous_cdbs()

    # ExaCC Autonomous Databases
    if display_dbs:
        html_report += generate_html_table_autonomous_dbs()

    # Javascript code in body
    if report_options:
        html_report += generate_html_script_body()

    # end of body and html page
    html_report += '''
    <br>
</body>
</html>
'''

    #
    return html_report

# ---- send an email to 1 or more recipients 
def send_email(email_recipients, html_report):

    # The email subject
    email_subject = f"{tenant_name.upper()}: ExaCC status report"

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject
    msg['From']    = email.utils.formataddr((email_sender_name, email_sender_address))
    msg['To']      = email_recipients

    # The email body for recipients with non-HTML email clients.
    # email_body_text = ( "The quarterly maintenance for Exadata Cloud @ Customer group  just COMPLETED.\n\n" 
    #                     f"The maintenance report is stored as object \n" )

    # The email body for recipients with HTML email clients.
    email_body_html = html_report

    # Record the MIME types: text/plain and html
    # part1 = MIMEText(email_body_text, 'plain')
    part2 = MIMEText(email_body_html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    # msg.attach(part1)
    msg.attach(part2)

    # send the EMAIL
    try:
        email_recipients_list = email_recipients.split(",")
        server = smtplib.SMTP(email_smtp_host, email_smtp_port)
        server.ehlo()
        server.starttls()
        #smtplib docs recommend calling ehlo() before & after starttls()
        server.ehlo()
        server.login(email_smtp_user, email_smtp_password)
        server.sendmail(email_sender_address, email_recipients_list, msg.as_string())
        server.close()
    except Exception as err:
        print (f"ERROR in send_email(): {err}", file=sys.stderr)

# ---- get the email configuration from environment variables:
#      EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SENDER_NAME, EMAIL_SENDER_ADDRESS 
def get_email_configuration():
    global email_smtp_user
    global email_smtp_password
    global email_smtp_host
    global email_smtp_port
    global email_sender_name
    global email_sender_address

    try:
        email_smtp_user      = os.environ['EMAIL_SMTP_USER']
        email_smtp_password  = os.environ['EMAIL_SMTP_PASSWORD']
        email_smtp_host      = os.environ['EMAIL_SMTP_HOST']
        email_smtp_port      = os.environ['EMAIL_SMTP_PORT']
        email_sender_name    = os.environ['EMAIL_SENDER_NAME']
        email_sender_address = os.environ['EMAIL_SENDER_ADDRESS']
    except:
        print ("ERROR: the following environments variables must be set for emails: EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SENDER_NAME, EMAIL_SENDER_ADDRESS !", file=sys.stderr )
        exit (3)

def set_region(region_name):
    global signer
    global config

    if authentication_mode == "user_profile":
        config["region"] = region_name
    else:
        signer.region = region_name

# ---- Store the HTML report in an OCI bucket
def store_report_in_bucket(bucket_name, html_report):
    if authentication_mode == "user_profile":
        ObjectStorageClient = oci.object_storage.ObjectStorageClient(config)
    else:
        ObjectStorageClient = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    # Save report to bucket
    now_str = now.strftime("%Y-%m-%d_%H:%M")
    namespace = ObjectStorageClient.get_namespace().data
    if args.bucket_suffix:
        object_name = f"ExaCC_report_{now_str}_{args.bucket_suffix}.html"
    else:
        object_name = f"ExaCC_report_{now_str}.html"
    response  = ObjectStorageClient.put_object(
        namespace_name  = namespace,
        bucket_name     = bucket_name,
        object_name     = object_name,
        put_object_body = html_report,
        content_type    = "text/html",
        retry_strategy  = oci.retry.DEFAULT_RETRY_STRATEGY) 

# -------- main

# -- parse arguments
parser = argparse.ArgumentParser(description = "List ExaCC VM clusters in HTML format")
parser.add_argument("-a", "--all_regions", help="Do this for all regions", action="store_true")
parser.add_argument("-e", "--email", help="email the HTML report to a list of comma separated email addresses")
parser.add_argument("-bn", "--bucket-name", help="Store the HTML report in an OCI bucket")
parser.add_argument("-bs", "--bucket-suffix", help="Suffix for object name in the OCI bucket (-bn required)")
parser.add_argument("-db", "--databases", help="Display DB Homes, CDBs, PDBs, Autonomous Container Databases and Autonomous Databases", action="store_true")
parser.add_argument("-ro", "--report-options", help="Add report options for dynamic changes in Web browsers", action="store_true")
parser.add_argument("-l", "--license", help="Display license model for VM clusters and Autonomous VM clusters", action="store_true")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-p", "--profile", help="OCI profile for user authentication")
group.add_argument("-ip", "--inst-principal", help="Use instance principal authentication", action="store_true")

# TODO: -bn required for -bs

args = parser.parse_args()

profile         = args.profile
all_regions     = args.all_regions
display_dbs     = args.databases
report_options  = args.report_options
display_license = args.license

if args.inst_principal:
    authentication_mode = "instance_principal"
else:
    authentication_mode = "user_profile"

if args.email:
    get_email_configuration()

# -- authentication to OCI
if authentication_mode == "user_profile":
    # authentication using user profile
    try:
        config = oci.config.from_file(configfile,profile)
    except:
        print (f"ERROR: profile '{profile}' not found in config file {configfile} !", file=sys.stderr)
        exit (2)
    IdentityClient = oci.identity.IdentityClient(config)
    user = IdentityClient.get_user(config["user"], retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY).data
    RootCompartmentID = user.compartment_id
else:
    # authentication using instance principal
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    IdentityClient = oci.identity.IdentityClient(config={}, signer=signer)
    RootCompartmentID = signer.tenancy_id

# -- get list of subscribed regions
response = oci.pagination.list_call_get_all_results(
    IdentityClient.list_region_subscriptions, 
    tenancy_id = RootCompartmentID, 
    retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
regions = response.data

# -- Find the home region to build the console URLs later
for r in regions:
    if r.is_home_region:
        home_region = r.region_name

# -- Get list of compartments with all sub-compartments
response = oci.pagination.list_call_get_all_results(
    IdentityClient.list_compartments,
    compartment_id = RootCompartmentID,
    compartment_id_in_subtree = True,
    retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
compartments = response.data

# -- Get Tenancy Name
response = IdentityClient.get_tenancy(RootCompartmentID, retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
tenant_name = response.data.name

# -- Get current Date and Time (UTC timezone)
now = datetime.now(timezone.utc)
now_str = now.strftime("%c %Z")

# -- OCI 
# -- Run the search query/queries for ExaCC Exadata infrastructures and save results in exadatainfrastructures list
if not(all_regions):
    search_exadatainfrastructures()
else:
    for region in regions:
        set_region(region.region_name)
        search_exadatainfrastructures()

# -- Run the search query/queries for ExaCC VM clusters and save results in vmclusters list
if not(all_regions):
    search_vmclusters()
else:
    for region in regions:
        set_region(region.region_name)
        search_vmclusters()

# -- If --database option specificed, run the search query/queries for ExaCC DB homes and save results in db_homes list
if display_dbs:
    if not(all_regions):
        search_db_homes()
    else:
        for region in regions:
            set_region(region.region_name)
            search_db_homes()

# -- Run the search query/queries for ExaCC autonomous VM clusters and save results in autonomousvmclusters list
if not(all_regions):
    search_autonomousvmclusters()
else:
    for region in regions:
        set_region(region.region_name)
        search_autonomousvmclusters()

# -- If --database option specificed:
# - run the search query/queries for ExaCC autonomous container databases and save results in auto_cdbs list
# - run the search query/queries for ExaCC autonomous databases and save results in auto_dbs list
if display_dbs:
    if not(all_regions):
        search_auto_cdbs()
        search_auto_dbs()
    else:
        for region in regions:
            set_region(region.region_name)
            search_auto_cdbs()
            search_auto_dbs()

# -- Generate HTML page with results
html_report = generate_html_report()

# -- Display HTML report 
print(html_report)

# -- Send HTML report by email if requested
if args.email:
    send_email(args.email, html_report)

# -- Store HTML report into an OCI object storage bucket (in the home region) if requested
if args.bucket_name:
    set_region(home_region)
    store_report_in_bucket(args.bucket_name, html_report)

# -- the end
exit (0)
