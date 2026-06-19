#!/bin/bash
# OCI CLI commands to create Saved Searches and Dashboard
# Note: You must replace <COMPARTMENT_OCID> with your actual compartment OCID
COMPARTMENT_ID='<COMPARTMENT_OCID>'

echo 'Creating Saved Search: OCI Console Login Failures'
# Query: 'Log Source' = 'OCI Audit Logs' | where Event Type = 'com.oraclecloud.identity.authentication.login' and Status = 'Success'

echo 'Creating Saved Search: Top Suspicious Linux Binaries'
# Query: 'Log Source' = 'OCI Audit Logs' | where 'Process Name' = 'netcat'

echo 'Creating Saved Search: Critical IAM Policy Changes'
# Query: 'Log Source' = 'OCI Audit Logs' | where (Event Type = 'com.oraclecloud.identity.policy.create' or Event Type = 'com.oraclecloud.identity.policy.update' or Event Type = 'com.oraclecloud.identity.policy.delete')

echo 'Creating Saved Search: Object Storage Public Buckets'
# Query: 'Log Source' = 'OCI Audit Logs' | where Event Type = 'com.oraclecloud.objectstorage.updatebucket' and 'Response Payload' like '*"publicAccessType":"ObjectRead"*'

echo 'Creating Saved Search: VCN Security List Open to World'
# Query: 'Log Source' = 'OCI Audit Logs' | where (Event Type = 'com.oraclecloud.virtualnetwork.createsecuritylist' or Event Type = 'com.oraclecloud.virtualnetwork.updatesecuritylist') and Request Action Type = 'POST' and 'Response Payload' like '*0.0.0.0/0*'

echo 'Creating Saved Search: SSH Failed Logins Trend'
# Query: 'Log Source' = 'OCI Audit Logs' | where 'Process Name' = 'sshd' and Message like '*Failed password*'

echo 'Creating Saved Search: Cloud Guard Critical Problems'
# Query: 'Log Source' = 'OCI Audit Logs' | where Problem Name = 'INSTANCE_PUBLIC_IP'

# To create the dashboard, use the OCI Console to drag and drop these saved searches