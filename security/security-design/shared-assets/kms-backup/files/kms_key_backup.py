import sys
import oci
import argparse
import os
import sys
import platform
import json
import hashlib
"""

kms_key_backup
Last update: 31.01.24

Export an OCI Vault Key and either save it to a file or copy the key to a different vault
It only exports or copies software keys. HSM keys are not exportable

Usage:
  python kms_key_backup [arguments]

  Parameters can be declared in a JSON file as arguments to the command line, or both.
  Any command line arguments overwrites JSON config file values

  The script is run in two modes, either key export only or backup to a 2. vault.

  Parameters/Arguments
  --configfile filename
    File with configuration parameters in JSON format

  Common parameters for both modi
    --ociconfig             path to OCI configuration file, assume both source and target use the same OCI config
    --source_ociprofile     Source profile in oci config
    --source_region         Source Region
    --source_compartment    Source Compartment
    --source_vault          Source vault OCI
    --source_keyname        Source Key Name, if searching for key
    --source_key_ocid       Source key OCID if searching for OCID
    --source_key_version    OCID of a specific key version, if not set pick the newest
    --wrapping_algorithm    Key Export Wrapper Algorithm
  --exportonly              Target vault is not used, only export the key and save it to a file.
    --outfile               File with encrypted key, used for exportonly option. If not set, print to stdout
    --wrapping_pubkey_file  For exportponly option, a file with openssl generated key that matches the wrapping algorithm
    --target_region         Target Region
    --target_compartment    Target Compartment
    --target_vault Target   Vault OCID
    --target_ociprofile     Target profile in oci config
    --target_keyname        Target keyname, the copy will be created with this name

"""

kms_key_backup_version= " 1.0, 31.01.24"

#
# Commandline arguments or configfile parameters and defaults
# Parameter name, default value, boolean true/false,"Help text"

config_parameters = [ \
    ['configfile',None,False,'path to configfile'], \
    ['ociconfig',None,False,'path to OCI configuration file'], \
    ['source_ociprofile',None,False,'Source profile in oci config'], \
    ['source_region',None,False,'Source Region'], \
    ['source_compartment',None,False,'Source Compartment'], \
    ['source_vault',None,False,'Source vault OCI'], \
    ['source_keyname',None,False,'Source Key Name, if search for key'], \
    ['source_key_ocid',None,False,'Source key OCID if search for OCID'], \
    ['source_key_version',None,False,'OCID of a spesific key version, if not set, latest will be set'], \
    ['target_region',None,False,'Target Region'], \
    ['target_compartment',None,False,'Target Compartment'], \
    ['target_vault',None,False,'Target Vault OCID'], \
    ['target_ociprofile',None,False,'Target profile in oci config'], \
    ['target_keyname',None,False,'Target keyname, the copy will be created with this name'], \
    ['wrapping_algorithm','RSA_OAEP_AES_SHA256',False,'Key Export Wrapper Algorithm'], \
    ['wrapping_pubkey_file',None,False,'If it supplied filepointer  external key for wrapping'], \
    ['exportonly',None,True,"only save to file or print  key, don't backup"], \
    ['outputfile',None,False,'File for the exported key']
    ]


#########################################################################
# load_config
# Load configfile from filename, Required to be a valid JSON document
# Returns configfile as JSON object
#########################################################################
def load_config(config_file_name):
    """Load config file and returns dict of configuration"""
    try:
        config_file = open(config_file_name)
    except Exception as ioError:
        print("Load of configuration file: " + args.configfile + " failed")
        exit(1)
    try:
        config = json.load(config_file)
        config_file.close()
    except Exception as ConfigError:
        print("JSON Parse of configuration file: " + config_file_name + " failed")
        exit(1)
    return config

#########################################################################
# parse_cmd_line
# Parses the command line with argsparser and returns args Namespace
#########################################################################
def parse_cmd_line():
    """ parse_cmd_line """
    global config_parameters
    args_parser = argparse.ArgumentParser(
        description='OCI KMS Software key copy program'
    )
    #
    # Loop throug and set all commandline parameters
    #
    for arg in config_parameters:
        if not arg[2]:
            args_parser.add_argument('--'+arg[0],default=arg[1],type=str,help=arg[3])
        else:
            args_parser.add_argument('--'+arg[0],default=arg[1],action='store_true',help=arg[3])
    # Parse and return parsed Namespace
    args = args_parser.parse_args()
    return(args)

#########################################################################
# overwrite_config
# Overwrite configfile settings from command line
# Any commandline settings will overwrite any settings inherited from the 
# config file, if loaded
#########################################################################
def overwrite_conf(args,config):
    """ overwrite_conf """
    dargs=vars(args)
    for arg in dargs.keys():
        if dargs[arg] is not None:
            config[arg]=dargs[arg]
    if 'exportonly' not in dargs or dargs['exportonly'] is None or not dargs['exportonly']:
        config['exportonly']=False
    else:
        config['exportonly']=True

#########################################################################
# verify_config
# Verifies that all mandatory parameters are set
# Take the two modi emxortkey or copykey into account
#########################################################################
def verify_config(config):
    """ verify_config, verifies that all mandatory configuration parameters is set """
    #
    # Mandatory source parameters
    # source_keyname" or"source_key_ocid"checked for explisitt
    #
    mandatory_source_parameters = [ 'ociconfig','source_ociprofile','source_region','source_compartment','source_vault']
    #
    # Mandatory target parameters
    #
    mandatory_target_parameters=['target_region','target_compartment','target_vault','target_ociprofile', 'target_keyname']
    #
    # Mandatory target parameters
    #
    mandatory_other_parameters=['wrapping_algorithm']
    #
    complete=0
    for param in mandatory_source_parameters:
        if config[param] is None:
            print("Mandatory source parameter "+param+ " is missing in configuration/commandline")
            complete+=1
    for param in mandatory_other_parameters:
        if config[param] is None:
            print("Mandatory other parameter "+param+ " is missing in configuration/commandline")
            complete+=1
    #
    # Add default for non mandatory parameters
    #
    config['source_key_version'] = None if 'source_key_version' not in config else config['source_key_version']
    config['source_keyname'] = None if 'source_keyname' not in config else config['source_keyname']
    config['source_key_ocid'] = None if 'source_key_ocid' not in config else config['source_key_ocid']
    #
    # Explisitt check for "source_keyname" or "source_key_ocid" at least one should be set,
    # if both, OCID takes presidents
    #
    if config['source_keyname'] is None and config['source_key_ocid'] is None :
        print("Neither source_keyname nor source_key_ocid is set")
        print(config)
        complete+=1
    #
    # Only validate target config parameters if exportonly is not set
    #
    if not config['exportonly']:
        #
        # Include target verification
        for param in mandatory_target_parameters:
            if config[param] is None:
                print("Mandatory target parameter "+param+ " is missing in configuration/commandline")
                complete+=1
    else:
        if not 'wrapping_pubkey_file' in config:
            print("wrapping_pubkey_file is required for exportonly option")
            complete+=1 
    return(complete == 0)

#########################################################################
# print_key_fingerprint
# Generates sha1 fingerprint of the encrypted export of the key
#########################################################################
def print_key_fingerprint(key): 
    """ print_key_fingerprint """                 
    #
    # print the hash of the key
    #
    hasher = hashlib.sha1()
    print(key)
    hasher.update(key.encode('utf-8'))
    print("######## Fingerprint ################")
    print("Sha1 hash of key: "+hasher.hexdigest())
    print("#####################################")

#########################################################################
# create_kms_client
# Generic allocation of kms client resources
# If successfull, returns a dict with the following elements:
# management_client=kms_management_client
# vault_client=kms_vault_client
# vault_data=kms_vault_data
# ociconfig=oci_config
#########################################################################
def create_kms_client(oci_config_file,oci_profile_name,kms_vault_ocid):
    """ create_kms_client """
    #################################################
    # Load OCI Config
    #################################################
    oci_config = oci.config.from_file(
        oci_config_file, oci_profile_name
    )

    ##################################################
    #### Create KMS client
    ##################################################
    kms_vault_client = oci.key_management.KmsVaultClient(oci_config)
    kms_vault_data = kms_vault_client.get_vault(kms_vault_ocid).data
    kms_service_endpoint = kms_vault_data.management_endpoint
    kms_management_client = oci.key_management.KmsManagementClient(
           config=oci_config, service_endpoint=kms_service_endpoint
    )
    kms_client={}
    kms_client['management_client']=kms_management_client
    kms_client['vault_client']=kms_vault_client
    kms_client['vault_data']=kms_vault_data
    kms_client['ociconfig']=oci_config
    return(kms_client)

#########################################################################
# get_kms_key
# 
# Search for the key in the given vault
# Either search for key based on name or ocid
# returns the kms_key object if found, else False. 
# Return the newest key if source_key_version is None
#########################################################################
def get_kms_key(kms_client,compartment_ocid,kms_keyname,kms_keyocid,wrapping_key,wrapping_algorithm,key_version):
    """ get_kms_key """
    if kms_keyname is None and kms_keyocid is None:
        print("Eiter keyname or keyocid needs to be set")
        return(False)
    ###################################################
    #### Allocate KSM management client, KMS vault client
    ###################################################
    kms_oci_config=kms_client['ociconfig']
    kms_vault_client=kms_client['vault_client']
    kms_vault_data = kms_client['vault_data']
    kms_service_endpoint = kms_vault_data.management_endpoint
    kms_crypto_endpoint = kms_vault_data.crypto_endpoint
    kms_management_client = kms_client['management_client']
    kms_crypto_client = oci.key_management.KmsCryptoClient(
        config=kms_oci_config, service_endpoint=kms_crypto_endpoint
    )
    ###################################################
    #### Get keys from vault
    ###################################################
    # get keys
    all_keys_in_vault = oci.pagination.list_call_get_all_results(
        kms_management_client.list_keys,
        compartment_ocid,
        sort_by='TIMECREATED',
        sort_order='DESC',
    ).data
    ###################################################
    #### Iterate over all keys in vault, searching for the key
    ################################################### 
    for kms_key in all_keys_in_vault:
        ###################################################
        #### Only export if the key is a softare key,
        #### and only if Enabled
        ###################################################

        if (kms_keyocid is not None and kms_keyocid == kms_key.id) or (kms_keyname is not None and kms_keyname == kms_key.display_name):
            if kms_key.protection_mode == 'SOFTWARE':
                # get details of the key
                current_key_data = kms_management_client.get_key(kms_key.id).data
                # export the key using the wrapping key from the target vault
                export_key_details = oci.key_management.models.ExportKeyDetails(
                    key_id=kms_key.id, algorithm=wrapping_algorithm, public_key=wrapping_key, 
                    key_version_id=key_version
                )
                ###################################################
                #### Export the key, if enabled
                ###################################################
                exported_key=False
                if kms_key.lifecycle_state == 'ENABLED':
                    exported_key = kms_crypto_client.export_key(
                        export_key_details
                    )
                    key_data={}
                    key_data['exported_key']=exported_key
                    key_data['kms_key_metadata']=kms_key
                    key_data['current_key_data']=current_key_data
                    return(key_data)
                else:
                    print("Key is not in ENABLED state")
                    return(False)
            else:
                print("Key found but it is not a softare key, export not permitted by OCI")
                return(False)
    #
    # This point is reached only if a key with OCID or name is not found
    #
    print("No key found, verify name/ocid")
    #
    return(False)

#########################################################################
# import_key
# 
# import the key to the target spesified in kms_client
# return when successfull,the OCI API resonse object
# return False, Import failed
#########################################################################
def import_key(config,key_data,kms_client,wrapping_key,wrapping_algorithm):
    """ import_key """
    # the algorithm to use for the wrapping key
    wrapping_algorithm = config['wrapping_algorithm']

    ##################################################
    #### Allocate KMS target client
    ##################################################

    target_kms_oci_config=kms_client['ociconfig']
    target_kms_vault_client=kms_client['vault_client']
    target_kms_vault_data = kms_client['vault_data']
    target_kms_management_client = kms_client['management_client']
    target_kms_service_endpoint = target_kms_vault_data.management_endpoint
    target_kms_crypto_endpoint = target_kms_vault_data.crypto_endpoint
    kms_key=key_data['kms_key_metadata']
    exported_key=key_data['exported_key']
    target_kms_crypto_client = oci.key_management.KmsCryptoClient(
        config=target_kms_oci_config, service_endpoint=target_kms_crypto_endpoint
    )
    """
    ###################################################
    #### Get wrapping key from target vault
    ###################################################
    wrapping_key_raw = target_kms_management_client.get_wrapping_key().data.public_key
    # strip new line characters from the key
    wrapping_key = wrapping_key_raw.replace("\n", "")
    """
    ###################################################
    #### Wrap the key for import
    ###################################################
    #current_key_data = target_kms_management_client.get_key(kms_key.id).data
    current_key_data=key_data['current_key_data']
    key_shape = oci.key_management.models.KeyShape(
        algorithm=kms_key.algorithm,
        length=int(current_key_data.key_shape.length),
    )
    wrapped_import_key = oci.key_management.models.WrappedImportKey(
        key_material=exported_key.data.encrypted_key, wrapping_algorithm=wrapping_algorithm
    )
    ###################################################
    #### Import the key to target
    ###################################################
    try:
        import_key_details = oci.key_management.models.ImportKeyDetails(
                            compartment_id=config['target_compartment'],
                            display_name=config['target_keyname'],
                            key_shape=key_shape,
                            protection_mode=kms_key.protection_mode,
                            wrapped_import_key=wrapped_import_key,
                            freeform_tags={
                                'source_vault_origin': config['target_vault'],
                                'source_key_origin': kms_key.id,
                            },
        )
        response = target_kms_management_client.import_key(
            import_key_details
        )
        print("Imported key: " + config['target_keyname'] + " with ID: " + kms_key.id )
        print("Target OCID " + response.data.id)
        return(response)
    except Exception as e:
        print("Failed to import key " + kms_key.id + ": " + str(e))
        return(False)



#########################################################################
# main
# main function called from commandline
######################################################################### 
def main():
    """main function"""
    #
    # Define default config file name
    #
    os_name = platform.system().lower()
    if os_name == 'linux':
        default_kms_copy_config_file = '/home/users/demo/key_backup.json'
    elif os_name == 'windows':
        default_kms_copy_config_file = 'c:\\temp\\key_backup.json'
    else:
        print("Platform: " + "os_name is not supported")
        exit(1)
    #
    # Parse commadn line args
    #
    args=parse_cmd_line()

    #
    #  Load config file
    #
    if(args.configfile is not None):
        config = load_config(args.configfile)
    else:
        config={}
    #
    # Add or owerwrite config from configfile with cmdline parameters
    #
    overwrite_conf(args,config)

    if not verify_config(config):
        print("Parameter verification failed, review error message")
        exit(1)
    #
    # Process based on print or backup
    #
    if config['exportonly']:
        #
        # Load the external public key
        #
        with open(config['wrapping_pubkey_file'], 'r') as file:
            pub_key = file.read().replace('\n', '')
        # Allocate kms_Client
        source_kms_client=create_kms_client(config['ociconfig'],config['source_ociprofile'],config['source_vault'])
        # Extract the key
        key_data=get_kms_key(source_kms_client,config['source_compartment'],config['source_keyname'],config['source_key_ocid'],
                             pub_key,config['wrapping_algorithm'],config['source_key_version'])
        if not key_data == False:
            encrypted_key=key_data['exported_key'].data.encrypted_key
            print_key_fingerprint(encrypted_key)
            # Succesfull extraction
            # Write to file if outputfile is defined
            if 'outputfile' in config:
                outfile=open(config['outputfile'],w)
                outfile.write(encrypted_key)
                outfile.close()
            else:
                print("######### Encrypted key #############")
                print(encrypted_key)
                print("#####################################")
    else:
        #
        # Backup the key from one region to another region#
        #
        # Allocate kms_Clients
        source_kms_client=create_kms_client(config['ociconfig'],config['source_ociprofile'],config['source_vault'])
        target_kms_client=create_kms_client(config['ociconfig'],config['target_ociprofile'],config['target_vault'])
        #
        # Get the target public key
        #
        wrapping_key = target_kms_client['management_client'].get_wrapping_key().data.public_key.replace("\n", "")
        # Extract the key
        key_data=get_kms_key(source_kms_client,config['source_compartment'],config['source_keyname'],config['source_key_ocid'],
                             wrapping_key,config['wrapping_algorithm'],config['source_key_version'])
        if key_data !=  False:
            response=import_key(config,key_data,target_kms_client,wrapping_key,config['wrapping_algorithm'])
            if response != False:
                print("Key successfully imported with OCID: ",end='')
    print("kms_key_backup complete")        
        

#
# Entrypoint if run as standalone script
if __name__ == "__main__":
    print("KMS Key extract/backup tool "+kms_key_backup_version)
    main()
