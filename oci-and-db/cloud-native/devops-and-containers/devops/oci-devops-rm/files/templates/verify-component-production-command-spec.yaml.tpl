version: 0.1
component: command
timeoutInSeconds: 600
shell: bash
env:
  variables:
    kube_endpoint: "${kube_endpoint}"
    OCI_CLI_REGION: "${region}"
    prod_cluster_id: "${prod_oke_cluster_id}"

steps:
  - type: Command
    name: Resolve production release
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      : "$${OCI_STAGE_ID:?OCI_STAGE_ID is required to resolve the production release}"

      stage_json="$${OCI_WORKSPACE_DIR}/production-verification-stage.json"
      context_file="$${OCI_WORKSPACE_DIR}/production-verification.env"
      oci devops deploy-stage get --stage-id "$${OCI_STAGE_ID}" >"$${stage_json}"
      python3 - "$${stage_json}" >"$${context_file}" <<'PY'
      import json, shlex, sys

      stage = json.load(open(sys.argv[1], encoding="utf-8"))["data"]
      tags = stage.get("freeform-tags") or stage.get("free-form-tags") or {}
      required = ("namespace", "release")
      missing = [key for key in required if not tags.get(key)]
      if missing:
          raise SystemExit(f"Production verification stage is missing freeform tags: {', '.join(missing)}")
      for key in required:
          print(f"{key}={shlex.quote(tags[key])}")
      PY

  - type: Command
    name: Configure production cluster access
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      oci ce cluster create-kubeconfig \
        --cluster-id "$${prod_cluster_id}" \
        --file "$${KUBECONFIG}" \
        --region "$${OCI_CLI_REGION}" \
        --token-version 2.0.0 \
        --kube-endpoint "$${kube_endpoint}"

  - type: Command
    name: Report production Helm release
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/production-verification.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      command -v helm >/dev/null 2>&1 || { echo "helm is not available in the deployment shell runner" >&2; exit 1; }

      echo "=== Release status and resources ==="
      helm status "$${release}" --namespace "$${namespace}" --show-resources

      echo "=== Release history ==="
      helm history "$${release}" --namespace "$${namespace}" --max 10

      echo "=== Release notes ==="
      helm get notes "$${release}" --namespace "$${namespace}"

      echo "=== Namespace release listing ==="
      helm list --namespace "$${namespace}" --filter "^$${release}$"
