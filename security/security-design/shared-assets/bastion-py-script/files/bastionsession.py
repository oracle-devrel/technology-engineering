
import argparse
import logging
import oci
import platform
import asyncio
import json
import time
import constants as const


"""Bastion Service script

Minimum python version 3.7,  asyncio.run

 Script to create a session for a named bastion services, and
 generates the ssh command for connection to the session

 The Session have two formats:
 - Just print the commands
 - Fork a bash shell and run the commands. In the latter case it waits
   for the session to expire and recreates a new, x number of times
   for PORT type SSH session, start a ssh tunnel, for managed session,
   connect to the target

 Command line:
 --configfile  name of json file with named session and OCI CLI config info
 --session     named session, section in config file
 --exec        executes the ssh command and establishes the ssh connection
 --loglevel    logging level, info or debug. default info
 --log         logging output file or stdout, defaul stdout



  If File location is missing, the default config will be used.
  If profile_name is missing DEFAULt fill be used
  If the OCIconfigname parameter is missing in the session section,
  DEFAULT from DEFAULT location will be used.

Documentation for inspiration:

https://www.ateam-oracle.com/post/openssh-proxyjump-with-oci-bastion-service
https://fluffyclouds.blog/2022/06/02/create-oci-bastion-sessions-with-python-sdk/
"""

"""
  Structure of config file
{ const.SESSIONS:[
                { <session one points to ociconfigurations>},
                { <session two points to ociconfigurations>}],
  const.OCICONFIGURATIONS: [
                { <ociconfiguration one>},
                { <ociconfiguration one>}]
}
For contents of sessions and ociconfiguration please refer to readme file

Copyright (c) 2025 Oracle and/or its affiliates

"""


#
# Globals
#
__version__ = "1.26.02.25"
__author__ = "Inge Os"
#
# Default logger
logger = logging.getLogger(__name__)
#
# Class definitions/extensions
#


#
# GenericError
#
# Extension of Exception class, thrown when any Exception is raised
# and caught or any API error/Exception occurs
#
class GenericError(Exception):
    """
    Generic Exception for clean close of resources.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Generic Exception raised"):
        """init function for extended class"""
        self.message = message
        super().__init__(self.message)


#
# MissingConfigError
#
# Extension of Exception class, thrown in case of errors with the config file
class MissingConfigError(Exception):
    """
    Missing configuration Error
    thrown when the JSON file misses a mandatory parameter,
    or a parameter is invalid

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Value missing in configuration"):
        """init function for extended class"""
        self.message = message
        super().__init__(self.message)


#
# get_validated_config_entry
#
# Iterate over JSON array (list) and return first JSON object (dict)
# where JSON element with name search_key_name matches search_key_value
#
# If a matching dict is found, iterate over it and verify existence of
# all mandator values
# Finally iterate over it and add any missing non mandatory values
#
# Returns a complete dict with valid entry with all default values for
# non mandatory values
#
# Raises MissingConfigError if no entry with search_key_value is found,
# or mandatory field is missing
#
# Input Parameters:
#   config_list, list of dict (JSON Array of JSON Objects)
#   search_key_name, string, key to look up in a dict in a list entry
#   search_key_value, string, value to math if key exists in dict
#   required_keys, list, when the first dict is found in config_list,
#   verify that all keys in required keys lists exists in dict
#   non_manadatory_key_values, dict, key/value pair.
#   If key names is missing in the dict, add key/value (will be default value)
#
# Return value:
#   dict of config values, valid dict is found in config_list
#   False matching search_key/search_value was not found
# Exception:
#   MissingConfigError, matching search_key/search_value
# was not found, or required key is missing


def get_validated_config_entry(
    config_list,
    search_key_name,
    search_key_value,
    required_keys,
    non_manadatory_key_values,
):
    """Function validates if all mandatory values exist in a
       json config object"""
    #
    # To be nice collect all session names and print them if not found
    session_names = []
    #
    # Lookup the entry in entry list that matches search_key_name
    # and search_key_value
    current_list_entry = False
    for idx, config_entry in enumerate(config_list):
        # Lookup entry in list, pull it if it matches the search
        if config_entry[search_key_name] == search_key_value:
            #
            current_list_entry = config_entry
            break
        session_names.append(config_entry[search_key_name])
    #
    # At this point currentSession = False if no session configs
    # matches SessionName
    if current_list_entry is False:
        # In case of typo, to be nice just dump the session names found
        print("Known session names:")
        for cname in session_names:
            print(cname + " ", end="")
        print("\n")
        #
        # raise exception and exit
        #
        raise MissingConfigError(
            "Missing configuration entry key:"
            + search_key_name
            + " in configuration file"
        )
    #
    # Iterate and verify all required_keys
    for required_key in required_keys:
        if not (required_key in config_entry):
            raise MissingConfigError(
                "Key: "
                + required_key
                + " is missing in "
                + search_key_value
                + " confguration"
            )
    #
    # Iterate and populate all non mandatory values with defaults
    if non_manadatory_key_values is not None:
        for key in non_manadatory_key_values:
            if key not in config_entry:
                config_entry[key] = non_manadatory_key_values[key]
    #  Return found DICT (JSON leaf node from JSON Array/list)
    return current_list_entry


#
# Validates key elements of the structure of config entry of type
# "session" or const.OCICONFIG
# Current code only simple verification of INT/string for some
# session config keys, and a few
# mandatory parameters. For more in-depth sanity check of the
# config key/values, add the code here
# The function assumes an earlier verification of mandatory and
# non_mandatory dict key's presence
#
# Input Parameters:
#   config, dict of attributes to be verified
#   config_type, session" or const.OCICONFIG
#   int_list, list of dict keys that should be converted from str to int
#
# Return value:
#   True, verification and str to int conversion passed
#   False if an error occurs
# Exception:
#   GenericError, if sessionType is not legal or if bastion
# public key can't be retreived
#
def valdate_config(config, config_type, int_list):
    """Function sanity checks and validates some key config entries, converts
       to int where string/int is optional"""
    if config_type == const.SESSION:
        # Validate session_type

        if (
            config[const.SESSIONTYPE] != const.MANAGED_SSH
            and config[const.SESSIONTYPE] != const.PORT_FORWARDING
        ):
            raise GenericError(
                "Invalid session type, permitted values are  \
                 MANAGED_SSH or PORT_FORWARDING, current value: "
                + config[const.SESSIONTYPE]
            )

        # Get the Public key from file

        try:
            with open(config[const.BASTIONPUBLICKEYFILE], "r") as f:
                config[const.PUBKEYCONTENT] = f.read()
            f.close()
        except Exception:
            raise GenericError("Failed to load bastion public key")

    elif config_type == const.OCICONFIG:
        # No real verification, leave it to OCI SDK,
        # only allocate proper default values
        config[const.CONFIGFILENAME] = (
            config[const.CONFIGFILENAME]
            if const.CONFIGFILENAME in config
            else oci.config.DEFAULT_LOCATION
        )
        config[const.PROFILENAME] = (
            config[const.PROFILENAME]
            if const.PROFILENAME in config
            else oci.config.DEFAULT_PROFILE
        )
    else:
        logger.error("Unknown config type: " + config_type)
        return False

    #
    # Verify numeric conversion (integers)
    # Only verifies INT values from config, config accepts both INT
    # and string formats. OCI SDK requires INT
    # Leave the rest to the OCI SDK
    #
    # Config file accepts both styles, ie."3600" and 3600 as int
    #
    if int_list is not None:
        for key in int_list:
            if not isinstance(config[key], int):
                try:
                    config[key] = int(config[key])
                except Exception:
                    raise GenericError(
                        "Integer conversion for :"
                        + key
                        + " "
                        + config[key]
                        + " failed"
                    )
    #
    #  All good
    #
    return True


#
#  create_single_session
#
#  creates a bastion session with the SDK (API)
#  Bastion session will normally take some time. If initial call is
# successful the bastion state is "CREATING"
#  and when the creation is complete and successful,
# it changes state to "ACTIVE"
#  The code loops and sleeps until max iterations is reached or
# "ACTIVE" state is reached
#
# Input Parameters:
#   session_config, attributes from session configuration from config file
#   bastion_client, alloccated OCI BAstionClient
#
# Return value:
#   bastion session response data or
#   False if an error occurs
#
def create_single_session(session_config, bastion_client):
    """Function creates a single bastion session of type
       defined in session_config, assumes valid SDK client"""
    try:
        # Create bastion session, SDK exeption is raised if it fails
        create_session_response = bastion_client.create_session(
            create_session_details=oci.bastion.models.CreateSessionDetails(
                bastion_id=session_config[const.BASTIONOCID],
                target_resource_details=
                oci.bastion.models.CreateManagedSshSessionTargetResourceDetails(
                    session_type=session_config[const.SESSIONTYPE],
                    target_resource_operating_system_user_name=session_config[
                        const.OSUSERNAME
                    ],
                    target_resource_id=session_config[const.TARGETOCID],
                    target_resource_private_ip_address=session_config[
                        const.TARGETPRIVATEIP
                    ],
                    target_resource_port=session_config[const.TARGETPORT],
                ),
                key_details=oci.bastion.models.PublicKeyDetails(
                    public_key_content=session_config[const.PUBKEYCONTENT]
                ),
                display_name=session_config[const.SESSIONDISPLAYNAME],
                # display_name='abc',
                key_type=const.PUBLIC,
                session_ttl_in_seconds=session_config[const.TIMETOLIVE],
            )
        )
        #
        # At this point no exeption is raised, fetch the session data
        # The state will be "creating"
        #
        get_session_response = bastion_client.get_session(
            session_id=create_session_response.data.id
        )
        logger.debug(get_session_response.data)
    except Exception as e:
        print("Failed to create Bastion session, review logfile")
        logger.error("Failed to create Bastion session")
        logger.error(str(e), exc_info=True)
        return False
    #
    # Loop until max time and wait for session to be migrated
    # from CREATING to ACTIVE
    # The loops iterates maxWaitCount times and sleep waitRefresh
    # seconds between each iteration
    #
    active_session = False
    count = 0
    try:
        while active_session is False and count < session_config[const.MAXWAITCOUNT]:
            get_session_response = bastion_client.get_session(
                session_id=create_session_response.data.id
            )
            if get_session_response.data.lifecycle_state == const.STATE_ACTIVE:
                print("Session has been created and is ACTIVE")
                active_session = True
                break
            else:
                print(
                    "Waiting for session state to be active. Current State .."
                    + str(get_session_response.data.lifecycle_state)
                )
                time.sleep(session_config[const.WAITREFRESH])
                count = count + 1
    except Exception as e:
        print(
            "Failed to create Bastion session,  \
                active session poll failed, review logfile"
        )
        logger.error("Failed to create Bastion session,  \
                     active session poll failed")
        logger.error(e, exc_info=True)
        return False
    #
    # Verify if loop was exited due to ACTIVE state reached
    #
    if active_session is False:
        #
        # Nope active state not reached
        #
        print(
            "Session do not achive active-state within timelimit.  \
                Current State: "
            + str(get_session_response.data.lifecycle_state)
        )
        logger.error(
            "Session do not achived activestate  \
                within timelimit. Current State:",
            str(get_session_response.data.lifecycle_state),
        )
        return False
    return get_session_response.data


#
# Generate the ssh or putty command for connecting to the bastion or
# start the tunnel
# The command skeleton is derived from the OCI SDK return object after a
# successful session creation
#
# Input Parameters:
#
#   bastion_session  = response object from createSession SDK, DICT with
# const.COMMAND entry
#   session_config, attributes from session configuration from config file
#
# Return value:
#   cmd, dict with const.SERVERSIDE command for tunnel and direct connect,
# const.CLIENTSIDE command for connecting to the tunnel
#
#
def get_command(bastion_session, session_config):
    """Function to retrieve valid command as generated by bastion SDK"""
    cmd = {}
    session_cmd = bastion_session.ssh_metadata[const.COMMAND]
    print("Port managed start cmd")
    #
    # The bastion service might add a note to the end of the command.
    # Supress the note
    #
    if session_cmd.find(" # ") > -1:
        session_cmd = session_cmd.split(" # ")[0]
    #
    # Select session type, either port forwarding or
    # managed (through the agent)
    #
    if session_config[const.SESSIONTYPE] == const.PORT_FORWARDING:
        print("Port forwarding start cmd")
        print(session_cmd)
        tunnel_cmd = session_cmd.replace(
            "<privateKey>", session_config[const.BASTIONPRIVATEKEYFILE]
        )
        tunnel_cmd = tunnel_cmd.replace("<localPort>",
                                        str(session_config[const.LOCALPORT]))
        #
        # Setup the correct client comamnd for ssh or putty
        if session_config[const.SSHCOMMAND] == const.SSH:
            client_cmd = (
                "ssh -i "
                + session_config[const.TARGETPRIVATEKEYFILE]
                + " -p "
                + str(session_config[const.LOCALPORT]))
            if session_config[const.SSHCOMMANDOPTIONS] is not None:
                client_cmd = client_cmd + " " +  \
                    session_config[const.SSHCOMMANDOPTIONS]
            client_cmd = (client_cmd
                          + " "
                          + session_config[const.OSUSERNAME]
                          + "@"
                          + "localhost")
            cmd[const.CLIENTSIDE] = client_cmd
        else:
            client_cmd = (
                "putty -i "
                + session_config[const.TARGETPRIVATEKEYFILE]
                + " -P "
                + str(session_config[const.LOCALPORT])
                + " "
                + session_config[const.OSUSERNAME]
                + "@"
                + "localhost"
            )
            cmd[const.CLIENTSIDE] = client_cmd
        #
        # Build serverside command
        #
        if session_config[const.SSHCOMMAND] == const.SSH:
            cmd[const.SERVERSIDE] = tunnel_cmd
            if session_config[const.SSHCOMMANDOPTIONS] is not None:
                cmd[const.SERVERSIDE] = cmd[const.SERVERSIDE] + " " \
                    + session_config[const.SSHCOMMAND]
            return cmd
        else:
            #
            # Adjust serverside cmd for putty.exe
            #
            cmd[const.SERVERSIDE] = (
                (tunnel_cmd.replace("ssh", "putty", 1))
                .replace("-N", "-N -ssh")) \
                .replace("-p 22", "")
            return cmd
    else:
        #
        # Managed session through the agent
        #
        print("Port managed start cmd")
        print(session_cmd)
        session_cmd = (
            session_cmd.replace("<privateKey>",
                                session_config[const.TARGETPRIVATEKEYFILE])
        ).replace("<localPort>", str(session_config[const.TARGETPORT]))
        if session_config[const.SSHCOMMAND] == const.SSH:
            return {const.SERVERSIDE: session_cmd}
        else:
            cmd[const.SERVERSIDE] = (
                (session_cmd.replace("ssh", "putty.exe", 1))
                .replace("-N", "-N -ssh")).replace("-p 22", "")
            return {cmd}


#
# process_command_line_args
#
# Using the args_parser to process the command line arguments
# Simple verification of the command-line arguments
# Opens logger
# JSON parses bastion session
#
# Input Parameters:
#   process_command_line_args, default value of config file location
# Return value:
#   dict with two entries cmdargs:
#       cmdargs: args object
#       bastionconfig: config from config file
#
#   Exception:
#       GenericError, raised if --session is missing, opening of log file
#           raises IO error
#           opening of session config file raises error, or JSON parse
#           of session config file fails
def process_command_line_args(default_bastion_config_file):
    """Function that process and validates command-line arguments"""
    # Parse args
    args_parser = \
        argparse.ArgumentParser(description="Bastion session manager")
    args_parser.add_argument(
        "--configfile",
        default=default_bastion_config_file,
        type=str,
        help="Bastion Config File",
    )
    args_parser.add_argument(
        "--session", default=None, type=str,
        help="name of session from session config"
    )
    args_parser.add_argument(
        "--exec", action="store_true", help="Forks new shell with ssh command"
    )
    args_parser.add_argument(
        "--loglevel",
        default="info",
        type=str,
        help="Logging level, permittable values are: INFO or DEBUG",
    )
    args_parser.add_argument(
        "--log",
        default=None,
        type=str,
        help="target for the logger, default stderr, filename|-   \
              - redirects to stderr",
    )
    args = args_parser.parse_args()
    #
    # Configuring logging level, for simplicity no check for INFO or DEBUG only
    #
    log_level = getattr(logging, args.loglevel.upper(), None)
    if args.log is None or args.log == "-":
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(level=log_level, filename=args.log, filemode="w")
    logging.info("Open logfile")
    print(
        "Open logfile: "
        + ("stderr" if args.log is None or args.log == "-" else args.log)
    )
    #
    #  Process bastion configuration
    #
    bastion_config_file = args.configfile
    #
    # Open config file
    #
    try:
        config_file = open(bastion_config_file)
    except Exception:
        raise GenericError(
            "Load of configuration file: " + bastion_config_file + " failed"
        )
    try:
        config = json.load(config_file)
        config_file.close()
    except Exception as ConfigError:
        logger.error("Configuration load error")
        logger.error(ConfigError)
        raise GenericError(
            "JSON Parse of configuration file: "
            + bastion_config_file
            + " failed"
        )
    #
    # Session name is the only argument that is mandatory
    #
    if args.session is None:
        logger.error("Missing --session")
        raise GenericError("Missing --session command-line argument")
    #
    # At this point, the basic command-line args has been processed,
    # log file opened and configuration file
    # read as a valid JSON input
    #
    return {const.CMDARGS: args, const.BASTIONCONFIG: config}


#
# process_bastion_config
#
# Input Parameters:
#   config, dict representing the JSON config file
#   session_name, name of session from command-line
# Return value:
#   dict with session config and OCI config
#
#   Exception:
#       MissingConfigError if any the session name, OCI config
# name is not found, an missing mandatory values
#           or str to int conversion fails
#
def process_bastion_config(config, session_name):
    """Validates all configuration elements and look up
       correct OCI SDK config"""
    #
    # Verify integrity of config file and find the JSON dict for bastion
    # session and OCI SDK configuration
    #
    # List of valid and mandatory entries in the sessions object
    # from JSON config file
    #
    mandatory_session_keys = [
        const.SESSIONNAME,
        const.SESSIONTYPE,
        const.OCICONFIG,
        const.BASTIONOCID,
        const.BASTIONPUBLICKEYFILE,
        const.SESSIONDISPLAYNAME,
        const.TARGETOCID,
        const.TARGETPRIVATEIP,
        const.OCIREGION,
    ]

    # dict of non mandatory keys,in the sessions object from JSON,
    # with default values
    non_mandatory_session_keys = {
        const.BASTIONPRIVATEKEYFILE: "<bastion private key file>",
        const.TARGETPRIVATEKEYFILE: "<target private key file>",
        const.TARGETPORT: "<target port>",
        const.LOCALPORT: "<local tunnel port>",
        const.OSUSERNAME: "<target OS username>",
        const.TIMETOLIVE: "3600",
        const.MAXWAITCOUNT: "10",
        const.WAITREFRESH: "10",
        const.SSHCOMMAND: "ssh",
        const.MAXSESSIONS: "1",
    }
    #
    # List of valid and mandatory entries in the ociconfigurations object
    # from JSON config file
    #
    mandatory_oci_keys = [const.CONFIGNAME,
                          const.CONFIGFILENAME,
                          const.PROFILENAME]
    #
    # List of valid and non-mandatory entries in the ociconfigurations
    # object from JSON config file
    #
    non_mandatory_oci_keys = None  # Not required but for the readability
    #
    # List of parameters that must be of type int,
    # otherwise SDK call will fail,
    # port numbers are only used
    # for generation of command line, so non int port numbers
    # does not affect the SDK
    #
    session_int_list = {
        const.TIMETOLIVE,
        const.MAXWAITCOUNT,
        const.WAITREFRESH,
        const.TARGETPORT,
        const.MAXSESSIONS,
    }
    #
    # The OCI section of the configuration does not require any string
    # to in conversion
    #
    oci_int_list = None

    if not (const.SESSIONS in config.keys()):
        raise MissingConfigError("Session key is missing in configuration")
    if not (const.OCICONFIGURATIONS in config.keys()):
        raise MissingConfigError("Ociconfigurations key is missing in configuration")
    #
    # Verify configurations, verify all mandatory elements and add defaults
    # for non mandatory elements
    #
    # Verify Session
    #
    session_config = get_validated_config_entry(
        config[const.SESSIONS],
        const.SESSIONNAME,
        session_name,
        mandatory_session_keys,
        non_mandatory_session_keys,
    )
    if session_config is False:
        logger.error("get_validated_config_entry for sessions failed")
        raise MissingConfigError("get_validated_config_entry for sessions failed")
    #
    # Verify OCIConfiguration
    #
    oci_config = get_validated_config_entry(
        config[const.OCICONFIGURATIONS],
        const.CONFIGNAME,
        session_config[const.OCICONFIG],
        mandatory_oci_keys,
        non_mandatory_oci_keys,
    )
    if oci_config is False:
        logger.error("get_validated_config_entry for OCI config failed")
        raise MissingConfigError("get_validated_config_entry for OCI config failed")
    #
    # Sanity check session config, and convert named entries to int
    #
    if not valdate_config(session_config, const.SESSION, session_int_list):
        raise MissingConfigError("Session config validation failed")
    #
    # Sanity check OCI config, and convert named entries to int
    #
    if not valdate_config(oci_config, const.OCICONFIG, oci_int_list):
        raise MissingConfigError("OCIconfig validation failed")

    return {const.SESSIONCONFIG: session_config, const.OCICONFIG: oci_config}


#
# execBastionCmd
#
# executes the generated bastion cmd asynchronously
#
# Input Parameters:
#
#   bastion_session  = response object from createSession SDK
#   cmd, session creation command
#   bastion_client, allocated client from successful signin process
#   with the SDK
#
# Return value:
#
def execBastionCmd(bastion_session, bastion_client, cmd):
    """Function to fork new shell and execute
       bastion command as generated by SDK"""
    #
    # Number of retry, hardcoded
    #
    max_retry = 10

    ttl = bastion_session.session_ttl_in_seconds
    logger.debug("TTL of the session is : " + str(ttl))
    wait_refresh = ttl / max_retry

    print("Next session will be created after " + str(ttl) + " seconds")
    print("Connection to target with active bastion session")
    #
    # Python code for PY 3.8 or above
    # asynio.run requires PY38,
    # ref: https://superfastpython.com/asyncio-run-program/
    #
    # https://superfastpython.com/python-coroutine/
    # If the ssh command is executed to quick it will fail
    #
    time.sleep(10)
    asyncio.run(exec_command(cmd))
    #
    # PY 3.7 or below
    # Added as prereq Python 8
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(exec_command(cmd))
    #
    # Waiting for session to be expired
    #
    wait_for_session_deletion(
        bastion_session.id, wait_refresh, max_retry, bastion_client
    )
    print("session expired")
    logger.debug("Session Details: " + str(bastion_session.id))


#
# exec_command
#
#  Forks off a new async shell and executes the command in the new shell
#  Implemented as a coroutine
#  Waits for output
#
# Input Parameters:
#   String, cmd, command to be executed async
#
# Return value:
#
async def exec_command(cmd: str):
    """Function to async fork off a new shell"""
    proc = await asyncio.create_subprocess_shell(
        cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logging.error(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        logging.info(f"[stdout]\n{stdout.decode()}")
    if stderr:
        logging.error(f"[stderr]\n{stderr.decode()}")
    if proc.returncode != 0:
        print("Fork off new shell with PID: " + str(proc.pid))


#
# wait_for_session_deletion
#
# Check the status of previous session and wait for the session to deleted.
#
# Input Parameters:
#
#   session_id, OCID of session from session creation
#   bastion_client, allocated client from API call
#   wait_refresh, wait time before rechecking status
#   max_retry, max attempt before returning
#
# Return value:
#
def wait_for_session_deletion(session_id,
                              wait_refresh,
                              max_retry,
                              bastion_client):
    """Function to wait for bastion session to be
       expired and fork new if applicable"""
    session_deletion = False
    tries = 0
    #
    # max_retry = 20
    #
    while session_deletion is False and tries < max_retry:
        get_session_response = \
            bastion_client.get_session(session_id=session_id)
        if get_session_response.data.lifecycle_state != const.STATE_DELETED:
            print(
                "Previous session still active. Current status is  "
                + str(get_session_response.data.lifecycle_state)
                + " wait for "
                + str(wait_refresh)
                + " seconds"
            )
            print("Deleting the session..............")
            delete_session_response = bastion_client.delete_session(
                session_id=session_id
            )
            print(delete_session_response.headers)
            time.sleep(wait_refresh)
            tries = tries + 1
        else:
            print("The previous session has been deleted")
            session_deletion = True
            break


#
# create_sessions
#
# Creates one or more consecuive bastion sessions
#  Create Bastion Session
#  if exec_ssh is true,  A new session is created when the past expires
#  Iterate until maxSessions is reached or session creation fail
#
# Input Parameters:
#   config, dict representing the JSON config file
#   exec_ssh, True if ssh command should be forked,
#
# Return value:
#   Boolean TRUE, successfully created session(s)
#   Boolean FALSE, session creation failed
#
#   Exceptions:
#
def create_sessions(config, exec_ssh):
    """Function that orchestrate creation of bastion sessions
       and if required starts the sessions"""
    session_config = config[const.SESSIONCONFIG]
    oci_config = config[const.OCICONFIG]
    #
    # Allocate OCI bastion_client
    # load the OCI config from file, default parameters is set prior
    # Leave to SDK to throw any exceptions
    #
    try:
        current_oci_config = oci.config.from_file(
            oci_config[const.CONFIGFILENAME], oci_config[const.PROFILENAME]
        )
        #
        # Initialize service client, SDK exeption is raised if it fails
        #
        bastion_client = oci.bastion.BastionClient(current_oci_config)
    except Exception as e:
        logger.error("Failed to allocate OCI BastionClient")
        logger.error(e, exc_info=True)
        return False
    #
    # Process exec_ssh command only
    #
    if not exec_ssh:
        #
        # Create just one session and print the command
        #
        bastion_session = create_single_session(session_config, bastion_client)
        if isinstance(bastion_session, bool) and bastion_session is False:
            print("Creation of bastion failed, review logfile")
            logger.error("Creation of bastion failed", bastion_session)
        elif bastion_session.lifecycle_state == const.STATE_ACTIVE:
            print("Bastion session created")
            logger.debug("Bastion session created %s", str(bastion_session))
            cmd = get_command(bastion_session, session_config)
            if const.CLIENTSIDE in cmd:
                print("ssh tunnel command:")
                print(cmd[const.SERVERSIDE])
                print("Client Connect: ")
                print(cmd[const.CLIENTSIDE])
            else:
                print("connect with:")
                print(cmd[const.SERVERSIDE])
            return True
        else:
            print("Bastion session not ACTIVE"
                  + bastion_session.lifecycle_state)
            logger.debug("Bastion session not ACTIVE", bastion_session)
    else:
        #
        # Create maxSession sessions and exec the bastion command
        # When the session expires, recreate new session
        #
        session_count = 0
        while session_count <= session_config[const.MAXSESSIONS]:
            bastion_session = \
                create_single_session(session_config, bastion_client)
            if isinstance(bastion_session, bool) and bastion_session is False:
                print("Creation of bastion failed, review logfile")
                logger.error("Creation of bastion failed", bastion_session)
                break
            elif bastion_session.lifecycle_state == const.STATE_ACTIVE:
                print("Bastion session created")
                cmd = get_command(bastion_session, session_config)
                print("Forking shell with ssh")
                if const.CLIENTSIDE in cmd:
                    print("ssh tunnel created with command:")
                    print(cmd[const.SERVERSIDE])
                    print("Connect to the client: ")
                    print(cmd[const.CLIENTSIDE])

                logger.debug("Bastion session created %s",
                             str(bastion_session))
                try:
                    execBastionCmd(
                        bastion_session,
                        bastion_client,
                        cmd[const.SERVERSIDE],
                    )
                    return True
                except KeyboardInterrupt:
                    logging.error("Keyboard Interrupt user pressed ctrl-c button.")
                    print("Cancelled by user, terminating")
                    return 1
            else:
                print("Bastion session not ACTIVE" +
                      bastion_session.lifecycle_state)
                logger.debug("Bastion session not ACTIVE", bastion_session)
                break
            session_count = session_count + 1
    return False


#
# main
#
#  Main function
#
#  Open and reads configfile
#  verifies JSON structure
#  Calls the create session API
#  and upon success, generates example ssh or putty syntax
#  If desired and upon successful creation the script can wait and recreate
# the session when it expires x number of times
#
# 	Exception
# 		throws MissingConfigError if either configfile can't be read or JSON
#       parse error. Underlying exceptions are passed on to caller
#
def main():
    """Main entry point, orkestrates all functions"""
    print("Bastion session manager " + __version__ + "\n")
    #
    # Get bastion config
    #
    os_name = platform.system().lower()
    if os_name == const.OS_LINUX:
        default_bastion_config_file = "/home/users/demo/config.json"
    elif os_name == const.OS_WINDOWS:
        default_bastion_config_file = "c:\\temp\\bastion.json"
    elif os_name == 'darwin':
        default_bastion_config_file = "/home/users/demo/config.json"
    else:
        print("Platform: " + os_name + " is not supported")
        raise GenericError("Unsupported platform")
    #
    # process command-line arguments, open log file read and parse config
    # file, any exception passed up in the stack
    #
    all_config = process_command_line_args(default_bastion_config_file)
    args = all_config[const.CMDARGS]
    #
    # Process JSON/dict with all config data
    #
    config = process_bastion_config(
        all_config[const.BASTIONCONFIG], all_config[const.CMDARGS].session
    )
    session_config = config[const.SESSIONCONFIG]
    oci_config = config[const.OCICONFIG]

    if session_config[const.SESSIONTYPE].upper() == \
        const.MANAGED_SSH and (args[const.EXEC]):
        raise MissingConfigError("OCIconfig validation failed")
    #
    # Then we are good
    #
    print("Successfully loaded session and OCI Config parameters")
    logger.debug("session configuration", session_config)
    logger.debug("OCI configuration", oci_config)

    #
    #  Create Bastion Session
    #
    if create_sessions(config, all_config[const.CMDARGS].exec):
        print("Successfully completed bastion session(s)")
    else:
        print("Bastion session returned error, please review logfile")


#
#  Main entry point
#
if __name__ == "__main__":
    try:
        main()
    except Exception as es:
        print("Runtime error, review log for info")
        logger.error(es, exc_info=True)
