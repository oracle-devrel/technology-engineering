# coding: utf-8

import oci
from modules.utils import red

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Define custom retry strategy
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
# OCI tag resources class
# - - - - - - - - - - - - - - - - - - - - - - - - - -

class ResourcesTagger:
    def __init__(self, oci_client):
        self.oci_client = oci_client

    def tag_instance_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.core.models.UpdateInstanceDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_instance(
                                                       resource_id, 
                                                       details, 
                                                       retry_strategy=custom_retry_strategy)
        except Exception as e:
            print(red(e))
            response = ''

        return response

    def tag_bootvolume_resource(self, resource_id, defined_tags_dict):
        try:
            # remove tags before update, if any
            try:
                details = oci.core.models.UpdateBootVolumeDetails(defined_tags={})
                response = self.oci_client.update_boot_volume(
                                                                resource_id, 
                                                                details, 
                                                                retry_strategy=custom_retry_strategy)
            except Exception:
                pass

            details = oci.core.models.UpdateBootVolumeDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_boot_volume(
                                                            resource_id, 
                                                            details, 
                                                            retry_strategy=custom_retry_strategy)
        except Exception as e:
            print(red(e))
            response = ''

        return response

    def tag_volume_resource(self, resource_id, defined_tags_dict):
        try:
            # remove tags before update, if any
            try:
                details = oci.core.models.UpdateVolumeDetails(defined_tags={})
                response = self.oci_client.update_volume(
                                                    resource_id, 
                                                    details, 
                                                    retry_strategy=custom_retry_strategy
                                                    )
            except Exception:
                pass

            details = oci.core.models.UpdateVolumeDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_volume(
                                                resource_id, 
                                                details, 
                                                retry_strategy=custom_retry_strategy
                                                )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_boot_backup_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.core.models.UpdateBootVolumeBackupDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_boot_volume_backup(
                                                            resource_id, 
                                                            details, 
                                                            retry_strategy=custom_retry_strategy
                                                            )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_volume_backup_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.core.models.UpdateVolumeBackupDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_volume_backup(
                                                       resource_id, 
                                                       details, 
                                                       retry_strategy=custom_retry_strategy
                                                       )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_fss_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.file_storage.models.UpdateFileSystemDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_file_system(
                                                    resource_id, details, 
                                                    retry_strategy=custom_retry_strategy
                                                    )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_bucket_resource(self, resource_name, defined_tags_dict):
        namespace_name=self.oci_client.get_namespace().data

        try:
            details = oci.object_storage.models.UpdateBucketDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_bucket(
                                                namespace_name, 
                                                resource_name,
                                                details, 
                                                retry_strategy=custom_retry_strategy
                                                )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_lb_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.load_balancer.models.UpdateLoadBalancerDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_load_balancer(
                                                       details,
                                                       resource_id
                                                       )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_nlb_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.network_load_balancer.models.UpdateNetworkLoadBalancerDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_network_load_balancer(
                                                                    resource_id, 
                                                                    details, 
                                                                    retry_strategy=custom_retry_strategy
                                                                    )
            oci.wait_until(
                            self.oci_client, 
                            self.oci_client.get_network_load_balancer(resource_id), 
                            'lifecycle_state', 
                            'ACTIVE', 
                            max_wait_seconds=600
                            ).data
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_networkfw_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.network_firewall.models.UpdateNetworkFirewallDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_network_firewall(
                                                          resource_id, 
                                                          details, 
                                                          retry_strategy=custom_retry_strategy
                                                          )
        except Exception as e:
            print(red(e.message))
            response=''

        return response

    def tag_dbsystem_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateDbSystemDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_db_system(
                                                   resource_id, 
                                                   details, 
                                                   retry_strategy=custom_retry_strategy
                                                   )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_dbsys_db_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateDatabaseDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_database(
                                                  resource_id, 
                                                  details, 
                                                  retry_strategy=custom_retry_strategy
                                                  )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_autonomous_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateAutonomousDatabaseDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_autonomous_database(
                                                             resource_id, 
                                                             details, 
                                                             retry_strategy=custom_retry_strategy
                                                             )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_mysql_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.mysql.models.UpdateDbSystemDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_db_system(
                                                   resource_id, 
                                                   details, 
                                                   retry_strategy=custom_retry_strategy
                                                   )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_nosql_resource(self, resource_id, defined_tags_dict):
        try:
            # remove tags before update, if any
            try:
                details = oci.nosql.models.UpdateTableDetails(defined_tags={})
                response = self.oci_client.update_table(
                                                resource_id, 
                                                details, 
                                                retry_strategy=custom_retry_strategy
                                                )
            except Exception:
                pass
        
            details = oci.nosql.models.UpdateTableDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_table(
                                                resource_id, 
                                                details, 
                                                retry_strategy=custom_retry_strategy
                                                )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_opensearch_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.opensearch.models.UpdateOpensearchClusterDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_opensearch_cluster(
                                                            resource_id, 
                                                            details, 
                                                            retry_strategy=custom_retry_strategy
                                                            )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_exa_infra_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateCloudExadataInfrastructureDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_cloud_exadata_infrastructure(
                                                                      resource_id, 
                                                                      details, 
                                                                      retry_strategy=custom_retry_strategy
                                                                      )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_auto_vm_cluster_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateCloudAutonomousVmClusterDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_cloud_autonomous_vm_cluster(
                                                                     resource_id, 
                                                                     details, 
                                                                     retry_strategy=custom_retry_strategy
                                                                     )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_cloud_vm_cluster_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.database.models.UpdateCloudVmClusterDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_cloud_vm_cluster(
                                                          resource_id, 
                                                          details, 
                                                          retry_strategy=custom_retry_strategy
                                                          )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_analytics_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.analytics.models.UpdateAnalyticsInstanceDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_analytics_instance(
                                                            resource_id, 
                                                            details, 
                                                            retry_strategy=custom_retry_strategy
                                                            )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_bigdata_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.bds.models.UpdateBdsInstanceDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_bds_instance(
                                                      resource_id, 
                                                      details, 
                                                      retry_strategy=custom_retry_strategy
                                                      )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_data_catalog_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.data_catalog.models.UpdateCatalogDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_catalog(
                                                 resource_id, 
                                                 details, 
                                                 retry_strategy=custom_retry_strategy
                                                 )
        except Exception as e:
            print(red(e))
            response=''

        return response
       
    def tag_data_integration_resource(self, resource_name, resource_id, defined_tags_dict):

        # submit 2 attributes as a workaround, crashs if only one submitted (oci v2.105.0)
        # see https://github.com/oracle/oci-python-sdk/issues/546
        try:
            details = oci.data_integration.models.UpdateWorkspaceDetails(display_name=resource_name, defined_tags=defined_tags_dict)
            response = self.oci_client.update_workspace(
                                                   resource_id, 
                                                   details
                                                   )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_function_app_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.functions.models.UpdateApplicationDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_application(
                                                     resource_id, 
                                                     details, 
                                                     retry_strategy=custom_retry_strategy
                                                     )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_function_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.functions.models.UpdateFunctionDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_function(
                                                  resource_id, 
                                                  details, 
                                                  retry_strategy=custom_retry_strategy
                                                  )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_container_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.container_instances.models.UpdateContainerInstanceDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_container_instance(
                                                            resource_id, 
                                                            details, 
                                                            retry_strategy=custom_retry_strategy
                                                            )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_artifact_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.artifacts.models.UpdateRepositoryDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_repository(
                                                    resource_id, 
                                                    details, 
                                                    retry_strategy=custom_retry_strategy
                                                    )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_mesh_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.service_mesh.models.UpdateMeshDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_mesh(
                                               resource_id, 
                                               details, 
                                               retry_strategy=custom_retry_strategy
                                               )
        except Exception as e:
            print(red(e))
            response=''

        return response

    def tag_visual_builder_resource(self, resource_id, defined_tags_dict):
        try:
            details = oci.visual_builder.models.UpdateVbInstanceDetails(defined_tags=defined_tags_dict)
            response = self.oci_client.update_vb_instance(
                                                     resource_id, 
                                                     details, 
                                                     retry_strategy=custom_retry_strategy
                                                    )
        except Exception as e:
            print(red(e))
            response=''

        return response

