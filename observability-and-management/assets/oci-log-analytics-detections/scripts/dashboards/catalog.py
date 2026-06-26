"""Dashboard catalog: the DASHBOARDS definition + Sentinel group loader.

Auto-extracted from deploy_dashboard.py (behavior-preserving). Pure data plus the
deterministic Sentinel-group loader; no OCI client calls at import beyond reading
local query JSON.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oci_config import QUERIES_DIR


OCTO_APM_WORKSHOP_TIME_SELECTION = {"timePeriod": "l21d"}


def octo_apm_workshop_widget(title, query_file):
    """Return an Octo workshop widget pinned to the workshop evidence window."""
    return {
        "title": title,
        "query_file": query_file,
        "time_selection": OCTO_APM_WORKSHOP_TIME_SELECTION.copy(),
    }


DASHBOARDS = {
    "SOC Overview Dashboard": {
        "description": "Executive cross-domain security command center for the 21-day demo. Opens with a KPI tile row spanning all four attack stories (Cloud/Identity, Endpoint, Web/App, Network/C2), then an attack-volume timeline and MITRE sunburst, a clickable top-attacker table, the global multicloud health map, the Kubernetes/OKE attack rollup, and a row of critical detections for fast drilldown.",
        "widgets": [
            # ── Row 1: KPI tiles — one headline number per attack story (21-day window) ──
            {"title": "Cloud: Critical Audit Events", "query_file": "hunting/demo_cloud_critical_kpi.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Endpoint: Critical Detections", "query_file": "hunting/coordinator_total_hits_kpi.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Web/App: Browser Attacks", "query_file": "apps/apm_total_attacks_kpi.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Network: C2 Affected Hosts", "query_file": "hunting/c2_affected_hosts_kpi.json",
             "time_selection": {"timePeriod": "l21d"}},
            # ── Row 2: when did each story fire + MITRE composition ──
            {"title": "Attack Activity Timeline (21d)", "query_file": "hunting/demo_attack_timeline.json"},
            {"title": "MITRE Tactics x Process", "query_file": "hunting/bluelight_mitre_tactics_sunburst.json",
             "time_selection": {"timePeriod": "l21d"}},
            # ── Row 3: clickable attacker drilldown ──
            {"title": "Top Attacker Source IPs (Cloud)", "query_file": "hunting/demo_top_attacker_ips.json"},
            # ── Row 4: global posture ──
            {"title": "Global Multicloud Health Map", "query_file": "hunting/multicloud_geo_health_regional_map.json",
             "time_selection": {"timePeriod": "l21d"}},
            # ── Row 5: Kubernetes / OKE attack rollup ──
            {"title": "Kubernetes / OKE Attack Overview", "query_file": "apps/oke_kubernetes_attack_overview.json",
             "time_selection": {"timePeriod": "l21d"}},
            # ── Row 6+: critical detections — fast drilldown across the four stories ──
            {"title": "Cloud: IAM Policy Modified", "query_file": "oci_iam_policy_modified.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Cloud: KMS Key Deletion", "query_file": "oci_kms_key_scheduled_for_deletion.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Cloud: Compartment Deleted", "query_file": "oci_compartment_deleted.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Endpoint: Reverse Shell (Linux)", "query_file": "linux_reverse_shell_detected.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Endpoint: Credential Dumping (Win)", "query_file": "windows_credential_dumping_via_procdump.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Network: VCN Open to World", "query_file": "oci_vcn_security_list_open_to_world.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Web: OWASP Multi-Stage Attack", "query_file": "hunting/web_owasp_multi_stage_attack.json",
             "time_selection": {"timePeriod": "l21d"}},
            {"title": "Web: WAF Multi-Attack Score", "query_file": "hunting/waf_multi_attack_scoring.json",
             "time_selection": {"timePeriod": "l21d"}},
        ]
    },
    "SOC: OCI STIG Compliance Dashboard": {
        "description": "OCI STIG compliance monitoring: MFA, key rotation, audit configuration, network security, identity governance.",
        "widgets": [
            {"title": "STIG: MFA Disabled", "query_file": "oci_user_mfa_not_enabled.json"},
            {"title": "STIG: Identity Provider Created", "query_file": "oci_identity_provider_created.json"},
            {"title": "STIG: Dynamic Group Created", "query_file": "oci_dynamic_group_created.json"},
            {"title": "STIG: Auth Token Created", "query_file": "oci_auth_token_created.json"},
            {"title": "STIG: Compartment Deleted", "query_file": "oci_compartment_deleted.json"},
            {"title": "STIG: Audit Config Changed", "query_file": "oci_audit_configuration_changed.json"},
            {"title": "STIG: Key Rotation Update", "query_file": "oci_vault_key_rotation_overdue.json"},
            {"title": "STIG: Security List All Protocols", "query_file": "oci_security_list_allows_all_protocols.json"},
            {"title": "STIG: Network Firewall Modified", "query_file": "oci_network_firewall_policy_modified.json"},
            {"title": "STIG: VCN Peering Created", "query_file": "oci_vcn_peering_connection_created.json"},
            {"title": "STIG: Cross-Region Data Copy", "query_file": "oci_cross-region_data_copy.json"},
            {"title": "STIG: Pre-Auth Request Created", "query_file": "oci_object_storage_pre-authenticated_request_created.json"},
            {"title": "STIG: Cloud Shell Session", "query_file": "oci_cloud_shell_session_started.json"},
            {"title": "STIG: Function Invoked", "query_file": "oci_function_invoked.json"},
            {"title": "STIG: Vault Secret Deleted", "query_file": "oci_vault_secret_deleted.json"},
            {"title": "STIG: User Password Reset", "query_file": "oci_user_password_reset_by_admin.json"},
            {"title": "STIG: Customer Secret Key", "query_file": "oci_customer_secret_key_created.json"},
        ]
    },
    "SOC: OCI Audit Security Dashboard": {
        "description": "OCI Audit event monitoring: IAM, Network, Compute, Storage, KMS, and Database.",
        "widgets": [
            {"title": "OCI: Console Login from Unusual IP", "query_file": "oci_console_login_from_unusual_ip.json"},
            {"title": "OCI: Console Login Failure", "query_file": "oci_console_login_failure.json"},
            {"title": "OCI: IAM Policy Modified", "query_file": "oci_iam_policy_modified.json"},
            {"title": "OCI: Admin Policy - Manage All", "query_file": "oci_iam_admin_policy_created_with_manage_all.json"},
            {"title": "OCI: API Key Uploaded", "query_file": "oci_api_key_uploaded.json"},
            {"title": "OCI: Compute Instance Terminated", "query_file": "oci_compute_instance_terminated.json"},
            {"title": "OCI: Autonomous DB Terminated", "query_file": "oci_autonomous_database_terminated.json"},
            {"title": "OCI: DB System Terminated", "query_file": "oci_database_system_terminated.json"},
            {"title": "OCI: KMS Key Scheduled Deletion", "query_file": "oci_kms_key_scheduled_for_deletion.json"},
            {"title": "OCI: Load Balancer Deleted", "query_file": "oci_network_load_balancer_deleted.json"},
            {"title": "OCI: Bucket Made Public", "query_file": "oci_object_storage_bucket_made_public.json"},
            {"title": "OCI: NSG Updated", "query_file": "oci_network_security_group_updated.json"},
            {"title": "OCI: Route Table Updated", "query_file": "oci_route_table_update.json"},
            {"title": "OCI: WAF Configuration Updated", "query_file": "oci_waf_configuration_updated.json"},
            {"title": "OCI: VCN Security List Open", "query_file": "oci_vcn_security_list_open_to_world.json"},
            {"title": "OCI: Pre-Auth Request", "query_file": "oci_object_storage_pre-authenticated_request_created.json"},
            {"title": "OCI: Bastion Session Created", "query_file": "oci_bastion_session_created.json"},
            {"title": "OCI: Console Connection", "query_file": "oci_instance_console_connection_created.json"},
            {"title": "OCI: Notification Subscription", "query_file": "oci_notification_subscription_created.json"},
            {"title": "OCI: Log Group Deleted", "query_file": "oci_log_group_deleted.json"},
            {"title": "OCI: Cloud Infra Discovery", "query_file": "oci_cloud_infrastructure_discovery.json"},
            {"title": "OCI: Password Spraying", "query_file": "oci_password_spraying_attack.json"},
        ]
    },
    "SOC: Cloud Guard Security Dashboard": {
        "description": "Cloud Guard problem monitoring for security posture issues.",
        "widgets": [
            {"title": "CG: Bucket Public Read", "query_file": "cloud_guard_problem_bucket_public_read.json"},
            {"title": "CG: Bucket Public Write", "query_file": "cloud_guard_problem_bucket_public_write.json"},
            {"title": "CG: Instance Public IP", "query_file": "cloud_guard_problem_instance_public_ip.json"},
            {"title": "CG: Instance Principals", "query_file": "cloud_guard_problem_instance_principals_enabled.json"},
            {"title": "CG: Policy Too Permissive", "query_file": "cloud_guard_problem_policy_too_permissive.json"},
            {"title": "CG: Too Many Admins", "query_file": "cloud_guard_problem_group_has_too_many_admins.json"},
            {"title": "CG: Stale API Key", "query_file": "cloud_guard_problem_iam_user_api_key_old.json"},
            {"title": "CG: Stale Console Password", "query_file": "cloud_guard_problem_iam_user_console_password_old.json"},
            {"title": "CG: Audit Log Retention", "query_file": "cloud_guard_problem_audit_log_retention.json"},
            {"title": "CG: VCN Flow Logs Disabled", "query_file": "cloud_guard_problem_vcn_flow_log_disabled.json"},
            {"title": "CG: SSH Port Open", "query_file": "cloud_guard_problem_vcn_security_list_port_ssh.json"},
            {"title": "CG: RDP Port Open", "query_file": "cloud_guard_problem_vcn_security_list_port_rdp.json"},
        ]
    },
    "SOC: Cloud Guard Instance Security Dashboard": {
        "description": "Cloud Guard Instance Security and OSQuery result monitoring for OCI workload runtime posture.",
        "widgets": [
            {"title": "CGIS: Pack Coverage", "query_file": "cloud_guard_instance_security_pack_coverage.json"},
            {"title": "CGIS: Findings by Host", "query_file": "cloud_guard_instance_security_findings_by_host.json"},
            {"title": "CGIS: Findings by Pack Query", "query_file": "cloud_guard_instance_security_findings_by_pack_query.json"},
            {"title": "CGIS: High Severity Pivots", "query_file": "cloud_guard_instance_security_high_severity_pivots.json"},
            {"title": "CGIS: Instance to Query Link", "query_file": "cloud_guard_instance_security_instance_to_query_link.json"},
            {"title": "CGIS: Raw Result Detail", "query_file": "cloud_guard_instance_security_raw_result_detail.json"},
        ]
    },
    "SOC: Linux Security Dashboard": {
        "description": "Linux endpoint security: SSH, sudo, GTFOBins, reverse shells, persistence, anti-forensics, container escape.",
        "widgets": [
            {"title": "Linux: Reverse Shell Detected", "query_file": "linux_reverse_shell_detected.json"},
            {"title": "Linux: SSH Failed Logins", "query_file": "linux_ssh_failed_login.json"},
            {"title": "Linux: Sudo Usage", "query_file": "linux_sudo_usage.json"},
            {"title": "Linux: Crontab Persistence", "query_file": "linux_crontab_modification.json"},
            {"title": "Linux: SSH Authorized Keys", "query_file": "linux_ssh_authorized_keys_modified.json"},
            {"title": "Linux: History Cleared", "query_file": "linux_history_file_cleared.json"},
            {"title": "Linux: Container Escape", "query_file": "linux_container_escape_attempt.json"},
            {"title": "Linux: LD_PRELOAD Hijack", "query_file": "linux_ld_preload_library_hijacking.json"},
            {"title": "Linux: Kernel Module /tmp", "query_file": "linux_kernel_module_loaded_from_temp_directory.json"},
            {"title": "Linux: Passwd File Modified", "query_file": "linux_password_file_direct_modification.json"},
            {"title": "Linux: Ptrace Injection", "query_file": "linux_process_injection_via_ptrace.json"},
            {"title": "Linux: Network Redirect", "query_file": "linux_suspicious_network_traffic_redirect.json"},
            {"title": "Linux: Systemd Persistence", "query_file": "linux_systemd_service_persistence.json"},
            {"title": "Linux: SSH Tunneling", "query_file": "linux_ssh_tunneling_detected.json"},
            {"title": "Linux: Download to /tmp", "query_file": "linux_suspicious_download_to_tmp.json"},
            {"title": "Linux: /dev/shm Execution", "query_file": "linux_process_execution_from_devshm.json"},
            {"title": "Linux: Sudoers Modified", "query_file": "linux_sudoers_file_modification.json"},
            {"title": "Linux: Shell Profile Persist", "query_file": "linux_shell_profile_persistence.json"},
            {"title": "Linux: At Job Scheduled", "query_file": "linux_at_job_scheduled.json"},
            {"title": "Linux: DNS Tunneling", "query_file": "linux_dns_tunneling_detected.json"},
        ]
    },
    "SOC: Linux Advanced Threats Dashboard": {
        "description": "Linux advanced threat detection: C2, exfiltration, discovery, web shells, cryptomining, and post-exploitation.",
        "widgets": [
            {"title": "Linux: Hosts File Modified", "query_file": "linux_hosts_file_modification.json"},
            {"title": "Linux: /proc Memory Access", "query_file": "linux_process_memory_access_via_proc.json"},
            {"title": "Linux: Web Shell Created", "query_file": "linux_web_shell_file_creation.json"},
            {"title": "Linux: Cryptominer Detected", "query_file": "linux_cryptominer_activity_detected.json"},
            {"title": "Linux: Log Tampering", "query_file": "linux_log_file_tampering.json"},
            {"title": "Linux: Enumeration Script", "query_file": "linux_post-exploitation_enumeration_script.json"},
            {"title": "Linux: Bind Shell", "query_file": "linux_bind_shell_listener.json"},
            {"title": "Linux: Suspicious Cron Job", "query_file": "linux_suspicious_cron_job_content.json"},
            {"title": "Linux: Hidden File Creation", "query_file": "linux_hidden_file_or_directory_creation_in_suspicious_location.json"},
            {"title": "Linux: Network Scanning", "query_file": "linux_network_service_scanning.json"},
            {"title": "Linux: User Discovery", "query_file": "linux_system_owner_and_user_discovery.json"},
            {"title": "Linux: Remote Service Abuse", "query_file": "linux_external_remote_service_abuse.json"},
            {"title": "Linux: Exfil Alt Protocol", "query_file": "linux_exfiltration_over_alternative_protocol.json"},
            {"title": "Linux: Archive for Exfil", "query_file": "linux_archive_data_collected_for_exfiltration.json"},
            {"title": "Linux: Sensitive Data Access", "query_file": "linux_sensitive_data_collection_from_local_system.json"},
            {"title": "Linux: Proxy/Tunnel Tool", "query_file": "linux_proxy_and_tunneling_tool_detected.json"},
            {"title": "Linux: Encrypted C2", "query_file": "linux_encrypted_channel_c2_communication.json"},
            {"title": "Linux: SUID Binary Created", "query_file": "linux_setuid_binary_creation.json"},
        ]
    },
    "SOC: Windows Security Dashboard": {
        "description": "Windows endpoint security: ransomware indicators, AMSI bypass, WMI persistence, credential dumping, LOLBins.",
        "widgets": [
            {"title": "Win: Shadow Copy Deletion", "query_file": "windows_shadow_copy_deletion.json"},
            {"title": "Win: Boot Config Modified", "query_file": "windows_boot_configuration_modified.json"},
            {"title": "Win: Credential Dump (LSASS)", "query_file": "windows_credential_dumping_via_procdump.json"},
            {"title": "Win: Encoded PowerShell", "query_file": "windows_encoded_powershell_execution.json"},
            {"title": "Win: AMSI Bypass", "query_file": "windows_amsi_bypass_attempt.json"},
            {"title": "Win: WMI Persistence", "query_file": "windows_wmi_event_subscription_persistence.json"},
            {"title": "Win: Registry Run Key", "query_file": "windows_registry_run_key_modification.json"},
            {"title": "Win: DLL Side-Loading", "query_file": "windows_dll_side-loading_via_suspicious_path.json"},
            {"title": "Win: Certutil Download/Decode", "query_file": "windows_certutil_download_or_decode.json"},
            {"title": "Win: Service Creation (SC)", "query_file": "windows_service_creation_via_sc.json"},
            {"title": "Win: PowerShell LOLBin", "query_file": "windows_lolbin_usage_powershell.json"},
            {"title": "Win: WMIC LOLBin", "query_file": "windows_lolbin_usage_wmic.json"},
            {"title": "Win: Mimikatz Patterns", "query_file": "windows_mimikatz_execution_patterns.json"},
            {"title": "Win: Firewall Rule Change", "query_file": "windows_firewall_rule_modification.json"},
            {"title": "Win: RDP Lateral Movement", "query_file": "windows_rdp_lateral_movement.json"},
            {"title": "Win: Scheduled Task (schtasks)", "query_file": "windows_scheduled_task_creation_via_schtasks.json"},
            {"title": "Win: Scheduled Task Event", "query_file": "windows_scheduled_task_created_or_updated_event.json"},
            {"title": "Win: Service Installed Event", "query_file": "windows_service_installed_event_log.json"},
            {"title": "Win: PS Download Cradle", "query_file": "windows_powershell_download_cradle.json"},
            {"title": "Win: PowerShell 4104 Suspicious", "query_file": "windows_powershell_script_block_suspicious_content.json"},
            {"title": "Win: Defender Malware/Tamper", "query_file": "windows_defender_malware_or_remediation_event.json"},
            {"title": "Win: LSASS Memory Access", "query_file": "windows_lsass_memory_access.json"},
            {"title": "Win: Event Log Clearing", "query_file": "windows_event_log_clearing.json"},
            {"title": "Win: Native Log Cleared", "query_file": "windows_security_log_cleared_event.json"},
            {"title": "Win: Audit Policy Changed", "query_file": "windows_audit_policy_changed.json"},
            {"title": "Win: ClickFix PowerShell", "query_file": "clickfix_fake_captcha_powershell_execution.json"},
            {"title": "Win: PsExec Lateral Move", "query_file": "windows_psexec_remote_execution.json"},
        ]
    },
    "SOC: Windows Advanced Threats Dashboard": {
        "description": "Windows advanced threat detection: Kerberoasting, Golden Ticket, DCSync, Mimikatz, pass-the-ticket, privilege escalation — all against real GOAD AD lab data (3M+ events).",
        "widgets": [
            {"title": "Kerb: RC4 Ticket (Kerberoast)", "query_file": "kerberoasting_rc4_ticket_request.json"},
            {"title": "Kerb: SPN Sweep", "query_file": "kerberoasting_spn_sweep.json"},
            {"title": "Kerb: Pre-Auth Failures", "query_file": "windows_kerberos_pre_authentication_failures.json"},
            {"title": "NTLM: Auth Failures", "query_file": "windows_ntlm_authentication_failures.json"},
            {"title": "Golden Ticket: RC4 TGT", "query_file": "golden_ticket_anomaly.json"},
            {"title": "DCSync: Directory Replication", "query_file": "dcsync_directory_replication.json"},
            {"title": "Pass-the-Ticket: Explicit Cred", "query_file": "pass_the_ticket_logon.json"},
            {"title": "PrivEsc: Sensitive Privileges", "query_file": "privilege_escalation_sensitive_privileges.json"},
            {"title": "PrivEsc: Group Membership", "query_file": "windows_privileged_group_membership_change_event.json"},
            {"title": "Lateral: Network Logon Sweep", "query_file": "lateral_movement_logon_pattern.json"},
            {"title": "Lateral: Admin Share Events", "query_file": "windows_admin_share_access_spike_event.json"},
            {"title": "Brute Force: Failed Logons", "query_file": "brute_force_failed_logon_spike.json"},
            {"title": "Discovery: Account/Group Enum", "query_file": "windows_account_or_group_enumeration_spike.json"},
            {"title": "PS: Suspicious Commands", "query_file": "powershell_suspicious_commands.json"},
            {"title": "CMD: Suspicious Execution", "query_file": "cmd_suspicious_child_process.json"},
            {"title": "Mimikatz: Command Indicators", "query_file": "mimikatz_command_and_module_indicators_in_process_logs.json"},
            {"title": "Cred Manager: Dump Activity", "query_file": "credential_manager_access.json"},
            {"title": "Group Enum: SharpHound/BloodH", "query_file": "security_group_enumeration.json"},
            {"title": "Hunt: Kerb RC4/AES Ratio", "query_file": "hunting/kerberoasting_anomaly_detection.json"},
            {"title": "Hunt: AD Attack Timeline", "query_file": "hunting/ad_attack_timeline.json"},
            {"title": "Win: Screen Capture", "query_file": "windows_screen_capture_activity.json"},
            {"title": "Win: Remote Access Tool", "query_file": "windows_remote_access_tool_detected.json"},
            {"title": "Win: Token Manipulation", "query_file": "windows_access_token_manipulation.json"},
        ]
    },
    "SOC: GOAD Caldera Operations Dashboard": {
        "description": "Maps the 5 Caldera adversary operations from c7_run_caldera_operations.sh (Discovery, Credential Access, Lateral Movement, Collection, Exfiltration) to detection rules firing on the 10 GOAD + Apex AD Windows hosts (kingslanding, winterfell, meereen, castelblack, braavos, hq-dc01, eu-dc01, eu-app01, apac-dc01, apac-db01). Each Caldera operation phase maps to a row of detection tiles plus two host-scoped hunting tiles (sandcat agent activity + multi-stage attack chain) that filter to the 11 lab Entities so red-team noise stays scoped and BLUE drilldowns stay attributable to a specific Caldera op.",
        "widgets": [
            {"title": "Op1 Discovery: AD Enum (AdFind)", "query_file": "ad_enumeration_via_adfind.json"},
            {"title": "Op1 Discovery: BloodHound", "query_file": "bloodhound_ad_enumeration.json"},
            {"title": "Op1 Discovery: Domain Trust (nltest)", "query_file": "domain_trust_discovery_via_nltest.json"},
            {"title": "Op1 Discovery: Net View Shares", "query_file": "network_share_enumeration_via_net_view.json"},
            {"title": "Op1 Discovery: Win Share Enum", "query_file": "windows_network_share_discovery.json"},
            {"title": "Op2 CredAccess: Kerberoast RC4", "query_file": "kerberoasting_rc4_ticket_request.json"},
            {"title": "Op2 CredAccess: AS-REP Roasting", "query_file": "as-rep_roasting_via_rubeus.json"},
            {"title": "Op2 CredAccess: LSASS via comsvcs", "query_file": "lsass_memory_dump_via_comsvcs_dll.json"},
            {"title": "Op2 CredAccess: DCSync (Non-DC)", "query_file": "dcsync_directory_replication.json"},
            {"title": "Op2 CredAccess: Mimikatz Indicators", "query_file": "mimikatz_command_and_module_indicators_in_process_logs.json"},
            {"title": "Op3 Lateral: PSExec Remote Exec", "query_file": "windows_psexec_remote_execution.json"},
            {"title": "Op3 Lateral: WinRM (PowerShell)", "query_file": "winrm_lateral_movement_via_powershell.json"},
            {"title": "Op3 Lateral: Admin Share (net use)", "query_file": "windows_admin_share_access_via_net_use.json"},
            {"title": "Op3 Lateral: Pass-the-Ticket", "query_file": "pass_the_ticket_logon.json"},
            {"title": "Op3 Lateral: Tool Transfer (robocopy)", "query_file": "lateral_tool_transfer_via_robocopy.json"},
            {"title": "Op4 Collection: 7-Zip Archive", "query_file": "data_compression_for_exfiltration_via_7zip.json"},
            {"title": "Op4 Collection: Screen Capture", "query_file": "windows_screen_capture_activity.json"},
            {"title": "Op4 Collection: Data Staging", "query_file": "windows_data_staging_for_exfiltration.json"},
            {"title": "Op5 Exfil: BITS Job Abuse", "query_file": "windows_bits_job_abuse_for_persistence.json"},
            {"title": "Op5 Exfil: PowerShell Download Cradle", "query_file": "windows_powershell_download_cradle.json"},
            {"title": "Op5 Exfil: Large HTTP Response", "query_file": "unusually_large_http_response_data_exfiltration.json"},
            {"title": "Hunt: Sandcat Agent Activity (GOAD/Apex)", "query_file": "hunting/goad_caldera_sandcat_activity.json"},
            {"title": "Hunt: Caldera Attack Chain (GOAD/Apex)", "query_file": "hunting/goad_caldera_attack_chain.json"},
        ]
    },
    "SOC: Threat Hunting Dashboard": {
        "description": "Advanced threat hunting analytics inspired by the Threat Hunter's Cookbook. Uses frequency analysis, rare value detection, anomaly scoring, multi-stage correlation, and grouping techniques across all log sources.",
        "widgets": [
            {"title": "Hunt: SSH Brute Force (Frequency)", "query_file": "hunting/ssh_brute_force_frequency.json"},
            {"title": "Hunt: OCI Console Brute Force", "query_file": "hunting/oci_console_brute_force.json"},
            {"title": "Hunt: Windows Rare Processes", "query_file": "hunting/windows_rare_process.json"},
            {"title": "Hunt: Linux Rare Processes", "query_file": "hunting/linux_rare_process.json"},
            {"title": "Hunt: Long Command Lines", "query_file": "hunting/windows_long_command_line.json"},
            {"title": "Hunt: OCI IAM Rapid Changes", "query_file": "hunting/oci_iam_rapid_changes.json"},
            {"title": "Hunt: Lateral Movement Cluster", "query_file": "hunting/windows_lateral_movement_cluster.json"},
            {"title": "Hunt: Linux Multi-Stage Attack", "query_file": "hunting/linux_multi_stage_attack.json"},
            {"title": "Hunt: OCI Destruction Spike", "query_file": "hunting/oci_resource_destruction_spike.json"},
            {"title": "Hunt: Credential Access Cluster", "query_file": "hunting/windows_credential_access_cluster.json"},
            {"title": "Hunt: Multi-User Same IP", "query_file": "hunting/oci_multi_user_same_ip.json"},
            {"title": "Hunt: Linux Persistence Score", "query_file": "hunting/linux_persistence_score.json"},
            {"title": "Hunt: Unusual Process Paths", "query_file": "hunting/windows_process_unusual_path.json"},
            {"title": "Hunt: After-Hours IAM Activity", "query_file": "hunting/oci_after_hours_iam_activity.json"},
            {"title": "Hunt: Defense Evasion Score", "query_file": "hunting/windows_defense_evasion_score.json"},
        ]
    },
    "SOC: Sysmon Network and Lateral Movement Dashboard": {
        "description": "Sysmon network connection analysis: lateral movement detection, C2 beacon identification, DNS tunneling, named pipe activity, and MITRE ATT&CK technique mapping.",
        "widgets": [
            {"title": "Net: C2 Beacon Candidates", "query_file": "sysmon_c2_beacon_-_periodic_outbound_https.json"},
            {"title": "Net: Lateral Movement - SMB", "query_file": "sysmon_lateral_movement_via_smb.json"},
            {"title": "Net: Lateral Movement - WinRM", "query_file": "sysmon_lateral_movement_via_winrm.json"},
            {"title": "Net: RDP Lateral Movement", "query_file": "sysmon_rdp_lateral_movement.json"},
            {"title": "Net: DNS Tunnel Indicators", "query_file": "sysmon_dns_tunneling_via_network_connection.json"},
            {"title": "Net: LOLBin Outbound Traffic", "query_file": "sysmon_suspicious_outbound_connection_from_lolbin.json"},
            {"title": "Net: Kerberoasting Network", "query_file": "sysmon_kerberoasting_network_indicator.json"},
            {"title": "Net: LDAP Reconnaissance", "query_file": "sysmon_ldap_reconnaissance.json"},
            {"title": "File: Executable Dropped", "query_file": "sysmon_executable_file_created_or_detected.json"},
            {"title": "Net: Cobalt Strike C2", "query_file": "sysmon_cobalt_strike_c2_network_indicators.json"},
            {"title": "Net: Mimikatz Network", "query_file": "sysmon_mimikatz_network_activity.json"},
            {"title": "Pipe: Cobalt Strike Pipes", "query_file": "sysmon_cobalt_strike_named_pipe.json"},
            {"title": "Pipe: PsExec Pipes", "query_file": "sysmon_psexec_named_pipe.json"},
            {"title": "Pipe: Mimikatz Pipes", "query_file": "sysmon_mimikatz_named_pipe.json"},
            {"title": "Pipe: Suspicious C2 Pipes", "query_file": "sysmon_suspicious_named_pipe_pattern.json"},
            {"title": "DNS: Data Exfiltration", "query_file": "sysmon_dns_data_exfiltration.json"},
            {"title": "DNS: C2 Framework Domains", "query_file": "sysmon_dns_query_to_known_c2_framework_domains.json"},
            {"title": "DNS: Suspicious TLDs", "query_file": "sysmon_dns_query_to_suspicious_tlds.json"},
        ]
    },
    "C2 & Beaconing Detection": {
        "description": "Enhanced command-and-control investigation dashboard for DNS beacons, HTTPS callbacks, suspicious C2 destinations, VCN/Network Firewall egress, and host-to-destination link analysis across the 21-day demo dataset.",
        "widgets": [
            {"title": "Top C2 DNS Domains", "query_file": "hunting/c2_top_dns_domains.json"},
            {"title": "Beacon Activity Timeline", "query_file": "hunting/c2_beacon_activity_timeline.json"},
            {"title": "DNS Beacon Queries", "query_file": "hunting/c2_dns_beacon_queries_kpi.json"},
            {"title": "C2 Destination IPs", "query_file": "hunting/c2_destination_ips.json"},
            {"title": "C2 Communication Topology", "query_file": "hunting/c2_communication_topology.json"},
            {"title": "DNS Beacon Sources", "query_file": "hunting/c2_dns_beacon_sources.json"},
            {"title": "Unique C2 Domains", "query_file": "hunting/c2_unique_domains_kpi.json"},
            {"title": "C2 Flow Connections", "query_file": "hunting/c2_flow_connections_kpi.json"},
            {"title": "HTTPS Beaconing (Port 443)", "query_file": "hunting/c2_https_beaconing.json"},
            {"title": "Affected Hosts", "query_file": "hunting/c2_affected_hosts_kpi.json"},
        ]
    },
    "SOC: FreeLabFriday Threat Hunting Dashboard": {
        "description": "Black Hills InfoSec FreeLabFriday-inspired hunting dashboard for DNS C2, BITS and cloud-service exfiltration, domain-fronted C2, vsagent HTTP beaconing, credential stuffing, rogue user persistence, and port-knocking drilldowns.",
        "widgets": [
            {"title": "FLF: DNS C2 Patterns", "query_file": "hunting/flf_dns_c2_pattern_analysis.json"},
            {"title": "FLF: BITS Exfiltration", "query_file": "hunting/flf_bits_exfiltration.json"},
            {"title": "FLF: Cloud Service Exfiltration", "query_file": "hunting/flf_cloud_service_exfiltration.json"},
            {"title": "FLF: Domain Fronting CDN C2", "query_file": "hunting/flf_domain_fronting_cdn_c2.json"},
            {"title": "FLF: vsagent HTTP Beaconing", "query_file": "hunting/flf_vsagent_http_beaconing.json"},
            {"title": "FLF: Credential Stuffing", "query_file": "hunting/flf_credential_stuffing_pattern.json"},
            {"title": "FLF: New User Persistence", "query_file": "hunting/flf_new_user_persistence.json"},
            {"title": "FLF: Port Knocking Sequence", "query_file": "hunting/flf_port_knocking_sequence.json"},
        ]
    },
    "SOC: 2025-2026 Threat Hunting Dashboard": {
        "description": "MELTS-driven threat-hunting dashboard for 2025-2026 attack tradecraft: ClickFix/CrashFix, SharePoint ToolShell, RMM abuse, AiTM token replay, compromised-machine drilldowns, and exfiltration evidence.",
        "widgets": [
            {"title": "MELTS: Signal Overview", "query_file": "hunting/melts_attack_signal_overview.json"},
            {"title": "MELTS: Attack Timeline", "query_file": "hunting/melts_attack_timeline.json"},
            {"title": "MELTS: Attack Path Link", "query_file": "hunting/melts_attack_path_link.json"},
            {"title": "ClickFix: Clipboard PowerShell", "query_file": "hunting/clickfix_clipboard_powershell_execution.json"},
            {"title": "ClickFix: LOLBin Payloads", "query_file": "hunting/clickfix_lolbin_payload_execution.json"},
            {"title": "CrashFix: Python RAT", "query_file": "hunting/crashfix_python_rat_activity.json"},
            {"title": "SharePoint: ToolShell Attempts", "query_file": "hunting/sharepoint_toolshell_exploitation.json"},
            {"title": "SharePoint: Webshell Post-Exploit", "query_file": "hunting/sharepoint_toolshell_webshell_post_exploit.json"},
            {"title": "RMM: Post-Compromise Activity", "query_file": "hunting/rmm_post_compromise_activity.json"},
            {"title": "Cloud Identity: AiTM Token Abuse", "query_file": "hunting/cloud_identity_aitm_token_abuse.json"},
            {"title": "Exfil: After Initial Access", "query_file": "hunting/exfiltration_after_initial_access_2025_2026.json"},
            {"title": "Compromised Machines and Data", "query_file": "hunting/compromised_machines_and_data_2025_2026.json"},
        ]
    },
    "SOC: Web Application Security Dashboard": {
        "description": "OWASP Top 10 web attack detection via WAF, Load Balancer, and application logs. SQL injection, XSS, path traversal, SSRF, command injection, and more.",
        "widgets": [
            {"title": "WAF: SQL Injection Blocked", "query_file": "waf_sql_injection_attack_blocked.json"},
            {"title": "WAF: SQL Injection Allowed", "query_file": "waf_sql_injection_attack_allowed_through.json"},
            {"title": "WAF: XSS Attack Blocked", "query_file": "waf_cross-site_scripting_attack_blocked.json"},
            {"title": "WAF: Path Traversal Blocked", "query_file": "waf_path_traversal_attack_blocked.json"},
            {"title": "WAF: Command Injection Blocked", "query_file": "waf_command_injection_attack_blocked.json"},
            {"title": "WAF: SSRF Attack Blocked", "query_file": "waf_server-side_request_forgery_blocked.json"},
            {"title": "WAF: XXE Attack Blocked", "query_file": "waf_xml_external_entity_attack_blocked.json"},
            {"title": "WAF: SSTI Attack Blocked", "query_file": "waf_server-side_template_injection_blocked.json"},
            {"title": "WAF: Log4Shell Blocked", "query_file": "waf_log4shell_cve-2021-44228_attack_blocked.json"},
            {"title": "WAF: NoSQL Injection Blocked", "query_file": "waf_nosql_injection_attack_blocked.json"},
            {"title": "WAF: LDAP Injection Blocked", "query_file": "waf_ldap_injection_attack_blocked.json"},
            {"title": "WAF: Web Shell Upload Blocked", "query_file": "waf_web_shell_upload_attempt_blocked.json"},
            {"title": "WAF: Protocol Attack Blocked", "query_file": "waf_protocol_attack_blocked.json"},
            {"title": "WAF: Rate Limiting Triggered", "query_file": "waf_rate_limiting_triggered.json"},
            {"title": "WAF: CORS Bypass Blocked", "query_file": "waf_cors_bypass_attempt_blocked.json"},
            {"title": "LB: Vulnerability Scanner", "query_file": "web_vulnerability_scanner_detected.json"},
            {"title": "LB: Brute Force Login", "query_file": "web_application_brute_force_login_attempt.json"},
            {"title": "LB: Directory Enumeration", "query_file": "web_directory_enumeration_detected.json"},
            {"title": "LB: Sensitive Data Access", "query_file": "sensitive_data_endpoint_access.json"},
            {"title": "LB: HTTP Method Abuse", "query_file": "suspicious_http_method_usage.json"},
            {"title": "LB: Large Response Exfil", "query_file": "unusually_large_http_response_data_exfiltration.json"},
            {"title": "LB: Server Errors", "query_file": "web_application_server_error_spike.json"},
            {"title": "LB: API Unauthorized", "query_file": "api_endpoint_unauthorized_access_attempts.json"},
            {"title": "LB: Suspicious User Agent", "query_file": "suspicious_or_empty_user_agent_detected.json"},
            {"title": "App: IDOR Detected", "query_file": "insecure_direct_object_reference_detected.json"},
            {"title": "App: Privilege Escalation", "query_file": "web_application_privilege_escalation.json"},
            {"title": "App: Auth Bypass", "query_file": "web_application_authentication_bypass.json"},
            {"title": "App: Insecure Deserialization", "query_file": "insecure_deserialization_attack_detected.json"},
            {"title": "App: Session Hijacking", "query_file": "web_application_session_hijacking_indicators.json"},
            {"title": "App: Mass Assignment", "query_file": "mass_assignment_attack_detected.json"},
        ]
    },
    "SOC: Web Threat Hunting Dashboard": {
        "description": "Advanced web application threat hunting analytics. WAF attack frequency, SQL injection stacking, multi-vector scoring, geographic anomalies, and multi-stage attack chain correlation.",
        "widgets": [
            {"title": "Hunt: WAF Attack by Source IP", "query_file": "hunting/waf_attack_frequency_by_source.json"},
            {"title": "Hunt: SQLi Pattern Stacking", "query_file": "hunting/waf_sqli_pattern_stacking.json"},
            {"title": "Hunt: Web Brute Force", "query_file": "hunting/web_brute_force_frequency.json"},
            {"title": "Hunt: Directory Scan Cluster", "query_file": "hunting/web_directory_scan_clustering.json"},
            {"title": "Hunt: Multi-Attack Scoring", "query_file": "hunting/waf_multi_attack_scoring.json"},
            {"title": "Hunt: Attack Geo Anomaly", "query_file": "hunting/web_attack_geo_anomaly.json"},
            {"title": "Hunt: OWASP Multi-Stage", "query_file": "hunting/web_owasp_multi_stage_attack.json"},
            {"title": "Hunt: Scanner Tool Stacking", "query_file": "hunting/web_scanner_tool_stacking.json"},
        ]
    },
    "SOC: Web-to-Cloud Threat Hunting Dashboard": {
        "description": "Incident-focused dashboard for the web-to-cloud attack chain: SSRF entry point, compromised machines and identity, VCN egress, Network Firewall C2, OCI Audit cloud abuse, and exfiltration evidence with link and sunburst drilldowns.",
        "widgets": [
            {"title": "W2C: Correlated Timeline", "query_file": "hunting/web_to_cloud_attack_timeline.json"},
            {"title": "W2C: Entry Point and SSRF", "query_file": "hunting/web_to_cloud_entry_point.json"},
            {"title": "W2C: Compromised Machines", "query_file": "hunting/web_to_cloud_compromised_machines.json"},
            {"title": "W2C: Compromised Identity", "query_file": "hunting/web_to_cloud_compromised_identity.json"},
            {"title": "W2C: VCN Egress", "query_file": "hunting/web_to_cloud_vcn_egress.json"},
            {"title": "W2C: Network Firewall C2", "query_file": "hunting/web_to_cloud_firewall_c2.json"},
            {"title": "W2C: OCI Audit Cloud Abuse", "query_file": "hunting/web_to_cloud_cloud_abuse.json"},
            {"title": "W2C: Exfiltrated Data", "query_file": "hunting/web_to_cloud_exfiltration.json"},
            {"title": "W2C: Attack Path Link", "query_file": "hunting/web_to_cloud_attack_path_link.json"},
            {"title": "W2C: MITRE Stage Breakdown", "query_file": "hunting/web_to_cloud_mitre_sunburst.json"},
        ]
    },
    "OCI-DEMO: Application 360 Monitoring Dashboard": {
        "description": "360-degree observability for OCI-DEMO applications (CRM Portal + Drone Shop). Runs on SOC Application Logs, a custom JSON telemetry source that models application, browser, and trace context with a shared Trace ID for correlation.",
        "widgets": [
            {"title": "App: Error Rate by Service", "query_file": "apps/app_error_rate_by_service.json"},
            {"title": "App: Slow Requests (>2s)", "query_file": "apps/app_slow_requests.json"},
            {"title": "App: Request Rate by Endpoint", "query_file": "apps/app_request_rate_by_endpoint.json"},
            {"title": "App: Service Health Timeline", "query_file": "apps/app_service_health_timeline.json"},
            {"title": "App: OWASP Attack Detection", "query_file": "apps/app_owasp_attack_detection.json"},
            {"title": "App: WAF Signal Correlation", "query_file": "apps/app_waf_signal_correlation.json"},
            {"title": "App: SQLi + XSS Detection", "query_file": "apps/app_sqli_xss_detection.json"},
            {"title": "App: Auth Brute Force", "query_file": "apps/app_auth_brute_force.json"},
            {"title": "App: Security Attack by IP", "query_file": "apps/app_security_attack_by_ip.json"},
            {"title": "App: Cross-Service Trace Correlation", "query_file": "apps/app_cross_service_trace_correlation.json"},
            {"title": "App: Order Sync Pipeline", "query_file": "apps/app_order_sync_pipeline.json"},
            {"title": "App: DB Performance Correlation", "query_file": "apps/app_db_performance_correlation.json"},
        ]
    },
    "OCI-DEMO: Octo APM Demo Dashboard": {
        "description": "Dedicated APM correlation dashboard for octo-apm-demo data in SOC Application Logs. Correlates request logs, APM span hierarchy, DB spans, Java sidecar errors, API Gateway edge decisions, OSQuery host evidence, payment threats, and metric samples by Trace ID, Span ID, Parent Span ID, Request ID, Run ID, and Attack ID.",
        "widgets": [
            octo_apm_workshop_widget("Octo APM: RED Metrics", "apps/apm_octo_red_metrics.json"),
            octo_apm_workshop_widget("Octo APM: Request Timeline", "apps/apm_octo_request_timeline.json"),
            octo_apm_workshop_widget("Octo APM: Span Hotspots", "apps/apm_octo_span_latency_hotspots.json"),
            octo_apm_workshop_widget("Octo APM: Trace Logs Correlation", "apps/apm_octo_trace_logs_correlation.json"),
            octo_apm_workshop_widget("Octo APM: Trace Investigation Tiles", "apps/apm_octo_trace_investigation_tiles.json"),
            octo_apm_workshop_widget("Octo APM: Span Link Analysis", "apps/apm_octo_span_link.json"),
            octo_apm_workshop_widget("Octo APM: Error Logs", "apps/apm_octo_error_logs.json"),
            octo_apm_workshop_widget("Octo APM: Metric Samples", "apps/apm_octo_metric_samples.json"),
            octo_apm_workshop_widget("Octo APM: Database Spans", "apps/apm_octo_db_spans.json"),
            octo_apm_workshop_widget("Octo APM: Java Sidecar Errors", "apps/apm_octo_java_sidecar_errors.json"),
            octo_apm_workshop_widget("Octo APM: API Gateway Edge Decisions", "apps/apm_octo_api_gateway_edge.json"),
            octo_apm_workshop_widget("Octo APM: Attack Timeline", "apps/apm_octo_attack_timeline.json"),
            octo_apm_workshop_widget("Octo APM: Attack Path Link", "apps/apm_octo_attack_path_link.json"),
            octo_apm_workshop_widget("Octo APM: Attack Trace Correlation", "apps/apm_octo_attack_trace_correlation.json"),
            octo_apm_workshop_widget("Octo APM: Payment Threats", "apps/apm_octo_payment_threats.json"),
            octo_apm_workshop_widget("Octo APM: OSQuery Host Evidence", "apps/apm_octo_osquery_findings.json"),
            octo_apm_workshop_widget("Octo APM: Compromised VM Pivots", "apps/apm_octo_compromised_vm_pivots.json"),
        ]
    },
    "OCI-DEMO: OKE Kubernetes Attack Dashboard": {
        "description": "OKE and Kubernetes attack detection using SOC Application Logs and APM-correlated synthetic telemetry. Covers Boopkit-style eBPF rootkit activity, Kubernetes API reconnaissance, secret collection, privileged workload creation, pod exec, node escape, CronJob persistence, and RBAC backdoor creation.",
        "widgets": [
            {"title": "OKE: Boopkit Attack Timeline", "query_file": "apps/oke_boopkit_attack_timeline.json"},
            {"title": "OKE: Kubernetes Attack Overview", "query_file": "apps/oke_kubernetes_attack_overview.json"},
            {"title": "OKE: Privileged Workload Creation", "query_file": "apps/oke_privileged_workload_creation.json"},
            {"title": "OKE: Secrets and RBAC Abuse", "query_file": "apps/oke_secrets_and_rbac_abuse.json"},
            {"title": "OKE: Exec and Node Escape", "query_file": "apps/oke_exec_and_node_escape.json"},
            {"title": "OKE: eBPF Rootkit Activity", "query_file": "apps/oke_ebpf_rootkit_activity.json"},
            {"title": "OKE: Kubernetes Attack Path Link", "query_file": "apps/oke_kubernetes_attack_path_link.json"},
            {"title": "OKE: Boopkit Rule Count", "query_file": "apps/oke_rule_boopkit_ebpf_rootkit_count.json"},
            {"title": "OKE: Privileged Workload Rule Count", "query_file": "apps/oke_rule_privileged_workload_count.json"},
        ]
    },
    "SOC: Geographic Health Dashboard": {
        "description": "Multicloud geographic health visualization. Regional instance health status across OCI, Azure, AWS, and GCP on a global map with provider summaries, tier breakdowns, and unhealthy region alerts.",
        "widgets": [
            {"title": "Geo: Regional Health Map", "query_file": "hunting/multicloud_geo_health_regional_map.json"},
            {"title": "Geo: Cloud Provider Summary", "query_file": "hunting/multicloud_geo_health_by_provider.json"},
            {"title": "Geo: Instance Detail", "query_file": "hunting/multicloud_geo_health_instance_detail.json"},
            {"title": "Geo: Unhealthy Regions", "query_file": "hunting/multicloud_geo_health_unhealthy_regions.json"},
            {"title": "Geo: Service Tier Status", "query_file": "hunting/multicloud_geo_health_tier_status.json"},
        ]
    },
    "SOC: APT Detection Dashboard": {
        "description": "APT threat detection: BLUELIGHT RAT (S0657/APT37) full kill chain + YARA-enhanced indicators from Volexity research. Covers browser exploitation, Graph API/Google C2, cookie theft, keylogging, and OneDrive exfiltration. Showcase row at the top renders the full attack path on a single canvas.",
        "widgets": [
            {"title": "BLUELIGHT: Total Detections (24h)", "query_file": "hunting/bluelight_total_detections_kpi.json"},
            {"title": "BLUELIGHT: Top Affected Hosts", "query_file": "hunting/bluelight_top_affected_hosts.json"},
            {"title": "BLUELIGHT: MITRE Tactics x Techniques", "query_file": "hunting/bluelight_mitre_tactics_sunburst.json"},
            {"title": "BLUELIGHT: Kill Chain Timeline", "query_file": "hunting/bluelight_kill_chain_timeline.json"},
            {"title": "BLUELIGHT: Attack Path (per Host)", "query_file": "hunting/bluelight_attack_path_link.json"},
            {"title": "APT37: Drive-by Compromise", "query_file": "bluelight_drive_by_compromise.json"},
            {"title": "APT37: Browser Child Process", "query_file": "bluelight_browser_child_process.json"},
            {"title": "APT37: Obfuscated Commandline", "query_file": "bluelight_obfuscated_commandline.json"},
            {"title": "APT37: Graph API C2", "query_file": "bluelight_graph_api_c2.json"},
            {"title": "APT37: WMI System Discovery", "query_file": "bluelight_system_discovery.json"},
            {"title": "APT37: Registry Enumeration", "query_file": "bluelight_registry_enumeration.json"},
            {"title": "APT37: File Discovery", "query_file": "bluelight_file_discovery.json"},
            {"title": "APT37: Screen Capture", "query_file": "bluelight_screen_capture.json"},
            {"title": "APT37: Browser Credential Theft", "query_file": "bluelight_browser_credential_theft.json"},
            {"title": "APT37: Ingress Tool Transfer", "query_file": "bluelight_ingress_tool_transfer.json"},
            {"title": "APT37: OneDrive Exfiltration", "query_file": "bluelight_onedrive_exfiltration.json"},
            {"title": "YARA: PDB Path Indicators", "query_file": "bluelight_yara_pdb_strings.json"},
            {"title": "YARA: System Recon JSON", "query_file": "bluelight_yara_system_recon.json"},
            {"title": "YARA: Cookie Theft (Chrome/Edge)", "query_file": "bluelight_yara_cookie_theft.json"},
            {"title": "YARA: Keylogger Staging", "query_file": "bluelight_yara_keylogger.json"},
            {"title": "YARA: Google App C2", "query_file": "bluelight_yara_google_c2.json"},
            {"title": "Hunt: BLUELIGHT Kill Chain", "query_file": "hunting/bluelight_apt37_kill_chain.json"},
        ]
    },
    "SOC: Browser Attack Detection Dashboard": {
        "description": "Browser-side attack detection using SOC Application Logs, a custom OpenTelemetry-shaped JSON source for browser and application telemetry. Showcase row at the top renders cross-tier trace correlation with the WAF and OWASP attack-mix breakdowns. Detection widgets below cover XSS, SQLi, CSRF, session hijacking, clickjacking, DOM attacks, cryptomining, and fingerprinting across monitored applications.",
        "widgets": [
            {"title": "APM: Total Browser Attacks (24h)", "query_file": "apps/apm_total_attacks_kpi.json"},
            {"title": "APM: OWASP Attack Mix by Service", "query_file": "apps/apm_owasp_breakdown_sunburst.json"},
            {"title": "APM: Browser Attack -> WAF Correlation", "query_file": "apps/apm_attack_to_waf_correlation.json"},
            {"title": "APM: Trace Correlation (APM x WAF)", "query_file": "apps/apm_trace_correlation_link.json"},
            {"title": "Browser: XSS Attack Detection", "query_file": "apps/apm_xss_attack_detection.json"},
            {"title": "Browser: SQL Injection Detection", "query_file": "apps/apm_sqli_attack_detection.json"},
            {"title": "Browser: CSRF Violation", "query_file": "apps/apm_csrf_violation_detection.json"},
            {"title": "Browser: Session Hijacking", "query_file": "apps/apm_session_hijacking_detection.json"},
            {"title": "Browser: Clickjacking Detection", "query_file": "apps/apm_clickjacking_detection.json"},
            {"title": "Browser: DOM-Based Attacks", "query_file": "apps/apm_dom_attack_detection.json"},
            {"title": "Browser: Suspicious JS Patterns", "query_file": "apps/apm_suspicious_js_patterns.json"},
            {"title": "Browser: Fingerprinting Detection", "query_file": "apps/apm_browser_fingerprinting.json"},
            {"title": "Hunt: Browser Attack Frequency", "query_file": "hunting/browser_attack_frequency_analysis.json"},
        ]
    },
    "SOC: oci-coordinator Hunt Showcase Dashboard": {
        "description": (
            "End-to-end threat-hunting showcase for the oci-coordinator demo. "
            "Top row: KPI tiles for total hits, affected hosts, critical alerts, and distinct MITRE techniques "
            "across 15 critical-severity scenarios (Linux, OCI Audit, APM, Web). "
            "Middle: MITRE tactic→technique sunburst, per-scenario breakdown bar, attack timeline line, "
            "and top-affected-hosts horizontal bar. "
            "Bottom: drill-down tiles for each of the 15 scenarios — bind shell, boopkit eBPF, container escape, "
            "kernel module loaded from temp, passwd/shadow direct mod, exec from /dev/shm, reverse shell, "
            "web shell file, SSRF to IMDS, insmod from temp, shadow file read, web process spawning shell, "
            "APM SQL injection, insecure deserialization, OCI audit retention reduced."
        ),
        "widgets": [
            # ─── KPI band ───
            {"title": "Total Hunt Hits (l7d)", "query_file": "hunting/coordinator_total_hits_kpi.json"},
            {"title": "Affected Hosts (l7d)", "query_file": "hunting/coordinator_affected_hosts_kpi.json"},
            {"title": "Critical Alerts (l7d)", "query_file": "hunting/coordinator_critical_alerts_kpi.json"},
            {"title": "MITRE Techniques (l7d)", "query_file": "hunting/coordinator_mitre_techniques_kpi.json"},
            # ─── Analytical band ───
            {"title": "MITRE Tactic → Technique", "query_file": "hunting/coordinator_mitre_sunburst.json"},
            {"title": "Per-Scenario Breakdown", "query_file": "hunting/coordinator_scenario_breakdown.json"},
            {"title": "Attack Timeline (1h bins)", "query_file": "hunting/coordinator_attack_timeline.json"},
            {"title": "Top Affected Hosts", "query_file": "hunting/coordinator_top_affected_hosts.json"},
            # ─── Per-scenario drilldowns (15) ───
            {"title": "Hunt: Bind Shell Listener", "query_file": "linux_bind_shell_listener.json"},
            {"title": "Hunt: Boopkit eBPF Rootkit", "query_file": "linux_boopkit_ebpf_rootkit_activity.json"},
            {"title": "Hunt: Container Escape", "query_file": "linux_container_escape_attempt.json"},
            {"title": "Hunt: Kernel Module from Temp", "query_file": "linux_kernel_module_loaded_from_temp_directory.json"},
            {"title": "Hunt: Passwd/Shadow Direct Mod", "query_file": "linux_password_file_direct_modification.json"},
            {"title": "Hunt: Exec from /dev/shm", "query_file": "linux_process_execution_from_devshm.json"},
            {"title": "Hunt: Reverse Shell", "query_file": "linux_reverse_shell_detected.json"},
            {"title": "Hunt: Web Shell File Creation", "query_file": "linux_web_shell_file_creation.json"},
            {"title": "Hunt: SSRF to Cloud IMDS", "query_file": "ssrf_to_cloud_instance_metadata_service_linux.json"},
            {"title": "Hunt: insmod from Temp", "query_file": "suspicious_usage_of_insmod.json"},
            {"title": "Hunt: Shadow File Read", "query_file": "suspicious_usage_of_shadow.json"},
            {"title": "Hunt: Web Process Spawning Shell", "query_file": "web_server_process_spawning_shell_with_injection_characters_linux.json"},
            {"title": "Hunt: APM SQL Injection", "query_file": "apm_sql_injection_attack_in_request.json"},
            {"title": "Hunt: Insecure Deserialization", "query_file": "insecure_deserialization_attack_detected.json"},
            {"title": "Hunt: OCI Audit Retention Reduced", "query_file": "oci_audit_configuration_retention_reduced.json"},
        ]
    },
}


SENTINEL_DASHBOARD_GROUPS = {
    "identity": "SOC: Microsoft Sentinel Identity Converted Detections",
    "endpoint": "SOC: Microsoft Sentinel Endpoint Converted Detections",
    "azure_cloud": "SOC: Microsoft Sentinel Azure Cloud Converted Detections",
    "m365": "SOC: Microsoft Sentinel M365 Converted Detections",
    "network": "SOC: Microsoft Sentinel Network Converted Detections",
}


SENTINEL_DASHBOARD_DESCRIPTIONS = {
    "identity": "Live-validated Microsoft Sentinel identity detections converted to OCI Log Analytics Logan QL.",
    "endpoint": "Live-validated Microsoft Sentinel endpoint detections converted to OCI Log Analytics Logan QL.",
    "azure_cloud": "Live-validated Microsoft Sentinel Azure cloud detections converted to OCI Log Analytics Logan QL.",
    "m365": "Live-validated Microsoft Sentinel Microsoft 365 detections converted to OCI Log Analytics Logan QL.",
    "network": "Live-validated Microsoft Sentinel network detections converted to OCI Log Analytics Logan QL.",
}


SENTINEL_LIVE_VALIDATION_PASS_VALUES = {"passed", "ok", "success"}


SENTINEL_DASHBOARD_UNSUPPORTED_QUERY_PATTERNS = (
    "Properties like",
)


def _as_sorted_strings(value):
    if isinstance(value, list):
        return sorted(str(item) for item in value if item)
    if value:
        return [str(value)]
    return []


def _sentinel_connector_names(connectors):
    names = []
    if not isinstance(connectors, list):
        return names
    for connector in connectors:
        if not isinstance(connector, dict):
            continue
        connector_id = connector.get("connector_id") or connector.get("connectorId")
        if connector_id:
            names.append(str(connector_id))
        for data_type in connector.get("data_types") or connector.get("dataTypes") or []:
            if data_type:
                names.append(str(data_type))
    return sorted(set(names))


def _sentinel_coverage_keys(payload):
    keys = []
    for table in _as_sorted_strings(payload.get("sentinel_tables")):
        keys.append(("table", table))
    if payload.get("level"):
        keys.append(("level", str(payload["level"])))
    mitre = payload.get("mitre_attack", {})
    if isinstance(mitre, dict):
        for technique in _as_sorted_strings(mitre.get("techniques")):
            keys.append(("technique", technique))
    for connector in _sentinel_connector_names(payload.get("required_data_connectors")):
        keys.append(("connector", connector))
    if not keys:
        keys.append(("query", payload.get("title", "")))
    return tuple(keys)


def _select_sentinel_dashboard_widgets(widgets, max_widgets):
    """Choose a deterministic, coverage-aware subset of Sentinel widgets."""
    remaining = sorted(widgets, key=lambda item: (item.get("title", ""), item.get("query_file", "")))
    selected = []
    covered = set()
    while remaining and len(selected) < max_widgets:
        best_index = 0
        best_score = None
        for index, widget in enumerate(remaining):
            coverage = set(widget.get("_coverage_keys", ()))
            new_coverage = len(coverage - covered)
            score = (-new_coverage, widget.get("title", ""), widget.get("query_file", ""))
            if best_score is None or score < best_score:
                best_index = index
                best_score = score
        widget = remaining.pop(best_index)
        covered.update(widget.get("_coverage_keys", ()))
        selected.append({key: value for key, value in widget.items() if not key.startswith("_")})
    return selected


def load_sentinel_dashboard_groups(queries_dir=QUERIES_DIR, max_widgets=24):
    """Load Sentinel dashboard groups from live-validated converted query JSON."""
    sentinel_dir = os.path.join(queries_dir, "sentinel")
    if not os.path.isdir(sentinel_dir):
        return {}

    grouped = {category: [] for category in SENTINEL_DASHBOARD_GROUPS}
    for filename in sorted(os.listdir(sentinel_dir)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(sentinel_dir, filename)
        try:
            with open(path) as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        if payload.get("source_type") != "microsoft_sentinel":
            continue
        if payload.get("conversion_status") != "promoted":
            continue
        if str(payload.get("live_validation_status", "")).lower() not in SENTINEL_LIVE_VALIDATION_PASS_VALUES:
            continue
        if any(pattern in payload.get("query", "") for pattern in SENTINEL_DASHBOARD_UNSUPPORTED_QUERY_PATTERNS):
            continue

        category = payload.get("sentinel_category", "")
        if category not in grouped:
            continue

        dashboard_meta = payload.get("dashboard", {})
        grouped[category].append({
            "title": f"Sentinel: {payload.get('title', filename)}",
            "query_file": f"sentinel/{filename}",
            "visualization_type": dashboard_meta.get("visualizationType", "table"),
            "_coverage_keys": _sentinel_coverage_keys(payload),
        })

    dashboards = {}
    for category, widgets in grouped.items():
        if not widgets:
            continue
        dashboards[SENTINEL_DASHBOARD_GROUPS[category]] = {
            "description": SENTINEL_DASHBOARD_DESCRIPTIONS[category],
            "widgets": _select_sentinel_dashboard_widgets(widgets, max_widgets),
        }
    return dashboards


DASHBOARDS.update(load_sentinel_dashboard_groups())


def select_dashboards(dashboard_names=None, dashboards=None):
    """Return a display-name keyed dashboard subset for targeted operations."""
    dashboards = dashboards or DASHBOARDS
    if not dashboard_names:
        return dashboards

    selected = {}
    name_lookup = {name.lower(): name for name in dashboards}
    missing = []
    for requested_name in dashboard_names:
        canonical_name = requested_name if requested_name in dashboards else None
        if canonical_name is None:
            canonical_name = name_lookup.get(requested_name.lower())
        if canonical_name is None:
            missing.append(requested_name)
            continue
        selected[canonical_name] = dashboards[canonical_name]

    if missing:
        available = ", ".join(sorted(dashboards))
        raise ValueError(
            f"unknown dashboard name(s): {', '.join(missing)}. "
            f"Available dashboards: {available}"
        )

    return selected
