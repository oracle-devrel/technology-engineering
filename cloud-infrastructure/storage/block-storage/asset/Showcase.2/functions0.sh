#!/bin/bash
# Version: @(#).functions0.sh 1.0.0 
# License
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License (UPL), Version 1.0.
# See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
#
#@  functions needed to run healthcheck.storage.sh
#@
#
# Update history:
#
# V 1.0.0 28.06.2023 initial version
#


if [ 1 -eq 1 ] ; then # define colors
Color_Off='\e[0m'       # Text Reset

# Regular Colors
Black='\e[0;30m'        # Black
Red='\e[0;31m'          # Red
Green='\e[0;32m'        # Green
Yellow='\e[0;33m'       # Yellow
Blue='\e[0;34m'         # Blue
Purple='\e[0;35m'       # Purple
Cyan='\e[0;36m'         # Cyan
White='\e[0;37m'        # White

# Bold
BBlack='\e[1;30m'       # Black
BRed='\e[1;31m'         # Red
BGreen='\e[1;32m'       # Green
BYellow='\e[1;33m'      # Yellow
BBlue='\e[1;34m'        # Blue
BPurple='\e[1;35m'      # Purple
BCyan='\e[1;36m'        # Cyan
BWhite='\e[1;37m'       # White

# Underline
UBlack='\e[4;30m'       # Black
URed='\e[4;31m'         # Red
UGreen='\e[4;32m'       # Green
UYellow='\e[4;33m'      # Yellow
UBlue='\e[4;34m'        # Blue
UPurple='\e[4;35m'      # Purple
UCyan='\e[4;36m'        # Cyan
UWhite='\e[4;37m'       # White

# Background
On_Black='\e[40m'       # Black
On_Red='\e[41m'         # Red
On_Green='\e[42m'       # Green
On_Yellow='\e[43m'      # Yellow
On_Blue='\e[44m'        # Blue
On_Purple='\e[45m'      # Purple
On_Cyan='\e[46m'        # Cyan
On_White='\e[47m'       # White

# High Intensity
IBlack='\e[0;90m'       # Black
IRed='\e[0;91m'         # Red
IGreen='\e[0;92m'       # Green
IYellow='\e[0;93m'      # Yellow
IBlue='\e[0;94m'        # Blue
IPurple='\e[0;95m'      # Purple
ICyan='\e[0;96m'        # Cyan
IWhite='\e[0;97m'       # White

# Bold High Intensity
BIBlack='\e[1;90m'      # Black
BIRed='\e[1;91m'        # Red
BIGreen='\e[1;92m'      # Green
BIYellow='\e[1;93m'     # Yellow
BIBlue='\e[1;94m'       # Blue
BIPurple='\e[1;95m'     # Purple
BICyan='\e[1;96m'       # Cyan
BIWhite='\e[1;97m'      # White

# High Intensity backgrounds
On_IBlack='\e[0;100m'   # Black
On_IRed='\e[0;101m'     # Red
On_IGreen='\e[0;102m'   # Green
On_IYellow='\e[0;103m'  # Yellow
On_IBlue='\e[0;104m'    # Blue
On_IPurple='\e[0;105m'  # Purple
On_ICyan='\e[0;106m'    # Cyan
On_IWhite='\e[0;107m'   # White
fi

if [ 1 -eq 1 ] ; then # set environement
. parameter1.sh
fi

if [ 1 -eq 1 ] ; then # level 0 functions (this functions do not need/call other then level 0 functions)

function color_print() {
if [ ${DEBUG_LEVEL} -eq 0 ] ; then echo -e "$1: $2 ${Color_Off}"     ; fi
if [ ${DEBUG_LEVEL} -eq 1 ] ; then echo -e "$1(${DEBUG_LEVEL}) $(date "+%d.%m.%Y %H:%M:%S") : $2 ${Color_Off}"     ; fi
if [ ${DEBUG_LEVEL} -eq 2 ] ; then echo -e "$1(${DEBUG_LEVEL}) $(date "+%d.%m.%Y %H:%M:%S") : $2 ${Color_Off}"     ; fi
if [ ${DEBUG_LEVEL} -gt 2 ] ; then echo -e "$1(${DEBUG_LEVEL}) $(date "+%d.%m.%Y %H:%M:%S") : $2 ${Color_Off}"     ; fi
}

TIMESTAMP=$(date "+%Y%m%d%H%M%S")			# timestamp
UNIQUE_ID="k4JgHrt${TIMESTAMP}"				# generate a unique ID to tag resources created by this script
if [ -e /dev/urandom ];then
 UNIQUE_ID=$(cat /dev/urandom|LC_CTYPE=C tr -dc "[:alnum:]"|fold -w 32|head -n 1)
fi
TMP_FILE_LIST=()							# array keeps a list of temporary files to cleanup
THIS_SCRIPT="$(basename ${BASH_SOURCE})"	# sciptname

# Do cleanup
function Cleanup() {
color_print "${MYcolor}" "$PF1 function: $FUNCNAME"
  for i in "${!TMP_FILE_LIST[@]}"; do
    if [ -f "${TMP_FILE_LIST[$i]}" ]; then
      #echo -e "deleting ${TMP_FILE_LIST[$i]}"
      rm -f "${TMP_FILE_LIST[$i]}"
    fi
  done
}

# Do cleanup, display error message and exit
function Interrupt() {
  Cleanup
  exitcode=99
  echo -e "\nScript '${THIS_SCRIPT}' aborted by user. $Color_Off"
  exit $exitcode
}

# trap ctrl-c and call interrupt()
trap Interrupt INT
# trap exit and call cleanup()
trap Cleanup   EXIT

function tempfile()
{
  local __resultvar=$1
  local __tmp_file=$(mktemp -t ${THIS_SCRIPT}_tmp_file.XXXXXXXXXXX) || {
    echo -e "$Cyan ......#*** Creation of ${__tmp_file} failed $Color_Off";
    exit 1;
  }
  TMP_FILE_LIST+=("${__tmp_file}")
  if [[ "$__resultvar" ]]; then
    eval $__resultvar="'$__tmp_file'"
  else
    echo -e "$Cyan ......#$__tmp_file"
  fi
}

fi

# ---------------------------------------------------------------------------------------------------------------------------------------------
# end of file
# ---------------------------------------------------------------------------------------------------------------------------------------------
