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
    private_key_file = os.environ.get('COMPUTE_SSH_PRIVATE_KEY_FILE', '/home/opc/.ssh/oci_vm_key')

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


def build_exacs_database_inventory(manifest):
    """Build a local inventory for a registered ExaCS database move."""
    inventory = {
        'all': {'children': {'database_instances': {}}},
        'database_instances': {'hosts': {}}
    }

    environment = manifest['_control_plane_environment']
    registry = manifest['_exacs_database_registry']
    registered_databases = {
        database['display_name']: database for database in registry['databases']
    }

    for target in manifest.get('targets', []):
        name = target.get('display_name')
        database = registered_databases.get(name)
        if database is None:
            print(f"\n❌ ERROR: '{name}' is not registered for {environment}")
            sys.exit(1)
        target_home = next(
            (
                home for home in database['approved_target_db_homes']
                if home['id'] == target['target_db_home_id']
                and home['db_version'] == target['target_db_version']
            ),
            None,
        )
        if target_home is None:
            print("\n❌ ERROR: The target Database Home is not approved for this database")
            sys.exit(1)
        inventory['database_instances']['hosts'][name] = {
            'ansible_connection': 'local',
            'oci_ocid': database['database_id'],
            'service_model': database['service_model'],
            'declarative_owner': database['declarative_owner'],
            'registered_compartment_id': database['compartment_id'],
            'registered_vm_cluster_id': database['vm_cluster_id'],
            'expected_source_db_home_id': target['expected_source_db_home_id'],
            'target_db_home_id': target['target_db_home_id'],
            'target_db_version': target['target_db_version'],
            'timeout_minutes': target.get('timeout_minutes', 240),
        }

    return inventory


def load_exacs_database_registry(environment):
    """Load the platform-owned ExaCS registry for one logical environment."""
    registry_path = os.path.join('environments', environment, 'exacs-databases.json')
    try:
        registry = load_json(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"❌ Unable to read ExaCS registry: {exc}")
        sys.exit(1)

    if not isinstance(registry, dict) or set(registry) != {'schema_version', 'databases'}:
        print("❌ Invalid ExaCS database registry")
        sys.exit(1)
    if registry.get('schema_version') != 2 or not isinstance(registry.get('databases'), list):
        print("❌ Invalid ExaCS database registry")
        sys.exit(1)
    required_database_keys = {
        'display_name', 'database_id', 'compartment_id', 'vm_cluster_id',
        'service_model', 'declarative_owner', 'approved_target_db_homes',
    }
    required_home_keys = {'id', 'db_version'}
    for database in registry['databases']:
        if (
            not isinstance(database, dict)
            or set(database) != required_database_keys
            or not all(isinstance(database[key], str) and database[key]
                       for key in ('display_name', 'database_id', 'compartment_id', 'vm_cluster_id'))
            or database['service_model'] not in {'exacs', 'od-gcp'}
            or database['declarative_owner'] not in {'external', 'oci-exadata-state'}
            or not isinstance(database['approved_target_db_homes'], list)
            or not database['approved_target_db_homes']
        ):
            print("❌ Invalid ExaCS database registry")
            sys.exit(1)
        for home in database['approved_target_db_homes']:
            if (
                not isinstance(home, dict)
                or set(home) != required_home_keys
                or not all(isinstance(home[key], str) and home[key] for key in required_home_keys)
            ):
                print("❌ Invalid ExaCS database registry")
                sys.exit(1)
    return registry


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

    if operation_type == 'exacs-database-out-of-place-patch':
        path_parts = config_path.split('/')
        if len(path_parts) != 3:
            print("❌ Invalid ExaCS operation path")
            sys.exit(1)
        manifest['_control_plane_environment'] = path_parts[1]
        manifest['_exacs_database_registry'] = load_exacs_database_registry(path_parts[1])
        inventory = build_exacs_database_inventory(manifest)
        host_count = len(inventory['database_instances']['hosts'])
        inventory_path = get_inventory_path()
        save_json(inventory_path, inventory)
        print(f"✅ Inventory: {host_count} OCI API target → {inventory_path}")
        return

    namespace = os.environ.get('STATE_NAMESPACE')
    if not namespace:
        print("❌ STATE_NAMESPACE variable not configured")
        sys.exit(1)

    # State-backed operations use the project-region Terraform state.
    state_data = download_terraform_state(namespace, bucket, config_path)

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
