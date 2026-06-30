import json
import os

PROJECT_DIR = 'oci-log-analytics-detections'
QUERIES_DIR = os.path.join(PROJECT_DIR, 'queries')
DASHBOARD_FILE = os.path.join(PROJECT_DIR, 'SOC_Security_Dashboard.sh')

# Define which queries we want on the dashboard
dashboard_widgets = [
    {"title": "OCI Console Login Failures", "query_file": "oci_console_login_from_unusual_ip.json", "type": "CHART"},
    {"title": "Top Suspicious Linux Binaries", "query_file": "suspicious_usage_of_netcat.json", "type": "TABLE"},
    {"title": "Critical IAM Policy Changes", "query_file": "oci_iam_policy_modified.json", "type": "TABLE"},
    {"title": "Object Storage Public Buckets", "query_file": "oci_object_storage_bucket_made_public.json", "type": "TABLE"},
    {"title": "VCN Security List Open to World", "query_file": "oci_vcn_security_list_open_to_world.json", "type": "TABLE"},
    {"title": "SSH Failed Logins Trend", "query_file": "linux_ssh_failed_login.json", "type": "CHART"},
    {"title": "Cloud Guard Critical Problems", "query_file": "cloud_guard_problem_instance_public_ip.json", "type": "TABLE"}
]

def generate_oci_cli_commands():
    commands = [
        "#!/bin/bash",
        "# OCI CLI commands to create Saved Searches and Dashboard",
        "# Note: You must replace <COMPARTMENT_OCID> with your actual compartment OCID",
        "COMPARTMENT_ID='<COMPARTMENT_OCID>'",
        ""
    ]
    
    for widget in dashboard_widgets:
        query_path = os.path.join(QUERIES_DIR, widget['query_file'])
        if not os.path.exists(query_path):
            print(f"Warning: {query_path} not found.")
            continue
            
        with open(query_path, 'r') as f:
            data = json.load(f)
            
        commands.append(f"echo 'Creating Saved Search: {widget['title']}'")
        commands.append(f"# Query: {data['query']}")
        commands.append("")

    commands.append("# To create the dashboard, use the OCI Console to drag and drop these saved searches")
    
    with open(DASHBOARD_FILE, 'w') as f:
        f.write("\n".join(commands))
    
    print(f"Generated dashboard setup script: {DASHBOARD_FILE}")

if __name__ == "__main__":
    generate_oci_cli_commands()
