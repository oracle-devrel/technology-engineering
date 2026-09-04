# -------------------------------------------------------------------------------------------------------
# exccbb_iude.py
# -------------------------------------------------------------------------------------------------------
# Version 0.6
# -------------------------------------------------------------------------------------------------------
# Release Notes
# 2026-01-20: grolla@oracle
# --- v0.6: testing
# 2025-12-20: grolla@oracle
# --- v0.5: added AVMC analysis
# 2025-12-10: grolla@oracle
# --- v0.4: extended for both ExaDB-D and ExaDB-C@C
# 2025-10-30: grolla@oracle
# --- v0.3: added the options to get info from multiple regions
# --------- include in the config file the field "regions" equal to comma separated list of regions
# 2025-10-20: grolla@oracle
# --- v0.2: Improvement in error managements
# 2025-10-20: grolla@oracle
# --- v0.1: First Release
# -------------------------------------------------------------------------------------------------------
# Installation Notes
#  Requirements:
#   - Python 3.7 or higher
#   - OCI SDK
#  To install OCI SDK:
#   - pip install oci
# -------------------------------------------------------------------------------------------------------
import os
import logging
import datetime
import argparse
import oci
import json
import sys


VERSION = "0.6"
SUFFIX = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_FILE = ""
HTML_FILE = ""
CSV_FILE = ""
JSON_FILE = ""


def env_config(running_path, customer):
    # create LOG directory
    log_path = "/LOG"
    log_pfix = "".join(["/exccbb_iude_log_", customer, "_"])
    log_exte = ".log"
    log_sign = "exaccbb_iude"
    out_path = "/OUT"
    out_pfix = "".join(["/exccbb_iude_out_", customer, "_"])
    out_exte = ".json"
    htm_pfix = "".join(["/exccbb_iude_out_", customer, "_"])
    htm_exte = ".html"
    csv_pfix = "".join(["/exccbb_iude_out_", customer, "_"])
    csv_exte = ".csv"

    try:
        if os.path.exists("".join([running_path, log_path])):
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')},000 - exaccbb_iude - INFO - LOG Folder already exists under {running_path}, skipping creation")
        else:
            os.mkdir("".join([running_path, log_path]))
    except Exception as error_a:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')},000 - exaccbb_iude - CRITICAL - Unable to create LOG folder in {running_path}. Exiting. [Error 1]")
        print(error_a)
        exit(1)

    try:
        if os.path.exists("".join([running_path, out_path])):
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')},000 - exaccbb_iude - INFO - OUT Folder already exists under {running_path}, skipping creation")
        else:
            os.mkdir("".join([running_path, out_path]))
    except Exception as error_a:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')},000 - exaccbb_iude - CRITICAL - Unable to create LOG folder in {running_path}. Exiting. [Error 2]")
        print(error_a)
        exit(2)

    # configuring logger
    try:
        logfile = "".join([log_pfix, SUFFIX, log_exte])
        logdir = "".join([running_path, log_path])
        logfile = "".join([logdir, logfile])

        global JSON_FILE
        JSON_FILE = "".join([running_path, out_path, out_pfix, SUFFIX, out_exte])

        global HTML_FILE
        HTML_FILE = "".join([running_path, out_path, htm_pfix, SUFFIX, htm_exte])

        global CSV_FILE
        CSV_FILE = "".join([running_path, out_path, csv_pfix, SUFFIX, csv_exte])

        logger = logging.getLogger("exacclogger")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - '+log_sign+' - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # You can set the desired log level for console output
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logger.info('Logging initialized, starting the script.')

        return logger

    except Exception as error_a:
        print("CRITICAL: Something went wrong trying to configure the logging. Exiting. [Error 3]")
        print(error_a)
        exit(3)


def get_exadb_details(infra_type, logger, config, regions):
    logger.info(f"Starting retrieving information for Exadata Cloud Service Infrastructure")

    try:
        if infra_type == "ALL":
            services = ["CS", "CC"]
        else:
            services = []
            services.append(infra_type)

        global_json = []

        # printing tenancy information
        identity_client = oci.identity.IdentityClient(config)

        try:
            get_tenancy_response = identity_client.get_tenancy(
                tenancy_id=config['tenancy'])
            tenancy_name = get_tenancy_response.data.name
        except Exception:
            tenancy_name = "NA"

        for service in services:
            logger.info(f"Searching for all the Exadata Infrastructure Resources, type {service}...")

            infra_type = service

            if infra_type == "CS":
                query_text_infra = "query cloudexadatainfrastructure resources"
            elif infra_type == "CC":
                query_text_infra = "query exadatainfrastructure resources"
            else:
                logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 4]")
                exit(4)



            for region in regions:

                # setting region for config
                config["region"] = region

                logger.info(f"Checking in region {region}...")

                resource_search_client = oci.resource_search.ResourceSearchClient(config)

                # specify in the search query the resources, testing done using cloud exainfra and vmclusters
                search_resources_response = resource_search_client.search_resources(
                    search_details=oci.resource_search.models.StructuredSearchDetails(
                        type="Structured",
                        query=query_text_infra),
                    limit=514,
                    tenant_id=config['tenancy']
                )

                json_search = json.loads(str(search_resources_response.data))

                db_client = oci.database.DatabaseClient(config)

                infras_json = []

                # looping throught all the infras, and search for the vmcs
                for search in json_search['items']:

                    infra_ocid = search['identifier']

                    logger.info(f"Retrieving details for Exadata Infrastructure with OCID: {infra_ocid}")

                    if infra_type == "CS":
                        infra_detail_response = db_client.get_cloud_exadata_infrastructure(
                            cloud_exadata_infrastructure_id=infra_ocid
                        )
                    elif infra_type == "CC":
                        infra_detail_response = db_client.get_exadata_infrastructure(
                            exadata_infrastructure_id=infra_ocid
                        )
                    else:
                        logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 5]")
                        exit(5)

                    j_infra = json.loads(str(infra_detail_response.data))

                    comp_id = j_infra["compartment_id"]

                    list_maintenance_runs_response = db_client.list_maintenance_runs(
                        compartment_id=comp_id,
                        target_resource_id=infra_ocid,
                        lifecycle_state="SCHEDULED"
                    )

                    QUA_SCHED = "NA"
                    QUA_SCHED_TG_DB = "NA"
                    QUA_SCHED_TG_ST = "NA"
                    QUA_SCHED_SCHED = "NA"
                    MON_SCHED = "NA"
                    MON_SCHED_TG_DB = "NA"
                    MON_SCHED_TG_ST = "NA"
                    MON_SCHED_SCHED = "NA"

                    for maint in list_maintenance_runs_response.data:
                        maint_j = json.loads(str(maint))
                        if maint_j["maintenance_subtype"] == "QUARTERLY":
                            QUA_SCHED = maint_j["maintenance_subtype"]
                            QUA_SCHED_TG_DB = maint_j["target_db_server_version"]
                            QUA_SCHED_TG_ST = maint_j["target_storage_server_version"]
                            QUA_SCHED_SCHED = maint_j["time_scheduled"]
                        elif maint_j["maintenance_subtype"] == "SECURITY_MONTHLY":
                            MON_SCHED = maint_j["maintenance_subtype"]
                            MON_SCHED_TG_DB = maint_j["target_db_server_version"]
                            MON_SCHED_TG_ST = maint_j["target_storage_server_version"]
                            MON_SCHED_SCHED = maint_j["time_scheduled"]

                    # build filter for specific infra
                    if infra_type == "CS":
                        query_text_vmcs = f'query cloudvmcluster resources where cloudExadataInfrastructureId="{infra_ocid}"'

                    elif infra_type == "CC":
                        query_text_vmcs = f'query vmcluster resources where ExadataInfrastructureId="{infra_ocid}"'
                    else:
                        logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 6]")
                        exit(6)

                    logger.info("Retrieving all the VM Cluster for the parent infrastructure")

                    search_resources_response = resource_search_client.search_resources(
                        search_details=oci.resource_search.models.StructuredSearchDetails(
                            type="Structured",
                            query=query_text_vmcs),
                        limit=514,
                        tenant_id=config['tenancy']
                    )

                    vmc_search_j = json.loads(str(search_resources_response.data))

                    if "exascale_config" in j_infra:
                        if j_infra["exascale_config"] is None:
                            exascale_alloc = 0
                            exascale_avail = 0
                        else:
                            exascale_alloc = round(j_infra["exascale_config"]["total_storage_in_gbs"] / 1024, 2)
                            exascale_avail = round(j_infra["exascale_config"]["available_storage_in_gbs"] / 1024, 2)
                    else:
                        exascale_alloc = 0
                        exascale_avail = 0

                    if infra_type == "CS":
                        free_cpu = round(j_infra['max_cpu_count'] - j_infra['cpu_count'], 2)
                        free_lst = round(j_infra['max_db_node_storage_in_gbs'] - j_infra['db_node_storage_size_in_gbs'], 2)
                        free_est = round(j_infra['max_data_storage_in_tbs'] - j_infra['data_storage_size_in_tbs'], 2) - exascale_alloc
                    elif infra_type == "CC":
                        free_cpu = round(j_infra['max_cpu_count'] - j_infra['cpus_enabled'], 2)
                        free_lst = round(j_infra['max_db_node_storage_in_g_bs'] - j_infra['db_node_storage_size_in_gbs'], 2)
                        free_est = round(j_infra['max_data_storage_in_t_bs'] - j_infra['data_storage_size_in_tbs'], 2) - exascale_alloc
                    else:
                        logger.error("Wrong Infra type, exiting. [Error 7]")
                        exit(7)

                    free_mem = round(j_infra['max_memory_in_gbs'] - j_infra['memory_size_in_gbs'], 2)

                    # looping for vmcs
                    vmcs_arr = []
                    n_node = 0
                    cpu_core_count = 0

                    for vmc in vmc_search_j['items']:

                        vmc_ocid = vmc['identifier']

                        logger.info(f"Retriving details for VM Cluster with OCID: {vmc_ocid}")

                        if infra_type == "CS":
                            vmc_detail_response = db_client.get_cloud_vm_cluster(
                                cloud_vm_cluster_id=vmc_ocid
                            )
                        elif infra_type == "CC":
                            vmc_detail_response = db_client.get_vm_cluster(
                                vm_cluster_id=vmc_ocid
                            )
                        else:
                            logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 8]")
                            exit(8)

                        # find the databases that are running in this vmcluster
                        query_dbs = f'query database resources where vmClusterId="{vmc_ocid}"'

                        search_resources_response = resource_search_client.search_resources(
                            search_details=oci.resource_search.models.StructuredSearchDetails(
                                type="Structured",
                                query=query_dbs),
                            limit=514,
                            tenant_id=config['tenancy']
                        )

                        dbs_search_j = json.loads(str(search_resources_response.data))

                        n_dbs_per_vmc = len(dbs_search_j['items'])

                        vmc_j = json.loads(str(vmc_detail_response.data))

                        if infra_type == "CS":
                            n_node = vmc_j["node_count"]
                            storage_size_in_tbs = round(vmc_j["storage_size_in_gbs"]/1024, 2)
                            cpu_core_count = vmc_j["cpu_core_count"]
                        elif infra_type == "CC":
                            n_node = len(vmc_j["db_servers"])
                            storage_size_in_tbs = vmc_j["data_storage_size_in_tbs"]
                            cpu_core_count = vmc_j["cpus_enabled"]
                        else:
                            logger.error("Wrong Infra type, exiting. [Error 9]")
                            exit(9)

                        if "storage_management_type" in vmc_j:
                            storage_management_type = vmc_j["storage_management_type"]

                            if vmc_j["storage_management_type"] == "EXASCALE":
                                # get info from adb
                                get_exascale_db_storage_vault_response = db_client.get_exascale_db_storage_vault(
                                    exascale_db_storage_vault_id=vmc_j["exascale_db_storage_vault_id"]
                                )
                                data_storage_size_in_tbs = round(get_exascale_db_storage_vault_response.data.high_capacity_database_storage.total_size_in_gbs/1024,2)
                            elif vmc_j["storage_management_type"] == "ASM":
                                data_storage_size_in_tbs = vmc_j["data_storage_size_in_tbs"]
                            else:
                                storage_management_type = "Error"
                                data_storage_size_in_tbs = vmc_j["data_storage_size_in_tbs"]
                        else:
                            storage_management_type = "Error"
                            data_storage_size_in_tbs = vmc_j["data_storage_size_in_tbs"]

                        vmcs_dict = {"display_name": vmc_j["display_name"],
                                     "vmc_ocid": vmc_j["id"],
                                     "node_count": n_node,
                                     "license_model": vmc_j["license_model"],
                                     "lifecycle_state": vmc_j["lifecycle_state"],
                                     "dbs_number": n_dbs_per_vmc,
                                     "cpu_core_count": cpu_core_count,
                                     "gi_version": vmc_j["gi_version"],
                                     "system_version": vmc_j["system_version"],
                                     "storage_size_in_tbs": storage_size_in_tbs,
                                     "storage_management_type": storage_management_type,
                                     "data_storage_size_in_tbs": data_storage_size_in_tbs,
                                     "db_node_storage_size_in_gbs": vmc_j["db_node_storage_size_in_gbs"],
                                     "is_local_backup_enabled": vmc_j["is_local_backup_enabled"],
                                     "is_sparse_diskgroup_enabled": vmc_j["is_sparse_diskgroup_enabled"],
                                     "memory_size_in_gbs": vmc_j["memory_size_in_gbs"]}

                        vmcs_arr.append(vmcs_dict)

                    if infra_type == "CS":
                        query_text_avmcs = "query cloudautonomousvmcluster resources where lifeCycleState != 'TERMINATED'"
                    elif infra_type == "CC":
                        query_text_avmcs = "query autonomousvmcluster resources where lifeCycleState != 'TERMINATED'"
                    else:
                        logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 10]")
                        exit(10)

                    search_resources_response = resource_search_client.search_resources(
                        search_details=oci.resource_search.models.StructuredSearchDetails(
                            type="Structured",
                            query=query_text_avmcs),
                        limit=514,
                        tenant_id=config['tenancy']
                    )

                    avmc_search_j = json.loads(str(search_resources_response.data))

                    avmcs_arr = []

                    for avmc in avmc_search_j['items']:

                        vmc_ocid = avmc['identifier']

                        logger.info(f"Retriving details for Autonomous VM Cluster with OCID: {vmc_ocid}")

                        if infra_type == "CS":
                            avmc_detail_response = db_client.get_cloud_autonomous_vm_cluster(
                                cloud_autonomous_vm_cluster_id=vmc_ocid
                            )
                        elif infra_type == "CC":
                            avmc_detail_response = db_client.get_autonomous_vm_cluster(
                                autonomous_vm_cluster_id=vmc_ocid
                            )
                        else:
                            logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 11]")
                            exit(11)

                        avmc_j = json.loads(str(avmc_detail_response.data))

                        same_infra = 0

                        if infra_type == "CS":
                            if avmc_j["cloud_exadata_infrastructure_id"] == infra_ocid:
                                same_infra=1
                        elif infra_type == "CC":
                            if avmc_j["exadata_infrastructure_id"] == infra_ocid:
                                same_infra = 1
                        else:
                            logger.error(f"Infrastructure Type [{infra_type}] not recognized. Exiting. [Error 12]")
                            exit(12)

                        if same_infra == 1:
                            avmcs_dict = {"display_name": avmc_j["display_name"],
                                          "avmc_ocid": avmc_j["id"],
                                          "node_count": n_node,
                                          "license_model": avmc_j["license_model"],
                                          "lifecycle_state": avmc_j["lifecycle_state"],
                                          "cpu_core_count": cpu_core_count,
                                          "data_storage_size_in_tbs": avmc_j["autonomous_data_storage_size_in_tbs"]
                                          }
                            avmcs_arr.append(avmcs_dict)

                    if infra_type == "CS":
                        cpu_count = j_infra['cpu_count']
                        max_db_node_storage_in_gbs = round(j_infra['max_db_node_storage_in_gbs'], 4)
                        max_data_storage_in_tbs = round(j_infra['max_data_storage_in_tbs'], 4)
                        activated_storage_count = j_infra['activated_storage_count']
                    elif infra_type == "CC":
                        cpu_count = j_infra['cpus_enabled']
                        max_db_node_storage_in_gbs = round(j_infra['max_db_node_storage_in_g_bs'], 4)
                        max_data_storage_in_tbs = round(j_infra['max_data_storage_in_t_bs'], 4)
                        activated_storage_count = j_infra['storage_count']
                    else:
                        logger.error("Wrong Infra type, exiting. [Error 13]")
                        exit(13)

                    infra_dict = {"tenancy_name": tenancy_name,
                                  "region": region,
                                  "display_name": j_infra['display_name'],
                                  "ocid": j_infra['id'],
                                  "infra_type": infra_type,
                                  "compute_model": j_infra['compute_model'],
                                  "lifecycle_state": j_infra['lifecycle_state'],
                                  "shape": j_infra['shape'],
                                  "exascale_alloc": exascale_alloc,
                                  "exascale_avail": exascale_avail,
                                  "compute_count": j_infra['compute_count'],
                                  "activated_storage_count": activated_storage_count,
                                  "db_server_version": j_infra['db_server_version'],
                                  "storage_server_version": j_infra['storage_server_version'],
                                  "quarterly_schedule": QUA_SCHED,
                                  "quarterly_schedule_tg_db": QUA_SCHED_TG_DB,
                                  "quarterly_schedule_tg_st": QUA_SCHED_TG_ST,
                                  "quarterly_schedule_sched": QUA_SCHED_SCHED,
                                  "monthly_schedule": MON_SCHED,
                                  "monthly_schedule_tg_db": MON_SCHED_TG_DB,
                                  "monthly_schedule_tg_st": MON_SCHED_TG_ST,
                                  "monthly_schedule_sched": MON_SCHED_SCHED,
                                  "max_cpu_count": j_infra['max_cpu_count'],
                                  "cpu_count": cpu_count,
                                  "free_cpu": free_cpu,
                                  "max_memory_in_gbs": j_infra['max_memory_in_gbs'],
                                  "memory_size_in_gbs": j_infra['memory_size_in_gbs'],
                                  "free_mem": free_mem,
                                  "max_db_node_storage_in_gbs": max_db_node_storage_in_gbs,
                                  "db_node_storage_size_in_gbs": round(j_infra['db_node_storage_size_in_gbs'], 2),
                                  "free_lst": free_lst,
                                  "max_data_storage_in_tbs": max_data_storage_in_tbs,
                                  "data_storage_size_in_tbs": round(j_infra['data_storage_size_in_tbs'], 2),
                                  "free_est": free_est,
                                  "vm_clusters": vmcs_arr,
                                  "avm_clusters": avmcs_arr
                                  }

                    infras_json.append(infra_dict)

                global_json.append(infras_json)
                temp_json = {"items": global_json}

        try:
            global JSON_FILE

            if len(temp_json) == 0:
                logger.warning(
                    f"No Infrastructure details retrieved for the {infra_type} Service. Please review the info provided.")
            else:
                f = open(JSON_FILE, "a+")
                f.write(json.dumps(temp_json))
                f.close()
                logger.info(f"{JSON_FILE} properly written")

            return json.dumps(global_json)

        except Exception as error_a:
            logger.error(f"Unable to open the Json File for writing the details. Exiting. [Error 14]")
            logger.debug(error_a)
            exit(14)
    except Exception as error_b:
        logger.error(f"Unable to retrieve the Exadata Infrastructure details. Exiting. [Error 15]")
        logger.debug(error_b)
        exit(15)



if __name__ == '__main__':
    # configuring environment for logging

    py_maj = sys.version_info[0]
    py_min = sys.version_info[1]

    if py_maj < 3:
        print("CRITICAL: Unsupported Python version, minimum Python3.7")
        exit(99)
    if py_min < 7:
        print("CRITICAL: Unsupported Python version, minimum Python3.7")
        exit(99)

    parser = argparse.ArgumentParser()
    parser.add_argument("--oconfigf", "-of", default="DEF_PATH", help="OCI Configuration File Path", required=False)
    parser.add_argument("--oproname", "-on", default="0", help="OCI Profile Name [profile_name, DEFAULT]", required=False)
    parser.add_argument("--custname", "-cn", default="CUST_EXAMPLE", help="Customer Name", required=False)
    parser.add_argument("--restype", "-rt", default="CS", choices=['CS', 'CC', 'ALL'], help="Exadata Cloud Service Type [CS, CC, ALL]", required=False)

    args = parser.parse_args()

    running_path = os.path.realpath(os.path.dirname(__file__))

    logger = env_config(running_path, args.custname)

    logger.info('ExaCC Black Belt - Infrastructure Usage Details Extractor')
    logger.info(f'Version {VERSION}')
    logger.info("Opening OCI Tenancy Config File...")

    profile_list = []
    config_file = ""

    try:
        if args.oproname == "0":
            proname = "DEFAULT"
        else:
            proname = args.oproname

        if args.oconfigf != "DEF_PATH":
            if os.path.exists(args.oconfigf):
                config_file = args.oconfigf
            else:
                logger.error(f"unable to open parse OCI Configuration file. Exiting. [Error 16]")
                exit(16)

        if len(config_file) > 0:
            config = oci.config.from_file(file_location=config_file, profile_name=proname)
        else:
            config = oci.config.from_file(profile_name=proname)

        key_in_dict = "regions"
        regions = []

        if key_in_dict in config:
            regions = config[key_in_dict].split(",")
        else:
            regions.append(config["region"])

        exadb_json_details = get_exadb_details(args.restype, logger, config, regions)

        logger.info("Data retrival completed successfully!")

    except Exception as error:
        logger.error("Something went wrong in parsing input parameters. Exiting. [Error 17]")
        logger.error(error)
        exit(17)
