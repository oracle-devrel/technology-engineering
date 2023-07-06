# coding: utf-8

import oci
import os
from modules.utils import green, yellow, print_error, print_info, check_file_size

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# OCI Search
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def oci_search(config, signer, query):

    try:
        search_client = oci.resource_search.ResourceSearchClient(config=config, signer=signer)
        matching_context_type = oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE
        
        search_resource_details = oci.resource_search.models.StructuredSearchDetails(
            query=query,
            type='Structured',
            matching_context_type=matching_context_type)

        all_resources = oci.pagination.list_call_get_all_results(
                        search_client.search_resources, 
                        search_resource_details)

    except oci.exceptions.ServiceError as response:
        print_error("Search error:", query, response.code, response.message)
        raise SystemExit(1)

    return all_resources

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check if bucket already exists
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def check_bucket(obj_storage_client, report_comp, report_bucket, tenancy_id):

    try:
        my_namespace = obj_storage_client.get_namespace(compartment_id=tenancy_id).data
        all_buckets = obj_storage_client.list_buckets(my_namespace,report_comp).data
        bucket_etag=''

        for bucket in all_buckets:
            if bucket.name == report_bucket:
                print_info(green, 'Bucket', 'found', bucket.name)
                bucket_etag=bucket.etag

        if len(bucket_etag) < 1:
            print_info(yellow, 'Bucket', 'creating', report_bucket)

            create_bucket_details = oci.object_storage.models.CreateBucketDetails(
                                                                                public_access_type = 'NoPublicAccess',
                                                                                storage_tier = 'Standard',
                                                                                versioning = 'Disabled',
                                                                                name = report_bucket,
                                                                                compartment_id = report_comp)
            
            # create bucket 
            obj_storage_client.create_bucket(my_namespace, create_bucket_details)                
            
            result_response = obj_storage_client.get_bucket(my_namespace, report_bucket)

            wait_until_bucket_available_response = oci.wait_until(
                                                                obj_storage_client,
                                                                result_response,
                                                                'etag',
                                                                result_response.data.etag)
            
            print_info(yellow, 'Bucket', 'created', wait_until_bucket_available_response.data.name)

    except oci.exceptions.ServiceError as response:
        print_error("Bucket error:", report_bucket, response.code, response.message)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get boot volume for each instance
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_instances_bootvol(config, signer, availability_domain, compartment_id, instance_id):

    try:
        core_client=oci.core.ComputeClient(config=config, signer=signer)
        boot_volumes = oci.pagination.list_call_get_all_results(
                    core_client.list_boot_volume_attachments,
                    availability_domain=availability_domain, 
                    compartment_id=compartment_id, 
                    instance_id=instance_id
                    ).data

    except oci.exceptions.ServiceError as response:
        print_error("list_instances_bootvol error:", compartment_id, instance_id, response.code, response.message)
    
    return boot_volumes

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# list all block volume attachement for each instance
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_instances_volattach(config, signer, availability_domain, compartment_id, instance_id):
    
    try:
        core_client=oci.core.ComputeClient(config=config, signer=signer)
        volattachs=oci.pagination.list_call_get_all_results(
                                                            core_client.list_volume_attachments,
                                                            availability_domain=availability_domain, 
                                                            compartment_id=compartment_id, 
                                                            instance_id=instance_id
                                                            ).data

    except oci.exceptions.ServiceError as response:
        print_error("list_instances_volattach error:", compartment_id, instance_id, response.code, response.message)
        
    return volattachs

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# list all boot volume backups
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_boot_volume_backups(config, signer, compartment_id, boot_volume_id, lifecycle_state):

    try:
        blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
        bootvol_backups=oci.pagination.list_call_get_all_results(
                        blk_storage_client.list_boot_volume_backups, 
                        compartment_id=compartment_id, 
                        boot_volume_id=boot_volume_id,
                        lifecycle_state=lifecycle_state,
                        ).data

    except oci.exceptions.ServiceError as response:
        print_error("list_boot_volume_backups error:", compartment_id, boot_volume_id, response.code, response.message)
   
    return bootvol_backups

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# list all block volume backups
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_volume_backups(config, signer, compartment_id, volume_id, lifecycle_state):

    try:
        blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
        blockvol_backups=oci.pagination.list_call_get_all_results(
                        blk_storage_client.list_volume_backups, 
                        compartment_id=compartment_id, 
                        volume_id=volume_id,
                        lifecycle_state=lifecycle_state
                        ).data

    except oci.exceptions.ServiceError as response:
        print_error("list_volume_backups error:", compartment_id, volume_id, response.code, response.message)
   
    return blockvol_backups

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get volume group
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_volume_group(config, signer, volume_group_id):

    try:
        blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
        volume_group = blk_storage_client.get_volume_group(
                    volume_group_id=volume_group_id).data

    except oci.exceptions.ServiceError as response:
        print_error("get_volume_group error:", volume_group_id, response.code, response.message)
   
    return volume_group

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# list volume group backups
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_volume_group_backups(config, signer, compartment_id, volume_group_id):

    try:
        blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
        volume_group_backups=oci.pagination.list_call_get_all_results(
                        blk_storage_client.list_volume_group_backups,
                        compartment_id=compartment_id,
                        volume_group_id=volume_group_id,
                        sort_by='TIMECREATED').data

        # store all volume group backup ids
        volume_group_backups_ids=[]

        for vg_backup in volume_group_backups:
            for item in vg_backup.volume_backup_ids:
                volume_group_backups_ids.append(item)

    except oci.exceptions.ServiceError as response:
        print_error("list_volume_group_backups error:", compartment_id, volume_group_id, response.code, response.message)

    return volume_group_backups_ids

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# move csv report to oci
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def upload_file(obj_storage_client, report_bucket, csv_report, report_name, tenancy_id):

    try:
        if check_file_size(csv_report):
            namespace = obj_storage_client.get_namespace(compartment_id=tenancy_id).data

            # upload report to oci
            with open(csv_report, 'rb') as in_file:
                upload_response = obj_storage_client.put_object(
                                                                namespace,
                                                                report_bucket,
                                                                report_name,
                                                                in_file)

            # list objects in bucket and check md5 of uploaded file
            object_list = obj_storage_client.list_objects(
                                                        namespace,
                                                        report_bucket, 
                                                        fields=['md5'])

            for item in object_list.data.objects:
                if item.md5 == upload_response.headers['opc-content-md5']:
                    print(' '*20)
                    print(green(f"{'*'*94:94}"))
                    print_info(green, 'Upload', 'success', item.name)
                    print_info(green, 'MD5 checksum', 'success', item.md5)
                    print(green(f"{'*'*94:94}\n\n"))

                    # remove local report
                    os.remove(csv_report)
                    break
        else:
            print_error("Report does not contain any data",
                        csv_report,
                         "Upload process has been aborted",
                         level='INFO')

    except Exception as e:
        print_error("upload_file error", e)
        raise SystemExit(1)