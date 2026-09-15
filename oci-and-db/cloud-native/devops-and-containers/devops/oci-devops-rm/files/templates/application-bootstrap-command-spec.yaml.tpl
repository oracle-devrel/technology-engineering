version: 0.1
component: command
timeoutInSeconds: 600
shell: bash
env:
  variables:
    kube_endpoint: "${kube_endpoint}"
    noprod_cluster_id: "${noprod_oke_cluster_id}"
    OCI_CLI_REGION: "${region}"
    ocir_registry: "${region_key}.ocir.io"
    prod_cluster_id: "${prod_oke_cluster_id}"
    target_registry_username: "$${registry_username}"
    target_pull_password_secret_ocid: "$${pull_password_secret_ocid}"
    target_secret_name: "$${secret_name}"

steps:
  - type: Command
    name: Resolve bootstrap target
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      : "$${OCI_STAGE_ID:?OCI_STAGE_ID is required to resolve the bootstrap target}"

      stage_json="$${OCI_WORKSPACE_DIR}/bootstrap-stage.json"
      context_file="$${OCI_WORKSPACE_DIR}/bootstrap-context.env"
      oci devops deploy-stage get --stage-id "$${OCI_STAGE_ID}" >"$${stage_json}"
      python3 - "$${stage_json}" >"$${context_file}" <<'PY'
      import json, shlex, sys

      stage = json.load(open(sys.argv[1], encoding="utf-8"))["data"]
      tags = stage.get("freeform-tags") or stage.get("free-form-tags") or {}
      required = ("application", "cluster", "namespace")
      missing = [key for key in required if not tags.get(key)]
      if missing:
          raise SystemExit(f"Bootstrap stage is missing freeform tags: {', '.join(missing)}")
      for key in required:
          print(f"{key}={shlex.quote(tags[key])}")
      PY
      source "$${context_file}"

      case "$${cluster}" in
        noprod) target_cluster_id="$${noprod_cluster_id}" ;;
        prod) target_cluster_id="$${prod_cluster_id}" ;;
        *) echo "Unsupported bootstrap cluster: $${cluster}" >&2; exit 1 ;;
      esac
      printf 'target_cluster_id=%q\ntarget_namespace=%q\n' \
        "$${target_cluster_id}" "$${namespace}" >>"$${context_file}"

  - type: Command
    name: Validate namespace inputs
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/bootstrap-context.env"

      validate_k8s_dns_label() {
        value="$1"
        [ "$${#value}" -le 63 ] && printf '%s' "$${value}" | grep -Eq '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
      }

      printf '%s' "$${target_cluster_id}" | grep -Eq '^ocid1\.cluster\.' || { echo "Invalid OKE cluster OCID" >&2; exit 1; }
      validate_k8s_dns_label "$${target_namespace}" || { echo "Invalid namespace: $${target_namespace}" >&2; exit 1; }
      validate_k8s_dns_label "$${target_secret_name}" || { echo "Invalid secret name: $${target_secret_name}" >&2; exit 1; }
      : "$${target_registry_username:?registry_username pipeline parameter is required}"
      : "$${target_pull_password_secret_ocid:?pull_password_secret_ocid pipeline parameter is required}"
      printf '%s' "$${target_pull_password_secret_ocid}" | grep -Eq '^ocid1\.vaultsecret\.' || { echo "Invalid pull password secret OCID" >&2; exit 1; }

      echo "Bootstrap inputs validated for $${application} on $${cluster}"

  - type: Command
    name: Configure cluster access
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/bootstrap-context.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      oci ce cluster create-kubeconfig \
        --cluster-id "$${target_cluster_id}" \
        --file "$${KUBECONFIG}" \
        --region "$${OCI_CLI_REGION}" \
        --token-version 2.0.0 \
        --kube-endpoint "$${kube_endpoint}"

  - type: Command
    name: Ensure namespace exists
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/bootstrap-context.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      kubectl create namespace "$${target_namespace}" --dry-run=client -o yaml | kubectl apply -f -
      echo "Namespace initialized: $${target_namespace}"

  - type: Command
    name: Create OCIR pull secret
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/bootstrap-context.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      ocir_pull_password="$(oci secrets secret-bundle get \
        --secret-id "$${target_pull_password_secret_ocid}" \
        --query 'data."secret-bundle-content".content' \
        --raw-output | base64 --decode)"
      if [ -z "$${ocir_pull_password}" ]; then
        echo "OCIR pull password secret is empty" >&2
        exit 1
      fi

      kubectl -n "$${target_namespace}" delete secret "$${target_secret_name}" --ignore-not-found=true
      kubectl -n "$${target_namespace}" create secret docker-registry "$${target_secret_name}" \
        --docker-server="$${ocir_registry}" \
        --docker-username="$${target_registry_username}" \
        --docker-password="$${ocir_pull_password}"
      echo "OCIR pull secret created: $${target_secret_name}"
