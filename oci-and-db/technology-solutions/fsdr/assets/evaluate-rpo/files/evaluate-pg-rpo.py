# -----------------------------------------------------------------------------
# evaluate-pg-rpo.py
#
# Script that evaluates the RPO of a FSDR Protection Group. Currently supports the 
# following services:
#  - Volume Groups
#  - Buckets
#  - File Systems
#  - Movable VMs 
#  - ATP Serverless
#  - Base DB Services
#  - Load Balancers
#   
# Version Control:
# 1.0 - 13/10/2025 - First released version  
# 1.1 - 21/10/2025 - License updated  
# 1.2 - 31/10/2025 - Added information about OKE metadata backup when a cluster is in the 
#                    in the protection group.  
# 1.3 - 24/03/2026 - Cleanup and better date management
#
# Copyright (c) 2026 Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/
#
# You may use, copy, modify, and distribute this software and its documentation
# under the terms of the UPL. This software is provided "AS IS" without warranty
# of any kind.
#
# Oracle does not provide support for this script; community support only.
# This software is provided as it is and need to be considered an example
# of a possible implementation rather than for general use. 
#
# Script provided by: Cristiano Ghirardi, Oracle employee
# -----------------------------------------------------------------------------

import oci
import re
import argparse
import time
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VERSION = "1.3"
VERSION_DATE = "24/03/2026"

def to_utc_aware(dt):
    """Return a timezone-aware UTC datetime, or None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive timestamps are UTC (common OCI behavior fallback)
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def lag_seconds_from(now_utc, ts):
    """Compute lag in seconds from timestamp; inf if missing."""
    ts_utc = to_utc_aware(ts)
    if ts_utc is None:
        return float('inf')
    return (now_utc - ts_utc).total_seconds()

def parse_apply_lag(apply_lag):
    """Apply Lag to seconds"""
    time_units = {
        'hour': 3600,
        'hours': 3600,
        'minute': 60,
        'minutes': 60,
        'second': 1,
        'seconds': 1
    }

    # Match patterns like: 3 hour, 30 minute, 13 seconds
    pattern = r'(\d+)\s*(hour|hours|minute|minutes|second|seconds)'
    matches = re.findall(pattern, apply_lag.lower())

    if not matches:
        logging.warning("Unrecognized apply_lag format: %r", apply_lag)
        return None
    
    total_seconds = 0
    for value, unit in matches:
        total_seconds += int(value) * time_units[unit]
    return total_seconds

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(prog="evaluate-pg-rpo", description="Evaluate the RPO of a FSDR Protection Group.")
    parser.add_argument("-p", "--protection_group_id", type=str, required=False)
    parser.add_argument("-r", "--region", type=str)
    parser.add_argument("-t", "--tagging", action='store_true', help="Tagging flag, when enabled write the RPO in a free-form tag on the PG. Defaulting to no tagging.")
    parser.add_argument("-c", "--configuration_file", type=str, default="~/.oci/config", help="OCI configuration file, defaulting to ~/.oci/config. If \"none\" is provided, instance principal authentication is used.")
    parser.add_argument("-d", "--debug", action='store_true', help="Debug flag, defaulting to no debug")
    parser.add_argument("-v", "--version", action='store_true', help="Shows version.")
    args = parser.parse_args()
    debug_mode = args.debug
    tagging_mode = args.tagging
    
    if args.version:
        print("Version: ", VERSION,"-", VERSION_DATE)
        sys.exit(0)
        
    if args.protection_group_id is None:
        print("-p/--protection_group_id <Protection Group OCID> is required.")
        sys.exit(1)
        
    # Setup basic logging
    logging.basicConfig(
        level=logging.DEBUG if debug_mode else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s [%(module)s.%(funcName)s:%(lineno)d]',
        datefmt='%H:%M:%S'
    )

    inst_signer = None
    if args.configuration_file == "none":
        logging.debug("Instance authentication requested.")
        try:
            inst_signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            prim_config = {}
            stby_config = {}
        except Exception as ex:
            logging.error('Error in getting instance principal authentication: %s', ex)
            sys.exit(1)
    else:
        logging.debug("File authentication requested.")
        # Expand tilde for config file paths
        config_path = os.path.expanduser(args.configuration_file)
        try:
            prim_config = oci.config.from_file(config_path)
            stby_config = oci.config.from_file(config_path)
        except Exception as ex:
            logging.error('Error in OCI configuration: %s', ex)
            sys.exit(1)
    
    if args.region:
        logging.debug("Region set to: %s", args.region)
        try:
            prim_config.update({"region": args.region})
            stby_config.update({"region": args.region})
        except Exception as ex:
            logging.error('Error in OCI configuration, when changing region: %s', ex)
            sys.exit(1)

    try:
        if inst_signer:
            dr_client = oci.disaster_recovery.DisasterRecoveryClient(prim_config, signer=inst_signer)
        else:
            dr_client = oci.disaster_recovery.DisasterRecoveryClient(prim_config)
        primary_pg_id = args.protection_group_id
        get_dr_pg_res = dr_client.get_dr_protection_group(dr_protection_group_id=primary_pg_id)
        if get_dr_pg_res.data.role == "PRIMARY":
            logging.debug("Protection group: %s is PRIMARY", get_dr_pg_res.data.display_name)
            dr_client_prim = dr_client
            standby_pg_id = get_dr_pg_res.data.peer_id
            stby_config.update({"region": get_dr_pg_res.data.peer_region})
            if inst_signer:
                dr_client_stby = oci.disaster_recovery.DisasterRecoveryClient(stby_config, signer=inst_signer)
            else:
                dr_client_stby = oci.disaster_recovery.DisasterRecoveryClient(stby_config)
        else:
            logging.debug("Protection group: %s is STANDBY", get_dr_pg_res.data.display_name)
            dr_client_stby = dr_client
            standby_pg_id = primary_pg_id
            primary_pg_id = get_dr_pg_res.data.peer_id
            prim_config.update({"region": get_dr_pg_res.data.peer_region})
            if inst_signer:
                dr_client_prim = oci.disaster_recovery.DisasterRecoveryClient(prim_config, signer=inst_signer)
            else:
                dr_client_prim = oci.disaster_recovery.DisasterRecoveryClient(prim_config)
            get_dr_pg_res = dr_client_prim.get_dr_protection_group(dr_protection_group_id=primary_pg_id)
    except Exception as ex:
        logging.error('Error in DisasterRecoveryClient: %s', ex)
        sys.exit(1)

    try:
        components = get_dr_pg_res.data.members
        rpo = 0
        rpo_driving_component = ""
        comp_rpo = []
        logging.debug("===> Evaluation Start")
        now_utc = datetime.now(timezone.utc)
        oke_string = []
        begin_time = time.time()
        # Initialize clients once per region/config
        if inst_signer:
            db_client_prim = oci.database.DatabaseClient(prim_config, signer=inst_signer)
            db_client_stby = oci.database.DatabaseClient(stby_config, signer=inst_signer)
            bs_client_prim = oci.core.BlockstorageClient(prim_config, signer=inst_signer)
            bs_client_stby = oci.core.BlockstorageClient(stby_config, signer=inst_signer)
            os_client_prim = oci.object_storage.ObjectStorageClient(prim_config, signer=inst_signer)
            os_client_stby = oci.object_storage.ObjectStorageClient(stby_config, signer=inst_signer)
            fs_client_prim = oci.file_storage.FileStorageClient(prim_config, signer=inst_signer)
        else:
            db_client_prim = oci.database.DatabaseClient(prim_config)
            db_client_stby = oci.database.DatabaseClient(stby_config)
            bs_client_prim = oci.core.BlockstorageClient(prim_config)
            bs_client_stby = oci.core.BlockstorageClient(stby_config)
            os_client_prim = oci.object_storage.ObjectStorageClient(prim_config)
            os_client_stby = oci.object_storage.ObjectStorageClient(stby_config)
            fs_client_prim = oci.file_storage.FileStorageClient(prim_config)
        for c in components:
            logging.debug("")
            logging.debug("Member type: %s", c.member_type)
            logging.debug("Member info:")
            logging.debug(c)
            # Oracle Base DB System
            if c.member_type == "DATABASE":
                get_db_res = db_client_prim.get_database(c.member_id)
                list_dg_ass_res = db_client_prim.list_data_guard_associations(c.member_id)
                associations = list_dg_ass_res.data
                db_rpo = 0
                for a in associations:
                    # Defensive extract for apply_lag (should be "XX seconds", can be 0)
                    lag_seconds = 0
                    if hasattr(a, 'apply_lag'):
                        logging.debug("Apply Lag: %s", a.apply_lag)
                        lag_seconds = parse_apply_lag(a.apply_lag)
                    db_rpo = max(db_rpo, lag_seconds)
                logging.debug("%s : %s RPO is: %s sec", c.member_type, get_db_res.data.db_name, db_rpo)
                comp_rpo.append({'type': c.member_type, 'name': get_db_res.data.db_name, 'rpo': db_rpo})
                if db_rpo > rpo:
                    rpo_driving_component = c.member_type
                rpo = max(db_rpo, rpo)
            # Oracle Autonomous Database
            elif c.member_type == "AUTONOMOUS_DATABASE":
                get_adb_res = db_client_prim.get_autonomous_database(c.member_id)
                adb_rpo = 60  # As per Oracle's typical max SLA
                logging.debug("%s : %s RPO is: %s sec", c.member_type, get_adb_res.data.display_name, adb_rpo)
                comp_rpo.append({'type': c.member_type, 'name': get_adb_res.data.display_name, 'rpo': adb_rpo})
                if adb_rpo > rpo:
                    rpo_driving_component = c.member_type
                rpo = max(adb_rpo, rpo)
            # Block Storage Volume Group
            elif c.member_type == "VOLUME_GROUP":
                get_vg_res = bs_client_prim.get_volume_group(c.member_id)
                replicas = get_vg_res.data.volume_group_replicas
                for r in replicas:
                    get_vg_rep_res = bs_client_stby.get_volume_group_replica(r.volume_group_replica_id)
                    sync_time = get_vg_rep_res.data.time_last_synced
                    sync_lag = lag_seconds_from(now_utc, sync_time)
                    # if sync_time:
                    #    sync_lag = (now_utc - sync_time).total_seconds()
                    # else:
                    #    sync_lag = float('inf')
                    vol_rpo = sync_lag
                    logging.debug("%s : %s RPO is: %s sec", c.member_type, get_vg_res.data.display_name, vol_rpo)
                    comp_rpo.append({'type': c.member_type, 'name': get_vg_res.data.display_name, 'rpo': vol_rpo})
                    if vol_rpo > rpo:
                        rpo_driving_component = c.member_type
                    rpo = max(vol_rpo, rpo)
            # Object Storage Bucket
            elif c.member_type == "OBJECT_STORAGE_BUCKET":
                get_bucket_res = os_client_prim.get_bucket(c.namespace_name, c.bucket_name)
                list_rep_pol_res = os_client_prim.list_replication_policies(c.namespace_name, c.bucket_name)
                policies = list_rep_pol_res.data
                for p in policies:
                    sync_time = None
                    if hasattr(p, 'time_last_sync'):
                        sync_time = p.time_last_sync
                    sync_lag = lag_seconds_from(now_utc, sync_time)
                    # if sync_time:
                    #     sync_lag = (now_utc - sync_time).total_seconds()
                    # else:
                    #     sync_lag = float('inf')
                    obj_rpo = sync_lag
                    logging.debug("%s : %s RPO is: %s sec", c.member_type, get_bucket_res.data.name, obj_rpo)
                    comp_rpo.append({'type': c.member_type, 'name': get_bucket_res.data.name, 'rpo': obj_rpo})
                    if obj_rpo > rpo:
                        rpo_driving_component = c.member_type + " : " + get_bucket_res.data.name
                    rpo = max(obj_rpo, rpo)
            # OCI File System
            elif c.member_type == "FILE_SYSTEM":
                get_fs_res = fs_client_prim.get_file_system(c.member_id)
                # list_replications() API for File Storage expects compartment_id, availability_domain and file_system_id
                list_fs_reps_res = fs_client_prim.list_replications(
                    get_fs_res.data.compartment_id,
                    get_fs_res.data.availability_domain,
                    file_system_id=c.member_id
                )
                replications = list_fs_reps_res.data
                for r in replications:
                    sync_time = getattr(r, 'recovery_point_time', None)
                    sync_lag = lag_seconds_from(now_utc, sync_time)
                    # if sync_time:
                    #     sync_lag = (now_utc - sync_time).total_seconds()
                    # else:
                    #     sync_lag = float('inf')
                    fs_rpo = sync_lag
                    logging.debug("%s : %s RPO is: %s sec", c.member_type, get_fs_res.data.display_name, fs_rpo)
                    comp_rpo.append({'type': c.member_type, 'name': get_fs_res.data.display_name, 'rpo': fs_rpo})
                    if fs_rpo > rpo:
                        rpo_driving_component = c.member_type
                    rpo = max(fs_rpo, rpo)
            # Moving Compute Instance      
            elif c.member_type == "COMPUTE_INSTANCE_MOVABLE":
                logging.debug("Movable Compute Instance RPO depends on the Volume Groups RPO")
            elif c.member_type == "OKE_CLUSTER":
                if inst_signer:
                    ce_client = oci.container_engine.ContainerEngineClient(prim_config, signer=inst_signer)
                else:
                    ce_client = oci.container_engine.ContainerEngineClient(prim_config)
                get_clu_res = ce_client.get_cluster(c.member_id)
                clu_name = get_clu_res.data.name
                obj_name = str(primary_pg_id + "-" + c.member_id + "/metadata.yaml")
                get_obj_res = os_client_stby.get_object(c.backup_location.namespace, c.backup_location.bucket, obj_name)
                # The content is in response.data as a stream. Read it to bytes, or decode directly for text
                yaml_content = get_obj_res.data.content.decode('utf-8')
                # Parse YAML
                yaml_dict = yaml.safe_load(yaml_content)
                tz = ZoneInfo("UTC")
                latest_backup_time = datetime.strptime(yaml_dict["latest_backup"], "%Y%m%d%H%M").replace(tzinfo=tz)
                time_diff = now_utc - latest_backup_time
                hours_passed = time_diff.total_seconds() / 3600
                logging.debug("%s : %s latest backup was %s hours ago", c.member_type, clu_name, hours_passed)
                oke_string.append({'cluster': clu_name, 'hours' : hours_passed})  
            # Everything else
            else:
                logging.debug("Unknown member type; skipped.")
    except Exception as ex:
        logging.error('Error in Evaluation: %s', ex)
        sys.exit(1)
        
    end_time = time.time()
    logging.debug("===> Evaluation End")
    logging.debug("===> Elaboration time: %.2f sec", end_time - begin_time)

    # Update freeform tag on both Protection Groups
    if tagging_mode:
        try:
            logging.debug("Updating RPO freeform tag on both Protection Groups")
            rpo_string = f"{rpo:.0f} sec"
            upd_rec = oci.disaster_recovery.models.UpdateDrProtectionGroupDetails(freeform_tags={'RPO': rpo_string})
            dr_client_prim.update_dr_protection_group(upd_rec, primary_pg_id)
            dr_client_stby.update_dr_protection_group(upd_rec, standby_pg_id)
        except Exception as ex:
            logging.error('Error in updating RPO tags: %s', ex)
            sys.exit(1)

    # Output
    print("\nComponents RPO:")    
    print("-------- Type --------   -------- Name --------   --- RPO (sec) ---")
    for r in comp_rpo:
        rpo_str = f"{r['rpo']:6.0f}" if r['rpo'] != float('inf') else " N/A "
        print(f"{r['type']:24s} {r['name']:24s} {rpo_str}")
    print("")
    print("Protection Group RPO:")
    print("Global RPO            :", f"{rpo:6.0f}" if rpo != float('inf') else "N/A", "sec")
    print("Component driving RPO :", rpo_driving_component)
    print("")
    
    if oke_string:
        print("OKE clusters are present:")  
        print("-----------------------------------------------------------------")  
        for o in oke_string:
            print(f"> Cluster Name : {o['cluster']:24s}\n  Hours Since Latest Metadata Backup: {o['hours']:6.0f}")
        
if __name__ == "__main__":
    main()

