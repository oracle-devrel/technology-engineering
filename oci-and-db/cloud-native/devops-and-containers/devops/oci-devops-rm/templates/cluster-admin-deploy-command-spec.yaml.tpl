version: 0.1
component: command
timeoutInSeconds: 10000
shell: bash
env:
  variables:
    artifact_repository_id: "${artifact_repository_id}"
    chart_prefix: "${chart_prefix}"
    cluster_id: "$${cluster_id}"
    cluster_name: "$${cluster_name}"
    config_commit: "$${config_commit}"
    kube_endpoint: "${kube_endpoint}"
    region: "${region}"
    registry: "${registry}"
    repository_id: "${repository_id}"
    tenancy_namespace: "${tenancy_namespace}"

steps:
  - type: Command
    name: Validate cluster deployment input
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      : "$${config_commit:?config_commit deployment parameter is required}"
      : "$${cluster_id:?cluster_id deployment parameter is required}"
      case "$${cluster_name}" in noprod|prod) ;; *) echo "cluster_name must be noprod or prod" >&2; exit 1;; esac
      printf '%s' "$${config_commit}" | grep -Eq '^[0-9a-f]{40}$' || { echo "config_commit must be a full Git SHA" >&2; exit 1; }

  - type: Command
    name: Configure cluster access
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      oci ce cluster create-kubeconfig \
        --cluster-id "$${cluster_id}" \
        --file "$${KUBECONFIG}" \
        --region "$${region}" \
        --token-version 2.0.0 \
        --kube-endpoint "$${kube_endpoint}"

  - type: Command
    name: Download exact validated configuration
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      archive="$${OCI_WORKSPACE_DIR}/cluster-admin.zip"
      source_root="$${OCI_WORKSPACE_DIR}/cluster-admin-source"
      targets="$${OCI_WORKSPACE_DIR}/cluster-admin-targets.json"
      mkdir -p "$${source_root}"
      oci artifacts generic artifact download-by-path \
        --repository-id "$${artifact_repository_id}" \
        --artifact-path cluster-admin/deployment-plan.json \
        --artifact-version "$${config_commit}" \
        --file "$${targets}"
      oci devops repository get-repository-archive-content \
        --repository-id "$${repository_id}" \
        --ref-name "$${config_commit}" \
        --format zip \
        --file "$${archive}"
      unzip -q "$${archive}" -d "$${source_root}"
      catalog_file="$(find "$${source_root}" -type f -path '*/catalog/tools.yaml' -print -quit)"
      : "$${catalog_file:?catalog/tools.yaml not found in repository archive}"
      repo_dir="$(dirname "$(dirname "$${catalog_file}")")"
      printf 'repo_dir=%q\n' "$${repo_dir}" >"$${OCI_WORKSPACE_DIR}/cluster-deploy.env"

  - type: Command
    name: Authenticate to mirrored chart registry
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      token_file="$${OCI_WORKSPACE_DIR}/ocir-token.json"
      oci raw-request \
        --http-method GET \
        --target-uri "https://$${registry}/20180419/docker/token" >"$${token_file}"
      python3 - "$${token_file}" <<'PY' | helm registry login "$${registry}" -u BEARER_TOKEN --password-stdin
      import json, sys
      payload = json.load(open(sys.argv[1], encoding="utf-8"))
      data = payload.get("data", payload)
      if isinstance(data, str):
          data = json.loads(data)
      print(data["token"])
      PY

  - type: Command
    name: Deploy selected cluster changes
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/cluster-deploy.env"
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      python3 "$${repo_dir}/script/deploy-cluster.py" \
        --repo "$${repo_dir}" \
        --targets "$${OCI_WORKSPACE_DIR}/cluster-admin-targets.json" \
        --cluster "$${cluster_name}" \
        --commit "$${config_commit}" \
        --artifact-repository-id "$${artifact_repository_id}" \
        --registry "$${registry}" \
        --tenancy-namespace "$${tenancy_namespace}" \
        --chart-prefix "$${chart_prefix}"
