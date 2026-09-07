version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    artifact_repository_id: "${artifact_repository_id}"
    compartment_id: "${compartment_id}"
    mirror_pipeline_id: "${mirror_pipeline_id}"
    project_id: "${project_id}"
    region: "${region}"
    region_key: "${region_key}"
    tenancy_namespace: "${tenancy_namespace}"
    chart_repo_prefix: "${chart_repo_prefix}"
    target_file: "/workspace/cluster-admin-targets.json"

steps:
  - type: Command
    name: Prepare validation dependencies
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      python3 -c 'import yaml' 2>/dev/null || python3 -m pip install --disable-pip-version-check PyYAML==6.0.2

  - type: Command
    name: Validate changed cluster configuration
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      commit="$${OCI_PRIMARY_SOURCE_COMMIT_HASH:-$${OCI_TRIGGER_COMMIT_HASH:-}}"
      : "$${commit:?The cluster-admin source commit is unavailable}"

      python3 "$${OCI_PRIMARY_SOURCE_DIR}/script/validate-config.py" \
        --repo "$${OCI_PRIMARY_SOURCE_DIR}" \
        --commit "$${commit}" \
        --mode changed \
        --output "$${target_file}"

  - type: Command
    name: Publish values and dispatch changed targets
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export OCI_CLI_REGION="$${region}"

      python3 "$${OCI_PRIMARY_SOURCE_DIR}/script/publish-and-dispatch.py" \
        --repo "$${OCI_PRIMARY_SOURCE_DIR}" \
        --targets "$${target_file}" \
        --project-id "$${project_id}" \
        --mirror-pipeline-id "$${mirror_pipeline_id}" \
        --artifact-repository-id "$${artifact_repository_id}" \
        --compartment-id "$${compartment_id}"
