# Showcase 2: TRIM showcase

[Showcase 2: TRIM showcase](#showcase-trim)

Assets that contain a great opportunity to learn about Cloud Resilience or "Keep your systems running". This assets provide
- A theoretical overview
- An alignment of terms across several cloud provides like e.g. Oracle, Amazon, Google and Microsoft
- A hands on guidance on a real world example based on which you are able to gain insides for your individual cloud resilience implementation
- A list of Oracle Architectural Best Practices


Reviewed: 27.11.2023

# When to use this asset?

These assets should be used whenever you like to understand TRIM in Oracle Cloud Infrastructure (OCI) Storage Services.

# How to use this asset?

The information is generic in nature and not specified for a particular customer.


# Showcase TRIM

## Prepare your environment
- [Oracle Cloud Infrastructure CLI Command Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/index.html)
- Set up your individual "operate" instance
	- An Oracle enterprise Linux server with Command Line Interface (*see [How to create a new operate server](https://gitlab.com/hmielimo/next-generation-cloud/-/tree/main/doc/how.to.create.a.new.operate.server)  for details*).
	- Create and attach block volume: e.g. trim-test (*200GB*).

## Format and mount block volume
~~~
DEVICEoPATH=/dev/oracleoci/oraclevdb
DATAoDIR=/mnt/MyBlockVolume
sudo mkdir /mnt/MyBlockVolume
sudo mkfs -t ext4 ${DEVICEoPATH}
sudo mount ${DEVICEoPATH} ${DATAoDIR}
sudo chown -R opc:opc ${DATAoDIR}
ls -lah ${DATAoDIR}
sudo mount | grep ${DATAoDIR}
~~~

## Update fstab
~~~
sudo vi /etc/fstab
/dev/oracleoci/oraclevdb  /mnt/MyBlockVolume    ext4    defaults,_netdev,noatime  0  2
~~~

## TRIM OFF showcase


### Set needed variables (*please adjust variables to your needs before past into your terminal*)
~~~
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CUSTOMER SPECIFIC VALUES - please update appropriate
# ---------------------------------------------------------------------------------------------------------------------------------------------
export TENENCY_OCID=<your_tenency_ocid>
export USER_OCID=<your_user_ocid>
export COMPARTMENT_OCID=<your_compartment_ocid>
export CUST_REGION_SUBNET_OCID=<your_cust_region_subnet_ocid>
export CUST_REGION_REGION_IDENTIFIER=<your_cust_region_region_identifier>
export CUST_REGION_SERVER_NAME=<your_cust_region_server_name>
export AD=<your_ad_number>
export AD_PREFIX=<your_ad_prefix>
export CUST_REGION_AVAILABILITY_DOMAIN="${AD_PREFIX}:${CUST_REGION_REGION_IDENTIFIER}-AD-${AD}"
export PROFILE_CUST_REGION=CUST_REGION
export TRIM_TEST_OCID=<your_trim_test_ocid>
export TRIM_TEST_BACKUP_NAME=TrimTestBackup
export myLOGFILE=\tmp\trim.test.log
export myTEMPFILE=\tmp\.trim.test.tmp
export mySIZE=1048576
export myITERATIONS=13
~~~

### Preperation steps
~~~
DEVICEoPATH=/dev/oracleoci/oraclevdb
DATAoDIR=/mnt/MyBlockVolume
sudo mkdir /mnt/MyBlockVolume
sudo umount ${DATAoDIR}
sudo mkfs -t ext4 ${DEVICEoPATH}

sudo mount ${DEVICEoPATH} ${DATAoDIR}
sudo chown -R opc:opc ${DATAoDIR}
ls -lah ${DATAoDIR}
sudo mount | grep ${DATAoDIR}
df -h | grep ${DATAoDIR}
sudo fstrim --all
~~~

### This will run ~ 20 minutes
~~~
echo "Start Trim Test (trim NOT active)" > "${myLOGFILE}"
echo "============================================================================================" >> "${myLOGFILE}"
for i in $( seq 1 $myITERATIONS )
do

  if [ 1 -eq 1 ] ; then # show Size Information: Filesystem
    echo -n "Size Information: Filesystem..: " >> "${myLOGFILE}"
    df -h | grep /mnt/MyBlockVolume >> "${myLOGFILE}"
  fi

  if [ 1 -eq 1 ] ; then # take backup, show Size Information: Block Volume; delete backup
    oci --profile "${PROFILE_CUST_REGION}" bv backup create --volume-id "${TRIM_TEST_OCID}" --display-name "${TRIM_TEST_BACKUP_NAME}" --wait-for-state "AVAILABLE"

    oci --profile "${PROFILE_CUST_REGION}" bv backup list --compartment-id "${COMPARTMENT_OCID}" --display-name "${TRIM_TEST_BACKUP_NAME}" > "${myTEMPFILE}"
    for ii in $(cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(."display-name"=="TrimTestBackup")] | .[]."id" ')
    do
      TRIM_TEST_BACKUP_OCID=$ii
      TRIM_TEST_BACKUP_SIZE_IN_MB=$( cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(.'\"id\"'=='\"$ii\"')] | .[].'\"unique-size-in-mbs\"' ' )
    done
    echo "Size Information: Block Volume: Backup size in MB: ${TRIM_TEST_BACKUP_SIZE_IN_MB}" >> "${myLOGFILE}"

    echo "Action..........: Block Volume: delete backup" >> "${myLOGFILE}"
    oci --profile "${PROFILE_CUST_REGION}" bv backup delete --volume-backup-id "${TRIM_TEST_BACKUP_OCID}" --force --wait-for-state "TERMINATED"
  fi

  if [ 1 -eq 1 ] ; then # insert, update delete files
    echo "Action..........: Filesystem..: insert, update and delete" >> "${myLOGFILE}"
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file1.txt count=$mySIZE bs=1024
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file2.txt count=$mySIZE bs=1024
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file1.txt count=$mySIZE bs=1024
    rm -f /mnt/MyBlockVolume/iteration.$i.file1.txt
	#sudo fstrim --all
  fi  

done

cat "${myLOGFILE}"
~~~

## TRIM ON showcase

### Set needed variables (*please adjust variables to your needs before past into your terminal*).
~~~
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CUSTOMER SPECIFIC VALUES - Please update appropriate
# ---------------------------------------------------------------------------------------------------------------------------------------------
export TENENCY_OCID=<your_tenency_ocid>
export USER_OCID=<your_user_ocid>
export COMPARTMENT_OCID=<your_compartment_ocid>
export CUST_REGION_SUBNET_OCID=<your_cust_region_subnet_ocid>
export CUST_REGION_REGION_IDENTIFIER=<your_cust_region_region_identifier>
export CUST_REGION_SERVER_NAME=<your_cust_region_server_name>
export AD=<your_ad_number>
export AD_PREFIX=<your_ad_prefix>
export CUST_REGION_AVAILABILITY_DOMAIN="${AD_PREFIX}:${CUST_REGION_REGION_IDENTIFIER}-AD-${AD}"
export PROFILE_CUST_REGION=CUST_REGION
export TRIM_TEST_OCID=<your_trim_test_ocid>
export TRIM_TEST_BACKUP_NAME=TrimTestBackup
export myLOGFILE=\tmp\trim.test.log
export myTEMPFILE=\tmp\.trim.test.tmp
export mySIZE=1048576
export myITERATIONS=13
~~~

### Preperation steps
~~~
DEVICEoPATH=/dev/oracleoci/oraclevdb
DATAoDIR=/mnt/MyBlockVolume
sudo mkdir /mnt/MyBlockVolume
sudo umount ${DATAoDIR}
sudo mkfs -t ext4 ${DEVICEoPATH}

sudo mount ${DEVICEoPATH} ${DATAoDIR}
sudo chown -R opc:opc ${DATAoDIR}
ls -lah ${DATAoDIR}
sudo mount | grep ${DATAoDIR}
df -h | grep ${DATAoDIR}
sudo fstrim --all
~~~

### This will run ~ 30 minutes
~~~
echo "Start Trim Test (trim active)" > "${myLOGFILE}"
echo "============================================================================================" >> "${myLOGFILE}"
for i in $( seq 1 $myITERATIONS )
do

  if [ 1 -eq 1 ] ; then # show Size Information: Filesystem
    echo -n "Size Information: Filesystem..: " >> "${myLOGFILE}"
    df -h | grep /mnt/MyBlockVolume >> "${myLOGFILE}"
  fi

  if [ 1 -eq 1 ] ; then # take backup, show Size Information: Block Volume; delete backup
    oci --profile "${PROFILE_CUST_REGION}" bv backup create --volume-id "${TRIM_TEST_OCID}" --display-name "${TRIM_TEST_BACKUP_NAME}" --wait-for-state "AVAILABLE"

    oci --profile "${PROFILE_CUST_REGION}" bv backup list --compartment-id "${COMPARTMENT_OCID}" --display-name "${TRIM_TEST_BACKUP_NAME}" > "${myTEMPFILE}"
    for ii in $(cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(."display-name"=="TrimTestBackup")] | .[]."id" ')
    do
      TRIM_TEST_BACKUP_OCID=$ii
      TRIM_TEST_BACKUP_SIZE_IN_MB=$( cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(.'\"id\"'=='\"$ii\"')] | .[].'\"unique-size-in-mbs\"' ' )
    done
    echo "Size Information: Block Volume: Backup size in MB: ${TRIM_TEST_BACKUP_SIZE_IN_MB}" >> "${myLOGFILE}"

    echo "Action..........: Block Volume: delete backup" >> "${myLOGFILE}"
    oci --profile "${PROFILE_CUST_REGION}" bv backup delete --volume-backup-id "${TRIM_TEST_BACKUP_OCID}" --force --wait-for-state "TERMINATED"
  fi

  if [ 1 -eq 1 ] ; then # insert, update delete files
    echo "Action..........: Filesystem..: insert, update and delete" >> "${myLOGFILE}"
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file1.txt count=$mySIZE bs=1024
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file2.txt count=$mySIZE bs=1024
    dd if=/dev/zero of=/mnt/MyBlockVolume/iteration.$i.file1.txt count=$mySIZE bs=1024
    rm -f /mnt/MyBlockVolume/iteration.$i.file1.txt
	sudo fstrim --all
  fi  

done

cat "${myLOGFILE}"
~~~

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
