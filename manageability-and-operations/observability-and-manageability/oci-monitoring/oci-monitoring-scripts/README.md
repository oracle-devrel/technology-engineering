### sample oci scripts to get the status of my servers  

Motivation:

Run a simple oci cli script to get the status of the oci servers from OCI tenancies

the user should be able to read the instances state of the compartments that he want to inspect with the below code



```
# update all the relevant information about the oci identity user as required for the oci cli command to run

export user=""
export fingerprint=""
export tenancy=""
export region=""
export key_file=""

export OCI_CLI_CONFIG_FILE=""
echo $OCI_CLI_CONFIG_FILE  



## typical oci search queries
query instance resources where lifeCycleState = 'RUNNING'  
query all resources  where compartmentId = 'compartmentOcid'

query instance resources  where (compartmentId = 'compartmentOcid') && (lifeCycleState = 'RUNNING')


### get the list of the instances with the below format
### instance_name,lifecycle_state,defined_tafe_createdby,free_form_tag,ocid
rm -rf  full_tenancy_instances_ocids.txt
rm -rf  tenancy_instances_ocids.txt
rm -rf  full_tenancy_instances_ocids.csv

export instance_ocid=oci search resource structured-search \
  --profile DEFAULT  \
  --query-text "query instance resources  \
    where (compartmentId = '') &&   (lifeCycleState != 'TERMINATED' )  sorted  by  lifeCycleState asc" \
   --limit 3000
  echo "$instance_ocid" >> full_tenancy_instances_ocids.txt

sed '/^$/d' -i full_tenancy_instances_ocids.txt


cat full_tenancy_instances_ocids.txt | grep "identifier"  | sed  -e 's/"//g'   -e 's/identifier//g' -e  's/,//g' -e  's/://g' -e 's/^[ ]*//g' > tenancy_instances_ocids.txt

cat tenancy_instances_ocids.txt

cat full_tenancy_instances_ocids.txt | jq  ' .data[] | select( length > 0)' | jq '.[] | "(."display-name")(",")(."lifecycle-state")(",")(."defined-tags"."Oracle-Tags"."CreatedBy")(",")(."freeform-tags"."RunAlway")(",")(."identifier")"' \
 | sed 's/"//g' | sed 's/ //g' | sed "s/$/,$date_rep/g" > full_tenancy_instances_ocids.csv
 

### output example
fictious_oem_testbed,RUNNING,null,null,ocid1.instance.XXXX,
fictious_admin,RUNNING,null,null,ocid1.instance.XXXX,
fictious_dev_instance,STOPPED,null,null,ocid1.instance.XXXX,
fictious_ubuntu,Stopped,null,null,ocid1.instance.XXXX,

```

