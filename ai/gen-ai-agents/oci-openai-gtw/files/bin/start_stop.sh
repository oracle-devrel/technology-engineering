#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh terraform apply"
  exit 1
fi  
cd $PROJECT_DIR

ACTION=$1
. starter.sh env -silent

if [ "$ACTION" != "start" ] && [ "$ACTION" != "stop" ] && [ "$ACTION" != "list" ]; then
  error_exit "stop_start.sh ACTION unknown ($ACTION): stop / start / list"
fi  

function loop_resource() {
    RESOURCE_TYPE=$1
    for OCID in `cat $STATE_FILE | jq -r ".resources[] | select(.type==\"$RESOURCE_TYPE\" and .mode==\"managed\") | .instances[].attributes.id"`;
    do
        if [ "$ACTION" == "start" ] || [ "$ACTION" == "stop" ]; then
            title "$OCID"
            if [ "$RESOURCE_TYPE" == "oci_analytics_analytics_instance" ]; then
                oci analytics analytics-instance $ACTION --analytics-instance-id $OCID
            elif [ "$RESOURCE_TYPE" == "oci_core_instance" ]; then
                oci compute instance action --action $ACTION --instance-id $OCID
            elif [ "$RESOURCE_TYPE" == "oci_database_autonomous_database" ]; then
                oci db autonomous-database $ACTION --autonomous-database-id $OCID
            elif [ "$RESOURCE_TYPE" == "oci_database_db_system" ]; then
                COMPARTMENT_ID=`oci db system get --db-system-id $OCID | jq -r '.data["compartment-id"]'`
                NODES=$(oci db node list --all --compartment-id $COMPARTMENT_ID --db-system-id $OCID | jq -r '.data[].id')
                echo NODES=$NODES
                for NODE in $NODES
                do            
                    oci db node $ACTION --db-node-id $NODE
                done            
            elif [ "$RESOURCE_TYPE" == "oci_datascience_notebook_session" ]; then
                if [ "$ACTION" == "start" ]; then
                    oci data-science notebook-session activate --notebook-session-id $OCID
                else
                    oci data-science notebook-session deactivate --notebook-session-id $OCID
                fi
            elif [ "$RESOURCE_TYPE" == "oci_integration_integration_instance" ]; then
                oci integration integration-instance $ACTION --id $OCID
            elif [ "$RESOURCE_TYPE" == "oci_mysql_mysql_db_system" ]; then
                if [ "$ACTION" == "start" ]; then
                    oci mysql db-system $ACTION --db-system-id $OCID 
                else
                    oci mysql db-system $ACTION --db-system-id $OCID --shutdown-type innodb_fast_shutdown 
                fi
            elif [ "$RESOURCE_TYPE" == "oci_oda_oda_instance" ]; then
                oci oda instance $ACTION --oda-instance-id $OCID
            elif [ "$RESOURCE_TYPE" == "oci_containerengine_cluster" ]; then
                COMPARTMENT_ID=`oci ce cluster get --cluster-id $OCID | jq -r '.data["compartment-id"]'`
                echo "COMPARTMENT_ID=$COMPARTMENT_ID"
                POOLS=$( oci ce node-pool list --compartment-id $COMPARTMENT_ID --cluster-id $OCID | jq -r '.data[].id')
                echo POOLS=$POOLS
                for POOL in $POOLS
                do            
                    NODES=$(oci ce node-pool get --node-pool-id $POOL | jq -r '.data.nodes[].id')
                    echo NODES=$NODES
                    for NODE in $NODES
                    do      
                        oci compute instance action --action $ACTION --instance-id $NODE
                    done
                done                  
            fi
        else
            echo "Instance $OCID"
        fi
    done;
}

loop_resource oci_analytics_analytics_instance
loop_resource oci_core_instance
loop_resource oci_database_autonomous_database
loop_resource oci_database_db_system
loop_resource oci_datascience_notebook_session
loop_resource oci_integration_integration_instance
loop_resource oci_mysql_mysql_db_system
loop_resource oci_oda_oda_instance
loop_resource oci_containerengine_cluster

# loop_resource oci_objectstorage_bucket

