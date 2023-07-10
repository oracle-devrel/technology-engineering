# coding: utf-8

import oci
import os 
import json

from modules.utils import red, green, print_error, print_info

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set custom retry strategy
# - - - - - - - - - - - - - - - - - - - - - - - - - -

custom_retry_strategy = oci.retry.RetryStrategyBuilder(
                            max_attempts_check=True,
                            max_attempts=3,
                            total_elapsed_time_check=True,
                            total_elapsed_time_seconds=20,
                            retry_max_wait_between_calls_seconds=5,
                            retry_base_sleep_time_seconds=2,
                            ).get_retry_strategy()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get tenancy name
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_tenancy(tenancy_id, config, signer):

    identity = oci.identity.IdentityClient(config=config, signer=signer)
    try:
        tenancy = identity.get_tenancy(tenancy_id)
        home_region_key = f'home region: {tenancy.data.home_region_key}'
    except oci.exceptions.ServiceError as e:
        print_error("Tenancy error:", tenancy_id, e.code, e.message)
        raise SystemExit(1)

    return tenancy.data.name, home_region_key

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# create signer for Authentication
# input - config_profile and is_instance_principals and is_delegation_token
# output - config and signer objects
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def create_signer(config_file_path, config_profile, is_delegation_token, is_config_file):

    # --------------------------------
    # Config File authentication
    # --------------------------------
    if is_config_file:
        try:
            config = oci.config.from_file(file_location=config_file_path, profile_name=config_profile)
            oci.config.validate_config(config) # raise an error if error in config

            signer = oci.signer.Signer(
                tenancy=config['tenancy'],
                user=config['user'],
                fingerprint=config['fingerprint'],
                private_key_file_location=config.get('key_file'),
                pass_phrase=oci.config.get_config_value_or_default(config, 'pass_phrase'),
                private_key_content=config.get('key_content')
            )
            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            print_info(green, 'Login', 'success', 'config_file')
            print_info(green, 'Login', 'profile', config_profile)

            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            print_info(green, 'Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            print_error("Something went wrong with file content:", config_file_path, config_profile, e.code, e.message)
            raise SystemExit(1)

        except Exception as e:
            print_error(e)
            raise SystemExit(1)
    
    # --------------------------------
    # Delegation Token authentication
    # --------------------------------
    elif is_delegation_token:

        try:
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')
            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config['delegation_token_file']
            oci.config.validate_config(config) # raise an error if error in config

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            print_info(green, 'Login', 'success', 'delegation_token')
            print_info(green, 'Login', 'token', delegation_token_location)

            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            print_info(green, 'Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            print_error("CloudShell authentication error:", e)
            raise SystemExit(1)
        
        except Exception as e:
            print_error("CloudShell authentication error:", e)
            raise SystemExit(1)
        
    # -----------------------------------
    # Instance Principals authentication
    # -----------------------------------
    else:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner(retry_strategy=custom_retry_strategy)
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
          
            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)

            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            print_info(green, 'Login', 'success', 'instance_principals')
            print_info(green, 'Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            print_error("Instance_Principals authentication error:", e)
            raise SystemExit(1)

        except Exception as e:
            print_error("Instance Principals authentication error:", e)
            raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get compartment name
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_compartment_name(identity_client, compartment_id):
    
    try:
        compartment_name = identity_client.get_compartment(compartment_id).data.name
        return compartment_name
    
    except oci.exceptions.ServiceError as e:
        print_error("Compartment_id error:", compartment_id, e.code, e.message)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check compartment state
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def check_compartment_state(identity_client, compartment_id):

    try:
        compartment = identity_client.get_compartment(compartment_id).data

        if compartment.lifecycle_state != 'ACTIVE':
            print_error("Compartment:", compartment.name, "is", compartment.lifecycle_state)
            raise SystemExit(1)
  
    except oci.exceptions.ServiceError as e:
        print_error("Compartment_id error:", compartment_id, e.code, e.message)
        raise SystemExit(1)
    
# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get all subscribed region in the tenancy
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_region_subscription_list(identity_client, tenancy_id, target_region):

    try:
        print('   Retrieving regions...',end=' '*30+'\r',flush=True)
        subscribed_regions = identity_client.list_region_subscriptions(tenancy_id).data

        # create dic region_name:region for each region
        region_map = {region.region_name: region for region in subscribed_regions}

        if target_region:
            region = region_map.get(target_region.lower())
            if region:
                subscribed_region =[]
                subscribed_region.append(region)
                return subscribed_region
            else:
                print_error("Region error:", tenancy_id, target_region, "Region not subscribed or does not exist")
                raise SystemExit(1)

    except oci.exceptions.ServiceError as e:
        print_error("Region error:", tenancy_id, target_region, e)
        raise SystemExit(1)

    return subscribed_regions

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get all compartments in the tenancy using OCI search (not used hereby)
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_compartments(search_client):

    try:
        print('   Retrieving compartments...',end=' '*15+'\r',flush=True)    
        search = oci.resource_search.models.StructuredSearchDetails(
            query="query compartment resources",
            type='Structured',
            matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)
        
        compartments = oci.pagination.list_call_get_all_results(search_client.search_resources, search).data # no limits return
        print('   Compartments retrieved...',end=' '*15+'\r',flush=True)    
   
    except oci.exceptions.ServiceError as e:
        print_error(e)
        raise SystemExit(1) 

    except Exception as e:
        print_error(e)
        raise SystemExit(1) 

    return compartments

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get all compartments in the tenancy
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_compartment_list(identity_client, compartment_id, excluded_comp):
    
    print('   Retrieving compartments...',end=' '*15+'\r',flush=True)
    target_compartments = []
    all_compartments = []

    try:
        top_level_compartment_response = identity_client.get_compartment(compartment_id)
        target_compartments.append(top_level_compartment_response.data)
        all_compartments.append(top_level_compartment_response.data)
    
    except oci.exceptions.ServiceError as response:
        print_error("Error compartment_id: ", {compartment_id}, {response.code}, {response.message})
        raise SystemExit(1)

    while len(target_compartments) > 0:
        target = target_compartments.pop(0)

        # remove excluded_comp child compartments 
        if target.id != excluded_comp:
            child_compartment_response = oci.pagination.list_call_get_all_results(
                identity_client.list_compartments,
                target.id
            )
            target_compartments.extend(child_compartment_response.data)
            all_compartments.extend(child_compartment_response.data)

    active_compartments = []

    for compartment in all_compartments:
        if compartment.lifecycle_state== 'ACTIVE' and compartment.id != excluded_comp:
            active_compartments.append(compartment)

    return active_compartments

def check_tags(identity_client, search_client, cmd_tag_namespace, cmd_tag_key):

    try:
        search = oci.resource_search.models.StructuredSearchDetails(
            query="query tagnamespace resources",
            type='Structured',
            matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)

        tag_namespaces = oci.pagination.list_call_get_all_results(search_client.search_resources, search).data
        all_tag_namespaces={}

        for item in tag_namespaces:
            all_tag_namespaces.update({item.display_name : item.identifier})

        # search if TagNameSpace exists in tag_namespaces
        if cmd_tag_namespace in all_tag_namespaces:

            # check tag_namespace state
            tag_namespace=identity_client.get_tag_namespace(all_tag_namespaces[cmd_tag_namespace]).data

            if tag_namespace.is_retired == False and tag_namespace.lifecycle_state == 'ACTIVE':
                print_info(green, 'Tag Namespace', 'found', tag_namespace.name)
                # retrieve tag keys
                tag_keys=identity_client.list_tags(tag_namespace.id).data
                
                for tag_key in tag_keys:

                    if tag_key.name == cmd_tag_key:

                        # check tag_key state
                        if tag_key.is_retired == False and tag_key.lifecycle_state == 'ACTIVE':
                            tk=identity_client.get_tag(tag_namespace.id, tag_key.name).data
                            print_info(green, 'Tag Key', 'found', tag_key.name)

                            if tk.validator == None: # if validator is not 'null' means key is a list of predefined values 
                                return True
                            else:
                                tk_validator = str(tk.validator)
                                tk_validator = json.dumps(tk_validator).replace('\\n', '').replace('\\', '') # convert as single line
                                print_error('Invalid Tag Value Type:', tk_validator, 'must be an empty static value')
                                raise SystemExit(1)
                        else:
                            print_error('Invalid Tag Key State', 'Retired or Inactive')
                            raise SystemExit(1)
            else:
                print_error('Invalid Tag Namespace state', 'Retired:', tag_namespace.is_retired, 'Lifecycle_State:', tag_namespace.lifecycle_state)
                raise SystemExit(1)
        else:
            print_error('Tag Namespace not found', cmd_tag_namespace)
            raise SystemExit(1)
        
        print_error('Tag Key not found', cmd_tag_key)
        raise SystemExit(1)

    except oci.exceptions.ServiceError as e:
        print_error(e)
        raise SystemExit(1)

    except Exception as e:
        print_error(e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get all Availaibility Domains per region
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def list_ads(identity_client, tenancy_id):
    print('   Retrieving Availaibility Domains...',end=' '*15+'\r',flush=True)

    try:
        region_ads=[]
        all_ads = identity_client.list_availability_domains(tenancy_id).data

        for ad in all_ads:
            region_ads.append(ad.name)

        print('   Availaibility Domains retrieved...',end=' '*15+'\r',flush=True)    
   
    except oci.exceptions.ServiceError as e:
        print_error(e)
        raise SystemExit(1)

    except Exception as e:
        print_error(e)
        raise SystemExit(1) 
    
    return region_ads