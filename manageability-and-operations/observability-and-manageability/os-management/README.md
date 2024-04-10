# Oracle OCI OS Management

## Abstract

The Oracle Cloud Infrastructure (OCI) [OS Management](https://docs.oracle.com/en-us/iaas/os-management/osms/osms-overview.htm#about-osms) Service allows users to control the process of updating and patching the operating system enviroments of OCI [compute instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Concepts/computeoverview.htm). 

By default, the latest packages and patches available at the time the update is initiated will be installed. Versions of installed packages and patches will differ between compute instances that originated from the same [platform image](https://docs.oracle.com/en-us/iaas/Content/Compute/References/images.htm), depending on the time and date updates have been installed. Every update contains the risk to break installed applications. Therefore a more controlled process for updating and patches is desirable. OS Management, through Software Sources, offers a mechanism to update many compute instances to the exact same versions of packages and patches, regardless of when the udpate happens. The list of installed packages and patches can be read from a compute instance which has been tested and is known to work. This list can be put on a software source. Managed Instances receive available packages and patches from software sources instead of the public repositories of the OS distribution.

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/c5Ovp7yoN53kgfrED5DFlavvt1XERxWfmID4qwKQqR1jL8BEmcJr-miBWFmfhtOt/n/frxfz3gch4zb/b/FileShare/o/OSManagement.zip)

## Managed Instances, Managed Instance Groups and Software Sources

**Managed Instances** are compute instances under control of OS Management.

**Managed Instance Groups** group instances for updates.

**Software Sources** are loaded with lists of packages and patches, including their versions. Software Sources are associated with Managed Instances, not with Managed Instance Groups. This allows to group Managed Instances of different types into the same Managed Instance Group. An update command can be send to the group which then updates each Managed Instance from its associated Software Source.

**Golden Instance** A golden instance is a compute instance which has been prepared to have the packages and patches installed which will later be installed on managed instances. In other words, tests are made on the golden instance to make sure the installed packages and patches do work with the applications run by managed instances. When a healthy state has been achieved on the golden instance, a software source can be loaded with the list of the golden instances packages and patches.

## Prerequisites
[Terraform](https://developer.hashicorp.com/terraform/downloads), Python<br>
The Oracle Cloud Command Line Interface [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) is not strictly necessary. If it is installed and configured, Terrafrom can pick up the connection details from the Default entry in the config file. If it is not installed a [provider block](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/terraformconfig.htm#terraformconfig_topic_Configuration_File_Requirements_Provider) needs to be added to the Terraform configuration.

## Resources created
### Resource created by Terraform
* Compute Instances - Managed Instances
* Compute Instances - Golden Instances
* Managed Instance Groups
* Managed Instance Management (association of Manged Instance to Managed Instance Group)
* Dynamic Group
* Policy
* Virtual Cloud Network
* private and public Subnet
* private and public Security Lists
* local bash script to query the lifecycle state of compute instances
* Python script to create a software source and associate it with the managed instances of a managed instance group
* Python script to update a managed instance group

### Resources created by script
* Software Sources - the Python script `update_software_source.py`, located in subdirectory `python`, is created by Terraform from a template. The script takes a `managed instance group` and a `golden instance` as parameters, creates a software source, updates it with the list of packages and patches from the golden instance and associates the managed instances of the managed instance group with the software source.

## Architecture
Four Managed Instance Groups are created to test two different versions of operating systems (Oracle Linux 8, Oracle Linux 9) and different types of updates (`Ksplice` and `All`):
| | KSplice Update | All Update |
| - | - | - |
| Oracle Linux 8 | OracleLinux8_ManagedInstanceGroup1 | OracleLinux8_ManagedInstanceGroup2|
| Oracle Linux 9 | OracleLinux9_ManagedInstanceGroup1 | OracleLinux9_ManagedInstanceGroup2|

In the current incarnation of this demo, instance names are a combination of a city and a number:
* `Tokyo` for `OracleLinux8_ManagedInstanceGroup1`
* `Toronto` for `OracleLinux8_ManagedInstanceGroup2`
* `NewYork` for `OracleLinux9_ManagedInstanceGroup1`
* `London` for `OracleLinux9_ManagedInstanceGroup2`

Software Sources are named by appending the suffix `_SoftwareSource` to the Managed Instance Group name:
* `OracleLinux8_ManagedInstanceGroup1_SoftwareSource`
* `OracleLinux8_ManagedInstanceGroup2_SoftwareSource`
* `OracleLinux9_ManagedInstanceGroup1_SoftwareSource`
* `OracleLinux9_ManagedInstanceGroup2_SoftwareSource`

## Directory Structure
#### Subdirectory html
* `index.html`
* `index2.html`

open in a web browser to show screen snapshots from the created environment
#### Subdirectory misc
* `OS Management.pdf` - a handwritten script to describe what OS Management does
* `OSManagement.drawio` - architecture diagramm
* `checkdns.bash` - can be ignored
* `instancestate.bash` **will be created by terraform apply** shows the lifecycle state of managed and golden instances
#### Subdirectory python and python/batch
* `python/update_software_source.py` Python script to update (destroy and create) a software source from a golden instance. **This file will be created by terraform apply**
* `python/update_instances.py` Python script to update the instances of a managed instance group
* `python/batch/update_software_sources.bash` updates (destroys and creates) 4 software sources for the 4 managed intance groups
* `python/batch/update_instances.bash` applies `Ksplice` and `All` updates to managed intance groups
#### Subdirectory terraform
* all Terraform resources and file templates to let Terraform create local scripts.

## How to proceed
### Switch to the subdirectory html
Open the files `index.html` and `index2.html` in your browser for some screen snapshots.

### Switch to subdirectory terraform
Create a file private.tfvars to provide variable values for Terraform. The file looks like this:
```terraform
target_region    = "eu-frankfurt-1"
tenancy_ocid     = "ocid1.tenancy.oc1..aaa<EXAMPLE Tenancy OCID>"
user_ocid        = "ocid1.user.oc1..aaa<EXAMPLE User OCID>"
fingerprint      = "<EXAMPLE Fingerprint>"
private_key_path = "<path to private PEM key file>"

target_compartment_id = "ocid1.compartment.oc1..aaa<EXAMPLE compartment OCID>"
ssh_public_key        = "<EXAMPLE public ssh key>"
ignore_defined_tags   = []
oci_profile_name      = "<Name of profile in oci cli config file>"
```

In the file `locals.tf` check `mservers` and `golden_instances`:
```terraform
# golden instances
  golden_instances = [
    {name = "OL8GoldenInstance1", os = "OracleLinux8", subnet = "public", state = var.gi_state},
    {name = "OL8GoldenInstance2", os = "OracleLinux8", subnet = "public", state = var.gi_state},
    {name = "OL9GoldenInstance1", os = "OracleLinux9", subnet = "public", state = var.gi_state},
    {name = "OL9GoldenInstance2", os = "OracleLinux9", subnet = "public", state = var.gi_state},
  ]

# description of managed instance groups and managed instances
mservers = [
    {group = "OracleLinux8_ManagedInstanceGroup1",  name = "Tokyo8",      os = "OracleLinux8", subnet = "public", state="RUNNING", count = 4},
    {group = "OracleLinux8_ManagedInstanceGroup2",  name = "Toronto8",    os = "OracleLinux8", subnet = "public", state="RUNNING", count = 3},
    {group = "OracleLinux9_ManagedInstanceGroup1",  name = "NewYork9",    os = "OracleLinux9", subnet = "public", state="RUNNING", count = 2},
    {group = "OracleLinux9_ManagedInstanceGroup2",  name = "London9",     os = "OracleLinux9", subnet = "public", state="RUNNING", count = 2},
    {group = "Windows_ManagedInstanceGroup",        name = "Windows2019", os = "Windows2019",  subnet = "public", state="RUNNING", count = 0},
  ]
```
Each line in `golden_instance` defines the name, operating system, subnet and lifecycle state of a Golden Instance.
Each line in `mservers` defines a Managed Instance Group and the Managed Instances to create in the group. The first line of this variable will result in a Managed Group called `OracleLinux8_ManagedInstanceGroup1` with 4 Managed Instances named `Tokyo-1`..`Tokyo-4` based on Oracle Linux 8.
For allowed values for `os` check `os_images` in `locals.tf`


Check the following parts in the file `terraform.tfvars`
```terraform
shape = "VM.Standard.E4.Flex"
```
The variable `shape` applies to Golden and Managed Instances.

```terraform
# state of the golden instances
gi_state = "RUNNING"
mi_state = "RUNNING"
```
The lifecycle state of Golden Instances is controlled by `gi_state`, the state of Managed Instances by `mi_state`


```terraform
# network
vcndef = {
  name     = "VCNPatchTrain"
  cidr     = ["10.0.0.0/16","192.168.0.0/16"]
  subnets = {
    private = { name = "private", cidr = "10.0.0.0/17",   private = true }
    public  = { name = "public",  cidr = "10.0.128.0/17", private = false }
  }
}
```
The names for the VCN, private and public subnet as well as CIDR ranges are specified in the variable `vcndef`.<br>

```terraform
defined_tags = {
    "ResourceControl.dns"    = "true"
    "ResourceControl.keepup" = "false"
  }
```
If OCI is configured to automatically add tags on resource creation, Terraform would remove them the next time `terraform apply` is executed. By specifying the tags in the variable `defined_tags` Terraform is instructed to ignore these tags.

Run Terraform e.g. `terraform apply -var-file private.tfvars`. Note Terraform uses a timer to wait 10 minutes after creation of the compute instances before converting them into managed instances. After the instances have been created it takes some time before the Management Agent is fully functional. If the Agent is not fully settled, the conversion to a managed instance will fail. It might still fail after the 30 minutes wait. Rerun the `terraform apply` command when that happens or peform the conversion to a managed instance for those which failed later from the console.

Log in to golden instances via ssh and install the latest updates `sudo dnf upgrade -y`. This will install packages which are newer than those on the managed instances.

### Switch to the subdirectory python/batch
Run the script `./update_software_sources.bash`. The script iterates through the managed instance groups. Per managed instances group, all instances are detached from their software source (if at all attached), the existing software source is deleted (if it exists), the list of packages is read from the corresponding golden instance for the managed instance group, a new software source is created and the packages list uploaded to it before the managed instances are associated with the software source.

### On the OCI Console
In this state the golden instances can be stopped, they are not needed. Go to Compute-->OS Management and have a view at the Managed Instance Groups, Managed Instances and Software Sources. Notice the list of packages available for update for the Managed Intances. Now you can update the Managed Instances one by one or per Managed Instance Group and select if all or only a selection of packages will be installed.