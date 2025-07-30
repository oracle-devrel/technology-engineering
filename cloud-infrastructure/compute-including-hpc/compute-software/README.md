# Compute Software

This page contains information and useful links regarding Compute services that are mostly related to OS and Licenses Management on top of OCI Compute. You can also find resources about BYOI, BYOH and Autoscaling.

<i>Review date: 18 JUN 2025</i>

# Table of Contents

1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)

# Team Publications
- [Youtube Video: Windows In-Place Migration on OCI](https://youtu.be/W6j79zRdcuE)
- [Youtube Video: Migrating OCI Compute Instances to a newer shape](https://youtu.be/mXr5sosWdvI?feature=shared)
- [Youtube Video: How to Deploy Self-Managed Nodes on OKE](https://www.youtube.com/watch?v=OroPnRN7arE)
- [Youtube Video: Optimising performance - Deploying Red Hat Workloads on Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=_18PgW4NN40)
- [Youtube Video: Create KVM Guest from Oracle Linux KVM Host for Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=IiSsC7EqZSE)
- [Youtube Video: Using oci-kvm Network and Storage Commands for Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=IiSsC7EqZSE)
- [Youtube Video: Add a disk to an existing KVM VM on Oracle Linux](https://www.youtube.com/watch?v=B3h_DWOMwrk&t=16s)
- [Youtube Video: Using a Network Bridge with KVM VMs on Oracle Linux](https://www.youtube.com/watch?v=CXBTBxFoSKI&t=120s)
- [Youtube Video: Manage OCI instances directly from VirtualBox 7](https://www.youtube.com/watch?v=uFEN4Di-WDE)

- [Olygo Github: OCI_Compute_Function_Reserved_Pip_Allocator](https://github.com/Olygo/OCI-FN_reserved_pip_allocator)
- [Olygo Github: OCI Compute Capacity Report using CloudShell](https://github.com/Olygo/OCI_ComputeCapacityReport)
- [Olygo Github: Learn how to troubleshoot Linux and Windows instances using OCI Console Connection](https://github.com/Olygo/OCI_Console-Connections)
- [Olygo Github: OCI function that forces IMDSv2 on compute instances](https://github.com/Olygo/OCI-FN_IMDS-Watcher)
- [Olygo Github: OCI Script to update IMDSv1 to v2 on compute instance](https://github.com/Olygo/OCI_IMDS-Watchdog)
- [Olygo Github: Step-by-step guide to converting and importing Windows Hyper-V VMs into OCI using VHDX and QCOW2 formats](https://github.com/Olygo/OCI_Windows-VHDX-Import)
- [Olygo Github: Upgrade an existing Windows instance using In-Place Migration](https://github.com/Olygo/OCI_Windows_In-Place_Migration)
- [Olygo Github: https://github.com/Olygo/OCI_Windows_KMS_Activation_Guide](https://github.com/Olygo/OCI_Windows_KMS_Activation_Guide)
- [Olygo Github: Configure a secondary Vnic and routing on OL/RHEL/CentOS/Alma/Rocky](https://github.com/Olygo/OCI_Multi_VNIC_Setup)
- [Olygo Github: Script to request the termination of the instance on which it is executed](https://github.com/Olygo/OCI_Self-Terminate)
- [Olygo Github: Script to install and mount OCI bucket as Filesystem using Fuse S3FS](https://github.com/Olygo/OCI_S3FS)
- [Olygo Github: OCI Function for Defined Tags](https://github.com/Olygo/OCI-FN_TagCompute_DT)
- [Olygo Github: OCI Function for Freeform Tagging](https://github.com/Olygo/OCI-FN_TagCompute_FF)
- [Olygo Github: OCI List Backups](https://github.com/Olygo/OCI-ShowBackups)
- [Olygo Github: OCI Freeform Tagging](https://github.com/Olygo/OCI-TagCompute)
- [Olygo Github: OCI BackupInspector](https://github.com/Olygo/OCI-BackupInspector)
- [Olygo Github: OCI DR with Reserved Public IPs](https://github.com/Olygo/OCI_DR-Reserved_PIP)
- [Olygo Github: OCI Object Storage Refresh Data Replication ](https://github.com/Olygo/OCI-OS_RefreshDataReplication)
- [Olygo Github: OCI Cloud-Init WinPwd Update](https://github.com/Olygo/CloudInit_WinPwd_Update)
- [Olygo Github: OCI PowerShell 7 Launch Instance](https://github.com/Olygo/OCI_Pwsh_Launch_Instance)

- [Dezma Github: Open MPI on OCI ARM Compute Shapes](https://github.com/dezma/OpenMPI-OCI-ARM)
- [Dezma Github: OSU Benchmarks on OCI ARM Compute Shapes](https://github.com/dezma/OCI-HPC-ARM-EXAMPLES/tree/main/OSU-Benchmarks)
- [Dezma Github: GROMACS on OCI ARM Compute Shapes](https://github.com/dezma/OCI-HPC-ARM-EXAMPLES/tree/main/GROMACS)
- [Dezma Github: CP2K on OCI ARM Compute Shapes](https://github.com/dezma/OCI-HPC-ARM-EXAMPLES/tree/main/CP2K)
- [Dezma Github: HPC on OCI Kubernetes Engine OKE](https://github.com/dezma/oci-hpc-oke)

- [Marius Github: Cluster software on Oracle Linux 9 using Corosync and Pacemaker - create failover IP](https://github.com/mariusscholtz/Oracle-Cloud-Infrastructure-resources/blob/main/cluster/readme.md)
- [Marius Github: Transfer data to and from OCI using sftp/scp/oci-cli/curl](https://github.com/mariusscholtz/Oracle-Cloud-Infrastructure-resources/blob/main/VM-shapes/data%20transfer%20to%20OCI%20v1.0.pdf)
- [Marius Github: Cockpit – Web console to manage Oracle Linux](https://github.com/mariusscholtz/Oracle-Cloud-Infrastructure-resources/tree/main/cockpit)
- [Marius Gitlab: Mount a boot volume from one compute instance (or VM) onto another compute instance in order to replace lost ssh keys](https://gitlab.com/ms76152/system-administration)

- [Sharath Github: Troubleshoot Windows VM console connection via SAC](https://github.com/skbkkl/sharkuma/blob/main/Oracle-Cloud-Infrastructure-resources/Oracle-OCI-Troubleshooting/Troubleshooting-OCI-Win-VM-Console-Connection.pdf)
- [Sharath Github: Set up a console connection to an OCI Windows instance](https://github.com/skbkkl/sharkuma/blob/main/Oracle-Cloud-Infrastructure-resources/Oracle-OCI-Troubleshooting/Windows-Instance-Console-Creation.pdf)
- [Sharath Github: Troubleshooting OCI Windows VM console Fatal network error](https://github.com/skbkkl/sharkuma/blob/main/Oracle-Cloud-Infrastructure-resources/Oracle-OCI-Troubleshooting/OCI-Win-Instance-Console-Connection-FATAL%20ERROR-Network-error.pdf)
  
# Useful Links

- [Managing Custom Images](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/managingcustomimages.htm)
- [Oracle Blog - OCI OS Management](https://blogs.oracle.com/cloud-infrastructure/post/os-management-with-oracle-cloud-infrastructure)
- [Oracle Blog - RHEL runs on OCI supported by Oracle and Red Hat](https://blogs.oracle.com/cloud-infrastructure/post/red-hat-enterprise-linux-supported-oci)
- [Oracle Blog - How to Reset a Forgotten Password for a Windows Instance](https://blogs.oracle.com/cloud-infrastructure/post/tutorial-how-to-reset-a-forgotten-password-for-a-windows-instance)
- [Migrate to the cloud as is](https://www.oracle.com/cloud/oci-migration-hub/)
- [Microsoft Licensing on OCI](https://docs.oracle.com/en-us/iaas/Content/Compute/References/microsoftlicensing.htm)
- [Updated Microsoft Licensing Terms for dedicated hosted cloud services](https://www.microsoft.com/en-us/licensing/news/updated-licensing-rights-for-dedicated-cloud)
- [Deploy Apache Tomcat on ARM-based Kubernetes cluster in Oracle Cloud Infrastructure](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=824&p210_wec=&session=15158640819235)
- [Changing the shape of a compute instance: X5 to X9, or VM.Standard2 series to Flexible instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resizinginstances.htm#Changing_the_Shape_of_an_Instance)
- [Demo - Use autoscaling to adjust compute resources](https://docs.oracle.com/en/learn/configure_auto_scaling/index.html#introduction)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

