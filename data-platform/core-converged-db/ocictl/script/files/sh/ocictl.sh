#!/bin/bash

usage () {
    printf "usage:\n"
    printf "ocictl.sh adb     list\n"
    printf "                  start   <service_name>\n"
    printf "                  stop    <service_name>\n"
    printf "                  clone   <source_name> <target_name> <admin_password>\n"
    printf "                  delete  <service_name>\n"  
    printf "                  wallet  <service_name> <password>\n"
    printf "          db      list\n"
    printf "                  start     <service-name>\n"
    printf "                  stop      <service-name>\n"
    printf "                  cpu-scale <service-name>  <#oCPU>\n"
    #printf "                  storage-scale <service-name> <#GB>\n"
    printf "                  listpdb   <service-name>\n"
    printf "                  createpdb <service-name> <pdb-name> <pdb-admin-password> <tde-wallet-password>\n"
    printf "                  deletepdb <service_name> <pdbname>\n"
    printf "                  clonepdb  <service_name> <source_pdb_name> <target_pdb_name> <pdb-admin-password> <tde-wallet-password>\n"
    printf "                  startpdb  <service_name> <pdb_name>\n"
    printf "                  stoppdb   <service_name> <pdb_name>\n"
    printf "          compute list\n"
    printf "                  start   <service_name>\n"
    printf "                  stop    <service_name>\n"
    printf "          os      bucket list\n"
    printf "                         create <bucket_name>\n"
    printf "          os             delete <bucket_name>\n"
    printf "          os      file   list <bucket_name>\n"
    printf "          os      file   put  <bucket_name> <file_name>\n"
    printf "          os      file   get  <bucket_name> <file_name>\n"
    printf "          group   list\n"
    printf "          group   start  <groupname>\n"
    printf "          group   stop   <groupname>\n"
}

start_instance() {
    INSTANCES=`oci compute instance list --compartment-id $OCI_CID --display-name "$1"`
    INST_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$INSTANCES" "id"`
    for id in $INST_IDS
    do
        oci compute instance action --instance-id ${id} --action start
    done
}

stop_instance() {
    INSTANCES=`oci compute instance list --compartment-id $OCI_CID --display-name "$1"`
    INST_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$INSTANCES" "id"`
    for id in $INST_IDS
    do
        oci compute instance action --instance-id ${id} --action stop
    done
}

list_compute_instances() {
    if [ $# -eq 0 ];
    then
        INSTANCES=`oci compute instance list -c $OCI_CID`
    else
        INSTANCES=`oci compute instance list -c $OCI_CID --display-name "$1"`
    fi
    INST_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$INSTANCES" "id"`
    for id in $INST_IDS
    do
        INSTANCE=`oci compute instance get --instance-id "$id"`
        INST_NAME=`python3 $OCICTL_HOME/python/get_value.py "$INSTANCE" "display-name"`
        IMAGE_ID=`python3 $OCICTL_HOME/python/get_value.py "$INSTANCE" "image-id"`
        IMAGE=`oci compute image get --image-id "$IMAGE_ID"`
        OS_NAME=`python3 $OCICTL_HOME/python/get_value.py "$IMAGE" "operating-system"`
        OS_VERSION=`python3 $OCICTL_HOME/python/get_value.py "$IMAGE" "operating-system-version"`
        INST_STATUS=`python3 $OCICTL_HOME/python/get_value.py "$INSTANCE" "lifecycle-state"`
        if [ "$INST_STATUS" != "TERMINATED" ];
        then
            INST_VNICS=`oci compute instance list-vnics --instance-id "$id"`
            INST_PUBLIC_IPS=`python3 $OCICTL_HOME/python/get_lov.py "$INST_VNICS" "public-ip"`
            printf "%s:%s %s:%s" "$INST_NAME" "$OS_NAME" "$OS_VERSION" "$INST_STATUS"
            for ip in $INST_PUBLIC_IPS
            do
                printf ":%s" $ip
            done
            printf "\n"
        fi
    done
}

start_db () {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    DB_SYSTEM=`oci db database get --database-id "$DB_ID"`
    DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`
    DB_NODE_LIST=`oci db node list --compartment-id $OCI_CID --db-system-id $DB_SYSTEM_ID`
    NODE_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$DB_NODE_LIST" "id"`
    for nid in $NODE_IDS
    do
        oci db node start --db-node-id "$nid"
    done
}

stop_db () {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    DB_SYSTEM=`oci db database get --database-id "$DB_ID"`
    DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`
    DB_NODE_LIST=`oci db node list --compartment-id $OCI_CID --db-system-id $DB_SYSTEM_ID`
    NODE_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$DB_NODE_LIST" "id"`
    for nid in $NODE_IDS
    do
        oci db node stop --db-node-id "$nid"
    done
}

scale_cpu() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`  
    DB_SYSTEM=`oci db database get --database-id "$DB_ID"`
    DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`
    oci db system update --db-system-id $DB_SYSTEM_ID --cpu-core-count $2 
}

scale_storage() {
	    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`                                            DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`                                                        DB_SYSTEM=`oci db database get --database-id "$DB_ID"`                                                                  DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`                                     oci db system update --db-system-id $DB_SYSTEM_ID --data-storage-size-in-gbs $2
}

list_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    oci db pluggable-database list --database-id "$DB_ID"|python3 $OCICTL_HOME/python/pdb_list.py
}

start_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    PDB_ID=`oci db pluggable-database list --database-id "$DB_ID"|python3 $OCICTL_HOME/python/pdb_list2.py "$2"|cut -d":" -f2`
    oci db pluggable-database start --pluggable-database-id "$PDB_ID"
}

stop_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    PDB_ID=`oci db pluggable-database list --database-id "$DB_ID"|python3 $OCICTL_HOME/python/pdb_list2.py "$2"|cut -d":" -f2`
    oci db pluggable-database stop --pluggable-database-id "$PDB_ID"
}

create_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    oci db pluggable-database create --container-database-id "$DB_ID" --pdb-name "$2" --pdb-admin-password "$3" --tde-wallet-password "$4"
}

clone_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"`
    PDB_ID=`oci db pluggable-database list --database-id "$DB_ID"|python3 $OCICTL_HOME/python/pdb_list2.py "$2"|cut -d":" -f2`
    oci db pluggable-database local-clone --pluggable-database-id "$PDB_ID" --cloned-pdb-name "$3" --pdb-admin-password "$4" --target-tde-wallet-password "$5"
}

delete_pdb() {
    DB_SYSTEM=`oci db database list --compartment-id $OCI_CID --display-name $1`
    DB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEM" "id"` 
    PDB_ID=`oci db pluggable-database list --database-id "$DB_ID"|python3 $OCICTL_HOME/python/pdb_list2.py "$2"|cut -d":" -f2`
    oci db pluggable-database delete --pluggable-database-id "$PDB_ID"
}

list_db_systems () {
    if [ $# -eq 0 ];
    then     
	   DB_SYSTEMS=`oci db database list --compartment-id $OCI_CID`
    else
       DB_SYSTEMS=`oci db database list --compartment-id $OCI_CID --display-name ${1}`
    fi
	DB_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$DB_SYSTEMS" "id"`
    for id in $DB_IDS
    do
        DB_SYSTEM=`oci db database get --database-id "$id"`
        DB_LIFECYCLE_STATE=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "lifecycle-state"`
        if [ "$DB_LIFECYCLE_STATE" != "TERMINATED" ];
        then        
            DB_NAME=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-name"`
            DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`
            DB_SYSTEM_2=`oci db system get --db-system-id "$DB_SYSTEM_ID"`
            DB_CPUS=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM_2" "cpu-core-count"`
            DB_GBS=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM_2" "data-storage-size-in-gbs"`
            DB_USED_GBS=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM_2" "data-storage-percentage"`
            DB_HOME_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-home-id"`
            DB_HOME=`oci db db-home get --db-home-id "$DB_HOME_ID"`
            DB_VERSION=`python3 $OCICTL_HOME/python/get_value.py "$DB_HOME" "db-version"`
            printf "db system:\n %s:%s\n" $DB_NAME $id
            printf " db version: %s\n" $DB_VERSION
            printf " #oCPUs: %s\n" $DB_CPUS
            printf " Storage (GB): %s\n" $DB_GBS
            printf "    used (%%) : %s\n" $DB_USED_GBS
            DB_SYSTEM_ID=`python3 $OCICTL_HOME/python/get_value.py "$DB_SYSTEM" "db-system-id"`
            DB_NODE_LIST=`oci db node list --compartment-id $OCI_CID --db-system-id $DB_SYSTEM_ID`
            NODE_IDS=`python3 $OCICTL_HOME/python/get_lov.py "$DB_NODE_LIST" "id"`
            printf "node(s):\n"
            for nid in $NODE_IDS
            do
                NODE=`oci db node get --db-node-id $nid`
                NODE_NAME=`python3 $OCICTL_HOME/python/get_value.py "$NODE" "hostname"`
                NODE_STATUS=`python3 $OCICTL_HOME/python/get_value.py "$NODE" "lifecycle-state"`
                VNIC_ID=`python3 $OCICTL_HOME/python/get_value.py "$NODE" "vnic-id"`
                VNIC=`oci network vnic get --vnic-id $VNIC_ID 2>/dev/null`
                PUBLIC_IP=`python3 $OCICTL_HOME/python/get_value.py "$VNIC" "public-ip" 2>/dev/null`
                PRIVATE_IP=`python3 $OCICTL_HOME/python/get_value.py "$VNIC" "private-ip" 2>/dev/null`
                printf " %s:%s:%s:%s\n" $NODE_NAME $NODE_STATUS $PUBLIC_IP $nid
            done
            printf "pluggable database(s):\n"
            oci db pluggable-database list --database-id $id|python3 $OCICTL_HOME/python/pdb_list.py
            printf "\n"
        fi
    done
}


list_adb_instances () {
    if [ $# -eq 0 ];
    then    
        oci db autonomous-database list --compartment-id $OCI_CID|python3 $OCICTL_HOME/python/resource_list.py
    else
        oci db autonomous-database list --compartment-id $OCI_CID --display-name ${1}|python3 $OCICTL_HOME/python/resource_list.py
    fi
}

start_adb_instance () {
    ADB_SYSTEM=`oci db autonomous-database list --compartment-id $OCI_CID --display-name $1`
    ADB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$ADB_SYSTEM" "id"`
    oci db autonomous-database start --autonomous-database-id "$ADB_ID"
}

stop_adb_instance () {
    ADB_SYSTEM=`oci db autonomous-database list --compartment-id $OCI_CID --display-name $1`
    ADB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$ADB_SYSTEM" "id"`
    oci db autonomous-database stop --autonomous-database-id "$ADB_ID"
}

clone_adb_instance() {
    ADB_SYSTEM=`oci db autonomous-database list --compartment-id $OCI_CID --display-name $1`
    ADB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$ADB_SYSTEM" "id"`
    oci db autonomous-database create-from-clone --compartment-id "$OCI_CID" --source-id "$ADB_ID" --clone-type FULL --admin-password "$3" --db-name "$2" --display-name "$2" --data-storage-size-in-tbs 1 --compute-model ECPU --compute-count 2
}

delete_adb_instance() {
    ADB_SYSTEM=`oci db autonomous-database list --compartment-id $OCI_CID --display-name $1`
    ADB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$ADB_SYSTEM" "id"`
    oci db autonomous-database delete --autonomous-database-id "$ADB_ID"
}

download_adb_wallet() {
    ADB_SYSTEM=`oci db autonomous-database list --compartment-id $OCI_CID --display-name $1`    
    ADB_ID=`python3 $OCICTL_HOME/python/get_lov.py "$ADB_SYSTEM" "id"`
    oci db autonomous-database generate-wallet --autonomous-database-id "$ADB_ID" --password "$2" --file $WALLETS_HOME/wallet_$1.zip
}

list_bucket () {
    BUCKETS=`oci os bucket list --compartment-id $OCI_CID`
    python3 $OCICTL_HOME/python/get_lov.py "$BUCKETS" "name"
}

create_bucket () {
    oci os bucket create --compartment-id "$OCI_CID" --name ${1}
}

delete_bucket () {
    oci os bucket delete --name ${1} --empty --force
}

list_files () {
    oci os object list --bucket-name ${1}|python3 $OCICTL_HOME/python/file_list.py "$FILES"
}

put_file () {
    oci os object put --bucket-name ${1} --file ${2} --force
}

get_file () {
    oci os object get --bucket-name ${1} --name ${2} --file ${2}
}

groupstart () {
    while read srv type; do
        case ${type} in
            "adb"     ) start_adb_instance ${srv}
                        ;;
            "db"      ) start_db ${srv}
                        ;;
            "compute" ) start_instance ${srv}
                        ;;
                   *  ) printf "Unknown type. Exiting.\n"
                        exit
                        ;;
        esac
    done < $OCICTL_CONFIG/$1.oci.grp
}

groupstop () {
    while read srv type; do
        case ${type} in
            "adb"     ) stop_adb_instance ${srv}
                        ;;
            "db"      ) stop_db ${srv}
                        ;;
            "compute" ) stop_instance ${srv}
                        ;;
                   *  ) printf "Unknown type. Exiting.\n"
                        exit
                        ;;
        esac
    done < $OCICTL_CONFIG/$1.oci.grp
}

groupstatus() {
    while read srv type; do
        case ${type} in
            "adb"     ) list_adb_instances ${srv}
                        ;;
            "db"      ) list_db_systems ${srv}
                        ;;
            "compute" ) list_compute_instances ${srv}
                        ;;
                   *  ) printf "Unknown type. Exiting.\n"
                        exit
                        ;;
        esac
    done < $OCICTL_CONFIG/$1.oci.grp
}

grouplist() {
    for file in $OCICTL_CONFIG/*.oci.grp;
    do
        printf "%s\n" `basename $file|cut -d'.' -f1`
        while read srv type; do
            printf " %s:%s\n" $srv $type
        done < $file
    done
}

SWD=`dirname $0`
if [ -z $OCI_TID ];
then
    . $SWD/env_ocictl.sh
fi

case ${1} in
    "group"   ) case ${2} in
                    "list"  ) if [ $# -ne 2 ];
                              then
                                usage
                                exit 0
                              fi
                              grouplist
                              ;;
                    "start" ) if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              groupstart ${3}
                              ;;
                    "stop"  ) if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              groupstop ${3}
                              ;;
                  "status"  ) if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              groupstatus ${3}
                              ;; 
                        *   ) usage
                              ;;
                esac
                ;;
    "adb"     ) case ${2} in
                    "start" ) if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              start_adb_instance ${3}
                              ;;
                    "stop"  ) if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              stop_adb_instance ${3}
                              ;;
                    "list"  ) if [ $# -ne 2 ];
                              then
                                usage
                                exit 0
                              fi
                              list_adb_instances
                              ;;
                    "clone" ) if [ $# -ne 5 ];
                              then
                                usage
                                exit 0
                              fi
                              clone_adb_instance $3 $4 $5
                              ;;
                    "delete") if [ $# -ne 3 ];
                              then
                                usage
                                exit 0
                              fi
                              delete_adb_instance ${3}
                              ;;  
                    "wallet") if [ $# -ne 4 ];
                              then
                                usage
                                exit 0
                              fi
                              download_adb_wallet ${3} ${4}
                              ;;                              
                     *      ) usage
                              ;;
                esac
                ;;
    "db"      ) case ${2} in
	            "list"    ) list_db_systems $3
		   		            ;; 
                            
                "cpu-scale" ) if [ $# -ne 4 ];
                                then
                                    usage
                                    exit 0
                                fi
                                scale_cpu $3 $4
                                ;;
                "storage-scale" ) if [ $# -ne 4 ];
                                then
                                    usage
                                    exit 0
                                fi
                                scale_storage $3 $4
                                ;;
                
	            "listpdb" ) if [ $# -ne 3 ];
                                then
                                    usage
                                    exit 0
                                fi
                                list_pdb $3
                                ;;
		    "createpdb" ) if [ $# -ne 6 ];
                                then
                                    usage
                                    exit 0
                                fi
                                create_pdb $3 $4 $5 $6
                                ;;
		    "clonepdb"  ) if [ $# -ne 7 ];
                                then
                                    usage
                                    exit 0
                                fi
                                clone_pdb $3 $4 $5 $6 $7 
                                ;;
            "startpdb"   ) if [ $# -ne 4 ];
                          then
                                usage
                                exit 0
                          fi
                          start_pdb $3 $4
                          ;;
            "stoppdb"   ) if [ $# -ne 4 ];
                          then
                                usage
                                exit 0
                          fi
                          stop_pdb $3 $4
                          ;;                          
		    "deletepdb" ) if [ $# -ne 4 ];
                                then
                                    usage
                                    exit 0
                                fi
                                delete_pdb $3 $4
				;;
                    "start"     ) if [ $# -ne 3 ];
                                  then
                                      usage
                                      exit 0
                                  fi
                                  start_db $3
                                  ;;
                    "stop"      ) if [ $# -ne 3 ];
                                  then
                                      usage
                                      exit 0
                                  fi
                                  stop_db $3
                                  ;;                                
			      * ) usage
                                  ;;
	esac ;;
    "compute" ) case ${2} in
                    "start"   ) if [ $# -ne 3 ];
                                then
                                  usage
                                  exit 0
                                fi
                                start_instance ${3}
                                ;;
                    "stop"    ) if [ $# -ne 3 ];
                                then
                                  usage
                                  exit 0
                                fi
                                stop_instance ${3}
                                ;;
                    "list"    ) if [ $# -ne 2 ];
                                then
                                  usage
                                  exit 0
                                fi
                                list_compute_instances
                                ;;
                     *        ) usage
                                ;;
                esac
                ;;
    "os"      ) case ${2} in 
                    "bucket"  ) case ${3} in
                                    "list"     ) list_bucket
                                                 ;;
                                    "create"   ) if [ $# -ne 4 ];
                                                 then
                                                    usage
                                                    exit 0
                                                 fi
                                                 create_bucket ${4}
                                                 ;;
                                    "delete"   ) if [ $# -ne 4 ];
                                                 then
                                                    usage
                                                    exit 0
                                                 fi
                                                 delete_bucket ${4}
                                                 ;;
                                    *          ) usage
                                                 ;;
                                esac
                                ;;
                    "file"    ) case ${3} in
                                    "list"     ) if [ $# -ne 4 ];
                                                 then
                                                    usage
                                                    exit 0
                                                 fi
                                                 list_files ${4}
                                                 ;;
                                     "put"     ) if [ $# -ne 5 ];
                                                 then
                                                    usage
                                                    exit 0
                                                 fi
                                                 put_file ${4} ${5}
                                                 ;;
                                     "get"     ) if [ $# -ne 5 ];
                                                 then
                                                    usage
                                                    exit 0
                                                 fi
                                                 get_file ${4} ${5}
                                                 ;;
                                        *      ) usage
                                                 ;;
                                esac
                                ;;
                    *         ) usage
                                ;;
                esac
                ;;              
     *        ) usage
                ;;
esac
