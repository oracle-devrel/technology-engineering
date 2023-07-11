# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# name: OCI-TagCompute.py
# task: tag resources using display_name 
#       of each resource in order to get 
#       cost per display_name
#
# Author: Florian Bonneville
# Version: 1.1 - July 06th, 2023
#
# Disclaimer: 
# This script is an independent tool developed by 
# Florian Bonneville and is not affiliated with or 
# supported by Oracle. It is provided as-is and without 
# any warranty or official endorsement from Oracle
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# oci search for all resources using this tag :
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# query all resources where
#                         definedTags.namespace == 'My_Namespace' 
#                      && definedTags.key == 'display_name'
#
# or
#
# query all resources where
#                         definedTags.namespace == 'My_Namespace' 
#                      && definedTags.key == 'display_name' 
#                      && definedTags.value == 'SERVICE_NAME'
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import os
import oci
import copy
import argparse
from datetime import datetime
from modules.identity import create_signer, check_compartment_state, get_region_subscription_list, get_compartment_name, get_compartment_list, check_tags, list_ads
from modules.resources import ResourcesFinder
from modules.tagging import ResourcesTagger
from modules.utils import green, yellow, red, magenta, cyan, clear, print_info, print_output, strfdelta

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
                        help='config file section to use, default: DEFAULT')
    parser.add_argument('-tlc', default='', dest='target_comp', 
                        help='compartment ocid to analyze, default is your root compartment')
    parser.add_argument('-exc', default='', dest='exclude_comp', 
                        help='compartment ocid to exclude, default is none')
    parser.add_argument('-rg', default='', dest='target_region', 
                        help='region to analyze, default: all regions')
    parser.add_argument('-tn', default='', dest='tag_namespace', 
                        help='name of the TagNamespace owning your TagKey',required=True)
    parser.add_argument('-tk', default='', dest='tag_key', 
                        help='name of the TagKey to apply',required=True)
    parser.add_argument('-c', action='store_true', default=False, dest='compute', 
                        help='Tag Compute resources')
    parser.add_argument('-s', action='store_true', default=False, dest='storage', 
                        help='Tag Object Storage resources')
    parser.add_argument('-n', action='store_true', default=False, dest='network', 
                        help='Tag Network resources')
    parser.add_argument('-d', action='store_true', default=False, dest='database', 
                        help='Tag Database resources')
    parser.add_argument('-a', action='store_true', default=False, dest='analytics', 
                        help='Tag Analytics resources')
    parser.add_argument('-dev', action='store_true', default=False, dest='development', 
                        help='Tag Development resources')
    parser.add_argument('-all', action='store_true', default=False, dest='all_services', 
                        help='Tag all supported resources')

    return parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -

clear()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

cmd = parse_arguments()

if cmd.all_services:
    cmd.compute = True
    cmd.storage = True
    cmd.network = True
    cmd.database = True
    cmd.analytics = True
    cmd.development = True

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

search_client=oci.resource_search.ResourceSearchClient(
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

print_info(green, 'Region(#)', 'selected', len(analyzed_regions))

if cmd.target_region:
    print_info(green, 'Region(s)', 'analyzed', cmd.target_region)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set target compartments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

top_level_compartment_id = cmd.target_comp or tenancy_id
check_compartment_state(identity_client, top_level_compartment_id)
compartment_name = get_compartment_name(identity_client, top_level_compartment_id)
print_info(green, 'Compartment', 'parent source', compartment_name[:33])

if cmd.exclude_comp:
    excluded_compartment_name = get_compartment_name(identity_client, cmd.exclude_comp)
    print_info(green, 'Compartment', 'excluded', excluded_compartment_name[:33])

my_compartments=get_compartment_list(identity_client, top_level_compartment_id, cmd.exclude_comp)
print_info(green, 'Compartment(#)', 'selected', len(my_compartments))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check TagNamespace and TagKey
# - - - - - - - - - - - - - - - - - - - - - - - - - -

check_tags(identity_client, search_client, cmd.tag_namespace, cmd.tag_key)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print header
# - - - - - - - - - - - - - - - - - - - - - - - - - -

print(green(f"{'*'*94:94}\n"))
print(f"{'REGION':20}{'AD':6}{'COMPARTMENT':20}{'RESOURCE_TYPE':20}{'RESOURCE_NAME':20}\n")

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set custom retry strategy
# - - - - - - - - - - - - - - - - - - - - - - - - - -

custom_retry_strategy = oci.retry.RetryStrategyBuilder(
                                                        max_attempts_check=True,
                                                        max_attempts=10,
                                                        total_elapsed_time_check=True,
                                                        total_elapsed_time_seconds=600,
                                                        retry_max_wait_between_calls_seconds=45,#Max Wait: 45sec between attempts
                                                        retry_base_sleep_time_seconds=2,
                                                        service_error_check=True,
                                                        service_error_retry_on_any_5xx=True,
                                                        service_error_retry_config={
                                                                                    400: ['QuotaExceeded', 'LimitExceeded'],
                                                                                    429: [],
                                                                                    404: ['NotAuthorizedOrNotFound']
                                                                                    },
                                                        backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
                                                        ).get_retry_strategy()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# start analysis
# - - - - - - - - - - - - - - - - - - - - - - - - - -

# Iterate over regions and compartments

for region in analyzed_regions:
    config['region']=region.region_name
    identity_client=oci.identity.IdentityClient(config=config, signer=signer)
    core_client=oci.core.ComputeClient(config=config, signer=signer)
    blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
    object_client=oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    fss_client=oci.file_storage.FileStorageClient(config=config, signer=signer)
    loadbalancer_client=oci.load_balancer.LoadBalancerClient(config=config, signer=signer)
    networkloadbalancer_client=oci.network_load_balancer.NetworkLoadBalancerClient(config=config, signer=signer)
    networkfw_client=oci.network_firewall.NetworkFirewallClient(config=config, signer=signer)
    database_client=oci.database.DatabaseClient(config=config, signer=signer)
    mysql_client=oci.mysql.DbSystemClient(config=config, signer=signer)
    nosql_client=oci.nosql.NosqlClient(config=config, signer=signer)
    opensearch_client=oci.opensearch.OpensearchClusterClient(config=config, signer=signer)
    analytics_client=oci.analytics.AnalyticsClient(config=config, signer=signer)
    bds_client=oci.bds.BdsClient(config=config, signer=signer)
    data_catalog_client=oci.data_catalog.DataCatalogClient(config=config, signer=signer)
    data_integration_client=oci.data_integration.DataIntegrationClient(config=config, signer=signer)
    function_client=oci.functions.FunctionsManagementClient(config=config, signer=signer)
    container_client=oci.container_instances.ContainerInstanceClient(config=config, signer=signer)
    artifact_client=oci.artifacts.ArtifactsClient(config=config, signer=signer)
    mesh_client=oci.service_mesh.ServiceMeshClient(config=config, signer=signer)
    visual_builder_client=oci.visual_builder.VbInstanceClient(config=config, signer=signer)

    all_ads=list_ads(identity_client, tenancy_id)
    tagging_status = '   {}: Tagging {}: {}'
    
    for compartment in my_compartments:
        
        finder = ResourcesFinder(compartment.id, custom_retry_strategy)
        
        print('   {}: Analyzing compartment: {}'.format(region.region_name, compartment.name[0:18]),end=' '*15+'\r',flush=True)

        if cmd.compute:
            #-----------------------------------------
            # get compute instances
            #-----------------------------------------
            all_instances=finder.list_instances(core_client)

            for instance in all_instances:
                service='instance'

                try:
                    print(tagging_status.format(service, region.region_name, instance.display_name[0:18]),end=' '*15+'\r',flush=True)

                    # 1- retrieve instance tags
                    defined_tags_dict = copy.deepcopy(instance.defined_tags)

                    # 2- add key/value to defined_tags_dict
                    # 2a- if tagnamespace already exists in defined_tags_dict:
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = instance.display_name

                    # 2b- else when tagnamespace doesn't exist in defined_tags_dict
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: instance.display_name}})
                    
                    tagger = ResourcesTagger(core_client)
                    tagger.tag_instance_resource(instance.id, defined_tags_dict)

                    output_data = {
                        'color': green,
                        'region': region.region_name,
                        'region_ad': instance.availability_domain,
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': instance.display_name
                        }
                    print_output(output_data)

                    #-----------------------------------------
                    # get attached boot volume
                    #-----------------------------------------
                    instance_bootvolattach=finder.list_instances_bootvol(core_client, instance.availability_domain, instance.id)

                    for bootvolattach in instance_bootvolattach:
                        service='bootvolume'
                        print(tagging_status.format(service, region.region_name, bootvolattach.display_name[0:18]),end=' '*15+'\r',flush=True)
                        
                        bootvol=blk_storage_client.get_boot_volume(bootvolattach.boot_volume_id).data

                        defined_tags_dict = copy.deepcopy(bootvol.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = instance.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: instance.display_name}})

                        tagger = ResourcesTagger(blk_storage_client)
                        tagger.tag_bootvolume_resource(bootvol.id, defined_tags_dict)

                        output_data = {
                            'color': green,
                            'region': region.region_name,
                            'region_ad': bootvol.availability_domain,
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': bootvol.display_name
                            }
                        print_output(output_data)
                        
                    #-----------------------------------------
                    # get boot volume backups
                    #-----------------------------------------
                    boot_volume_backups=finder.list_boot_volume_backups(blk_storage_client, bootvol.id)

                    for boot_volume_backup in boot_volume_backups:
                        service='boot_backup'
                        print(tagging_status.format(service, region.region_name, boot_volume_backup.display_name[0:18]),end=' '*15+'\r',flush=True)

                        bootvolbkp=blk_storage_client.get_boot_volume_backup(boot_volume_backup.id).data

                        defined_tags_dict = copy.deepcopy(boot_volume_backup.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = instance.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: instance.display_name}})

                        tagger = ResourcesTagger(blk_storage_client)
                        tagger.tag_boot_backup_resource(boot_volume_backup.id, defined_tags_dict)

                        output_data = {
                            'color': green,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': bootvolbkp.display_name
                            }
                        print_output(output_data)

                    #-----------------------------------------
                    # get attached block volumes
                    #-----------------------------------------
                    try:
                        instance_vol_attach=finder.list_instances_volattach(core_client, instance.availability_domain, instance.id)

                        for vol_attach in instance_vol_attach:
                            service='volume'
                            print(tagging_status.format(service, region.region_name, vol_attach.display_name[0:18]),end=' '*15+'\r',flush=True)

                            volume=blk_storage_client.get_volume(vol_attach.volume_id).data

                            defined_tags_dict = copy.deepcopy(volume.defined_tags)
                            try:
                                defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = instance.display_name
                            except Exception:
                                defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: instance.display_name}})

                            tagger = ResourcesTagger(blk_storage_client)
                            tagger.tag_volume_resource(volume.id, defined_tags_dict)

                            output_data = {
                                'color': green,
                                'region': region.region_name,
                                'region_ad': volume.availability_domain,
                                'compartment': compartment.name,
                                'service': service, 
                                'obj_name': volume.display_name
                                }
                            print_output(output_data)

                        #-----------------------------------------
                        # get block volume backups
                        #-----------------------------------------
                        volume_backups=finder.list_volume_backups(blk_storage_client, volume.id)

                        for volume_backup in volume_backups:
                            service='volume_backup'
                            print(tagging_status.format(service, region.region_name, volume_backup.display_name[0:18]),end=' '*15+'\r',flush=True)

                            volbkp=blk_storage_client.get_volume_backup(volume_backup.id).data

                            defined_tags_dict = copy.deepcopy(volume_backup.defined_tags)
                            try:
                                defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = instance.display_name
                            except Exception:
                                defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: instance.display_name}})

                            tagger = ResourcesTagger(blk_storage_client)
                            tagger.tag_volume_backup_resource(volume_backup.id, defined_tags_dict)

                            output_data = {
                                'color': green,
                                'region': region.region_name,
                                'region_ad': ' - ',
                                'compartment': compartment.name,
                                'service': service, 
                                'obj_name': volbkp.display_name
                                }
                            print_output(output_data)

                    except Exception:
                        pass # pass if no block volumes or backups found

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{instance.display_name}\n ocid:{instance.id}\n {e}\n'))
                    

        if cmd.storage:
            #-----------------------------------------
            # get buckets
            #-----------------------------------------
            namespace_name=object_client.get_namespace().data
            resources=finder.list_buckets(object_client, namespace_name)

            for resource in resources:
                service='bucket'

                try:
                    working_bucket=object_client.get_bucket(namespace_name,resource.name).data

                    print(tagging_status.format(service, region.region_name, working_bucket.name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(working_bucket.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.name}})

                    tagger = ResourcesTagger(object_client)
                    tagger.tag_bucket_resource(working_bucket.name, defined_tags_dict)

                    output_data = {
                        'color': yellow,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': working_bucket.name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{working_bucket.name}\n ocid:{working_bucket.id}\n {e}\n'))
                    
            
            #-----------------------------------------
            # get fss
            #-----------------------------------------

            for ad in all_ads:
                resources=finder.list_fss(fss_client, ad)

                for resource in resources:
                    service='fss'

                    try:
                        print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)
                        
                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})

                        tagger = ResourcesTagger(fss_client)
                        tagger.tag_fss_resource(resource.id, defined_tags_dict)

                        output_data = {
                            'color': yellow,
                            'region': region.region_name,
                            'region_ad': resource.availability_domain,
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': resource.display_name
                            }
                        print_output(output_data)

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        

        if cmd.network:
            #-----------------------------------------
            # get load balancers
            #-----------------------------------------
            resources=finder.list_load_balancers(loadbalancer_client)

            for resource in resources:
                service='loadbalancer'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(loadbalancer_client)
                    tagger.tag_lb_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': magenta,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get network load balancers
            #-----------------------------------------
            resources=finder.list_network_load_balancers(networkloadbalancer_client)

            for resource in resources:
                service='ntwloadbalancer'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(networkloadbalancer_client)
                    tagger.tag_nlb_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': magenta,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get network firewalls
            #-----------------------------------------
            resources=finder.list_network_firewalls(networkfw_client)

            for resource in resources:
                service='networkfw'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(networkfw_client)
                    tagger.tag_networkfw_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': magenta,
                        'region': region.region_name,
                        'region_ad': resource.availability_domain,
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

        if cmd.database:
            #-----------------------------------------
            # get database systems
            #-----------------------------------------
            resources=finder.list_dbsystems(database_client)

            for resource in resources:
                service='dbsystem'

                try:
                    try:
                        print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                        
                        tagger = ResourcesTagger(database_client)
                        tagger.tag_dbsystem_resource(resource.id, defined_tags_dict)

                        output_data = {
                            'color': cyan,
                            'region': region.region_name,
                            'region_ad': resource.availability_domain,
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': resource.display_name
                            }
                        print_output(output_data)

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))

                    #-----------------------------------------
                    # get db_homes in database systems
                    #-----------------------------------------
                    dbhomes=finder.list_db_homes(database_client, resource.id)

                    for dbhome in dbhomes:
                        service='dbhome'
                        
                        #-----------------------------------------
                        # get databases in db_homes
                        #-----------------------------------------
                        databases=finder.list_databases(database_client, dbhome.id)

                        for database in databases:
                            service='dbsys_db'

                            try:
                                print(tagging_status.format(service, region.region_name, database.db_name[0:18]),end=' '*15+'\r',flush=True)

                                defined_tags_dict = copy.deepcopy(database.defined_tags)
                                try:
                                    defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                                except Exception:
                                    defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})

                                tagger = ResourcesTagger(database_client)
                                tagger.tag_dbsys_db_resource(database.id, defined_tags_dict)

                                output_data = {
                                    'color': cyan,
                                    'region': region.region_name,
                                    'region_ad': ' - ',
                                    'compartment': compartment.name,
                                    'service': service, 
                                    'obj_name': database.db_name
                                    }
                                print_output(output_data)

                            except Exception as e:
                                print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{database.db_name}\n ocid:{database.id}\n {e}\n'))
                                

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    
                    
            #-----------------------------------------
            # get autonomous databases
            #-----------------------------------------
            resources=finder.list_autonomous_db(database_client)

            for resource in resources:
                service='autonomous'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(database_client)
                    tagger.tag_autonomous_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get cloud exadata infrastructures
            #-----------------------------------------
            resources=finder.list_cloud_exadata_infrastructures(database_client)

            for resource in resources:
                service='exa_infra'

                try:
                    try:
                        print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                        
                        tagger = ResourcesTagger(database_client)
                        tagger.tag_exa_infra_resource(resource.id, defined_tags_dict)

                        output_data = {
                            'color': cyan,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': resource.display_name
                            }
                        print_output(output_data)

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        

                    #-----------------------------------------
                    # get cloud_autonomous_vm_clusters
                    #-----------------------------------------
                    cloud_autonomous_vm_clusters=finder.list_cloud_autonomous_vm_clusters(database_client, resource.id)

                    for cloud_autonomous_vm_cluster in cloud_autonomous_vm_clusters:
                        service='auto_vm_cluster'

                        try:
                            print(tagging_status.format(service, region.region_name, cloud_autonomous_vm_cluster.display_name[0:18]),end=' '*15+'\r',flush=True)

                            defined_tags_dict = copy.deepcopy(cloud_autonomous_vm_cluster.defined_tags)
                            try:
                                defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = cloud_autonomous_vm_cluster.display_name
                            except Exception:
                                defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: cloud_autonomous_vm_cluster.display_name}})
                            
                            tagger = ResourcesTagger(database_client)
                            tagger.tag_auto_vm_cluster_resource(cloud_autonomous_vm_cluster.id, defined_tags_dict)

                            output_data = {
                                'color': cyan,
                                'region': region.region_name,
                                'region_ad': ' - ',
                                'compartment': compartment.name,
                                'service': service, 
                                'obj_name': cloud_autonomous_vm_cluster.display_name
                                }
                            print_output(output_data)

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_autonomous_vm_cluster.display_name}\n ocid:{cloud_autonomous_vm_cluster.id}\n {e}\n'))
                            

                    #-----------------------------------------
                    # get cloud_vm_clusters
                    #-----------------------------------------
                    cloud_vm_clusters=finder.list_cloud_vm_clusters(database_client, resource.id)

                    for cloud_vm_cluster in cloud_vm_clusters:
                        service='cloud_vm_cluster'

                        try:
                            print(tagging_status.format(service, region.region_name, cloud_vm_cluster.display_name[0:18]),end=' '*15+'\r',flush=True)

                            defined_tags_dict = copy.deepcopy(cloud_vm_cluster.defined_tags)
                            try:
                                defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = cloud_vm_cluster.display_name
                            except Exception:
                                defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: cloud_vm_cluster.display_name}})
                            
                            tagger = ResourcesTagger(database_client)
                            tagger.tag_cloud_vm_cluster_resource(cloud_vm_cluster.id, defined_tags_dict)

                            output_data = {
                                'color': cyan,
                                'region': region.region_name,
                                'region_ad': ' - ',
                                'compartment': compartment.name,
                                'service': service, 
                                'obj_name': cloud_vm_cluster.display_name
                                }
                            print_output(output_data)

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_vm_cluster.display_name}\n ocid:{cloud_vm_cluster.id}\n {e}\n'))
                            

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_vm_cluster.display_name}\n ocid:{cloud_vm_cluster.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get MySQL databases
            #-----------------------------------------
            resources=finder.list_mysql_db(mysql_client)

            # MySQL instances must be running to update tag
            # script starts inactive/untagged instances, apply tags and stops
            stop_after_tag = False

            for resource in resources:
                service='mysql'
                
                mysql_inst=mysql_client.get_db_system(resource.id).data

                try:
                    print(tagging_status.format(service, region.region_name, mysql_inst.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(mysql_inst.defined_tags)

                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = mysql_inst.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: mysql_inst.display_name}})

                    # if != means tag is missing
                    if defined_tags_dict != mysql_inst.defined_tags:
                            
                        if (mysql_inst.lifecycle_state == 'INACTIVE'):
                            stop_after_tag = True

                            print('   Starting MySQL: {}'.format(mysql_inst.display_name),end=' '*40 +'\r',flush=True)

                            mysql_client.start_db_system(
                                                        mysql_inst.id, 
                                                        retry_strategy=custom_retry_strategy
                                                        )
                            
                            oci.wait_until(
                                            mysql_client, 
                                            mysql_client.get_db_system(mysql_inst.id),
                                            'lifecycle_state', 
                                            'ACTIVE', 
                                            max_wait_seconds=600, 
                                            retry_strategy=custom_retry_strategy
                                            ).data

                        tagger = ResourcesTagger(mysql_client)
                        tagger.tag_cloud_vm_cluster_resource(mysql_inst.id, defined_tags_dict)

                        output_data = {
                            'color': cyan,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': mysql_inst.display_name
                            }
                        print_output(output_data)

                    # stop instance previously stopped
                    if stop_after_tag == True:
                            print('   Stopping MySQL: {}'.format(mysql_inst.display_name),end=' '*40 +'\r',flush=True)
                            stop_db_system_details=oci.mysql.models.StopDbSystemDetails(shutdown_type="SLOW")
                            mysql_client.stop_db_system(mysql_inst.id, stop_db_system_details, retry_strategy=custom_retry_strategy)
                            wait_response = oci.wait_until(mysql_client, mysql_client.get_db_system(mysql_inst.id), 'lifecycle_state', 'UPDATING', max_wait_seconds=600).data

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{mysql_inst.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get NoSQL databases
            #-----------------------------------------
            resources=finder.list_nosql_db(nosql_client)

            for resource in resources:
                service='nosql'
                
                try:
                    print(tagging_status.format(service, region.region_name, resource.name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.name}})
                    
                    tagger = ResourcesTagger(nosql_client)
                    tagger.tag_nosql_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get OpenSearch clusters
            #-----------------------------------------
            resources=finder.list_opensearch_clusters(opensearch_client)

            for resource in resources:
                service='opensearch'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(opensearch_client)
                    tagger.tag_opensearch_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

        if cmd.analytics:
            #-----------------------------------------
            # get analytics instances
            #-----------------------------------------
            resources=finder.list_analytics(analytics_client)

            for resource in resources:
                service='analytics'
                resource=analytics_client.get_analytics_instance(resource.id).data

                try:
                    print(tagging_status.format(service, region.region_name, resource.name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.name}})
                    
                    tagger = ResourcesTagger(analytics_client)
                    tagger.tag_analytics_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get big data instances
            #-----------------------------------------
            resources=finder.list_bds(bds_client)

            for resource in resources:
                service='bigdata'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(bds_client)
                    tagger.tag_bigdata_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get data catalogs
            #-----------------------------------------
            resources=finder.list_catalogs(data_catalog_client)

            for resource in resources:
                service='datacatalog'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})

                    tagger = ResourcesTagger(data_catalog_client)
                    tagger.tag_data_catalog_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get data integration catalogs
            #-----------------------------------------
            resources=finder.list_workspaces(data_integration_client)

            for resource in resources:
                service='dataintegration'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})

                    tagger = ResourcesTagger(data_integration_client)
                    # submit 2 attributes as a workaround, crashs if only one submitted (oci v2.105.0)
                    # see https://github.com/oracle/oci-python-sdk/issues/546
                    tagger.tag_data_integration_resource(resource.display_name, resource.id, defined_tags_dict)

                    output_data = {
                        'color': cyan,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

        if cmd.development:
            #-----------------------------------------
            # get function applications
            #-----------------------------------------
            resources=finder.list_functions_app(function_client)

            for resource in resources:
                service='function_app'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(function_client)
                    tagger.tag_function_app_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': red,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

                #-----------------------------------------
                # get function instances
                #-----------------------------------------
                fn_apps=finder.list_functions(function_client, resource.id)

                for fn_app in fn_apps:
                    service='function'

                    try:
                        print(tagging_status.format(service, region.region_name, fn_app.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(fn_app.defined_tags)
                        try:
                            defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                        except Exception:
                            defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                        
                        tagger = ResourcesTagger(function_client)
                        tagger.tag_function_resource(fn_app.id, defined_tags_dict)

                        output_data = {
                            'color': red,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': fn_app.display_name
                            }
                        print_output(output_data)

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{fn_app.display_name}\n ocid:{fn_app.id}\n {e}\n'))
                        

            #-----------------------------------------
            # get container instances
            #-----------------------------------------
            resources=finder.list_container_instances(container_client)

            for resource in resources:
                service='container'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(container_client)
                    tagger.tag_container_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': red,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get artifact repositories
            #-----------------------------------------
            resources=finder.list_repositories(artifact_client)

            for resource in resources:
                service='artifact'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(artifact_client)
                    tagger.tag_artifact_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': red,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get mesh instances
            #-----------------------------------------
            resources=finder.list_meshes(mesh_client)

            for resource in resources:
                service='mesh'

                try:
                    print(tagging_status.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(resource.defined_tags)
                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = resource.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: resource.display_name}})
                    
                    tagger = ResourcesTagger(mesh_client)
                    tagger.tag_mesh_resource(resource.id, defined_tags_dict)

                    output_data = {
                        'color': red,
                        'region': region.region_name,
                        'region_ad': ' - ',
                        'compartment': compartment.name,
                        'service': service, 
                        'obj_name': resource.display_name
                        }
                    print_output(output_data)

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                    

            #-----------------------------------------
            # get visual builder instances
            #-----------------------------------------
            resources=finder.list_vb_instances(visual_builder_client)

            # VB instances must be running to update tag
            # script starts inactive/untagged instances, apply tags and stops
            stop_after_tag = False

            for resource in resources:
                service='visual_builder'

                vb_inst=visual_builder_client.get_vb_instance(resource.id).data

                try:                
                    print(tagging_status.format(service, region.region_name, vb_inst.display_name[0:18]),end=' '*15+'\r',flush=True)

                    defined_tags_dict = copy.deepcopy(vb_inst.defined_tags)

                    try:
                        defined_tags_dict[cmd.tag_namespace][cmd.tag_key] = vb_inst.display_name
                    except Exception:
                        defined_tags_dict.update({cmd.tag_namespace: {cmd.tag_key: vb_inst.display_name}})

                    # if != means tag is missing
                    if defined_tags_dict != vb_inst.defined_tags:

                        if (vb_inst.lifecycle_state == 'INACTIVE'):
                            stop_after_tag = True

                            print('   Starting Visual Builder: {}'.format(vb_inst.display_name),end=' '*40 +'\r',flush=True)

                            visual_builder_client.start_vb_instance(
                                                                    vb_inst.id, 
                                                                    retry_strategy=custom_retry_strategy
                                                                    )

                            oci.wait_until(
                                            visual_builder_client, 
                                            visual_builder_client.get_vb_instance(vb_inst.id), 
                                            'lifecycle_state', 
                                            'ACTIVE', 
                                            max_wait_seconds=600, 
                                            retry_strategy=custom_retry_strategy
                                            ).data

                        tagger = ResourcesTagger(visual_builder_client)
                        tagger.tag_visual_builder_resource(vb_inst.id, defined_tags_dict)

                        oci.wait_until(
                                        visual_builder_client, 
                                        visual_builder_client.get_vb_instance(vb_inst.id), 
                                        'lifecycle_state', 'ACTIVE', 
                                        max_wait_seconds=600
                                        ).data
                        
                        output_data = {
                            'color': yellow,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': vb_inst.display_name
                            }
                        print_output(output_data)

                    else:                        
                        output_data = {
                            'color': magenta,
                            'region': region.region_name,
                            'region_ad': ' - ',
                            'compartment': compartment.name,
                            'service': service, 
                            'obj_name': vb_inst.display_name
                            }
                        print_output(output_data)

                    # stop instance previously stopped
                    if stop_after_tag == True:
                            print('   Stopping Visual Builder: {}'.format(vb_inst.display_name),end=' '*40 +'\r',flush=True)
                            visual_builder_client.stop_vb_instance(
                                                                   vb_inst.id, 
                                                                   retry_strategy=custom_retry_strategy
                                                                   )
                            oci.wait_until(
                                            visual_builder_client, 
                                            visual_builder_client.get_vb_instance(vb_inst.id), 
                                            'lifecycle_state', 
                                            'UPDATING', 
                                            max_wait_seconds=600
                                            ).data

                except Exception as e:
                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{vb_inst.display_name}\n ocid:{vb_inst.id}\n {e}\n'))
                    


print(' '*60)
analysis_end = datetime.now()
execution_time = analysis_end - analysis_start
print(f"Execution time: {strfdelta(execution_time)}\n")