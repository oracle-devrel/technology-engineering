# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.


# Showcase manual block volume backup and restore

## Information
- [Mounting an Object Storage Bucket as File System on Oracle Linux](https://blogs.oracle.com/cloud-infrastructure/post/mounting-an-object-storage-bucket-as-file-system-on-oracle-linux)
- [OCI Compute - How to Install s3fs-fuse on Oracle Linux 8 (Doc ID 2938554.1)](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2938554.1)

## Prepare your environment
- set up your individual "operate" instance
	- An Oracle enterprise Linux server with Command Line Interface (*see [Set up your Server with Resilience by default using CLI](https://gitlab.com/hmielimo/cloud-resilience-by-default/#set-up-your-server-with-resilience-by-default-using-cli)  for details*)
	- create and attach block volume: e.g. backup-test (*50GB*)
	- create a bucket e.g. backup-test

## Set needed variables (*please adjust variables to your needs before past into your terminal*)
~~~
DEVICEoPATH1=/dev/oracleoci/oraclevdc
DEVICEoPATH2=/dev/oracleoci/oraclevdc1
MYoSOURCE1=/dev/sdb
MYoSOURCE2=/dev/sdb1
DATAoDIR=/mnt/MyBlockVolume.backup-test
OBJECTDATAoDIR=/mnt/MyObjectStorage.backup-test
BUCKEToNAME=backup-test
MYoREGION=<region>
MYoNAMESPACE=<your_namespace>
MYoSECREToKEY=<your_secret_key>
MYoACCESSoKEY=<your_access_key>
~~~

## Format and mount block volume
~~~
sudo umount ${DATAoDIR}
sudo mkdir ${DATAoDIR}
sudo fdisk -l
sudo fdisk ${MYoSOURCE1}

 n   add a new partition
 p   primary (0 primary, 0 extended, 4 free)
 Partition number (1-4, default 1):
 First sector (2048-419430399, default 2048):
 Last sector, +sectors or +size{K,M,G,T,P} (2048-419430399, default 419430399): +1G
 w   write table to disk and exit

sudo mkfs -t ext4 ${DEVICEoPATH2}
sudo mount ${DEVICEoPATH2} ${DATAoDIR}
sudo chown -R opc:opc ${DATAoDIR}
ls -lah ${DATAoDIR}
sudo mount | grep ${DATAoDIR}
lsblk
~~~

## Update fstab
~~~
sudo vi /etc/fstab
/dev/oracleoci/oraclevdc1  /mnt/MyBlockVolume.backup-test    ext4    defaults,_netdev,noatime  0  2
~~~

## Mounting an Object Storage Bucket as File System
~~~
# Generate Secret Key: <your_secret_key>

sudo yum update
sudo dnf upgrade
sudo dnf search epel

sudo dnf clean all
sudo dnf repolist all
sudo dnf install oracle-epel-release-el8

sudo tee /etc/yum.repos.d/ol8-epel.repo<<EOF
[ol8_developer_EPEL]
name= Oracle Linux \$releasever EPEL (\$basearch)
baseurl=https://yum.oracle.com/repo/OracleLinux/OL8/developer/EPEL/\$basearch/
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oracle
gpgcheck=1
enabled=1
EOF
sudo dnf makecache
sudo dnf repolist all

sudo yum install s3fs-fuse

echo ${MYoACCESSoKEY}:${MYoSECREToKEY} > ${HOME}/.passwd-s3fs
chmod 600 ${HOME}/.passwd-s3fs
cat ${HOME}/.passwd-s3fs
sudo rm -fr ${OBJECTDATAoDIR}
sudo mkdir ${OBJECTDATAoDIR}
sudo chown -R opc:opc ${OBJECTDATAoDIR}
sudo umount ${OBJECTDATAoDIR}
s3fs ${BUCKEToNAME} ${OBJECTDATAoDIR} -o endpoint=${MYoREGION} -o passwd_file=${HOME}/.passwd-s3fs -o url=https://${MYoNAMESPACE}.compat.objectstorage.${MYoREGION}.oraclecloud.com/ -o nomultipart -o use_path_request_style
ls -lah ${OBJECTDATAoDIR}
sudo mount | grep ${OBJECTDATAoDIR}
sudo mount | grep ${DATAoDIR}
~~~

## Create a Set of test data
~~~
touch ${DATAoDIR}/test.tmp
touch ${OBJECTDATAoDIR}/test.tmp

tee ${DATAoDIR}/test.txt<<EOF
This is a testfile located in a block volume.
EOF

tee ${OBJECTDATAoDIR}/test.txt<<EOF
This is a testfile located in object storage.
EOF

cat ${DATAoDIR}/test.txt
cat ${OBJECTDATAoDIR}/test.txt

ls -lah ${DATAoDIR}
ls -lah ${OBJECTDATAoDIR}
~~~

## Backup block volume (*here only a partition for testing purposes*)
~~~
sudo umount ${DATAoDIR}
sudo dd if=${MYoSOURCE} conv=sync,noerror bs=128M | gzip -c > ${OBJECTDATAoDIR}/my-disk.image.gz
ls -lah ${OBJECTDATAoDIR}/my-disk.image.gz
~~~

## Delete ${DATAoDIR}/test.txt
~~~
sudo mount ${DEVICEoPATH} ${DATAoDIR}
ls -lah ${DATAoDIR}
rm ${DATAoDIR}/test.txt
ls -lah ${DATAoDIR}
~~~

## Restore
~~~
sudo umount ${DATAoDIR}
gunzip -c ${OBJECTDATAoDIR}/my-disk.image.gz | sudo dd of=${MYoSOURCE}
~~~

## Test if restore was successful
~~~
sudo mount ${DEVICEoPATH} ${DATAoDIR}
ls -lah ${DATAoDIR}
~~~
