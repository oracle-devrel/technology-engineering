# coding: utf-8

import oci

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# OCI find resources class
# - - - - - - - - - - - - - - - - - - - - - - - - - -

class ResourcesFinder:

    def __init__(self, compartment_id, custom_retry_strategy):
        self.compartment_id = compartment_id
        self.custom_retry_strategy = custom_retry_strategy

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active instances
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_instances(self, core_client):

        desired_states=['RUNNING', 'STOPPED']
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        core_client.list_instances, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # get boot volume for each instance
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_instances_bootvol(self, core_client, availability_domain, instance_id):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        core_client.list_boot_volume_attachments,
                                                        availability_domain=availability_domain, 
                                                        compartment_id=self.compartment_id, 
                                                        instance_id=instance_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all boot volume backups
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_boot_volume_backups(self, blk_storage_client, boot_volume_id):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        blk_storage_client.list_boot_volume_backups, 
                                                        compartment_id=self.compartment_id, 
                                                        boot_volume_id=boot_volume_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data
        
        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all block volume attachement for each instance
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_instances_volattach(self, core_client, availability_domain, instance_id):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        core_client.list_volume_attachments,
                                                        availability_domain=availability_domain, 
                                                        compartment_id=self.compartment_id, 
                                                        instance_id=instance_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all block volume backups
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_volume_backups(self, blk_storage_client, volume_id):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        blk_storage_client.list_volume_backups,
                                                        compartment_id=self.compartment_id, volume_id=volume_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data
                
        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active buckets
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_buckets(self, object_client,namespace_name):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        object_client.list_buckets, 
                                                        namespace_name=namespace_name, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)
        
        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active fss
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_fss(self, fss_client, ad):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        fss_client.list_file_systems, 
                                                        compartment_id=self.compartment_id, 
                                                        availability_domain=ad, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active load balancers
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_load_balancers(self, loadbalancer_client):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        loadbalancer_client.list_load_balancers, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active network load balancers
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_network_load_balancers(self, networkloadbalancer_client):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        networkloadbalancer_client.list_network_load_balancers, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active network firewalls
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_network_firewalls(self, networkfw_client):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        networkfw_client.list_network_firewalls, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active database systems
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_dbsystems(self, database_client):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_db_systems, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active db_homes in database systems
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_db_homes(self, database_client, db_system_id):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_db_homes, 
                                                        db_system_id=db_system_id, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active databases in systems databases db_home
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_databases(self, database_client, db_home_id):
        
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_databases, 
                                                        db_home_id=db_home_id, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active autonomous databases
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_autonomous_db(self, database_client):

        desired_states=['AVAILABLE','STOPPED']
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_autonomous_databases, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active mysql databases
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_mysql_db(self, mysql_client):

        desired_states=['ACTIVE','INACTIVE']
        resources=[]

        items=oci.pagination.list_call_get_all_results(
                                                        mysql_client.list_db_systems, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active nosql databases
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_nosql_db(self, nosql_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        nosql_client.list_tables, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active opensearch clusters
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_opensearch_clusters(self, opensearch_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        opensearch_client.list_opensearch_clusters, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active cloud Exadata infrastructure on dedicated Exadata
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_cloud_exadata_infrastructures(self, database_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_cloud_exadata_infrastructures, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active Autonomous Exadata VM clusters in the Oracle cloud
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_cloud_autonomous_vm_clusters(self, database_client, cloud_exadata_infrastructure_id):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_cloud_autonomous_vm_clusters, 
                                                        compartment_id=self.compartment_id, 
                                                        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active Exadata VM clusters in the Oracle cloud
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_cloud_vm_clusters(self, database_client, cloud_exadata_infrastructure_id):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        database_client.list_cloud_vm_clusters, 
                                                        compartment_id=self.compartment_id, 
                                                        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active analytics instances
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_analytics(self, analytics_client):

        desired_states=['ACTIVE', 'INACTIVE']
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        analytics_client.list_analytics_instances,
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active bigdata instances
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_bds(self, bds_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        bds_client.list_bds_instances, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active data catalogs
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_catalogs(self, data_catalog_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        data_catalog_client.list_catalogs, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active data integration workspaces
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_workspaces(self, data_integration_client):

        desired_states=['ACTIVE', 'STOPPED']
        resources=[]
        items=oci.pagination.list_call_get_all_results( 
                                                        data_integration_client.list_workspaces, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active function applications
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_functions_app(self, function_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        function_client.list_applications, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active functions
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_functions(self, function_client, function_app_id):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        function_client.list_functions, 
                                                        application_id=function_app_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active container instances
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_container_instances(self, container_client):

        desired_states=['ACTIVE', 'INACTIVE']
        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        container_client.list_container_instances, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active artifacts
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_repositories(self, artifact_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        artifact_client.list_repositories, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='AVAILABLE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active meshes
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_meshes(self, mesh_client):

        resources=[]
        items=oci.pagination.list_call_get_all_results(
                                                        mesh_client.list_meshes, 
                                                        compartment_id=self.compartment_id, 
                                                        lifecycle_state='ACTIVE', 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            resources.append(item)

        return resources

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # list all active visual builder instances
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def list_vb_instances(self, visual_builder_client):

        # vb instances must be running to update tags
        resources=[]
        desired_states=['ACTIVE', 'INACTIVE']

        items=oci.pagination.list_call_get_all_results(
                                                        visual_builder_client.list_vb_instances, 
                                                        compartment_id=self.compartment_id, 
                                                        retry_strategy=self.custom_retry_strategy
                                                        ).data

        for item in items:
            if (item.lifecycle_state in desired_states):
                resources.append(item)

        return resources