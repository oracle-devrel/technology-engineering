version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    CHART_VALUES_FILE: ""
    repo_compartment_id: "${repo_compartment_id}"
    region: "${region}"
    region_key: "${region_key}"
    tenancy_namespace: "${tenancy_namespace}"

steps:
  - type: Command
    name: Package and push Helm chart
    failImmediatelyOnError: true
    command: |
      export OCI_CLI_REGION="$${region}"

      : "$${chart_name:?chart_name pipeline parameter is required}"
      : "$${chart_version:?chart_version pipeline parameter is required}"
      : "$${chart_path:?chart_path pipeline parameter is required}"
      : "$${chart_source_dir:?chart_source_dir pipeline parameter is required}"
      : "$${chart_repo_prefix:?chart_repo_prefix pipeline parameter is required}"

      cd "$${OCI_WORKSPACE_DIR}/$${chart_source_dir}"
      args=(
        -c "$${repo_compartment_id}"
        -k "$${region_key}"
        -n "$${chart_name}"
        -v "$${chart_version}"
        -d "$${chart_path}"
        -p "$${chart_repo_prefix}"
        -t "$${tenancy_namespace}"
      )
      if [ -n "$${CHART_VALUES_FILE:-}" ]; then
        args+=(-f "$${CHART_VALUES_FILE}")
      fi
      "$${OCI_PRIMARY_SOURCE_DIR}/script/package-push-chart.sh" \
        "$${args[@]}"
