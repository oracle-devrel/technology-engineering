#!/usr/bin/env python3
"""
Utilities for ansible_inventory.py
"""

import os
import sys
import json
import subprocess
import tempfile


def load_json(file_path):
    """Load JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def save_json(file_path, data):
    """Save data to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def get_inventory_path():
    """Get inventory file path."""
    work_temp = os.environ.get('WORK_TEMP', '/tmp')
    return os.path.join(work_temp, "inventory.json")


def get_terraform_state_key(bucket, config_path):
    """Build Terraform state key. Must match the Terraform backend key exactly."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("❌ GITHUB_REPOSITORY is not set; refusing to guess the state key")
        sys.exit(1)
    return f"{bucket}/{repo}/{config_path}/terraform.tfstate"


def download_from_bucket(namespace, bucket, object_name):
    """
    Download object from OCI Object Storage.
    Returns: string content or None if not found.
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name

    command = [
        'oci', 'os', 'object', 'get',
        '--namespace', namespace,
        '--bucket-name', bucket,
        '--name', object_name,
        '--file', tmp_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    try:
        if result.returncode == 0:
            with open(tmp_path, 'r') as f:
                return f.read()

        stderr = result.stderr or ""
        if 'NotAuthorizedOrNotFound' in stderr or '404' in stderr:
            # OCI returns this for both "absent" and "no permission"; the caller
            # reports the state key so the two can be told apart by an operator.
            print(f"ℹ️  Object absent or not readable: {object_name}")
            return None

        print(f"❌ Could not read {object_name}: {stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
