import os
import argparse
import datetime

from oci.log_analytics import LogAnalyticsClient
from oci.object_storage import ObjectStorageClient
import oci


def remove_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} removed successfully")
    except FileNotFoundError:
        print(f"File {file_path} not found")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")

def get_namespace(config, signer):
    try:
        object_storage_client = ObjectStorageClient(config=config, signer=signer)
        namespace = object_storage_client.get_namespace().data
        return namespace
    except oci.exceptions.ServiceError as e:
        print(f"OCI Service Error fetching namespace: {e}")
        exit(1)
    except Exception as e:
       print(f"Error fetching namespace: {e}")
       exit(1)


def run_only_once_per_day():
    lock_file_path = "./la_upload.txt"
    today = datetime.date.today().strftime('%Y-%m-%d')

    if os.path.exists(lock_file_path):
        with open(lock_file_path, 'r') as f:
            last_run_date = f.read().strip()

            if last_run_date == today:
                print("Script already ran today. Exiting.")
                exit(1)
            else:
                with open(lock_file_path, 'w') as f:
                    f.write(today)


    else:
        with open(lock_file_path, 'w') as f:
            f.write(today)


## CIS csv files to upload to Logging Analytics . The LogSource should pre-exist.
log_sources = {
    'cis_summary_report.csv': 'CISSummary',
    'cis_Storage_Object_Storage_5-1-1.csv': 'CISObjectstorage',
    'cis_Storage_Object_Storage_5-1-2.csv': 'CISObjectstorage',
    'cis_Storage_Object_Storage_5-1-3.csv': 'CISObjectstorage',
    'cis_Compute_3-1.csv': 'CISCompute',
    'cis_Compute_3-2.csv': 'CISCompute',
    'cis_Compute_3-3.csv': 'CISCompute',
    'cis_Storage_Block_Volumes_5-2-1.csv': 'CISBlockvolume',
    'cis_Storage_Block_Volumes_5-2-2.csv': 'CISBlockvolume',
    'cis_Storage_File_Storage_Service_5-3-1.csv': 'CISFileStorage',
    'cis_Networking_2-1.csv': 'CISNetworking',
    'cis_Networking_2-2.csv': 'CISNetworking',
    'cis_Networking_2-5.csv': 'CISNetworking',
    'cis_Networking_2-3.csv': 'CISNetworkingNSG',
    'cis_Networking_2-8.csv': 'CISNetworkingADB',
    'cis_Logging_and_Monitoring_4-2.csv': 'CISLoggingMonitoringTopic',
    'cis_Logging_and_Monitoring_4-13.csv': 'CISLoggingMonitoringVCNLogs',
    'cis_Logging_and_Monitoring_4-16.csv': 'CISLoggingMonitoringCMK',
    'cis_Logging_and_Monitoring_4-17.csv': 'CISLoggingMonitoringObject',
    'cis_Identity_and_Access_Management_1-1.csv': 'CISIdentity',
    'cis_Identity_and_Access_Management_1-15.csv': 'CISIdentity',
    'cis_Identity_and_Access_Management_1-3.csv': 'CISIdentity',
    'cis_Identity_and_Access_Management_1-7.csv': 'CISIdentityUser',
    'cis_Identity_and_Access_Management_1-8.csv': 'CISIdentityAPIKey_90days',
    'cis_Identity_and_Access_Management_1-9.csv': 'CISIdentitySecretkey_90days',
    'cis_Identity_and_Access_Management_1-10.csv': 'CISIdentityKeyRotation',
    'cis_Identity_and_Access_Management_1-11.csv': 'CISIdentityKeyRotation',
    'cis_Identity_and_Access_Management_1-12.csv': 'CISIdentityUser',
    'cis_Identity_and_Access_Management_1-13.csv': 'CISIdentityUser',
    'cis_Identity_and_Access_Management_1-16.csv': 'CISIdentityIAM45days',
    'cis_Identity_and_Access_Management_1-17.csv': 'CISIdentityOneActiveKey',
}


##Function to upload to Logging Analytics.
def upload_logs(log_files_folder, namespace, log_group_ocid, config, signer):
    for file_name in os.listdir(log_files_folder):
        file_path = os.path.join(log_files_folder, file_name)
        if os.path.isfile(file_path):
            log_source = log_sources.get(file_name)
            if log_source is None:
                print(f"Skipping {file_name} as log source name is not defined.")
                continue

            print(f"Uploading {file_name} with log source: {log_source}...")
            try:
                with open(file_path, 'rb') as file:
                    # Initialize the LogAnalyticsClient
                    log_analytics_client = LogAnalyticsClient(config=config, signer=signer)
                    log_analytics_client.upload_log_file(
                        namespace_name=namespace,
                        log_source_name=log_source,
                        filename=file_name,
                        opc_meta_loggrpid=log_group_ocid,
                        upload_log_file_body=file,
                        content_type='application/octet-stream')

                    print(f"Uploaded {file_name}")
            except Exception as e:
                print(f"Failed to upload {file_name}: {str(e)}")


##Below function Credit to CIS landing zone script --> https://github.com/oci-landing-zones/oci-cis-landingzone-quickstart/
def create_signer(file_location, config_profile, is_instance_principals, is_delegation_token, is_security_token):
    # if instance principals authentications
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("Error obtaining instance principals certificate, aborting")
            raise SystemExit

    # -----------------------------
    # Delegation Token
    # -----------------------------
    elif is_delegation_token:

        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print("*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                print("")
                raise SystemExit

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
                    delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("* Key Error obtaining delegation_token_file")
            raise SystemExit

        except Exception:
            raise
    # ---------------------------------------------------------------------------
    # Security Token - Credit to Dave Knot (https://github.com/dns-prefetch)
    # ---------------------------------------------------------------------------
    elif is_security_token:

        try:
            # Read the token file from the security_token_file parameter of the .config file
            config = oci.config.from_file(
                oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )

            token_file = config['security_token_file']
            token = None
            with open(token_file, 'r') as f:
                token = f.read()

            # Read the private key specified by the .config file.
            private_key = oci.signer.load_private_key_from_file(config['key_file'])

            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)

            return config, signer

        except KeyError:
            print("* Key Error obtaining security_token_file")
            raise SystemExit

        except Exception:
            raise

    # -----------------------------
    # config file authentication
    # -----------------------------
    else:

        try:
            config = oci.config.from_file(
                file_location if file_location else oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(
                    config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
            return config, signer
        except Exception:
            print(
                f'** OCI Config was not found here : {oci.config.DEFAULT_LOCATION} or env varibles missing, aborting **')
            raise SystemExit


if __name__ == "__main__":
    try:

        parser = argparse.ArgumentParser(description='Upload CIS output files to Logging Analytics')
        parser.add_argument('-c', default="", dest='file_location',
                            help='OCI config file location.')
        parser.add_argument('-t', default="", dest='config_profile',
                            help='Config file section to use (tenancy profile).')
        parser.add_argument('-ip', action='store_true', default=False,
                            dest='is_instance_principals', help='Use Instance Principals for Authentication.')
        parser.add_argument('-dt', action='store_true', default=False,
                            dest='is_delegation_token', help='Use Delegation Token for Authentication in Cloud Shell.')
        parser.add_argument('-st', action='store_true', default=False,
                            dest='is_security_token', help='Authenticate using Security Token.')

        parser.add_argument('-d', '--directory', help='Absolute Folder path', required=True)
        parser.add_argument('-lg', '--loggroup', help='LogGroup Id', required=True)
        args = parser.parse_args()

        log_files_folder = args.directory

        log_group_ocid = args.loggroup

        outer_config, outer_signer = create_signer(args.file_location, args.config_profile, args.is_instance_principals,
                                               args.is_delegation_token, args.is_security_token)
        namespace = get_namespace(outer_config,outer_signer)
        run_only_once_per_day()

        upload_logs(log_files_folder, namespace, log_group_ocid, outer_config, outer_signer)

    except Exception as e:
        remove_file("./la_upload.txt")
        print(f"Exception occurred during log upload: {e}")
        exit(1)