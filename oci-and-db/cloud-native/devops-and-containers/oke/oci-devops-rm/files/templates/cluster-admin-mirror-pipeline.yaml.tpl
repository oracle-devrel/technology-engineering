version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    compartment_id: "${compartment_id}"
    region: "${region}"
    registry: "${region_key}.ocir.io"
    tenancy_namespace: "${tenancy_namespace}"
    chart_repo_prefix: "${chart_repo_prefix}"

steps:
  - type: Command
    name: Prepare mirror dependencies
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      python3 -c 'import yaml' 2>/dev/null || python3 -m pip install --disable-pip-version-check PyYAML==6.0.2

  - type: Command
    name: Mirror missing tool charts
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export OCI_CLI_REGION="$${region}"

      python3 "$${OCI_PRIMARY_SOURCE_DIR}/script/mirror-charts.py" \
        --catalog "$${OCI_PRIMARY_SOURCE_DIR}/catalog/tools.yaml" \
        --compartment-id "$${compartment_id}" \
        --registry "$${registry}" \
        --tenancy-namespace "$${tenancy_namespace}" \
        --target-prefix "$${chart_repo_prefix}"
