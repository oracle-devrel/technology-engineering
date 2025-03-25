#!/bin/bash
###############################################################################
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Olaf Heimburger
#
VERSION=250307

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

RUN_CIS=1
RUN_SHOWOCI=1
NO_ZIP=0
REGION_NAME=''
TENANCY="DEFAULT"
INSTANCE_PRINCIPAL=0

SCRIPT_NAME=$(basename $0)
IS_ADVANCED=1
PYTHON_ENV=$HOME/.venv/advanced
if [ ${SCRIPT_NAME} == 'standard.sh' ]; then
    IS_ADVANCED=0
    RUN_SHOWOCI=0
    PYTHON_ENV=$HOME/.venv/standard
fi

PYTHON_CMD=$(which python3)
SCRIPT_CMD=$(which script)
_W_=$(which python3 | wc -c)
if [ ${_W_} -le 0 ]; then
    printf "ERROR: Please install python3 first!\n"
    exit 1
fi
_V_=$(${PYTHON_CMD} --version | sed -e 's,Python ,,g' -e 's;\.;;g')
if [ ${_V_} -lt 38 ]; then
    printf "ERROR: Please upgrade to Python 3.8 or higher.\n"
    exit 1
fi

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
SHOWOCI_SCRIPT_DIR="${SCRIPTS_DIR}/showoci"
SHOWOCI_SCRIPT_NAME="showoci_xlsx.py"
SHOWOCI_SCRIPT="${SHOWOCI_SCRIPT_DIR}/${SHOWOCI_SCRIPT_NAME}"

usage() {
    if [ $IS_ADVANCED -eq 1 ]; then
        printf "Usage: $0 [-h] [-ip] [-s|--showoci options]|-c|--cis options] [-r region_name] [-t tenancy_name] [-u] [-v]\n"
        printf " -h  -- This message.\n"
        printf " -ip -- Use instance principal for authentication.\n"
        printf " -c  -- Run cis_report only.\n"
        printf " -s  -- Run showoci only.\n"
        printf " --cis options     -- Run cis_report only and provide additional options.\n"
        printf " --showoci options -- Run showoci only and provide additional options.\n"
        printf "   For example, --showoci '-h' shows available options.\n"
        printf "   The options -jf, -ip, -t, -rg, -xlsx_nodate, --version are already supported by this script.\n"
    else
        printf "Usage: $0 [-h] [-ip] [-r region_name] [-t tenancy_name] [-v]\n"
        printf " -h -- this message\n"
        printf " -ip -- Use instance principal for authentication.\n"
        printf " --cis options     -- Run cis_report only and provide additional options.\n"
    fi
    printf " --no_zip -- Do not create a ZIP file for the contents pf the output directory.\n"
    printf " -r|--region region_name -- Run assess.sh on region region_name only.\n"
    printf " -t|--tenancy tenancy_configuration -- Specify a name of the tenancy.\n"
    printf "    Configuration in .oci/config (defaults to 'DEFAULT') will be used.\n"
    printf " -v -- Show the versions of the scripts used.\n"
    exit 1
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
    version_cis=`${PYTHON_CMD} ${CIS_SCRIPT} -v | sed -e 's;^Version ;;g' -e 's; Updated.*;;g'`
    if [ $IS_ADVANCED -eq 1 ]; then
        # Example: showoci_xlsx.py 24.03.02
        version_showoci=`${PYTHON_CMD} ${SHOWOCI_SCRIPT} --version | sed -e 's;^.* ;;g'`
        printf "{ \"assess\": \"%s\", \"cis_report\": \"%s\", \"showoci\": \"%s\"}" "${VERSION}" "${version_cis}" "${version_showoci}"
    else
        printf "{ \"assess\": \"%s\", \"cis_report\": \"%s\"}" "${VERSION}" "${version_cis}"
    fi
}

make_env() {
    if [ ! -d ${PYTHON_ENV} ]; then
        ${PYTHON_CMD} -m venv ${PYTHON_ENV}
    fi

    PIP_OPTS="-q --no-warn-script-location"
    if [ -d ${PYTHON_ENV} ]; then
        source ${PYTHON_ENV}/bin/activate
        PYTHON_CMD=$(which python3)
        ${PYTHON_CMD} -m pip install pip --upgrade ${PIP_OPTS}
    fi

    printf "INFO: Checking for required libraries...\n"
    # PIP_OPTS=""
    # ${PYTHON_CMD} -m pip install ${PIP_OPTS} -r ${ASSESS_DIR}/requirements.txt > ${OUTPUT_DIR_NAME}/assess_pip.txt
    ${PYTHON_CMD} -m pip install ${PIP_OPTS} -r ${ASSESS_DIR}/requirements.txt
    if [ $? -gt 0 ]; then
        printf "ERROR: Permissions to install the required libraries are missing.\n"
        printf "ERROR: Please check with your OCI administrator.\n"
        exit 1
    fi
}

check_shasum() {
    CMD_SHASUM='sha256sum'
    OPT_SHASUM=''
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

install_graal() {
    local _os_type='linux'
    local _os_platform='amd64'
    local _gzcat_cmd='gunzip -c'
    case "$OS_TYPE" in
        Darwin)
            _os_type=macos
            ;;
        Linux)
            _os_type=linux
            ;;
        *)
            printf "ERROR: Platform $OS_TYPE not supported\n"
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
        *)
            printf "ERROR: Platform $OS_PLATFORM not supported\n"
            exit 1
            ;;
    esac
    CMD_CURL=$(which curl)
    local _graal_base="graalpy-24.1.1-${_os_type}-${_os_platform}"
    local _graal_filename="${_graal_base}.tar.gz"
    local _bin_name="graalpy"
    local _bin_graalpy="${ASSESS_DIR}/${_graal_base}/bin/${_bin_name}"
    local _bin_python="${ASSESS_DIR}/${_graal_base}/bin/python3"
    if [ ! -e ${_bin_graalpy} ]; then
        if [ ! -e ${_graal_filename} ]; then
            ${CMD_CURL} -s -L https://github.com/oracle/graalpython/releases/latest/download/${_graal_filename} -o ${ASSESS_DIR}/${_graal_filename}
        fi
        if [ ! -e ${_graal_filename}.sha256 ]; then
            ${CMD_CURL} -s -L https://github.com/oracle/graalpython/releases/latest/download/${_graal_filename}.sha256 -o ${ASSESS_DIR}/${_graal_filename}.tmp
            echo "$(cat ${ASSESS_DIR}/${_graal_filename}.tmp)  ${_graal_filename}" > ${_graal_filename}.sha256
        fi
        check_shasum ${_graal_filename}.sha256
        ${_gzcat_cmd} ${_graal_filename} | tar xf -
        if [ -e ${_bin_graalpy} ] && [ "${_os_type}" == 'macos' ]; then
            printf "INFO: You may need to enter your OS password to continue...\n"
            sudo xattr -r -d com.apple.quarantine ${_bin_graalpy}
            ${_bin_fqp} ${_version} > /dev/null
            _error=$?
            if [ ${_error} -gt 0 ]; then
                printf "ERROR: '%s' cannot be executed, yet.\n" "$(_bin_name)"
                printf "ERROR: Open System Settings > Privacy & Security > Security\n"
                printf "ERROR: Find '%s' was blocked...\n" "$(_bin_name)"
                printf "ERROR: Click on 'Allow Anyway' and follow instructions.\n\n"
                printf "ERROR: Run %s again and click on 'Open' to continue.\n" "${SCRIPT_NAME}"
                exit 1
            fi
        fi
    fi
    # ${_bin_graalpy} -m standalone native --module ${SHOWOCI_SCRIPT} --output ${SHOWOCI_SCRIPT_DIR}/showoci --venv ${PYTHON_ENV}
    PYTHON_CMD=${_bin_python}
}

cleanup() {
    deactivate
}

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
        -ip)
            INSTANCE_PRINCIPAL=1
            shift 1
            ;;
        -r|--region)
            REGION_NAME="$2"
            shift 2
            ;;
        -t|--tenancy)
            TENANCY="$2"
            shift 2
            ;;
        --no-zip)
            NO_ZIP=1
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

make_env

if [ $IS_ADVANCED -ne 1 ]; then
    RUN_SHOWOCI=0
    RUN_CIS=1
else
    if [ -z "$CIS_DATA_OPT" ]; then
        CIS_DATA_OPT="--obp --all-resources"
    fi
    if [ -z "$SHOWOCI_DATA_OPT" ]; then
        SHOWOCI_DATA_OPT="--quiet -a -dsa"
    fi
fi

AUTH_OPT=""
TENANCY_NAME=""
if [ ! -z "${CLOUD_SHELL_TOOL_SET}" ]; then
    AUTH_OPT="-dt"
    CLI_TENANCY_NAME=$(oci iam tenancy get --tenancy-id $OCI_TENANCY --query 'data.name' 2>/dev/null)
    if [ $? -gt 0 ]; then
        printf "ERROR: Permissions to run the OCI CLI are missing.\n"
        printf "ERROR: Please contact your OCI administrator.\n"
        exit 1
    fi
    TENANCY_NAME=$(echo -n $CLI_TENANCY_NAME | sed -e 's/"//g')
elif [ "${INSTANCE_PRINCIPAL}" -gt 0 ]; then
    AUTH_OPT="-ip"
fi
if [ ! -z "${TENANCY_NAME}" ]; then
    TENANCY=${TENANCY_NAME}
fi

STAMP=$(date +%Y%m%d%H%M%S)
OUTPUT_DIR_NAME="${TENANCY}_${STAMP}"
POSTFIX="_standard"
if [ ${IS_ADVANCED} -eq 1 ]; then
    POSTFIX="_advanced"
fi
OUTPUT_DIR_NAME="${OUTPUT_DIR_NAME}${POSTFIX}"

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
    show_version_json > ${OUTPUT_DIR}/assess_versions.json
fi
OUTPUT_LOG="${OUTOUT_DIR}/assess.log"

#
# Tell the run options
MSG_SCRIPTS=""
if [ ${RUN_CIS} -eq 1 -a ${RUN_SHOWOCI} -ne 1 ]; then
    MSG_SCRIPTS=" ${CIS_SCRIPT_NAME}"
elif [ ${RUN_CIS} -ne 1 -a ${RUN_SHOWOCI} -eq 1 ]; then
    MSG_SCRIPTS=" ${SHOWOCI_SCRIPT_NAME}"
else
    MSG_SCRIPTS="s ${CIS_SCRIPT_NAME} and ${SHOWOCI_SCRIPT_NAME}"
fi
MSG_REGION="for all regions"
if [ ! -z "${REGION_NAME}" ]; then
    MSG_REGION="for region ${REGION_NAME}"
fi

INFO_STR="Running script${MSG_SCRIPTS} ${MSG_REGION}"
if [ ! -z "${TENANCY_NAME}" ]; then
    INFO_STR="${INFO_STR} in tenancy ${TENANCY_NAME}"
else
    INFO_STR="${INFO_STR} using configuration ${TENANCY}"
fi
printf "INFO: %s\n" "${INFO_STR}"

CIS_OPTS="-t ${TENANCY} ${CIS_REGION_OPT} ${CIS_DATA_OPT} ${AUTH_OPT} --report-summary-json --report-prefix ${OUTPUT_DIR_NAME}"
SHOWOCI_OPTS="-t ${TENANCY} ${SHOWOCI_REGION_OPT} ${AUTH_OPT} ${SHOWOCI_DATA_OPT}"

trap "cleanup; echo The script has been canceled; exiting" 1 2 3 6
_W_=$(which script | wc -c)
if [ $RUN_CIS -eq 1 ]; then
    out=$(echo -n ${OUTPUT_DIR} | sed -e 's;\./;;g')
    CIS_OPTS="${CIS_OPTS} --report-directory ${out}"
    if [ ${_W_} -gt 0 ]; then
        if [ "${OS_TYPE}" == 'Darwin' ]; then
            ${SCRIPT_CMD} -q ${out}/assess_cis_report.txt ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} 
        else
            ${SCRIPT_CMD} -c "${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS}" ${out}/assess_cis_report.txt
        fi
    else
        ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS}
    fi
fi
if [ $RUN_SHOWOCI -eq 1 ]; then
    if [ -z "${BUFFERED}" ]; then
    	export PYTHONUNBUFFERED=TRUE
    fi
    # SHOWOCI_CSV="-csv_nodate -csv ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}"
    SHOWOCI_XLSX="-xlsx_nodate -xlsx ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}"
    SHOWOCI_JSON="-jf ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}.json"
    if [ ${_W_} -gt 0 ]; then
        if [ "${OS_TYPE}" == 'Darwin' ]; then
            ${SCRIPT_CMD} -q ${OUTPUT_DIR}/assess_showoci.txt ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS}  ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}
        else
            ${SCRIPT_CMD} -c "${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}" ${OUTPUT_DIR}/assess_showoci.txt
        fi
    else
        ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS}  ${SHOWOCI_JSON} ${SHOWOCI_XLSX} ${SHOWOCI_CSV}
    fi
fi
if [ ${NO_ZIP} -eq 0 ]; then
    DIR_PARENT_OUTPUT="$(dirname ${OUTPUT_DIR})"
    cd $DIR_PARENT_OUTPUT
    zip -q -r ${OUTPUT_DIR_NAME}.zip ${OUTPUT_DIR_NAME}
    mv ${OUTPUT_DIR_NAME}.zip ${PARENT_DIR}
    printf "\nINFO: All output can be found in the directory '%s'.\nINFO: Results are packaged as downloadable file '%s' at '%s'.\n" "${OUTPUT_DIR_NAME}" "${OUTPUT_DIR_NAME}.zip" "${PARENT_DIR}"
fi
