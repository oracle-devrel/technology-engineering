#!/bin/bash

unset -v registry;
unset -v compartment_id;
unset -v artifact;

while getopts r:c:a: flag
do
    case "${flag}" in
        r) registry=${OPTARG};;
        c) compartment_id=${OPTARG};;
        a) artifact=${OPTARG};;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done

#shift "$(( OPTIND - 1 ))"  -----> to say that only 1 parameter is mandatory

if [ -z "$registry" ] || [ -z "$compartment_id" ] || [ -a "$artifact" ]; then
        echo 'Missing -r (registry) or -c (compartment_id) or -a (artifact)' >&2
        exit 1
fi


get_repo_path(){
  repo_region_name=$(echo "$1" | cut -d. -f4);
  region_key=$(oci iam region list --query "data[?name == '$repo_region_name'].key | [0]" --raw-output);
  region_key=$(echo "$region_key" | tr '[:upper:]' '[:lower:]');
  repo_namespace=$(oci artifacts container configuration get --compartment-id "$compartment_id" --query data.namespace --raw-output);
  repo_path=${region_key}.ocir.io/${repo_namespace}/$registry;
  echo "$repo_path";
}

#Checking if registry creation necessary
repo_id=$(oci artifacts container repository list --compartment-id "$compartment_id" --display-name "$registry/$artifact" --limit 1 --query data.items[0].id --raw-output);
# Create repo if it does not exist!
[ -z "$repo_id" ] && repo_id=$(oci artifacts container repository create --display-name "$registry/$artifact" --compartment-id "$compartment_id" --query data.id --raw-output);
# If repo_id is still empty, an error has occurred
[ -z "$repo_id" ] && exit 1
get_repo_path "$repo_id"



