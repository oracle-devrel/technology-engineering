version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    application_chart_source_dir: "application-chart"
    application_chart_path: "${application_chart_path}"
    application_chart_repo_prefix: "${application_chart_repo_prefix}"
    application_chart_name: "${application_chart_name}"
    application_baseline_env_file: "/workspace/application-baseline.env"
    repo_compartment_id: "${repo_compartment_id}"
    region: "${region}"
    region_key: "${region_key}"
    tenancy_namespace: "${tenancy_namespace}"
  exportedVariables:
    - chart_version

steps:
  - type: Command
    name: Read application chart version
    failImmediatelyOnError: true
    command: |
      export OCI_CLI_REGION="$${region}"

      chart_version="$(bash "$${OCI_PRIMARY_SOURCE_DIR}/script/read-chart-version.sh" \
        -p "$${OCI_WORKSPACE_DIR}/$${application_chart_source_dir}/$${application_chart_path}")"
      printf "chart_version=%q\n" "$${chart_version}" > "$${application_baseline_env_file}"
      export chart_version

      printf "Application baseline chart version: %s\n" "$${chart_version}"

  - type: Command
    name: Package application chart
    failImmediatelyOnError: true
    command: |
      source "$${application_baseline_env_file}"
      export chart_version

      cd "$${OCI_WORKSPACE_DIR}/$${application_chart_source_dir}"

      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/package-push-chart.sh" \
        -c "$${repo_compartment_id}" \
        -k "$${region_key}" \
        -n "$${application_chart_name}" \
        -v "$${chart_version}" \
        -d "$${application_chart_path}" \
        -p "$${application_chart_repo_prefix}" \
        -t "$${tenancy_namespace}"
