import os
import yaml
import uuid

RULES_DIR = 'rules'

def create_rule(path, content):
    full_path = os.path.join(RULES_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False)
    print(f"Created {full_path}")

def generate_linux_suspicious_binaries():
    binaries = [
        "netcat", "nc", "nmap", "tcpdump", "wireshark", "gdb", "strace", "wget", "curl", 
        "base64", "dd", "socat", "whoami", "id", "shadow", "passwd", "chown", "chmod", 
        "insmod", "rmmod", "modprobe", "tshark", "ncat", "python", "perl", "ruby", "lua"
    ]
    
    for bin_name in binaries:
        content = {
            "title": f"Suspicious Usage of {bin_name}",
            "id": str(uuid.uuid4()),
            "status": "experimental",
            "description": f"Detects execution of potentially suspicious binary {bin_name}.",
            "logsource": {"product": "linux", "service": "audit"},
            "detection": {
                "selection": {
                    "process_name": bin_name
                },
                "condition": "selection"
            },
            "level": "low",
            "tags": ["attack.execution", "attack.t1204"]
        }
        create_rule(f"linux/suspicious_binaries/sus_bin_{bin_name}.yaml", content)

def generate_oci_audit_events():
    events = [
        ("CreateUser", "com.oraclecloud.identity.user.create"),
        ("DeleteUser", "com.oraclecloud.identity.user.delete"),
        ("CreateGroup", "com.oraclecloud.identity.group.create"),
        ("DeleteGroup", "com.oraclecloud.identity.group.delete"),
        ("AddUserToGroup", "com.oraclecloud.identity.group.adduser"),
        ("RemoveUserFromGroup", "com.oraclecloud.identity.group.removeuser"),
        ("CreatePolicy", "com.oraclecloud.identity.policy.create"),
        ("DeletePolicy", "com.oraclecloud.identity.policy.delete"),
        ("UpdatePolicy", "com.oraclecloud.identity.policy.update"),
        ("CreateVcn", "com.oraclecloud.virtualnetwork.createvcn"),
        ("DeleteVcn", "com.oraclecloud.virtualnetwork.deletevcn"),
        ("CreateSubnet", "com.oraclecloud.virtualnetwork.createsubnet"),
        ("DeleteSubnet", "com.oraclecloud.virtualnetwork.deletesubnet"),
        ("CreateInternetGateway", "com.oraclecloud.virtualnetwork.createinternetgateway"),
        ("DeleteInternetGateway", "com.oraclecloud.virtualnetwork.deleteinternetgateway"),
        ("AttachInternetGateway", "com.oraclecloud.virtualnetwork.attachinternetgateway"),
        ("DetachInternetGateway", "com.oraclecloud.virtualnetwork.detachinternetgateway"),
        ("CreateRouteTable", "com.oraclecloud.virtualnetwork.createroutetable"),
        ("UpdateRouteTable", "com.oraclecloud.virtualnetwork.updateroutetable"),
        ("CreateSecurityList", "com.oraclecloud.virtualnetwork.createsecuritylist"),
        ("UpdateSecurityList", "com.oraclecloud.virtualnetwork.updatesecuritylist"),
        ("CreateInstance", "com.oraclecloud.computeapi.launchinstance"),
        ("TerminateInstance", "com.oraclecloud.computeapi.terminateinstance"),
        ("StopInstance", "com.oraclecloud.computeapi.stopinstance"),
        ("StartInstance", "com.oraclecloud.computeapi.startinstance"),
        ("CreateBucket", "com.oraclecloud.objectstorage.createbucket"),
        ("DeleteBucket", "com.oraclecloud.objectstorage.deletebucket"),
        ("UpdateBucket", "com.oraclecloud.objectstorage.updatebucket"),
        ("CreateKey", "com.oraclecloud.kms.createkey"),
        ("DeleteKey", "com.oraclecloud.kms.deletekey")
    ]
    
    for name, event_type in events:
        content = {
            "title": f"OCI Action: {name}",
            "id": str(uuid.uuid4()),
            "status": "stable",
            "description": f"Detects the execution of {name} action in OCI.",
            "logsource": {"product": "oci", "service": "audit"},
            "detection": {
                "selection": {
                    "event_type": event_type
                },
                "condition": "selection"
            },
            "level": "informational",
            "tags": ["oci.audit"]
        }
        create_rule(f"cloud/oci/audit_events/oci_audit_{name.lower()}.yaml", content)

def generate_windows_lolbins():
    lolbins = [
        "certutil", "bitsadmin", "powershell", "wmic", "mshta", "rundll32", "regsvr32", "schtasks", "at", 
        "sc", "net", "net1", "cmd", "cscript", "wscript", "tasklist", "taskkill", "whoami", "ipconfig", "systeminfo"
    ]
    
    for bin_name in lolbins:
         content = {
            "title": f"Windows LOLBin Usage: {bin_name}",
            "id": str(uuid.uuid4()),
            "status": "experimental",
            "description": f"Detects usage of Living off the Land binary {bin_name}.",
            "logsource": {"product": "windows", "service": "process_creation"},
            "detection": {
                "selection": {
                    "process_name": f"{bin_name}.exe"
                },
                "condition": "selection"
            },
            "level": "medium",
            "tags": ["attack.defense_evasion", "attack.t1218"]
        }
         create_rule(f"windows/process_creation/win_lolbin_{bin_name}.yaml", content)

def generate_cloud_guard_problems():
    problems = [
        "INSTANCE_PUBLIC_IP", "VCN_Security_List_Port_SSH", "VCN_Security_List_Port_RDP", 
        "IAM_User_API_Key_Old", "IAM_User_Console_Password_Old", "Bucket_Public_Read", 
        "Bucket_Public_Write", "VCN_Flow_Log_Disabled", "Audit_Log_Retention", 
        "Instance_Principals_Enabled", "Policy_Too_Permissive", "Group_Has_Too_Many_Admins"
    ]
    
    for problem in problems:
        content = {
            "title": f"Cloud Guard Problem: {problem.replace('_', ' ')}",
            "id": str(uuid.uuid4()),
            "status": "stable",
            "description": f"Detects Cloud Guard reporting problem: {problem}.",
            "logsource": {"product": "oci", "service": "cloud_guard"},
            "detection": {
                "selection": {
                    "problem_name": problem
                },
                "condition": "selection"
            },
            "level": "high",
            "tags": ["oci.cloud_guard"]
        }
        create_rule(f"cloud/oci/cloud_guard/cg_{problem.lower()}.yaml", content)

if __name__ == "__main__":
    generate_linux_suspicious_binaries()
    generate_oci_audit_events()
    generate_windows_lolbins()
    generate_cloud_guard_problems()
