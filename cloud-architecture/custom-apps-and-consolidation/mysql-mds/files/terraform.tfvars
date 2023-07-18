# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform variable definition file.
# @author: Vijay Kokatnur

# Identity and access parameters
home_region     = "eu-frankfurt-1"
region          = "eu-frankfurt-1"


# general oci parameters
compartment_id = "ocid1.compartment.oc1.."
label_prefix   = "none"

# ssh keys
ssh_private_key_path = "keys/id_rsa"
# ssh_public_key       = ""
# ssh_public_key_path  = "none"
ssh_public_key_path = "keys/id_rsa.pub"

#networking parameters
subnet_id     = "ocid1.subnet.oc1..."

create_subnet   = false
# If create_subnet = true - provide vcn_id, ig_route_id, newbits, netnum for subnet cidr 
# newbits = 8
# netnum  = 2
#vcn_id        = ""
#ig_route_id   = ""

assign_public_ip = false
enable_ext      = false

# Compute Instance
instance_count = 3
image_id    = "ocid1.image.oc1..."
os_version  = "8"
shape = {
  shape            = "VM.Standard2.4",
  ocpus            = 4,
  memory           = 60,
  boot_volume_size = 100
}
state    = "RUNNING"
timezone = "Etc/UTC"
type     = "public"
#upgrade_bastion  = false

#MySQL DB System Paramters
mysql_shape_name  = "MySQL.VM.Standard2.4.60GB"

mysql_db_subnet  = "ocid1.subnet.oc1..."

mysql_db_system_admin_username  = "admin" 

mysql_db_system_admin_password  = "admin123"

mysql_db_system_backup_policy_is_enabled  = "true"

mysql_db_system_backup_policy_retention_in_days  = "30"

mysql_db_system_backup_policy_window_start_time  = "23:00 UTC"

mysql_db_system_data_storage_size_in_gb  = "100"

mysql_db_system_description  = "oci mysql DB System"

mysql_db_system_display_name  = "ni-mysql-infradev"

mysql_db_system_fault_domain  = "FAULT-DOMAIN-1"

mysql_db_system_hostname_label  = "mysql-dev"

mysql_db_system_is_highly_available = "false"

mysql_db_bastion_enable = false

freeform_tags = {
  # compute host freeform_tags are required
  # add more freeform_tags in each as desired
    access      = "private",
    environment = "dev",
    security    = "high"

}