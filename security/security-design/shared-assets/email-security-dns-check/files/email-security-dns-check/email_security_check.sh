#!/bin/bash
###############################################################################
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Jacco Steur
#
##########################################################################
# email_security_check.sh
# Bash script to run the email security check Python script email_security_check.py
##########################################################################


##########################################################################
# Check if the Python script exists
##########################################################################
SCRIPT_DIR="$(dirname "$0")"
PYTHON_SCRIPT="${SCRIPT_DIR}/scripts/email_security_check.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Python script 'email_security_check.py' not found in $SCRIPT_DIR."
    exit 1
fi

##########################################################################
# Function to display help message
##########################################################################
function usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -s, --sender-domain DOMAIN     Sender domain (the domain where the email comes from)"
    echo "  -f, --eml-file FILE            Path to the .eml file to extract information from"
    echo "      --selector SELECTOR        DKIM selector for sender domain (if known)"
    echo "      --mx-selector SELECTOR     DKIM selector for MX domains (if known)"
    echo "  -t, --txt                      Dump all TXT records for domains being checked"
    echo "      --resolve-spf              Resolve all IP addresses in SPF records and get their locations"
    echo "  -h, --help                     Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 -s example.com"
    echo "  $0 -s example.com --resolve-spf"
    echo "  $0 -s example.com --selector selector1 -t"
    echo "  $0 -f email_file.eml"
    exit 1
}

# Parse command-line arguments
SENDER_DOMAIN=""
EML_FILE=""
SELECTOR=""
MX_SELECTOR=""
TXT_FLAG=""
RESOLVE_SPF_FLAG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--sender-domain)
            SENDER_DOMAIN="$2"
            shift 2
            ;;
        -f|--eml-file)
            EML_FILE="$2"
            shift 2
            ;;
        --selector)
            SELECTOR="$2"
            shift 2
            ;;
        --mx-selector)
            MX_SELECTOR="$2"
            shift 2
            ;;
        -t|--txt)
            TXT_FLAG="--txt"
            shift
            ;;
        --resolve-spf)
            RESOLVE_SPF_FLAG="--resolve-spf"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Ensure that either sender domain or .eml file is provided
if [ -z "$SENDER_DOMAIN" ] && [ -z "$EML_FILE" ]; then
    echo "Error: Please provide a sender domain with -s or an .eml file with -f."
    usage
fi

# Construct the command to run the Python script
CMD="python3 \"$PYTHON_SCRIPT\""

if [ -n "$SENDER_DOMAIN" ]; then
    CMD="$CMD -s \"$SENDER_DOMAIN\""
fi

if [ -n "$EML_FILE" ]; then
    CMD="$CMD -f \"$EML_FILE\""
fi

if [ -n "$SELECTOR" ]; then
    CMD="$CMD --selector \"$SELECTOR\""
fi

if [ -n "$MX_SELECTOR" ]; then
    CMD="$CMD --mx-selector \"$MX_SELECTOR\""
fi

if [ -n "$TXT_FLAG" ]; then
    CMD="$CMD $TXT_FLAG"
fi

if [ -n "$RESOLVE_SPF_FLAG" ]; then
    CMD="$CMD $RESOLVE_SPF_FLAG"
fi

# Execute the command
eval $CMD
