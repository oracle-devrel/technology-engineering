version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    application_chart_source_dir: "application-chart"
    component_chart_repo_prefix: "${component_chart_repo_prefix}"
    component_chart_path: "${component_chart_path}"
    component_delivery_env_file: "/workspace/component-delivery.env"
    component_name: "${component_name}"
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
    name: Select delivery actions
    failImmediatelyOnError: true
    command: |
      export OCI_CLI_REGION="$${region}"

      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/application-delivery-select-actions.sh" \
        -a "$${application_chart_source_dir}" \
        -p "$${component_chart_path}" \
        -r "$${component_chart_repo_prefix}" \
        -o "$${component_delivery_env_file}"

  - type: Command
    name: Build application image
    failImmediatelyOnError: true
    command: |
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/application-delivery-build-image.sh" \
        -e "$${component_delivery_env_file}" \
        -c "$${repo_compartment_id}" \
        -k "$${region_key}" \
        -p "$${component_image_repo_prefix}" \
        -t "$${tenancy_namespace}"

  - type: Command
    name: Ensure component chart exists
    failImmediatelyOnError: true
    command: |
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/application-delivery-check-chart.sh" \
        -e "$${component_delivery_env_file}" \
        -k "$${region_key}" \
        -t "$${tenancy_namespace}"

  - type: Command
    name: Package component chart
    failImmediatelyOnError: true
    command: |
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/application-delivery-package-chart.sh" \
        -e "$${component_delivery_env_file}" \
        -c "$${repo_compartment_id}" \
        -k "$${region_key}" \
        -t "$${tenancy_namespace}"

  - type: Command
    name: Export component dev deployment parameters
    failImmediatelyOnError: true
    command: |
      source "$${component_delivery_env_file}"

      if [ -z "$${chart_version:-}" ]; then
        chart_version="$(bash "$${OCI_PRIMARY_SOURCE_DIR}/script/read-chart-version.sh" \
          -p "$${OCI_WORKSPACE_DIR}/$${chart_source_dir}/$${chart_path}")"
      fi
      component_chart_version="$${chart_version}"

      image_repository="${component_image_repository}"
      image_tag="$(git -C "$${OCI_WORKSPACE_DIR}/$${component_name}" rev-parse --short=7 HEAD)"
      export image_repository
      export image_tag
      export component_chart_version

      printf "Component dev deployment chart version: %s\n" "$${component_chart_version}"
