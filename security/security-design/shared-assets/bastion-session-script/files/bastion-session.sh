#!/bin/bash
#
# Copyright (c) 2023 Oracle and/or its affiliates. All rights reserved.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
###############################################################################
#
# bastion-session.sh
# @author: Leon van Birgelen
#
###############################################################################

# Set default values.
version="1.0.3"
oci_profile="DEFAULT"
session_name="Bastion-Session"
session_check_counter=15  # times 10 seconds for maximum time while checking session creation status.
ttl=10800
target_port=22
username="opc"
keyalg="rsa"
keysize=4096
generatekeypair=true

###############################################################################
# Usage function.
###############################################################################
usage() {
   echo "Version: ${version}"
   echo "This shell script can be used to easily connect to the OCI Bastion service based on temporary SSH keys. Authorization is granted based on OCI CLI authentication and OCI Permissions. For OCI CLI authentication both the use of exchanged API keys and session security tokens is supported. This script works also directly on OCI Cloud Shell, however only for Managed SSH Sessions since port forwarding is not supported on OCI Cloud Shell."
   echo ""
   echo "Usage: $0 COMMAND [ARGS]..."
   echo ""
   echo "Example: $0 ssh -b bst001 -i instance-001 -u opc [-p <oci profile>]"
   echo "         $0 pf  -b bst001 -d 10.0.0.1 -e 3389 [-p <oci profile>] [-l <local port>] "
   echo ""
   echo "Commands:"
   echo "  ssh              The session type \"ssh\" for Managed SSH session."
   echo "  pf               The session type \"pf\" for Port Forwarding session."
   echo ""
   echo "Arguments:"
   echo "  -b, --bastion TEXT              (Required) The Name of the Bastion to be used. [-b or -c is required]"
   echo "  -c, --bastion-ocid TEXT         (Required) The OCID of the Bastion to be used. [-b or -c is required]"
   echo "  -i, --instance TEXT             The name of the target instance to be used."
   echo "  -j, --instance-ocid TEXT        The OCID of the target instance to be used."
   echo "  -u, --username TEXT             The target resource username to be used. [default: opc]"
   echo "  -p, --profile TEXT              The OCI profile in the config file to load. [default: DEFAULT]"
   echo "  -s, --session TEXT              The Bastion session name. [default: Bastion-Session]"
   echo "  -t, --ttl INTEGER               The Bastion session time-to-live in seconds, minimum 1800, maximum 10800. [default: 10800]"
   echo "  -d, --destination-ip IP         The destination IP Address to be used for Bastion session. [default: the first private IP address of instance]"
   echo "  -e, --destination-port INTEGER  The destination port to be used for Port Forwarding session. [default: 22]"
   echo "  -l, --local-port INTEGER        The local port to be used for Port Forwarding session. [defaults to same value as destination port]"
   echo "  -a, --key-alg TEXT              The algorithm for the SSH key (ssh-keygen) to be used. [default: rsa]"
   echo "  -k, --key-size INTEGER          The key size for the SSH key (ssh-keygen) to be used. [default: 4096]"
   echo "  -pr, --private-key TEXT         The private key file to be used when not generating a temporary key pair. [by default not used]"
   echo "  -pu, --public-key TEXT          The public key file to be used when not generating a temporary key pair. [by default not used]"
   echo "  -v, --verbose                   Show verbose output for troubleshooting."
   echo ""
   echo "Prerequisites:"
   echo "  - The OCI CLI must be installed and configured."
   echo "    (See also https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)"
   echo "  - The jq commandline JSON processer must be installed."
   echo "    (See also https://stedolan.github.io/jq)"
   echo ""
   exit 2
}

###############################################################################
# trap ctrl-c and call ctrl_c().
###############################################################################
trap ctrl_c INT

function ctrl_c() {
   echo "*** Aborting..."
   cleanup
   exit 1
}

###############################################################################
# Run the OCI CLI with or without verbose info.
###############################################################################
run_oci_cmd() {
   if [ "${verbose}" ]; then
      echo "*** Running OCI command: ${cmd}"
      result=$(${cmd})
   else
      result=$(${cmd} 2>/dev/null)
   fi
}

###############################################################################
# Retrieve private IP address based on instance OCID.
###############################################################################
oci_get_ip_address() {
   cmd="oci compute instance list-vnics --instance-id ${instance_ocid} ${oci_options}"
   if ! run_oci_cmd; then
      echo "*** Problem determining instance IP address. Check the OCI CLI connectivity and provided instance OCID."
      exit 1
   fi
   target_ip=$(echo "${result}" | jq -r '.data[0]."private-ip"')
   if [ -z "${target_ip}" ]; then
      echo "*** Problem finding instance IP address."
      exit 1
   fi
}

###############################################################################
# Retrieve OCID based on resource displayname.
###############################################################################
oci_get_resource_ocid() {
   if [ "${verbose}" ]; then
      cmd="oci search resource structured-search --query-text \"${query_text}\" ${oci_options}"
      echo "*** Running OCI command: ${cmd}"
      result=$(oci search resource structured-search --query-text "${query_text}" ${oci_options})
   else
      result=$(oci search resource structured-search --query-text "${query_text}" ${oci_options} 2>/dev/null)
   fi
   if [ $? != 0 ]; then
      echo "*** Problem finding resource by name. Check the OCI CLI connectivity and provided name."
      exit 1
   fi
   resource_ocid=$(echo "${result}" | jq -r '.data.items[0]."identifier"')
   if [ -z "${resource_ocid}" ]; then
      echo "*** Problem finding resource OCID."
      exit 1
   fi
}

###############################################################################
# Create a new bastion session.
###############################################################################
oci_create_bastion_session() {
   echo "*** Creating OCI Bastion session."
   if [ "$1" == "ssh" ]; then
      cmd="oci bastion session create-managed-ssh --bastion-id ${bastion_ocid} --display-name ${session_name} --session-ttl ${ttl} --key-type PUB  --ssh-public-key-file ${public_key_file} --target-resource-id ${instance_ocid} --target-port ${target_port} --target-os-username ${username} ${oci_options}"
   else
      cmd="oci bastion session create-port-forwarding --bastion-id ${bastion_ocid} --display-name ${session_name} --session-ttl ${ttl} --key-type PUB  --ssh-public-key-file ${public_key_file} --target-private-ip ${target_ip} --target-port ${target_port} ${oci_options}"
   fi
   if ! run_oci_cmd; then
      echo "*** Problem creating OCI Bastion session."
      exit 1
   fi
   session_id=$(echo "${result}" | jq -r '.data.id')
   if [ -z "${session_id}" ]; then
      echo "*** Problem creating OCI Bastion session."
      exit 1
   fi
   if [ "${verbose}" ]; then
      echo "*** OCI Bastion session OCID: ${session_id}"
   fi

   # Check for session creation status ACTIVE.
   cmd="oci bastion session get --session-id ${session_id} ${oci_options}"
   until [ $session_check_counter == 0 ]
   do
      sleep 5
      if ! run_oci_cmd; then
         echo "*** Problem retrieving OCI Bastion session status: ${session_id}"
         exit 1
      fi
      session_status=$(echo "${result}" | jq -r '.data."lifecycle-state"')
      echo "*** OCI Bastion session status: ${session_status}"
      if [ "${session_status}" == "CREATING" ]; then
         ((session_check_counter--))
      else
         session_check_counter=0
      fi
      sleep 5
   done
   if [ "${session_status}" != "ACTIVE" ]; then
      echo "*** Problem creating OCI Bastion session. Failed on status: ${session_status}"
      exit 1
   fi

   # Retrieve SSH command and replace SSH command placeholders.
   session_command=$(echo "${result}" | jq -r '.data."ssh-metadata".command')
   session_command=${session_command//"<privateKey>"/$private_key_file}
   session_command=${session_command//"<localPort>"/$local_port}
   if [ "${verbose}" ]; then
      echo "*** OCI Bastion session command: ${session_command}"
   fi

}

###############################################################################
# OCI session token refresh background process.
###############################################################################
oci_session_refresh() {
   while true
   do
     result=$(oci session refresh --profile ${oci_profile} >/dev/null 2>&1)
     sleep 900
   done
}

###############################################################################
# Remove an existing bastion session.
###############################################################################
oci_bastion_delete() {
   if [ "${session_id}" ]; then
      echo ""
      echo "*** Cleaning up the OCI Bastion session."
      cmd="oci bastion session delete --force --session-id ${session_id} ${oci_options}"
      run_oci_cmd
   fi
}

###############################################################################
# Cleanup temporary key files and optional oci session token refresh process.
###############################################################################
cleanup() {
   oci_bastion_delete
   if [ ${generatekeypair} == true ] && [ "${private_key_file}" ]; then
      if [ "${verbose}" ]; then
         echo "*** Cleaning up temporary key files."
      fi
      rm "${private_key_file}"
      rm "${public_key_file}"
   fi
   if [ -n "${oci_refresh_pid}" ]; then
      if [ "${verbose}" ]; then
         echo "*** Stopping keepalive process (pid: ${oci_refresh_pid})"
      fi
      kill "${oci_refresh_pid}" >/dev/null 2>&1
   fi
   echo "*** Done."
}

# Process cmdline arguments.
while [[ $# -gt 0 ]]; do
  case $1 in
    ssh)
      session_type="$1"
      shift # past argument
      ;;
    pf)
      session_type="$1"
      shift # past argument
      ;;
    -b|--bastion)
      bastion_name="$2"
      shift # past argument
      shift # past value
      ;;
    -c|--bastion-ocid)
      bastion_ocid="$2"
      shift # past argument
      shift # past value
      ;;
    -i|--instance)
      instance_name="$2"
      shift # past argument
      shift # past value
      ;;
    -j|--instance-ocid)
      instance_ocid="$2"
      shift # past argument
      shift # past value
      ;;
    -u|--username)
      username="$2"
      shift # past argument
      shift # past value
      ;;
    -p|--profile)
      oci_profile="$2"
      shift # past argument
      shift # past value
      ;;
    -d|--destination-ip)
      target_ip="$2"
      shift # past argument
      shift # past value
      ;;
    -e|--destination-port)
      target_port="$2"
      shift # past argument
      shift # past value
      ;;
    -l|--local-port)
      local_port="$2"
      shift # past argument
      shift # past value
      ;;
    -s|--session)
      session_name="$2"
      shift # past argument
      shift # past value
      ;;
    -t|--ttl)
      ttl="$2"
      shift # past argument
      shift # past value
      ;;
    -a|--key-alg)
      keyalg="$2"
      shift # past argument
      shift # past value
      ;;
    -k|--key-size)
      keysize="$2"
      shift # past argument
      shift # past value
      ;;
    -pr|--private-key)
      private_key_file="$2"
      generatekeypair=false
      shift # past argument
      shift # past value
      ;;
    -pu|--public-key)
      public_key_file="$2"
      generatekeypair=false
      shift # past argument
      shift # past value
      ;;
    -v|--verbose)
      verbose=true
      shift # past argument
      ;;
    *)
      echo "Unknown option $1"
      usage
      exit 1
      ;;
  esac
done

# Check for mandatory cmdline arguments.
if ! { [ "${session_type}" == "ssh" ] || [ "${session_type}" == "pf" ]; }; then
    usage
fi
if [ -z "${bastion_ocid}" ] && [ -z "${bastion_name}" ]; then
    usage
fi
if [ "${session_type}" == "ssh" ] && { [ -z "${instance_name}" ] && [ -z "${instance_ocid}" ]; }; then
    echo "Missing ssh session type argument!"
    usage
fi
if [ "${session_type}" == "pf" ] && { [ -z "${target_port}" ] || { [ -z "${instance_name}" ] && [ -z "${instance_ocid}" ] && [ -z "${target_ip}" ]; }; }; then
    echo "Missing pf session type argument!"
    usage
fi
if [ ${generatekeypair} == false ] && { [ -z "${private_key_file}" ] || [ -z "${public_key_file}" ]; }; then
    echo "Missing key file argument!"
    usage
fi

echo "*** Starting..."
if [ "${verbose}" ]; then
   echo "*** Version: ${version}"
fi

# Check for OCI CLI session security_token.
result=$(echo no | oci session validate --profile ${oci_profile} 2>/dev/null)
if [ $? == 0 ]; then
    if [ "${verbose}" ]; then
       echo "*** Detected valid OCI CLI session security_token."
    fi
    oci_options=" --auth security_token --profile=${oci_profile}"
    oci_session_refresh &
    oci_refresh_pid=$!
else
    if [[ ${result} == *"expired"* ]]; then
        echo "*** OCI CLI session security_token has expired! Use \"oci session authenticate --profile-name=${oci_profile}\" to renew."
        exit 1
    fi
    oci_options=" --profile=${oci_profile}"
fi

# Fetch the bastion OCID from the displayname.
if [ -z "${bastion_ocid}" ]; then
   query_text="query bastion resources where displayname = '${bastion_name}'"
   oci_get_resource_ocid
   if [ $? != 0 ] || [ "${resource_ocid}" == null ]; then
      echo "*** Problem finding bastion by name: ${bastion_name}"
      echo "*** If the bastion was created recently, it may take a few minutes to find it by name."
      exit 1
   fi
   if [ "${verbose}" ]; then
      echo "*** Retrieved bastion OCID for ${bastion_name}: ${resource_ocid}"
   fi
   bastion_ocid=${resource_ocid}
fi

# Fetch the instance OCID from the displayname.
if [ "${instance_name}" ] && [ -z "${instance_ocid}" ]; then
   query_text="query instance resources where displayname = '${instance_name}'"
   oci_get_resource_ocid
   if [ $? != 0 ] || [ "${resource_ocid}" == null ]; then
      echo "*** Problem finding instance by name: ${instance_name}"
      echo "*** If the instance was created recently, it may take a few minutes to find it by name."
      exit 1
   fi
   if [ "${verbose}" ]; then
      echo "*** Retrieved instance OCID for: ${instance_name}: ${resource_ocid}"
   fi
   instance_ocid=${resource_ocid}
fi

# Fetch the instance private IP address from instance OCID when not provided.
if [ -z "${target_ip}" ]; then
   if ! oci_get_ip_address; then
      echo "*** Problem finding instance IP address by name: ${instance_name}"
      exit 1
   fi
   if [ "${verbose}" ]; then
      echo "*** Retrieved instance IP address for ${instance_name}: ${target_ip}"
   fi
fi

# Generate key pair if needed.
# When CygWin (e.g. MobaXTerm) is used, place keys in current dir to avoid access issues.
if [ ${generatekeypair} == true ]; then
   platform=$(uname)
   if [ "${verbose}" ]; then
      echo "*** Platform is: ${platform}"
   fi
   if [[ $(grep -Fix ${platform:0:5} <<< "cygwin") ]]; then
      private_key_file=$(mktemp tmpkeyXXXXXXXX)
   else
      private_key_file=$(mktemp)
   fi
   public_key_file="${private_key_file}.pub"
   if [ "${verbose}" ]; then
      echo "*** Generating temporary ssh key pair."
      echo yes | ssh-keygen -t "${keyalg}" -b "${keysize}" -f "${private_key_file}" -N ""
   else
      echo yes | ssh-keygen -t "${keyalg}" -b "${keysize}" -f "${private_key_file}" -N "" >/dev/null 2>&1
   fi
else
   if [ "${verbose}" ]; then
      echo "*** Using existing ssh key pair."
   fi

fi
# When local_port not specified make it equal to target_port.
if [ "${session_type}" == "pf" ] && [ -z "${local_port}" ]; then
   local_port=${target_port}
fi

# Create the OCI Bastion Session.
oci_create_bastion_session ${session_type}
if [ $? != 0 ]; then
   cleanup
   exit 1
fi

# All looking good, just display status.
if [ "${session_type}" == "ssh" ]; then
   echo "*** Starting SSH session through OCI Bastion for user ${username} to ${target_ip}:${target_port}."
   echo "*** Enter \"exit\" to end session."
   echo "***"
else
   echo "*** Starting port forwarding through OCI Bastion from localhost:${local_port} to ${target_ip}:${target_port}."
   echo "*** Press CTRL-C to end session."
   echo "***"
fi

# Execute the ssh command for the bastion session.
eval "$session_command"

# Cleanup.
cleanup
