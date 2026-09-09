version: 0.1
component: build
timeoutInSeconds: 3000
runAs: root
shell: bash

steps:
  - type: Command
    name: Validate cluster administration configuration
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      python3 -c 'import yaml' 2>/dev/null || python3 -m pip install --disable-pip-version-check PyYAML==6.0.2

      commit="$${OCI_PRIMARY_SOURCE_COMMIT_HASH:-HEAD}"
      python3 "$${OCI_PRIMARY_SOURCE_DIR}/script/validate-config.py" \
        --repo "$${OCI_PRIMARY_SOURCE_DIR}" \
        --commit "$${commit}" \
        --mode all \
        --output "/workspace/cluster-admin-validation.json"

      echo "Cluster administration validation succeeded"
