#!/bin/bash
###############################################################################
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Olaf Heimburger
#
VERSION=260708
GRAAL_VERSION=25.1.3
SHA_VERSION=260708
FILE_SHA512_CHECKSUM="https://github.com/oracle-devrel/technology-engineering/raw/main/oci-and-db/foundation/ciso/security-design/shared-assets/oci-security-health-check-standard/files/resources/oci-security-health-check-standard-"${SHA_VERSION}".sha512"
OCI_CONFIG_FILE="${OCI_CLI_CONFIG_FILE:-$HOME/.oci/config}"

test_internet_access() {
    wget --timeout=5 --tries=2 -q --spider ${FILE_SHA512_CHECKSUM}
    error_code=$?
    if [ $error_code -gt 0 ]; then
        HAS_INTERNET_ACCESS=0
    fi
}

debug() {
    if [ $DEBUG -eq 1 ]; then
        echo 'DEBUG: ' $*
    fi
}

check_directories() {
    if [ ! -e ${ASSESS_DIR}/scripts ]; then
        printf "ERROR: Directory 'scripts' missing!\n"
        exit 1
    fi
    SCRIPTS_DIR="${ASSESS_DIR}/scripts"

    if [ ! -e ${SCRIPTS_DIR}/cis_reports ]; then
        printf "ERROR: Directory 'cis_reports' missing!\n"
        exit 1
    fi
    CIS_SCRIPT_DIR="${SCRIPTS_DIR}/cis_reports"
    CIS_SCRIPT_NAME="cis_reports.py"
    CIS_SCRIPT="${CIS_SCRIPT_DIR}/${CIS_SCRIPT_NAME}"

    if [ ${IS_ADVANCED} -eq 1 -a ! -e ${SCRIPTS_DIR}/showoci ]; then
        printf "ERROR: Directory 'showoci' missing!\n"
        exit 1
    fi
    SHOWOCI_SCRIPT_DIR="${SCRIPTS_DIR}"
    SHOWOCI_SCRIPT_NAME="showoci.py"
    SHOWOCI_SCRIPT="${SHOWOCI_SCRIPT_DIR}/${SHOWOCI_SCRIPT_NAME}"
}

check_python_version() {
    _W_=$(which python3 | wc -c)
    if [ ${_W_} -le 0 ]; then
        printf "ERROR: Please install python3 first! Use a version higher than 3.9.\n"
        exit 1
    fi
    PYTHON_VERSION=$(${PYTHON_CMD} --version | sed -e 's,Python ,,g')
    _V_=$(echo -n ${PYTHON_VERSION} | sed -e 's,Python ,,g' -e 's;GraalPy ;;g' -e 's;\.;;g' -e 's; (.*)$;;g')
    if [ 39 -ge ${_V_} ]; then
        printf "ERROR: Please upgrade your Python verion higher than 3.9.\n"
        exit 1
    fi
}

usage() {
    printf "\nUsage: $0 [-h] [-ip] [-st] [-cf config_file] [-r region_name] [-t tenancy_name]\n"
    if [ $IS_ADVANCED -eq 1 ]; then
        printf "          [-s|--showoci options] [-c|--cis options] \n"
    else
        printf "          [-c|--cis options]\n"
    fi
    printf "          [--no-zip] [--zip-protect] [--verbose] [-v|--version] [--redact]\n"
    printf " -h                                 -- This message.\n"
    printf " -ip                                -- Use instance principal for authentication.\n"
    printf " -st                                -- Use OCI security token for authentication.\n"
    printf " -c                                 -- Run cis_report only.\n"
    printf " -s                                 -- Run showoci only.\n"
    printf " -cf                                -- OCI config file (defaults to "'$HOME/.oci/config'").\n"
    printf " --cis options                      -- Run cis_report only and provide additional options.\n"
    printf "                                       For example, --cis '-h' shows available options.\n"
    printf "                                       The options -dt, -ip, -t, --regions are detected automatically and are not required.\n"
    if [ $IS_ADVANCED -eq 1 ]; then
        printf " --showoci options                  -- Run showoci only and provide additional options.\n"
        printf "                                       For example, --showoci '-h' shows available options.\n"
        printf "                                       The options -jf, -ip, -t, -rg, -xlsx_nodate, --version are detected automatically and are not required.\n"
        printf " --exclude <comma_seperated_list>   -- Option for showoci. List of excluded services.\n"
    fi
    printf " --redact                           -- Redact OCIDs in output files.\n"
    printf " --no-zip                           -- Do not create a ZIP file for the contents pf the output directory.\n"
    printf " --zip-protect                      -- Encrypt ZIP file with a password of your choice.\n"
    printf " --verbose                          -- Print more details.\n"
    printf " -r|--region region_name            -- Run assess.sh on region region_name only.\n"
    printf " -t|--tenancy tenancy_configuration -- Specify a name of the tenancy.\n"
    printf "                                       Configuration in $HOME/.oci/config (defaults to 'DEFAULT') will be used.\n"
    printf " -v|--version                       -- Show the version numbers of the scripts used.\n"
    exit 1
}

check_config_for_profile() {
    _wc_=$(grep '\['"$1"'\]' $OCI_CONFIG_FILE)
    if [ -z "${_wc_}" ]; then
        printf "ERROR: Profile name %s is not present in the OCI config file (%s)!\n" ${TENANCY} ${OCI_CONFIG_FILE}
        exit 1
    fi
}

get_oci_config_value() {
  local profile="$1"
  local key="$2"
  local file="${OCI_CLI_CONFIG_FILE:-$HOME/.oci/config}"

  awk -F'=' -v profile="[$profile]" -v key="$key" '
    $0 == profile { found=1; next }
    /^\[/ { found=0 }
    found && $1 ~ key {
      gsub(/^[ \t]+|[ \t]+$/, "", $2)
      print $2
      exit
    }
  ' "$file"
}

check_jwt_expiry() {
    local jwt="$1"
    local BASE64_DECODE="base64 -d"
    if [ "${OS_TYPE}" == 'Darwin' ]; then
        BASE64_DECODE="base64 -D"
    fi

    # Extract payload (2nd part)
    local payload="${jwt#*.}"
    payload="${payload%%.*}"

    # Convert base64url to base64
    payload="${payload//-/+}"
    payload="${payload//_/\/}"    
    payload="${payload}$(printf '=%.0s' $(seq 1 "$pad"))"

    # Decode JSON payload
    local json="$(printf '%s' "$payload" | base64 -d 2>/dev/null)"

    # Extract "exp" value using bash tools
    local exp="$(printf '%s\n' "$json" | grep -o '"exp":[0-9]*' | cut -d: -f2)"

    # Current time
    local now="$(date +%s)"

    if [[ "$exp" =~ ^[0-9]+$ ]]; then
        if (( now < exp )); then
            printf "INFO: Security Token is valid for $(( (exp - now) / 60)) minutes.\n"
        else
            printf "ERROR: Security Token is expired!\n"
            printf "ERROR: Please re-authenticate using\nERROR:  'oci session authenticate --tenancy-name tname --region-name rname --identity-provider-name dname --session-expiry-time-in-minutes mins --profile-name pname'\n"
            printf "ERROR: For details see https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/session/authenticate.html\n"
            exit 1
        fi
    else
        printf "ERROR: Could not parse expiry date of Security Token.\n"
        exit 1
    fi
}

show_version() {
    printf "INFO: %s version %s\n" "$0" "${VERSION}"
    ${PYTHON_CMD} ${CIS_SCRIPT} -v
    if [ $IS_ADVANCED -eq 1 ]; then
    	${PYTHON_CMD} ${SHOWOCI_SCRIPT} --version
    fi
}

show_version_json() {
    # Example: Version 2.8.0 Updated on February 23, 2024
    version_cis=$(${PYTHON_CMD} ${CIS_SCRIPT} -v | sed -e 's;^Version ;;g' -e 's; Updated.*;;g')
    if [ $IS_ADVANCED -eq 1 ]; then
        # Example: showoci.py 24.03.02
        version_showoci=`${PYTHON_CMD} ${SHOWOCI_SCRIPT} --version | sed -e 's;^'"${SHOWOCI_SCRIPT_NAME}"' ;;g'`
        printf "{ \"%s\": \"%s\", \"%s\": \"%s\", \"%s\": \"%s\"}" "${SCRIPT_NAME}" "${VERSION}" "${CIS_SCRIPT_NAME}" "${version_cis}" "${SHOWOCI_SCRIPT_NAME}" "${version_showoci}"
    else
        printf "{ \"%s\": \"%s\", \"%s\": \"%s\"}" "${SCRIPT_NAME}" "${VERSION}" "${CIS_SCRIPT_NAME}" "${version_cis}"
    fi
}

check_tenancy_size() {
    local num_cmps=$(oci iam compartment list --all --include-root --access-level ANY -c ${OCI_TENANCY} --query 'data[].id' | sed -e '/\[/d'  -e '/\]/d' | wc -l)
    printf "INFO: Number of compartments: %d\n" "${num_cmps}"
    if [ ${num_cmps} -gt 32 ]; then
        printf "WARNING: Number of compartments (%d) is too big for a proper run in Cloud Shell.\n" $num_cmps
        printf "WARNING: Please consider running the script in a Compute VM or from your desktop.\n"
        printf "WARNING: See the README for details.\n"
        exit 1
    fi
    num_regions=$(oci iam region-subscription list --query 'data[]."region-key"' | sed -e '/\[/d'  -e '/\]/d' | wc -l)
    printf "INFO: Number of regions: %d\n" "${num_regions}"
    if [ ${num_regions} -gt 5 ]; then
        printf "WARNING: Number of regions (%d) is too big for a proper run in Cloud Shell.\n" $num_regions
        printf "WARNING: Please consider running the script in a Compute VM or from your desktop.\n"
        printf "WARNING: See the README for details.\n"
        exit 1
    fi
}

make_env() {
    if [ $HAS_INTERNET_ACCESS -eq 1 ]; then
        if [ ! -d ${PYTHON_ENV} ]; then
            ${PYTHON_CMD} -m venv ${PYTHON_ENV}
        fi
    fi
    PIP_OPTS="-q --no-warn-script-location"
    if [ -d ${PYTHON_ENV} ]; then
        source ${PYTHON_ENV}/bin/activate
        PYTHON_CMD=$(which python3)
        if [ $HAS_INTERNET_ACCESS -eq 1 ]; then
            ${PYTHON_CMD} -m pip install pip --upgrade ${PIP_OPTS}
        else
            local _V_
            local PYVENV_VERSION
            _V_=$(echo -n ${PYTHON_VERSION} | sed -e 's,Python ,,g' -e 's;\.;;g')
            PYVENV_VERSION=$(cat ${PYTHON_ENV}/pyvenv.cfg | grep version | sed -e 's;version = ;;g' -e 's;\.;;g')
            if [ $PYVENV_VERSION -ne $_V_ ]; then
                printf "ERROR: Python and Python Virtual Environment version mismatch!\n"
                printf "ERROR: Python version: %s\n" "${PYTHON_VERSION}"
                printf "ERROR: Python Virtual Environment version: %s!\n" "${PYVENV_VERSION}"
                printf "ERROR: Please use matching versions!\n"
                exit 1
            fi
        fi
    fi

    if [ $HAS_INTERNET_ACCESS -eq 1 ]; then
        printf "INFO: Checking for required libraries ...\n"
    #     echo >${ASSESS_DIR}/requirements <<EOF
    # xlsxwriter>=3.2.9
    # pytz
    # openpyxl>=3.1.5
    # pyyaml>=6.0.3
    # oci==2.172.0
    # requests
    # matplotlib
    # numpy
    # EOF
        ${PYTHON_CMD} -m pip install ${PIP_OPTS} -r ${ASSESS_DIR}/requirements.txt
        if [ $? -gt 0 ]; then
            printf "ERROR: Permissions to install the required libraries are missing.\n"
            printf "ERROR: Please check with your OCI administrator.\n"
            exit 1
        fi
    fi
}

check_shasum() {
    local CMD_SHASUM='sha256sum'
    local OPT_SHASUM=''
    if [ "${OS_TYPE}" == 'Darwin' ]; then
        CMD_SHASUM="shasum"
        OPT_SHASUM='-a 256'
    fi
	local fn=$(basename ${1})
	local _error=0
	printf "INFO: Verifying checksum ... "
	${CMD_SHASUM} ${OPT_SHASUM} -c ${fn}
	_error=$?
	if [ ${_error} -gt 0 ]; then
		exit 1
	fi
}

install_binary() {
    local CMD_CURL=$(which curl)
    local _base=$1
    local _filename="${_base}.tar.gz"
    local _url=$3
    local _binary=$2
    local _f_binary="${ASSESS_DIR}/${_base}/bin/${_binary}"
    if [ ! -z ${4} ]; then
        local _f_binary="${ASSESS_DIR}/${4}/bin/${_binary}"
    fi
    local _gzcat_cmd='gunzip -c'
    if [ ! -e ${_f_binary} ]; then
        if [ ! -e ${_filename} ]; then
            ${CMD_CURL} -s -L ${_url}/${_filename} -o ${ASSESS_DIR}/${_filename}
        fi
        if [ ! -e ${_filename}.sha256 ]; then
            ${CMD_CURL} -s -L ${_url}/${_filename}.sha256 -o ${ASSESS_DIR}/${_filename}.tmp
            echo "$(cat ${ASSESS_DIR}/${_filename}.tmp)  ${_filename}" > ${_filename}.sha256
        fi
        check_shasum ${_filename}.sha256
        ${_gzcat_cmd} ${_filename} | tar xf -
        if [ -e ${_binary} ] && [ "${_os_type}" == 'macos' ]; then
            printf "INFO: You may need to enter your OS password to continue ...\n"
            sudo xattr -r -d com.apple.quarantine ${_graalpy}
            ${_binary} ${_version} > /dev/null
            _error=$?
            if [ ${_error} -gt 0 ]; then
                printf "ERROR: '%s' cannot be executed, yet.\n" "$(_binary)"
                printf "ERROR: Open System Settings > Privacy & Security > Security\n"
                printf "ERROR: Find '%s' was blocked ...\n" "$(_binary)"
                printf "ERROR: Click on 'Allow Anyway' and follow instructions.\n\n"
                printf "ERROR: Run %s again and click on 'Open' to continue.\n" "${SCRIPT_NAME}"
                exit 1
            fi
        fi
    fi
}

create_native() {
    if [ ! -z "${CLOUD_SHELL_TOOL_SET}" ]; then
        printf "INFO: Native image generation is not supported in OCI Cloud Shell!\n"
        exit 1
    fi
    printf "INFO: GraalPy support is experimental!\n"
    local _os_type='linux'
    local _os_platform='amd64'
    case "${OS_TYPE}" in
        Darwin)
            _os_type=macos
            ;;
        Linux)
            _os_type=linux
            ;;
        *)
            printf "ERROR: Platform %s is not supported!\n" ${OS_TYPE}
            exit 1
            ;;
    esac
    case "$OS_PLATFORM" in
        x86_64)
            _os_platform='amd64'
            ;;
        arm64)
            _os_platform='aarch64'
            ;;
        aarch64)
            _os_platform='aarch64'
            ;;
        *)
            printf "ERROR: Platform %s is not supported!\n" $OS_PLATFORM
            exit 1
            ;;
    esac
    local __graal_base="graalvm-jdk-${GRAAL_VERSION}+9.1"
    local __graalpy_base="graalpy-${GRAAL_VERSION}-${_os_type}-${_os_platform}"
    install_binary "graalvm-jdk-25_${_os_type}-${_os_platform}_bin" java "https://download.oracle.com/graalvm/25/latest" "graalvm-jdk-${GRAAL_VERSION}+9.1"
    install_binary "${_graalpy_base}" graalpy "https://github.com/oracle/graalpython/releases/latest/download"

    printf "INFO: Creating binary ...\n"
    local _bin_graalpy="${ASSESS_DIR}/${_graalpy_base}/bin/graalpy"
    JAVA_HOME="${ASSESS_DIR}/${_graal_base}"; ${_bin_graalpy} -m standalone native --enable-native-access=org.graalvm.truffle --module ${CIS_SCRIPT} --output ${CIS_SCRIPT_DIR}/cis_report --venv ${PYTHON_ENV}
    if [ ${IS_ADVANCED} -eq 1 ]; then
        JAVA_HOME="${ASSESS_DIR}/${_graal_base}"; ${_bin_graalpy} -m standalone native --enable-native-access=org.graalvm.truffle --module ${SHOWOCI_SCRIPT} --output ${SHOWOCI_SCRIPT_DIR}/showoci --venv ${PYTHON_ENV}
    fi
    exit 1
    local _bin_python="${ASSESS_DIR}/${_graalpy_base}/bin/python3"
    PYTHON_CMD=${_bin_python}
}

check_authentication() {
    if [ $PREPARE_ONLY -ne 1 ]; then
        if [ ! -z "${TENANCY}" -a -z "${CLOUD_SHELL_TOOL_SET}" -a "${INSTANCE_PRINCIPAL}" -eq 0 ]; then
            local tname=$(get_oci_config_value ${TENANCY} tenancy)
            local security_token_file=$(get_oci_config_value ${TENANCY} security_token_file)
            if [ -z ${tname} ]; then
                printf "ERROR: Profile name %s is not present in the config file!\n" ${TENANCY}
            fi
            if [ ! -z ${security_token_file} ]; then
                jwt="$(tr -d '\n\r ' < "${security_token_file}")"
                check_jwt_expiry "${jwt}"
                SHOWOCI_AUTH_OPT="-is"
                CIS_AUTH_OPT="-st"
            fi
        fi
    fi
}

prepare_end() {
    if [ $PREPARE_ONLY -eq 1 ]; then
        local _WC_=$(${PYTHON_CMD} -m pip list | grep pytz | wc -c)
        if [ ${_WC_} -gt 0]; then
            ZIP_ENV_NAME=$(basename ${ASSESS_DIR})'-supplement.zip'
            (cd $HOME; zip -q -r ${HOME}/${ZIP_ENV_NAME} .venv)
            if [ -e ${HOME}/${ZIP_ENV_NAME} ]; then
                printf "\nINFO: Python environment copied to %s \n" "${HOME}/${ZIP_ENV_NAME}"
            fi
        else
            printf "ERROR: **************************\n"
            printf "ERROR: venv configuration failed!\n"
            printf "ERROR: **************************\n"
        fi
        exit 1
    fi
}

check_env() {
    local _WC_=$(${PYTHON_CMD} -m pip list | grep pytz | wc -c)
    if [ ${_WC_} -lt 1 ]; then
        printf "ERROR: ************************************************************************\n"
        printf "ERROR: venv configuration failed!\n"
        printf "ERROR: ************************************************************************\n"
        if [ ${HAS_INTERNET_ACCESS} -eq 0 ]; then
            if [ ! -z ${CLOUD_SHELL_TOOL_SET} ]; then
                printf "ERROR: Either:\n"
                printf "ERROR: - Change the Cloud Shell network to 'public'.\n"
                printf "ERROR: or\n"
                printf "ERROR: - Please ask your Oracle contact for the required supplement file.\n"
            else
                printf "ERROR: - Ensure that the Internet can be reached (NAT mode will be sufficient).\n"
            fi
            printf "ERROR: When finished re-run again.\n"
            printf "ERROR: ************************************************************************\n"
        fi
        exit 1
    fi
}

cleanup() {
    deactivate
}

OS_TYPE=$(uname)
OS_PLATFORM=$(uname -m)

ASSESS_DIR=$(dirname $0)
if [ ${ASSESS_DIR} == "." ]; then
    ASSESS_DIR=${PWD}
    PARENT_DIR="$(dirname ${ASSESS_DIR})"
else
    PARENT_DIR="$(dirname ${ASSESS_DIR})"
fi
if [ ${PARENT_DIR} == "." ]; then
    PARENT_DIR=${PWD}
fi

DEBUG=0
RUN_CIS=1
RUN_SHOWOCI=1
NO_ZIP=0
NO_CSV=1
ZIP_PROTECT=0
QUIET=1
PREPARE_ONLY=0
REGION_NAME=''
TENANCY="DEFAULT"
INSTANCE_PRINCIPAL=0
SECURITY_TOKEN=0
REDACT_OUTPUT=0
CREATE_NATIVE=0
PYTHON_CMD=$(which python3)
SCRIPT_CMD=$(which script)
SHOWOCI_EXCLUDE=""
OPT_MANAGEMENT_COMPARTMENT="-mc"

SCRIPT_NAME=$(basename $0)
IS_ADVANCED=1
TYPE_NAME='advanced_ng'
HAS_INTERNET_ACCESS=1

if [ ${SCRIPT_NAME} == 'standard.sh' ]; then
    IS_ADVANCED=0
    RUN_SHOWOCI=0
    TYPE_NAME='standard'
    test_internet_access
fi

PYTHON_ENV="$HOME/.venv/${TYPE_NAME}"
POSTFIX="_${TYPE_NAME}"

while test -n "$1"; do
    case "$1" in
        -c)
            RUN_CIS=1
            RUN_SHOWOCI=0
            shift 1
            ;;
        --cis)
            RUN_CIS=1
            RUN_SHOWOCI=0
            CIS_DATA_OPT="$2"
            shift 2
            ;;
        -s)
            RUN_CIS=0
            RUN_SHOWOCI=1
            shift 1
            ;;
        --showoci)
            RUN_CIS=0
            RUN_SHOWOCI=1
    	    if [ $IS_ADVANCED -eq 1 ]; then
                SHOWOCI_DATA_OPT="$2"
                shift 2
            else
                shift 1
            fi
            ;;
        --include-management-compartment)
            OPT_MANAGEMENT_COMPARTMENT=""
            shift 1
            ;;
        --exclude)
    	    if [ $IS_ADVANCED -eq 1 -a $RUN_SHOWOCI -eq 1 ]; then
                SHOWOCI_EXCLUDE="-exclude $2"
                shift 2
            else
                shift 2
            fi
            ;;
        -ip)
            INSTANCE_PRINCIPAL=1
            SECURITY_TOKEN=0
            shift 1
            ;;
        -st)
            INSTANCE_PRINCIPAL=0
            SECURITY_TOKEN=1
            shift 1
            ;;
        -r|--region)
            REGION_NAME="$2"
            shift 2
            ;;
        --redact)
            REDACT_OUTPUT=1
            shift 1
            ;;
        -t|--tenancy)
            TENANCY="$2"
            check_config_for_profile $TENANCY
            shift 2
            ;;
        -cf|--config-file)
            OCI_CONFIG_FILE="$2"
            shift 2
            ;;
        --zip-protect)
            ZIP_PROTECT=1
            shift 1
            ;;
        --no-zip)
            NO_ZIP=1
            shift 1
            ;;
        -g)
            CREATE_NATIVE=1
            shift 1
            ;;
        --prepare)
            PREPARE_ONLY=1
            shift 1
            ;;
        --verbose)
            QUIET=0
            shift 1
            ;;
        -v|--version)
            show_version
            exit 1
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

if [ $IS_ADVANCED -ne 1 ]; then
    RUN_SHOWOCI=0
    RUN_CIS=1
else
    if [ -z "$CIS_DATA_OPT" ]; then
        CIS_DATA_OPT="--all-resources"
    fi
    if [ -z "$SHOWOCI_DATA_OPT" ]; then
        SHOWOCI_DATA_OPT="-a -dsa"
    fi
fi

if [ $REDACT_OUTPUT -eq 1 ]; then
    CIS_DATA_OPT="${CIS_DATA_OPT} --redact-output"
    SHOWOCI_DATA_OPT="${SHOWOCI_DATA_OPT}"
fi

SHOWOCI_AUTH_OPT=""
CIS_AUTH_OPT=""
TENANCY_NAME=""
if [ ! -z "${CLOUD_SHELL_TOOL_SET}" ]; then
    SHOWOCI_AUTH_OPT="-dt"
    CIS_AUTH_OPT="-dt"
    CLI_TENANCY_NAME=$(oci iam tenancy get --tenancy-id $OCI_TENANCY --query 'data.name' 2>/dev/null)
    if [ $? -gt 0 ]; then
        if [ $HAS_INTERNET_ACCESS -eq 0 ]; then
            printf "ERROR: Cloud Shell with NO internet access can run in Home region, only!\n"
        else
            printf "ERROR: Permissions to run the OCI CLI are missing.\n"
            printf "ERROR: Please contact your OCI administrator.\n"
        fi
        exit 1
    fi
    TENANCY_NAME=$(echo -n $CLI_TENANCY_NAME | sed -e 's/"//g')
    if [ $IS_ADVANCED -gt 0 ]; then
        check_tenancy_size
    fi
elif [ "${INSTANCE_PRINCIPAL}" -gt 0 ]; then
    SHOWOCI_AUTH_OPT="-ip"
    CIS_AUTH_OPT="-ip"
elif [ "${SECURITY_TOKEN}" -gt 0 ]; then
    SHOWOCI_AUTH_OPT="-is"
    CIS_AUTH_OPT="-st"
fi
if [ ! -z "${TENANCY_NAME}" ]; then
    TENANCY=${TENANCY_NAME}
fi

check_directories
check_python_version
make_env
if [ $CREATE_NATIVE -eq 1 ]; then
    create_native
fi
check_authentication
prepare_end

check_env

STAMP=$(date +%Y%m%d%H%M%S)
OUTPUT_DIR_NAME="${TENANCY}_${STAMP}"
OUTPUT_DIR_NAME="${OUTPUT_DIR_NAME}${POSTFIX}"

if [ $HAS_INTERNET_ACCESS -ne 1 -a ! -z "${OCI_REGION}" ]; then
    printf "WARNING: No Internet connection.\n\nWARNING: This script can run on home region only!\n\n"
    if [ ! -z "${REGION_NAME}" ]; then
        printf "WARNING: Ignoring option '-r "${REGION_NAME}"'.\n"
    fi
    printf "INFO: Running check for region '"${OCI_REGION}"' only.\n"
    REGION_NAME=${OCI_REGION}
fi

CIS_REGION_OPT=''
SHOWOCI_REGION_OPT=''
if [ ! -z "${REGION_NAME}" ]; then
    CIS_REGION_OPT="--regions ${REGION_NAME}"
    SHOWOCI_REGION_OPT="-rg ${REGION_NAME}"
    OUTPUT_REGION='_'`echo -n ${REGION_NAME} | sed '-e s;,;_;g'`
    OUTPUT_DIR_NAME="${OUTPUT_DIR_NAME}${OUTPUT_REGION}"
fi
OUTPUT_DIR="${ASSESS_DIR}/${OUTPUT_DIR_NAME}"
if [ ! -e ${OUTPUT_DIR} ]; then
    mkdir -p ${OUTPUT_DIR}
    show_version_json > ${OUTPUT_DIR}/script_versions.json
fi
OUTPUT_LOG="${OUTOUT_DIR}/${TYPE_NAME}.log"

#
# Tell the run options
MSG_SCRIPTS=""
if [ ${RUN_CIS} -eq 1 -a ${RUN_SHOWOCI} -ne 1 ]; then
    MSG_SCRIPTS=" '"${CIS_SCRIPT_NAME}"'"
elif [ ${RUN_CIS} -ne 1 -a ${RUN_SHOWOCI} -eq 1 ]; then
    MSG_SCRIPTS=" '"${SHOWOCI_SCRIPT_NAME}"'"
else
    MSG_SCRIPTS="s '"${CIS_SCRIPT_NAME}"' and '"${SHOWOCI_SCRIPT_NAME}"'"
fi
MSG_REGION="for all regions"
if [ ! -z "${REGION_NAME}" ]; then
    MSG_REGION="for region '"${REGION_NAME}"'"
fi

INFO_STR="Running script${MSG_SCRIPTS} ${MSG_REGION}"
if [ ! -z "${TENANCY_NAME}" ]; then
    INFO_STR="${INFO_STR} in tenancy '"${TENANCY_NAME}"'"
else
    INFO_STR="${INFO_STR} using configuration '"${TENANCY}"'"
fi
printf "INFO: %s\n" "${INFO_STR}"

CIS_OPTS="-t ${TENANCY} -c ${OCI_CONFIG_FILE} ${CIS_REGION_OPT} ${CIS_DATA_OPT} ${CIS_AUTH_OPT} --report-summary-json --report-prefix ${OUTPUT_DIR_NAME}"
SHOWOCI_OPTS="-t ${TENANCY} -cf ${OCI_CONFIG_FILE} ${SHOWOCI_REGION_OPT} ${SHOWOCI_AUTH_OPT} ${SHOWOCI_DATA_OPT} ${OPT_MANAGEMENT_COMPARTMENT} ${SHOWOCI_EXCLUDE}"

trap "cleanup; echo The script has been canceled; exiting" 1 2 3 6
_W_=$(which script | wc -c)
if [ $RUN_CIS -eq 1 ]; then
    out=$(echo -n ${OUTPUT_DIR} | sed -e 's;\./;;g')
    CIS_OPTS="${CIS_OPTS} --report-directory ${out}"
    if [ ${_W_} -gt 0 ]; then
        if [ "${OS_TYPE}" == 'Darwin' ]; then
            ${SCRIPT_CMD} -q ${out}/${TYPE_NAME}_cis_report.txt ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} 
        else
            ${SCRIPT_CMD} -c "${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS}" ${out}/${TYPE_NAME}_cis_report.txt
        fi
    else
        ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS}
    fi
fi
if [ $RUN_SHOWOCI -eq 1 ]; then
    if [ -z "${BUFFERED}" ]; then
    	export PYTHONUNBUFFERED=TRUE
    fi
    SHOWOCI_CSV=""
    if [ ${NO_CSV} -eq 0 ]; then
        SHOWOCI_CSV="-csv_nodate -csv ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}"
    fi
    SHOWOCI_XLSX="-xlsx_nodate -xlsx ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}"
    SHOWOCI_JSON_FILE="${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}.json"
    SHOWOCI_JSON="-jf ${SHOWOCI_JSON_FILE}"
    SHOWOCI_QUIET=""
    if [ ${QUIET} -eq 1 ]; then
        SHOWOCI_QUIET="--quiet"
    fi
    if [ ${_W_} -gt 0 ]; then
        if [ "${OS_TYPE}" == 'Darwin' ]; then
            ${SCRIPT_CMD} -q ${OUTPUT_DIR}/${TYPE_NAME}_showoci.txt ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} ${SHOWOCI_QUIET} ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}
        else
            ${SCRIPT_CMD} -c "${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} ${SHOWOCI_QUIET} ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}" ${OUTPUT_DIR}/${TYPE_NAME}_showoci.txt
        fi
    else
        ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS}  ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}
    fi
fi
if [ ${NO_ZIP} -eq 0 ]; then
    DIR_PARENT_OUTPUT="$(dirname ${OUTPUT_DIR})"
    cd $DIR_PARENT_OUTPUT
    if [ ${ZIP_PROTECT} -eq 1 ]; then
        printf "\nPlease enter a password for the ZIP file. Zero length passwords are not supported!\n"
        zip -e -q -r ${OUTPUT_DIR_NAME}.zip ${OUTPUT_DIR_NAME}
        if [ $? -ne 0 ]; then
            printf "Please run $0 again.\n"
            exit 1
        fi
    else
        zip -q -r ${OUTPUT_DIR_NAME}.zip ${OUTPUT_DIR_NAME}
        if [ $? -ne 0 ]; then
            printf "Please run $0 again.\n"
            exit 1
        fi
    fi
    mv ${OUTPUT_DIR_NAME}.zip ${PARENT_DIR}
    printf "\nINFO: All output can be found in the directory '%s'.\nINFO: Results are packaged as downloadable file '%s' at '%s'.\n" "${OUTPUT_DIR_NAME}" "${OUTPUT_DIR_NAME}.zip" "${PARENT_DIR}"
    if [ ! -z "${CLOUD_SHELL_TOOL_SET}" ]; then
        printf "\nINFO: To download the ZIP file:\nINFO:  1. Copy the filename %s\nINFO:  2. Click on the settings icon of the Cloud Shell on the right\nINFO:  3. Select 'Download'\nINFO:  4. Paste the file name into the modal window and click on 'Download'\n\n" "${OUTPUT_DIR_NAME}.zip"
    fi
    if [ $HAS_INTERNET_ACCESS -eq 0 -a ! -z "$OCI_REGION" ]; then
        printf "\nWARNING: Your Cloud Shell seems to have the OCI services network configured.\n"
        printf "WARNING: With this setup the script can check your home region '"${OCI_REGION}"' only.\nWARNING: To check all your regions you need Internet access for your Cloud Shell!\n\n"
    fi
fi
