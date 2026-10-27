version: 0.1
component: build
timeoutInSeconds: 10000
runAs: root
shell: bash
env:
  variables:
    configured_component_name: "${component_name}"
    component_image_repo_prefix: "${component_image_repo_prefix}"
    component_image_repository: "${component_image_repository}"
    repo_compartment_id: "${repo_compartment_id}"
    region: "${region}"
    region_key: "${region_key}"
    tenancy_namespace: "${tenancy_namespace}"
  exportedVariables:
    - image_repository
    - image_tag

steps:
  - type: Command
    name: Build component image
    failImmediatelyOnError: true
    command: |
      export OCI_CLI_REGION="$${region}"

      component_dir="$${OCI_WORKSPACE_DIR}/$${configured_component_name}"
      validated_env="$${component_dir}/.oci-devops/application.validated.env"

      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/read-application-metadata.sh" \
        -f "$${component_dir}/.oci-devops/application.env" \
        -o "$${validated_env}"
      source "$${validated_env}"

      if [ "$${component_name}" != "$${configured_component_name}" ]; then
        echo "Component metadata does not match the configured build source." >&2
        exit 1
      fi

      cd "$${component_dir}"
      bash "$${OCI_PRIMARY_SOURCE_DIR}/script/build-push-image.sh" \
        -c "$${repo_compartment_id}" \
        -k "$${region_key}" \
        -n "$${component_name}" \
        -p "$${component_image_repo_prefix}" \
        -t "$${tenancy_namespace}"

      image_repository="$${component_image_repository}"
      image_tag="$(git rev-parse --short=7 HEAD)"
      export image_repository
      export image_tag

      printf "Published build-only image: %s:%s\n" "$${image_repository}" "$${image_tag}"
