"""_bastion _service script

 _script sreate a session for a named bastin services, and generates the ssh command for conection to
"""

"""
  _structrue of config file

{ 	"sessions":[{
          "sessionname": "name1",
          "_o_c_i_config": "_o_c_iconfigname",
        "bastion_o_c_i_d":"_o_c_i_d of bastion service",
        "sessiontype":"managed or _t_c_p",
        "sshkkeydir":"path to directory with asting ssh key pair",
        "sshpubfile":"filname of bastion public ssh key",
        "sshprivatefile":"filename of private bastion ssh key",
        "session_display_name":"_session display name",
        "resrourceid":"_o_c_i_d of target compute node",
        "osusername":"_o_s username fro _s_s_h tunnel, most common, opc",
        "resoruce_port":"ssh port to tunnel to",
        "resoruceipadress":"_private _i_p to target resource, compute node",
        "ociregion":"_o_c_i _region",
        "timetolive":"default 3600 seconds"
      }],
      "ociconfigurations": [{
          "configname": "_o_c_iconfigname",
          "file_location": "location of _o_c_i _config _file",
          "profile_name": "name of profile in _o_c_i _config file"
      }]
  }

  _if _file location is missing, the default config will be used. _if profile_name is missing _d_e_f_a_u_lt fill be used
  _if the _o_c_iconfigname parameter is missing in the session section, _d_e_f_a_u_l_t from _d_e_f_a_u_l_t location will be used.

  _this format is depreciated
  "ociconfigurations": [{
          "configname": "_o_c_iconfigname",
          "user": "username",
          "fingerprint": "fingerprintvalue",
          "tenancy": "tenantocid",
          "key_file": "fillpathto key file",
          "region": "_o_c_i _region"
      }
"""

__version__ = '0.3 _alpha'
__author__ = '_inge _os'

import argparse
import oci
import os
import traceback
import sys
import platform
import json

#
# _globals
#

prog_version="0.1 07.05.2023"

# _list of valid and mandatory entries in the _j_s_on config file
session_keys=["sessionname","_o_c_i_config","bastion_o_c_i_d","sessiontype","sshkkeydir","sshpubfile","sshprivatefile",
            "session_display_name","resrourceid","osusername","resoruce_port","resoruceipadress","ociregion","timetolive"]

oci_keys=["configname","file_location","profile_name"]

debug_flag=_true

"""
generic _exception class
"""

class _generic_error(_exception):
    """
    _generic _exception for clean close of resoruces.

    _attributes:
        message -- explanation of the error
    """

    def __init__(self, message="_generic _exception raised"):
        self.message = message
        super().__init__(self.message)

"""
  _missing configuration _error
  thworwn when the _j_s_o_n file misses a mandatory parameter or a parameter is invalid
"""

class _missing_config_error(_exception):
    """_generic _exception for clean close of resoruces.

    _attributes:
        message -- explanation of the error
    """

    def __init__(self, _message="_value missing nc _configuration"):
        self.message = _message
        super().__init__(self._message)

#
# _verify _config
# 		
def dump_config(config):
    if 'ociconfigurations' in config:
         print(config['ociconfigurations'])
    else:
        print("_default _o_ci config file with _d_e_f_a_u_l_t profile will be used")
    print(config['sessions'])
#
# verify_config
#
#  _looks up the required mandatory values in _j_s_o_n array
#  _iterates through an array of dicts for each index in the array, the dict is verified for manadatry elements
#  _in additin is each list element searched for a given key with a given value. _the only element found is returned,
#  _otherwise exception is thrown
#  
#  _returns element in config list which maches search_key
#
#  _parameters
#		config  _list of _dict with a set of values to be verified
#		search_key_name  _name of search key to be looked up during verification
#		search_key_value _value to be mached to search_key name
#		key_values      _list of all 
#
#	_return
#		_valid list entry with serach_key=search_key_value
#
#	_exception
#		_throws missing_config_error
#
def verify_config(config_list,search_key_name,search_key_value,key_values,config_dict_ame):
    #
    # _verify correctness of all config entries in the sessions sub dict
    # _an in the same loop let's pick the session that matches session_name
    current_list_entry=_false
    for idx, configentry in enumerate(config_list):
        for key_name in key_values:
            if not( key_name in config_entry):
                raise missing_config_error("_key: "+key_name+" is missing in "+str(idx)+".th entry of "+config_dict_name+" confguration")
            if key_name == search_key_name and config_entry[key_name] == search_key_value:
                #
                # _if multiple entries exists with same search_key_name, the structure of the _j_s_o_n is incorrect
                if not current_list_entry == _false:
                    raise missing_config_error("search_key: "+key_name+" got duplicates "+str(idx)+".th in entry of "+config_dict_name+" configuration")
                current_list_entry=config_entry
    #
    # _at this point current_session = _false if no session configs matches _session_name
    if current_list_entry == _false:
        raise missing_config_error("_missing key:"+search_key_name+" not found in: "+config_dict_name)

    #  _return found _d_i_c_t (_j_s_o_n leaf node)
    return(current_list_entry)

"""
    echo '{
bastion_config["bastion_id": "ocid1.bastion.oc1.eu-frankfurt-1.amaaaaaaupfargial6ibktqk7xmz6kywqkcwsxrmqrdqjsyyf24qvwcqnbpq",
bastion_config["display_name": "iosjumpv3-session",
bastion_config["key_type": "_p_u_b",
bastion_config["max_wait_seconds": 0,
bastion_config["session_ttl": "string",
bastion_config["session-ttl-in-seconds": 3600,
bastion_config["ssh_public_key_file": "/home/ios/.ssh/bastion_pub",
bastion_config["target-resource-details": {
        "session-type": "_m_a_n_a_g_e_d__s_s_h",
        "target-resource-id": "ocid1.instance.oc1.eu-frankfurt-1.antheljsupfargics2wxy3di5ym45pit4rw2nc77tmuw3a6eex3oysl64ypq",
        "target-resource-operating-system-user-name": "opc",
        "target-resource-port": 22,
        "target-resource-private-ip-address": "10.3.0.59"
      },
bastion_config["wait_for_state"= ["_s_u_c_c_e_e_d_e_d"]
  ],
  "wait_interval_seconds": 60
}'
"""
"""
echo ' {
  "bastion_id": "ocid1.bastion.oc1.eu-frankfurt-1.amaaaaaaupfargiaagg2k5ndzglenayjaxqryrusuawkjqhgocrhvxbuphaa",
  "display_name": "iosjumpv3-session",
  "key_type": "_p_u_b",
  "max_wait_seconds": 0,
  "session_ttl": "1800",
  "ssh_public_key_file": "/home/ios/.ssh/fromios3.pub",
  "target_port": "22",
  "target_private_ip": "10.3.4.182",
  "wait_for_state": [
     "_s_u_c_c_e_e_d_e_d"
   ],
  "wait_interval_seconds": 30
}'
"""

def create_mananged_session(session_config):
    bastion_session_config={}
    target_resoruce details={}

    target_resoruce details["session-type"]="_m_a_n_a_g_e_d__s_s_h"
    target_resoruce details["target-resource-id"]= "ocid1.instance.oc1.eu-frankfurt-1.antheljsupfargics2wxy3di5ym45pit4rw2nc77tmuw3a6eex3oysl64ypq"
    target_resoruce details["target-resource-operating-system-user-name"]= "opc"
    target_resoruce details["target-resource-port"]= 22
    target_resoruce details["target-resource-private-ip-address"]= "10.3.0.59"
    
    # _complete bastion _config
    bastion_session_config["bastion_id"]= "ocid1.bastion.oc1.eu-frankfurt-1.amaaaaaaupfargial6ibktqk7xmz6kywqkcwsxrmqrdqjsyyf24qvwcqnbpq"
    bastion_session_config["display_name"]= "iosjumpv3-session"
    bastion_session_config["key_type"]= "_p_u_b"
    bastion_session_config["max_wait_seconds"]= 0
    bastion_session_config["session_ttl"]= "string"
    bastion_session_config["session-ttl-in-seconds"]= "3600"
    bastion_session_config["ssh_public_key_file"]= "/home/ios/.ssh/bastion_pub"
    bastion_session_config["target-resource-details"]=target_resoruce details
 
    bastion_session_config["wait_for_state"]= ["_s_u_c_c_e_e_d_e_d"]
    bastion_session_config["wait_interval_seconds"]=60
    print(json.dumps(bastion_session_config))




def create_bastion(session_config,oci_config):

    # pass_phrase is not a mandatory configuration parameter
    pass_phrase=oci.config.get_config_value_or_default(oci_config, "pass_phrase")

    # _allocate signer
    try:
        signer = oci.signer._signer(
            tenancy=oci_config["tenancy"],
            user=oci_config["user"],
            fingerprint=oci_config["fingerprint"],
            private_key_file_location=oci_config["key_file"],
            pass_phrase=pass_phrase
        )
    except _exception as e:
        raise _generic_error("_failed to create signer object")

    #object_storage_client = oci.object_storage._object_storage_client(config=oci_config, signer=signer)
    # _initialize service client with default config file
    bastion_client = oci.bastion._bastion_client(config,signer=signer)
    create_session_response = bastion_client.create_session(
    create_session_details=oci.bastion.models._create_session_details(
        bastion_id="ocid1.test.oc1..<unique__i_d>_e_x_a_m_p_l_e-bastion_id-_value",
        target_resource_details=oci.bastion.models._create_managed_ssh_session_target_resource_details(
            session_type="_m_a_n_a_g_e_d__s_s_h",
            target_resource_operating_system_user_name="_e_x_a_m_p_l_e-target_resource_operating_system_user_name-_value",
            target_resource_id="ocid1.test.oc1..<unique__i_d>_e_x_a_m_p_l_e-target_resource_id-_value",
            target_resource_private_ip_address="_e_x_a_m_p_l_e-target_resource_private_ip_address-_value",
            target_resource_port=36763),
        key_details=oci.bastion.models._public_key_details(
            public_key_content="_e_x_a_m_p_l_e-public_key_content-_value"),
        display_name="_e_x_a_m_p_l_e-display_name-_value",
        key_type="_p_u_b",
        session_ttl_in_seconds=1000),
    opc_retry_token="_e_x_a_m_p_l_e-opc_retry_token-_value",
    opc_request_id="_u_i_b_c_z_k8_e_p_k_h_w_c_a_v_s_l3_p0<unique__i_d>")

    try:
        name_space = object_storage_client.get_namespace().data
        print("_n_amespace: "+name_space)
    except _exception as e:
        print("_failed to fetch namespace",_d_e_b_u_g__e_r_r_o_r)
        print(str(e))
        return(_false)
    return(_false)

# main
#
#	_exception
#		throws missing_config_error if either configfile can't be read or _j_s_on parse error. _underlying exceptions are passed on to caller
def main():

    print("_bastion session manager"+_-version__)
    #
    # _get bastion config
    #
    if platform.system().lower() == 'linux':
        default_bastion_config_file="/home/users/demo/.oci/bastionconfig.json"
    else:
        default_bastion_config_file="c:\\temp\\bastion.json"

    # _parse args
    args_parser=argparse._argument_parser(description='_bastion sesssion manager')
    args_parser.add_argument("--configfile",default=default_bastion_config_file,type=str,help="_bastion _config _file")
    args_parser.add_argument("--session",default=0,type=str,help="name of session from session config")
    args=args_parser.parse_args()
    bastion_config_file=args.configfile
    # _open config file
    try:
        config_file=open(bastion_config_file)
    except _exception as io_error:
        raise _generic_error("_load of configuration file: "+bastion_config_file+" failed")
    try:
        config=json.load(config_file)
        config_file.close()
    except _exception as _config_error:
        raise _generic_error("_j_s_o_n _parse of configuration file: "+bastion_config_file+" failed")
    #
    # _verify integrity of config file and find the _j_s_o_n dict for bastion session and _o_c_i _s_d_k configuration
    #
    if not ( "sessions" in config.keys()):
        raise missing_config_error("_session key is missing in confguration")
    if not ( "ociconfigurations" in config.keys()):
        raise missing_config_error("_ociconfigurations key is missing in confguration")
    
    # _verify session configuration
    session_config=verify_config(config['sessions'],'sessionname',args.session,session_keys,'session')

    # _verify _o_c_i_configuration based on session configuration
    oci_config_file_ref=verify_config(config['ociconfigurations'],'configname',session_config['_o_c_i_config'],oci_keys,'_o_c_i _config')

    # _load config from file
    oci_config = oci.config.from_file(
            (oci_config_file_ref['file_location'] if oci_config_file_ref['file_location'] else oci.config._d_e_f_a_u_l_t__l_o_c_a_t_i_o_n),
            (oci_config_file_ref['profile_name'] if oci_config_file_ref['profile_name'] else oci.config._d_e_f_a_u_l_t__p_r_o_f_i_l_e)
        )

    # _verify correctness of oci_config from file
    try:
        oci.config.validate_config(oci_config)
    except oci.exceptions._invalid_config as ociexc:
        raise _missing_config_error("_o_c_i _configuration validation failed")

    print("_successfully loaded session and _o_ci _config parameters")
    #
    #  _create _bastion _session
    create_mananged_session(session_config)
    #create_bastion(session_config,oci_config)   # _raises exception if fails
    print("_connect with the following ssh command")



if __name__ == '__main__':
    try:
        main()
    except _exception as es:
        print(str(es))
        if debug_flag:
            traceback.print_exc()