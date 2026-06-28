import os
import yaml

rules = [
    {
        "path": "rules/cloud/oci/oci_vcn_open_to_world.yaml",
        "content": {
            "title": "OCI VCN Security List Open to World",
            "id": "uuid-1",
            "status": "experimental",
            "description": "Detects creation or update of a Security List allowing ingress from 0.0.0.0/0.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": ["com.oraclecloud.virtualnetwork.createsecuritylist", "com.oraclecloud.virtualnetwork.updatesecuritylist"],
                    "request_action": "POST",
                    "response_payload|contains": "0.0.0.0/0"
                },
                "condition": "selection"
            },
            "level": "high",
            "tags": ["attack.defense_evasion"]
        }
    },
    {
        "path": "rules/cloud/oci/oci_iam_policy_change.yaml",
        "content": {
            "title": "OCI IAM Policy Modified",
            "id": "uuid-2",
            "status": "stable",
            "description": "Detects changes to OCI IAM Policies.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": ["com.oraclecloud.identity.policy.create", "com.oraclecloud.identity.policy.update", "com.oraclecloud.identity.policy.delete"],
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.persistence"]
        }
    },
    {
        "path": "rules/cloud/oci/oci_bucket_public.yaml",
        "content": {
            "title": "OCI Object Storage Bucket Made Public",
            "id": "uuid-3",
            "status": "high",
            "description": "Detects when a bucket's visibility is set to public.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": "com.oraclecloud.objectstorage.updatebucket",
                    "response_payload|contains": '"publicAccessType":"ObjectRead"'
                },
                "condition": "selection"
            },
            "level": "high",
            "tags": ["attack.exfiltration"]
        }
    },
    {
        "path": "rules/cloud/oci/oci_api_key_upload.yaml",
        "content": {
            "title": "OCI API Key Uploaded",
            "id": "uuid-4",
            "status": "stable",
            "description": "Detects upload of a new API key to a user account.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": "com.oraclecloud.identity.user.uploadapikey"
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.persistence"]
        }
    },
    {
        "path": "rules/linux/linux_sudo_usage.yaml",
        "content": {
            "title": "Linux Sudo Usage",
            "id": "uuid-5",
            "status": "stable",
            "description": "Detects execution of sudo commands.",
            "logsource": {"product": "linux", "service": "auth"},
            "detection": {
                "selection": {
                    "process_name": "sudo",
                    "message|contains": "COMMAND="
                },
                "condition": "selection"
            },
            "level": "low",
            "tags": ["attack.privilege_escalation"]
        }
    },
    {
        "path": "rules/linux/linux_ssh_failed.yaml",
        "content": {
            "title": "Linux SSH Failed Login",
            "id": "uuid-6",
            "status": "stable",
            "description": "Detects failed SSH login attempts.",
            "logsource": {"product": "linux", "service": "auth"},
            "detection": {
                "selection": {
                    "process_name": "sshd",
                    "message|contains": "Failed password"
                },
                "condition": "selection"
            },
            "level": "low",
            "tags": ["attack.initial_access"]
        }
    },
     {
        "path": "rules/cloud/oci/oci_compute_terminate.yaml",
        "content": {
            "title": "OCI Compute Instance Terminated",
            "id": "uuid-7",
            "status": "stable",
            "description": "Detects termination of a compute instance.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": "com.oraclecloud.computeapi.terminateinstance"
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.impact"]
        }
    },
    {
        "path": "rules/cloud/oci/oci_network_security_group_update.yaml",
        "content": {
            "title": "OCI Network Security Group Updated",
            "id": "uuid-8",
            "status": "stable",
            "description": "Detects updates to Network Security Groups (NSGs).",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                     "event_type": ["com.oraclecloud.virtualnetwork.updatenetworksecuritygroup", "com.oraclecloud.virtualnetwork.addnetworksecuritygroupsecurityrules"]
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.defense_evasion"]
        }
    },
    {
        "path": "rules/cloud/oci/oci_waf_update.yaml",
        "content": {
            "title": "OCI WAF Configuration Updated",
            "id": "uuid-9",
            "status": "stable",
            "description": "Detects changes to Web Application Firewall configurations.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": ["com.oraclecloud.waf.updatewebappfirewall", "com.oraclecloud.waf.updatewebappfirewallpolicy"]
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.defense_evasion"]
        }
    },
     {
        "path": "rules/cloud/oci/oci_route_table_update.yaml",
        "content": {
            "title": "OCI Route Table Update",
            "id": "uuid-10",
            "status": "stable",
            "description": "Detects changes to VCN Route Tables.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": ["com.oraclecloud.virtualnetwork.updateroutetable", "com.oraclecloud.virtualnetwork.createroutetable"]
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.persistence"]
        }
    }
]

for rule in rules:
    # Ensure directory exists
    os.makedirs(os.path.dirname(rule['path']), exist_ok=True)
    
    with open(rule['path'], 'w') as f:
        yaml.dump(rule['content'], f, sort_keys=False)
    print(f"Created {rule['path']}")
