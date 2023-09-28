#!/bin/bash
###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Olaf Heimburger
#
VERSION=230630

ASSESS_DIR=`dirname $0`

RUN_CIS=1
RUN_SHOWOCI=1
REGION_NAME=''
TENANCY="DEFAULT"

SCRIPT_NAME=`basename $0`
IS_ADVANCED=1
if [ ${SCRIPT_NAME} == 'standard.sh' ]; then
    IS_ADVANCED=0
fi

PYTHON_CMD=`which python3`
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


# echo "$0 version $VERSION"
usage() {
    if [ $IS_ADVANCED -eq 1 ]; then
	echo "Usage: $0 [-h] [-s|-c] [-r region_name] [-t tenancy_name] [-u] [-v]"
	echo " -h -- this message"
	echo " -c -- run cis_report only"
	echo " -s -- run showoci only"
	echo " -u -- unbuffered output for showoci"
    else
	echo "Usage: $0 [-h] [-r region_name] [-t tenancy_name] [-v]"
	echo " -h -- this message"
    fi
    echo " -r region_name -- run assess.sh on region region_name only"
    echo " -t tenancy_configuration -- specify a name of the tenancy"
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

while getopts 'bchr:st:v' opt; do
    case "$opt" in
	c)
	    RUN_CIS=1
	    RUN_SHOWOCI=0
	    ;;
	s)
	    if [ $IS_ADVANCED -eq 1 ]; then
		RUN_CIS=0
		RUN_SHOWOCI=1
	    fi
	    ;;
	r)
	    REGION_NAME=$OPTARG
	    ;;
	t)
	    TENANCY="$OPTARG"
	    echo
	    ;;
	b)
	    BUFFERED="1"
	    ;;
	h)
	    usage
	    ;;
	v)
	    show_version
	    exit 1
	    ;;
    esac
done
shift "$(($OPTIND -1))"

if [ $IS_ADVANCED -ne 1 ]; then
    RUN_SHOWOCI=0
    RUN_CIS=1
fi

CLOUD_SHELL_OPT=""
TENANCY_NAME=""
if [ "x${CLOUD_SHELL_TOOL_SET}" != 'x' ]; then
    CLOUD_SHELL_OPT=" -dt "
    CLI_TENANCY_NAME=`oci iam tenancy get --tenancy-id $OCI_TENANCY --query 'data.name' 2>/dev/null`
    if [ $? -gt 0 ]; then
        echo "ERROR: Permissions to run the OCI CLI are missing."
        echo "ERROR: Please check with your OCI administrator."
        exit 1
    fi
    TENANCY_NAME=`echo -n $CLI_TENANCY_NAME | sed -e 's/"//g'`
fi

STAMP=`date +%Y%m%d%H%M%S`
OUTPUT_DIR="${ASSESS_DIR}/${TENANCY}_${STAMP}"
if [ "x${TENANCY_NAME}" != 'x' ]; then
    POSTFIX="_standard"
    if [ ${IS_ADVANCED} -eq 1 ]; then
	POSTFIX="_advanced"
    fi
    OUTPUT_DIR="${ASSESS_DIR}/${TENANCY_NAME}_${STAMP}${POSTFIX}"
fi

${PYTHON_CMD} -m pip install -q -r ${ASSESS_DIR}/requirements.txt --user
if [ $? -gt 0 ]; then
    echo "ERROR: Permissions to install the required libraries are missing."
    echo "ERROR: Please check with your OCI administrator."
    exit 1
fi

CIS_REGION_OPT=''
SHOWOCI_REGION_OPT=''
if [ "x${REGION_NAME}" != 'x' ]; then
    CIS_REGION_OPT="--regions ${REGION_NAME}"
    SHOWOCI_REGION_OPT="-rg ${REGION_NAME}"
    OUTPUT_REGION='_'`echo -n ${REGION_NAME} | sed '-e s;,;_;g'`
    OUTPUT_DIR="${OUTPUT_DIR}${OUTPUT_REGION}"
fi
if [ ! -e ${OUTPUT_DIR} ]; then
    mkdir ${OUTPUT_DIR}
    show_version > ${OUTPUT_DIR}/assess_versions.txt
fi
OUTPUT_LOG="${OUTOUT_DIR}/assess.log"

# if [ -z "$SCRIPT" ]; then
#    /usr/bin/script ${OUTPUT_LOG} /bin/bash -c "$0 $*"
# fi

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
if [ "x${REGION_NAME}"  != 'x' ]; then
    MSG_REGION="for region ${REGION_NAME}"
fi

if [ "x${TENANCY_NAME}" != 'x' ]; then
    echo "INFO: Running script${MSG_SCRIPTS} ${MSG_REGION} in tenancy ${TENANCY_NAME}"
else
    echo "INFO: Running script${MSG_SCRIPTS} ${MSG_REGION} for configuration ${TENANCY}"
fi

if [ ${IS_ADVANCED} -eq 1 ]; then
    CIS_BEST_PRACTICES_OPT="--obp"
    # CIS_REDACTION_OPT="--redact"
    # CIS_RAW_OPT="--raw"
fi
CIS_OPTS="-t ${TENANCY} ${CIS_REGION_OPT} ${CIS_BEST_PRACTICES_OPT} ${CIS_REDACT_OPT} ${CIS_RAW_OPT} ${CLOUD_SHELL_OPT}"
SHOWOCI_DATA_OPT='-a'
SHOWOCI_OPTS="-t ${TENANCY} ${SHOWOCI_REGION_OPT} ${CLOUD_SHELL_OPT} ${SHOWOCI_DATA_OPT}"

trap "echo The script has been canceled; exit" SIGINT
if [ $RUN_CIS -eq 1 ]; then
    out=`echo -n ${OUTPUT_DIR} | sed -e 's;\./;;g'`
    ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} --report-directory ${out}
    # ${PYTHON_CMD} ${CIS_SCRIPT} ${CIS_OPTS} --report-directory ${OUTPUT_DIR}
fi
if [ $RUN_SHOWOCI -eq 1 ]; then
    if [ -z "${BUFFERED}" ]; then
	export PYTHONUNBUFFERED=TRUE
    fi
    ${PYTHON_CMD} ${SHOWOCI_SCRIPT} ${SHOWOCI_OPTS} -jf ${OUTPUT_DIR}/showoci${OUTPUT_REGION}.json -xlsx ${OUTPUT_DIR}/showoci${OUTPUT_REGION}
fi
zip -r ${OUTPUT_DIR}.zip ${OUTPUT_DIR}
mv ${OUTPUT_DIR}.zip ${HOME}
echo
echo "INFO: All output is also available in the directory ${OUTPUT_DIR}."
echo "INFO: Downloadable result is available as ${OUTPUT_DIR}.zip at ${HOME}."
echo

