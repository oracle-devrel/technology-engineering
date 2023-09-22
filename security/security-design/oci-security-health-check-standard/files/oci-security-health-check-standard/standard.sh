#!/bin/bash
###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Olaf Heimburger
#
VERSION=230922

ASSESS_DIR=`dirname $0`
if [ ${ASSESS_DIR} == "." ]; then
    ASSESS_DIR=`pwd`
    PARENT_DIR="$(dirname ${ASSESS_DIR})"
else
    PARENT_DIR="$(dirname ${ASSESS_DIR})"
fi
if [ ${PARENT_DIR} == "." ]; then
    PARENT_DIR=`pwd`
fi

RUN_CIS=1
RUN_SHOWOCI=1
REGION_NAME=''
TENANCY="DEFAULT"

SCRIPT_NAME=`basename $0`
IS_ADVANCED=1
if [ ${SCRIPT_NAME} == 'standard.sh' ]; then
    IS_ADVANCED=0
    RUN_SHOWOCI=0
fi

PYTHON_CMD=`which python3`
SCRIPT_CMD=`which script`
_W_=`which python3 | wc -c`
if [ ${_W_} -le 0 ]; then
    echo "ERROR: Please install python3 first!"
    exit 1
fi
_V_=`${PYTHON_CMD} --version | sed -e 's,Python ,,g' -e 's;\.;;g'`
if [ ${_V_} -lt 38 ]; then
    echo "ERROR: Please upgrade to Python 3.8"
    exit 1
fi

if [ ! -e ${ASSESS_DIR}/scripts ]; then
    echo "ERROR: Directory 'scripts' missing!"
    exit 1
fi
SCRIPTS_DIR="${ASSESS_DIR}/scripts"

if [ ! -e ${SCRIPTS_DIR}/cis_reports ]; then
    echo "ERROR: Directory 'cis_reports' missing!"
    exit 1
fi
CIS_SCRIPT_DIR="${SCRIPTS_DIR}/cis_reports"
CIS_SCRIPT="${CIS_SCRIPT_DIR}/cis_reports.py"

if [ ${IS_ADVANCED} -eq 1 -a ! -e ${SCRIPTS_DIR}/showoci ]; then
    echo "ERROR: Directory 'showoci' missing!"
    exit 1
fi
SHOWOCI_SCRIPT_DIR="${SCRIPTS_DIR}/showoci"
SHOWOCI_SCRIPT="${SHOWOCI_SCRIPT_DIR}/showoci_xlsx.py"

usage() {
    if [ $IS_ADVANCED -eq 1 ]; then
        echo "Usage: $0 [-h] [-s [showoci options]|-c cis_report.py options] [-r region_name] [-t tenancy_name] [-u] [-v]"
        echo " -h -- this message"
        echo " -c -- run cis_report only"
        echo " --cis options -- run cis_report only, with additional options."
        echo " -s -- run showoci only."
        echo " --showoci -- run showoci only, with additional options."
    else
        echo "Usage: $0 [-h] [-r region_name] [-t tenancy_name] [-v]"
        echo " -h -- this message"
    fi
    echo " -r|--region region_name -- run assess.sh on region region_name only"
    echo " -t|--tenancy tenancy_configuration -- specify a name of the tenancy"
    echo "    configuration in .oci/config (defaults to 'DEFAULT')"
    echo " -v -- show the version of this script"
    exit 1
}

show_version() {
    echo $0 version $VERSION
    ${PYTHON_CMD} ${CIS_SCRIPT} -v
    if [ $IS_ADVANCED -eq 1 ]; then
	${PYTHON_CMD} ${SHOWOCI_SCRIPT} --version
    fi
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
    	    if [ $IS_ADVANCED -eq 1 ]; then
                CIS_DATA_OPT="$2"
                shift 2
            else
                shift 1
            fi
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
        -r|--region)
            REGION_NAME="$2"
            shift 2
            ;;
        -t|--tenancy)
            TENANCY="$2"
            shift 2
            ;;
        -v|--version)
            show_version
            shift 1
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
        CIS_DATA_OPT="--obp"
    fi
    if [ -z "$SHOWOCI_DATA_OPT" ]; then
        SHOWOCI_DATA_OPT="-a"
    fi
fi

CLOUD_SHELL_OPT=""
TENANCY_NAME=""
if [ ! -z "${CLOUD_SHELL_TOOL_SET}" ]; then
    CLOUD_SHELL_OPT="-dt"
    CLI_TENANCY_NAME=`oci iam tenancy get --tenancy-id $OCI_TENANCY --query 'data.name' 2>/dev/null`
    if [ $? -gt 0 ]; then
        echo "ERROR: Permissions to run the OCI CLI are missing."
        echo "ERROR: Please contact your OCI administrator."
        exit 1
    fi
    TENANCY_NAME=`echo -n $CLI_TENANCY_NAME | sed -e 's/"//g'`
fi
if [ ! -z "${TENANCY_NAME}" ]; then
    TENANCY=${TENANCY_NAME}
fi

STAMP=`date +%Y%m%d%H%M%S`
OUTPUT_DIR_NAME="${TENANCY}_${STAMP}"
POSTFIX="_standard"
if [ ${IS_ADVANCED} -eq 1 ]; then
    POSTFIX="_advanced"
fi
OUTPUT_DIR_NAME="${OUTPUT_DIR_NAME}${POSTFIX}"

${PYTHON_CMD} -m pip install -q -r ${ASSESS_DIR}/requirements.txt --user --no-warn-script-location
if [ $? -gt 0 ]; then
    echo "ERROR: Permissions to install the required libraries are missing."
    echo "ERROR: Please check with your OCI administrator."
    exit 1
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
    show_version > ${OUTPUT_DIR}/assess_versions.txt
fi
OUTPUT_LOG="${OUTOUT_DIR}/assess.log"

#
# Tell the run options
MSG_SCRIPTS=""
if [ ${RUN_CIS} -eq 1 -a ${RUN_SHOWOCI} -ne 1 ]; then
    MSG_SCRIPTS=" cis_reports.py"
elif [ ${RUN_CIS} -ne 1 -a ${RUN_SHOWOCI} -eq 1 ]; then
    MSG_SCRIPTS=" showoci.py"
else
    MSG_SCRIPTS="s cis_reports.py and showoci.py"
fi
MSG_REGION="for all regions"
if [ ! -z "${REGION_NAME}" ]; then
    MSG_REGION="for region ${REGION_NAME}"
fi

INFO_STR="INFO: Running script${MSG_SCRIPTS} ${MSG_REGION}"
if [ ! -z "${TENANCY_NAME}" ]; then
    info_str="${INFO_STR} in tenancy ${TENANCY_NAME}"
else
    info_str="${INFO_STR} for configuration ${TENANCY}"
fi
echo ${INFO_STR}

CIS_OPTS="-t ${TENANCY} ${CIS_REGION_OPT} ${CIS_DATA_OPT} ${CLOUD_SHELL_OPT}"
SHOWOCI_OPTS="-t ${TENANCY} ${SHOWOCI_REGION_OPT} ${CLOUD_SHELL_OPT} ${SHOWOCI_DATA_OPT}"

trap "echo The script has been canceled; exiting" SIGINT
_W_=`which script | wc -c`
if [ $RUN_CIS -eq 1 ]; then
    out=`echo -n ${OUTPUT_DIR} | sed -e 's;\./;;g'`
    if [ ${_W_} -gt 0 ]; then
        ${SCRIPT_CMD} -c "${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} --report-directory ${out}" ${out}/assess_cis_report.txt
    else
        ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} --report-directory ${out}
    fi
fi
if [ $RUN_SHOWOCI -eq 1 ]; then
    if [ -z "${BUFFERED}" ]; then
	export PYTHONUNBUFFERED=TRUE
    fi
    if [ ${_W_} -gt 0 ]; then
        ${SCRIPT_CMD} -c "${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} -jf ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}.json -xlsx ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}" ${OUTPUT_DIR}/assess_showoci.txt
    else
        ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} -jf ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}.json -xlsx ${OUTPUT_DIR}/showoci_${OUTPUT_DIR_NAME}
    fi
fi
DIR_PARENT_OUTPUT="$(dirname ${OUTPUT_DIR})"
cd $DIR_PARENT_OUTPUT
zip -r ${OUTPUT_DIR_NAME}.zip ${OUTPUT_DIR_NAME}
mv ${OUTPUT_DIR_NAME}.zip ${PARENT_DIR}
echo
echo "INFO: All output is also available in the directory ${OUTPUT_DIR_NAME}."
echo "INFO: Downloadable result is available as ${OUTPUT_DIR_NAME}.zip at ${PARENT_DIR}."
echo
