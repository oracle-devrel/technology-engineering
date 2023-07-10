# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Name: OCI-BackupInspector.py
# Task: Generate comprehensive CSV reports that assess 
#       compute backup status for boot and block volumes
#
# Author: Florian Bonneville
# Version: 1.0 - July 03th, 2023
#
# Disclaimer: 
# This script is an independent tool developed by 
# Florian Bonneville and is not affiliated with or 
# supported by Oracle. It is provided as-is and without 
# any warranty or official endorsement from Oracle
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import os
import oci
import argparse
import datetime
from datetime import datetime
from modules.identity import create_signer, get_region_subscription_list, check_compartment_state, get_compartment_name
from modules.oci import check_bucket, oci_search, list_instances_bootvol, list_instances_volattach, list_boot_volume_backups, get_volume_group, list_volume_group_backups, list_volume_backups, get_volume_group, list_volume_group_backups, upload_file
from modules.utils import clear, init_csv_report, green ,yellow, red, cyan, magenta, print_info, print_output, path_expander, check_folder, write_to_csv, calculate_backup_age, strfdelta

script_path = os.path.abspath(__file__)
script_name = (os.path.basename(script_path))[:-3]
analysis_start = datetime.now()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get command line arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-cs', action='store_true', default=False, dest='is_delegation_token',
                        help='Use CloudShell Delegation Token for authentication')
    parser.add_argument('-cf', action='store_true', default=False, dest='is_config_file',
                        help='Use local OCI config file for authentication')
    parser.add_argument('-cfp', default='~/.oci/config', dest='config_file_path',
                        help='Path to your OCI config file, default: ~/.oci/config')
    parser.add_argument('-cp', default='DEFAULT', dest='config_profile',
                        help='Config file section to use, default: DEFAULT')
    parser.add_argument('-c', default='', dest='report_comp',
                        help='Compartment OCID to store the bucket report, default: Root')
    parser.add_argument('-b', default='', dest='report_bucket',
                        help='Bucket name to store the report, default: reports_YOUR_TENANT_NAME')
    parser.add_argument('-rf', default='~/', dest='report_folder',
                        help='Local folder path to store the report, default: ~')
    parser.add_argument('-rn', default='compute_backups_', dest='report_name',
                        help='Name of the CSV report')
    parser.add_argument('-nocloud', action='store_true', default=False, dest='nocloud',
                        help='Do not move the report to OCI Storage')
    parser.add_argument('-tlc', default='', dest='target_comp',
                        help='Define the compartment name to analyze, default is your root compartment')
    parser.add_argument('-rg', default='', dest='target_region',
                        help='Define regions to analyze, default is all regions')

    return parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -

clear()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

cmd = parse_arguments()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print header
# - - - - - - - - - - - - - - - - - - - - - - - - - -

print(green(f"\n{'*'*94:94}"))
print_info(green, 'Analysis', 'started', script_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# oci authentication
# - - - - - - - - - - - - - - - - - - - - - - - - - -

config, signer, oci_tname=create_signer(cmd.config_file_path, 
                                        cmd.config_profile, 
                                        cmd.is_delegation_token, 
                                        cmd.is_config_file)

tenancy_id=config['tenancy']

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# init oci service clients
# - - - - - - - - - - - - - - - - - - - - - - - - - -

identity_client=oci.identity.IdentityClient(
                config=config, 
                signer=signer)

obj_storage_client=oci.object_storage.ObjectStorageClient(
                    config=config, 
                    signer=signer)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set target regions
# - - - - - - - - - - - - - - - - - - - - - - - - - -

analyzed_regions=get_region_subscription_list(
                                         identity_client, 
                                         tenancy_id, 
                                         cmd.target_region)

print_info(green, 'Region(s)', 'selected', len(analyzed_regions))

if cmd.target_region:
    print_info(green, 'Regions', 'analyzed', cmd.target_region)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set target compartments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

top_level_compartment_id = cmd.target_comp or tenancy_id
check_compartment_state(identity_client, top_level_compartment_id)
compartment_level = 'child' if cmd.target_comp else 'root'
compartment_name = get_compartment_name(identity_client, top_level_compartment_id)

print_info(green, 'Compartment', compartment_level, compartment_name[:33])

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set csv report folder
# - - - - - - - - - - - - - - - - - - - - - - - - - -

report_folder = path_expander(cmd.report_folder if cmd.report_folder else '~/')
check_folder(report_folder, output=True)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# init csv report file
# - - - - - - - - - - - - - - - - - - - - - - - - - -

now = datetime.today().strftime('%Y%m%d_%H%M')
default_report_name = 'compute_backups_'
report_name = f"{cmd.report_name}_" if cmd.report_name else None
report_name = f"{report_name or default_report_name}{now}.csv"
csv_report = os.path.join(report_folder, report_name)

print_info(green, 'Report', 'name', report_name[:33])
init_csv_report(csv_report)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check report compartment & bucket
# - - - - - - - - - - - - - - - - - - - - - - - - - -

if not cmd.nocloud:
    if not cmd.report_comp:
      cmd.report_comp = tenancy_id

    cmd.report_bucket = f'oci_reports_{oci_tname}' if not cmd.report_bucket else cmd.report_bucket
    csv_compartment_name = get_compartment_name(identity_client, cmd.report_comp)

    check_compartment_state(identity_client, cmd.report_comp)

    print_info(green, 'Compartment', 'report', csv_compartment_name[:33])

    check_bucket(
                 obj_storage_client, 
                 cmd.report_comp, 
                 cmd.report_bucket, 
                 tenancy_id)

print_info(green, 'Nocloud', 'value', str(cmd.nocloud))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print screen header
# - - - - - - - - - - - - - - - - - - - - - - - - - -

print(green(f"{'*'*94:94}\n"))

print(f"{'REGION':8} {'AD':7} {'COMPARTMENT':14} {'VOL_NAME':14}"
     f"{'VOL_TYPE':13} {'VG_NAME':13} {'VG_BKP':9} {'INSTANCE':14}"
     f"{'TYPE':7} {'DATE':13} {'AGE':8} {'SIZE_GBS':12}"
     f"{'SOURCE':12} {'STATE':12} {'NAME':14} {'EOL':12}\n")

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# start analysis
# - - - - - - - - - - - - - - - - - - - - - - - - - -

for region in analyzed_regions:

    # set regional config
    config['region'] = region.region_name
    core_client = oci.core.ComputeClient(config=config, signer=signer)
    blk_storage_client = oci.core.BlockstorageClient(config=config, signer=signer)

    # set search queries
    instance_query = "query instance resources where lifeCycleState = 'RUNNING' || lifeCycleState = 'STOPPED'"
    boot_query = "query bootvolume resources where lifeCycleState = 'AVAILABLE'"
    block_query = "query volume resources where lifeCycleState = 'AVAILABLE'"

    if cmd.target_comp:
        instance_query = f"query instance resources where (lifeCycleState = 'RUNNING' || lifeCycleState = 'STOPPED') && compartmentId = '{cmd.target_comp}'"
        boot_query = f"query bootvolume resources where lifeCycleState = 'AVAILABLE' && compartmentId = '{cmd.target_comp}'"
        block_query = f"query volume resources where lifeCycleState = 'AVAILABLE' && compartmentId = '{cmd.target_comp}'"

    # search resources
    print(f"   {region.region_name} : Collecting instances...",end=' '*30+'\r')
    all_instances = oci_search(config, signer, instance_query)
    
    print(f"   {region.region_name} : Collecting boot volumes...",end=' '*30+'\r')
    all_boot_vols = oci_search(config, signer, boot_query)
    
    print(f"   {region.region_name} : Collecting block volumes...",end=' '*30+'\r')
    all_block_vols = oci_search(config, signer, block_query)

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # 1- for each instance from search_response
    #    - retrieve attached boot/block volumes
    #    - store result in my_instances{}
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    # get all Instances in the region
    my_instances = {}
    for instance in all_instances.data:
        print(f"   {region.region_name} : Analyzing instance: {instance.display_name}",end=' '*30+'\r')

        # get instance boot volume
        instance_bootvol = list_instances_bootvol(
                                        config,
                                        signer, 
                                        instance.availability_domain, 
                                        instance.compartment_id, 
                                        instance.identifier)
        
        # get instance block volumes
        instance_blockvol = list_instances_volattach(
                                        config,
                                        signer, 
                                        instance.availability_domain, 
                                        instance.compartment_id, 
                                        instance.identifier)

        for attach in instance_bootvol:                    
            # Record instance name with boot volumes id
            my_instances[instance.display_name] = [attach.boot_volume_id]

        for attach in instance_blockvol:
            # Record instance name with block volumes id(s)
            my_instances[instance.display_name].append(attach.volume_id)

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # 2- for each boot volume from search_response
    #    - get boot volume details
    #    - get boot volume backups 
    #    - check if boot volume is attached to an instance 
    #    - check if boot volume is part of a volume group 
    #    - print/record result
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    # analyze all boot volumes in the region
    for boot_volume_data in all_boot_vols.data:
        
        backup_dates = {}
        is_volume_group_backup = ' - '

        resource_compartment = identity_client.get_compartment(boot_volume_data.compartment_id).data
        boot_volume = blk_storage_client.get_boot_volume(boot_volume_data.identifier).data

        available_boot_backups = list_boot_volume_backups(
                                config, 
                                signer,
                                boot_volume_data.compartment_id, 
                                boot_volume_data.identifier, 
                                lifecycle_state='AVAILABLE')
        
        # // for next release
        faulty_boot_backups = list_boot_volume_backups(
                                config, 
                                signer,
                                boot_volume_data.compartment_id, 
                                boot_volume_data.identifier, 
                                lifecycle_state='FAULTY')

        # check if volume is attached to an instance
        attached_instance_name = ' - '
        attached_instance_id = ' - '

        for instance_name, ids in my_instances.items():
            for id in ids:
                if boot_volume.id in id:
                    attached_instance_name = instance_name
                    attached_instance_id = instance.identifier
                    break

        # check if volume is part of a volume group
        volume_group_name = ' - '
        volume_group_id = ' - '
        volume_group_backups_ids = []

        if boot_volume.volume_group_id is not None:
            volume_group = get_volume_group(
                            config, 
                            signer, 
                            boot_volume.volume_group_id)
            
            volume_group_name = volume_group.display_name
            volume_group_id = volume_group.id
            
            volume_group_backups_ids = list_volume_group_backups(
                                    config,
                                    signer,
                                    resource_compartment.id,
                                    volume_group_id)
                
        # if backup found
        if available_boot_backups:

            # record backup per time created
            for backup in available_boot_backups:

                backup_dates[backup.time_created] = [backup]
                backup_expiration_time = str(backup.expiration_time) if backup.expiration_time else ' None '

            # find the most recent backup
            most_recent_backup_date = max(backup_dates.keys())
            most_recent_backup = backup_dates[most_recent_backup_date]

            # retrieve data from the most recent backup
            backup_display_name = most_recent_backup[0].display_name
            backup_id = most_recent_backup[0].id
            backup_lifecycle_state = most_recent_backup[0].lifecycle_state
            backup_type = most_recent_backup[0].type
            backup_source_type = most_recent_backup[0].source_type
            backup_unique_size_in_gbs = most_recent_backup[0].unique_size_in_gbs
            backup_time_created = most_recent_backup[0].time_created
            backup_age = calculate_backup_age(backup_time_created)
            
            # check if last backup comes from volume group
            is_volume_group_backup = 'True' if backup_id in volume_group_backups_ids else 'False'
            is_volume_group_backup = ' - ' if not volume_group_name else is_volume_group_backup

            output_data = {
                'color': yellow,
                'region': region.region_key,
                'region_ad': boot_volume_data.availability_domain,
                'compartment': resource_compartment.name,
                'obj_name': boot_volume_data.display_name, 
                'obj_type': boot_volume_data.resource_type, 
                'vg': volume_group_name, 
                'is_vg_bkp': is_volume_group_backup, 
                'instance': attached_instance_name, 
                'bkp_type': backup_type, 
                'bkp_created': backup_time_created,
                'bkp_age': backup_age,
                'bkp_size': backup_unique_size_in_gbs, 
                'bkp_source': backup_source_type, 
                'bkp_state': backup_lifecycle_state, 
                'bkp_name': backup_display_name,
                'bkp_eol': backup_expiration_time,
            }

            print_output(output_data)

            csv_data = {
                'region_name': region.region_name,
                'resource_ad': boot_volume_data.availability_domain,
                'compartment_name': resource_compartment.name,
                'compartment_id': resource_compartment.id,
                'resource_name': boot_volume_data.display_name,
                'resource_id': boot_volume_data.identifier,
                'resource_type': boot_volume_data.resource_type,
                'volume_group_name': volume_group_name,
                'volume_group_id': volume_group_id,
                'is_volume_group_backup': is_volume_group_backup,
                'attached_instance': attached_instance_name,
                'attached_instance_id': attached_instance_id,
                'backup_type': backup_type,
                'backup_time_created': backup_time_created,
                'backup_age': backup_age,
                'backup_unique_size_in_gbs': backup_unique_size_in_gbs,
                'backup_source_type': backup_source_type,
                'backup_lifecycle_state': backup_lifecycle_state,
                'backup_display_name': backup_display_name,
                'backup_expiration': backup_expiration_time,
                'backup_id': backup_id
            }

            write_to_csv(csv_report, csv_data)

        # else no backup or no 'AVAILABLE' backup
        else:
            output_data = {
                'color': red,
                'region': region.region_key,
                'region_ad': boot_volume_data.availability_domain,
                'compartment': resource_compartment.name,
                'obj_name': boot_volume_data.display_name, 
                'obj_type': boot_volume_data.resource_type, 
                'vg': volume_group_name, 
                'is_vg_bkp': is_volume_group_backup, 
                'instance': attached_instance_name, 
            }

            print_output(output_data)

            csv_data = {
                'region_name': region.region_name,
                'resource_ad': boot_volume_data.availability_domain,
                'compartment_name': resource_compartment.name,
                'compartment_id': resource_compartment.id,
                'resource_name': boot_volume_data.display_name,
                'resource_id': boot_volume_data.identifier,
                'resource_type': boot_volume_data.resource_type,
                'volume_group_name': volume_group_name,
                'volume_group_id': volume_group_id,
                'is_volume_group_backup': is_volume_group_backup,
                'attached_instance': attached_instance_name,
                'attached_instance_id': attached_instance_id,
            }

            write_to_csv(csv_report, csv_data)

    # analyze all block volumes in the region                    
    for volume_data in all_block_vols.data:

        backup_dates = {}
        is_volume_group_backup = ' - '

        resource_compartment = identity_client.get_compartment(volume_data.compartment_id).data
        block_volume = blk_storage_client.get_volume(volume_data.identifier).data

        available_block_backups = list_volume_backups(
                                    config,
                                    signer,
                                    volume_data.compartment_id,
                                    volume_data.identifier,
                                    lifecycle_state='AVAILABLE')

        # // for next release
        faulty_block_backups = list_volume_backups(
                                    config,
                                    signer,
                                    volume_data.compartment_id,
                                    volume_data.identifier,
                                    lifecycle_state='FAULTY')

        # check if volume is attached to an instance
        attached_instance_id = ' - '
        attached_instance_name = ' - '
        volume_group_backups_ids = []

        for instance_name, ids in my_instances.items():
            for id in ids:
                if block_volume.id in id:
                    attached_instance_name=instance_name
                    attached_instance_id=instance.identifier
                    break

        # check if volume is part of a volume group
        volume_group_id = ' - '
        volume_group_name = ' - '
        volume_group_backups_ids = []

        if block_volume.volume_group_id is not None:
            volume_group = get_volume_group(
                            config, 
                            signer, 
                            block_volume.volume_group_id)
            
            volume_group_id = volume_group.id
            volume_group_name = volume_group.display_name

            volume_group_backups_ids = list_volume_group_backups(
                                    config,
                                    signer,
                                    resource_compartment.id,
                                    volume_group_id)

        # if backup found:
        if available_block_backups:
            
            # record backup per time created
            for backup in available_block_backups:

                backup_dates[backup.time_created] = [backup]
                backup_expiration_time = str(backup.expiration_time) if backup.expiration_time else ' None '

            # find the most recent backup
            most_recent_backup_date = max(backup_dates.keys())
            most_recent_backup = backup_dates[most_recent_backup_date]

            # retrieve data from the most recent backup
            backup_display_name = most_recent_backup[0].display_name
            backup_id = most_recent_backup[0].id
            backup_lifecycle_state = most_recent_backup[0].lifecycle_state
            backup_type = most_recent_backup[0].type
            backup_source_type = most_recent_backup[0].source_type
            backup_unique_size_in_gbs = most_recent_backup[0].unique_size_in_gbs
            backup_time_created = most_recent_backup[0].time_created
            backup_age = calculate_backup_age(backup_time_created)

            # check if last backup comes from volume group
            is_volume_group_backup = 'True' if backup_id in volume_group_backups_ids else 'False'
            is_volume_group_backup = ' - ' if not volume_group_name else is_volume_group_backup

            output_data = {
                'color': cyan,
                'region': region.region_key,
                'region_ad': volume_data.availability_domain,
                'compartment': resource_compartment.name,
                'obj_name': volume_data.display_name, 
                'obj_type': volume_data.resource_type, 
                'vg': volume_group_name, 
                'is_vg_bkp': is_volume_group_backup, 
                'instance': attached_instance_name, 
                'bkp_type': backup_type, 
                'bkp_created': backup_time_created,
                'bkp_age': backup_age,
                'bkp_size': backup_unique_size_in_gbs, 
                'bkp_source': backup_source_type, 
                'bkp_state': backup_lifecycle_state, 
                'bkp_name': backup_display_name,
                'bkp_eol': backup_expiration_time,
            }

            print_output(output_data)

            csv_data = {
                'region_name': region.region_name,
                'resource_ad': volume_data.availability_domain,
                'compartment_name': resource_compartment.name,
                'compartment_id': resource_compartment.id,
                'resource_name': volume_data.display_name,
                'resource_id': volume_data.identifier,
                'resource_type': volume_data.resource_type,
                'volume_group_name': volume_group_name,
                'volume_group_id': volume_group_id,
                'is_volume_group_backup': is_volume_group_backup,
                'attached_instance': attached_instance_name,
                'attached_instance_id': attached_instance_id,
                'backup_type': backup_type,
                'backup_time_created': backup_time_created,
                'backup_age': backup_age,
                'backup_unique_size_in_gbs': backup_unique_size_in_gbs,
                'backup_source_type': backup_source_type,
                'backup_lifecycle_state': backup_lifecycle_state,
                'backup_display_name': backup_display_name,
                'backup_expiration': backup_expiration_time,
                'backup_id': backup_id
            }

            write_to_csv(csv_report, csv_data)

        # else no backup or no 'AVAILABLE' backup
        else:

            output_data = {
                'color': magenta,
                'region': region.region_key,
                'region_ad': volume_data.availability_domain,
                'compartment': resource_compartment.name,
                'obj_name': volume_data.display_name, 
                'obj_type': volume_data.resource_type, 
                'vg': volume_group_name, 
                'is_vg_bkp': is_volume_group_backup, 
                'instance': attached_instance_name, 
            }

            print_output(output_data)

            csv_data = {
                'region_name': region.region_name,
                'resource_ad': volume_data.availability_domain,
                'compartment_name': resource_compartment.name,
                'compartment_id': resource_compartment.id,
                'resource_name': volume_data.display_name,
                'resource_id': volume_data.identifier,
                'resource_type': volume_data.resource_type,
                'volume_group_name': volume_group_name,
                'volume_group_id': volume_group_id,
                'is_volume_group_backup': is_volume_group_backup,
                'attached_instance': attached_instance_name,
                'attached_instance_id': attached_instance_id,
            }

            write_to_csv(csv_report, csv_data)


# - - - - - - - - - - - - - - - - - - - - - - - - - -
# upload csv report to oci 
# - - - - - - - - - - - - - - - - - - - - - - - - - -
if not cmd.nocloud:
    print(' ',end=' '*60+'\r\n')
    upload_file(
                obj_storage_client,
                cmd.report_bucket,
                csv_report,
                report_name,
                tenancy_id)
else:
    print(' ',end=' '*60+'\r\n')

analysis_end = datetime.now()
execution_time = analysis_end - analysis_start
print(f"Execution time: {strfdelta(execution_time)}\n")