###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

import json
import oci
import io
import logging
import pandas as pd

from oci.util import to_dict
from fdk import response
from datetime import datetime, timedelta

# Set Logging level.
logger = logging.getLogger()
logger.setLevel(logging.INFO)



def init_rps_client():
    try:
        rps_client = oci.auth.signers.get_resource_principals_signer()
    except Exception as e:
        logger.error("Init rps client error: %s.", e)
        raise
    else:
        logger.debug("Rps client initialized.")
    return rps_client


def init_datasafe_client(ds_rps_client):
    try:
        datasafe_client = oci.data_safe.DataSafeClient({}, signer=ds_rps_client)
    except Exception as e:
        logger.error("Init Data Safe client error: %s.", e)
        raise
    else:
        logger.debug("Data Safe client initialized.")
    return datasafe_client

def init_logging_ingestion_client(lo_rps_client):
    try:
        logging_ingestion_client = oci.loggingingestion.LoggingClient({}, signer=lo_rps_client)
    except Exception as e:
        logger.error("Init logging ingestion client error: %s.", e)
        raise
    else:
        logger.debug("Logging ingestion client initialized.")
    return logging_ingestion_client

def init_objectstorage_client(os_rps_client):
    try:
        objectstorage_client = oci.object_storage.ObjectStorageClient({}, signer=os_rps_client)
    except Exception as e:
        logger.error("Init OCI ObjectStorage client error: %s.", e)
        raise
    else:
        logger.debug("Logging OCI ObjectStorage client initialized.")
    return objectstorage_client

def generate_log_entries(audit_events, headAuditEventTime):
    logger.debug("Generate log entries.")
    aus=[]
    for i in audit_events.index: 
        aus.append(oci.loggingingestion.models.LogEntry(
            data = audit_events.loc[i].to_json(),
            id = audit_events.at[i, 'id'],
            time = audit_events.at[i, headAuditEventTime]
        ))
    logger.debug("End Function - Generate log entries.")
    return aus

def get_audit_events(data_safe_cl,l_compartment_id, l_sort_order, l_limit, l_sort_by, l_compartment_id_in_subtree, l_access_level, l_scim_query, headerTimeCollected, l_max_auditevents):
    logger.debug("Get DB audit events from Data Safe.")
    try:   
        audit_events_response = data_safe_cl.list_audit_events(
                                                                    compartment_id=l_compartment_id, 
                                                                    sort_order=l_sort_order,
                                                                    limit=l_limit, 
                                                                    sort_by=l_sort_by,
                                                                    compartment_id_in_subtree=l_compartment_id_in_subtree,
                                                                    access_level=l_access_level,
                                                                    scim_query=l_scim_query
                )
        
        # Add audit events in pandas dataframe.
        ds_audit = pd.DataFrame()
        ds_audit=pd.json_normalize(to_dict(audit_events_response.data), record_path='items')
        # Paging audit events
        while (audit_events_response.has_next_page and len(ds_audit) < l_max_auditevents):
            audit_events_response = data_safe_cl.list_audit_events(
                                                                    compartment_id=l_compartment_id, 
                                                                    sort_order=l_sort_order,
                                                                    limit=l_limit, 
                                                                    sort_by=l_sort_by,
                                                                    compartment_id_in_subtree=l_compartment_id_in_subtree,
                                                                    access_level=l_access_level,
                                                                    scim_query=l_scim_query,
                                                                    page=audit_events_response.next_page
            )
            # Add audit events in pandas dataframe.
            ds_audit=pd.concat([ds_audit,pd.json_normalize(to_dict(audit_events_response.data), record_path='items')],verify_integrity=True, ignore_index=True)
            logger.info("Paging list audit events from Data Safe.")
            logger.info("Number of audit events imported:  %s.", len(ds_audit))
        if (not ds_audit.empty):
            # To camel dataframe headers.
            ds_audit.columns = map(to_camel_case, ds_audit.columns)
            # Convert timecollected column in datatime format.
            ds_audit[headerTimeCollected] = pd.to_datetime(ds_audit[headerTimeCollected], format='mixed', yearfirst=True, utc=True)
            # Sort DataFrame by 'timeCollected' value.
            ds_audit = ds_audit.sort_values(by=headerTimeCollected, ascending=False, ignore_index=True)
            # Rebuild index of dataframe.
            ds_audit = ds_audit.reset_index(drop=True)
    except Exception as e:
        logger.error("List audits from Data Safe error: %s.", e)
        raise
    else:
        logger.debug("List audits from Data Safe done.")
        logger.info("Number of audit events imported:  %s.", len(ds_audit))
    return ds_audit

def put_logs(data, logging_ing_client, logging_log_id, l_headerAuditEventTime):
    logger.debug("Put DB audit events to OCI Logging.")
    put_logs_response = logging_ing_client.put_logs(
            log_id=logging_log_id,
            put_logs_details=oci.loggingingestion.models.PutLogsDetails(
                specversion="1.0",
                log_entry_batches=[
                     oci.loggingingestion.models.LogEntryBatch(
                         entries = generate_log_entries(data, l_headerAuditEventTime),
                         source="OracleDatabaseUnifiedAudit",
                         type='com.oraclecloud.logging.custom.oracledbunifiedaudit',
                         defaultlogentrytime='1900-01-01T00:00:00.000Z',
                         subject="OracleDatabaseUnifiedAudit"
                     )
                 ]
             ))   
    logger.debug("End Function - Put DB audit events to OCI Logging.")    

def to_camel_case(text):
    text = text.replace("-", " ").replace("_", " ")
    words = text.split()
    return "".join([w.capitalize() if w != words[0] else w for w in words])

def check_object_from_bucket(l_bucketName, l_objectName, ol_client):
    logger.debug("Check object file " + l_objectName + "is in a OCI ObjectStorage.")
    l_namespace = ol_client.get_namespace().data
    try:
        list_objects_response = ol_client.list_objects(namespace_name=l_namespace,
                                                       bucket_name=l_bucketName,
                                                       prefix=l_objectName
                                                       )
        if list_objects_response.data.objects:
            for o in list_objects_response.data.objects:
                # File already present in OCI ObjectStorage.
                logger.debug("ObjectName: " + str(o.name) + ".")
                if o.name == l_objectName:
                    logger.debug("Object file " + l_objectName + " is in a OCI ObjectStorage.")
                    fileExist = True
                else:
                    logger.debug("Object file " + l_objectName + " is not present in a OCI ObjectStorage.")
                    fileExist = False
        else:
            # File is not present in OCI ObjectStorage.
            logger.debug("Object file " + l_objectName + " is not present in a OCI ObjectStorage.")
            fileExist = False    
    except Exception as e:
        logger.error("Failed access to OCI ObjectStorage to check Object file " + l_objectName + ": %s.", e)
        raise
    else:
        logger.debug("Check object file " + l_objectName + " in OCI ObjectStorage done.")
    return fileExist

def check_file_lock_bucket(lo_bucketName, lo_objectName, lo_client, lo_fntimeout, lo_current_time):
    # Check if lock file is in OCI ObjectStorage.
    logger.debug("Check lock file is in a OCI ObjectStorage.")
    lockFilePresent = False
    lockFileExist = check_object_from_bucket(lo_bucketName, lo_objectName, lo_client)
    if lockFileExist:
        logger.debug("Check if lock file last modified time is > of fn execution.")
        # Get Last Modified Time lock file from OCI ObjectStorage.
        oblastmodifiedtime_str = get_object_last_modified_time_from_bucket(lo_bucketName, lo_objectName, lo_client)
        # Covert data in datatimeFormat date.
        oblastmodifiedtime = datetime.strptime(oblastmodifiedtime_str, '%a, %d %b %Y %H:%M:%S %Z')
        oblastmodifiedtime = oblastmodifiedtime + lo_fntimeout

        if lo_current_time > oblastmodifiedtime:
            logger.debug("Check if lock file last modified time is > of fn execution -> Current time: " + lo_current_time.isoformat(sep='T', timespec='milliseconds') + "> lock file last-modified time + fn timeout" + oblastmodifiedtime.isoformat(sep='T', timespec='milliseconds') + ".")
            logger.debug("Lock is not valid.")
            lockFilePresent = False
        else:
            logger.debug("Check if lock file last modified time is < of fn execution -> Current time: " + lo_current_time.isoformat(sep='T', timespec='milliseconds') + "> lock file last-modified time + fn timeout" + oblastmodifiedtime.isoformat(sep='T', timespec='milliseconds')+ ".")
            logger.debug("Lock is valid.")
            lockFilePresent = True
    else:
        lockFilePresent = False 
    return lockFilePresent

def get_object_from_bucket(r_bucketName, r_objectName, or_client, r_lastAuditEventRecordTime_attr):
    # Get cursor file with last execution in OCI ObjectStorage.
    logger.debug("Get object " + r_objectName + " file from OCI ObjectStorage.")
    r_namespace = or_client.get_namespace().data
    try:
        object = or_client.get_object(r_namespace, r_bucketName, r_objectName)   
        
        r_lastexecutionupdatime_json = json.loads(object.data.text)
        r_lastexecutionupdatime = r_lastexecutionupdatime_json.get(r_lastAuditEventRecordTime_attr)
    except Exception as e:
        logger.error("Failed access to OCI ObjectStorage to get object file: %s.", e)
        raise
    else:
        logger.debug("The object " + r_objectName + " was retrieved from OCI ObjectStorage.")
    return r_lastexecutionupdatime

def delete_object_from_bucket(d_bucketName, d_objectName, d_client):
    # Delete object from OCI ObjectStorage.
    logger.debug("Delete object " + d_objectName + " OCI ObjectStorage.")
    d_namespace = d_client.get_namespace().data
    try:
        delete = d_client.delete_object(d_namespace, d_bucketName, d_objectName)   
    except Exception as e:
        logger.error("Failed access to OCI ObjectStorage to delete object " + d_objectName + " : %s.", e)
        raise
    else:
        logger.debug("The object " + d_objectName + " was deleted from OCI ObjectStorage.")
    

def get_object_last_modified_time_from_bucket(h_bucketName, h_objectName, h_client):
    # Get last_modified_time header from file in OCI ObjectStorage.
    logger.debug("Get last_modified_time header from object " + h_objectName + " in OCI ObjectStorage.")
    h_namespace = h_client.get_namespace().data
    try:
        object_headers = h_client.head_object(h_namespace, h_bucketName, h_objectName)   
        
        h_last_update_time_object = object_headers.headers['last-modified']
        logger.debug("Last modified time: " + str(h_last_update_time_object) + " was retrieved from object " + str(h_objectName) + " from OCI ObjectStorage.")
    except Exception as e:
        logger.error("Failed access to OCI ObjectStorage for get last_modified_time header object " + h_objectName + " in OCI ObjectStorage: %s.", e)
        raise
    else:
        logger.debug("Last modified time was retrieved from object " + h_objectName + " from OCI ObjectStorage.")
    return h_last_update_time_object

def put_object_to_bucket(w_bucketName, w_objectName, ow_client, w_content_object):
    logger.debug("Put object " + w_objectName + " value to OCI ObjectStorage.")
    nspace = ow_client.get_namespace().data
    try:
        object = ow_client.put_object(nspace, w_bucketName, w_objectName, w_content_object)
                
    except Exception as e:
        logger.error("Failed write to OCI ObjectStorage to update/create object: %s.", e)
        raise
    else:
        logger.debug("Updated/created object " + w_objectName + " in OCI ObjectStorage.")

def last_collected_time(last_time_collected):
    logger.debug("Last time DB audit event collected: " + str(last_time_collected) + ".")
    str_list_time_collected = last_time_collected.isoformat(sep='T', timespec='milliseconds').replace("+00:00", "Z")
    if str_list_time_collected.find('Z') == -1:
            str_list_time_collected = str_list_time_collected + "Z"
    logger.debug("Last time DB audit event collected: " + str_list_time_collected + ".")
    return str_list_time_collected

def generate_scim_query(q_last_time_collected, q_actual_time):
    logger.debug("Generate SCIM query for Data Safe.")
    scim_query = '(timeCollected gt "' + q_last_time_collected + '")'
    logger.info("SCIM query: " + str(scim_query) + ".")
    return scim_query

def main(ctx):
    # Initializing variables.
    limit = 10000
    access_level = "ACCESSIBLE"
    sort_by = "timeCollected"
    sort_order = "ASC"
    compartment_id_in_subtree = True
    headerTimeCollected = "timeCollected"
    headerAuditEventTime = "auditEventTime" 
    cursor_file_name = "cursor.json"
    lock_file_name = "lock.json"
    lastAuditEventRecordTime_attr = "lastAuditEventRecordTime"
    ds_dbaudit_events = pd.DataFrame()
    # Maximun number of audit events collected for each execution. The value 50000 is specific with function timeout equal to 5 mins.  
    max_auditevents = 50000
    try:
        logger.info("Function start.")
        logger.info("Get configuration parameter.")
        cfg = dict(ctx.Config())
        ociDataSafeCompartmentOCID = cfg["ociDataSafeCompartmentOCID"]
        logger.debug(
            "DataSafe Compartment OCID: " + ociDataSafeCompartmentOCID + "."
        )
        ociLoggingLogOCID = cfg["ociLoggingLogOCID"]
        logger.debug(
            "OCI Logging OCID: " + ociLoggingLogOCID + "."
        )
        ociOSTrackerBucketName = cfg["ociOSTrackerBucketName"]
        logger.debug(
            "OCI OS BucketName: " + ociOSTrackerBucketName + "."
        )
        
        # Calculate fn timeout configured for manage validity of lock file.
        fndeadlinetime_str = ctx.Deadline()
        fndeadlinetime = datetime.strptime(fndeadlinetime_str, '%Y-%m-%dT%H:%M:%SZ')
        current_time_t = datetime.utcnow()
        fntimeout = fndeadlinetime - current_time_t
        logger.debug("Function expire time: " + fndeadlinetime_str + ".")
        logger.debug("Function timeout configured: " + str(fntimeout.total_seconds()) + " sec.")

        current_time = datetime.utcnow().isoformat(sep='T', timespec='milliseconds').replace("+00:00", "Z")
        if current_time.find('Z') == -1:
            current_time = current_time + "Z"
        logger.debug("Current Time: " + str(current_time))
        logger.info("Start execution.")
        # Step 1: Initializing RPS client.
        logger.debug("Initializing RPS client")
        rps = init_rps_client()
        logger.debug("RPS client obtain with instance principal.")
        # Step 2: Initializing OCI ObjectStorage client.
        logger.debug("Initializing OCI ObjectStorage client.")
        os_client = init_objectstorage_client(rps)
        logger.debug("OCI ObjectStorage client obtained with instance principal.")
        # Step 3: Check file lock in OCI ObjectStorage.
        logger.debug("Manage file lock in OCI ObjectStorage.")
        check_file_lock = check_file_lock_bucket(ociOSTrackerBucketName, lock_file_name, os_client, fntimeout, current_time_t)
        if check_file_lock:
            # File lock is present and valid other fn execution is active.
            logger.info("File lock is valid other fn session is yet in execution.")
        else:
            # Step 4: Check if exist file cursor in OCI ObjectStorage. 
            logger.debug("Check if file cursor exist in OCI ObjectStorage.")
            check_existence_cursor_file = check_object_from_bucket(ociOSTrackerBucketName, cursor_file_name, os_client)
            logger.debug("Check existence of cursor file in OCI ObjectStorage done.")
            if check_existence_cursor_file:  
                logger.debug("Cursor file is in the OCI ObjectStorage.")
                # Step 5: Create/Update lock lile.
                logger.debug("Create/Update lock file.")
                content_lock_file=json.dumps({"lock": current_time})
                put_object_to_bucket(ociOSTrackerBucketName, lock_file_name, os_client, content_lock_file)
                # Step 6: Get file cursor from OCI ObjectStorage. 
                logger.debug("Get file cursor content from OCI ObjectStorage.")
                lastexecutionupdatime = get_object_from_bucket(ociOSTrackerBucketName, cursor_file_name, os_client, lastAuditEventRecordTime_attr)
                logger.debug("Content from file cursor lasteventexecutiontime: " + lastexecutionupdatime + ".")
                logger.debug("Content from file cursor done.") 
                # Step 7: Initializing Data Safe client.
                logger.debug("Initializing Data Safe client.")
                data_safe_client = init_datasafe_client(rps)
                logger.debug("Data Safe client obtained with instance principal.")
                # Step 8: Generate SCIM query based on time window.
                logger.debug("Generate SCIM query.")
                scim_query= generate_scim_query(lastexecutionupdatime, current_time)
                logger.debug("Generate SCIM query done.")
                # Step 9: Get DB audit events from Data Safe.
                logger.debug("Get DB audit events from Data Safe.")
                ds_dbaudit_events = get_audit_events(data_safe_client,ociDataSafeCompartmentOCID, sort_order, limit, sort_by, compartment_id_in_subtree, access_level, scim_query, headerTimeCollected, max_auditevents)
                if not ds_dbaudit_events.empty:
                    # Step 10: Get last event time DB audits collected.
                    lastdbauditeventcolletcted = ds_dbaudit_events[headerTimeCollected].iloc[0]
                    logger.debug("Last DB audit time events collected from Data Safe: " + str(lastdbauditeventcolletcted) + ".")
                    # Step 11: Initializing OCI Logging ingestion client.
                    logger.debug("Initializing OCI Logging ingestion client.")
                    oci_logging_ingestion_client = init_logging_ingestion_client(rps)
                    logger.debug("OCI Logging ingestion client obtained with instance principal.") 
                    #Step 12: Send DB audit events to OCI Logging.
                    logger.debug("Send audit events to OCI Logging.")
                    put_logs(ds_dbaudit_events, oci_logging_ingestion_client, ociLoggingLogOCID, headerAuditEventTime)
                    logger.debug("End send audit events to OCI Logging.")
                    #Step 13: Put Last time collect DB audit events in cursor file.
                    logger.debug("Put last time collect DB audit events in cursor file in OCI ObjectStorage.")
                    new_lastdbauditeventcolletcted = last_collected_time(lastdbauditeventcolletcted)
                    content_cursor_file_time=json.dumps({lastAuditEventRecordTime_attr: new_lastdbauditeventcolletcted})
                    put_object_to_bucket(ociOSTrackerBucketName, cursor_file_name, os_client, content_cursor_file_time)
                    logger.debug("End last time collect DB audit events in cursor file in OCI ObjectStorage.")
                # Step 14: Delete lock file in OCI ObjectStorage.
                logger.debug("Delete lock file in OCI ObjectStorage.")
                delete_object_from_bucket(ociOSTrackerBucketName, lock_file_name, os_client)
            else:
                logger.debug("Cursor file is not in the OCI ObjectStorage, initialize cursor file.")
                content_cursor_file=json.dumps({lastAuditEventRecordTime_attr: current_time})
                put_object_to_bucket(ociOSTrackerBucketName, cursor_file_name, os_client, content_cursor_file)
    
    except Exception as e:
        logger.error("Failed main function: %s.", e)
        raise
    else:
        logger.debug("Main function ok.")

def handler(ctx, data: io.BytesIO = None):
    oci.base_client.is_http_log_enabled(False)
    try:
        if (data and data.getvalue()):
            notification = json.loads(data.getvalue())
            if (notification['type'] != "FIRING_TO_OK"):
                logger.debug("Notification FIRING_TO_OK - execute main")
                main(ctx)
                
        else:
            logger.debug("Other conditions - execute main.")
            main(ctx)
        return response.Response(
            ctx,
            response_data=json.dumps({"status": "ok"}),
            headers={"Content-Type": "application/json"},
        )
    except (Exception, ValueError) as ex:
        logger.error("error during routine: %s", ex)
        pass
        return response.Response(
            ctx, status_code=401, response_data=json.dumps({"error": "exception"})
        )