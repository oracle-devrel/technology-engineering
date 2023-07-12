################################################################################
# Copyright (c) 2023, Oracle and/or its affiliates. All rights reserved.
# This software is dual-licensed to you under the Universal Permissive 
# License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl
################################################################################

. ./set-local-vars.sh

fn config function $FN_APP_NAME ${PWD##*/} ociDataSafeCompartmentOCID $OCI_DATASAFE_COMPARTMENT_OCID
fn config function $FN_APP_NAME ${PWD##*/} ociLoggingLogOCID $OCI_LOGGING_LOG_OCID
fn config function $FN_APP_NAME ${PWD##*/} ociOSTrackerBucketName $OCI_OS_TRACKER_BUCKET_NAME
