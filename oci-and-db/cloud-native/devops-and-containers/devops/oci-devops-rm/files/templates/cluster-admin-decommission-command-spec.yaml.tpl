version: 0.1
component: command
timeoutInSeconds: 1200
shell: bash
env:
  variables:
    kube_endpoint: "${kube_endpoint}"
    namespace: "$${tool_namespace}"
    noprod_cluster_id: "${noprod_oke_cluster_id}"
    prod_cluster_id: "${prod_oke_cluster_id}"
    region: "${region}"
    repository_id: "${repository_id}"
    tool_name: "$${tool_name}"

steps:
  - type: Command
    name: Validate decommission request
    failImmediatelyOnError: true
    command: |
      set -euo pipefail

      validate_dns_label() {
        value="$1"
        [ "$${#value}" -le 63 ] && printf '%s' "$${value}" | grep -Eq '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
      }

      : "$${tool_name:?tool_name deployment parameter is required}"
      : "$${namespace:?tool_namespace deployment parameter is required}"
      : "$${OCI_STAGE_ID:?OCI_STAGE_ID is required to resolve the target cluster}"

      stage_json="$${OCI_WORKSPACE_DIR}/decommission-stage.json"
      context_file="$${OCI_WORKSPACE_DIR}/decommission-context.env"
      oci devops deploy-stage get --deploy-stage-id "$${OCI_STAGE_ID}" >"$${stage_json}"
      python3 - "$${stage_json}" >"$${context_file}" <<'PY'
      import json, shlex, sys

      stage = json.load(open(sys.argv[1], encoding="utf-8"))["data"]
      tags = stage.get("freeform-tags") or stage.get("free-form-tags") or {}
      cluster = tags.get("cluster")
      if cluster not in ("noprod", "prod"):
          raise SystemExit(f"Decommission stage has invalid cluster tag: {cluster!r}")
      print(f"cluster_name={shlex.quote(cluster)}")
      PY
      source "$${context_file}"
      case "$${cluster_name}" in
        noprod) cluster_id="$${noprod_cluster_id}" ;;
        prod) cluster_id="$${prod_cluster_id}" ;;
      esac
      printf 'cluster_id=%q\n' "$${cluster_id}" >>"$${context_file}"

      validate_dns_label "$${cluster_name}" || { echo "Invalid cluster_name: $${cluster_name}" >&2; exit 1; }
      validate_dns_label "$${tool_name}" || { echo "Invalid tool_name: $${tool_name}" >&2; exit 1; }
      validate_dns_label "$${namespace}" || { echo "Invalid tool_namespace: $${namespace}" >&2; exit 1; }

      echo "Decommission request validated for $${cluster_name}/$${tool_name} in namespace $${namespace}"

  - type: Command
    name: Configure cluster access
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/decommission-context.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      oci ce cluster create-kubeconfig \
        --cluster-id "$${cluster_id}" \
        --file "$${KUBECONFIG}" \
        --region "$${region}" \
        --token-version 2.0.0 \
        --kube-endpoint "$${kube_endpoint}"

  - type: Command
    name: Load current tool configuration
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/decommission-context.env"
      archive="$${OCI_WORKSPACE_DIR}/cluster-admin.zip"
      source_dir="$${OCI_WORKSPACE_DIR}/cluster-admin-source"
      mkdir -p "$${source_dir}"
      oci devops repository get-repository-archive-content \
        --repository-id "$${repository_id}" \
        --ref-name main \
        --format zip \
        --file "$${archive}"
      unzip -q "$${archive}" -d "$${source_dir}"

      tool_dir="$(find "$${source_dir}" -type d -path "*/clusters/$${cluster_name}/tools/$${tool_name}" -print -quit)"
      : "$${tool_dir:?Tool configuration must remain on main until decommission completes}"
      printf 'tool_dir=%q\n' "$${tool_dir}" >"$${OCI_WORKSPACE_DIR}/decommission.env"

  - type: Command
    name: Delete supplemental resources
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/decommission-context.env"
      source "$${OCI_WORKSPACE_DIR}/decommission.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      resources_dir="$${tool_dir}/resources"

      if [ -d "$${resources_dir}" ] && find "$${resources_dir}" -maxdepth 1 -type f \( -name '*.yaml' -o -name '*.yml' \) | grep -q .; then
        dry_run="$${OCI_WORKSPACE_DIR}/decommission-dry-run.json"
        kubectl apply --server-side --dry-run=server --field-manager=oci-devops-cluster-admin \
          -n "$${namespace}" -f "$${resources_dir}" -o json >"$${dry_run}"
      python3 - "$${dry_run}" "$${namespace}" <<'PY'
      import json, sys

      text, expected = open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]
      decoder, index = json.JSONDecoder(), 0
      while index < len(text):
          while index < len(text) and text[index].isspace():
              index += 1
          if index >= len(text):
              break
          obj, index = decoder.raw_decode(text, index)
          for item in obj.get("items", [obj]):
              namespace = item.get("metadata", {}).get("namespace")
              if namespace != expected:
                  kind = item.get("kind")
                  name = item.get("metadata", {}).get("name")
                  raise SystemExit(f"Refusing to delete {kind}/{name} from namespace {namespace!r}; expected {expected!r}")
      PY
        kubectl delete -n "$${namespace}" -f "$${resources_dir}" --ignore-not-found=true
      else
        echo "No supplemental resources to delete for $${cluster_name}/$${tool_name}"
      fi

  - type: Command
    name: Uninstall tool chart
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/decommission-context.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      if helm status "$${tool_name}" -n "$${namespace}" >/dev/null 2>&1; then
        helm uninstall "$${tool_name}" -n "$${namespace}" --wait --timeout 10m
        echo "Uninstalled Helm release $${tool_name} from $${namespace}"
      else
        echo "Helm release $${tool_name} is already absent from $${namespace}"
      fi
      echo "Namespace $${namespace} was retained for explicit administrator review"
