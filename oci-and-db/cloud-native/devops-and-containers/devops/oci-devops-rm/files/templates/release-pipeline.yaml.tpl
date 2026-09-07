version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    application_chart_source_dir: "application-chart"
    application_chart_path: "${application_chart_path}"
    component_chart_repo_prefix: "${component_chart_repo_prefix}"
    application_release_env_file: "/workspace/application-release.env"
    application_release_image_env_file: "/workspace/application-release-image.env"
    component_image_repository: "${component_image_repository}"
    component_image_repo_prefix: "${component_image_repo_prefix}"
    repo_compartment_id: "${repo_compartment_id}"
    region: "${region}"
    region_key: "${region_key}"
    tenancy_namespace: "${tenancy_namespace}"
  exportedVariables:
    - component_chart_version
    - image_repository
    - image_tag

steps:
  - type: Command
    name: Resolve release inputs
    failImmediatelyOnError: true
    command: |
      export OCI_CLI_REGION="$${region}"

      : "$${release_tag:?release_tag pipeline parameter is required}"
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/release-resolve-inputs.sh" \
        -g "$${release_tag}" \
        -i "$${commit_id:-}" \
        -a "$${application_chart_source_dir}" \
        -p "$${application_chart_path}" \
        -r "$${component_chart_repo_prefix}" \
        -o "$${application_release_env_file}"

  - type: Command
    name: Promote application image
    failImmediatelyOnError: true
    command: |
      source "$${application_release_env_file}"

      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/release-image-tag.sh" \
        -c "$${repo_compartment_id}" \
        -k "$${region_key}" \
        -n "$${component_name}" \
        -p "$${component_image_repo_prefix}" \
        -t "$${tenancy_namespace}" \
        -g "$${release_tag}" \
        -i "$${resolved_commit_id}" \
        -r "$${source_repository_id}" \
        -o "$${application_release_image_env_file}"

  - type: Command
    name: Verify application chart
    failImmediatelyOnError: true
    command: |
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/release-verify-chart.sh" \
        -e "$${application_release_env_file}" \
        -k "$${region_key}" \
        -t "$${tenancy_namespace}"

  - type: Command
    name: Print release summary
    failImmediatelyOnError: true
    command: |
      source "$${application_release_env_file}"
      source "$${application_release_image_env_file}"

      component_chart_version="$${chart_version}"
      image_repository="$${component_image_repository}"
      image_tag="$${promoted_image_tag}"
      export component_chart_version
      export image_repository
      export image_tag

      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/release-print-summary.sh" \
        -e "$${application_release_env_file}" \
        -p "$${application_release_image_env_file}"

      printf "Component staging deployment chart version: %s\n" "$${component_chart_version}"
