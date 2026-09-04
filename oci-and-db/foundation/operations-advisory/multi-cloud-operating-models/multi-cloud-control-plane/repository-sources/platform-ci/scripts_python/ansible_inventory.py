#!/usr/bin/env python3
"""
Generate dynamic Ansible inventory from Terraform state.
Usage: python3 ansible_inventory.py <cloud> <bucket> <config-path> <operation-file>
"""

import os
import sys
import json
from utils import load_json, save_json, get_inventory_path, get_terraform_state_key, download_from_bucket


def download_terraform_state(namespace, bucket, config_path):
    """Download terraform.tfstate from OCI bucket."""
    state_key = get_terraform_state_key(bucket, config_path)

    print(f"Loading Terraform state...")
    print(f"   Bucket: {bucket}")
    print(f"   Key: {state_key}")

    content = download_from_bucket(namespace, bucket, state_key)

    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in Terraform state: {e}")
            return None
    return None


def parse_adb_resources(state_data):
    """Extract ADBs from Terraform state. Returns dict display_name → info."""
    adb_map = {}

    if not state_data:
        return adb_map

    for resource in state_data.get('resources', []):
        if resource.get('type') != 'oci_database_autonomous_database':
            continue

        for instance in resource.get('instances', []):
            attrs = instance.get('attributes', {})
            display_name = attrs.get('display_name', resource.get('name'))

            adb_map[display_name] = {
                'ocid': attrs.get('id'),
                'db_name': attrs.get('db_name'),
                'state': attrs.get('lifecycle_state'),
                'freeform_tags': attrs.get('freeform_tags', {})
            }

    return adb_map


def parse_compute_resources(state_data):
    """Extract compute instances from Terraform state. Returns dict display_name → info."""
    compute_map = {}

    if not state_data:
        return compute_map

    for resource in state_data.get('resources', []):
        if resource.get('type') != 'oci_core_instance':
            continue

        for instance in resource.get('instances', []):
            attrs = instance.get('attributes', {})
            display_name = attrs.get('display_name', resource.get('name'))

            # Get primary private IP
            private_ip = None
            create_details = attrs.get('create_vnic_details', {})
            if isinstance(create_details, dict):
                private_ip = create_details.get('private_ip')
            if not private_ip:
                private_ip = attrs.get('private_ip')

            compute_map[display_name] = {
                'ocid': attrs.get('id'),
                'private_ip': private_ip,
                'state': attrs.get('state'),
                'shape': attrs.get('shape'),
                'freeform_tags': attrs.get('freeform_tags', {})
            }

    return compute_map


def build_inventory(manifest, adb_map):
    """Build Ansible inventory for ADB resources."""
    inventory = {
        'all': {'children': {'adb_instances': {}}},
        'adb_instances': {'hosts': {}}
    }

    # targets is a list of ADB operations
    adb_resources = manifest.get('targets', [])

    for adb_target in adb_resources:
        name = adb_target.get('display_name')

        if name not in adb_map:
            print(f"\n❌ ERROR: '{name}' not found in Terraform state")
            print(f"Available: {list(adb_map.keys()) or '(none)'}")
            sys.exit(1)

        adb_info = adb_map[name]
        # Put hostvars directly in the host entry
        inventory['adb_instances']['hosts'][name] = {
            'ansible_connection': 'local',
            'oci_ocid': adb_info['ocid'],
            'oci_state': adb_info['state'],
            'db_name': adb_info['db_name'],
            'action': adb_target.get('action'),
            'wait_for_state': adb_target.get('wait_for_state', True),
            'timeout_minutes': adb_target.get('timeout_minutes', 30),
        }

    return inventory


def build_compute_inventory(manifest, compute_map):
    """Build Ansible inventory for compute instances."""
    inventory = {
        'all': {'children': {'compute_instances': {}}},
        'compute_instances': {'hosts': {}}
    }

    targets = manifest.get('targets', [])
    ansible_user = os.environ.get('COMPUTE_ANSIBLE_USER', 'opc')
    private_key_file = os.environ.get(
        'COMPUTE_SSH_PRIVATE_KEY_FILE',
        '/home/github-runner/.ssh/oci_vm_key',
    )

    for target in targets:
        name = target.get('display_name')

        if name not in compute_map:
            print(f"\n❌ ERROR: '{name}' not found in Terraform state")
            print(f"Available: {list(compute_map.keys()) or '(none)'}")
            sys.exit(1)

        info = compute_map[name]
        inventory['compute_instances']['hosts'][name] = {
            'ansible_host': info['private_ip'],
            'ansible_connection': 'ssh',
            'ansible_user': ansible_user,
            'ansible_ssh_private_key_file': private_key_file,
            'oci_ocid': info['ocid'],
            'oci_state': info['state'],
            'agent_type': manifest.get('agent_type', 'unknown'),
            'agent_version': manifest.get('agent_version', 'latest'),
        }

    return inventory


def main():
    if len(sys.argv) != 5:
        print("Usage: ansible_inventory.py <cloud> <bucket> <config-path> <operation-file>")
        sys.exit(1)

    cloud, bucket, config_path, operation_file = sys.argv[1:5]

    if cloud != 'oci':
        print(f"❌ {cloud} not supported")
        sys.exit(1)

    # Load manifest and determine operation type.
    manifest = load_json(operation_file)
    operation_type = manifest.get('operation_type', 'adb-lifecycle')

    namespace = os.environ.get('STATE_NAMESPACE')
    if not namespace:
        print("❌ STATE_NAMESPACE variable not configured")
        sys.exit(1)

    # State-backed operations use the project-region Terraform state.
    state_data = download_terraform_state(namespace, bucket, config_path)
    if state_data is None:
        state_key = get_terraform_state_key(bucket, config_path)
        print(f"❌ Terraform state is absent or not readable: {state_key}")
        print("   Deploy the resource before operating it, and confirm the "
              "runner identity can read the state bucket.")
        sys.exit(1)

    # Route to the right parser/builder based on operation type
    if operation_type == 'deploy-agent':
        compute_map = parse_compute_resources(state_data)
        print(f"✅ Found {len(compute_map)} compute instances in Terraform state")
        inventory = build_compute_inventory(manifest, compute_map)
        host_count = len(inventory['compute_instances']['hosts'])
    elif operation_type == 'adb-lifecycle':
        adb_map = parse_adb_resources(state_data)
        print(f"✅ Found {len(adb_map)} ADBs in Terraform state")
        inventory = build_inventory(manifest, adb_map)
        host_count = len(inventory['adb_instances']['hosts'])
    else:
        print(f"❌ Unsupported operation type: {operation_type}")
        sys.exit(1)

    inventory_path = get_inventory_path()
    save_json(inventory_path, inventory)

    print(f"✅ Inventory: {host_count} hosts → {inventory_path}")


if __name__ == "__main__":
    main()
